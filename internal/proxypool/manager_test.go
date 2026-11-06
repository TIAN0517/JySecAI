package proxypool

import (
	"context"
	"errors"
	"os"
	"testing"
	"time"

	"jysecai/internal/config"

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
		got, transport, enabled, err := manager.nextTransport("")
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
		endpoint, _, _, err := manager.nextTransport("")
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
	_, _, enabled, err := manager.nextTransport("")
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
	_, transport, enabled, err := manager.nextTransport("")
	if err != nil {
		t.Fatal(err)
	}
	if enabled || transport != nil {
		t.Fatal("disabled pool should use the direct transport")
	}
}

func TestGroupFiltering(t *testing.T) {
	cfg := testConfig()
	cfg.Proxies = append(cfg.Proxies,
		config.SOCKS5ProxyConfig{Name: "res-a", URL: "socks5://203.0.113.10:1080", Enabled: true, Group: "residential"},
		config.SOCKS5ProxyConfig{Name: "dc-b", URL: "socks5://203.0.113.11:1080", Enabled: true, Group: "dc"},
	)
	manager, err := New(cfg, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	// residential 組只會選到 res-a;dc 組只會選到機房條目。
	seen := map[string]bool{}
	for i := 0; i < 4; i++ {
		got, _, enabled, err := manager.nextTransport("residential")
		if err != nil || !enabled {
			t.Fatalf("residential selection %d: enabled=%v err=%v", i, enabled, err)
		}
		if got.ProxyGroupEffective() != "residential" {
			t.Fatalf("residential selection leaked %q group=%q", got.Name, got.ProxyGroupEffective())
		}
		seen[got.Name] = true
	}
	if seen["dc-b"] || len(seen) != 1 || !seen["res-a"] {
		t.Fatalf("residential group picked unexpected endpoints: %v", seen)
	}
	// 空群組 = 不限,行為與既有 Client() 一致:全部可選。
	all := map[string]bool{}
	for i := 0; i < 12; i++ {
		got, _, enabled, err := manager.nextTransport("")
		if err != nil || !enabled {
			t.Fatalf("unfiltered selection %d: enabled=%v err=%v", i, enabled, err)
		}
		all[got.Name] = true
	}
	if !all["res-a"] || !all["dc-b"] {
		t.Fatalf("unfiltered selection should include every endpoint: %v", all)
	}
	// 預設群組:未標記 group 的條目視為 dc(僅含未標記條目時,dc 組可選到它)。
	cfg2 := testConfig()
	cfg2.Proxies = []config.SOCKS5ProxyConfig{{Name: "legacy", URL: "socks5://203.0.113.12:1080", Enabled: true}}
	manager2, err := New(cfg2, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	got, _, enabled, err := manager2.nextTransport("dc")
	if err != nil || !enabled || got.Name != "legacy" {
		t.Fatalf("dc group should pick untagged endpoint, got %q enabled=%v err=%v", got.Name, enabled, err)
	}
}

func TestProxyGroupEffective(t *testing.T) {
	cases := map[string]string{"": "dc", "dc": "dc", "residential": "residential", "Residential": "residential", "  residential  ": "residential", "bogus": "dc"}
	for in, want := range cases {
		probe := config.SOCKS5ProxyConfig{Group: in}
		if got := probe.ProxyGroupEffective(); got != want {
			t.Fatalf("ProxyGroupEffective(%q) = %q, want %q", in, got, want)
		}
	}
}
