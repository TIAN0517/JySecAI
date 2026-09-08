package c2

import (
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestSessionWatchdogWithStaleTimeout(t *testing.T) {
	m := NewManager(nil, zap.NewNop(), t.TempDir())

	w := NewSessionWatchdogWithOptions(m, WithStaleTimeout(12*time.Second))
	if w.minGrace != 12*time.Second {
		t.Fatalf("minGrace = %v, want 12s", w.minGrace)
	}

	now := time.Now()
	{ // 超过 12s 宽限期 → stale
		s := &database.C2Session{SleepSeconds: 5, LastCheckIn: now.Add(-40 * time.Second)}
		if !w.isStale(s, now) {
			t.Fatal("session 40s 未心跳应判为 stale（宽限期 12s）")
		}
	}
	{ // 未超过 → 非 stale
		s := &database.C2Session{SleepSeconds: 5, LastCheckIn: now.Add(-5 * time.Second)}
		if w.isStale(s, now) {
			t.Fatal("session 5s 未心跳不应判为 stale")
		}
	}
}

func TestSessionWatchdogWithStaleTimeoutIgnoresNonPositive(t *testing.T) {
	m := NewManager(nil, zap.NewNop(), t.TempDir())
	w := NewSessionWatchdogWithOptions(m, WithStaleTimeout(0), WithStaleTimeout(-time.Second))
	if w.minGrace != 30*time.Second {
		t.Fatalf("minGrace = %v, want default 30s", w.minGrace)
	}
	if w.interval != 15*time.Second {
		t.Fatalf("interval = %v, want default 15s", w.interval)
	}
}

func TestSessionWatchdogDefaultConstructor(t *testing.T) {
	m := NewManager(nil, zap.NewNop(), t.TempDir())
	w := NewSessionWatchdog(m)
	if w.minGrace != 30*time.Second || w.interval != 15*time.Second {
		t.Fatalf("default watchdog = minGrace %v interval %v", w.minGrace, w.interval)
	}
}