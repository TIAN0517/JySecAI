package handler

import (
	"context"
	"fmt"
	"strings"
	"time"

	"jysecai/internal/agent"
	"jysecai/internal/agentfinalizer"
	"jysecai/internal/mcp"
	"jysecai/internal/multiagent"

	"go.uber.org/zap"
)

const finalizationAutoContinueMaxAttempts = 3
const finalizationPendingToolCancelWait = 2 * time.Second
const finalizationPendingToolCancelPoll = 50 * time.Millisecond
const finalizationPendingToolCancelNote = "Agent 迭代已结束，最终回复前自动终止未完成的工具执行"

func shouldAutoContinueAfterFinalization(d agentfinalizer.Decision, attempt int) bool {
	if d.Finalizable || d.Finalized {
		return false
	}
	if attempt >= finalizationAutoContinueMaxAttempts {
		return false
	}
	return d.CompletionReason == agentfinalizer.ReasonMissingEvidence
}

func (h *AgentHandler) tryAutoContinueAfterFinalization(
	taskCtx context.Context,
	conversationID string,
	result *multiagent.RunResult,
	decision agentfinalizer.Decision,
	executionIDs []string,
	attempt *int,
	curHistory *[]agent.ChatMessage,
	curFinalMessage *string,
	progressCallback func(eventType, message string, data interface{}),
) bool {
	if !shouldAutoContinueAfterFinalization(decision, *attempt) || result == nil || !multiagent.HasEinoResumeTrace(result) {
		return false
	}
	*attempt++
	h.persistEinoAgentTraceForResume(conversationID, result)
	if hist, err := h.loadHistoryFromAgentTrace(conversationID); err == nil && len(hist) > 0 {
		*curHistory = hist
	} else if h.logger != nil {
		h.logger.Warn("finalization auto-continue could not restore trace",
			zap.String("conversationId", conversationID),
			zap.Error(err))
		return false
	}
	// 将恢复约束作为本段临时输入，不写入用户消息。相比原样重跑，它会要求
	// Agent 读取真实错误、修正参数或改用安全替代方案，避免重复相同失败调用。
	*curFinalMessage = h.finalizationRecoveryInstruction(decision, *attempt, executionIDs)
	if progressCallback != nil {
		progressCallback("finalization_auto_continue", "最终回复检查尚未收敛，正在基于已有轨迹继续执行…", map[string]interface{}{
			"conversationId":      conversationID,
			"source":              "finalizer",
			"attempt":             *attempt,
			"maxAttempts":         finalizationAutoContinueMaxAttempts,
			"status":              decision.Status,
			"completionReason":    decision.CompletionReason,
			"missingChecks":       decision.MissingChecks,
			"pendingExecutionIds": decision.PendingExecutionIDs,
			"contextInjection":    true,
		})
	}
	select {
	case <-taskCtx.Done():
		return false
	case <-time.After(finalizationAutoContinueBackoff(*attempt)):
		return true
	}
}

func (h *AgentHandler) finalizationRecoveryInstruction(decision agentfinalizer.Decision, attempt int, executionIDs []string) string {
	failed, allTerminal := h.finalizationFailedExecutions(executionIDs)
	contextLine := "前一段尚未产生可验证的成功工具执行。"
	if allTerminal && len(failed) > 0 {
		contextLine = fmt.Sprintf("前一段共有 %d 个工具执行以失败、拦截、取消或超时结束。", len(failed))
	}
	return fmt.Sprintf(
		"[JySecAI 自动复原 %d/%d]\n%s 请读取轨迹中的实际工具错误并继续完成原任务：参数错误就修正；暂时性错误才有限重试；工具不可用则改用等价且安全的替代方案。不要无变化地重复同一失败调用，不要把失败写成成功，也不要绕过工具守卫或 HITL。缺失检查：%s",
		attempt, finalizationAutoContinueMaxAttempts, contextLine, strings.Join(decision.MissingChecks, "; "),
	)
}

func (h *AgentHandler) finalizationFailedExecutions(executionIDs []string) ([]*mcp.ToolExecution, bool) {
	ids := uniqueNonEmptyStrings(executionIDs)
	if h == nil || h.db == nil || len(ids) == 0 {
		return nil, false
	}
	failed := make([]*mcp.ToolExecution, 0, len(ids))
	for _, id := range ids {
		execution, err := h.db.GetToolExecution(id)
		if err != nil || execution == nil {
			return failed, false
		}
		switch strings.TrimSpace(execution.Status) {
		case mcp.ToolExecutionStatusFailed,
			mcp.ToolExecutionStatusBlocked,
			mcp.ToolExecutionStatusCancelled,
			mcp.ToolExecutionStatusHardTimeout,
			mcp.ToolExecutionStatusOrphaned:
			failed = append(failed, execution)
		default:
			return failed, false
		}
	}
	return failed, len(failed) == len(ids)
}

// finalizeExhaustedFailedExecutions closes a fully terminal failed run after
// bounded autonomous recovery. It delivers an explicit failure result instead
// of leaving a 24/7 job waiting for a human or presenting a false success.
func (h *AgentHandler) finalizeExhaustedFailedExecutions(decision agentfinalizer.Decision, attempt int, executionIDs []string, result *multiagent.RunResult) agentfinalizer.Decision {
	if decision.CompletionReason != agentfinalizer.ReasonMissingEvidence {
		return decision
	}
	if attempt < finalizationAutoContinueMaxAttempts && result != nil && multiagent.HasEinoResumeTrace(result) {
		return decision
	}
	failed, allTerminal := h.finalizationFailedExecutions(executionIDs)
	if !allTerminal || len(failed) == 0 {
		return decision
	}
	tools := make([]string, 0, len(failed))
	seen := make(map[string]struct{}, len(failed))
	for _, execution := range failed {
		name := strings.TrimSpace(execution.ToolName)
		if name == "" {
			name = "unknown-tool"
		}
		entry := name + " (" + strings.TrimSpace(execution.Status) + ")"
		if _, ok := seen[entry]; ok {
			continue
		}
		seen[entry] = struct{}{}
		tools = append(tools, entry)
	}
	decision.Finalizable = true
	decision.Finalized = true
	decision.Status = agentfinalizer.StatusFailed
	decision.CompletionReason = agentfinalizer.ReasonFailed
	decision.EvidenceVerified = false
	decision.MissingChecks = nil
	recoverySummary := fmt.Sprintf("系統已完成 %d 次有界自動復原", attempt)
	if attempt == 0 {
		recoverySummary = "本次執行沒有可安全續跑的 Agent 軌跡"
	}
	decision.FinalText = fmt.Sprintf("自動執行未完成：%d 筆工具執行皆以終止狀態結束，%s，未將失敗誤報為成功。失敗工具：%s。此輪已正常結束，不需人工解除；排程可在下一輪再次執行。", len(failed), recoverySummary, strings.Join(tools, ", "))
	if result != nil {
		result.Finalized = true
		result.Status = decision.Status
		result.CompletionReason = decision.CompletionReason
		result.EvidenceVerified = false
		result.MissingChecks = nil
	}
	return decision
}

func finalizationAutoContinueBackoff(attempt int) time.Duration {
	if attempt <= 1 {
		return 500 * time.Millisecond
	}
	return time.Duration(attempt) * time.Second
}

func (h *AgentHandler) cleanupPendingToolExecutionsAfterIteration(
	taskCtx context.Context,
	conversationID string,
	decision agentfinalizer.Decision,
	progressCallback func(eventType, message string, data interface{}),
) []string {
	if h == nil || h.agent == nil || decision.CompletionReason != agentfinalizer.ReasonPendingTools {
		return nil
	}
	pending := uniqueNonEmptyStrings(decision.PendingExecutionIDs)
	if len(pending) == 0 {
		return nil
	}
	cancelled := make([]string, 0, len(pending))
	for _, executionID := range pending {
		if h.agent.CancelMCPToolExecutionWithNote(executionID, finalizationPendingToolCancelNote) {
			cancelled = append(cancelled, executionID)
		} else if h.logger != nil {
			h.logger.Warn("finalization pending tool cleanup could not cancel execution",
				zap.String("conversationId", conversationID),
				zap.String("executionId", executionID))
		}
	}
	if len(cancelled) == 0 {
		return nil
	}
	if progressCallback != nil {
		progressCallback("finalization_pending_tools_cancelled", "迭代结束，已自动终止仍在运行的工具执行。", map[string]interface{}{
			"conversationId":                   conversationID,
			"source":                           "finalizer",
			"autoCancelledPendingExecutionIds": cancelled,
			"pendingExecutionIds":              pending,
			"reason":                           agentfinalizer.ReasonPendingTools,
		})
	}
	h.waitForToolExecutionsToLeavePending(taskCtx, cancelled, finalizationPendingToolCancelWait)
	return cancelled
}

func (h *AgentHandler) waitForToolExecutionsToLeavePending(ctx context.Context, executionIDs []string, wait time.Duration) {
	if h == nil || h.db == nil || len(executionIDs) == 0 || wait <= 0 {
		return
	}
	timer := time.NewTimer(wait)
	defer timer.Stop()
	ticker := time.NewTicker(finalizationPendingToolCancelPoll)
	defer ticker.Stop()
	for {
		if !h.hasPendingToolExecutions(executionIDs) {
			return
		}
		select {
		case <-contextDone(ctx):
			return
		case <-timer.C:
			return
		case <-ticker.C:
		}
	}
}

func (h *AgentHandler) hasPendingToolExecutions(executionIDs []string) bool {
	if h == nil || h.db == nil {
		return false
	}
	for _, executionID := range uniqueNonEmptyStrings(executionIDs) {
		exec, err := h.db.GetToolExecution(executionID)
		if err != nil || exec == nil {
			continue
		}
		switch strings.TrimSpace(exec.Status) {
		case mcp.ToolExecutionStatusQueued, mcp.ToolExecutionStatusRunning:
			return true
		}
	}
	return false
}

func uniqueNonEmptyStrings(values []string) []string {
	seen := make(map[string]struct{}, len(values))
	out := make([]string, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	return out
}

func contextDone(ctx context.Context) <-chan struct{} {
	if ctx == nil {
		return nil
	}
	return ctx.Done()
}
