package config

import "testing"

func TestProxyPoolNormalizeAndValidate(t *testing.T) {
	cfg := ProxyPoolConfig{
		Enabled: true,
		Proxies: []SOCKS5ProxyConfig{{URL: "127.0.0.1:1080", Enabled: true}},
	}
	if err := cfg.NormalizeAndValidate(); err != nil {
		t.Fatal(err)
	}
	if cfg.Strategy != "round_robin" || cfg.HealthCheckURL != "https://api.ipify.org" {
		t.Fatalf("defaults were not applied: %#v", cfg)
	}
	if cfg.Proxies[0].URL != "socks5://127.0.0.1:1080" {
		t.Fatalf("proxy URL = %q", cfg.Proxies[0].URL)
	}
	if cfg.Proxies[0].Name != "127.0.0.1:1080" {
		t.Fatalf("proxy name = %q", cfg.Proxies[0].Name)
	}
}

func TestProxyPoolRejectsDuplicates(t *testing.T) {
	cfg := ProxyPoolConfig{Proxies: []SOCKS5ProxyConfig{
		{URL: "socks5://127.0.0.1:1080", Enabled: true},
		{URL: "socks5://127.0.0.1:1080", Enabled: true},
	}}
	if err := cfg.NormalizeAndValidate(); err == nil {
		t.Fatal("expected duplicate proxy error")
	}
}

func TestProxyPoolRejectsURLWithPathOrQuery(t *testing.T) {
	for _, rawURL := range []string{
		"socks5://127.0.0.1:1080/path",
		"socks5://127.0.0.1:1080?mode=unsafe",
	} {
		cfg := ProxyPoolConfig{Proxies: []SOCKS5ProxyConfig{{URL: rawURL, Enabled: true}}}
		if err := cfg.NormalizeAndValidate(); err == nil {
			t.Fatalf("expected %q to fail", rawURL)
		}
	}
}

func TestProxyPoolEnabledRequiresEndpoint(t *testing.T) {
	cfg := ProxyPoolConfig{Enabled: true}
	if err := cfg.NormalizeAndValidate(); err == nil {
		t.Fatal("expected enabled pool without endpoints to fail")
	}
}
