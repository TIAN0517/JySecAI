package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// scopeimport 的匯入邏輯測試。
//
// 測試約束：不碰正式資料庫（用暫存 SQLite）；不對外送出任何網路請求。

// newImportTestDB 建立暫存資料庫。
func newImportTestDB(t *testing.T) *database.DB {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "scopeimport.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatalf("建立測試資料庫失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

// TestClassifyHost：host／wildcard／cidr／url_prefix 的分類。
func TestClassifyHost(t *testing.T) {
	cases := []struct {
		in        string
		wantType  string
		wantValue string
	}{
		{"example.com", database.ScopeTargetTypeHost, "example.com"},
		{"*.example.org", database.ScopeTargetTypeWildcard, "*.example.org"},
		{"192.0.2.10", database.ScopeTargetTypeHost, "192.0.2.10"},
		{"192.0.2.0/24", database.ScopeTargetTypeCIDR, "192.0.2.0/24"},
		{"https://example.net/path", database.ScopeTargetTypeURLPrefix, "https://example.net/path"},
	}
	for _, tc := range cases {
		gotType, gotValue := classifyHost(tc.in)
		if gotType != tc.wantType || gotValue != tc.wantValue {
			t.Fatalf("classifyHost(%q) = (%q, %q), want (%q, %q)",
				tc.in, gotType, gotValue, tc.wantType, tc.wantValue)
		}
	}
}

// TestParseAuthFileSupportsObjectAndArray：scopes 欄位支援物件與陣列兩種形狀。
func TestParseAuthFileSupportsObjectAndArray(t *testing.T) {
	objectForm := `{"version":1,"scopes":{"example.com":{"authorized":true,"allowed_hosts":["a.example.com"],"allowed_action_classes":["harmless_request"]}}}`
	entries, err := parseAuthFile([]byte(objectForm))
	if err != nil {
		t.Fatalf("解析物件格式失敗: %v", err)
	}
	if len(entries) != 1 || entries[0].Key != "example.com" {
		t.Fatalf("物件格式解析結果 = %+v", entries)
	}
	if len(entries[0].Scope.AllowedHosts) != 1 || entries[0].Scope.AllowedHosts[0] != "a.example.com" {
		t.Fatalf("allowed_hosts 解析錯誤: %+v", entries[0].Scope)
	}

	arrayForm := `{"version":1,"scopes":[{"authorized":true,"allowed_hosts":["b.example.com"]}]}`
	entries, err = parseAuthFile([]byte(arrayForm))
	if err != nil {
		t.Fatalf("解析陣列格式失敗: %v", err)
	}
	if len(entries) != 1 || len(entries[0].Scope.AllowedHosts) != 1 {
		t.Fatalf("陣列格式解析結果 = %+v", entries)
	}

	if _, err := parseAuthFile([]byte(`{"version":1}`)); err == nil {
		t.Fatal("缺少 scopes 欄位應該報錯")
	}
}

// TestImportSkipsForbiddenTargets：禁區目標一律跳過並警告，不寫進 registry。
func TestImportSkipsForbiddenTargets(t *testing.T) {
	entry := authScopeEntry{
		Key: "example-client",
		Scope: authScope{
			Authorized:            true,
			AllowedHosts:          []string{"app119.tfd.gov.tw", "example.com"},
			AllowedActionClasses:  []string{"harmless_request"},
			AuthorizedUntil:       "2026-12-01",
			AuthorizedBy:          "bossjy",
		},
	}
	targets, skipped, warnings := buildImportTargets(entry, "", "_授權.json")
	if skipped != 1 {
		t.Fatalf("禁區目標應跳過 1 筆，得到 %d", skipped)
	}
	if len(targets) != 1 || targets[0].TargetValue != "example.com" {
		t.Fatalf("只應留下非禁區目標，得到 %+v", targets)
	}
	joined := strings.Join(warnings, "\n")
	if !strings.Contains(joined, "禁區") {
		t.Fatalf("應該有禁區警告，得到 %q", joined)
	}
}

// TestImportSkipsUnauthorizedScopes：authorized=false 的 scope 不匯入。
func TestImportSkipsUnauthorizedScopes(t *testing.T) {
	entry := authScopeEntry{
		Key:   "not-authorized",
		Scope: authScope{Authorized: false, AllowedHosts: []string{"example.com"}},
	}
	targets, skipped, _ := buildImportTargets(entry, "", "_授權.json")
	if len(targets) != 0 {
		t.Fatalf("未授權的 scope 不該匯入，得到 %+v", targets)
	}
	if skipped != 1 {
		t.Fatalf("跳過筆數 = %d, want 1", skipped)
	}
}

// TestImportInvalidValidUntilDoesNotFailWholeFile：authorized_until 解析失敗只警告。
func TestImportInvalidValidUntilDoesNotFailWholeFile(t *testing.T) {
	entry := authScopeEntry{
		Key: "example-client",
		Scope: authScope{
			Authorized:           true,
			AllowedHosts:         []string{"example.com", "example.org"},
			AuthorizedUntil:      "不是時間",
			AllowedActionClasses: []string{"harmless_request"},
		},
	}
	targets, skipped, warnings := buildImportTargets(entry, "", "_授權.json")
	if len(targets) != 2 {
		t.Fatalf("時間壞掉不該讓整筆 scope 失敗，得到 %d 筆", len(targets))
	}
	if skipped != 0 {
		t.Fatalf("跳過筆數 = %d, want 0", skipped)
	}
	for _, target := range targets {
		if target.ValidUntil != nil {
			t.Fatalf("解析失敗時有效期限應留空，得到 %v", target.ValidUntil)
		}
	}
	if len(warnings) == 0 || !strings.Contains(strings.Join(warnings, "\n"), "authorized_until") {
		t.Fatalf("應該有時間解析警告，得到 %v", warnings)
	}
}

// TestImportIsIdempotent：同一份來源重跑不會產生重複列。
func TestImportIsIdempotent(t *testing.T) {
	db := newImportTestDB(t)
	entry := authScopeEntry{
		Key: "example-client",
		Scope: authScope{
			Authorized:           true,
			AllowedHosts:         []string{"example.com", "*.example.org"},
			AllowedActionClasses: []string{"harmless_request"},
			AuthorizedUntil:      "2026-12-01",
			AuthorizedBy:         "bossjy",
		},
	}
	targets, _, _ := buildImportTargets(entry, "", "_授權.json")
	if len(targets) != 2 {
		t.Fatalf("應產生 2 筆匯入項目，得到 %d", len(targets))
	}

	for round := 0; round < 2; round++ {
		for _, target := range targets {
			if err := database.UpsertScopeTarget(context.Background(), db, database.ScopeTarget{
				ID:            target.ID,
				Owner:         target.Owner,
				TargetType:    target.TargetType,
				TargetValue:   target.TargetValue,
				ActionClasses: target.ActionClasses,
				Conditions:    database.ScopeConditions{},
				ValidUntil:    target.ValidUntil,
				Provenance:    target.Provenance,
				Status:        database.ScopeTargetStatusActive,
				CreatedAt:     time.Now(),
			}); err != nil {
				t.Fatalf("第 %d 輪寫入失敗: %v", round+1, err)
			}
		}
	}

	var count int
	if err := db.QueryRow(`SELECT COUNT(*) FROM scope_targets`).Scan(&count); err != nil {
		t.Fatalf("統計失敗: %v", err)
	}
	if count != 2 {
		t.Fatalf("重跑後應維持 2 筆，得到 %d", count)
	}
	// 冪等鍵相同時 ID 也相同（upsert 靠它收斂）。
	if scopeTargetID("example-client", "host", "example.com") != scopeTargetID("example-client", "host", "example.com") {
		t.Fatal("冪等鍵推導出的 ID 必須穩定")
	}
	if scopeTargetID("example-client", "host", "example.com") == scopeTargetID("other", "host", "example.com") {
		t.Fatal("不同 owner 應該推導出不同 ID")
	}
}

// TestImportOwnerOverride：--owner 覆寫 owner。
func TestImportOwnerOverride(t *testing.T) {
	entry := authScopeEntry{
		Key:   "example-client",
		Scope: authScope{Authorized: true, AllowedHosts: []string{"example.com"}},
	}
	targets, _, _ := buildImportTargets(entry, "forced-owner", "_授權.json")
	if len(targets) != 1 || targets[0].Owner != "forced-owner" {
		t.Fatalf("--owner 應覆寫 owner，得到 %+v", targets)
	}
	targets, _, _ = buildImportTargets(entry, "", "_授權.json")
	if len(targets) != 1 || targets[0].Owner != "example-client" {
		t.Fatalf("未指定 --owner 時應用 scope 鍵，得到 %+v", targets)
	}
}

// TestImportProvenanceRecordsSource：provenance.source 記錄來源檔名。
func TestImportProvenanceRecordsSource(t *testing.T) {
	entry := authScopeEntry{
		Key:   "example-client",
		Scope: authScope{Authorized: true, AllowedHosts: []string{"example.com"}, AuthorizedBy: "bossjy"},
	}
	targets, _, _ := buildImportTargets(entry, "", "_授權.json")
	if len(targets) != 1 {
		t.Fatalf("應產生 1 筆，得到 %d", len(targets))
	}
	if targets[0].Provenance.Source != "_授權.json" {
		t.Fatalf("provenance.source = %q, want _授權.json", targets[0].Provenance.Source)
	}
	if targets[0].Provenance.DecidedBy != "bossjy" {
		t.Fatalf("provenance.decided_by = %q, want bossjy", targets[0].Provenance.DecidedBy)
	}
}

// TestParseValidUntilFormats：有效期限支援 RFC3339 與日期格式。
func TestParseValidUntilFormats(t *testing.T) {
	for _, raw := range []string{"2026-12-01T12:52:32+08:00", "2026-12-01"} {
		if _, err := parseValidUntil(raw); err != nil {
			t.Fatalf("parseValidUntil(%q) 失敗: %v", raw, err)
		}
	}
	if _, err := parseValidUntil("明天"); err == nil {
		t.Fatal("不支援的格式應該報錯")
	}
}

// TestCollectSourcesAcceptsDirectory：來源可以是目錄（會匯入目錄內所有 *.json）。
func TestCollectSourcesAcceptsDirectory(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "a.json"), []byte("{}"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "b.txt"), []byte("{}"), 0o600); err != nil {
		t.Fatal(err)
	}
	sources, err := collectSources(dir, nil)
	if err != nil {
		t.Fatalf("collectSources 失敗: %v", err)
	}
	if len(sources) != 1 || !strings.HasSuffix(sources[0], "a.json") {
		t.Fatalf("來源收集結果 = %v", sources)
	}
}
