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
// MiniMax-M3.1 等强制 adaptive thinking 的模型会对 thinking.type="disabled" 直接回 400，
// 而 auditAgentReview 对调用失败是 fail-closed 判成 reject，会让所有工具调用都被误拒。
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
