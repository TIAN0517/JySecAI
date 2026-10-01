package handler

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"jysecai/internal/audit"
	"jysecai/internal/config"
	"net"
	"net/http"
	"strconv"
	"strings"

	"jysecai/internal/database"
	"jysecai/internal/security"
	"jysecai/internal/xsshook"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// XSSCollectorProvider 向 XSS 处理器暴露当前收集服务参数（token 不上行前端）。
type XSSCollectorProvider func() (publicURL, token string, enabled bool)

// XSSHandler 管理 XSS 窃密载荷与收割记录。
type XSSHandler struct {
	db       *database.DB
	logger   *zap.Logger
	provider XSSCollectorProvider
	cfg      config.XssConfig
	audit    *audit.Service
}

func NewXSSHandler(db *database.DB, logger *zap.Logger, provider XSSCollectorProvider) *XSSHandler {
	return &XSSHandler{db: db, logger: logger, provider: provider}
}

type XssHandler = XSSHandler

func NewXssHandler(db *database.DB, cfg *config.XssConfig, log *zap.Logger) *XSSHandler {
	if cfg == nil {
		cfg = &config.XssConfig{}
	}
	value := *cfg
	h := &XSSHandler{db: db, logger: log, cfg: value}
	h.provider = func() (string, string, bool) {
		base := strings.TrimRight(value.PublicURL, "/")
		if base == "" {
			base = "http://" + net.JoinHostPort(value.XssBindHostEffective(), fmt.Sprint(value.XssBindPortEffective()))
		}
		return base, value.Token, value.Enabled
	}
	return h
}
func (h *XSSHandler) SetAudit(a *audit.Service) { h.audit = a }
func xssAccess(c *gin.Context) database.RBACListAccess {
	if session, ok := security.CurrentSession(c); ok {
		permission := "xss:read"
		switch c.Request.Method {
		case http.MethodPost, http.MethodPut, http.MethodPatch:
			permission = "xss:write"
		case http.MethodDelete:
			permission = "xss:delete"
		}
		return database.RBACListAccess{UserID: session.UserID, Scope: session.ScopeFor(permission)}
	}
	return database.RBACListAccess{}
}
func RegisterXSSRoutes(group *gin.RouterGroup, h *XSSHandler) {
	group.Use(func(c *gin.Context) {
		c.Header("Cache-Control", "no-store")
		c.Header("X-Content-Type-Options", "nosniff")
		c.Next()
	})
	group.GET("/config", h.GetConfig)
	group.GET("/payloads", h.ListPayloads)
	group.POST("/payloads/generate", h.GeneratePayload)
	group.GET("/payloads/:id", h.GetPayload)
	group.DELETE("/payloads/:id", h.DeletePayload)
	group.GET("/captures", h.ListCaptures)
	group.GET("/captures/:id", h.GetCapture)
	group.PUT("/captures/:id/status", h.UpdateCaptureStatus)
	group.DELETE("/captures/:id", h.DeleteCapture)
}

func xssPagination(c *gin.Context, defaultLimit int) (offset, limit int) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "50"))
	if pageSize < 1 {
		pageSize = defaultLimit
	}
	if pageSize > 200 {
		pageSize = 200
	}
	return (page - 1) * pageSize, pageSize
}

// GetConfig 返回前端可见的 XSS 收集服务状态（不含 token）。
func (h *XSSHandler) GetConfig(c *gin.Context) {
	publicURL, _, enabled := h.collectorParams()
	c.JSON(http.StatusOK, gin.H{
		"enabled":    enabled,
		"public_url": publicURL,
		"bind_host":  h.cfg.XssBindHostEffective(), "bind_port": h.cfg.XssBindPortEffective(), "cooldown_seconds": h.cfg.CooldownSeconds,
	})
}

// GeneratePayload 生成一段窃密载荷并落库：脚本内置收割地址与共享密钥。
func (h *XSSHandler) GeneratePayload(c *gin.Context) {
	var req struct {
		Name           string `json:"name"`
		SourceURL      string `json:"source_url"`
		ConversationID string `json:"conversation_id"`
		ProjectID      string `json:"project_id"`
		Enabled        *bool  `json:"enabled"`
		Domain         string `json:"domain"`
		DomainOnly     bool   `json:"domain_only"`
	}
	c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, 32*1024)
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request JSON"})
		return
	}
	publicURL, _, enabled := h.collectorParams()
	if !enabled {
		c.JSON(http.StatusBadRequest, gin.H{"error": "XSS collector is disabled in deployment configuration"})
		return
	}

	if len(req.Name) > 1024 || len(req.SourceURL) > 8192 {
		c.JSON(413, gin.H{"error": "field too large"})
		return
	}
	access := xssAccess(c)
	if access.UserID == "" {
		c.JSON(403, gin.H{"error": "access denied"})
		return
	}
	conversationID := strings.TrimSpace(req.ConversationID)
	projectID := strings.TrimSpace(req.ProjectID)
	if conversationID != "" {
		if !h.db.UserCanAccessResource(access.UserID, access.Scope, "conversation", conversationID) {
			c.JSON(403, gin.H{"error": "conversation denied"})
			return
		}
		parent, err := h.db.GetConversationProjectID(conversationID)
		if err != nil {
			c.JSON(400, gin.H{"error": "invalid conversation"})
			return
		}
		if projectID != "" && projectID != parent {
			c.JSON(400, gin.H{"error": "project/conversation mismatch"})
			return
		}
		projectID = parent
	}
	if projectID != "" && conversationID == "" && !h.db.UserCanAccessResource(access.UserID, access.Scope, "project", projectID) {
		c.JSON(403, gin.H{"error": "project denied"})
		return
	}
	domain := ""
	if req.Domain != "" {
		var err error
		domain, err = xsshook.NormalizeDomain(req.Domain)
		if err != nil {
			c.JSON(400, gin.H{"error": "invalid domain"})
			return
		}
	}
	if req.DomainOnly && domain == "" {
		c.JSON(400, gin.H{"error": "domain required"})
		return
	}
	random := make([]byte, 32)
	if _, err := rand.Read(random); err != nil {
		c.JSON(500, gin.H{"error": "token generation failed"})
		return
	}
	token := hex.EncodeToString(random)

	id := uuid.New().String()
	createdBy := ""
	if session, ok := security.CurrentSession(c); ok {
		createdBy = session.UserID
	}
	p := &database.XSSPayload{
		ID:             id,
		ProjectID:      projectID,
		ConversationID: conversationID,
		Name:           strings.TrimSpace(req.Name),
		SourceURL:      strings.TrimSpace(req.SourceURL),
		Status:         "armed",
		CreatedBy:      createdBy,
		OwnerUserID:    createdBy, CallbackToken: token, Enabled: 1, Domain: domain,
	}
	if req.Enabled != nil && !*req.Enabled {
		p.Enabled = 0
	}
	if req.DomainOnly {
		p.DomainOnly = 1
	}
	p.Script = xsshook.Build(xsshook.BuildOptions{
		PayloadID: p.ID,
		BeaconURL: publicURL,
		Token:     token,
	})
	created, err := h.db.CreateXSSPayload(p)
	if err != nil {
		h.logger.Error("生成XSS载荷失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "生成XSS载荷失败"})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "xss", "payload_create", "Create XSS payload", "xss_payload", created.ID, nil)
	}

	c.JSON(http.StatusOK, gin.H{
		"payload":    created,
		"beacon_url": publicURL + "/api/xss/capture",
	})
}

func (h *XSSHandler) collectorParams() (publicURL, token string, enabled bool) {
	if h.provider == nil {
		return "", "", false
	}
	return h.provider()
}

// ListPayloads 列出窃密载荷。
func (h *XSSHandler) ListPayloads(c *gin.Context) {
	filter := database.XSSListFilter{
		ProjectID:      strings.TrimSpace(c.Query("project_id")),
		ConversationID: strings.TrimSpace(c.Query("conversation_id")),
		Status:         strings.TrimSpace(c.Query("status")),
	}
	offset, limit := xssPagination(c, 50)
	items, total, err := h.db.ListXSSPayloads(filter, xssAccess(c), offset, limit)
	if err != nil {
		h.logger.Error("查询XSS载荷失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询XSS载荷失败"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"payloads":    items,
		"total":       total,
		"page":        offset/limit + 1,
		"page_size":   limit,
		"total_pages": (total + limit - 1) / limit,
	})
}

// GetPayload 载荷详情（含完整脚本）。
func (h *XSSHandler) GetPayload(c *gin.Context) {
	p, err := h.db.GetXSSPayload(c.Param("id"))
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "载荷不存在"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询载荷失败"})
		return
	}
	if !h.db.UserCanAccessXSS(xssAccess(c), "xss_payloads", "xss_payload", p.ID) {
		c.JSON(http.StatusForbidden, gin.H{"error": "没有权限访问该载荷"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"payload": p})
}

// DeletePayload 删除一段载荷。
func (h *XSSHandler) DeletePayload(c *gin.Context) {
	if !h.db.UserCanAccessXSS(xssAccess(c), "xss_payloads", "xss_payload", c.Param("id")) {
		c.JSON(http.StatusForbidden, gin.H{"error": "没有权限访问该载荷"})
		return
	}
	if err := h.db.DeleteXSSPayload(c.Param("id")); err != nil {
		h.logger.Error("删除XSS载荷失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除XSS载荷失败"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// ListCaptures 列出收割记录。
func (h *XSSHandler) ListCaptures(c *gin.Context) {
	filter := database.XSSListFilter{
		ProjectID:      strings.TrimSpace(c.Query("project_id")),
		ConversationID: strings.TrimSpace(c.Query("conversation_id")),
		PayloadID:      strings.TrimSpace(c.Query("payload_id")),
		Status:         strings.TrimSpace(c.Query("status")),
	}
	offset, limit := xssPagination(c, 50)
	items, total, err := h.db.ListXSSCaptures(filter, xssAccess(c), offset, limit)
	if err != nil {
		h.logger.Error("查询XSS收割记录失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询XSS收割记录失败"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"captures":    items,
		"total":       total,
		"page":        offset/limit + 1,
		"page_size":   limit,
		"total_pages": (total + limit - 1) / limit,
	})
}

// GetCapture 收割详情。
func (h *XSSHandler) GetCapture(c *gin.Context) {
	if !h.db.UserCanAccessXSS(xssAccess(c), "xss_captures", "xss_capture", c.Param("id")) {
		c.JSON(http.StatusForbidden, gin.H{"error": "没有权限访问该收割记录"})
		return
	}
	capRow, err := h.db.GetXSSCapture(c.Param("id"))
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "收割记录不存在"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询收割记录失败"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"capture": capRow})
}

// UpdateCaptureStatus 更新收割记录处理状态（如标记为已接管）。
func (h *XSSHandler) UpdateCaptureStatus(c *gin.Context) {
	if !h.db.UserCanAccessXSS(xssAccess(c), "xss_captures", "xss_capture", c.Param("id")) {
		c.JSON(http.StatusForbidden, gin.H{"error": "没有权限访问该收割记录"})
		return
	}
	var req struct {
		Status string `json:"status" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request JSON"})
		return
	}
	if err := h.db.UpdateXSSCaptureStatus(c.Param("id"), req.Status); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// DeleteCapture 删除一条收割记录。
func (h *XSSHandler) DeleteCapture(c *gin.Context) {
	if !h.db.UserCanAccessXSS(xssAccess(c), "xss_captures", "xss_capture", c.Param("id")) {
		c.JSON(http.StatusForbidden, gin.H{"error": "没有权限访问该收割记录"})
		return
	}
	if err := h.db.DeleteXSSCapture(c.Param("id")); err != nil {
		h.logger.Error("删除XSS收割记录失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "删除XSS收割记录失败"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}
