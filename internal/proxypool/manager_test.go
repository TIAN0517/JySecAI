package proxypool

import (
	"context"
	"errors"
	"os"
	"testing"
	"time"

	"cyberstrike-ai/internal/config"

	"go.uber.org/zap"
)

func testConfig() config.ProxyPoolConfig {
	return config.ProxyPoolConfig{
		Enabled:          true,
		Strategy:         "round_robin",
		FailureThreshold: 2,
		CooldownSeconds:  60,
		Proxies: []config.SOCKS5ProxyConfig{
			{Name: "one", URL: "socks5://127.0.0.1:10001", Enabled: true},
			{Name: "two", URL: "socks5://127.0.0.1:10002", Enabled: true},
			{Name: "three", URL: "socks5://127.0.0.1:10003", Enabled: true},
		},
	}
}

func TestConfiguredProxyPoolLive(t *testing.T) {
	if os.Getenv("JYSEC_PROXY_POOL_LIVE") != "1" {
		t.Skip("set JYSEC_PROXY_POOL_LIVE=1 to run live SOCKS5 checks")
	}
	repoConfig, err := config.Load("../../config.yaml")
	if err != nil {
		t.Fatal(err)
	}
	results, err := CheckAll(context.Background(), repoConfig.ProxyPool)
	if err != nil {
		t.Fatal(err)
	}
	for _, result := range results {
		if !result.Healthy {
			t.Errorf("proxy %s failed: %s", result.URL, result.Error)
		}
	}
}

func TestRoundRobinSelection(t *testing.T) {
	manager, err := New(testConfig(), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range []string{"one", "two", "three", "one"} {
		got, transport, enabled, err := manager.nextTransport()
		if err != nil {
			t.Fatalf("selection %d: %v", i, err)
		}
		if !enabled || transport == nil {
			t.Fatalf("selection %d did not return an enabled transport", i)
		}
		if got.Name != want {
			t.Fatalf("selection %d = %q, want %q", i, got.Name, want)
		}
	}
}

func TestFailedEndpointEntersCooldownAndIsSkipped(t *testing.T) {
	cfg := testConfig()
	manager, err := New(cfg, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	failedURL := cfg.Proxies[0].URL
	manager.recordFailure(failedURL, time.Millisecond, errors.New("first"))
	manager.recordFailure(failedURL, time.Millisecond, errors.New("second"))

	for i := 0; i < 4; i++ {
		endpoint, _, _, err := manager.nextTransport()
		if err != nil {
			t.Fatal(err)
		}
		if endpoint.URL == failedURL {
			t.Fatalf("cooled endpoint selected on iteration %d", i)
		}
	}
}

func TestAllEndpointsCoolingFailsClosed(t *testing.T) {
	cfg := testConfig()
	cfg.FailureThreshold = 1
	manager, err := New(cfg, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	for _, endpoint := range cfg.Proxies {
		manager.recordFailure(endpoint.URL, time.Millisecond, errors.New("down"))
	}
	_, _, enabled, err := manager.nextTransport()
	if !enabled {
		t.Fatal("pool unexpectedly fell back to a direct connection")
	}
	if !errors.Is(err, ErrNoHealthyProxy) {
		t.Fatalf("error = %v, want ErrNoHealthyProxy", err)
	}
}

func TestDisabledPoolUsesDirectTransport(t *testing.T) {
	cfg := testConfig()
	cfg.Enabled = false
	manager, err := New(cfg, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	_, transport, enabled, err := manager.nextTransport()
	if err != nil {
		t.Fatal(err)
	}
	if enabled || transport != nil {
		t.Fatal("disabled pool should use the direct transport")
	}
}
