package app

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"cyberstrike-ai/internal/authctx"
	"cyberstrike-ai/internal/config"
	"cyberstrike-ai/internal/database"
	"cyberstrike-ai/internal/mcp"
	"cyberstrike-ai/internal/mcp/builtin"

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
