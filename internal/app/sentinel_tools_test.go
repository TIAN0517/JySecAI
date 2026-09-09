package app

import (
	"context"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/authctx"
	"jysecai/internal/database"
	"jysecai/internal/handler"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"
	"jysecai/internal/sentinel"

	"go.uber.org/zap"
)

func setupSentinelToolsTest(t *testing.T) (*database.DB, *mcp.Server, *handler.SentinelHandler, string, context.Context) {
	t.Helper()
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "sentinel-tools-test.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	user, err := db.CreateRBACUser("sentinel-tester", "Sentinel Tester", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	principal := authctx.NewPrincipal(user.ID, user.Username, database.RBACScopeAll, map[string]bool{
		"asset:read": true, "asset:write": true, "vulnerability:read": true, "vulnerability:write": true,
	})
	ctx := authctx.WithPrincipal(context.Background(), principal)

	conversation, err := db.CreateConversation("sentinel conv", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}

	sentinelHandler := handler.NewSentinelHandler(db, zap.NewNop())
	server := mcp.NewServer(zap.NewNop())
	server.SetToolAuthorizer(mcpToolAuthorizer(db))
	registerSentinelTools(server, db, sentinelHandler, zap.NewNop())

	return db, server, sentinelHandler, conversation.ID, mcp.WithMCPConversationID(ctx, conversation.ID)
}

func TestSentinelToolsLifecycle(t *testing.T) {
	db, server, _, _, ctx := setupSentinelToolsTest(t)

	// 預先寫入一筆完成的探測快照供測試
	snap := &sentinel.ScanSnapshot{
		ID:         "test-sentinel-mcp-01",
		Target:     "example.com",
		TargetKind: "domain",
		Status:     "completed",
		CreatedAt:  time.Now().Add(-5 * time.Minute),
		FinishedAt: time.Now().Format(time.RFC3339),
		DurationMs: 3500,
		Summary: sentinel.ScanSummary{
			HostCount:     2,
			AliveCount:    2,
			OpenPortCount: 3,
			DatabaseCount: 1,
			HighCount:     1,
			MediumCount:   1,
		},
		Assets: []sentinel.AssetItem{
			{ID: "a1", Host: "example.com", IP: "93.184.216.34", Scope: "official", Alive: true, Title: "Example Domain"},
			{ID: "a2", Host: "api.example.com", IP: "93.184.216.35", Scope: "product", Alive: true, Title: "Example API"},
		},
		Ports: []sentinel.PortItem{
			{ID: "p1", Host: "example.com", IP: "93.184.216.34", Port: 80, Service: "http"},
			{ID: "p2", Host: "example.com", IP: "93.184.216.34", Port: 443, Service: "https"},
			{ID: "p3", Host: "example.com", IP: "93.184.216.34", Port: 6379, Service: "redis"},
		},
		Databases: []sentinel.DatabaseItem{
			{ID: "d1", EngineID: "redis", EngineName: "Redis", Host: "example.com", Port: 6379, Risk: "unauth", Evidence: "+PONG"},
		},
		Findings: []sentinel.FindingItem{
			{ID: "f1", Severity: "high", Category: "database", Host: "example.com", Title: "Redis 未授权访问 / 暴露在公网", Detail: "Redis 端口 6379 可直接握手免密交互"},
			{ID: "f2", Severity: "medium", Category: "port", Host: "example.com", Title: "开放非常规运维端口", Detail: "8080 端口暴露"},
		},
	}
	if err := db.SaveSentinelScan(snap); err != nil {
		t.Fatal(err)
	}

	// 1. 測試 get_sentinel_scan (留空 scan_id 應自動取得最新快照)
	res1, _, err := server.CallTool(ctx, builtin.ToolGetSentinelScan, map[string]interface{}{})
	if err != nil {
		t.Fatalf("call get_sentinel_scan failed: %v", err)
	}
	if res1.IsError {
		t.Fatalf("get_sentinel_scan returned error: %s", res1.Content[0].Text)
	}
	text1 := res1.Content[0].Text
	if !strings.Contains(text1, "example.com") || !strings.Contains(text1, "Redis") {
		t.Errorf("expected snapshot report to mention example.com and Redis, got: %s", text1)
	}

	// 2. 測試 sentinel_sync_assets (同步快照資產至系統資產庫)
	res2, _, err := server.CallTool(ctx, builtin.ToolSentinelSyncAssets, map[string]interface{}{
		"scan_id": "test-sentinel-mcp-01",
	})
	if err != nil {
		t.Fatalf("call sentinel_sync_assets failed: %v", err)
	}
	if res2.IsError {
		t.Fatalf("sentinel_sync_assets returned error: %s", res2.Content[0].Text)
	}
	text2 := res2.Content[0].Text
	if !strings.Contains(text2, "新建立資產數") {
		t.Errorf("expected asset sync summary, got: %s", text2)
	}

	// 3. 測試 sentinel_sync_vulnerabilities (同步高/中危風險至漏洞庫)
	res3, _, err := server.CallTool(ctx, builtin.ToolSentinelSyncVulnerabilities, map[string]interface{}{
		"scan_id": "test-sentinel-mcp-01",
	})
	if err != nil {
		t.Fatalf("call sentinel_sync_vulnerabilities failed: %v", err)
	}
	if res3.IsError {
		t.Fatalf("sentinel_sync_vulnerabilities returned error: %s", res3.Content[0].Text)
	}
	text3 := res3.Content[0].Text
	if !strings.Contains(text3, "**新建立漏洞記錄**: 2 條") {
		t.Errorf("expected 2 vulns created, got: %s", text3)
	}

	// 重複同步應觸發自動去重
	res3Dup, _, err := server.CallTool(ctx, builtin.ToolSentinelSyncVulnerabilities, map[string]interface{}{
		"scan_id": "test-sentinel-mcp-01",
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(res3Dup.Content[0].Text, "**新建立漏洞記錄**: 0 條") || !strings.Contains(res3Dup.Content[0].Text, "**已存在/去重跳過**: 2 條") {
		t.Errorf("expected 0 created and 2 skipped on duplicate sync, got: %s", res3Dup.Content[0].Text)
	}

	// 4. 測試 sentinel_scan 異步發起模式 (wait=false)
	res4, _, err := server.CallTool(ctx, builtin.ToolSentinelScan, map[string]interface{}{
		"target": "example.com",
		"wait":   false,
	})
	if err != nil {
		t.Fatalf("call sentinel_scan async failed: %v", err)
	}
	if res4.IsError {
		t.Fatalf("sentinel_scan async returned error: %s", res4.Content[0].Text)
	}
	if !strings.Contains(res4.Content[0].Text, "已成功在後台發起暴露面探測任務") {
		t.Errorf("expected async notice, got: %s", res4.Content[0].Text)
	}
}
