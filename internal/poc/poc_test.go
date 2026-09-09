package poc

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestPocFilenameFor(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:    "vuln-12345",
		Title: "SQL Injection in /api/login?user=admin",
	}
	name := PocFilenameFor(vuln)
	if name == "" {
		t.Fatalf("expected non-empty filename")
	}
	if filepath.Ext(name) != ".md" {
		t.Fatalf("expected .md extension, got %s", name)
	}
}

func TestBuildPocDraftMarkdown(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:          "vuln-test",
		Title:       "Sample Command Injection",
		Severity:    "high",
		Status:      "open",
		Type:        "RCE",
		Target:      "https://example.com/exec",
		Description: "Target is vulnerable to command injection via ping utility",
		ReproSteps:  "Send POST /exec with cmd=;id",
		Evidence:    "uid=0(root) gid=0(root)",
		CreatedAt:   time.Now(),
	}

	md := BuildPocDraftMarkdown(vuln, nil)
	if len(md) == 0 {
		t.Fatalf("expected non-empty markdown")
	}
	if !containsStr(md, "Sample Command Injection") {
		t.Errorf("markdown missing title")
	}
	if !containsStr(md, "https://example.com/exec") {
		t.Errorf("markdown missing target")
	}
}

func TestGeneratePocDraft(t *testing.T) {
	tmpDir := t.TempDir()
	vuln := &database.Vulnerability{
		ID:       "vuln-unit-1",
		Title:    "Test Vulnerability Draft",
		Severity: "medium",
		Target:   "https://test.local",
	}

	res, err := GeneratePocDraft(nil, vuln, tmpDir, false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if res.Filename == "" {
		t.Fatalf("expected non-empty filename")
	}

	content, err := os.ReadFile(res.FullPath)
	if err != nil {
		t.Fatalf("failed to read generated file: %v", err)
	}
	if len(content) == 0 {
		t.Fatalf("generated file is empty")
	}
}

func containsStr(haystack, needle string) bool {
	return len(haystack) >= len(needle) && (haystack == needle || len(needle) == 0 || stringContains(haystack, needle))
}

func stringContains(s, substr string) bool {
	for i := 0; i+len(substr) <= len(s); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func TestHasPocDraftMarker(t *testing.T) {
	cases := []struct {
		evidence string
		expected bool
	}{
		{"", false},
		{"normal evidence text", false},
		{"> [自動生成 POC/EXP 草稿] poc_drafts/vuln-1.md", true},
		{"> [自动生成 POC/EXP 草稿] poc_drafts/vuln-2.md", true},
		{"prefix\n\n> [自動生成 POC/EXP 草稿] test.md\nsuffix", true},
		{"prefix\n\n> [自动生成 POC/EXP 草稿] test.md\nsuffix", true},
	}

	for _, c := range cases {
		got := HasPocDraftMarker(c.evidence)
		if got != c.expected {
			t.Errorf("HasPocDraftMarker(%q) = %v, want %v", c.evidence, got, c.expected)
		}
	}
}

func TestVerifyPoc(t *testing.T) {
	// 建立 Mock HTTP 伺服器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/vuln-test" {
			w.Header().Set("X-Powered-By", "MockEngine/2.0")
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status":"vulnerable","leak":"secret_token_12345"}`))
			return
		}
		if r.URL.Path == "/not-found" {
			w.WriteHeader(http.StatusNotFound)
			_, _ = w.Write([]byte(`404 Not Found`))
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	ctx := context.Background()

	// 1. 成功匹配 status, string, regex
	spec := &VerifyPocSpec{
		TargetURL:   server.URL + "/vuln-test",
		Method:      "GET",
		MatchStatus: 200,
		MatchString: "secret_token_12345",
		MatchRegex:  `"leak":"[a-z0-9_]+"`,
	}
	res, err := VerifyPoc(ctx, nil, spec, false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !res.Verified {
		t.Fatalf("expected verified=true, got false. Matched: %v, Error: %s", res.MatchedConditions, res.Error)
	}
	if len(res.MatchedConditions) != 3 {
		t.Errorf("expected 3 matched conditions, got %d: %v", len(res.MatchedConditions), res.MatchedConditions)
	}
	if res.StatusCode != 200 {
		t.Errorf("expected 200, got %d", res.StatusCode)
	}

	// 2. 匹配條件失敗測試
	specFail := &VerifyPocSpec{
		TargetURL:   server.URL + "/vuln-test",
		Method:      "GET",
		MatchStatus: 500, // 實際是 200
	}
	resFail, err := VerifyPoc(ctx, nil, specFail, false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resFail.Verified {
		t.Fatalf("expected verified=false for status mismatch")
	}

	// 3. 測試結合 DB 更新漏洞狀態與 Evidence
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "poc-verify-test.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	vuln := &database.Vulnerability{
		ID:        "vuln-verify-001",
		Title:     "Test Leak Vuln",
		Status:    "open",
		Target:    server.URL + "/vuln-test",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	if _, err := db.CreateVulnerability(vuln); err != nil {
		t.Fatal(err)
	}

	specDB := &VerifyPocSpec{
		VulnerabilityID: vuln.ID,
		MatchString:     "secret_token_12345",
	}
	resDB, err := VerifyPoc(ctx, db, specDB, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !resDB.Verified || !resDB.UpdatedVulnerability {
		t.Fatalf("expected verified=true and updated=true, got verified=%v, updated=%v", resDB.Verified, resDB.UpdatedVulnerability)
	}

	// 驗證 DB 狀態是否已改為 confirmed
	reloaded, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatal(err)
	}
	if reloaded.Status != "confirmed" {
		t.Errorf("expected status 'confirmed', got %q", reloaded.Status)
	}
	if !stringContains(reloaded.Evidence, "[JySecAI 在线验证通过]") {
		t.Errorf("expected evidence to contain verification marker, got %q", reloaded.Evidence)
	}
}
