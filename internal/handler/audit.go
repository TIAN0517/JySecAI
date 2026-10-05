package handler

import (
	"net/http"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// AuditHandler serves platform audit log APIs.
type AuditHandler struct {
	db     *database.DB
	audit  *audit.Service
	logger *zap.Logger
}

// NewAuditHandler creates an audit log handler.
func NewAuditHandler(db *database.DB, auditSvc *audit.Service, logger *zap.Logger) *AuditHandler {
	return &AuditHandler{db: db, audit: auditSvc, logger: logger}
}

// Meta GET /api/audit/meta
func (h *AuditHandler) Meta(c *gin.Context) {
	enabled := false
	retentionDays := 0
	if h.audit != nil {
		enabled = h.audit.Enabled()
		retentionDays = h.audit.RetentionDays()
	}
	c.JSON(http.StatusOK, gin.H{
		"enabled":           enabled,
		"retention_days":    retentionDays,
		"default_page_size": 20,
		"max_page_size":     100,
		"max_export":        5000,
	})
}

// Summary GET /api/audit/summary
func (h *AuditHandler) Summary(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "database unavailable"})
		return
	}
	base, ok := auditFilterForAccess(c, auditFilterFromQuery(c))
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未登录"})
		return
	}
	total, err := h.db.CountAuditLogs(base)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	failFilter := base
	failFilter.Result = "failure"
	failures, err := h.db.CountAuditLogs(failFilter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	since := time.Now().AddDate(0, 0, -7)
	recentFilter := base
	recentFilter.Since = &since
	recent7d, err := h.db.CountAuditLogs(recentFilter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"total":     total,
		"failures":  failures,
		"recent_7d": recent7d,
		"has_filters": c.Query("category") != "" || c.Query("action") != "" || c.Query("result") != "" ||
			c.Query("q") != "" || c.Query("since") != "" || c.Query("until") != "",
	})
}

// ListLogs GET /api/audit/logs
func (h *AuditHandler) ListLogs(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "database unavailable"})
		return
	}
	filter, ok := auditFilterForAccess(c, auditFilterFromQuery(c))
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未登录"})
		return
	}
	page, pageSize := auditPaginationFromQuery(c)
	filter.Limit = pageSize
	filter.Offset = (page - 1) * pageSize

	logs, err := h.db.ListAuditLogs(filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	total, err := h.db.CountAuditLogs(filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"logs":      logs,
		"total":     total,
		"page":      page,
		"page_size": pageSize,
	})
}

// GetLog GET /api/audit/logs/:id
func (h *AuditHandler) GetLog(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "database unavailable"})
		return
	}
	row, err := h.db.GetAuditLogByID(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "审计记录不存在"})
		return
	}
	if session, ok := security.CurrentSession(c); !ok || (session.Scope != database.RBACScopeAll && row.Actor != session.Username) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	audit.ApplyResourceAvailability(h.db, row)
	c.JSON(http.StatusOK, gin.H{"log": row})
}

// ExportLogs GET /api/audit/logs/export — JSON or CSV (?format=csv), max 5000 rows.
func (h *AuditHandler) ExportLogs(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "database unavailable"})
		return
	}
	filter, ok := auditFilterForAccess(c, auditFilterFromQuery(c))
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未登录"})
		return
	}
	filter.Limit = 5000
	filter.Offset = 0

	logs, err := h.db.ListAuditLogs(filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if c.Query("format") == "csv" {
		writeAuditLogsCSV(c, logs)
		return
	}
	c.Header("Content-Disposition", `attachment; filename="audit-logs.json"`)
	c.JSON(http.StatusOK, gin.H{
		"exported_at": time.Now().UTC().Format(time.RFC3339),
		"logs":        logs,
	})
}

// auditFilterForAccess 把审计日志收窄到调用者自己的记录。
//
// 解析不出 session 时返回 ok=false：原本的 `if session, ok := ...; ok && ...`
// 在 !ok 时让 filter.Actor 留空，而 buildAuditLogsWhere 只在 Actor 非空时才
// 附加条件，于是查询退化成 WHERE 1=1，返回全部租户的审计记录。
// 同文件的 GetLog 已经用 `!ok ||` 正确拒绝，这里是同样的语义。
func auditFilterForAccess(c *gin.Context, filter database.ListAuditLogsFilter) (database.ListAuditLogsFilter, bool) {
	session, ok := security.CurrentSession(c)
	if !ok {
		return filter, false
	}
	if session.Scope != database.RBACScopeAll {
		filter.Actor = session.Username
	}
	return filter, true
}
