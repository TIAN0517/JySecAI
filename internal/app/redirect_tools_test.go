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

// TestRegisterRedirectToolsFollowsEnabledRule 確認註冊規則只有一條，且初次註冊與
// 熱套用後的重新註冊走的是同一條：enabled 為 true 或端點清單非空才提供工具。
func TestRegisterRedirectToolsFollowsEnabledRule(t *testing.T) {
	cases := []struct {
		name       string
		cfg        config.RedirectConfig
		registered bool
	}{
		{"完全没设定", config.RedirectConfig{}, false},
		{"只有开关", config.RedirectConfig{Enabled: true}, true},
		{"只有端点清单", config.RedirectConfig{URLs: []string{"https://97y.me/tjneJ"}}, true},
		{"开关关闭但清单有值", config.RedirectConfig{Enabled: false, URLs: []string{"https://97y.me/tjneJ"}}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			server := mcp.NewServer(zap.NewNop())
			cfg := &config.Config{Redirect: tc.cfg}
			registerRedirectTools(server, nil, cfg, zap.NewNop())

			found := false
			for _, tool := range server.GetAllTools() {
				if tool.Name == builtin.ToolRedirectProbe {
					found = true
				}
			}
			if found != tc.registered {
				t.Fatalf("redirect_probe registered = %v, want %v", found, tc.registered)
			}
		})
	}
}

// TestRegisterRedirectToolsUnregistersWhenDisabled 確認把端點清單清掉之後，
// 工具會被下架，而不是留著一個沒有端點可用的空殼。
func TestRegisterRedirectToolsUnregistersWhenDisabled(t *testing.T) {
	server := mcp.NewServer(zap.NewNop())
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{"https://97y.me/tjneJ"}}}
	registerRedirectTools(server, nil, cfg, zap.NewNop())

	found := false
	for _, tool := range server.GetAllTools() {
		if tool.Name == builtin.ToolRedirectProbe {
			found = true
		}
	}
	if !found {
		t.Fatal("redirect_probe was not registered")
	}

	cfg.Redirect = config.RedirectConfig{}
	registerRedirectTools(server, nil, cfg, zap.NewNop())
	for _, tool := range server.GetAllTools() {
		if tool.Name == builtin.ToolRedirectProbe {
			t.Fatal("redirect_probe is still registered after the endpoint list was cleared")
		}
	}
}

// TestRedirectProbeToolReportsReflection 走一次完整的工具呼叫：目標 302 跳向受控端點，
// 工具必須讀回 Location 並判定為命中，而且不能跟著跳轉過去。
func TestRedirectProbeToolReportsReflection(t *testing.T) {
	var finalHits int
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/final" {
			finalHits++
			w.WriteHeader(http.StatusOK)
			return
		}
		w.Header().Set("Location", "https://97y.me/tjneJ/steal")
		w.WriteHeader(http.StatusFound)
	}))
	defer server.Close()

	mcpServer := mcp.NewServer(zap.NewNop())
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{"https://97y.me/tjneJ"}}}
	registerRedirectTools(mcpServer, nil, cfg, zap.NewNop())

	result, _, err := mcpServer.CallTool(context.Background(), builtin.ToolRedirectProbe, map[string]interface{}{
		"target_url": server.URL + "/go",
		"param":      "next",
	})
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result.IsError {
		t.Fatalf("tool returned an error: %s", toolResultText(result))
	}
	text := toolResultText(result)
	if !strings.Contains(text, "已回連") {
		t.Fatalf("tool output does not report the callback:\n%s", text)
	}
	if !strings.Contains(text, "https://97y.me/tjneJ/steal") {
		t.Fatalf("tool output does not include the Location header:\n%s", text)
	}
	if finalHits != 0 {
		t.Fatalf("tool followed the redirect (%d hits on /final)", finalHits)
	}
}

// TestRedirectProbeToolWritesBackToVulnerability 確認帶 vulnerability_id 時，
// 結果會被寫進該筆漏洞的證據與複測紀錄。
func TestRedirectProbeToolWritesBackToVulnerability(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "redirect.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	vuln, err := db.CreateVulnerability(&database.Vulnerability{
		Title:      "开放式跳转",
		Severity:   "medium",
		Status:     database.VulnerabilityStatusOpen,
		Target:     "https://victim.example/go",
		Evidence:   "原始证据",
		ReproSteps: "1. 访问 /go",
	})
	if err != nil {
		t.Fatal(err)
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Location", "https://97y.me/tjneJ/steal")
		w.WriteHeader(http.StatusFound)
	}))
	defer server.Close()

	mcpServer := mcp.NewServer(zap.NewNop())
	mcpServer.SetToolAuthorizer(mcpToolAuthorizer(db))
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{"https://97y.me/tjneJ"}}}
	registerRedirectTools(mcpServer, db, cfg, zap.NewNop())

	principal := authctx.NewPrincipal("admin", "admin", database.RBACScopeAll, map[string]bool{
		"agent:execute":       true,
		"vulnerability:read":  true,
		"vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	result, _, err := mcpServer.CallTool(ctx, builtin.ToolRedirectProbe, map[string]interface{}{
		"target_url":       server.URL + "/go",
		"param":            "next",
		"vulnerability_id": vuln.ID,
	})
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result.IsError {
		t.Fatalf("tool returned an error: %s", toolResultText(result))
	}

	updated, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatalf("GetVulnerability: %v", err)
	}
	if !strings.Contains(updated.Evidence, "受控跳轉複測") {
		t.Fatalf("evidence was not appended:\n%s", updated.Evidence)
	}
	if !strings.Contains(updated.Evidence, "原始证据") {
		t.Fatalf("the original evidence was dropped:\n%s", updated.Evidence)
	}
	if !strings.Contains(updated.RetestNotes, "受控跳轉複測") {
		t.Fatalf("retest notes were not appended:\n%s", updated.RetestNotes)
	}
}

// TestRedirectProbeToolRejectsUnauthorizedWrite 確認沒有漏洞寫入權限時不會改動紀錄。
func TestRedirectProbeToolRejectsUnauthorizedWrite(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "redirect.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	vuln, err := db.CreateVulnerability(&database.Vulnerability{
		Title:    "开放式跳转",
		Severity: "medium",
		Status:   database.VulnerabilityStatusOpen,
		Evidence: "原始证据",
	})
	if err != nil {
		t.Fatal(err)
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Location", "https://97y.me/tjneJ/steal")
		w.WriteHeader(http.StatusFound)
	}))
	defer server.Close()

	mcpServer := mcp.NewServer(zap.NewNop())
	mcpServer.SetToolAuthorizer(mcpToolAuthorizer(db))
	cfg := &config.Config{Redirect: config.RedirectConfig{Enabled: true, URLs: []string{"https://97y.me/tjneJ"}}}
	registerRedirectTools(mcpServer, db, cfg, zap.NewNop())

	principal := authctx.NewPrincipal("reader", "reader", database.RBACScopeAll, map[string]bool{
		"agent:execute":      true,
		"vulnerability:read": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	_, _, err = mcpServer.CallTool(ctx, builtin.ToolRedirectProbe, map[string]interface{}{
		"target_url":       server.URL + "/go",
		"param":            "next",
		"vulnerability_id": vuln.ID,
	})
	if err == nil {
		t.Fatal("expected the authorizer to deny the write")
	}
	if !strings.Contains(err.Error(), "vulnerability:write") {
		t.Fatalf("unexpected error: %v", err)
	}

	updated, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatalf("GetVulnerability: %v", err)
	}
	if updated.Evidence != "原始证据" {
		t.Fatalf("evidence was modified without permission:\n%s", updated.Evidence)
	}
}
