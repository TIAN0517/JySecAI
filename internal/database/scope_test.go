package database

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	"go.uber.org/zap"
)

// newScopeTestDB 建立一個走完整初始化的資料庫，並補上 scope registry 的 schema。
//
// 這裡刻意走 NewDB 而不是直接 sql.Open：要驗證 *DB（內嵌 *sql.DB）
// 確實能當成 QueryerLike 使用——這是整合者會依賴的呼叫方式。
func newScopeTestDB(t *testing.T) *DB {
	t.Helper()
	dbPath := filepath.Join(t.TempDir(), "scope.db")
	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err := EnsureScopeSchema(db.DB); err != nil {
		t.Fatal(err)
	}
	return db
}

func TestEnsureScopeSchemaIsIdempotent(t *testing.T) {
	db := newScopeTestDB(t)
	// 第二次呼叫不該出錯（initTables 之後、或重複啟動都會再跑一次）。
	if err := EnsureScopeSchema(db.DB); err != nil {
		t.Fatal(err)
	}
	if err := EnsureScopeSchema(db.DB); err != nil {
		t.Fatal(err)
	}
}

func TestEnsureScopeSchemaAddsMissingColumns(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	// 模擬舊版資料檔：scope_targets 只有少數欄位。
	if _, err := db.ExecContext(ctx, `DROP TABLE scope_targets`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.ExecContext(ctx, `
		CREATE TABLE scope_targets (
			id TEXT PRIMARY KEY,
			owner TEXT NOT NULL,
			target_type TEXT NOT NULL,
			target_value TEXT NOT NULL,
			created_at DATETIME NOT NULL
		)`); err != nil {
		t.Fatal(err)
	}
	if err := EnsureScopeSchema(db.DB); err != nil {
		t.Fatalf("舊資料檔應能被補齊欄位：%v", err)
	}

	// 補齊後可以正常寫入與讀回。
	target := ScopeTarget{
		ID:         "legacy-1",
		Owner:      "self",
		TargetType: ScopeTargetTypeHost,
		TargetValue: "example.com",
	}
	if err := UpsertScopeTarget(ctx, db, target); err != nil {
		t.Fatal(err)
	}
	loaded, err := GetScopeTarget(ctx, db, "legacy-1")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.TargetValue != "example.com" {
		t.Fatalf("讀回的內容不正確：%#v", loaded)
	}
}

func TestUpsertAndListScopeTargets(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	validUntil := time.Date(2026, 12, 1, 0, 0, 0, 0, time.UTC)
	target := ScopeTarget{
		ID:            "t-1",
		Owner:         "client-a",
		TargetType:    ScopeTargetTypeWildcard,
		TargetValue:   "*.example.com",
		ActionClasses: []string{"harmless_request"},
		Conditions: ScopeConditions{
			Port:       "8443",
			MaxUses:    3,
			ValidUntil: &validUntil,
		},
		Provenance: ScopeProvenance{
			Source:       "import",
			DecidedBy:    "operator",
			DecidedAt:    time.Now().UTC().Truncate(time.Second),
			EvidenceHash: "sha256:0000",
			Note:         "匯入測試",
		},
		Status:    ScopeTargetStatusActive,
		CreatedAt: time.Now().UTC(),
	}
	if err := UpsertScopeTarget(ctx, db, target); err != nil {
		t.Fatal(err)
	}

	// 同一個 id 再寫一次是覆寫（匯入 CLI 需要冪等）。
	target.ActionClasses = []string{"harmless_request", "credential_enum"}
	if err := UpsertScopeTarget(ctx, db, target); err != nil {
		t.Fatal(err)
	}

	list, err := ListScopeTargets(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 {
		t.Fatalf("應只有 1 筆，實際 %d", len(list))
	}
	got := list[0]
	if got.Owner != "client-a" || got.TargetType != ScopeTargetTypeWildcard {
		t.Fatalf("欄位未正確往返：%#v", got)
	}
	if len(got.ActionClasses) != 2 {
		t.Fatalf("action_classes 未正確往返：%v", got.ActionClasses)
	}
	if got.Conditions.Port != "8443" || got.Conditions.MaxUses != 3 {
		t.Fatalf("conditions 未正確往返：%#v", got.Conditions)
	}
	if got.Conditions.ValidUntil == nil || !got.Conditions.ValidUntil.Equal(validUntil) {
		t.Fatalf("conditions.valid_until 未正確往返：%v", got.Conditions.ValidUntil)
	}
	if got.Provenance.Source != "import" || got.Provenance.DecidedBy != "operator" {
		t.Fatalf("provenance 未正確往返：%#v", got.Provenance)
	}
}

func TestUpsertScopeTargetGeneratesID(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	target := ScopeTarget{
		Owner:       "self",
		TargetType:  ScopeTargetTypeHost,
		TargetValue: "example.com",
	}
	if err := UpsertScopeTarget(ctx, db, target); err != nil {
		t.Fatal(err)
	}
	list, err := ListScopeTargets(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].ID == "" {
		t.Fatalf("應自動產生 ID：%#v", list)
	}
}

func TestUpsertScopeTargetValidatesRequiredFields(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	if err := UpsertScopeTarget(ctx, db, ScopeTarget{
		TargetType:  ScopeTargetTypeHost,
		TargetValue: "example.com",
	}); err == nil {
		t.Fatal("缺 owner 時應報錯")
	}
	if err := UpsertScopeTarget(ctx, db, ScopeTarget{
		Owner:      "self",
		TargetValue: "example.com",
	}); err == nil {
		t.Fatal("缺 target_type 時應報錯")
	}
	if err := UpsertScopeTarget(ctx, db, ScopeTarget{
		Owner:      "self",
		TargetType: ScopeTargetTypeHost,
	}); err == nil {
		t.Fatal("缺 target_value 時應報錯")
	}
}

func TestRevokeScopeTargetHidesRow(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	if err := UpsertScopeTarget(ctx, db, ScopeTarget{
		ID:          "t-revoke",
		Owner:       "self",
		TargetType:  ScopeTargetTypeHost,
		TargetValue: "example.com",
	}); err != nil {
		t.Fatal(err)
	}
	if err := RevokeScopeTarget(ctx, db, "t-revoke"); err != nil {
		t.Fatal(err)
	}
	list, err := ListScopeTargets(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 0 {
		t.Fatalf("撤銷後不該再列出：%#v", list)
	}
	loaded, err := GetScopeTarget(ctx, db, "t-revoke")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Status != ScopeTargetStatusRevoked {
		t.Fatalf("狀態應為 revoked，實際 %q", loaded.Status)
	}
}

func TestCreateAndConsumeScopeGrant(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	grant := ScopeGrant{
		ID:            "g-1",
		TargetType:    ScopeTargetTypeHost,
		TargetValue:   "new.example.com",
		ActionClasses: []string{"harmless_request"},
		MaxUses:       2,
		IssuedBy:      "operator",
		Evidence:      "evidence-hash",
	}
	if err := CreateScopeGrant(ctx, db, grant); err != nil {
		t.Fatal(err)
	}

	loaded, err := GetScopeGrant(ctx, db, "g-1")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.MaxUses != 2 || loaded.UsesUsed != 0 {
		t.Fatalf("計數器不正確：%#v", loaded)
	}
	if len(loaded.ActionClasses) != 1 || loaded.ActionClasses[0] != "harmless_request" {
		t.Fatalf("action_classes 未正確往返：%v", loaded.ActionClasses)
	}

	// 第一次消耗：仍是 active。
	if err := ConsumeScopeGrant(ctx, db, "g-1"); err != nil {
		t.Fatal(err)
	}
	loaded, err = GetScopeGrant(ctx, db, "g-1")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.UsesUsed != 1 || loaded.Status != ScopeGrantStatusActive {
		t.Fatalf("第一次消耗後狀態不正確：%#v", loaded)
	}

	// 第二次消耗：用盡。
	if err := ConsumeScopeGrant(ctx, db, "g-1"); err != nil {
		t.Fatal(err)
	}
	loaded, err = GetScopeGrant(ctx, db, "g-1")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.UsesUsed != 2 || loaded.Status != ScopeGrantStatusExhausted {
		t.Fatalf("用盡後狀態不正確：%#v", loaded)
	}

	// 用盡後不能再消耗。
	if err := ConsumeScopeGrant(ctx, db, "g-1"); err == nil {
		t.Fatal("用盡的授權券不該再能消耗")
	}
}

func TestCreateScopeGrantDefaults(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	if err := CreateScopeGrant(ctx, db, ScopeGrant{
		TargetType:  ScopeTargetTypeHost,
		TargetValue: "new.example.com",
		IssuedBy:    "operator",
	}); err != nil {
		t.Fatal(err)
	}
	list, err := ListScopeGrants(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 {
		t.Fatalf("應有 1 張券：%#v", list)
	}
	if list[0].MaxUses != 1 {
		t.Fatalf("max_uses 預設應為 1，實際 %d", list[0].MaxUses)
	}
	if list[0].ID == "" {
		t.Fatal("應自動產生 ID")
	}
}

func TestRecordAndListScopeDenials(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	denial := ScopeDenial{
		Target:    "example.com",
		Owner:     "client-a",
		Reason:    "rejected",
		DecidedBy: "operator",
	}
	if err := RecordScopeDenial(ctx, db, denial); err != nil {
		t.Fatal(err)
	}
	// 同一目標再拒一次是更新（冪等）。
	denial.Reason = "rejected-again"
	denial.DecidedBy = "operator-2"
	if err := RecordScopeDenial(ctx, db, denial); err != nil {
		t.Fatal(err)
	}

	list, err := ListScopeDenials(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 {
		t.Fatalf("應只有 1 筆拒絕記錄：%#v", list)
	}
	if list[0].Reason != "rejected-again" || list[0].DecidedBy != "operator-2" {
		t.Fatalf("拒絕記錄未正確更新：%#v", list[0])
	}
	if list[0].DecidedAt.IsZero() {
		t.Fatal("decided_at 應有值")
	}

	if err := DeleteScopeDenial(ctx, db, "example.com"); err != nil {
		t.Fatal(err)
	}
	list, err = ListScopeDenials(ctx, db)
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 0 {
		t.Fatalf("刪除後應沒有記錄：%#v", list)
	}
}
