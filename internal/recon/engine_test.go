package recon

import (
	"context"
	"testing"
)

func TestEngineRejectsUnknownCollector(t *testing.T) {
	_, err := NewEngine(1).Start(context.Background(), "example.com", "quick", []string{"not-real"})
	if err == nil {
		t.Fatal("expected unknown collector error")
	}
}

func TestNormalizeTarget(t *testing.T) {
	got, err := normalizeTarget("https://example.com:8443/path")
	if err != nil || got != "example.com" {
		t.Fatalf("normalizeTarget() = %q, %v", got, err)
	}
}

func TestNativeRegistryCoversDesinterCollectors(t *testing.T) {
	engine := NewEngine(2)
	required := []string{
		"enterprise", "subdomain", "dns_enum", "asn_bgp", "cdn_ip", "cloud_assets",
		"port_scan", "network_space", "http_probe", "waf_detect", "dir_scan",
		"cms_finger", "source_leak", "js_api", "crawler", "mobile", "github_leak",
		"nuclei_scan", "wayback_history", "site_metadata", "api_probe", "legacy_hunter",
		"screenshot",
	}
	for _, name := range required {
		if _, ok := engine.collectors[name]; !ok {
			t.Fatalf("collector %q is not registered", name)
		}
	}
}
