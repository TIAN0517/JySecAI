package handler

import (
	"bytes"
	"net/http"
	"net/url"
	"strings"
	"text/template"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/handler/xsstemplates"
)

// defaultXSSModules are the modules rendered into every image payload.
// Sensitive modules stay out: rendering them would collect session cookies
// or form values without the HITL arming path.
var defaultXSSModules = []string{"metadata", "keepsession"}

type xssModuleVars struct {
	Token              string
	ProjectID          string
	CaptureBase        string
	BeaconBase         string
	MaxBytes           int
	KeepSessionSeconds int
	Html2CanvasURL     string
	FormHookNoMask     bool
}

func (h *XssHandler) renderDefaultModules(payload *database.XssPayload) string {
	names := append([]string{}, defaultXSSModules...)
	if payload.OneTime == 1 {
		names = []string{"metadata"}
	}
	interval := h.cfg.CooldownSeconds
	if interval <= 0 {
		interval = 30
	}
	vars := xssModuleVars{
		Token:              payload.Token,
		ProjectID:          payload.ProjectID,
		CaptureBase:        h.publicBaseURL() + "/xss/capture",
		BeaconBase:         h.publicBaseURL() + "/xss",
		MaxBytes:           h.cfg.XssMaxCaptureBytesEffective(),
		KeepSessionSeconds: interval,
	}
	tpl, err := template.ParseFS(xsstemplates.FS, "*.js.tmpl")
	if err != nil {
		h.logger.Warn("XSS module templates failed to parse")
		return ""
	}
	var buf bytes.Buffer
	for _, name := range names {
		if !xsstemplates.ValidateName(name) {
			continue
		}
		if err := tpl.ExecuteTemplate(&buf, name+".js.tmpl", vars); err != nil {
			h.logger.Warn("XSS module render failed")
			continue
		}
		buf.WriteByte('\n')
	}
	return buf.String()
}

func (h *XssHandler) captureModule(w http.ResponseWriter, r *http.Request, token string) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	payload, ok := h.availablePayload(w, token, false)
	if !ok {
		return
	}
	limit := h.cfg.XssMaxCaptureBytesEffective()
	r.Body = http.MaxBytesReader(w, r.Body, int64(limit*8))
	if err := r.ParseForm(); err != nil {
		http.Error(w, "invalid callback", http.StatusBadRequest)
		return
	}
	kind := strings.TrimSpace(r.Form.Get("kind"))
	if kind == "" && r.Form.Get("canary") != "" {
		h.captureCanary(w, r, payload, r.Form.Get("canary"))
		return
	}
	if kind != "metadata" && kind != "keepsession" {
		http.Error(w, "unsupported callback", http.StatusBadRequest)
		return
	}
	pageURL := truncateBytes(r.Form.Get("url"), limit)
	h.storeModuleHit(w, r, payload, kind, pageURL, r.Form.Get("origin"))
}

func (h *XssHandler) captureKeepSession(w http.ResponseWriter, r *http.Request, token string) {
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		w.Header().Set("Allow", "GET, HEAD")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	payload, ok := h.availablePayload(w, token, false)
	if !ok {
		return
	}
	pageURL := truncateBytes(r.URL.Query().Get("url"), h.cfg.XssMaxCaptureBytesEffective())
	if !h.storeModuleHit(w, r, payload, "keepsession", pageURL, "") {
		return
	}
	w.Header().Set("Content-Type", "image/gif")
	w.Header().Set("Cache-Control", "no-store, private, max-age=0")
	w.WriteHeader(http.StatusOK)
	if r.Method != http.MethodHead {
		_, _ = w.Write(transparentGIF)
	}
}

func (h *XssHandler) storeModuleHit(w http.ResponseWriter, r *http.Request, payload *database.XssPayload, kind, pageURL, origin string) bool {
	ip := collectorClientIP(r, h.cfg.TrustProxyHeaders)
	if !h.allowCollectorRequest(payload.Token, ip, time.Now()) {
		w.Header().Set("Retry-After", "60")
		http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
		return false
	}
	domain := moduleDomain(pageURL, origin, payload.Domain)
	_, accepted, err := h.db.CreateXssCaptureIfAvailable(payload.ID, payload.Token, "", pageURL, domain, truncateBytes(r.UserAgent(), 256), ip, kind)
	if err != nil {
		h.logger.Warn("XSS module storage failed")
		http.Error(w, "callback unavailable", http.StatusServiceUnavailable)
		return false
	}
	if !accepted {
		http.Error(w, "callback expired or already consumed", http.StatusGone)
		return false
	}
	if kind == "keepsession" && (r.Method == http.MethodGet || r.Method == http.MethodHead) {
		return true
	}
	w.WriteHeader(http.StatusNoContent)
	return true
}

func moduleDomain(pageURL, origin, fallback string) string {
	if origin != "" {
		if parsed, err := url.Parse(origin); err == nil && parsed.Host != "" {
			return truncateBytes(parsed.Host, 200)
		}
	}
	if parsed, err := url.Parse(pageURL); err == nil && parsed.Host != "" {
		return truncateBytes(parsed.Host, 200)
	}
	return truncateBytes(fallback, 200)
}
