package config

import "testing"

func TestXssCanaryCookieNameCannotTargetAuthenticationCookie(t *testing.T) {
	for _, configured := range []string{"", "session", "jwt", "jysec_session", "jysec_xss_canary; session"} {
		cfg := XssConfig{CanaryCookieName: configured}
		if got := cfg.XssCanaryCookieNameEffective(); got != "jysec_xss_canary" {
			t.Fatalf("configured %q resolved to unsafe name %q", configured, got)
		}
	}
}

func TestXssSafetyLimitsAreBounded(t *testing.T) {
	cfg := XssConfig{ProbeTTLSeconds: 1, RateLimitPerMinute: 10000, MaxCaptureBytes: 1}
	if got := cfg.XssProbeTTLSecondsEffective(); got != 60 {
		t.Fatalf("ttl=%d, want 60", got)
	}
	if got := cfg.XssRateLimitPerMinuteEffective(); got != 300 {
		t.Fatalf("rate=%d, want 300", got)
	}
	if got := cfg.XssMaxCaptureBytesEffective(); got != 64 {
		t.Fatalf("capture bytes=%d, want 64", got)
	}
}
