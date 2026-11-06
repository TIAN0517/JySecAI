package multiagent

import (
	"context"
	"errors"
	"fmt"
	"testing"

	"github.com/cloudwego/eino/adk"
)

// 2026-11-01：MiniMax 通道回 429「已达到 Token Plan 用量上限」，
// 舊邏輯把它當成暫時性速率限制，退避重試 4 次後仍失敗，
// 批次佇列因此每數分鐘重打同一個任務，兩小時內噴了 58 次同樣的錯誤。
// 額度用盡必須立刻失敗（讓上層切通道），不能進重試迴圈。

func TestQuotaExhausted429IsNotTransient(t *testing.T) {
	t.Parallel()
	err := errors.New(`create message stream failed: POST "https://api.minimax.cn/anthropic/v1/messages": 429 Too Many Requests {"type":"error","error":{"type":"rate_limit_error","message":"已达到 Token Plan 用量上限：请升级 Token Plan 套餐或购买积分补充用量。 (2056)"}}`)

	if isEinoTransientRunError(err) {
		t.Fatal("quota exhaustion must not be treated as a transient (retryable) error")
	}
}

func TestPlainRateLimit429IsStillTransient(t *testing.T) {
	t.Parallel()
	// 純粹的速率限制重試會好，必須維持可重試。
	err := errors.New("HTTP 429 Too Many Requests")
	if !isEinoTransientRunError(err) {
		t.Fatal("plain rate limit must stay retryable")
	}
}

func TestQuotaExhaustedUserDetailKind(t *testing.T) {
	t.Parallel()
	err := errors.New(`429 Too Many Requests {"type":"rate_limit_error","message":"已达到 Token Plan 用量上限：请升级 Token Plan 套餐"}`)
	kind, summary := einoTransientRunErrorUserDetail(err)
	if kind != "quota_exhausted" {
		t.Fatalf("kind = %q, want quota_exhausted", kind)
	}
	if summary == "" {
		t.Fatal("summary must not be empty")
	}
}

func TestQuotaExhaustedMarkers(t *testing.T) {
	t.Parallel()
	positive := []string{
		"已达到 Token Plan 用量上限",
		"insufficient_quota",
		"Quota exceeded for quota metric",
		"You exceeded your current quota",
		"out of credits",
	}
	for _, p := range positive {
		if !isEinoQuotaExhaustedError(errors.New(p)) {
			t.Errorf("marker %q should be detected as quota exhaustion", p)
		}
	}
	negative := []string{
		"HTTP 429 Too Many Requests",
		"connection reset by peer",
		"invalid api key",
		"internal server error",
	}
	for _, n := range negative {
		if isEinoQuotaExhaustedError(errors.New(n)) {
			t.Errorf("marker %q must NOT be detected as quota exhaustion", n)
		}
	}
}

// 額度用盡時不應退避重試；一般暫時性錯誤仍應重試。
func TestModelRetryDecisionSkipsQuotaExhaustion(t *testing.T) {
	t.Parallel()
	cfg := newEinoModelRetryConfig(nil, nil, "test")
	quotaErr := fmt.Errorf(`429 Too Many Requests {"message":"已达到 Token Plan 用量上限"}`)
	if got := cfg.ShouldRetry(context.Background(), &adk.RetryContext{Err: quotaErr}); got == nil || got.Retry {
		t.Fatal("quota exhaustion must not be retried")
	}
	if got := cfg.ShouldRetry(context.Background(), &adk.RetryContext{Err: errors.New("HTTP 429 Too Many Requests")}); got == nil || !got.Retry {
		t.Fatal("transient rate limit should still be retried")
	}
}
