package app

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
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

func newPocGeneratorEnv(t *testing.T) (*database.DB, *mcp.Server, string, context.Context) {
	t.Helper()
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "poc-tools.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	user, err := db.CreateRBACUser("poc-agent", "POC Agent", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	principal := authctx.NewPrincipal(user.ID, user.Username, database.RBACScopeAssigned, map[string]bool{
		"vulnerability:read": true, "vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	conversation, err := db.CreateConversation("poc conv", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	if err := db.AssignResourceToUser(user.ID, "conversation", conversation.ID); err != nil {
		t.Fatal(err)
	}

	server := mcp.NewServer(zap.NewNop())
	server.SetToolAuthorizer(mcpToolAuthorizer(db))
	cfg := &config.Config{Database: config.DatabaseConfig{Path: filepath.Join(tmp, "data", "conversations.db")}}
	registerPocGeneratorTools(server, db, cfg, zap.NewNop())

	return db, server, conversation.ID, mcp.WithMCPConversationID(ctx, conversation.ID)
}

func TestGeneratePocDraftSingle(t *testing.T) {
	db, server, convID, ctx := newPocGeneratorEnv(t)

	vuln, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID,
		Title:          "/api/login SQL 注入测试",
		Description:    "登录接口存在可注入点",
		Severity:       "high",
		Type:           "SQL注入",
		Target:         "https://vps.xs1.ccwu.cc/api/login",
		ReproSteps:     "1. 发送请求 2. 观察响应",
		Impact:         "可绕过认证",
		Recommendation: "使用参数化查询",
	})
	if err != nil {
		t.Fatal(err)
	}

	outDir := filepath.Join(t.TempDir(), "poc_drafts")
	result, _, err := server.CallTool(ctx, builtin.ToolGeneratePocDraft, map[string]interface{}{
		"vulnerability_id": vuln.ID,
		"output_dir":       outDir,
	})
	if err != nil {
		t.Fatal(err)
	}
	text := toolResultText(result)
	if result.IsError {
		t.Fatalf("unexpected error result: %s", text)
	}

	expectedFile := pocFilenameFor(vuln)
	if _, err := os.Stat(filepath.Join(outDir, expectedFile)); err != nil {
		t.Fatalf("draft file not created: %v", err)
	}
	raw, err := os.ReadFile(filepath.Join(outDir, expectedFile))
	if err != nil {
		t.Fatal(err)
	}
	content := string(raw)
	for _, needle := range []string{"POC/EXP 草稿", "SQL 注入", expectedFile, "复现步骤"} {
		if !strings.Contains(content, needle) {
			t.Fatalf("draft missing %q in %s", needle, content)
		}
	}

	if !strings.Contains(text, vuln.ID) || !strings.Contains(text, outDir) {
		t.Fatalf("result missing id/outdir: %s", text)
	}

	// 默认回写 evidence
	updated, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(updated.Evidence, "[自动生成 POC/EXP 草稿] "+expectedFile) {
		t.Fatalf("evidence not updated: %q", updated.Evidence)
	}
}

func TestGeneratePocDraftBatchOnlyMissing(t *testing.T) {
	db, server, convID, ctx := newPocGeneratorEnv(t)

	withEvidence, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID, Title: "已有证据", Severity: "low", Type: "XSS",
		Evidence: ">= 有原始请求响应 ==",
	})
	if err != nil {
		t.Fatal(err)
	}
	missingEvidence, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID, Title: "缺证据", Severity: "high", Type: "RCE",
		ReproSteps: "发送 payload",
	})
	if err != nil {
		t.Fatal(err)
	}

	outDir := filepath.Join(t.TempDir(), "poc_drafts")
	result, _, err := server.CallTool(ctx, builtin.ToolGeneratePocDraft, map[string]interface{}{
		"output_dir": outDir,
		"limit":      20,
	})
	if err != nil {
		t.Fatal(err)
	}
	text := toolResultText(result)
	if result.IsError {
		t.Fatalf("unexpected error result: %s", text)
	}
	if strings.Contains(text, withEvidence.ID) {
		t.Fatalf("with-evidence vuln should be skipped: %s", text)
	}
	if !strings.Contains(text, missingEvidence.ID) {
		t.Fatalf("missing-evidence vuln should be processed: %s", text)
	}
}

func TestGeneratePocDraftUnauthorized(t *testing.T) {
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "poc-tools.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	user, err := db.CreateRBACUser("poc-agent-ro", "", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	principal := authctx.NewPrincipal(user.ID, "poc-agent-ro", database.RBACScopeAssigned, map[string]bool{})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	conversation, err := db.CreateConversation("poc conv", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	if err := db.AssignResourceToUser(user.ID, "conversation", conversation.ID); err != nil {
		t.Fatal(err)
	}

	server := mcp.NewServer(zap.NewNop())
	server.SetToolAuthorizer(mcpToolAuthorizer(db))
	registerPocGeneratorTools(server, db, &config.Config{Database: config.DatabaseConfig{Path: filepath.Join(tmp, "data", "conversations.db")}}, zap.NewNop())

	result, _, err := server.CallTool(mcp.WithMCPConversationID(ctx, conversation.ID), builtin.ToolGeneratePocDraft,
		map[string]interface{}{"vulnerability_id": "00000000-0000-0000-0000-000000000001"})
	if err == nil {
		t.Fatal("expected authorization error")
	}
	if !strings.Contains(err.Error(), "vulnerability:write") {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != nil {
		t.Fatalf("denied call should not produce result: %#v", result)
	}
}

func TestPocFilenameForAndMarkdown(t *testing.T) {
	v := &database.Vulnerability{
		ID: "abc-123", Title: "  /api/Login SQL注入!!  ",
	}
	name := pocFilenameFor(v)
	if strings.ContainsAny(name, " /!?") {
		t.Fatalf("filename contains unsafe chars: %s", name)
	}
	if !strings.HasPrefix(name, "abc-123-") || !strings.HasSuffix(name, ".md") {
		t.Fatalf("unexpected filename: %s", name)
	}

	md := buildPocDraftMarkdown(&database.Vulnerability{
		ID: "abc-123", Title: "测试漏洞", Severity: "high", Type: "SQL注入",
		ReproSteps: "- 发送请求\n- 观察响应",
	}, nil)
	for _, needle := range []string{"# POC/EXP 草稿", "草稿（未验证）", "1. 发送请求", "2. 观察响应"} {
		if !strings.Contains(md, needle) {
			t.Fatalf("markdown missing %q: %s", needle, md)
		}
	}
}

func TestRenderNumberedBlocks(t *testing.T) {
	got := renderNumberedBlocks("- step one\n- step two\n\n- step three")
	for _, want := range []string{"1. step one\n", "2. step two\n", "3. step three\n"} {
		if !strings.Contains(got, want) {
			t.Fatalf("numbered blocks missing %q: %q", want, got)
		}
	}
}

func TestVerifyPocTool(t *testing.T) {
	db, server, convID, ctx := newPocGeneratorEnv(t)

	// 建立 Mock HTTP 伺服器
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Server", "JySec-Mock/1.0")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"leak_info":"vulnerable_database_exposed_token"}`))
	}))
	defer mockServer.Close()

	// 建立待驗證漏洞
	vuln, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: convID,
		Title:          "Mock Information Leak",
		Status:         "open",
		Target:         mockServer.URL,
	})
	if err != nil {
		t.Fatal(err)
	}

	// 呼叫 verify_poc 工具
	res, _, err := server.CallTool(ctx, builtin.ToolVerifyPoc, map[string]interface{}{
		"vulnerability_id": vuln.ID,
		"match_string":     "vulnerable_database_exposed_token",
		"match_status":     200,
		"update_status":    true,
	})
	if err != nil {
		t.Fatalf("call verify_poc failed: %v", err)
	}
	if res.IsError {
		t.Fatalf("verify_poc returned error: %s", res.Content[0].Text)
	}

	text := res.Content[0].Text
	if !strings.Contains(text, "验证通过 (Vulnerability Confirmed)") {
		t.Errorf("expected confirmed result, got: %s", text)
	}
	if !strings.Contains(text, "漏洞库联动") {
		t.Errorf("expected db linkage update, got: %s", text)
	}

	// 檢驗資料庫狀態
	updated, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatal(err)
	}
	if updated.Status != "confirmed" {
		t.Errorf("expected status to be 'confirmed', got %q", updated.Status)
	}
	if !strings.Contains(updated.Evidence, "[JySecAI 在线验证通过]") {
		t.Errorf("expected evidence marker, got: %s", updated.Evidence)
	}
}
