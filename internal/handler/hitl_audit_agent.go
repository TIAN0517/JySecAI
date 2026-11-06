package handler

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/openai"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// auditAgentFallbackDecision 审批链异常时的裁决。
//
// 默认 fail-closed：审批链一坏（模型没配置、调用失败、回应解析不出来）就一律拒绝。
// 闸门失效时「拦住」才是安全的一侧 —— 把「闸门故障」当成「闸门不存在」会让
// 模型一挂就被自动放行所有工具调用。
//
// 确实需要 fail-open 的环境（例如长时间自动扫描、宁可跑完也不要中断）可以显式
// 打开 hitl.audit_agent_fail_open，但那是把审批闸门整个拿掉，必须由人决定。
func (h *AgentHandler) auditAgentFallbackDecision(reason string) hitlDecision {
	if h != nil && h.config != nil && h.config.Hitl.AuditAgentFailOpen {
		return hitlDecision{
			Decision: "approve",
			Comment:  "audit agent: " + reason + "，自动授权放行（audit_agent_fail_open 已开启）",
		}
	}
	return hitlDecision{
		Decision: "reject",
		Comment:  "audit agent: " + reason + "，保守拒绝",
	}
}

// auditAgentReview 在 reviewer=audit_agent 时由 LLM 代行审批。
// 白名单工具在 shouldInterrupt 阶段已跳过，到达此处的一律需要裁决。
// LLM / 解析失败时默认 fail-closed（reject）；可用 hitl.audit_agent_fail_open 显式改为放行。
func (h *AgentHandler) auditAgentReview(ctx context.Context, hitlMode, toolName string, payload map[string]interface{}) hitlDecision {
	if h == nil {
		return h.auditAgentFallbackDecision("handler unavailable")
	}
	mode := normalizeHitlMode(hitlMode)
	prompt := config.DefaultHitlAuditAgentPrompt()
	if h.config != nil {
		prompt = h.config.Hitl.EffectiveAuditAgentPromptForMode(mode)
	}
	llmCfg := h.auditLLMConfig()
	if strings.TrimSpace(llmCfg.APIKey) == "" || strings.TrimSpace(llmCfg.Model) == "" {
		return h.auditAgentFallbackDecision("LLM 未配置")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	callCtx, cancel := context.WithTimeout(ctx, 90*time.Second)
	defer cancel()

	userContent := buildAuditAgentReviewInput(mode, toolName, payload)

	// 输出额度必须够大：审计模型多半是会先思考的模型（MiniMax-M3.1 系列会回
	// reasoning_content），思考 token 与正文共用同一份额度。额度太小（例如旧版
	// 写死的 1024）会让模型在正文输出前就被截断，响应只剩 reasoning、没有可解析
	// 的决策 JSON → 解析失败 → fail-closed 拒绝，等于把 nmap/sqlmap/execute 这类
	// 正常工具调用全部挡掉。这里改用配置额度（hitl.audit_model.max_completion_tokens
	// 或通道默认值 config.DefaultMaxCompletionTokens）。
	maxTokens := llmCfg.MaxCompletionTokensEffective()

	raw, finishReason, err := h.auditAgentCallLLM(callCtx, llmCfg, prompt, userContent, maxTokens)
	if err != nil {
		if errors.Is(err, errAuditAgentNoChoices) {
			return h.auditAgentFallbackDecision("LLM 无有效响应")
		}
		h.logger.Warn("审计 Agent LLM 调用失败，按 fail-closed 拒绝", zap.Error(err), zap.String("tool", toolName))
		return h.auditAgentFallbackDecision("LLM 调用失败")
	}

	dec, parseErr := parseAuditAgentLLMContent(raw)
	if parseErr != nil {
		// 第一次解析失败就拒绝，会把「模型只是没按格式回」变成任务中断。
		// 这里用更严格的输出指示重试一次；重试仍失败才 fail-closed。
		h.logger.Warn("审计 Agent 响应解析失败，重试一次",
			zap.Error(parseErr),
			zap.String("tool", toolName),
			zap.String("mode", mode),
			zap.String("finish_reason", finishReason),
		)
		retryCtx, cancelRetry := context.WithTimeout(ctx, 60*time.Second)
		defer cancelRetry()
		retryRaw, retryFinish, retryErr := h.auditAgentCallLLM(
			retryCtx, llmCfg, prompt+auditAgentStrictJSONInstruction, userContent, maxTokens)
		if retryErr == nil {
			if retryDec, retryParseErr := parseAuditAgentLLMContent(retryRaw); retryParseErr == nil {
				return h.auditAgentFinalizeDecision(retryDec, mode, toolName)
			}
		}
		snippet := raw
		if len(snippet) > 240 {
			snippet = snippet[:240] + "..."
		}
		h.logger.Warn("审计 Agent 响应解析失败，按 fail-closed 拒绝",
			zap.Error(parseErr),
			zap.String("tool", toolName),
			zap.String("mode", mode),
			zap.String("finish_reason", finishReason),
			zap.String("retry_finish_reason", retryFinish),
			zap.String("retry_error", retryErrString(retryErr)),
			zap.String("snippet", snippet),
		)
		return h.auditAgentFallbackDecision("响应无法解析")
	}
	return h.auditAgentFinalizeDecision(dec, mode, toolName)
}

// errAuditAgentNoChoices 表示供应商回了 200 但没有任何 choice。
var errAuditAgentNoChoices = errors.New("audit agent LLM 无有效响应")

// auditAgentStrictJSONInstruction 用于解析失败后的重试，压掉模型的思考与说明。
const auditAgentStrictJSONInstruction = "\n\n【输出格式要求（务必遵守）】只输出且只输出一行 JSON 物件，格式为 {\"decision\":\"approve\",\"comment\":\"理由\"}（decision 只能是 approve 或 reject）。不要输出思考过程、不要用 markdown 程式码区块、不要有任何前后说明文字。"

// auditAgentCallLLM 调用审计模型，返回可解析的正文与供应商给出的 finish_reason。
//
// content 为空时回退到 reasoning_content：会思考的模型（例如 MiniMax-M3.1）
// 把思考放在 reasoning_content，正文才在 content；正文被截断而思考还没结束
// 时 content 会是空的，此时剩下的 reasoning 也解析不出决策。
func (h *AgentHandler) auditAgentCallLLM(ctx context.Context, llmCfg config.OpenAIConfig, systemPrompt, userContent string, maxTokens int) (string, string, error) {
	requestBody := map[string]interface{}{
		"model": strings.TrimSpace(llmCfg.Model),
		"messages": []map[string]interface{}{
			{"role": "system", "content": systemPrompt},
			{"role": "user", "content": userContent},
		},
		"temperature":           0.1,
		"max_completion_tokens": maxTokens,
		// 不要在这里发送 thinking / reasoning 控制参数。
		// 这里原本固定送 thinking.type=disabled，目的是避免 Qwen 等把正文放进
		// reasoning_content 导致解析失败。但 MiniMax-M3.1 这类强制 adaptive thinking
		// 的模型会直接返回 400（"model requires adaptive thinking; thinking.type=
		// disabled is not allowed"）。该场景改由下方 msg.Content 为空时回退
		// reasoning_content 的既有逻辑处理 —— 不需要靠 fail-open 来绕过。
	}

	var apiResponse struct {
		Choices []struct {
			FinishReason string `json:"finish_reason"`
			Message      struct {
				Content          string `json:"content"`
				ReasoningContent string `json:"reasoning_content"`
			} `json:"message"`
		} `json:"choices"`
	}
	client := openai.NewClient(&llmCfg, nil, h.logger)
	if err := client.ChatCompletion(ctx, requestBody, &apiResponse); err != nil {
		return "", "", err
	}
	if len(apiResponse.Choices) == 0 {
		return "", "", errAuditAgentNoChoices
	}
	msg := apiResponse.Choices[0].Message
	raw := strings.TrimSpace(msg.Content)
	if raw == "" {
		raw = strings.TrimSpace(msg.ReasoningContent)
	}
	return raw, apiResponse.Choices[0].FinishReason, nil
}

// auditAgentFinalizeDecision 收斂審計裁決：忽略審批模式下的 editedArguments，
// 並統一補上 audit agent 前綴。
func (h *AgentHandler) auditAgentFinalizeDecision(dec hitlDecision, mode, toolName string) hitlDecision {
	if mode != "review_edit" && len(dec.EditedArguments) > 0 {
		h.logger.Warn("审计 Agent 在审批模式下返回 editedArguments，已忽略",
			zap.String("tool", toolName),
		)
		dec.EditedArguments = nil
	}
	if dec.Comment == "" {
		dec.Comment = "audit agent: " + dec.Decision
	} else if !strings.HasPrefix(strings.ToLower(dec.Comment), "audit agent") {
		dec.Comment = "audit agent: " + dec.Comment
	}
	return dec
}

func retryErrString(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}

func (h *AgentHandler) auditLLMConfig() config.OpenAIConfig {
	if h != nil && h.config != nil {
		return h.config.Hitl.AuditModelEffective(h.config.OpenAI)
	}
	return config.OpenAIConfig{}
}

func buildAuditAgentReviewInput(hitlMode, toolName string, payload map[string]interface{}) string {
	review := map[string]interface{}{
		"hitlMode": normalizeHitlMode(hitlMode),
		"toolName": strings.TrimSpace(toolName),
	}
	if payload != nil {
		for _, k := range []string{"arguments", "argumentsObj", "command", hitlPayloadUserMessage, hitlPayloadThinking, hitlPayloadReasoningChain, hitlPayloadPlanning} {
			if v, ok := payload[k]; ok && v != nil && fmt.Sprint(v) != "" {
				review[k] = v
			}
		}
	}
	b, err := json.MarshalIndent(review, "", "  ")
	if err != nil {
		return fmt.Sprintf(`{"hitlMode":%q,"toolName":%q}`, normalizeHitlMode(hitlMode), toolName)
	}
	return string(b)
}

func parseAuditAgentLLMContent(content string) (hitlDecision, error) {
	s := strings.TrimSpace(content)
	if s == "" {
		return hitlDecision{}, errors.New("empty content")
	}
	for _, candidate := range auditAgentJSONCandidates(s) {
		dec, comment, editedArgs, err := parseAuditAgentDecisionObject(candidate)
		if err == nil {
			return hitlDecision{
				Decision:        dec,
				Comment:         comment,
				EditedArguments: editedArgs,
			}, nil
		}
	}
	return hitlDecision{}, fmt.Errorf("no valid decision json in response")
}

func auditAgentJSONCandidates(s string) []string {
	out := make([]string, 0, 4)
	seen := make(map[string]struct{})
	add := func(c string) {
		c = strings.TrimSpace(c)
		if c == "" {
			return
		}
		if _, ok := seen[c]; ok {
			return
		}
		seen[c] = struct{}{}
		out = append(out, c)
	}
	add(s)
	add(stripMarkdownCodeFence(s))
	if obj := extractFirstJSONObject(s); obj != "" {
		add(obj)
	}
	if obj := extractFirstJSONObject(stripMarkdownCodeFence(s)); obj != "" {
		add(obj)
	}
	return out
}

func stripMarkdownCodeFence(s string) string {
	s = strings.TrimSpace(s)
	for _, fence := range []string{"```json", "```JSON", "```"} {
		if strings.HasPrefix(s, fence) {
			s = strings.TrimPrefix(s, fence)
		}
	}
	s = strings.TrimSuffix(s, "```")
	return strings.TrimSpace(s)
}

func extractFirstJSONObject(s string) string {
	start := strings.Index(s, "{")
	if start < 0 {
		return ""
	}
	depth := 0
	inStr := false
	esc := false
	for i := start; i < len(s); i++ {
		ch := s[i]
		if inStr {
			if esc {
				esc = false
				continue
			}
			if ch == '\\' {
				esc = true
				continue
			}
			if ch == '"' {
				inStr = false
			}
			continue
		}
		switch ch {
		case '"':
			inStr = true
		case '{':
			depth++
		case '}':
			depth--
			if depth == 0 {
				return s[start : i+1]
			}
		}
	}
	return ""
}

func parseAuditAgentDecisionObject(jsonText string) (decision, comment string, editedArgs map[string]interface{}, err error) {
	var parsed map[string]interface{}
	if err := json.Unmarshal([]byte(jsonText), &parsed); err != nil {
		return "", "", nil, err
	}
	rawDecision := auditAgentPickString(parsed, "decision", "Decision", "result", "action", "verdict", "决策", "决定")
	decision = normalizeAuditAgentDecision(rawDecision)
	if decision == "" {
		return "", "", nil, fmt.Errorf("missing decision")
	}
	comment = auditAgentPickString(parsed, "comment", "Comment", "reason", "message", "rationale", "备注", "理由", "说明")
	editedArgs = auditAgentPickObject(parsed, "editedArguments", "edited_arguments", "editedArgs")
	return decision, strings.TrimSpace(comment), editedArgs, nil
}

func auditAgentPickString(m map[string]interface{}, keys ...string) string {
	for _, k := range keys {
		if v, ok := m[k]; ok && v != nil {
			s := strings.TrimSpace(fmt.Sprint(v))
			if s != "" {
				return s
			}
		}
	}
	return ""
}

func auditAgentPickObject(m map[string]interface{}, keys ...string) map[string]interface{} {
	for _, k := range keys {
		v, ok := m[k]
		if !ok || v == nil {
			continue
		}
		switch t := v.(type) {
		case map[string]interface{}:
			if len(t) > 0 {
				return t
			}
		case string:
			s := strings.TrimSpace(t)
			if s == "" || s == "{}" {
				continue
			}
			var obj map[string]interface{}
			if err := json.Unmarshal([]byte(s), &obj); err == nil && len(obj) > 0 {
				return obj
			}
		}
	}
	return nil
}

func normalizeAuditAgentDecision(v string) string {
	d := strings.ToLower(strings.TrimSpace(v))
	switch d {
	case "approve", "approved", "pass", "passed", "allow", "allowed", "yes", "ok", "accept", "accepted":
		return "approve"
	case "reject", "rejected", "deny", "denied", "no", "block", "blocked", "refuse", "refused":
		return "reject"
	}
	switch strings.TrimSpace(v) {
	case "通过", "批准", "允许", "同意", "放行":
		return "approve"
	case "拒绝", "驳回", "禁止", "否决":
		return "reject"
	}
	return ""
}

type hitlAuditStrategyReq struct {
	AuditAgentPrompt           string `json:"auditAgentPrompt"`
	AuditAgentPromptReviewEdit string `json:"auditAgentPromptReviewEdit"`
}

func (h *AgentHandler) GetHITLAuditStrategy(c *gin.Context) {
	approvalPrompt := config.DefaultHitlAuditAgentPrompt()
	reviewEditPrompt := config.DefaultHitlAuditAgentPromptReviewEdit()
	approvalCustom := false
	reviewEditCustom := false
	if h.config != nil {
		approvalPrompt = h.config.Hitl.EffectiveAuditAgentPromptForMode("approval")
		reviewEditPrompt = h.config.Hitl.EffectiveAuditAgentPromptForMode("review_edit")
		approvalCustom = strings.TrimSpace(h.config.Hitl.AuditAgentPrompt) != ""
		reviewEditCustom = strings.TrimSpace(h.config.Hitl.AuditAgentPromptReviewEdit) != ""
	}
	c.JSON(http.StatusOK, gin.H{
		"auditAgentPrompt":                  approvalPrompt,
		"auditAgentPromptCustom":            approvalCustom,
		"auditAgentPromptReviewEdit":        reviewEditPrompt,
		"auditAgentPromptReviewEditCustom":  reviewEditCustom,
		"defaultAuditAgentPrompt":           config.DefaultHitlAuditAgentPrompt(),
		"defaultAuditAgentPromptReviewEdit": config.DefaultHitlAuditAgentPromptReviewEdit(),
	})
}

func (h *AgentHandler) UpdateHITLAuditStrategy(c *gin.Context) {
	if h.hitlStrategySaver == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "HITL 策略持久化不可用"})
		return
	}
	var req hitlAuditStrategyReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	approvalPrompt := strings.TrimSpace(req.AuditAgentPrompt)
	reviewEditPrompt := strings.TrimSpace(req.AuditAgentPromptReviewEdit)
	if err := h.hitlStrategySaver.UpdateHitlAuditAgentStrategy(approvalPrompt, reviewEditPrompt); err != nil {
		h.logger.Warn("保存审计 Agent 提示词失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "hitl", "audit_strategy_update", "HITL 审计策略更新", "hitl_config", "audit_agent_prompt", nil)
	}
	if h.config != nil {
		h.config.Hitl.AuditAgentPrompt = approvalPrompt
		h.config.Hitl.AuditAgentPromptReviewEdit = reviewEditPrompt
	}
	c.JSON(http.StatusOK, gin.H{
		"ok":                               true,
		"auditAgentPrompt":                 config.HitlConfig{AuditAgentPrompt: approvalPrompt}.EffectiveAuditAgentPromptForMode("approval"),
		"auditAgentPromptCustom":           approvalPrompt != "",
		"auditAgentPromptReviewEdit":       config.HitlConfig{AuditAgentPromptReviewEdit: reviewEditPrompt}.EffectiveAuditAgentPromptForMode("review_edit"),
		"auditAgentPromptReviewEditCustom": reviewEditPrompt != "",
	})
}

// HitlAuditStrategySaver 持久化审计 Agent 提示词到 config.yaml。
type HitlAuditStrategySaver interface {
	UpdateHitlAuditAgentStrategy(approvalPrompt, reviewEditPrompt string) error
}

// SetHitlAuditStrategySaver 设置审计策略落盘。
func (h *AgentHandler) SetHitlAuditStrategySaver(s HitlAuditStrategySaver) {
	h.hitlStrategySaver = s
}
