// Package tooltarget owns the target normalization and authorization pipeline
// that runs between schema validation and process exec.
//
// Order of operations (also enforced by Executor):
//
//	1. schema validate    (internal/toolargs)
//	2. target normalize   (this package)
//	3. authorization      (this package)
//	4. preflight          (internal/preflight)
//
// The normalization step is intentionally tolerant of common input shapes
// (URLs, bare hostnames, IPv4) but rejects anything ambiguous: empty host,
// userinfo, control characters, malformed schemes.
package tooltarget

import (
	"fmt"
	"net"
	"net/url"
	"strings"
)

// Normalized is the canonical, comparable representation of a target.
// The Authorization layer MUST operate on Normalized.Host or Normalized.IP
// only — never on the original input string — to prevent suffix-matching
// bypasses such as `example.com.attacker.invalid`.
type Normalized struct {
	// Original is the unmodified caller-supplied target (for diagnostics
	// only — never for authorization).
	Original string
	// Kind discriminates URL vs bare hostname vs IP literal.
	Kind Kind
	// Scheme is the URL scheme when Kind == KindURL; empty otherwise.
	Scheme string
	// Host is the lower-cased hostname (Kind == KindURL or KindHostname) or
	// the IP literal as supplied (Kind == KindIP). Always non-empty for a
	// successfully normalized target.
	Host string
	// IP is the parsed net.IP when Kind == KindIP. nil otherwise.
	IP net.IP
	// Port is the explicit port when present in the input; 0 otherwise.
	Port int
}

// Kind discriminates how the target was classified.
type Kind string

const (
	KindURL      Kind = "url"
	KindHostname Kind = "hostname"
	KindIP       Kind = "ip"
)

// Normalize parses and validates the supplied target. On failure it returns
// a nil *Normalized and a non-nil error suitable for surfacing as
// failure.CodeInvalidTarget.
//
// The parser is conservative: any ambiguous input is rejected rather than
// silently coerced.
func Normalize(raw string) (*Normalized, error) {
	s := strings.TrimSpace(raw)
	if s == "" {
		return nil, fmt.Errorf("target is empty")
	}
	if hasControl(s) {
		return nil, fmt.Errorf("target contains control characters")
	}
	// Try URL first; if it parses with a scheme and host, treat as URL.
	if u, err := url.Parse(s); err == nil && u.Scheme != "" && u.Host != "" {
		if u.User != nil {
			// userinfo is explicitly forbidden
			return nil, fmt.Errorf("userinfo URL not allowed")
		}
		host := u.Hostname()
		if host == "" {
			return nil, fmt.Errorf("URL has no host")
		}
		switch strings.ToLower(u.Scheme) {
		case "http", "https":
			// allowed
		default:
			return nil, fmt.Errorf("scheme %q not allowed", u.Scheme)
		}
		low := strings.ToLower(host)
		if ip := net.ParseIP(low); ip != nil {
			return &Normalized{
				Original: raw, Kind: KindURL, Scheme: strings.ToLower(u.Scheme),
				Host: low, IP: ip, Port: portOf(u),
			}, nil
		}
		if !validHostname(low) {
			return nil, fmt.Errorf("URL host %q is not a valid hostname", host)
		}
		return &Normalized{
			Original: raw, Kind: KindURL, Scheme: strings.ToLower(u.Scheme),
			Host: low, Port: portOf(u),
		}, nil
	}
	// Try IP literal.
	if ip := net.ParseIP(s); ip != nil {
		host := ip.String()
		if ip.To4() != nil {
			host = ip.To4().String()
		}
		return &Normalized{Original: raw, Kind: KindIP, Host: host, IP: ip}, nil
	}
	// Bare hostname.
	low := strings.ToLower(s)
	if !validHostname(low) {
		return nil, fmt.Errorf("target %q is not a valid URL, IP, or hostname", raw)
	}
	return &Normalized{Original: raw, Kind: KindHostname, Host: low}, nil
}

// portOf extracts the explicit port from a parsed URL; 0 if absent.
func portOf(u *url.URL) int {
	if p := u.Port(); p != "" {
		var port int
		fmt.Sscanf(p, "%d", &port)
		return port
	}
	if strings.EqualFold(u.Scheme, "https") {
		return 443
	}
	if strings.EqualFold(u.Scheme, "http") {
		return 80
	}
	return 0
}

// validHostname applies a deliberately narrow rule: one or more DNS labels
// separated by dots, each label 1–63 characters of [a-z0-9-], not starting
// or ending with '-'. This rejects internationalized names and underscores;
// the agent is expected to punycode them upstream if needed.
func validHostname(h string) bool {
	if h == "" || len(h) > 253 {
		return false
	}
	labels := strings.Split(h, ".")
	if len(labels) < 2 {
		return false
	}
	for _, l := range labels {
		if len(l) == 0 || len(l) > 63 {
			return false
		}
		if l[0] == '-' || l[len(l)-1] == '-' {
			return false
		}
		for i := 0; i < len(l); i++ {
			c := l[i]
			if !((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-') {
				return false
			}
		}
	}
	return true
}

// hasControl reports whether s contains any ASCII control character (0x00-0x1F
// or 0x7F). Used to reject shell injection attempts that bypass URL parsing.
func hasControl(s string) bool {
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c < 0x20 || c == 0x7f {
			return true
		}
	}
	return false
}
