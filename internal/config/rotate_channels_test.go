package config

import "testing"

func TestNextRotateChannelAlternates(t *testing.T) {
	cfg := &Config{AI: AIConfig{
		DefaultChannel: "grok-sub",
		RotateChannels: []string{"grok-sub", "gpt-sub"},
		Channels: map[string]AIChannelConfig{
			"grok-sub": {APIKey: "a", BaseURL: "http://127.0.0.1:18788/v1", Model: "grok-4.6", Provider: "openai_compatible"},
			"gpt-sub":  {APIKey: "b", BaseURL: "http://127.0.0.1:18787/v1", Model: "gpt-6-astra", Provider: "openai_compatible"},
		},
	}}
	scanChannelRotate.n = 0
	first, ok := cfg.NextRotateChannel()
	second, ok2 := cfg.NextRotateChannel()
	third, ok3 := cfg.NextRotateChannel()
	if !ok || !ok2 || !ok3 {
		t.Fatal("rotation should be enabled")
	}
	if first != "grok-sub" || second != "gpt-sub" || third != "grok-sub" {
		t.Fatalf("order = %s %s %s", first, second, third)
	}
}
