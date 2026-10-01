package xsshook

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"go.uber.org/zap"
	"go.uber.org/zap/zaptest/observer"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"net"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

func collectorFixture(t *testing.T, cooldown int) (*Collector, *database.DB, *database.XSSPayload) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "fixture.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	p, err := db.CreateXSSPayload(&database.XSSPayload{Name: "synthetic", Script: "synthetic", Enabled: 1, CallbackToken: strings.Repeat("a", 64)})
	if err != nil {
		t.Fatal(err)
	}
	c := NewCollector(db, config.XssConfig{Enabled: true, Token: "legacy-synthetic-only", CooldownSeconds: cooldown}, zap.NewNop())
	return c, db, p
}
func requestFixture(id string) CaptureRequest {
	return CaptureRequest{PayloadID: id, SourceURL: "http://127.0.0.1/test", Cookies: []Cookie{{Name: "jysec_test", Value: "1"}}, LocalStorage: map[string]string{"synthetic": "1"}, SessionStorage: map[string]string{}}
}
func callback(c *Collector, req CaptureRequest, token string) *httptest.ResponseRecorder {
	body, _ := json.Marshal(req)
	return rawCallback(c, body, token)
}
func rawCallback(c *Collector, body []byte, token string) *httptest.ResponseRecorder {
	r := httptest.NewRequest("POST", "/api/xss/capture", bytes.NewReader(body))
	r.RemoteAddr = "192.0.2.1:2222"
	r.Header.Set("X-XSS-Token", token)
	w := httptest.NewRecorder()
	c.ServeHTTP(w, r)
	return w
}
func captures(t *testing.T, db *database.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow("SELECT count(*) FROM xss_captures").Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}
func TestXSSCollectorRichCallbackAndEmptyCookie(t *testing.T) {
	c, db, p := collectorFixture(t, 0)
	req := requestFixture(p.ID)
	for _, empty := range []bool{false, true} {
		if empty {
			req.Cookies = nil
		}
		w := callback(c, req, p.CallbackToken)
		if w.Code != 204 {
			t.Fatalf("code %d", w.Code)
		}
		if w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("X-Content-Type-Options") != "nosniff" {
			t.Fatal("headers")
		}
	}
	if captures(t, db) != 2 {
		t.Fatal("empty callback lost")
	}
	p2, err := db.GetXSSPayload(p.ID)
	if err != nil || p2.Status != "fired" {
		t.Fatal(err)
	}
}
func TestXSSCollectorLegacyGlobalTokenOnlyForEmptyPerPayloadToken(t *testing.T) {
	c, db, p := collectorFixture(t, 0)
	req := requestFixture(p.ID)
	if w := callback(c, req, c.cfg.Token); w.Code != 403 {
		t.Fatal("global token overrides per-payload token")
	}
	for _, tok := range []interface{}{nil, ""} {
		if _, err := db.Exec("UPDATE xss_payloads SET callback_token=? WHERE id=?", tok, p.ID); err != nil {
			t.Fatal(err)
		}
		if w := callback(c, req, c.cfg.Token); w.Code != 204 {
			t.Fatal(w.Code)
		}
	}
	if captures(t, db) != 2 {
		t.Fatal("legacy callback missing")
	}
}
func TestXSSCollectorEnabledDomainAndInvalidToken(t *testing.T) {
	c, db, p := collectorFixture(t, 0)
	req := requestFixture(p.ID)
	for _, tok := range []string{"", "wrong", "bad token", strings.Repeat("a", 513)} {
		if w := callback(c, req, tok); w.Code != 403 {
			t.Fatal("bad token accepted")
		}
	}
	db.Exec("UPDATE xss_payloads SET enabled=0 WHERE id=?", p.ID)
	if w := callback(c, req, p.CallbackToken); w.Code != 403 {
		t.Fatal("disabled")
	}
	db.Exec("UPDATE xss_payloads SET enabled=1,domain='example.com',domain_only=1 WHERE id=?", p.ID)
	for _, test := range []struct {
		url  string
		code int
	}{{"http://example.com/test", 204}, {"https://sub.example.com/test", 204}, {"https://badexample.com/test", 403}, {"https://example.com.evil.invalid/test", 403}, {"https://example.com@evil.invalid/test", 400}} {
		req.SourceURL = test.url
		if w := callback(c, req, p.CallbackToken); w.Code != test.code {
			t.Fatal(test.url, w.Code)
		}
	}
}
func TestXSSCollectorLimitsMethodsAndMalformedJSON(t *testing.T) {
	c, db, p := collectorFixture(t, 0)
	for _, method := range []string{"GET", "PUT", "DELETE", "PATCH"} {
		r := httptest.NewRequest(method, "/api/xss/capture", nil)
		w := httptest.NewRecorder()
		c.ServeHTTP(w, r)
		if w.Code != 405 {
			t.Fatal(method, w.Code)
		}
	}
	for _, body := range []string{"{", "{} {}", `{"payload_id":"not-a-uuid"}`, `{"unexpected":1}`} {
		if w := rawCallback(c, []byte(body), p.CallbackToken); w.Code != 400 {
			t.Fatal(w.Code)
		}
	}
	if w := rawCallback(c, bytes.Repeat([]byte(" "), MaxBodyBytes+1), p.CallbackToken); w.Code != 413 {
		t.Fatal("body size", w.Code)
	}
	req := requestFixture(p.ID)
	req.PageTitle = strings.Repeat("a", 4097)
	if w := callback(c, req, p.CallbackToken); w.Code != 413 {
		t.Fatal("field size", w.Code)
	}
	req = requestFixture(p.ID)
	req.Cookies[0].Value = strings.Repeat("a", 65537)
	if w := callback(c, req, p.CallbackToken); w.Code != 413 {
		t.Fatal("cookie size", w.Code)
	}
	req = requestFixture(p.ID)
	req.UserAgent = strings.Repeat("a", 4097)
	if w := callback(c, req, p.CallbackToken); w.Code != 413 {
		t.Fatal("UA size", w.Code)
	}
	if captures(t, db) != 0 {
		t.Fatal("rejected callback stored")
	}
}
func TestXSSCollectorTrustedProxyAndSpoofedHeaders(t *testing.T) {
	r := httptest.NewRequest("POST", "/api/xss/capture", nil)
	r.RemoteAddr = "192.0.2.1:12"
	r.Header.Set("CF-Connecting-IP", "198.51.100.1")
	r.Header.Set("X-Real-IP", "198.51.100.2")
	r.Header.Set("X-Forwarded-For", "198.51.100.3, 127.0.0.1")
	if ClientIP(r, []string{"127.0.0.1", "192.0.2.1"}) != "192.0.2.1" {
		t.Fatal("direct spoof accepted")
	}
	r.RemoteAddr = "127.0.0.1:12"
	if ClientIP(r, nil) != "127.0.0.1" {
		t.Fatal("implicit local trust")
	}
	for _, want := range []string{"198.51.100.1", "198.51.100.2", "198.51.100.3"} {
		if got := ClientIP(r, []string{"127.0.0.1"}); got != want {
			t.Fatal(got)
		}
		if want == "198.51.100.1" {
			r.Header.Del("CF-Connecting-IP")
		} else {
			r.Header.Del("X-Real-IP")
		}
	}
}
func TestXSSCollectorCooldownConcurrentRaceSafe(t *testing.T) {
	c, db, p := collectorFixture(t, 60)
	req := requestFixture(p.ID)
	var wg sync.WaitGroup
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if w := callback(c, req, p.CallbackToken); w.Code != 204 {
				t.Errorf("code %d", w.Code)
			}
		}()
	}
	wg.Wait()
	if n := captures(t, db); n != 1 {
		t.Fatalf("cooldown persisted %d", n)
	}
	c.now = func() time.Time { return time.Now().Add(61 * time.Second) }
	if w := callback(c, req, p.CallbackToken); w.Code != 204 {
		t.Fatal(w.Code)
	}
	if captures(t, db) != 2 {
		t.Fatal("cooldown expiry")
	}
}
func TestXSSCollectorPersistenceFailureLogsWithoutSecrets(t *testing.T) {
	c, db, p := collectorFixture(t, 60)
	core, logs := observer.New(zap.DebugLevel)
	c.log = zap.New(core)
	if _, err := db.Exec(`CREATE TRIGGER fail_capture BEFORE INSERT ON xss_captures BEGIN SELECT RAISE(FAIL, 'synthetic failure'); END`); err != nil {
		t.Fatal(err)
	}
	if w := callback(c, requestFixture(p.ID), p.CallbackToken); w.Code != 500 {
		t.Fatal("failure disguised as success", w.Code)
	}
	if len(c.lastSeen) != 0 || captures(t, db) != 0 {
		t.Fatal("failed capture consumed cooldown or persisted")
	}
	if logs.FilterMessage("XSS capture persistence failed").Len() != 1 {
		t.Fatal("missing error log")
	}
	rendered := fmt.Sprint(logs.All())
	if strings.Contains(rendered, p.CallbackToken) || strings.Contains(rendered, "jysec_test") {
		t.Fatal("sensitive log")
	}
	db.Exec("DROP TRIGGER fail_capture") // Only this synthetic test DB.
	if w := callback(c, requestFixture(p.ID), p.CallbackToken); w.Code != 204 {
		t.Fatal("retry blocked", w.Code)
	}
}
func TestXSSCollectorShutdownRestartReleasesPort(t *testing.T) {
	c, _, _ := collectorFixture(t, 0)
	probe, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := probe.Addr().(*net.TCPAddr).Port
	probe.Close()
	c.cfg.BindHost = "127.0.0.1"
	c.cfg.BindPort = port
	for i := 0; i < 2; i++ {
		if err = c.Start(); err != nil {
			t.Fatal(err)
		}
		addr := c.Addr()
		resp, err := http.Get("http://" + addr + "/api/xss/capture")
		if err != nil {
			t.Fatal(err)
		}
		resp.Body.Close()
		if resp.StatusCode != 405 {
			t.Fatal(resp.StatusCode)
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		err = c.Stop(ctx)
		cancel()
		if err != nil {
			t.Fatal(err)
		}
		ln, err := net.Listen("tcp", addr)
		if err != nil {
			t.Fatal("port not released", err)
		}
		ln.Close()
	}
}
