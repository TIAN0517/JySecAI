package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/security"

	"go.uber.org/zap"
)

// 回归测试：审计请求不得携带 thinking / reasoning 控制参数。
// MiniMax-M3.1 等强制 adaptive thinking 的模型会对 thinking.type="disabled" 直接回 400；
// 调用失败走 fail-closed（reject），不再靠自动放行来避免误拦任务。
func TestAuditAgentReviewDoesNotSendThinkingParam(t *testing.T) {
	// 审核用的 mock 端点在 127.0.0.1，而 OpenAI 客户端会拒绝拨向受限网段。
	defer security.SetAllowPrivateNetworkForTesting(true)()
	var got map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if err := json.NewDecoder(r.Body).Decode(&got); err != nil {
			t.Errorf("decode request body: %v", err)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"choices":[{"message":{"content":"{\"decision\":\"approve\",\"comment\":\"ok\"}"}}]}`))
	}))
	defer srv.Close()

	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{
			Hitl: config.HitlConfig{
				AuditModel: config.OpenAIConfig{
					Provider: "openai_compatible",
					BaseURL:  srv.URL,
					APIKey:   "test-key",
					Model:    "test-model",
				},
			},
		},
	}

	dec := h.auditAgentReview(context.Background(), "approval", "exec", map[string]interface{}{
		"arguments": `{"command":"id"}`,
	})
	if dec.Decision != "approve" {
		t.Fatalf("decision = %q (comment=%q), want approve", dec.Decision, dec.Comment)
	}
	if got == nil {
		t.Fatal("服务端没有收到请求")
	}
	if v, ok := got["thinking"]; ok {
		t.Fatalf("審計請求不得帶 thinking 參數，實際送出: %v", v)
	}
	if v, ok := got["reasoning"]; ok {
		t.Fatalf("審計請求不得帶 reasoning 參數，實際送出: %v", v)
	}
	if got["model"] != "test-model" {
		t.Fatalf("model = %v, want test-model", got["model"])
	}
	if _, ok := got["messages"]; !ok {
		t.Fatalf("請求缺少 messages: %v", got)
	}
}

func TestParseAuditAgentLLMContentApprove(t *testing.T) {
	d, err := parseAuditAgentLLMContent(`{"decision":"approve","comment":"与任务一致"}`)
	if err != nil {
		t.Fatal(err)
	}
	if d.Decision != "approve" || d.Comment != "与任务一致" {
		t.Fatalf("unexpected %+v", d)
	}
}

func TestParseAuditAgentLLMContentReject(t *testing.T) {
	d, err := parseAuditAgentLLMContent("```json\n{\"decision\":\"reject\",\"comment\":\"风险过高\"}\n```")
	if err != nil {
		t.Fatal(err)
	}
	if d.Decision != "reject" {
		t.Fatalf("expected reject, got %s", d.Decision)
	}
}

func TestParseAuditAgentLLMContentInvalid(t *testing.T) {
	_, err := parseAuditAgentLLMContent(`{"decision":"maybe"}`)
	if err == nil {
		t.Fatal("expected error for invalid decision")
	}
}

func TestParseAuditAgentLLMContentProseWrapped(t *testing.T) {
	d, err := parseAuditAgentLLMContent("好的，裁决如下：\n```json\n{\"decision\":\"approve\",\"comment\":\"只读 ls\"}\n```\n以上。")
	if err != nil {
		t.Fatal(err)
	}
	if d.Decision != "approve" {
		t.Fatalf("expected approve, got %s", d.Decision)
	}
}

func TestParseAuditAgentLLMContentChineseDecision(t *testing.T) {
	d, err := parseAuditAgentLLMContent(`{"decision":"通过","comment":"风险低"}`)
	if err != nil {
		t.Fatal(err)
	}
	if d.Decision != "approve" {
		t.Fatalf("expected approve, got %s", d.Decision)
	}
}

func TestParseAuditAgentLLMContentWithEditedArguments(t *testing.T) {
	d, err := parseAuditAgentLLMContent(`{"decision":"approve","comment":"收窄路径","editedArguments":{"path":"/safe"}}`)
	if err != nil {
		t.Fatal(err)
	}
	if d.Decision != "approve" {
		t.Fatalf("expected approve, got %s", d.Decision)
	}
	if d.EditedArguments == nil || d.EditedArguments["path"] != "/safe" {
		t.Fatalf("unexpected edited args: %+v", d.EditedArguments)
	}
}

func TestAuditAgentReviewFailClosedOnLLMError(t *testing.T) {
	defer security.SetAllowPrivateNetworkForTesting(true)()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "upstream down", http.StatusBadGateway)
	}))
	defer srv.Close()

	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{
			Hitl: config.HitlConfig{
				AuditModel: config.OpenAIConfig{
					Provider: "openai_compatible",
					BaseURL:  srv.URL,
					APIKey:   "test-key",
					Model:    "test-model",
				},
			},
		},
	}
	dec := h.auditAgentReview(context.Background(), "review_edit", "nmap", map[string]interface{}{
		"arguments": `{"target":"1.2.3.4"}`,
	})
	if dec.Decision != "reject" {
		t.Fatalf("decision = %q (comment=%q), want reject fail-closed", dec.Decision, dec.Comment)
	}
	if !strings.Contains(dec.Comment, "保守拒绝") {
		t.Fatalf("comment = %q, want fail-closed note", dec.Comment)
	}
}

func TestAuditAgentReviewFailClosedWhenUnconfigured(t *testing.T) {
	h := &AgentHandler{logger: zap.NewNop(), config: &config.Config{}}
	dec := h.auditAgentReview(context.Background(), "approval", "exec", nil)
	if dec.Decision != "reject" {
		t.Fatalf("decision = %q, want reject when LLM missing", dec.Decision)
	}
}

// TestAuditAgentReviewUsesConfiguredTokenBudget 回归：审计请求的输出额度不得写死。
//
// 旧版把 max_completion_tokens 写死 1024，而审计模型（MiniMax-M3.1 系列）是会先
// 思考的模型：思考 token 与正文共用额度，额度太小会让响应在正文输出前被截断，
// 只剩 reasoning_content → 解析不到决策 JSON → fail-closed 拒绝，把 nmap/sqlmap/
// execute 这类正常工具调用全部挡掉（2026-11-01 生产环境当天发生 13 次）。
func TestAuditAgentReviewUsesConfiguredTokenBudget(t *testing.T) {
	defer security.SetAllowPrivateNetworkForTesting(true)()
	var got map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if err := json.NewDecoder(r.Body).Decode(&got); err != nil {
			t.Errorf("decode request body: %v", err)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"choices":[{"message":{"content":"{\"decision\":\"approve\",\"comment\":\"ok\"}"}}]}`))
	}))
	defer srv.Close()

	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{
			Hitl: config.HitlConfig{
				AuditModel: config.OpenAIConfig{
					Provider: "openai_compatible",
					BaseURL:  srv.URL,
					APIKey:   "test-key",
					Model:    "test-model",
				},
			},
		},
	}
	if dec := h.auditAgentReview(context.Background(), "approval", "nmap", map[string]interface{}{
		"arguments": `{"target":"1.2.3.4"}`,
	}); dec.Decision != "approve" {
		t.Fatalf("decision = %q, want approve", dec.Decision)
	}
	budget, ok := got["max_completion_tokens"].(float64)
	if !ok {
		t.Fatalf("请求缺少 max_completion_tokens: %v", got)
	}
	if int(budget) < 4096 {
		t.Fatalf("max_completion_tokens = %v，思考型模型會在正文輸出前被截斷，want >= 4096", int(budget))
	}

	// 明確設定時以設定值為準。
	h.config.Hitl.AuditModel.MaxCompletionTokens = 8192
	if dec := h.auditAgentReview(context.Background(), "approval", "nmap", nil); dec.Decision != "approve" {
		t.Fatalf("decision = %q, want approve", dec.Decision)
	}
	if budget, ok := got["max_completion_tokens"].(float64); !ok || int(budget) != 8192 {
		t.Fatalf("max_completion_tokens = %v, want 8192（應尊重設定值）", got["max_completion_tokens"])
	}
}

// TestAuditAgentReviewRetriesWhenResponseUnparsable 回归：第一次回應解析不到決策時，
// 應以嚴格輸出格式重試一次，並採用重試的結果，而不是直接 fail-closed 拒絕。
func TestAuditAgentReviewRetriesWhenResponseUnparsable(t *testing.T) {
	defer security.SetAllowPrivateNetworkForTesting(true)()
	calls := 0
	var bodies []map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var body map[string]any
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Errorf("decode request body: %v", err)
		}
		bodies = append(bodies, body)
		calls++
		w.Header().Set("Content-Type", "application/json")
		if calls == 1 {
			// 模擬思考型模型：正文被截斷，只剩 reasoning_content。
			_, _ = w.Write([]byte(`{"choices":[{"finish_reason":"length","message":{"content":"","reasoning_content":"We need answer only one-line JSON Chinese likely. Need assess tool call nmap arguments."}}]}`))
			return
		}
		_, _ = w.Write([]byte(`{"choices":[{"finish_reason":"stop","message":{"content":"{\"decision\":\"approve\",\"comment\":\"僅連接埠掃描\"}"}}]}`))
	}))
	defer srv.Close()

	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{
			Hitl: config.HitlConfig{
				AuditModel: config.OpenAIConfig{
					Provider: "openai_compatible",
					BaseURL:  srv.URL,
					APIKey:   "test-key",
					Model:    "test-model",
				},
			},
		},
	}
	dec := h.auditAgentReview(context.Background(), "review_edit", "nmap", map[string]interface{}{
		"arguments": `{"target":"1.2.3.4"}`,
	})
	if calls != 2 {
		t.Fatalf("呼叫次數 = %d, want 2（第一次解析失敗應重試一次）", calls)
	}
	if dec.Decision != "approve" {
		t.Fatalf("decision = %q (comment=%q), want approve（重試成功應採用重試結果）", dec.Decision, dec.Comment)
	}
	if len(bodies) != 2 {
		t.Fatalf("bodies = %d, want 2", len(bodies))
	}
	first, _ := bodies[0]["messages"].([]any)
	second, _ := bodies[1]["messages"].([]any)
	if len(first) == 0 || len(second) == 0 {
		t.Fatalf("重試請求缺少 messages: %v", bodies[1])
	}
	sysSecond, _ := second[0].(map[string]any)
	sysPrompt, _ := sysSecond["content"].(string)
	if !strings.Contains(sysPrompt, "只输出且只输出一行 JSON") {
		t.Fatalf("重試請求的 system prompt 未帶嚴格輸出指示: %q", sysPrompt)
	}
}

// TestAuditAgentReviewFailsClosedAfterRetryFailed 回归：兩次都解析不到決策時，
// 仍必須 fail-closed 拒絕（審批閘門失效時「攔住」才是安全的一側）。
func TestAuditAgentReviewFailsClosedAfterRetryFailed(t *testing.T) {
	defer security.SetAllowPrivateNetworkForTesting(true)()
	calls := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"choices":[{"finish_reason":"length","message":{"content":"","reasoning_content":"We need answer only one-line JSON Chinese likely."}}]}`))
	}))
	defer srv.Close()

	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{
			Hitl: config.HitlConfig{
				AuditModel: config.OpenAIConfig{
					Provider: "openai_compatible",
					BaseURL:  srv.URL,
					APIKey:   "test-key",
					Model:    "test-model",
				},
			},
		},
	}
	dec := h.auditAgentReview(context.Background(), "review_edit", "execute", map[string]interface{}{
		"arguments": `{"command":"id"}`,
	})
	if calls != 2 {
		t.Fatalf("呼叫次數 = %d, want 2", calls)
	}
	if dec.Decision != "reject" {
		t.Fatalf("decision = %q (comment=%q), want reject fail-closed", dec.Decision, dec.Comment)
	}
	if !strings.Contains(dec.Comment, "保守拒绝") {
		t.Fatalf("comment = %q, want fail-closed note", dec.Comment)
	}
}

// TestAuditAgentReviewFailOpenOptIn 明确开启 audit_agent_fail_open 时才自动放行。
func TestAuditAgentReviewFailOpenOptIn(t *testing.T) {
	h := &AgentHandler{
		logger: zap.NewNop(),
		config: &config.Config{Hitl: config.HitlConfig{AuditAgentFailOpen: true}},
	}
	dec := h.auditAgentReview(context.Background(), "approval", "exec", nil)
	if dec.Decision != "approve" {
		t.Fatalf("decision = %q (comment=%q), want approve when fail-open opt-in is on", dec.Decision, dec.Comment)
	}
}

func TestBuildAuditAgentReviewInputIncludesMode(t *testing.T) {
	s := buildAuditAgentReviewInput("review_edit", "execute", map[string]interface{}{
		"arguments": `{"command":"pwd"}`,
	})
	if !strings.Contains(s, "review_edit") || !strings.Contains(s, "execute") {
		t.Fatalf("unexpected input: %s", s)
	}
}

func TestBuildAuditAgentReviewInput(t *testing.T) {
	s := buildAuditAgentReviewInput("approval", "nmap", map[string]interface{}{
		"arguments":   `{"target":"10.0.0.1"}`,
		"userMessage": "扫描内网",
	})
	if s == "" {
		t.Fatal("expected non-empty input")
	}
	if !strings.Contains(s, "nmap") || !strings.Contains(s, "10.0.0.1") || !strings.Contains(s, "扫描内网") {
		t.Fatalf("unexpected input: %s", s)
	}
}
