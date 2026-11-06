package config

import "testing"

func TestOfficialOpenAIReasoningNoneIsScoped(t *testing.T) {
	official := &OpenAIConfig{Provider: "openai", BaseURL: "https://api.openai.com/v1", Model: "gpt-5.6"}
	if !official.SupportsOpenAIReasoningNone() || !official.OpenAIChatToolsNeedNone() {
		t.Fatal("known official model should keep an explicit none")
	}
	bridge := &OpenAIConfig{Provider: "openai_compatible", BaseURL: "http://127.0.0.1:18788/v1", Model: "grok-4.6"}
	if bridge.UsesOfficialOpenAIReasoning() || bridge.SupportsOpenAIReasoningNone() {
		t.Fatal("subscription bridge must not inherit official OpenAI reasoning rules")
	}
	dated := &OpenAIConfig{Provider: "openai", BaseURL: "https://api.openai.com/v1", Model: "gpt-5.6-sol-2026-10-21"}
	if !dated.SupportsOpenAIReasoningNone() {
		t.Fatal("dated snapshot of a known model was rejected")
	}
}
