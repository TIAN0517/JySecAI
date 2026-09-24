package handler

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/database"

	"go.uber.org/zap"
)

func newXssTestHandler(t *testing.T, cfg *config.XssConfig) (*XssHandler, *database.DB) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "xss.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return NewXssHandler(db, cfg, zap.NewNop()), db
}

func createXssTestPayload(t *testing.T, db *database.DB, token string, enabled, domainOnly int, domain string) int64 {
	t.Helper()
	id, err := db.CreateXssPayload(&database.XssPayload{
		Token:      token,
		Name:       "test",
		Type:       "image",
		Payload:    "",
		Enabled:    enabled,
		DomainOnly: domainOnly,
		Domain:     domain,
	})
	if err != nil {
		t.Fatal(err)
	}
	return id
}

func TestXssCollectorFallbackURLIncludesConfiguredPort(t *testing.T) {
	h, db := newXssTestHandler(t, &config.XssConfig{
		Enabled:         true,
		BindHost:        "127.0.0.1",
		BindPort:        18877,
		CooldownSeconds: -1,
	})
	createXssTestPayload(t, db, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1, 0, "")

	req := httptest.NewRequest(http.MethodGet, "http://collector/xss/token-a.js", nil)
	rec := httptest.NewRecorder()
	h.ServeCollectorJS(rec, req, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body.String())
	}
	if !strings.Contains(rec.Body.String(), "http://127.0.0.1:18877/xss/token-a.gif") {
		t.Fatalf("collector callback URL does not include configured port: %s", rec.Body.String())
	}
}

func TestXssCollectorRejectsDisabledPayload(t *testing.T) {
	h, db := newXssTestHandler(t, &config.XssConfig{
		Enabled:         true,
		BindHost:        "127.0.0.1",
		BindPort:        18877,
		CooldownSeconds: -1,
	})
	createXssTestPayload(t, db, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", 0, 0, "")

	req := httptest.NewRequest(http.MethodGet, "http://collector/xss/token-disabled.js", nil)
	rec := httptest.NewRecorder()
	h.ServeCollectorJS(rec, req, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

	if rec.Code != http.StatusNotFound {
		t.Fatalf("disabled payload status = %d, want 404", rec.Code)
	}
}

func TestXssCollectorEnforcesDomainOnly(t *testing.T) {
	h, db := newXssTestHandler(t, &config.XssConfig{
		Enabled:         true,
		BindHost:        "127.0.0.1",
		BindPort:        18877,
		CooldownSeconds: -1,
	})
	createXssTestPayload(t, db, "cccccccccccccccccccccccccccccccccccccccc", 1, 1, "example.com")

	req := httptest.NewRequest(http.MethodGet, "http://collector/xss/token-domain.js", nil)
	req.Header.Set("Referer", "https://evil.example.net/page")
	rec := httptest.NewRecorder()
	h.ServeCollectorJS(rec, req, "cccccccccccccccccccccccccccccccccccccccc")
	if rec.Code != http.StatusNotFound {
		t.Fatalf("wrong-domain status = %d, want 404", rec.Code)
	}

	req = httptest.NewRequest(http.MethodGet, "http://collector/xss/token-domain.js", nil)
	req.Header.Set("Referer", "https://app.example.com/page")
	rec = httptest.NewRecorder()
	h.ServeCollectorJS(rec, req, "cccccccccccccccccccccccccccccccccccccccc")
	if rec.Code != http.StatusOK {
		t.Fatalf("authorized-domain status = %d, want 200", rec.Code)
	}
}

func TestXssCaptureRecordsHitWithoutReadableCookie(t *testing.T) {
	h, db := newXssTestHandler(t, &config.XssConfig{
		Enabled:         true,
		BindHost:        "127.0.0.1",
		BindPort:        18877,
		CooldownSeconds: -1,
	})
	createXssTestPayload(t, db, "dddddddddddddddddddddddddddddddddddddddd", 1, 0, "")

	form := url.Values{}
	form.Set("url", "https://example.com/login")
	req := httptest.NewRequest(http.MethodPost, "http://collector/xss/token-empty-cookie/capture", strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("User-Agent", "JySecAI-Test")
	req.RemoteAddr = "127.0.0.1:54321"
	rec := httptest.NewRecorder()
	h.Capture(rec, req, "dddddddddddddddddddddddddddddddddddddddd")

	if rec.Code != http.StatusOK {
		t.Fatalf("capture status = %d, body = %s", rec.Code, rec.Body.String())
	}
	captures, err := db.ListXssCaptures()
	if err != nil {
		t.Fatal(err)
	}
	if len(captures) != 1 {
		t.Fatalf("captures = %d, want 1", len(captures))
	}
	if captures[0].Cookie != "" || captures[0].URL != "https://example.com/login" || captures[0].UserAgent != "JySecAI-Test" {
		t.Fatalf("unexpected capture: %#v", captures[0])
	}
}

func TestXssCaptureDoesNotTrustForwardedIPFromDirectClient(t *testing.T) {
	h, db := newXssTestHandler(t, &config.XssConfig{
		Enabled:         true,
		BindHost:        "127.0.0.1",
		BindPort:        18877,
		CooldownSeconds: -1,
	})
	createXssTestPayload(t, db, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 1, 0, "")

	req := httptest.NewRequest(http.MethodGet, "http://collector/xss/token-ip.gif", nil)
	req.RemoteAddr = "203.0.113.10:4567"
	req.Header.Set("X-Forwarded-For", "198.51.100.99")
	rec := httptest.NewRecorder()
	h.ServeCollectorGIF(rec, req, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

	if rec.Code != http.StatusOK {
		t.Fatalf("capture status = %d", rec.Code)
	}
	captures, err := db.ListXssCaptures()
	if err != nil {
		t.Fatal(err)
	}
	if len(captures) != 1 || captures[0].IP != "203.0.113.10" {
		t.Fatalf("forwarded IP was trusted unexpectedly: %#v", captures)
	}
}
