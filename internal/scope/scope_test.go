package scope

import (
	"context"
	"database/sql"
	"encoding/json"
	"testing"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"jysecai/internal/database"
)

// 測試用固定時間：到期語意要可重現，不能依賴「現在」。
var testNow = time.Date(2026, 11, 2, 12, 0, 0, 0, time.UTC)

// newScopeTestDB 建立記憶體資料庫並套用 scope registry 的 schema。
//
// 刻意呼叫 database.EnsureScopeSchema（而不是在本檔重貼一份 DDL）：
// 兩邊共用同一份 schema 定義正是這兩個套件的契約，重貼一份只會讓欄位悄悄走鍰。
func newScopeTestDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	// 記憶體 SQLite 每條連線各自一個庫，限制成單一連線才不會出現「no such table」。
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { db.Close() })
	if err := database.EnsureScopeSchema(db); err != nil {
		t.Fatal(err)
	}
	return db
}

// insertTarget 寫入一筆常駐集授權。
func insertTarget(t *testing.T, db *sql.DB, id, owner, kind, value string, classes []string, conditions map[string]any, validUntil *time.Time) {
	t.Helper()
	insertTargetWindow(t, db, id, owner, kind, value, classes, conditions, nil, validUntil)
}

// insertTargetWindow 寫入一筆常駐集授權（可指定生效／到期時間）。
func insertTargetWindow(t *testing.T, db *sql.DB, id, owner, kind, value string, classes []string, conditions map[string]any, validFrom, validUntil *time.Time) {
	t.Helper()
	if classes == nil {
		classes = []string{}
	}
	classesJSON, err := json.Marshal(classes)
	if err != nil {
		t.Fatal(err)
	}
	conditionsJSON, err := json.Marshal(conditions)
	if err != nil {
		t.Fatal(err)
	}
	var from, until any
	if validFrom != nil {
		from = validFrom.UTC().Format(time.RFC3339Nano)
	}
	if validUntil != nil {
		until = validUntil.UTC().Format(time.RFC3339Nano)
	}
	_, err = db.Exec(`
		INSERT INTO scope_targets (id, owner, target_type, target_value, action_classes,
		                           conditions, valid_from, valid_until, provenance, status, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', 'active', ?)`,
		id, owner, kind, value, string(classesJSON), string(conditionsJSON), from, until,
		testNow.Format(time.RFC3339Nano))
	if err != nil {
		t.Fatal(err)
	}
}

// insertGrant 寫入一張授權券。
func insertGrant(t *testing.T, db *sql.DB, id, kind, value string, classes []string, maxUses, usesUsed int, validUntil *time.Time, status string) {
	t.Helper()
	if classes == nil {
		classes = []string{}
	}
	classesJSON, err := json.Marshal(classes)
	if err != nil {
		t.Fatal(err)
	}
	var until any
	if validUntil != nil {
		until = validUntil.UTC().Format(time.RFC3339Nano)
	}
	_, err = db.Exec(`
		INSERT INTO scope_grants (id, target_type, target_value, action_classes, max_uses,
		                          uses_used, valid_until, issued_by, issued_at, evidence, status)
		VALUES (?, ?, ?, ?, ?, ?, ?, 'tester', ?, '', ?)`,
		id, kind, value, string(classesJSON), maxUses, usesUsed, until,
		testNow.Format(time.RFC3339Nano), status)
	if err != nil {
		t.Fatal(err)
	}
}

// coveredTargets 取 Covered 裡的目標鍵。
func coveredTargets(result Result) []string {
	out := make([]string, 0, len(result.Covered))
	for _, match := range result.Covered {
		out = append(out, match.Target.Key())
	}
	return out
}

// uncoveredTargets 取 Uncovered 裡的目標鍵。
func uncoveredTargets(result Result) []string {
	out := make([]string, 0, len(result.Uncovered))
	for _, target := range result.Uncovered {
		out = append(out, target.Key())
	}
	return out
}

// denialFor 找出某個目標的拒絕原因。
func denialFor(result Result, key string) string {
	for _, denial := range result.Denied {
		if denial.Target.Key() == key {
			return denial.Reason
		}
	}
	return ""
}

func TestResolveHostMatch(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-host", "self", "host", "example.com", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com", "other.example.com", "EXAMPLE.COM"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 2 {
		t.Fatalf("應命中 2 個目標，實際 %d：%v", len(result.Covered), coveredTargets(result))
	}
	if result.Covered[0].Target.Host != "example.com" {
		t.Fatalf("正規化後的主機應為 example.com，實際 %q", result.Covered[0].Target.Host)
	}
	if result.Covered[0].Source != SourceScopeTarget || result.Covered[0].GrantID != "t-host" {
		t.Fatalf("命中來源不正確：%#v", result.Covered[0])
	}
	if result.Covered[0].Owner != "self" {
		t.Fatalf("owner 應為 self，實際 %q", result.Covered[0].Owner)
	}
	if got := uncoveredTargets(result); len(got) != 1 || got[0] != "other.example.com" {
		t.Fatalf("未覆蓋清單不正確：%v", got)
	}
	if len(result.Denied) != 0 {
		t.Fatalf("不應有拒絕：%v", result.Denied)
	}
}

func TestResolveWildcardMatchesExactlyOneLabel(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-wild", "self", "wildcard", "*.example.com", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"api.example.com", "example.com", "a.b.example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if got := coveredTargets(result); len(got) != 1 || got[0] != "api.example.com" {
		t.Fatalf("wildcard 只應命中一層，實際：%v", got)
	}
	if got := uncoveredTargets(result); len(got) != 2 {
		t.Fatalf("example.com 與 a.b.example.com 都不應被涵蓋：%v", got)
	}
}

func TestResolveCIDRMatch(t *testing.T) {
	db := newScopeTestDB(t)
	// RFC 5737 測試網段，絕不碰真實位址。
	insertTarget(t, db, "t-cidr", "self", "cidr", "192.0.2.0/24", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"192.0.2.10", "198.51.100.10", "example.test"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if got := coveredTargets(result); len(got) != 1 || got[0] != "192.0.2.10" {
		t.Fatalf("CIDR 涵蓋結果不正確：%v", got)
	}
	if got := uncoveredTargets(result); len(got) != 2 {
		t.Fatalf("網段外的目標應為未覆蓋：%v", got)
	}
}

func TestResolveCIDRCoversWholeNetwork(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-cidr-wide", "self", "cidr", "192.0.2.0/24", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"192.0.2.128/25"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("授權網段應涵蓋子網段：%v", coveredTargets(result))
	}
}

func TestResolveURLPrefixMatch(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-url", "client", "url_prefix", "https://example.com/admin/", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(), []string{
		"https://example.com/admin/users",
		"https://example.com/admin",
		"https://example.com/administrator",
		"https://example.com/",
	}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	got := coveredTargets(result)
	if len(got) != 2 {
		t.Fatalf("URL 前綴應命中 admin 目錄及其子路徑，實際：%v", got)
	}
	for _, key := range got {
		if key != "https://example.com/admin" && key != "https://example.com/admin/users" {
			t.Fatalf("誤判命中：%s", key)
		}
	}
	if len(result.Uncovered) != 2 {
		t.Fatalf("其餘 URL 應為未覆蓋：%v", uncoveredTargets(result))
	}
}

func TestResolveHostScopeCoversURLTarget(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-host", "self", "host", "example.com", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"https://example.com/anything"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("主機授權應涵蓋同主機的 URL 目標：%v", coveredTargets(result))
	}
}

func TestResolvePortCondition(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-port", "self", "host", "example.com", nil,
		map[string]any{"port": "8443"}, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com:8443", "example.com", "example.com:443", "https://example.com:8443/x"},
		ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if got := coveredTargets(result); len(got) != 2 {
		t.Fatalf("只有 8443 埠位應被涵蓋：%v", got)
	}
}

func TestResolveExpiredTargetIsDeniedNotUncovered(t *testing.T) {
	db := newScopeTestDB(t)
	past := testNow.Add(-24 * time.Hour)
	insertTarget(t, db, "t-expired", "self", "host", "example.com", nil, nil, &past)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Uncovered) != 0 {
		t.Fatalf("到期授權不該算未覆蓋：%v", uncoveredTargets(result))
	}
	if reason := denialFor(result, "example.com"); reason != ReasonExpired {
		t.Fatalf("應回報 expired，實際 %q", reason)
	}
}

func TestResolveExpiredConditionExpiresEntry(t *testing.T) {
	db := newScopeTestDB(t)
	past := testNow.Add(-time.Hour)
	insertTarget(t, db, "t-cond-expired", "self", "host", "example.com", nil,
		map[string]any{"valid_until": past.UTC().Format(time.RFC3339Nano)}, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "example.com"); reason != ReasonExpired {
		t.Fatalf("應回報 expired，實際 %q", reason)
	}
}

func TestResolveNotYetValidIsExpired(t *testing.T) {
	db := newScopeTestDB(t)
	future := testNow.Add(time.Hour)
	// 尚未生效的授權：主機對、但現在還不能用。
	insertTargetWindow(t, db, "t-future", "self", "host", "example.com", nil, nil, &future, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "example.com"); reason != ReasonExpired {
		t.Fatalf("尚未生效的授權應回報 expired，實際 %q", reason)
	}
}

func TestResolveFutureExpiryIsStillValid(t *testing.T) {
	db := newScopeTestDB(t)
	future := testNow.Add(time.Hour)
	insertTarget(t, db, "t-future-end", "self", "host", "example.com", nil, nil, &future)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("未到期的授權應該有效：%v", result.Denied)
	}
}

func TestResolveGrantCoversAndConsumesSeparately(t *testing.T) {
	db := newScopeTestDB(t)
	insertGrant(t, db, "g-1", "host", "new.example.com", nil, 1, 0, nil, "active")
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"new.example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("授權券應覆蓋目標：%v", coveredTargets(result))
	}
	if result.Covered[0].Source != SourceScopeGrant || result.Covered[0].GrantID != "g-1" {
		t.Fatalf("命中來源不正確：%#v", result.Covered[0])
	}
	if result.Covered[0].Owner != "" {
		t.Fatalf("授權券不該有 owner：%q", result.Covered[0].Owner)
	}

	// Resolve 本身不扣次數（判定與消耗是兩個動作）。
	var usesUsed int
	if err := db.QueryRow(`SELECT uses_used FROM scope_grants WHERE id = 'g-1'`).Scan(&usesUsed); err != nil {
		t.Fatal(err)
	}
	if usesUsed != 0 {
		t.Fatalf("Resolve 不該消耗授權券，uses_used = %d", usesUsed)
	}

	if err := service.ConsumeGrant(context.Background(), "g-1"); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRow(`SELECT uses_used FROM scope_grants WHERE id = 'g-1'`).Scan(&usesUsed); err != nil {
		t.Fatal(err)
	}
	if usesUsed != 1 {
		t.Fatalf("消耗後 uses_used 應為 1，實際 %d", usesUsed)
	}
}

func TestResolveExhaustedGrant(t *testing.T) {
	db := newScopeTestDB(t)
	insertGrant(t, db, "g-used", "host", "new.example.com", nil, 1, 1, nil, "active")
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"new.example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "new.example.com"); reason != ReasonExhausted {
		t.Fatalf("應回報 exhausted，實際 %q", reason)
	}
}

func TestResolveExpiredGrant(t *testing.T) {
	db := newScopeTestDB(t)
	past := testNow.Add(-time.Minute)
	insertGrant(t, db, "g-expired", "host", "new.example.com", nil, 3, 0, &past, "active")
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"new.example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "new.example.com"); reason != ReasonExpired {
		t.Fatalf("應回報 expired，實際 %q", reason)
	}
}

func TestConsumeGrantFailsWhenExhausted(t *testing.T) {
	db := newScopeTestDB(t)
	insertGrant(t, db, "g-once", "host", "new.example.com", nil, 1, 0, nil, "active")
	service := NewService(db)

	if err := service.ConsumeGrant(context.Background(), "g-once"); err != nil {
		t.Fatal(err)
	}
	if err := service.ConsumeGrant(context.Background(), "g-once"); err == nil {
		t.Fatal("用盡的授權券不該再能消耗")
	}
}

func TestActionClassAllowlistSemantics(t *testing.T) {
	db := newScopeTestDB(t)
	// 空 action_classes：只代表一般類別全部允許（設計 §3.1）。
	insertTarget(t, db, "t-general", "self", "host", "example.com", nil, nil, nil)
	service := NewService(db)

	general := []string{
		ActionLocalAnalysis,
		ActionOfflineReplay,
		ActionHarmlessRequest,
		ActionDBReadExtract,
	}
	for _, class := range general {
		result, err := service.Resolve(context.Background(),
			[]string{"example.com"}, class, testNow)
		if err != nil {
			t.Fatal(err)
		}
		if len(result.Covered) != 1 {
			t.Fatalf("一般類別 %s 應被允許：%v", class, result.Denied)
		}
		if len(result.Covered[0].ActionClasses) != len(general) {
			t.Fatalf("空 action_classes 應展開成四個一般類別，實際 %v", result.Covered[0].ActionClasses)
		}
	}

	explicit := []string{ActionCredentialEnum, ActionBulkScan, ActionArbitrary}
	for _, class := range explicit {
		result, err := service.Resolve(context.Background(),
			[]string{"example.com"}, class, testNow)
		if err != nil {
			t.Fatal(err)
		}
		if len(result.Covered) != 0 {
			t.Fatalf("%s 未明確列出時不該被允許", class)
		}
		if reason := denialFor(result, "example.com"); reason != ReasonActionClassNotAllowed {
			t.Fatalf("應回報 action_class_not_allowed，實際 %q", reason)
		}
	}
}

func TestActionClassRequiresExplicitListing(t *testing.T) {
	db := newScopeTestDB(t)
	insertTarget(t, db, "t-cred", "client", "host", "example.com",
		[]string{ActionCredentialEnum, ActionHarmlessRequest}, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionCredentialEnum, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("明確列出的類別應被允許：%v", result.Denied)
	}

	// 非空 action_classes 就是允許清單：未列出的類別不放行。
	result, err = service.Resolve(context.Background(),
		[]string{"example.com"}, ActionBulkScan, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if reason := denialFor(result, "example.com"); reason != ReasonActionClassNotAllowed {
		t.Fatalf("應回報 action_class_not_allowed，實際 %q", reason)
	}
}

func TestPermanentBlockedActionClasses(t *testing.T) {
	db := newScopeTestDB(t)
	// 就算 action_classes 明列了 destructive／real_transaction 也不會解鎖。
	insertTarget(t, db, "t-destructive", "self", "host", "example.com",
		[]string{ActionDestructive, ActionRealTransaction}, nil, nil)
	service := NewService(db)

	for _, class := range []string{ActionDestructive, ActionRealTransaction} {
		result, err := service.Resolve(context.Background(),
			[]string{"example.com"}, class, testNow)
		if err != nil {
			t.Fatal(err)
		}
		if len(result.Covered) != 0 {
			t.Fatalf("%s 屬永久封鎖，不該被授權", class)
		}
		if reason := denialFor(result, "example.com"); reason != ReasonPermanentBlock {
			t.Fatalf("應回報 permanent_block，實際 %q", reason)
		}
	}
}

func TestGrantWithoutActionClassCannotAuthorizeSensitiveClass(t *testing.T) {
	db := newScopeTestDB(t)
	insertGrant(t, db, "g-scope", "host", "new.example.com", nil, 1, 0, nil, "active")
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"new.example.com"}, ActionCredentialEnum, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("空 action_classes 的授權券不該授權 credential_enum")
	}
	if reason := denialFor(result, "new.example.com"); reason != ReasonActionClassNotAllowed {
		t.Fatalf("應回報 action_class_not_allowed，實際 %q", reason)
	}
}

func TestNormalizeTarget(t *testing.T) {
	cases := []struct {
		raw  string
		kind TargetType
		host string
		port string
		url  string
	}{
		{raw: "example.com", kind: TargetHost, host: "example.com"},
		{raw: "EXAMPLE.com.", kind: TargetHost, host: "example.com"},
		{raw: "example.com:8443", kind: TargetHost, host: "example.com", port: "8443"},
		{raw: "*.example.com", kind: TargetWildcard, host: "*.example.com"},
		{raw: "192.0.2.0/24", kind: TargetCIDR, host: "192.0.2.0/24"},
		{raw: "https://example.com/admin/", kind: TargetURLPrefix, host: "example.com",
			url: "https://example.com/admin/"},
		{raw: "https://example.com:8443/x", kind: TargetURLPrefix, host: "example.com",
			port: "8443", url: "https://example.com:8443/x"},
	}
	for _, tc := range cases {
		got := NormalizeTarget(tc.raw)
		if got.Kind != tc.kind || got.Host != tc.host || got.Port != tc.port || got.URL != tc.url {
			t.Fatalf("NormalizeTarget(%q) = %#v，期望 kind=%s host=%s port=%s url=%s",
				tc.raw, got, tc.kind, tc.host, tc.port, tc.url)
		}
	}
}

func TestTargetKeyIsStable(t *testing.T) {
	a := NormalizeTarget("https://Example.com:443/Admin")
	b := NormalizeTarget("https://example.com/Admin")
	if a.Key() != b.Key() {
		t.Fatalf("同一目標的 Key 應一致：%q vs %q", a.Key(), b.Key())
	}
}

// TestResolveWithoutSchemaFailsClosed：schema 沒建好時必須報錯，不能假裝「沒有授權」。
//
// 假裝「沒有授權」會讓呼叫端把目標當成未覆蓋而放行（或誤以為已被授權），
// 兩種都是安全上的錯向；直接報錯讓呼叫端 fail closed。
func TestResolveWithoutSchemaFailsClosed(t *testing.T) {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { db.Close() })

	service := NewService(db)
	if _, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow); err == nil {
		t.Fatal("schema 未建立時應回報錯誤（fail closed）")
	}
}

func TestResolveWithoutServiceFailsClosed(t *testing.T) {
	var service *Service
	if _, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow); err == nil {
		t.Fatal("未初始化的服務應回報錯誤")
	}
}
