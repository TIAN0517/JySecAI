package app

import (
	"encoding/json"
	"path/filepath"
	"testing"

	"jysecai/internal/c2"
	"jysecai/internal/config"
	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestReconcileAutoCheckinListeners(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2-auto-checkin.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	mgr := c2.NewManager(db, zap.NewNop(), t.TempDir())
	mgr.Registry().Register(string(c2.ListenerTypeHTTPBeacon), c2.NewHTTPBeaconListener)
	mgr.Registry().Register(string(c2.ListenerTypeWebSocket), c2.NewWebSocketListener)
	t.Cleanup(mgr.Close)

	enabled := true
	disabled := false
	sleep := 7
	jitterPercent := 12
	ac := &config.C2AutoCheckinConfig{
		Enabled:              &enabled,
		DefaultSleepSeconds:  &sleep,
		DefaultJitterPercent: &jitterPercent,
		Listeners: []config.C2AutoListenerConfig{
			{Name: "auto-http", Type: "http_beacon", BindHost: "127.0.0.1", BindPort: 49171, Enabled: &enabled},
			{Name: "auto-ws", Type: "websocket", BindHost: "127.0.0.1", BindPort: 49172, Enabled: &disabled},
		},
	}

	if err := reconcileAutoCheckinListeners(mgr, ac, zap.NewNop()); err != nil {
		t.Fatalf("reconcile: %v", err)
	}

	listeners, err := db.ListC2Listeners()
	if err != nil {
		t.Fatal(err)
	}
	if len(listeners) != 1 {
		t.Fatalf("listener count = %d, want 1 (disabled ws skipped)", len(listeners))
	}
	ln := listeners[0]
	if ln.Name != "auto-http" {
		t.Fatalf("listener name = %q, want auto-http", ln.Name)
	}
	if ln.Status != "running" {
		t.Fatalf("listener status = %q, want running (auto_start)", ln.Status)
	}

	var lcfg c2.ListenerConfig
	if err := json.Unmarshal([]byte(ln.ConfigJSON), &lcfg); err != nil {
		t.Fatalf("unmarshal listener config: %v", err)
	}
	if lcfg.DefaultSleep != 7 || lcfg.DefaultJitter != 12 {
		t.Fatalf("listener defaults = sleep %d jitter %d, want 7/12", lcfg.DefaultSleep, lcfg.DefaultJitter)
	}

	// 幂等性：再次协调不产生重复监听器。
	if err := reconcileAutoCheckinListeners(mgr, ac, zap.NewNop()); err != nil {
		t.Fatalf("second reconcile: %v", err)
	}
	listeners, err = db.ListC2Listeners()
	if err != nil {
		t.Fatal(err)
	}
	if len(listeners) != 1 {
		t.Fatalf("listener count after second reconcile = %d, want 1 (idempotent)", len(listeners))
	}
}

func TestReconcileAutoCheckinListenersDisabledOrNil(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2-auto-checkin-off.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	mgr := c2.NewManager(db, zap.NewNop(), t.TempDir())
	t.Cleanup(mgr.Close)

	off := false
	if err := reconcileAutoCheckinListeners(mgr, &config.C2AutoCheckinConfig{Enabled: &off}, zap.NewNop()); err != nil {
		t.Fatalf("reconcile(disabled): %v", err)
	}
	if err := reconcileAutoCheckinListeners(mgr, nil, zap.NewNop()); err != nil {
		t.Fatalf("reconcile(nil): %v", err)
	}
	listeners, err := db.ListC2Listeners()
	if err != nil {
		t.Fatal(err)
	}
	if len(listeners) != 0 {
		t.Fatalf("listener count = %d, want 0 (disabled/nil)", len(listeners))
	}
}

func TestReconcileAutoCheckinListenersCreateOnlyWhenAutoStartOff(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2-auto-checkin-nostart.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	mgr := c2.NewManager(db, zap.NewNop(), t.TempDir())
	t.Cleanup(mgr.Close)

	truev := true
	falsev := false
	ac := &config.C2AutoCheckinConfig{
		Enabled:            &truev,
		AutoStartListeners: &falsev,
		Listeners: []config.C2AutoListenerConfig{
			{Name: "auto-nostart", Type: "http_beacon", BindHost: "127.0.0.1", BindPort: 49173, Enabled: &truev},
		},
	}
	if err := reconcileAutoCheckinListeners(mgr, ac, zap.NewNop()); err != nil {
		t.Fatalf("reconcile: %v", err)
	}
	listeners, err := db.ListC2Listeners()
	if err != nil {
		t.Fatal(err)
	}
	if len(listeners) != 1 {
		t.Fatalf("listener count = %d, want 1", len(listeners))
	}
	if listeners[0].Status != "stopped" {
		t.Fatalf("listener status = %q, want stopped (auto_start_listeners=false)", listeners[0].Status)
	}
}

func TestReconcileAutoCheckinListenersSkipsInvalidPort(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2-auto-checkin-badport.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	mgr := c2.NewManager(db, zap.NewNop(), t.TempDir())
	t.Cleanup(mgr.Close)

	truev := true
	ac := &config.C2AutoCheckinConfig{
		Enabled: &truev,
		Listeners: []config.C2AutoListenerConfig{
			{Name: "auto-bad", Type: "http_beacon", BindHost: "127.0.0.1", BindPort: 99999, Enabled: &truev},
		},
	}
	if err := reconcileAutoCheckinListeners(mgr, ac, zap.NewNop()); err != nil {
		t.Fatalf("reconcile: %v", err)
	}
	listeners, err := db.ListC2Listeners()
	if err != nil {
		t.Fatal(err)
	}
	if len(listeners) != 0 {
		t.Fatalf("listener count = %d, want 0 (invalid port skipped)", len(listeners))
	}
}