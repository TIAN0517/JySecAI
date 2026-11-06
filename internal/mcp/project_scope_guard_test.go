package mcp

import (
	"context"
	"strings"
	"testing"

	"jysecai/internal/toolguard"

	"go.uber.org/zap"
)

// 專案授權範圍注入攔截層的測試。

func TestToolGuardAppliesInjectedProjectScope(t *testing.T) {
	storage := newInMemoryMonitorStorage()
	server := NewServerWithStorage(zap.NewNop(), storage)
	server.SetToolGuard(testToolGuard(t, true))

	scope, err := toolguard.NewTargetScope(
		&toolguard.Scope{Domains: []string{"agency.gov.cn"}},
		nil,
	)
	if err != nil {
		t.Fatal(err)
	}
	server.SetProjectScopeResolver(func(context.Context) *toolguard.TargetScope {
		return scope
	})

	var calls int
	server.RegisterTool(Tool{Name: "scan"}, func(context.Context, map[string]interface{}) (*ToolResult, error) {
		calls++
		return &ToolResult{Content: []Content{{Type: "text", Text: "ok"}}}, nil
	})

	result, _, err := server.CallTool(context.Background(), "scan", map[string]interface{}{
		"target": "https://agency.gov.cn/x",
	})
	if err != nil {
		t.Fatal(err)
	}
	if result == nil || !result.Blocked {
		t.Fatalf("expected the project scope to allow the authorized target, got %#v", result)
	}
	if calls != 0 {
		t.Fatalf("handler must not run, calls=%d", calls)
	}
}

func TestToolGuardWithoutResolverKeepsBehaviour(t *testing.T) {
	storage := newInMemoryMonitorStorage()
	server := NewServerWithStorage(zap.NewNop(), storage)
	server.SetToolGuard(testToolGuard(t, true))
	// 沒有注入 resolver：行為必須與原本完全一致（政府目標照樣被擋）。

	var calls int
	server.RegisterTool(Tool{Name: "scan"}, func(context.Context, map[string]interface{}) (*ToolResult, error) {
		calls++
		return &ToolResult{Content: []Content{{Type: "text", Text: "ok"}}}, nil
	})

	result, _, err := server.CallTool(context.Background(), "scan", map[string]interface{}{
		"target": "https://agency.gov.cn/x",
	})
	if err != nil {
		t.Fatal(err)
	}
	if result == nil || !result.Blocked {
		t.Fatalf("expected the government rule to block, got %#v", result)
	}
	if calls != 0 {
		t.Fatalf("handler must not run, calls=%d", calls)
	}
}

func TestToolGuardProjectScopeDenyBlocksTarget(t *testing.T) {
	storage := newInMemoryMonitorStorage()
	server := NewServerWithStorage(zap.NewNop(), storage)
	server.SetToolGuard(testToolGuard(t, true))

	scope, err := toolguard.NewTargetScope(nil, &toolguard.Scope{Domains: []string{"legacy.gov.cn"}})
	if err != nil {
		t.Fatal(err)
	}
	server.SetProjectScopeResolver(func(context.Context) *toolguard.TargetScope {
		return scope
	})

	server.RegisterTool(Tool{Name: "scan"}, func(context.Context, map[string]interface{}) (*ToolResult, error) {
		return &ToolResult{Content: []Content{{Type: "text", Text: "ok"}}}, nil
	})

	result, _, err := server.CallTool(context.Background(), "scan", map[string]interface{}{
		"target": "https://legacy.gov.cn/x",
	})
	if err != nil {
		t.Fatal(err)
	}
	if result == nil || !result.Blocked {
		t.Fatalf("expected the project exclude list to block, got %#v", result)
	}
	if !strings.Contains(ToolResultPlainText(result), toolguard.ProjectScopeExcludeRuleID) {
		t.Fatalf("refusal should name the project exclude rule: %q", ToolResultPlainText(result))
	}
}
