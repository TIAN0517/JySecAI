package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
)

// Scope Registry 的持久化層。
//
// 為什麼獨立成一個檔
// ------------------
// 授權是平台「唯一權威」的資料（設計 §2）：常駐集（scope_targets）、授權券（scope_grants）、
// 拒絕記憶（scope_denials）三張表會同時被匯入 CLI、P1 的 handoff 流程、稽核與執行閘使用。
// 把它集中在這裡，是為了讓「表名／欄位名」只有一份定義，避免各處各寫一份 SQL 結果欄位對不起來。
//
// 命名契約（重要）
// ----------------
// 表名與欄位名是 internal/scope 與本檔之間的契約。internal/scope 刻意不 import 本套件
// （避免循環依賴、也讓它能單獨用純 *sql.DB 測試），而是用自己的 SQL 讀同一張表；
// 因此任何欄位改名都必須兩邊同步，否則 scope 端會靜默讀不到資料。
//
// 遷移原則：CREATE TABLE IF NOT EXISTS + 補欄位（ADD COLUMN），
// 既有 DB 檔不需要重建就能開（設計 §2「遷移必須向後相容」）。

const (
	// ScopeTargetTypeHost 是精確主機（example.com）。
	ScopeTargetTypeHost = "host"
	// ScopeTargetTypeWildcard 是一層子網域（*.example.com，只匹對一層）。
	ScopeTargetTypeWildcard = "wildcard"
	// ScopeTargetTypeCIDR 是網段（192.0.2.0/24）。
	ScopeTargetTypeCIDR = "cidr"
	// ScopeTargetTypeURLPrefix 是 URL 前綴（https://example.com/admin/）。
	ScopeTargetTypeURLPrefix = "url_prefix"
)

const (
	// ScopeTargetStatusActive 表示常駐集項目有效。
	ScopeTargetStatusActive = "active"
	// ScopeTargetStatusRevoked 表示已被操作者撤銷。
	ScopeTargetStatusRevoked = "revoked"
)

const (
	// ScopeGrantStatusActive 表示授權券仍可使用。
	ScopeGrantStatusActive = "active"
	// ScopeGrantStatusExhausted 表示授權券次數用盡。
	ScopeGrantStatusExhausted = "exhausted"
	// ScopeGrantStatusExpired 表示授權券已過期。
	ScopeGrantStatusExpired = "expired"
	// ScopeGrantStatusRevoked 表示授權券已被撤銷。
	ScopeGrantStatusRevoked = "revoked"
	// ScopeGrantStatusPending 表示授權券已起草、等待人工裁決。
	//
	// pending 的券不構成涵蓋（internal/scope 的 matchGrantRows 會略過它），
	// 只有經 ActivateScopeGrant 轉成 active 之後才會生效。
	ScopeGrantStatusPending = "pending"
)

// ScopeConditions 是 scope_targets.conditions 的 JSON 結構。
//
// 這三個欄位是「附條件授權」的最小集合：埠位限定、用次數上限、有效期限。
// 空的 action_classes 代表「一般類別全部允許」，不是「全部類別允許」——
// 這一點在 internal/scope 那端有硬性規則（敏感類別必須明列）。
type ScopeConditions struct {
	// Port 是選配的埠位限定；空字串代表不限埠位。
	Port string `json:"port,omitempty"`
	// MaxUses 是使用次數上限；0 代表不限。
	MaxUses int `json:"max_uses,omitempty"`
	// ValidUntil 是條件層的有效期限；nil 代表無期限。
	ValidUntil *time.Time `json:"valid_until,omitempty"`
}

// ScopeProvenance 是 scope_targets.provenance 的 JSON 結構。
//
// 誰、何時、依據什麼證據把這個目標放進常駐集——稽核要靠它，
// 沒有 provenance 的授權等同於「不知道誰批准的」。
type ScopeProvenance struct {
	Source       string    `json:"source,omitempty"`
	DecidedBy    string    `json:"decided_by,omitempty"`
	DecidedAt    time.Time `json:"decided_at,omitempty"`
	EvidenceHash string    `json:"evidence_hash,omitempty"`
	Note         string    `json:"note,omitempty"`
}

// ScopeTarget 是一筆常駐授權（自有資產、已批准的客戶 scope）。
type ScopeTarget struct {
	ID            string          `json:"id"`
	Owner         string          `json:"owner"`
	TargetType    string          `json:"target_type"`
	TargetValue   string          `json:"target_value"`
	ActionClasses []string        `json:"action_classes"`
	Conditions    ScopeConditions `json:"conditions"`
	ValidFrom     *time.Time      `json:"valid_from,omitempty"`
	ValidUntil    *time.Time      `json:"valid_until,omitempty"`
	Provenance    ScopeProvenance `json:"provenance"`
	Status        string          `json:"status"`
	CreatedAt     time.Time       `json:"created_at"`
}

// ScopeGrant 是一張授權券（有條件／一次性，自帶目標描述）。
type ScopeGrant struct {
	ID            string     `json:"id"`
	TargetType    string     `json:"target_type"`
	TargetValue   string     `json:"target_value"`
	ActionClasses []string   `json:"action_classes"`
	MaxUses       int        `json:"max_uses"`
	UsesUsed      int        `json:"uses_used"`
	ValidUntil    *time.Time `json:"valid_until,omitempty"`
	IssuedBy      string     `json:"issued_by"`
	IssuedAt      time.Time  `json:"issued_at"`
	Evidence      string     `json:"evidence"`
	Status        string     `json:"status"`
	// DecidedBy 是最後一次人工決定（核准／拒絕）的人。
	DecidedBy string `json:"decided_by,omitempty"`
	// DecidedAt 是最後一次人工決定的時間。
	DecidedAt *time.Time `json:"decided_at,omitempty"`
}

// ScopeDenial 是「被拒絕過的目標」記憶。
//
// 拒絕也會被記住：同一個目標再回來時直接拒，不再打擾操作者（設計 §6／§7）。
type ScopeDenial struct {
	Target    string    `json:"target"`
	Owner     string    `json:"owner"`
	Reason    string    `json:"reason"`
	DecidedBy string    `json:"decided_by"`
	DecidedAt time.Time `json:"decided_at"`
}

// QueryerLike 是本檔 CRUD 需要的最小資料庫介面。
//
// 用介面而不是直接吃 *sql.DB，是為了讓 *sql.DB 與 database.DB（內嵌 *sql.DB）都能直接呼叫。
type QueryerLike interface {
	QueryContext(ctx context.Context, query string, args ...any) (*sql.Rows, error)
	QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
	ExecContext(ctx context.Context, query string, args ...any) (sql.Result, error)
}

const createScopeTargetsTable = `
	CREATE TABLE IF NOT EXISTS scope_targets (
		id             TEXT PRIMARY KEY,
		owner          TEXT NOT NULL,
		target_type    TEXT NOT NULL,
		target_value   TEXT NOT NULL,
		action_classes TEXT NOT NULL DEFAULT '[]',
		conditions     TEXT NOT NULL DEFAULT '{}',
		valid_from     DATETIME,
		valid_until    DATETIME,
		provenance     TEXT NOT NULL DEFAULT '{}',
		status         TEXT NOT NULL DEFAULT 'active',
		created_at     DATETIME NOT NULL
	);`

const createScopeGrantsTable = `
	CREATE TABLE IF NOT EXISTS scope_grants (
		id             TEXT PRIMARY KEY,
		target_type    TEXT NOT NULL,
		target_value   TEXT NOT NULL,
		action_classes TEXT NOT NULL DEFAULT '[]',
		max_uses       INTEGER NOT NULL DEFAULT 1,
		uses_used      INTEGER NOT NULL DEFAULT 0,
		valid_until    DATETIME,
		issued_by      TEXT NOT NULL,
		issued_at      DATETIME NOT NULL,
		evidence       TEXT NOT NULL DEFAULT '',
		status         TEXT NOT NULL DEFAULT 'active'
	);`

const createScopeDenialsTable = `
	CREATE TABLE IF NOT EXISTS scope_denials (
		target      TEXT PRIMARY KEY,
		owner       TEXT NOT NULL,
		reason      TEXT NOT NULL,
		decided_by  TEXT NOT NULL,
		decided_at  DATETIME NOT NULL
	);`

// EnsureScopeSchema 建立 scope registry 的三張表。
//
// 冪等且向後相容：已經存在的表不會被改動，缺欄位時才補欄位。
// 整合者需要在 internal/database/database.go 的 initTables() 內呼叫本函式，
// 否則 scope registry 讀不到資料（internal/scope 會回報「表不存在」）。
func EnsureScopeSchema(db *sql.DB) error {
	if db == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	for _, stmt := range []string{createScopeTargetsTable, createScopeGrantsTable, createScopeDenialsTable} {
		if _, err := db.Exec(stmt); err != nil {
			return fmt.Errorf("建立 scope registry 資料表失敗: %w", err)
		}
	}
	// 舊的 scope registry 資料檔可能少欄位：逐一補齊（已存在時忽略）。
	// 既有慣例是忽略 "duplicate column" 錯誤（見 redirect_verify.go）。
	additions := []struct {
		table  string
		column string
		def    string
	}{
		{"scope_targets", "action_classes", "TEXT NOT NULL DEFAULT '[]'"},
		{"scope_targets", "conditions", "TEXT NOT NULL DEFAULT '{}'"},
		{"scope_targets", "provenance", "TEXT NOT NULL DEFAULT '{}'"},
		{"scope_targets", "status", "TEXT NOT NULL DEFAULT 'active'"},
		{"scope_targets", "valid_from", "DATETIME"},
		{"scope_targets", "valid_until", "DATETIME"},
		{"scope_grants", "action_classes", "TEXT NOT NULL DEFAULT '[]'"},
		{"scope_grants", "max_uses", "INTEGER NOT NULL DEFAULT 1"},
		{"scope_grants", "uses_used", "INTEGER NOT NULL DEFAULT 0"},
		{"scope_grants", "valid_until", "DATETIME"},
		{"scope_grants", "status", "TEXT NOT NULL DEFAULT 'active'"},
		{"scope_grants", "decided_by", "TEXT NOT NULL DEFAULT ''"},
		{"scope_grants", "decided_at", "DATETIME"},
	}
	for _, add := range additions {
		if _, err := db.Exec(fmt.Sprintf("ALTER TABLE %s ADD COLUMN %s %s", add.table, add.column, add.def)); err != nil {
			if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
				return fmt.Errorf("遷移 %s.%s 失敗: %w", add.table, add.column, err)
			}
		}
	}
	return nil
}

// ListScopeTargets 列出所有未撤銷的常駐授權。
func ListScopeTargets(ctx context.Context, q QueryerLike) ([]ScopeTarget, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	rows, err := q.QueryContext(ctx, `
		SELECT id, owner, target_type, target_value, action_classes, conditions,
		       valid_from, valid_until, provenance, status, created_at
		  FROM scope_targets
		 WHERE COALESCE(status, 'active') = 'active'
		 ORDER BY created_at ASC, rowid ASC`)
	if err != nil {
		return nil, fmt.Errorf("查詢 scope_targets 失敗: %w", err)
	}
	defer rows.Close()

	var out []ScopeTarget
	for rows.Next() {
		target, err := scanScopeTarget(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, *target)
	}
	return out, rows.Err()
}

// GetScopeTarget 取得單一常駐授權。
func GetScopeTarget(ctx context.Context, q QueryerLike, id string) (*ScopeTarget, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return nil, fmt.Errorf("scope target ID 為空")
	}
	row := q.QueryRowContext(ctx, `
		SELECT id, owner, target_type, target_value, action_classes, conditions,
		       valid_from, valid_until, provenance, status, created_at
		  FROM scope_targets WHERE id = ?`, id)
	target, err := scanScopeTarget(row)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("scope target 不存在")
	}
	if err != nil {
		return nil, err
	}
	return target, nil
}

// UpsertScopeTarget 新增或覆寫一筆常駐授權。
//
// 以 id 為鍵做 upsert（匯入 CLI 需要冪等），created_at 在覆寫時保留原值。
func UpsertScopeTarget(ctx context.Context, q QueryerLike, target ScopeTarget) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	target.ID = strings.TrimSpace(target.ID)
	if target.ID == "" {
		target.ID = uuid.New().String()
	}
	if strings.TrimSpace(target.Owner) == "" {
		return fmt.Errorf("scope target 必須有 owner")
	}
	if strings.TrimSpace(target.TargetType) == "" {
		return fmt.Errorf("scope target 必須有 target_type")
	}
	if strings.TrimSpace(target.TargetValue) == "" {
		return fmt.Errorf("scope target 必須有 target_value")
	}
	if strings.TrimSpace(target.Status) == "" {
		target.Status = ScopeTargetStatusActive
	}
	if target.CreatedAt.IsZero() {
		target.CreatedAt = time.Now()
	}
	classes, err := json.Marshal(nonNilStrings(target.ActionClasses))
	if err != nil {
		return fmt.Errorf("序列化 action_classes 失敗: %w", err)
	}
	conditions, err := json.Marshal(target.Conditions)
	if err != nil {
		return fmt.Errorf("序列化 conditions 失敗: %w", err)
	}
	provenance, err := json.Marshal(target.Provenance)
	if err != nil {
		return fmt.Errorf("序列化 provenance 失敗: %w", err)
	}
	_, err = q.ExecContext(ctx, `
		INSERT INTO scope_targets (
			id, owner, target_type, target_value, action_classes, conditions,
			valid_from, valid_until, provenance, status, created_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			owner = excluded.owner,
			target_type = excluded.target_type,
			target_value = excluded.target_value,
			action_classes = excluded.action_classes,
			conditions = excluded.conditions,
			valid_from = excluded.valid_from,
			valid_until = excluded.valid_until,
			provenance = excluded.provenance,
			status = excluded.status`,
		target.ID, target.Owner, target.TargetType, target.TargetValue,
		string(classes), string(conditions),
		nullIfEmptyTime(target.ValidFrom), nullIfEmptyTime(target.ValidUntil),
		string(provenance), target.Status, formatSQLiteUTC(target.CreatedAt))
	if err != nil {
		return fmt.Errorf("寫入 scope target 失敗: %w", err)
	}
	return nil
}

// RevokeScopeTarget 撤銷一筆常駐授權（保留紀錄，只改狀態）。
func RevokeScopeTarget(ctx context.Context, q QueryerLike, id string) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return fmt.Errorf("scope target ID 為空")
	}
	result, err := q.ExecContext(ctx, `UPDATE scope_targets SET status = ? WHERE id = ?`, ScopeTargetStatusRevoked, id)
	if err != nil {
		return fmt.Errorf("撤銷 scope target 失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("撤銷 scope target 失敗: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("scope target 不存在")
	}
	return nil
}

// ListScopeGrants 列出所有授權券（含已用盡／已過期，供稽核與 UI 顯示）。
func ListScopeGrants(ctx context.Context, q QueryerLike) ([]ScopeGrant, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	rows, err := q.QueryContext(ctx, `
		SELECT id, target_type, target_value, action_classes, max_uses, uses_used,
		       valid_until, issued_by, issued_at, evidence, status, decided_by, decided_at
		  FROM scope_grants
		 ORDER BY issued_at ASC, rowid ASC`)
	if err != nil {
		return nil, fmt.Errorf("查詢 scope_grants 失敗: %w", err)
	}
	defer rows.Close()

	var out []ScopeGrant
	for rows.Next() {
		grant, err := scanScopeGrant(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, *grant)
	}
	return out, rows.Err()
}

// GetScopeGrant 取得單一授權券。
func GetScopeGrant(ctx context.Context, q QueryerLike, id string) (*ScopeGrant, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return nil, fmt.Errorf("scope grant ID 為空")
	}
	row := q.QueryRowContext(ctx, `
		SELECT id, target_type, target_value, action_classes, max_uses, uses_used,
		       valid_until, issued_by, issued_at, evidence, status, decided_by, decided_at
		  FROM scope_grants WHERE id = ?`, id)
	grant, err := scanScopeGrant(row)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("scope grant 不存在")
	}
	if err != nil {
		return nil, err
	}
	return grant, nil
}

// CreateScopeGrant 簽發一張授權券。
func CreateScopeGrant(ctx context.Context, q QueryerLike, grant ScopeGrant) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	grant.ID = strings.TrimSpace(grant.ID)
	if grant.ID == "" {
		grant.ID = uuid.New().String()
	}
	if strings.TrimSpace(grant.TargetType) == "" {
		return fmt.Errorf("scope grant 必須有 target_type")
	}
	if strings.TrimSpace(grant.TargetValue) == "" {
		return fmt.Errorf("scope grant 必須有 target_value")
	}
	if strings.TrimSpace(grant.IssuedBy) == "" {
		return fmt.Errorf("scope grant 必須有 issued_by")
	}
	if grant.MaxUses <= 0 {
		grant.MaxUses = 1
	}
	if grant.UsesUsed < 0 {
		grant.UsesUsed = 0
	}
	if strings.TrimSpace(grant.Status) == "" {
		grant.Status = ScopeGrantStatusActive
	}
	if grant.IssuedAt.IsZero() {
		grant.IssuedAt = time.Now()
	}
	classes, err := json.Marshal(nonNilStrings(grant.ActionClasses))
	if err != nil {
		return fmt.Errorf("序列化 action_classes 失敗: %w", err)
	}
	_, err = q.ExecContext(ctx, `
		INSERT INTO scope_grants (
			id, target_type, target_value, action_classes, max_uses, uses_used,
			valid_until, issued_by, issued_at, evidence, status
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		grant.ID, grant.TargetType, grant.TargetValue, string(classes),
		grant.MaxUses, grant.UsesUsed, nullIfEmptyTime(grant.ValidUntil),
		grant.IssuedBy, formatSQLiteUTC(grant.IssuedAt), grant.Evidence, grant.Status)
	if err != nil {
		return fmt.Errorf("寫入 scope grant 失敗: %w", err)
	}
	return nil
}

// ActivateScopeGrant 把一張待裁決的授權券轉為生效。
//
// 只允許 pending → active 的單向轉換，而且必須還沒過期、還沒用盡：
//   - 已經是 active 的券再呼叫 → 回傳 false，不重置 uses_used（冪等、不會重放）。
//   - 已撤銷／已用盡／已過期／不存在的券 → 回傳 false。
//   - 讀取或寫入失敗 → 回傳錯誤。
//
// 這是「按一次核准」的唯一入口，所以語意刻意保守：只認 pending。
func ActivateScopeGrant(ctx context.Context, q QueryerLike, id, activatedBy string) (bool, error) {
	if q == nil {
		return false, fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return false, fmt.Errorf("scope grant ID 為空")
	}
	var status string
	var maxUses, usesUsed int
	var validUntil sql.NullString
	err := q.QueryRowContext(ctx, `
		SELECT COALESCE(status, 'active'), max_uses, uses_used, valid_until
		  FROM scope_grants WHERE id = ?`, id).
		Scan(&status, &maxUses, &usesUsed, &validUntil)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return false, nil
		}
		return false, fmt.Errorf("讀取 scope grant 失敗: %w", err)
	}
	if !strings.EqualFold(strings.TrimSpace(status), ScopeGrantStatusPending) {
		return false, nil
	}
	if maxUses > 0 && usesUsed >= maxUses {
		return false, nil
	}
	now := time.Now().UTC()
	if validUntil.Valid {
		if expiry := parseNullableScopeTime(validUntil); expiry != nil && !expiry.After(now) {
			return false, nil
		}
	}
	result, err := q.ExecContext(ctx, `
		UPDATE scope_grants
		   SET status = ?, decided_by = ?, decided_at = ?
		 WHERE id = ? AND COALESCE(status, 'active') = ?`,
		ScopeGrantStatusActive, strings.TrimSpace(activatedBy), formatSQLiteUTC(now),
		id, ScopeGrantStatusPending)
	if err != nil {
		return false, fmt.Errorf("啟用 scope grant 失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return false, fmt.Errorf("啟用 scope grant 失敗: %w", err)
	}
	return affected > 0, nil
}

// RevokeScopeGrant 撤銷一張授權券。
//
// 撤銷是人的決定（這件事被拒絕了），所以 pending 與 active 都能撤銷。
// 已撤銷／已用盡／已過期的券再撤銷一次回傳 false（冪等）。
func RevokeScopeGrant(ctx context.Context, q QueryerLike, id, revokedBy string) (bool, error) {
	if q == nil {
		return false, fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return false, fmt.Errorf("scope grant ID 為空")
	}
	now := time.Now().UTC()
	result, err := q.ExecContext(ctx, `
		UPDATE scope_grants
		   SET status = ?, decided_by = ?, decided_at = ?
		 WHERE id = ? AND COALESCE(status, 'active') IN (?, ?)`,
		ScopeGrantStatusRevoked, strings.TrimSpace(revokedBy), formatSQLiteUTC(now),
		id, ScopeGrantStatusPending, ScopeGrantStatusActive)
	if err != nil {
		return false, fmt.Errorf("撤銷 scope grant 失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return false, fmt.Errorf("撤銷 scope grant 失敗: %w", err)
	}
	return affected > 0, nil
}

// ConsumeScopeGrant 使用一次授權券。
//
// 用一條 UPDATE 完成「遞增 + 判定用盡」，避免先讀後寫的競態；
// WHERE 條件同時擋掉已用盡／已撤銷的券。
func ConsumeScopeGrant(ctx context.Context, q QueryerLike, id string) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return fmt.Errorf("scope grant ID 為空")
	}
	result, err := q.ExecContext(ctx, `
		UPDATE scope_grants
		   SET uses_used = uses_used + 1,
		       status = CASE WHEN uses_used + 1 >= max_uses THEN 'exhausted' ELSE status END
		 WHERE id = ?
		   AND COALESCE(status, 'active') = 'active'
		   AND uses_used < max_uses`, id)
	if err != nil {
		return fmt.Errorf("使用 scope grant 失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("使用 scope grant 失敗: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("授權券不存在、已撤銷或已用盡")
	}
	return nil
}

// RecordScopeDenial 記住一次拒絕（同一目標再次出現時直接拒，不再打擾操作者）。
//
// target 必須是「正規化後的目標鍵」：呼叫端請用
// scope.NormalizeTarget(raw).Key() 產生，否則大小寫或結尾點的差異
// 會讓拒絕記憶對不上（internal/scope 讀取時就是用 Target.Key() 比對的）。
func RecordScopeDenial(ctx context.Context, q QueryerLike, denial ScopeDenial) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	denial.Target = strings.TrimSpace(denial.Target)
	if denial.Target == "" {
		return fmt.Errorf("拒絕記錄必須有 target")
	}
	if strings.TrimSpace(denial.Reason) == "" {
		denial.Reason = "rejected"
	}
	if denial.DecidedAt.IsZero() {
		denial.DecidedAt = time.Now()
	}
	_, err := q.ExecContext(ctx, `
		INSERT INTO scope_denials (target, owner, reason, decided_by, decided_at)
		VALUES (?, ?, ?, ?, ?)
		ON CONFLICT(target) DO UPDATE SET
			owner = excluded.owner,
			reason = excluded.reason,
			decided_by = excluded.decided_by,
			decided_at = excluded.decided_at`,
		denial.Target, denial.Owner, denial.Reason, denial.DecidedBy,
		formatSQLiteUTC(denial.DecidedAt))
	if err != nil {
		return fmt.Errorf("寫入 scope denial 失敗: %w", err)
	}
	return nil
}

// ListScopeDenials 列出所有拒絕記憶。
func ListScopeDenials(ctx context.Context, q QueryerLike) ([]ScopeDenial, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	rows, err := q.QueryContext(ctx, `
		SELECT target, owner, reason, decided_by, decided_at
		  FROM scope_denials
		 ORDER BY decided_at DESC, rowid DESC`)
	if err != nil {
		return nil, fmt.Errorf("查詢 scope_denials 失敗: %w", err)
	}
	defer rows.Close()

	var out []ScopeDenial
	for rows.Next() {
		var denial ScopeDenial
		var decidedAt string
		if err := rows.Scan(&denial.Target, &denial.Owner, &denial.Reason, &denial.DecidedBy, &decidedAt); err != nil {
			return nil, fmt.Errorf("掃描 scope_denials 失敗: %w", err)
		}
		denial.DecidedAt = parseDBTime(decidedAt)
		out = append(out, denial)
	}
	return out, rows.Err()
}

// DeleteScopeDenial 移除一筆拒絕記憶（例如操作者改變心意時重新開放該目標）。
func DeleteScopeDenial(ctx context.Context, q QueryerLike, target string) error {
	if q == nil {
		return fmt.Errorf("資料庫連線不能為空")
	}
	target = strings.TrimSpace(target)
	if target == "" {
		return fmt.Errorf("拒絕記錄的 target 為空")
	}
	if _, err := q.ExecContext(ctx, `DELETE FROM scope_denials WHERE target = ?`, target); err != nil {
		return fmt.Errorf("刪除 scope denial 失敗: %w", err)
	}
	return nil
}

// scopeRowScanner 是掃描單列的介面（*sql.Row 與 *sql.Rows 都符合）。
type scopeRowScanner interface {
	Scan(dest ...any) error
}

func scanScopeTarget(row scopeRowScanner) (*ScopeTarget, error) {
	var target ScopeTarget
	var classes, conditions, provenance string
	var validFrom, validUntil sql.NullString
	var createdAt string
	if err := row.Scan(
		&target.ID, &target.Owner, &target.TargetType, &target.TargetValue,
		&classes, &conditions, &validFrom, &validUntil, &provenance, &target.Status, &createdAt,
	); err != nil {
		if err == sql.ErrNoRows {
			return nil, err
		}
		return nil, fmt.Errorf("掃描 scope_targets 失敗: %w", err)
	}
	target.ActionClasses = decodeScopeClasses(classes)
	target.Conditions = decodeScopeConditions(conditions)
	target.Provenance = decodeScopeProvenance(provenance)
	target.ValidFrom = parseNullableScopeTime(validFrom)
	target.ValidUntil = parseNullableScopeTime(validUntil)
	target.CreatedAt = parseDBTime(createdAt)
	return &target, nil
}

func scanScopeGrant(row scopeRowScanner) (*ScopeGrant, error) {
	var grant ScopeGrant
	var classes string
	var validUntil sql.NullString
	var issuedAt string
	var decidedAt sql.NullString
	if err := row.Scan(
		&grant.ID, &grant.TargetType, &grant.TargetValue, &classes,
		&grant.MaxUses, &grant.UsesUsed, &validUntil,
		&grant.IssuedBy, &issuedAt, &grant.Evidence, &grant.Status,
		&grant.DecidedBy, &decidedAt,
	); err != nil {
		if err == sql.ErrNoRows {
			return nil, err
		}
		return nil, fmt.Errorf("掃描 scope_grants 失敗: %w", err)
	}
	grant.ActionClasses = decodeScopeClasses(classes)
	grant.ValidUntil = parseNullableScopeTime(validUntil)
	grant.IssuedAt = parseDBTime(issuedAt)
	grant.DecidedAt = parseNullableScopeTime(decidedAt)
	return &grant, nil
}

// decodeScopeClasses 解析 action_classes JSON 陣列；壞掉的 JSON 視為空陣列（不放行敏感類別）。
func decodeScopeClasses(raw string) []string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil
	}
	var out []string
	if err := json.Unmarshal([]byte(raw), &out); err != nil {
		return nil
	}
	return out
}

// decodeScopeConditions 解析 conditions JSON 物件；壞掉的 JSON 視為無條件。
func decodeScopeConditions(raw string) ScopeConditions {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ScopeConditions{}
	}
	var out ScopeConditions
	if err := json.Unmarshal([]byte(raw), &out); err != nil {
		return ScopeConditions{}
	}
	return out
}

// decodeScopeProvenance 解析 provenance JSON 物件。
func decodeScopeProvenance(raw string) ScopeProvenance {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ScopeProvenance{}
	}
	var out ScopeProvenance
	if err := json.Unmarshal([]byte(raw), &out); err != nil {
		return ScopeProvenance{}
	}
	return out
}

// nonNilStrings 確保 JSON 序列化出來的是 [] 而不是 null（欄位預設值是 '[]'）。
func nonNilStrings(values []string) []string {
	if values == nil {
		return []string{}
	}
	return values
}

// nullIfEmptyTime 把零值時間轉成可寫入資料表的 nil。
func nullIfEmptyTime(value *time.Time) interface{} {
	if value == nil || value.IsZero() {
		return nil
	}
	return formatSQLiteUTC(*value)
}

// parseNullableScopeTime 解析可為空的時間欄位。
func parseNullableScopeTime(value sql.NullString) *time.Time {
	if !value.Valid {
		return nil
	}
	parsed := parseDBTime(value.String)
	if parsed.IsZero() {
		return nil
	}
	return &parsed
}
