package handler

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"cyberstrike-ai/internal/audit"
	"cyberstrike-ai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

const (
	defaultSecurityOpsURL      = "http://127.0.0.1:8788"
	defaultSecurityOpsTenantID = "dev-tenant"
	securityOpsMaxRequestBytes = 1 << 20
	securityOpsMaxResponseSize = 4 << 20
)

// SecurityOpsHandler exposes a narrow, authenticated bridge to the local
// security control plane. It is deliberately not a generic reverse proxy.
type SecurityOpsHandler struct {
	baseURL  *url.URL
	tenantID string
	client   *http.Client
	logger   *zap.Logger
	audit    *audit.Service
}

func NewSecurityOpsHandler(logger *zap.Logger) *SecurityOpsHandler {
	baseURL := strings.TrimSpace(os.Getenv("JYSEC_CONTROL_PLANE_URL"))
	if baseURL == "" {
		baseURL = defaultSecurityOpsURL
	}
	parsed, err := url.Parse(baseURL)
	if err != nil || parsed.Scheme == "" || parsed.Host == "" {
		parsed, _ = url.Parse(defaultSecurityOpsURL)
		if logger != nil {
			logger.Warn("invalid JYSEC_CONTROL_PLANE_URL; using local default", zap.String("value", baseURL))
		}
	}
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	parsed.RawQuery = ""
	parsed.Fragment = ""

	tenantID := strings.TrimSpace(os.Getenv("JYSEC_CONTROL_PLANE_TENANT_ID"))
	if tenantID == "" {
		tenantID = defaultSecurityOpsTenantID
	}
	return &SecurityOpsHandler{
		baseURL:  parsed,
		tenantID: tenantID,
		client:   &http.Client{Timeout: 35 * time.Second},
		logger:   logger,
	}
}

func (h *SecurityOpsHandler) SetAudit(service *audit.Service) { h.audit = service }

func (h *SecurityOpsHandler) Catalog(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/catalog", false)
}
func (h *SecurityOpsHandler) ListRuns(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/runs", false)
}
func (h *SecurityOpsHandler) CreateRun(c *gin.Context) {
	h.forward(c, http.MethodPost, "/v1/runs", true)
}
func (h *SecurityOpsHandler) GetRun(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/runs/"+url.PathEscape(c.Param("runId")), false)
}
func (h *SecurityOpsHandler) ListEvents(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/runs/"+url.PathEscape(c.Param("runId"))+"/events", false)
}
func (h *SecurityOpsHandler) ListArtifacts(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/runs/"+url.PathEscape(c.Param("runId"))+"/artifacts", false)
}
func (h *SecurityOpsHandler) ListFindings(c *gin.Context) {
	h.forward(c, http.MethodGet, "/v1/projects/"+url.PathEscape(c.Param("projectId"))+"/findings", false)
}
func (h *SecurityOpsHandler) ApproveRun(c *gin.Context) {
	h.forward(c, http.MethodPost, "/v1/runs/"+url.PathEscape(c.Param("runId"))+"/approve", false)
}
func (h *SecurityOpsHandler) CancelRun(c *gin.Context) {
	h.forward(c, http.MethodPost, "/v1/runs/"+url.PathEscape(c.Param("runId"))+"/cancel", false)
}

func (h *SecurityOpsHandler) forward(c *gin.Context, method, upstreamPath string, rewriteCreate bool) {
	session, ok := security.CurrentSession(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "authentication required"})
		return
	}

	var body io.Reader
	if method != http.MethodGet && method != http.MethodHead {
		data, err := io.ReadAll(io.LimitReader(c.Request.Body, securityOpsMaxRequestBytes+1))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to read request"})
			return
		}
		if len(data) > securityOpsMaxRequestBytes {
			c.JSON(http.StatusRequestEntityTooLarge, gin.H{"error": "request body is too large"})
			return
		}
		if rewriteCreate {
			data, err = h.bindCreateIdentity(data)
			if err != nil {
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
				return
			}
		}
		body = bytes.NewReader(data)
	}

	target := *h.baseURL
	target.Path = strings.TrimRight(h.baseURL.Path, "/") + upstreamPath
	target.RawQuery = c.Request.URL.RawQuery
	req, err := http.NewRequestWithContext(c.Request.Context(), method, target.String(), body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to build control-plane request"})
		return
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Jysec-Tenant", h.tenantID)
	req.Header.Set("X-Jysec-User", session.UserID)
	req.Header.Set("X-Jysec-Roles", h.controlPlaneRoles(c))

	resp, err := h.client.Do(req)
	if err != nil {
		if h.logger != nil {
			h.logger.Warn("security control plane unavailable", zap.Error(err))
		}
		h.record(c, method, upstreamPath, http.StatusBadGateway, "failure")
		c.JSON(http.StatusBadGateway, gin.H{"error": "security control plane unavailable"})
		return
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, securityOpsMaxResponseSize+1))
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "failed to read control-plane response"})
		return
	}
	if len(data) > securityOpsMaxResponseSize {
		c.JSON(http.StatusBadGateway, gin.H{"error": "control-plane response is too large"})
		return
	}
	result := "success"
	if resp.StatusCode >= http.StatusBadRequest {
		result = "failure"
	}
	h.record(c, method, upstreamPath, resp.StatusCode, result)
	contentType := resp.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "application/json; charset=utf-8"
	}
	c.Data(resp.StatusCode, contentType, data)
}

func (h *SecurityOpsHandler) bindCreateIdentity(data []byte) ([]byte, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(data, &payload); err != nil {
		return nil, fmt.Errorf("invalid JSON request")
	}
	authorization, ok := payload["authorization"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("authorization is required")
	}
	authorization["tenantId"] = h.tenantID
	return json.Marshal(payload)
}

func (h *SecurityOpsHandler) controlPlaneRoles(c *gin.Context) string {
	roles := []string{"security_operator"}
	if security.SessionHasPermission(c, "hitl:write") {
		roles = append(roles, "security_approver")
	}
	return strings.Join(roles, ",")
}

func (h *SecurityOpsHandler) record(c *gin.Context, method, path string, status int, result string) {
	if h.audit == nil || (method == http.MethodGet && status < http.StatusBadRequest) {
		return
	}
	h.audit.Record(c, audit.Entry{
		Category:     "security_ops",
		Action:       strings.ToLower(method),
		Result:       result,
		ResourceType: "security_run",
		ResourceID:   c.Param("runId"),
		Message:      "Web security operation forwarded to governed control plane",
		Detail:       map[string]interface{}{"path": path, "status": status},
	})
}
