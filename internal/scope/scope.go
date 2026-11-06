// Package scope 是平台的授權唯一權威（Scope Registry）。
//
// 為什麼需要這一層
// ----------------
// 現況（設計 §「既有能力盤點」）：平台端完全沒有目標白名單，MCP 工具對任何主機都照打，
// 真正的保護只有 RBAC（誰能用）、HITL（這次要不要批）、SSRF guard 與禁區（只接在
// redirect 驗證一條功能上）。也就是說「授權只有一份、錯位、半覆蓋」。
//
// 這個套件把授權變成一份可稽核的狀態機：常駐集（scope_targets）＋授權券（scope_grants）
// ＋拒絕記憶（scope_denials）。呼叫端（handler 閘、executor 兜底）在工具執行前呼叫
// Resolve()，由這裡回答「這個目標、這個動作類別，有沒有被授權」。
//
// 三條不可退讓的規則
// ------------------
//  1. 禁區優先（§6）：internal/forbidden 是唯一權威，命中禁區的目標一律拒絕，
//     即使 scope_targets 明確涵蓋它、即使操作者按了批准。禁區規則不在這裡重複實作。
//  2. 破壞性類別永久封鎖（§3.1）：destructive / real_transaction 任何 scope 都解鎖不了。
//  3. 空 action_classes 只代表「一般類別全部允許」，不代表「全部類別允許」：
//     credential_enum / bulk_scan / arbitrary 必須被明確列出。
//
// 與 internal/database 的關係
// ------------------------
// internal/scope 刻意不 import internal/database（避免循環，也讓本套件能用純 *sql.DB 單獨測試），
// 而是用自己的 SQL 讀同一組表。表名／欄位名是兩邊的契約，改一邊就要改兩邊。
package scope

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"sort"
	"strings"
	"time"

	"jysecai/internal/forbidden"
)

// TargetType 是授權目標的型別。
type TargetType string

const (
	// TargetHost 是精確主機（example.com、192.0.2.10）。
	TargetHost TargetType = "host"
	// TargetWildcard 是一層子網域（*.example.com）：命中 x.example.com，
	// 不命中 example.com 本身，也不命中 x.y.example.com。
	TargetWildcard TargetType = "wildcard"
	// TargetCIDR 是網段（192.0.2.0/24）。
	TargetCIDR TargetType = "cidr"
	// TargetURLPrefix 是 URL 前綴（https://example.com/admin/）。
	TargetURLPrefix TargetType = "url_prefix"
)

// 動作類別詞彙（沿用 all/工具/guard.py 的既有八類，避免兩邊對不上；設計 §3）。
const (
	// ActionLocalAnalysis 是本機檔案分析。
	ActionLocalAnalysis = "local_analysis"
	// ActionOfflineReplay 是離線重放／本機證據比對。
	ActionOfflineReplay = "offline_replay"
	// ActionHarmlessRequest 是無害請求（GET／HEAD 類）。
	ActionHarmlessRequest = "harmless_request"
	// ActionDBReadExtract 是唯讀資料庫提取。
	ActionDBReadExtract = "db_read_extract"
	// ActionDestructive 是破壞性操作（寫入／刪除／竄改）：永久封鎖。
	ActionDestructive = "destructive"
	// ActionCredentialEnum 是憑證枚舉：必須被明確授權。
	ActionCredentialEnum = "credential_enum"
	// ActionBulkScan 是大量掃描：必須被明確授權。
	ActionBulkScan = "bulk_scan"
	// ActionRealTransaction 是真實交易（下單／付款／轉帳）：永久封鎖。
	ActionRealTransaction = "real_transaction"
	// ActionArbitrary 是未宣告動作類別的任意執行：必須被明確授權。
	ActionArbitrary = "arbitrary"
)

// 拒絕原因字串。
const (
	// ReasonForbidden 是命中禁區（119／EPCR／消防救護）：永遠拒絕。
	ReasonForbidden = "forbidden"
	// ReasonPermanentBlock 是永久封鎖的動作類別：任何授權都解鎖不了。
	ReasonPermanentBlock = "permanent_block"
	// ReasonPreviouslyDenied 是這個目標先前已被拒絕過。
	ReasonPreviouslyDenied = "previously_denied"
	// ReasonExpired 是授權已過期。
	ReasonExpired = "expired"
	// ReasonExhausted 是授權券次數已用盡。
	ReasonExhausted = "exhausted"
	// ReasonActionClassNotAllowed 是主機有被授權，但這個動作類別沒有。
	ReasonActionClassNotAllowed = "action_class_not_allowed"
)

// 授權來源字串。
const (
	// SourceScopeTarget 表示命中常駐集（scope_targets）。
	SourceScopeTarget = "scope_target"
	// SourceScopeGrant 表示命中授權券（scope_grants）。
	SourceScopeGrant = "scope_grant"
)

// generalActionClasses 是「空 action_classes 時」允許的四個一般類別。
//
// 這是設計 §3.1 的重點：空陣列不是「全部類別」，只是「一般類別」。
var generalActionClasses = []string{
	ActionLocalAnalysis,
	ActionOfflineReplay,
	ActionHarmlessRequest,
	ActionDBReadExtract,
}

// Target 是一個正規化後的目標。
type Target struct {
	// Raw 是原始輸入（未加工），稽核要留原樣。
	Raw string
	// Host 是正規化主機（去掉 scheme／path／port）。
	Host string
	// Port 是可選埠位；沒有則是空字串。
	Port string
	// Kind 是型別：host | wildcard | cidr | url_prefix。
	Kind TargetType
	// URL 是原始是 URL 時保留的完整正規化 URL。
	URL string
}

// Key 回傳這個目標的正規化鍵（拒絕記憶與稽核都用它）。
//
// 規則：URL 目標用正規化 URL；CIDR 用網段字串；其餘用 host[:port]。
func (t Target) Key() string {
	switch t.Kind {
	case TargetURLPrefix:
		if t.URL != "" {
			return t.URL
		}
	case TargetCIDR:
		if t.Host != "" {
			return t.Host
		}
	}
	if t.Host == "" {
		return strings.ToLower(strings.TrimSpace(t.Raw))
	}
	if t.Port != "" {
		return t.Host + ":" + t.Port
	}
	return t.Host
}

// Match 是一筆命中的授權。
type Match struct {
	// Target 是被命中的目標。
	Target Target
	// GrantID 是 scope_targets.id 或 scope_grants.id。
	GrantID string
	// Source 是 scope_target 或 scope_grant。
	Source string
	// Owner 是 scope_targets.owner；授權券留空。
	Owner string
	// ActionClasses 是這筆授權實際容許的動作類別。
	//
	// 空的 action_classes 會展開成四個一般類別，因為呼叫端多半要顯示
	// 「這張卡片的授權到底能做什麼」，而不是拿到一個空清單。
	ActionClasses []string
}

// Denial 是一次拒絕。
type Denial struct {
	// Target 是被拒的目標。
	Target Target
	// Reason 是拒絕原因（forbidden / permanent_block / previously_denied /
	// expired / exhausted / action_class_not_allowed）。
	Reason string
	// Detail 是給人看的補充說明。
	Detail string
}

// Result 是一次判定的結果。
type Result struct {
	// Covered 是已被授權涵蓋的目標。
	Covered []Match
	// Uncovered 是既沒被授權、也沒被拒絕的目標（需要操作者裁決）。
	Uncovered []Target
	// Denied 是被拒絕的目標。
	Denied []Denial
}

// Queryer 是本套件需要的最小資料庫介面。
//
// 由 *sql.DB 與 database.DB（內嵌 *sql.DB）滿足。
type Queryer interface {
	QueryContext(ctx context.Context, query string, args ...any) (*sql.Rows, error)
	QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
	ExecContext(ctx context.Context, query string, args ...any) (sql.Result, error)
}

// Service 是 scope registry 的查詢服務。
type Service struct {
	q Queryer
}

// NewService 建立 scope registry 服務。
func NewService(q Queryer) *Service {
	return &Service{q: q}
}

// Resolve 判斷一組目標在指定動作類別下是否被授權涵蓋。
//
// 判定順序（順序本身就是安全語意，不可調換）：
//  1. 禁區優先：命中 internal/forbidden 的目標直接拒絕，不列入 Uncovered——
//     它不是「還沒被授權」，而是「永遠不該被碰到」。
//  2. 永久封鎖的動作類別（destructive / real_transaction）：整批拒絕。
//  3. 拒絕記憶：之前拒過的目標直接拒，不再打擾操作者。
//  4. 常駐集（scope_targets）→ 授權券（scope_grants）。
//
// at 是判定基準時間；零值代表現在。時間可注入是為了測試到期語意。
func (s *Service) Resolve(ctx context.Context, targets []string, actionClass string, at time.Time) (Result, error) {
	var result Result
	if s == nil || s.q == nil {
		return result, errors.New("scope 服務尚未初始化（缺少資料庫連線）")
	}
	if at.IsZero() {
		at = time.Now()
	}
	actionClass = strings.TrimSpace(actionClass)

	rows, err := s.loadScopeRows(ctx)
	if err != nil {
		return result, err
	}
	grants, err := s.loadGrantRows(ctx)
	if err != nil {
		return result, err
	}
	denials, err := s.loadDenials(ctx)
	if err != nil {
		return result, err
	}

	for _, raw := range targets {
		target := NormalizeTarget(raw)
		if target.Host == "" && target.URL == "" {
			continue
		}

		// ① 禁區優先：即使 scope_targets 涵蓋、即使操作者批准，都必須擋下來。
		if reason := forbidden.Reason(target.Host, target.Raw, "", "", ""); reason != "" {
			result.Denied = append(result.Denied, Denial{
				Target: target,
				Reason: ReasonForbidden,
				Detail: "命中禁區（" + reason + "）：任何授權都無法解除",
			})
			continue
		}

		// ② 永久封鎖的動作類別。
		if isPermanentBlocked(actionClass) {
			result.Denied = append(result.Denied, Denial{
				Target: target,
				Reason: ReasonPermanentBlock,
				Detail: "動作類別 " + actionClass + " 屬永久封鎖，任何 scope／授權券都無法授權",
			})
			continue
		}

		// ③ 拒絕記憶。
		if denial, ok := denials[target.Key()]; ok {
			result.Denied = append(result.Denied, Denial{
				Target: target,
				Reason: ReasonPreviouslyDenied,
				Detail: denialDetail(denial),
			})
			continue
		}

		scopeMatch, scopeDenial := matchScopeRows(rows, target, actionClass, at)
		grantMatch, grantDenial := matchGrantRows(grants, target, actionClass, at)
		switch {
		case scopeMatch != nil:
			result.Covered = append(result.Covered, *scopeMatch)
		case grantMatch != nil:
			result.Covered = append(result.Covered, *grantMatch)
		case scopeDenial != nil:
			result.Denied = append(result.Denied, *scopeDenial)
		case grantDenial != nil:
			result.Denied = append(result.Denied, *grantDenial)
		default:
			result.Uncovered = append(result.Uncovered, target)
		}
	}
	return result, nil
}

// ConsumeGrant 使用一次授權券。
//
// 判定與消耗是分開的兩個動作：Resolve 只回答「能不能」，實際扣次數必須由呼叫端
// 明確呼叫本函式（例如工具真的執行成功之後）。
//
// SQL 與 database.ConsumeScopeGrant 相同（單條 UPDATE 完成遞增與用盡判定，
// 避免先讀後寫的競態）；兩邊刻意不共用程式碼，因為 internal/scope 不 import
// internal/database，欄位名才是兩邊的契約。
func (s *Service) ConsumeGrant(ctx context.Context, id string) error {
	if s == nil || s.q == nil {
		return errors.New("scope 服務尚未初始化（缺少資料庫連線）")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return errors.New("授權券 ID 為空")
	}
	result, err := s.q.ExecContext(ctx, `
		UPDATE scope_grants
		   SET uses_used = uses_used + 1,
		       status = CASE WHEN uses_used + 1 >= max_uses THEN 'exhausted' ELSE status END
		 WHERE id = ?
		   AND COALESCE(status, 'active') = 'active'
		   AND uses_used < max_uses`, id)
	if err != nil {
		return fmt.Errorf("使用授權券失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("使用授權券失敗: %w", err)
	}
	if affected == 0 {
		return errors.New("授權券不存在、已撤銷或已用盡")
	}
	return nil
}

// scopeRow 是常駐集的一列（已解析 JSON 欄位）。
type scopeRow struct {
	id         string
	owner      string
	kind       TargetType
	value      string
	classes    []string
	port       string
	condUntil  *time.Time
	validFrom  *time.Time
	validUntil *time.Time
}

// grantRow 是授權券的一列。
type grantRow struct {
	id         string
	kind       TargetType
	value      string
	classes    []string
	maxUses    int
	usesUsed   int
	validUntil *time.Time
	status     string
}

// denialRow 是拒絕記憶的一列。
type denialRow struct {
	target    string
	owner     string
	reason    string
	decidedBy string
	decidedAt time.Time
}

// scopeConditions 是 scope_targets.conditions 的 JSON 結構（讀取端）。
type scopeConditions struct {
	Port       string     `json:"port"`
	MaxUses    int        `json:"max_uses"`
	ValidUntil *time.Time `json:"valid_until"`
}

// loadScopeRows 讀取常駐集。
func (s *Service) loadScopeRows(ctx context.Context) ([]scopeRow, error) {
	rows, err := s.q.QueryContext(ctx, `
		SELECT id, COALESCE(owner, ''), target_type, target_value,
		       COALESCE(action_classes, '[]'), COALESCE(conditions, '{}'),
		       valid_from, valid_until
		  FROM scope_targets
		 WHERE COALESCE(status, 'active') = 'active'`)
	if err != nil {
		return nil, fmt.Errorf("讀取 scope_targets 失敗（請確認已呼叫 database.EnsureScopeSchema）: %w", err)
	}
	defer rows.Close()

	var out []scopeRow
	for rows.Next() {
		var (
			row                   scopeRow
			classes, conditions   string
			validFrom, validUntil sql.NullString
		)
		if err := rows.Scan(&row.id, &row.owner, &row.kind, &row.value,
			&classes, &conditions, &validFrom, &validUntil); err != nil {
			return nil, fmt.Errorf("掃描 scope_targets 失敗: %w", err)
		}
		row.classes = decodeClasses(classes)
		var cond scopeConditions
		if err := json.Unmarshal([]byte(conditions), &cond); err == nil {
			row.port = strings.TrimSpace(cond.Port)
			row.condUntil = cond.ValidUntil
		}
		row.validFrom = parseScopeTime(validFrom)
		row.validUntil = parseScopeTime(validUntil)
		out = append(out, row)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("讀取 scope_targets 失敗: %w", err)
	}

	// 匹配順序：host → wildcard → cidr → url_prefix（設計 §1）。
	sort.SliceStable(out, func(i, j int) bool {
		return kindPriority(out[i].kind) < kindPriority(out[j].kind)
	})
	return out, nil
}

// loadGrantRows 讀取授權券（含已用盡／已過期，這些要能回報原因）。
func (s *Service) loadGrantRows(ctx context.Context) ([]grantRow, error) {
	rows, err := s.q.QueryContext(ctx, `
		SELECT id, target_type, target_value, COALESCE(action_classes, '[]'),
		       max_uses, uses_used, valid_until, COALESCE(status, 'active')
		  FROM scope_grants`)
	if err != nil {
		return nil, fmt.Errorf("讀取 scope_grants 失敗（請確認已呼叫 database.EnsureScopeSchema）: %w", err)
	}
	defer rows.Close()

	var out []grantRow
	for rows.Next() {
		var (
			row        grantRow
			classes    string
			validUntil sql.NullString
		)
		if err := rows.Scan(&row.id, &row.kind, &row.value, &classes,
			&row.maxUses, &row.usesUsed, &validUntil, &row.status); err != nil {
			return nil, fmt.Errorf("掃描 scope_grants 失敗: %w", err)
		}
		row.classes = decodeClasses(classes)
		row.validUntil = parseScopeTime(validUntil)
		out = append(out, row)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("讀取 scope_grants 失敗: %w", err)
	}
	sort.SliceStable(out, func(i, j int) bool {
		return kindPriority(out[i].kind) < kindPriority(out[j].kind)
	})
	return out, nil
}

// loadDenials 讀取拒絕記憶。
func (s *Service) loadDenials(ctx context.Context) (map[string]denialRow, error) {
	rows, err := s.q.QueryContext(ctx, `
		SELECT target, COALESCE(owner, ''), COALESCE(reason, ''),
		       COALESCE(decided_by, ''), COALESCE(decided_at, '')
		  FROM scope_denials`)
	if err != nil {
		return nil, fmt.Errorf("讀取 scope_denials 失敗（請確認已呼叫 database.EnsureScopeSchema）: %w", err)
	}
	defer rows.Close()

	out := make(map[string]denialRow)
	for rows.Next() {
		var row denialRow
		var decidedAt string
		if err := rows.Scan(&row.target, &row.owner, &row.reason, &row.decidedBy, &decidedAt); err != nil {
			return nil, fmt.Errorf("掃描 scope_denials 失敗: %w", err)
		}
		row.decidedAt = parseScopeTimeString(decidedAt)
		out[row.target] = row
	}
	return out, rows.Err()
}

// matchScopeRows 比對常駐集。
//
// 回傳 (命中, 拒絕)：命中優先；沒有命中但有「主機對、條件不對」的情況時回傳拒絕，
// 因為那代表操作者已經授權過這個主機，缺的是動作類別或有效期——不是「完全沒授權過」。
func matchScopeRows(rows []scopeRow, target Target, actionClass string, at time.Time) (*Match, *Denial) {
	var expiredDenial, classDenial *Denial
	for _, row := range rows {
		if !scopeRowCovers(row, target) {
			continue
		}
		if reason, detail := scopeRowExpired(row, at); reason != "" {
			if expiredDenial == nil {
				expiredDenial = &Denial{Target: target, Reason: ReasonExpired, Detail: detail}
			}
			continue
		}
		if !classAllowed(row.classes, actionClass) {
			if classDenial == nil {
				classDenial = &Denial{
					Target: target,
					Reason: ReasonActionClassNotAllowed,
					Detail: "此授權（" + row.id + "）未包含動作類別 " + actionClass,
				}
			}
			continue
		}
		return &Match{
			Target:        target,
			GrantID:       row.id,
			Source:        SourceScopeTarget,
			Owner:         row.owner,
			ActionClasses: effectiveClasses(row.classes),
		}, nil
	}
	// 到期優先於類別不符：連授權本身都失效了，先講清楚為什麼。
	if expiredDenial != nil {
		return nil, expiredDenial
	}
	return nil, classDenial
}

// matchGrantRows 比對授權券。
func matchGrantRows(rows []grantRow, target Target, actionClass string, at time.Time) (*Match, *Denial) {
	var expiredDenial, exhaustedDenial, classDenial *Denial
	for _, row := range rows {
		if !grantRowCovers(row, target) {
			continue
		}
		if strings.EqualFold(strings.TrimSpace(row.status), "revoked") {
			// 已撤銷的券不算涵蓋，也不特別回報（沒有對應的拒絕原因字串）。
			continue
		}
		if strings.EqualFold(strings.TrimSpace(row.status), "pending") {
			// 待裁決的授權券尚未生效：不構成涵蓋，也不視為拒絕。
			//
			// 這是「自動起草」機制的安全前提：若 pending 也算涵蓋，等於機器先批准、
			// 人事後追認，整個授權狀態機就形同虛設。
			continue
		}
		if row.validUntil != nil && !row.validUntil.After(at) {
			if expiredDenial == nil {
				expiredDenial = &Denial{
					Target: target,
					Reason: ReasonExpired,
					Detail: "授權券 " + row.id + " 已於 " + row.validUntil.Format(time.RFC3339) + " 到期",
				}
			}
			continue
		}
		if strings.EqualFold(strings.TrimSpace(row.status), "expired") {
			if expiredDenial == nil {
				expiredDenial = &Denial{Target: target, Reason: ReasonExpired, Detail: "授權券 " + row.id + " 已過期"}
			}
			continue
		}
		if row.maxUses > 0 && row.usesUsed >= row.maxUses {
			if exhaustedDenial == nil {
				exhaustedDenial = &Denial{
					Target: target,
					Reason: ReasonExhausted,
					Detail: "授權券 " + row.id + " 的使用次數已用盡",
				}
			}
			continue
		}
		if strings.EqualFold(strings.TrimSpace(row.status), "exhausted") {
			if exhaustedDenial == nil {
				exhaustedDenial = &Denial{Target: target, Reason: ReasonExhausted, Detail: "授權券 " + row.id + " 已用盡"}
			}
			continue
		}
		if !classAllowed(row.classes, actionClass) {
			if classDenial == nil {
				classDenial = &Denial{
					Target: target,
					Reason: ReasonActionClassNotAllowed,
					Detail: "授權券 " + row.id + " 未包含動作類別 " + actionClass,
				}
			}
			continue
		}
		return &Match{
			Target:        target,
			GrantID:       row.id,
			Source:        SourceScopeGrant,
			Owner:         "",
			ActionClasses: effectiveClasses(row.classes),
		}, nil
	}
	if expiredDenial != nil {
		return nil, expiredDenial
	}
	if exhaustedDenial != nil {
		return nil, exhaustedDenial
	}
	return nil, classDenial
}

// scopeRowCovers 判斷一筆常駐集是否涵蓋目標。
func scopeRowCovers(row scopeRow, target Target) bool {
	if !valueMatches(row.kind, row.value, target) {
		return false
	}
	// 埠位限定：conditions.port 有值時，目標的埠位必須一致。
	if row.port != "" {
		if target.effectivePort() != row.port {
			return false
		}
	}
	return true
}

// scopeRowExpired 判斷這筆常駐集在 at 當下是否已過期。
func scopeRowExpired(row scopeRow, at time.Time) (string, string) {
	if row.validUntil != nil && !row.validUntil.After(at) {
		return ReasonExpired, "授權 " + row.id + " 已於 " + row.validUntil.Format(time.RFC3339) + " 到期"
	}
	if row.condUntil != nil && !row.condUntil.After(at) {
		return ReasonExpired, "授權 " + row.id + " 的條件有效期限已過"
	}
	if row.validFrom != nil && row.validFrom.After(at) {
		return ReasonExpired, "授權 " + row.id + " 尚未生效"
	}
	return "", ""
}

// grantRowCovers 判斷一張授權券是否涵蓋目標。
func grantRowCovers(row grantRow, target Target) bool {
	return valueMatches(row.kind, row.value, target)
}

// valueMatches 依型別比對授權值與目標。
//
// 這是整個比對語意的核心，順序與規則來自設計 §1：
//   - host：主機名稱完全相同（大小寫不拘）。
//   - wildcard：只命中一層（*.example.com 命中 x.example.com，不命中 example.com、
//     也不命中 x.y.example.com）。目標本身是 wildcard 時，只有完全相同的樣式才算涵蓋。
//   - cidr：目標 IP 必須在網段內；目標是網段時，整個網段必須被包含。
//   - url_prefix：目標必須是 URL，且正規化後以該前綴開頭（路徑邊界要對齊，
//     否則 /admin 會誤蓋 /administrator）。
//
// URL 目標除了 url_prefix 之外，也能被 host／wildcard／cidr 授權涵蓋
// （實務上「授權 example.com」本來就該涵蓋 https://example.com/xxx）。
func valueMatches(kind TargetType, value string, target Target) bool {
	switch kind {
	case TargetHost:
		host := scopeHost(value)
		return host != "" && host == target.Host
	case TargetWildcard:
		return wildcardMatches(value, target)
	case TargetCIDR:
		return cidrMatches(value, target)
	case TargetURLPrefix:
		if target.URL == "" {
			return false
		}
		return urlPrefixMatches(value, target.URL)
	default:
		return false
	}
}

// scopeHost 取授權值裡的主機名（去掉 scheme、path、port）。
func scopeHost(value string) string {
	normalized := NormalizeTarget(value)
	if normalized.Host == "" {
		return ""
	}
	return normalized.Host
}

// wildcardMatches 比對一層 wildcard。
func wildcardMatches(pattern string, target Target) bool {
	pattern = strings.ToLower(strings.TrimSpace(pattern))
	if !strings.HasPrefix(pattern, "*.") {
		return false
	}
	suffix := strings.TrimPrefix(pattern, "*.")
	if suffix == "" {
		return false
	}
	switch target.Kind {
	case TargetWildcard:
		// 目標本身是 wildcard：只有完全相同的樣式才算涵蓋。
		return strings.ToLower(strings.TrimSpace(target.Host)) == pattern
	default:
		host := strings.ToLower(target.Host)
		if host == "" || !strings.HasSuffix(host, "."+suffix) {
			return false
		}
		// 只允許一層：前綴必須剛好是一個標籤。
		prefix := strings.TrimSuffix(host, "."+suffix)
		return prefix != "" && !strings.Contains(prefix, ".")
	}
}

// cidrMatches 判斷目標是否落在授權網段內。
func cidrMatches(value string, target Target) bool {
	_, network, err := net.ParseCIDR(strings.TrimSpace(value))
	if err != nil {
		return false
	}
	switch target.Kind {
	case TargetCIDR:
		_, other, err := net.ParseCIDR(target.Host)
		if err != nil {
			return false
		}
		// 目標網段必須整個被授權網段包含（不只是起點 IP 落在裡面）。
		return network.Contains(other.IP) && networkMaskSize(network) <= networkMaskSize(other)
	default:
		ip := net.ParseIP(target.Host)
		if ip == nil {
			return false
		}
		return network.Contains(ip)
	}
}

// networkMaskSize 回傳網段遮罩的位元數。
func networkMaskSize(network *net.IPNet) int {
	if network == nil {
		return 0
	}
	ones, _ := network.Mask.Size()
	return ones
}

// urlPrefixMatches 比對 URL 前綴（路徑邊界必須對齊）。
func urlPrefixMatches(prefix, incoming string) bool {
	normalizedPrefix := normalizeScopeURL(prefix)
	if normalizedPrefix == "" {
		return false
	}
	trimmed := strings.TrimSuffix(normalizedPrefix, "/")
	if trimmed == "" {
		return false
	}
	if incoming == trimmed || incoming == normalizedPrefix {
		return true
	}
	return strings.HasPrefix(incoming, trimmed+"/")
}

// normalizeScopeURL 正規化授權值裡的 URL 前綴。
func normalizeScopeURL(raw string) string {
	normalized := NormalizeTarget(raw)
	if normalized.Kind == TargetURLPrefix {
		return normalized.URL
	}
	return ""
}

// kindPriority 回傳匹配順序的優先序（越小越先）。
func kindPriority(kind TargetType) int {
	switch kind {
	case TargetHost:
		return 0
	case TargetWildcard:
		return 1
	case TargetCIDR:
		return 2
	case TargetURLPrefix:
		return 3
	default:
		return 4
	}
}

// isPermanentBlocked 判斷動作類別是否屬永久封鎖（設計 §3.1）。
func isPermanentBlocked(actionClass string) bool {
	switch strings.TrimSpace(actionClass) {
	case ActionDestructive, ActionRealTransaction:
		return true
	default:
		return false
	}
}

// requiresExplicitClass 判斷動作類別是否必須被明確列出。
//
// credential_enum／bulk_scan／arbitrary 這三類風險高，必須在該筆授權的
// action_classes 內明列才算允許；其餘四類是一般類別。
func requiresExplicitClass(actionClass string) bool {
	switch strings.TrimSpace(actionClass) {
	case ActionCredentialEnum, ActionBulkScan, ActionArbitrary:
		return true
	default:
		return false
	}
}

// classAllowed 判斷某一筆授權是否允許該動作類別。
//
// 語意（設計 §3.1「避免『空值＝全部』把封鎖解掉」）：
//   - action_classes 為空陣列 → 只允許四個一般類別。
//   - action_classes 非空 → 就是明確允許清單，必須明列才允許。
//
// 非空即清單（而不是「清單＋一般類別」）是刻意的取捨：安全控制的失敗方向
// 要偏向「過度限制」（操作者被多問一次）而不是「過度放行」。
func classAllowed(classes []string, actionClass string) bool {
	if isPermanentBlocked(actionClass) {
		return false
	}
	actionClass = strings.TrimSpace(actionClass)
	if len(classes) == 0 {
		return !requiresExplicitClass(actionClass)
	}
	for _, class := range classes {
		if strings.EqualFold(strings.TrimSpace(class), actionClass) {
			return true
		}
	}
	return false
}

// effectiveClasses 回傳該筆授權實際容許的動作類別清單。
func effectiveClasses(classes []string) []string {
	if len(classes) == 0 {
		return append([]string(nil), generalActionClasses...)
	}
	return append([]string(nil), classes...)
}

// decodeClasses 解析 action_classes JSON 陣列；壞掉的 JSON 視為空陣列
// （等於只允許一般類別，不會誤放行敏感類別）。
func decodeClasses(raw string) []string {
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

// denialDetail 組出拒絕記憶的人看的說明。
func denialDetail(row denialRow) string {
	detail := "此目標先前已被拒絕"
	if row.reason != "" {
		detail += "（原因：" + row.reason + "）"
	}
	if row.decidedBy != "" {
		detail += "，決策者：" + row.decidedBy
	}
	if !row.decidedAt.IsZero() {
		detail += "，時間：" + row.decidedAt.Format(time.RFC3339)
	}
	return detail
}

// scopeTimeLayouts 是讀取 DATETIME 欄位時要容忍的格式。
//
// 寫入端（internal/database）統一用 RFC3339Nano UTC，但既有資料或其他寫法
// 可能用 SQLite 原生的空格分隔格式，所以這裡多給幾種。
var scopeTimeLayouts = []string{
	time.RFC3339Nano,
	time.RFC3339,
	"2006-01-02 15:04:05.999999999-07:00",
	"2006-01-02 15:04:05-07:00",
	"2006-01-02T15:04:05.999999999-07:00",
	"2006-01-02T15:04:05-07:00",
	"2006-01-02 15:04:05.999999999",
	"2006-01-02 15:04:05",
	"2006-01-02",
}

// parseScopeTime 解析可為空的時間欄位。
func parseScopeTime(value sql.NullString) *time.Time {
	if !value.Valid {
		return nil
	}
	parsed := parseScopeTimeString(value.String)
	if parsed.IsZero() {
		return nil
	}
	return &parsed
}

// parseScopeTimeString 解析時間字串。
func parseScopeTimeString(value string) time.Time {
	value = strings.TrimSpace(value)
	if value == "" {
		return time.Time{}
	}
	for _, layout := range scopeTimeLayouts {
		if parsed, err := time.Parse(layout, value); err == nil {
			return parsed.UTC()
		}
	}
	return time.Time{}
}
