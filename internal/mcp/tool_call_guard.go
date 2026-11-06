package mcp

import (
	"context"

	"jysecai/internal/toolguard"
)

const toolGuardBlockedPrefix = toolguard.BlockedPrefix
const toolGuardBlockedMetaKey = toolguard.BlockedMetaKey

// ScopeResolver 回傳目前這次呼叫所屬對話的專案授權範圍。
//
// 回傳 nil 代表這次呼叫不套用任何專案範圍（預設行為）。app 層在啟動時注入這個
// 回呼：internal/mcp 不得 import internal/database（會造成 import cycle），所以
// 「這次呼叫屬於哪個專案」必須由外面送進來。
type ScopeResolver func(ctx context.Context) *toolguard.TargetScope

// toolGuardBlockError carries structured policy results through pre-run hooks.
type toolGuardBlockError struct{ result *ToolResult }

func (e *toolGuardBlockError) Error() string { return ToolResultPlainText(e.result) }

func toolResultProtocolMeta(result *ToolResult) map[string]interface{} {
	if result != nil && result.Blocked {
		return map[string]interface{}{toolGuardBlockedMetaKey: true}
	}
	return nil
}

// toolGuardBlockedResult uses the standard MCP error result so the refusal is
// visible both to the model and in persisted execution monitoring records.
func toolGuardBlockedResult(guard *toolguard.Manager, toolName string, args map[string]interface{}, scope *toolguard.TargetScope) *ToolResult {
	if guard == nil {
		return nil
	}
	match := guard.CheckScoped(toolName, args, scope)
	if match == nil {
		return nil
	}
	return &ToolResult{Content: []Content{{Type: "text", Text: toolguard.RefusalMessage(match)}}, IsError: true, Blocked: true}
}
