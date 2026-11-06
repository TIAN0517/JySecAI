package security

import (
	"context"
	"errors"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/scope"

	"go.uber.org/zap"
)

// Scope Registry P1：攔截點 B（executor 層兜底）的行為測試。
//
// 測試約束：不對外送出任何真實網路請求；測試命令是本機的 echo。

// newScopeTestDB 建立帶 scope schema 的暫存資料庫。
func newScopeTestDB(t *testing.T) *database.DB {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "executor-scope.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatalf("建立測試資料庫失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

// scopeTestTools 是測試用工具（目標參數有宣告 target: true）。
func scopeTestTools() []config.ToolConfig {
	pos := 0
	return []config.ToolConfig{
		{
			Name:        "httpx",
			Command:     "echo",
			Enabled:     true,
			ActionClass: scope.ActionHarmlessRequest,
			Parameters: []config.ParameterConfig{
				{Name: "targets", Type: "string", Target: true, TargetKind: "mixed", Position: &pos},
			},
		},
	}
}

// newScopeExecutor 建立帶 scope 檢查器的執行器。
func newScopeExecutor(t *testing.T, tools []config.ToolConfig, service *scope.Service, mode string) *Executor {
	t.Helper()
	logger := zap.NewNop()
	executor := NewExecutor(&config.SecurityConfig{Tools: tools}, nil, logger)
	if mode != "" {
		executor.SetScopeGuard(NewRegistryScopeGuard(service, mode, logger))
	}
	return executor
}

// TestExecuteToolScopeNotCoveredFailsClosed：繞過 handler 直呼 executor，
// 未覆蓋的目標必須被擋下（fail closed）。
func TestExecuteToolScopeNotCoveredFailsClosed(t *testing.T) {
	db := newScopeTestDB(t)
	service := scope.NewService(db)
	executor := newScopeExecutor(t, scopeTestTools(), service, config.ScopeEnforcementEnforce)

	_, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "not-covered.example.org",
	})
	if err == nil {
		t.Fatal("未覆蓋的目標必須被拒絕（fail closed）")
	}
	var notCovered *ScopeNotCoveredError
	if !errors.As(err, &notCovered) {
		t.Fatalf("錯誤型別 = %T（%v），應該是 ScopeNotCoveredError", err, err)
	}
	if notCovered.ToolName != "httpx" {
		t.Fatalf("ToolName = %q", notCovered.ToolName)
	}
}

// TestExecuteToolScopeCoveredPasses：有授權 → 通過。
func TestExecuteToolScopeCoveredPasses(t *testing.T) {
	db := newScopeTestDB(t)
	if err := database.UpsertScopeTarget(context.Background(), db, database.ScopeTarget{
		ID:            "scope_allowed",
		Owner:         "example-client",
		TargetType:    database.ScopeTargetTypeHost,
		TargetValue:   "allowed.example.com",
		ActionClasses: []string{scope.ActionHarmlessRequest},
		Conditions:    database.ScopeConditions{},
		Provenance:    database.ScopeProvenance{Source: "test", DecidedBy: "test", DecidedAt: time.Now()},
		Status:        database.ScopeTargetStatusActive,
		CreatedAt:     time.Now(),
	}); err != nil {
		t.Fatalf("寫入授權失敗: %v", err)
	}

	service := scope.NewService(db)
	executor := newScopeExecutor(t, scopeTestTools(), service, config.ScopeEnforcementEnforce)

	result, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "allowed.example.com",
	})
	if err != nil {
		t.Fatalf("已授權的目標應該通過: %v", err)
	}
	if result == nil || result.IsError {
		t.Fatalf("工具應該執行成功，結果 = %+v", result)
	}
}

// TestExecuteToolScopeOffModeKeepsLegacyBehavior：off 模式 → 完全不影響既有行為。
func TestExecuteToolScopeOffModeKeepsLegacyBehavior(t *testing.T) {
	db := newScopeTestDB(t)
	service := scope.NewService(db)
	executor := newScopeExecutor(t, scopeTestTools(), service, config.ScopeEnforcementOff)

	result, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "not-covered.example.org",
	})
	if err != nil {
		t.Fatalf("off 模式不該阻擋: %v", err)
	}
	if result == nil || result.IsError {
		t.Fatalf("off 模式工具應該照常執行，結果 = %+v", result)
	}
}

// TestExecuteToolScopeAuditModeDoesNotBlock：audit 模式 → 只記錄不阻擋。
func TestExecuteToolScopeAuditModeDoesNotBlock(t *testing.T) {
	db := newScopeTestDB(t)
	service := scope.NewService(db)
	executor := newScopeExecutor(t, scopeTestTools(), service, config.ScopeEnforcementAudit)

	result, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "not-covered.example.org",
	})
	if err != nil {
		t.Fatalf("audit 模式不該阻擋: %v", err)
	}
	if result == nil || result.IsError {
		t.Fatalf("audit 模式工具應該照常執行，結果 = %+v", result)
	}
}

// TestExecuteToolScopeGrantIsConsumedAfterSuccess：用掉一次授權券之後，
// 同一張券不該再被當成有效授權。
func TestExecuteToolScopeGrantIsConsumedAfterSuccess(t *testing.T) {
	db := newScopeTestDB(t)
	if err := database.CreateScopeGrant(context.Background(), db, database.ScopeGrant{
		ID:            "grant_once",
		TargetType:    database.ScopeTargetTypeHost,
		TargetValue:   "once.example.com",
		ActionClasses: []string{scope.ActionHarmlessRequest},
		MaxUses:       1,
		IssuedBy:      "test",
		IssuedAt:      time.Now(),
		Status:        database.ScopeGrantStatusActive,
	}); err != nil {
		t.Fatalf("簽發授權券失敗: %v", err)
	}

	service := scope.NewService(db)
	executor := newScopeExecutor(t, scopeTestTools(), service, config.ScopeEnforcementEnforce)

	if _, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "once.example.com",
	}); err != nil {
		t.Fatalf("第一次執行應該通過: %v", err)
	}
	var usesUsed int
	var status string
	if err := db.QueryRow(`SELECT uses_used, status FROM scope_grants WHERE id='grant_once'`).Scan(&usesUsed, &status); err != nil {
		t.Fatalf("讀取授權券失敗: %v", err)
	}
	if usesUsed != 1 {
		t.Fatalf("uses_used = %d, want 1", usesUsed)
	}
	if status != database.ScopeGrantStatusExhausted {
		t.Fatalf("status = %q, want %q", status, database.ScopeGrantStatusExhausted)
	}

	// 第二次不該再通過（券已用盡）。
	if _, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "once.example.com",
	}); err == nil {
		t.Fatal("用盡的授權券不該再放行")
	}
}

// TestExecutorWithoutScopeGuardIsUnchanged：沒有注入檢查器時，行為完全不變。
func TestExecutorWithoutScopeGuardIsUnchanged(t *testing.T) {
	db := newScopeTestDB(t)
	_ = db
	executor := newScopeExecutor(t, scopeTestTools(), nil, "")
	if executor.ScopeGuard() != nil {
		t.Fatal("未注入時 ScopeGuard 應為 nil")
	}
	result, err := executor.ExecuteTool(context.Background(), "httpx", map[string]interface{}{
		"targets": "not-covered.example.org",
	})
	if err != nil {
		t.Fatalf("沒有檢查器時不該阻擋: %v", err)
	}
	if result == nil || result.IsError {
		t.Fatalf("工具應該照常執行，結果 = %+v", result)
	}
}
