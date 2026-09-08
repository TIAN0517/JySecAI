package handler

import (
	"database/sql"
	"errors"
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
}

func NewXSSHandler(db *database.DB, logger *zap.Logger, provider XSSCollectorProvider) *XSSHandler {
	return &XSSHandler{db: db, logger: logger, provider: provider}
}

func xssAccess(c *gin.Context) database.RBACListAccess {
	if session, ok := security.CurrentSession(c); ok {
		return database.RBACListAccess{UserID: session.UserID, Scope: session.ScopeFor("xss:read")}
	}
	return database.RBACListAccess{}
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
	publicURL, _ , enabled := h.collectorParams()
	c.JSON(http.StatusOK, gin.H{
		"enabled":    enabled,
		"public_url": publicURL,
	})
}

// GeneratePayload 生成一段窃密载荷并落库：脚本内置收割地址与共享密钥。
func (h *XSSHandler) GeneratePayload(c *gin.Context) {
	var req struct {
		Name           string `json:"name"`
		SourceURL      string `json:"source_url"`
		ConversationID string `json:"conversation_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}
	publicURL, token, enabled := h.collectorParams()
	if !enabled || strings.TrimSpace(token) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "XSS 收集服务未启用或未配置密钥（先启用 config.yaml 的 xss 段并重启，或填写 token）"})
		return
	}

	conversationID := strings.TrimSpace(req.ConversationID)
	projectID := ""
	if conversationID != "" {
		if pid, err := h.db.GetConversationProjectID(conversationID); err == nil {
			projectID = pid
		}
	}

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
	if createdBy != "" {
		_ = h.db.AssignResourceToUser(createdBy, "xss_payload", created.ID)
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
		"payloads": items,
		"total":    total,
		"page":     offset/limit + 1,
		"page_size": limit,
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
		"captures":  items,
		"total":     total,
		"page":      offset/limit + 1,
		"page_size": limit,
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
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
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