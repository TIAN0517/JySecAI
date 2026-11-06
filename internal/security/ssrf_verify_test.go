package security

import (
	"net"
	"testing"
)

func TestIsBlockedIP(t *testing.T) {
	blocked := []string{"127.0.0.1", "169.254.169.254", "10.0.0.5", "192.168.1.1",
		"172.16.0.1", "::1", "0.0.0.0", "100.64.0.1", "::ffff:127.0.0.1", "fc00::1"}
	allowed := []string{"8.8.8.8", "1.1.1.1", "2001:4860:4860::8888"}
	for _, s := range blocked {
		if !IsBlockedIP(parseIP(s)) {
			t.Errorf("IsBlockedIP(%s) = false, want true", s)
		}
	}
	for _, s := range allowed {
		if IsBlockedIP(parseIP(s)) {
			t.Errorf("IsBlockedIP(%s) = true, want false", s)
		}
	}
}

func TestValidateOutboundURL(t *testing.T) {
	bad := []string{"http://127.0.0.1:8080/", "http://169.254.169.254/latest",
		"file:///etc/passwd", "gopher://x", "http://[::1]/", "",
		"http://127.0.0.1:18786/v1", "http://10.0.0.1:18787/v1"}
	for _, u := range bad {
		if err := ValidateOutboundURL(u); err == nil {
			t.Errorf("ValidateOutboundURL(%q) = nil, want error", u)
		}
	}
	for _, u := range []string{
		"https://api.openai.com/v1",
		"http://example.com:8080/x",
		"http://127.0.0.1:18787/v1/chat/completions",
		"http://127.0.0.1:18788/v1",
		"http://[::1]:18789/v1",
		"http://localhost:18787/v1",
	} {
		if err := ValidateOutboundURL(u); err != nil {
			t.Errorf("ValidateOutboundURL(%q) = %v, want nil", u, err)
		}
	}
}

func TestIsAllowedLoopbackBridge(t *testing.T) {
	if !IsAllowedLoopbackBridge("127.0.0.1", "18787") {
		t.Fatal("expected 127.0.0.1:18787 allowed")
	}
	if IsAllowedLoopbackBridge("127.0.0.1", "8080") {
		t.Fatal("expected 127.0.0.1:8080 blocked")
	}
	if IsAllowedLoopbackBridge("8.8.8.8", "18787") {
		t.Fatal("expected public IP with bridge port blocked")
	}
}

func parseIP(s string) net.IP { return net.ParseIP(s) }
