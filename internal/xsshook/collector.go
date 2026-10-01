package xsshook

import (
	"context"
	"crypto/sha256"
	"crypto/subtle"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"go.uber.org/zap"
	"jysecai/internal/config"
	"jysecai/internal/database"
)

const MaxBodyBytes = 128 * 1024

// Collector contains no worker/scanner/model integration. It only validates and
// persists an already authorized browser callback.
type Collector struct {
	db        *database.DB
	cfg       config.XssConfig
	log       *zap.Logger
	mu        sync.Mutex
	lastSeen  map[string]time.Time
	lifecycle sync.Mutex
	server    *http.Server
	listener  net.Listener
	now       func() time.Time
}

func NewCollector(db *database.DB, cfg config.XssConfig, log *zap.Logger) *Collector {
	if log == nil {
		log = zap.NewNop()
	}
	return &Collector{db: db, cfg: cfg, log: log, lastSeen: map[string]time.Time{}, now: time.Now}
}
func (c *Collector) Start() error {
	c.lifecycle.Lock()
	defer c.lifecycle.Unlock()
	if c.server != nil {
		return nil
	}
	if !c.cfg.Enabled {
		return nil
	}
	ln, err := net.Listen("tcp", net.JoinHostPort(c.cfg.XssBindHostEffective(), fmt.Sprint(c.cfg.XssBindPortEffective())))
	if err != nil {
		return err
	}
	srv := &http.Server{Handler: c, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: 15 * time.Second, IdleTimeout: 30 * time.Second, MaxHeaderBytes: 16 * 1024}
	c.listener = ln
	c.server = srv
	go func() {
		if err := srv.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
			c.log.Error("XSS listener failed", zap.String("error_type", fmt.Sprintf("%T", err)))
		}
	}()
	return nil
}
func (c *Collector) Stop(ctx context.Context) error {
	c.lifecycle.Lock()
	defer c.lifecycle.Unlock()
	if c.server == nil {
		return nil
	}
	err := c.server.Shutdown(ctx)
	if err != nil {
		_ = c.server.Close()
	}
	_ = c.listener.Close()
	c.server = nil
	c.listener = nil
	return err
}
func (c *Collector) Addr() string {
	c.lifecycle.Lock()
	defer c.lifecycle.Unlock()
	if c.listener == nil {
		return ""
	}
	return c.listener.Addr().String()
}
func validSecret(v string) bool {
	if len(v) == 0 || len(v) > 512 {
		return false
	}
	for _, r := range v {
		if r <= 32 || r == 127 {
			return false
		}
	}
	return true
}
func tokenEqual(a, b string) bool {
	if !validSecret(a) || !validSecret(b) {
		return false
	}
	x, y := sha256.Sum256([]byte(a)), sha256.Sum256([]byte(b))
	return subtle.ConstantTimeCompare(x[:], y[:]) == 1
}
func ClientIP(r *http.Request, trusted []string) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	peer := net.ParseIP(host)
	if peer == nil {
		return "unknown"
	}
	allow := false
	// Trust must be explicit and local; a LAN CIDR or arbitrary forwarded value
	// cannot expand this boundary.
	if peer.IsLoopback() {
		for _, s := range trusted {
			ip := net.ParseIP(s)
			if ip != nil && peer.Equal(ip) {
				allow = true
				break
			}
		}
	}
	if allow {
		for _, key := range []string{"CF-Connecting-IP", "X-Real-IP", "X-Forwarded-For"} {
			v := strings.TrimSpace(strings.Split(r.Header.Get(key), ",")[0])
			if ip := net.ParseIP(v); ip != nil {
				return ip.String()
			}
		}
	}
	return peer.String()
}
func NormalizeDomain(v string) (string, error) {
	v = strings.ToLower(strings.TrimSuffix(strings.TrimSpace(v), "."))
	if v == "" || len(v) > 253 {
		return "", fmt.Errorf("invalid domain")
	}
	if ip := net.ParseIP(v); ip != nil {
		return ip.String(), nil
	}
	for _, label := range strings.Split(v, ".") {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return "", fmt.Errorf("invalid domain")
		}
		for _, r := range label {
			if !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9' || r == '-') {
				return "", fmt.Errorf("invalid domain")
			}
		}
	}
	return v, nil
}
func sourceURL(v string) (*url.URL, error) {
	u, err := url.Parse(v)
	if err != nil || u.Hostname() == "" || (u.Scheme != "http" && u.Scheme != "https") || u.User != nil {
		return nil, fmt.Errorf("invalid source URL")
	}
	return u, nil
}
func DomainAllows(domain, source string) bool {
	expected, err := NormalizeDomain(domain)
	if err != nil {
		return false
	}
	u, err := sourceURL(source)
	if err != nil {
		return false
	}
	host, err := NormalizeDomain(u.Hostname())
	if err != nil {
		return false
	}
	return host == expected || (net.ParseIP(expected) == nil && strings.HasSuffix(host, "."+expected))
}
func fieldsWithinLimit(r CaptureRequest) bool {
	if len(r.PayloadID) > 64 || len(r.SourceURL) > 8192 || len(r.PageTitle) > 4096 || len(r.UserAgent) > 4096 || len(r.URLFragment) > 8192 || len(r.Cookies) > 128 {
		return false
	}
	for _, v := range r.Cookies {
		if len(v.Name) > 1024 || len(v.Value) > 65536 || len(v.Domain) > 253 || len(v.Path) > 4096 {
			return false
		}
	}
	for _, m := range []map[string]string{r.LocalStorage, r.SessionStorage} {
		if len(m) > 128 {
			return false
		}
		for k, v := range m {
			if len(k) > 1024 || len(v) > 16384 {
				return false
			}
		}
	}
	return true
}
func (c *Collector) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	if r.URL.Path != "/api/xss/capture" {
		http.NotFound(w, r)
		return
	}
	if !c.cfg.Enabled {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-XSS-Token")
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "POST, OPTIONS")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if len(r.URL.RawQuery) > 1024 || len(r.UserAgent()) > 4096 {
		http.Error(w, "request too large", 413)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, MaxBodyBytes)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		var max *http.MaxBytesError
		if errors.As(err, &max) {
			http.Error(w, "request too large", 413)
		} else {
			http.Error(w, "invalid body", 400)
		}
		return
	}
	var req CaptureRequest
	dec := json.NewDecoder(strings.NewReader(string(body)))
	dec.DisallowUnknownFields()
	if err = dec.Decode(&req); err != nil {
		http.Error(w, "invalid JSON", 400)
		return
	}
	if err = dec.Decode(new(interface{})); err != io.EOF {
		http.Error(w, "invalid JSON", 400)
		return
	}
	if !fieldsWithinLimit(req) {
		http.Error(w, "field too large", 413)
		return
	}
	if _, err = uuid.Parse(req.PayloadID); err != nil {
		http.Error(w, "invalid payload", 400)
		return
	}
	u, err := sourceURL(req.SourceURL)
	if err != nil {
		http.Error(w, "invalid source URL", 400)
		return
	}
	token := r.Header.Get("X-XSS-Token")
	if token == "" {
		token = r.URL.Query().Get("token")
	}
	if !validSecret(token) {
		http.Error(w, "forbidden", 403)
		return
	}
	payload, err := c.db.GetXSSPayload(req.PayloadID)
	if errors.Is(err, sql.ErrNoRows) {
		http.Error(w, "forbidden", 403)
		return
	}
	if err != nil {
		c.log.Error("XSS payload lookup failed", zap.String("payload_id", req.PayloadID))
		http.Error(w, "persistence unavailable", 500)
		return
	}
	expected := payload.CallbackToken
	if expected == "" {
		expected = c.cfg.Token
	}
	if !tokenEqual(token, expected) || payload.Enabled != 1 || payload.Status == "expired" || (payload.DomainOnly != 0 && !DomainAllows(payload.Domain, req.SourceURL)) {
		http.Error(w, "forbidden", 403)
		return
	}
	ip := ClientIP(r, c.cfg.TrustedLocalProxies)
	cap := &database.XSSCapture{PayloadID: payload.ID, ProjectID: payload.ProjectID, ConversationID: payload.ConversationID, SourceURL: req.SourceURL, PageTitle: req.PageTitle, UserAgent: req.UserAgent, ClientIP: ip, URLFragment: req.URLFragment, LocalStorage: req.LocalStorage, SessionStorage: req.SessionStorage, Cookies: []database.XSSCookie{}}
	for _, ck := range req.Cookies {
		cap.Cookies = append(cap.Cookies, database.XSSCookie{Name: ck.Name, Value: ck.Value, Domain: ck.Domain, Path: ck.Path, Secure: ck.Secure, HttpOnly: ck.HttpOnly})
	}
	// One mutex covers check + persist + timestamp. No cleanup goroutine can race,
	// and failed inserts never consume the cooldown window.
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.now()
	window := time.Duration(c.cfg.CooldownSeconds) * time.Second
	key := payload.ID + "|" + ip
	if window > 0 {
		for k, t := range c.lastSeen {
			if !now.Before(t.Add(window)) {
				delete(c.lastSeen, k)
			}
		}
		if t, ok := c.lastSeen[key]; ok && now.Before(t.Add(window)) {
			w.WriteHeader(204)
			return
		}
		if len(c.lastSeen) >= 4096 {
			http.Error(w, "collector capacity reached", 429)
			return
		}
	}
	row, err := c.db.PersistXSSCallback(cap)
	if err != nil {
		c.log.Error("XSS capture persistence failed", zap.String("payload_id", payload.ID), zap.String("client_ip", ip), zap.String("source_host", u.Hostname()))
		http.Error(w, "persistence failed", 500)
		return
	}
	if window > 0 {
		c.lastSeen[key] = now
	}
	c.log.Info("XSS callback persisted", zap.String("capture_id", row.ID), zap.String("payload_id", payload.ID), zap.String("source_host", u.Hostname()), zap.String("client_ip", ip), zap.Int("cookies", len(req.Cookies)), zap.Int("local_storage", len(req.LocalStorage)), zap.Int("session_storage", len(req.SessionStorage)))
	w.WriteHeader(http.StatusNoContent)
}
