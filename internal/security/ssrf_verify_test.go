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
		"file:///etc/passwd", "gopher://x", "http://[::1]/", ""}
	for _, u := range bad {
		if err := ValidateOutboundURL(u); err == nil {
			t.Errorf("ValidateOutboundURL(%q) = nil, want error", u)
		}
	}
	for _, u := range []string{"https://api.openai.com/v1", "http://example.com:8080/x"} {
		if err := ValidateOutboundURL(u); err != nil {
			t.Errorf("ValidateOutboundURL(%q) = %v, want nil", u, err)
		}
	}
}

func parseIP(s string) net.IP { return net.ParseIP(s) }
