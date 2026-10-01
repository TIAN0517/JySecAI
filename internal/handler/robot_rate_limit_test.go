package handler

import (
	"testing"
	"time"

	"go.uber.org/zap"
	"jysecai/internal/config"
)

func TestRobotPerSenderRateLimit(t *testing.T) {
	cfg := &config.Config{}
	cfg.Robots.Session.RateLimitPerMinute = 60
	cfg.Robots.Session.RateLimitBurst = 2
	h := NewRobotHandler(cfg, nil, nil, zap.NewNop())
	now := time.Unix(1000, 0)
	if !h.allowRobotMessageAt("telegram", "user-a", now) || !h.allowRobotMessageAt("telegram", "user-a", now) {
		t.Fatal("initial burst should be allowed")
	}
	if h.allowRobotMessageAt("telegram", "user-a", now) {
		t.Fatal("request above burst should be blocked")
	}
	if !h.allowRobotMessageAt("telegram", "user-b", now) {
		t.Fatal("rate limits must be isolated per sender")
	}
	if !h.allowRobotMessageAt("telegram", "user-a", now.Add(time.Second)) {
		t.Fatal("one token should refill after one second at 60/minute")
	}
}

func TestRobotRateLimitCoversCommandsButAllowsEmergencyControls(t *testing.T) {
	cfg := &config.Config{}
	cfg.Robots.Session.RateLimitPerMinute = 1
	cfg.Robots.Session.RateLimitBurst = 1
	h := NewRobotHandler(cfg, nil, nil, zap.NewNop())
	if _, allowed := h.checkRobotRateLimit("wecom", "user-a", "帮助"); !allowed {
		t.Fatal("first command should be allowed")
	}
	if _, allowed := h.checkRobotRateLimit("wecom", "user-a", "帮助"); allowed {
		t.Fatal("commands should not bypass the rate limiter")
	}
	if _, allowed := h.checkRobotRateLimit("wecom", "user-a", "停止"); !allowed {
		t.Fatal("emergency stop must remain available while rate limited")
	}
	if _, allowed := h.checkRobotRateLimit("wecom", "user-a", "cancel"); !allowed {
		t.Fatal("cancel must remain available while rate limited")
	}
}
