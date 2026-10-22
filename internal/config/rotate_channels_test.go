package config

import "testing"

func TestNextRotateChannelAlternates(t *testing.T) {
	cfg := &Config{AI: AIConfig{
		DefaultChannel: "minimax-m3-a",
		RotateChannels: []string{"minimax-m3-a", "minimax-m3-b"},
		Channels: map[string]AIChannelConfig{
			"minimax-m3-a": {APIKey: "a", BaseURL: "https://api.minimax.cn/anthropic", Model: "MiniMax-M3.1-Flash-Preview", Provider: "claude"},
			"minimax-m3-b": {APIKey: "b", BaseURL: "https://api.minimax.cn/anthropic", Model: "MiniMax-M3.1-Flash-Preview", Provider: "claude"},
		},
	}}
	scanChannelRotate.n = 0
	first, ok := cfg.NextRotateChannel()
	second, ok2 := cfg.NextRotateChannel()
	third, ok3 := cfg.NextRotateChannel()
	if !ok || !ok2 || !ok3 {
		t.Fatal("rotation should be enabled")
	}
	if first != "minimax-m3-a" || second != "minimax-m3-b" || third != "minimax-m3-a" {
		t.Fatalf("order = %s %s %s", first, second, third)
	}
}
