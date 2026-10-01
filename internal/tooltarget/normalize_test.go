package tooltarget

import "testing"

// Test 7: malformed target rejected (empty).
func TestNormalizeRejectsEmpty(t *testing.T) {
	if _, err := Normalize("   "); err == nil {
		t.Fatalf("expected error on empty target")
	}
}

// Test 7: malformed target rejected (control characters).
func TestNormalizeRejectsControlChars(t *testing.T) {
	if _, err := Normalize("example.com\x00"); err == nil {
		t.Fatalf("expected error on control character")
	}
}

// Test 8: userinfo URL rejected.
func TestNormalizeRejectsUserinfoURL(t *testing.T) {
	if _, err := Normalize("https://user:pass@example.com/"); err == nil {
		t.Fatalf("expected error on userinfo URL")
	}
}

func TestNormalizeAcceptsHTTPSHost(t *testing.T) {
	n, err := Normalize("https://Example.COM:8443/path")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if n.Kind != KindURL {
		t.Fatalf("expected KindURL, got %s", n.Kind)
	}
	if n.Scheme != "https" {
		t.Fatalf("expected https, got %s", n.Scheme)
	}
	if n.Host != "example.com" {
		t.Fatalf("expected lower-cased host, got %q", n.Host)
	}
	if n.Port != 8443 {
		t.Fatalf("expected port 8443, got %d", n.Port)
	}
}

func TestNormalizeAcceptsBareIP(t *testing.T) {
	n, err := Normalize("192.0.2.10")
	if err != nil {
		t.Fatalf("unexpected: %v", err)
	}
	if n.Kind != KindIP {
		t.Fatalf("expected KindIP, got %s", n.Kind)
	}
	if n.Host != "192.0.2.10" {
		t.Fatalf("unexpected host: %s", n.Host)
	}
}

func TestNormalizeAcceptsBareHostname(t *testing.T) {
	n, err := Normalize("example.com")
	if err != nil {
		t.Fatalf("unexpected: %v", err)
	}
	if n.Kind != KindHostname {
		t.Fatalf("expected KindHostname, got %s", n.Kind)
	}
}

// TestCanonicalPreservesAllComponents verifies the canonical form contains
// every component the user supplied: scheme, host, port, path, query.
func TestCanonicalPreservesAllComponents(t *testing.T) {
	cases := []struct {
		in, want string
	}{
		{"http://127.0.0.1:18080/path?q=1", "http://127.0.0.1:18080/path?q=1"},
		{"https://example.com:8443/a", "https://example.com:8443/a"},
		{"192.0.2.10", "192.0.2.10"},
		{"example.com", "example.com"},
		{"HTTPS://Example.COM/A/B?x=1&y=2", "https://example.com/A/B?x=1&y=2"},
	}
	for _, tc := range cases {
		n, err := Normalize(tc.in)
		if err != nil {
			t.Fatalf("normalize(%q): %v", tc.in, err)
		}
		got := n.Canonical()
		if got != tc.want {
			t.Fatalf("Canonical(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}
}

// TestCanonicalNilSafe verifies Canonical handles a nil receiver.
func TestCanonicalNilSafe(t *testing.T) {
	var n *Normalized
	if got := n.Canonical(); got != "" {
		t.Fatalf("nil Canonical must return \"\", got %q", got)
	}
}

func TestNormalizeRejectsScheme(t *testing.T) {
	if _, err := Normalize("ftp://example.com"); err == nil {
		t.Fatalf("expected error on ftp scheme")
	}
}

func TestNormalizeRejectsBadHostname(t *testing.T) {
	if _, err := Normalize("not a host!"); err == nil {
		t.Fatalf("expected error on bad hostname")
	}
}
