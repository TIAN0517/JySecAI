package handler

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"

	"go.uber.org/zap"
)

func newXSSSafetyHandler(t *testing.T, rate int) (*XssHandler, *database.DB) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "xss-safety.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	h := NewXssHandler(db, &config.XssConfig{
		Enabled: true, BindHost: "127.0.0.1", BindPort: 18877,
		PublicURL: "https://callbacks.example.test", CanaryCookieName: "jysec_xss_canary",
		ProbeTTLSeconds: 3600, RateLimitPerMinute: rate, MaxCaptureBytes: 512,
	}, zap.NewNop())
	return h, db
}

func addXSSSafetyPayload(t *testing.T, db *database.DB, token, kind string, oneTime bool, expires time.Time) *database.XssPayload {
	t.Helper()
	p := &database.XssPayload{
		Token: token, Name: "safety-test", Type: kind, Payload: "generated",
		Config: []byte("{}"), Enabled: 1, OneTime: xssBoolToInt(oneTime), ExpiresAt: &expires,
	}
	id, err := db.CreateXssPayload(p)
	if err != nil {
		t.Fatalf("CreateXssPayload: %v", err)
	}
	p.ID = id
	return p
}

func TestRenderCollectorJSOnlySendsJySecCanary(t *testing.T) {
	h, _ := newXSSSafetyHandler(t, 30)
	js := h.renderCollectorJS(&database.XssPayload{Token: strings.Repeat("a", 40)})
	for _, forbidden := range []string{"encodeURIComponent(document.cookie)", "btoa(document.cookie)", "?cookie="} {
		if strings.Contains(js, forbidden) {
			t.Fatalf("collector transmits full cookie through %q: %s", forbidden, js)
		}
	}
	if !strings.Contains(js, "jysec_xss_canary") || !strings.Contains(js, "?canary=") {
		t.Fatalf("collector does not use the canary-only channel: %s", js)
	}
}

func TestNormalizeCanaryCookieRejectsSessionCookie(t *testing.T) {
	if got, ok := normalizeCanaryCookie("session=secret; auth=jwt", "jysec_xss_canary", 512); ok || got != "" {
		t.Fatalf("session cookie was accepted: %q", got)
	}
	want := `jysec_xss_canary=<probe>"'`
	if got, ok := normalizeCanaryCookie("session=secret; "+want+"; auth=jwt", "jysec_xss_canary", 512); !ok || got != want {
		t.Fatalf("canary was not isolated: got %q, ok=%v", got, ok)
	}
}

func TestOneTimeCanaryCaptureAndSpecialCharacters(t *testing.T) {
	h, db := newXSSSafetyHandler(t, 30)
	token := strings.Repeat("b", 40)
	p := addXSSSafetyPayload(t, db, token, "image", true, time.Now().Add(time.Hour))
	canary := `jysec_xss_canary=<probe>"'`
	target := "/xss/" + token + ".gif?canary=" + url.QueryEscape(canary)

	first := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, target, nil)
	req.RemoteAddr = "192.0.2.25:4321"
	h.serveCollector(first, req)
	if first.Code != http.StatusOK {
		t.Fatalf("first callback status=%d body=%q", first.Code, first.Body.String())
	}
	captures, err := db.ListXssCapturesByPayload(p.ID)
	if err != nil || len(captures) != 1 {
		t.Fatalf("captures=%d err=%v", len(captures), err)
	}
	if captures[0].Cookie != canary || strings.Contains(captures[0].Cookie, "session=") {
		t.Fatalf("unexpected stored value: %q", captures[0].Cookie)
	}

	second := httptest.NewRecorder()
	h.serveCollector(second, httptest.NewRequest(http.MethodGet, target, nil))
	if second.Code != http.StatusGone {
		t.Fatalf("second callback status=%d, want %d", second.Code, http.StatusGone)
	}
}

func TestInteractionProbeIsOneTimeAndMetadataMinimal(t *testing.T) {
	h, db := newXSSSafetyHandler(t, 30)
	token := strings.Repeat("c", 40)
	p := addXSSSafetyPayload(t, db, token, "probe", true, time.Now().Add(time.Hour))

	first := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/probe/"+token+"?secret=must-not-store", strings.NewReader("body=must-not-store"))
	req.Header.Set("Cookie", "session=must-not-store")
	req.RemoteAddr = "127.0.0.1:9000"
	// Spoofed: the default configuration must not record this as the client IP.
	req.Header.Set("CF-Connecting-IP", "198.51.100.10")
	h.serveProbe(first, req)
	if first.Code != http.StatusNoContent {
		t.Fatalf("probe status=%d body=%q", first.Code, first.Body.String())
	}
	captures, err := db.ListXssCapturesByPayload(p.ID)
	if err != nil || len(captures) != 1 {
		t.Fatalf("captures=%d err=%v", len(captures), err)
	}
	got := captures[0]
	// The recorded IP is the real peer. A header the client chose must never
	// become the identity the operator sees, nor the rate-limit key.
	if got.IP != "127.0.0.1" {
		t.Errorf("probe recorded IP %q; a spoofed proxy header was trusted", got.IP)
	}
	if got.Cookie != probeCaptureMarker || got.URL != "" || got.UserAgent != "" || got.Extra != "interaction-probe" {
		t.Fatalf("unexpected probe capture: %+v", got)
	}

	second := httptest.NewRecorder()
	h.serveProbe(second, httptest.NewRequest(http.MethodGet, "/probe/"+token, nil))
	if second.Code != http.StatusGone {
		t.Fatalf("replayed probe status=%d, want %d", second.Code, http.StatusGone)
	}
}

func TestExpiredAndRateLimitedCallbacks(t *testing.T) {
	h, db := newXSSSafetyHandler(t, 1)
	expiredToken := strings.Repeat("d", 40)
	addXSSSafetyPayload(t, db, expiredToken, "image", false, time.Now().Add(-time.Minute))
	expired := httptest.NewRecorder()
	h.serveCollector(expired, httptest.NewRequest(http.MethodGet, "/xss/"+expiredToken+".gif?canary=jysec_xss_canary%3Dok", nil))
	if expired.Code != http.StatusGone {
		t.Fatalf("expired callback status=%d, want %d", expired.Code, http.StatusGone)
	}

	token := strings.Repeat("e", 40)
	addXSSSafetyPayload(t, db, token, "image", false, time.Now().Add(time.Hour))
	target := "/xss/" + token + ".gif?canary=jysec_xss_canary%3Dok"
	first := httptest.NewRecorder()
	h.serveCollector(first, httptest.NewRequest(http.MethodGet, target, nil))
	if first.Code != http.StatusOK {
		t.Fatalf("first status=%d", first.Code)
	}
	second := httptest.NewRecorder()
	h.serveCollector(second, httptest.NewRequest(http.MethodGet, target, nil))
	if second.Code != http.StatusTooManyRequests {
		t.Fatalf("rate-limited status=%d, want %d", second.Code, http.StatusTooManyRequests)
	}
}

// TestCollectorClientIPIgnoresSpoofedProxyHeaders pins the default behaviour:
// CF-Connecting-IP is attacker-controlled unless a deployment opts in. A
// same-host reverse proxy forwards the client's header verbatim, so a loopback
// peer is not evidence of a trusted tunnel, and trusting it let any visitor mint
// a fresh rate-limit bucket per request against the unauthenticated collector.
func TestCollectorClientIPIgnoresSpoofedProxyHeaders(t *testing.T) {
	direct := httptest.NewRequest(http.MethodGet, "/", nil)
	direct.RemoteAddr = "203.0.113.7:1234"
	direct.Header.Set("CF-Connecting-IP", "198.51.100.9")
	if got := collectorClientIP(direct, false); got != "203.0.113.7" {
		t.Fatalf("trusted spoofed header from direct peer: %q", got)
	}

	// Same request arriving through a local proxy must still not be believed
	// while the opt-in is off.
	proxied := httptest.NewRequest(http.MethodGet, "/", nil)
	proxied.RemoteAddr = "127.0.0.1:1234"
	proxied.Header.Set("CF-Connecting-IP", "198.51.100.9")
	if got := collectorClientIP(proxied, false); got != "127.0.0.1" {
		t.Fatalf("trusted spoofed header from loopback peer: %q", got)
	}
}

// TestCollectorClientIPHonoursProxyHeadersWhenOptedIn keeps the Cloudflare
// deployment working once the operator has confirmed their edge overwrites the
// header.
func TestCollectorClientIPHonoursProxyHeadersWhenOptedIn(t *testing.T) {
	proxied := httptest.NewRequest(http.MethodGet, "/", nil)
	proxied.RemoteAddr = "127.0.0.1:1234"
	proxied.Header.Set("CF-Connecting-IP", "198.51.100.9")
	if got := collectorClientIP(proxied, true); got != "198.51.100.9" {
		t.Fatalf("opted-in deployment did not honour the tunnel header: %q", got)
	}

	// Even opted in, a non-loopback peer is still not believed.
	direct := httptest.NewRequest(http.MethodGet, "/", nil)
	direct.RemoteAddr = "203.0.113.7:1234"
	direct.Header.Set("CF-Connecting-IP", "198.51.100.9")
	if got := collectorClientIP(direct, true); got != "203.0.113.7" {
		t.Fatalf("opted-in mode trusted a header from a direct peer: %q", got)
	}

	// A malformed header must fall back to the peer rather than yield "".
	garbage := httptest.NewRequest(http.MethodGet, "/", nil)
	garbage.RemoteAddr = "127.0.0.1:1234"
	garbage.Header.Set("CF-Connecting-IP", "not-an-ip")
	if got := collectorClientIP(garbage, true); got != "127.0.0.1" {
		t.Fatalf("malformed header produced %q", got)
	}
}
