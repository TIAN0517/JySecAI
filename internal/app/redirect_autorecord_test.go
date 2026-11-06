package app

import (
	"context"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/authctx"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"

	"go.uber.org/zap"
)

// TestRedirectProbeToolAutoRecordsConfirmedRedirect 釘死原本的行為：
// 驗證確認可跳轉之後，auto_record 就**必須**自動建立漏洞紀錄，
// 不因目標或受控端點是 127.0.0.1 而跳過。
//
// 為什麼不該用「目標是 loopback 就別上鍊」來擋自我測試：
// 「跳轉到 localhost」本身是真實的攻擊原語（把受害者導去他自己的
// 127.0.0.1:6379 之類的內部服務），任何以 loopback 為由的禁令都會誤殺
// 真實發現。測試 fixture 該自己清理，不該靠產品層加禁令。
func TestRedirectProbeToolAutoRecordsConfirmedRedirect(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "redirect-autorecord.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	const endpoint = "http://127.0.0.1:18099/landing"
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if target := r.URL.Query().Get("next"); target != "" {
			w.Header().Set("Location", target)
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	mcpServer := mcp.NewServer(zap.NewNop())
	mcpServer.SetToolAuthorizer(mcpToolAuthorizer(db))
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{endpoint}}}
	registerRedirectTools(mcpServer, db, cfg, zap.NewNop())

	principal := authctx.NewPrincipal("admin", "admin", database.RBACScopeAll, map[string]bool{
		"agent:execute":       true,
		"vulnerability:read":  true,
		"vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	result, _, err := mcpServer.CallTool(ctx, builtin.ToolRedirectProbe, map[string]interface{}{
		"target_url":  server.URL + "/go",
		"param":       "next",
		"auto_record": true,
	})
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result.IsError {
		t.Fatalf("tool returned an error: %s", toolResultText(result))
	}
	text := toolResultText(result)
	if !strings.Contains(text, "已自动建立") {
		t.Fatalf("the tool did not report an automatic record:\n%s", text)
	}

	vulns, err := db.ListVulnerabilities(50, 0, database.VulnerabilityListFilter{})
	if err != nil {
		t.Fatalf("ListVulnerabilities: %v", err)
	}
	if len(vulns) != 1 {
		t.Fatalf("expected exactly 1 vulnerability record, got %d", len(vulns))
	}
	if vulns[0].TypeCode != "open-redirect" {
		t.Fatalf("unexpected vulnerability type code: %q", vulns[0].TypeCode)
	}
	if vulns[0].Status != database.VulnerabilityStatusConfirmed {
		t.Fatalf("unexpected vulnerability status: %q", vulns[0].Status)
	}
	if !strings.Contains(vulns[0].Evidence, endpoint) {
		t.Fatalf("evidence does not carry the controlled endpoint:\n%s", vulns[0].Evidence)
	}
}

// TestRedirectProbeToolAutoRecordsBatchRedirect 批次模式（多筆目標）也要照樣自動上鍊。
func TestRedirectProbeToolAutoRecordsBatchRedirect(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "redirect-autorecord-batch.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	const endpoint = "http://127.0.0.1:18099/landing"
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if target := r.URL.Query().Get("next"); target != "" {
			w.Header().Set("Location", target)
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	mcpServer := mcp.NewServer(zap.NewNop())
	mcpServer.SetToolAuthorizer(mcpToolAuthorizer(db))
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{endpoint}}}
	registerRedirectTools(mcpServer, db, cfg, zap.NewNop())

	principal := authctx.NewPrincipal("admin", "admin", database.RBACScopeAll, map[string]bool{
		"agent:execute":       true,
		"vulnerability:read":  true,
		"vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	result, _, err := mcpServer.CallTool(ctx, builtin.ToolRedirectProbe, map[string]interface{}{
		"target_urls": []string{server.URL + "/go?next=/a", server.URL + "/go?next=/b"},
		"param":       "next",
		"auto_record": true,
	})
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result.IsError {
		t.Fatalf("tool returned an error: %s", toolResultText(result))
	}

	vulns, err := db.ListVulnerabilities(50, 0, database.VulnerabilityListFilter{})
	if err != nil {
		t.Fatalf("ListVulnerabilities: %v", err)
	}
	if len(vulns) != 2 {
		t.Fatalf("expected 2 vulnerability records, got %d", len(vulns))
	}
	for _, vuln := range vulns {
		if vuln.TypeCode != "open-redirect" {
			t.Fatalf("unexpected vulnerability type code: %q", vuln.TypeCode)
		}
		if vuln.Status != database.VulnerabilityStatusConfirmed {
			t.Fatalf("unexpected vulnerability status: %q", vuln.Status)
		}
	}
}
