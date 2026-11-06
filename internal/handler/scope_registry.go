package handler

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/scope"
	"jysecai/internal/scopeaudit"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// ScopeRegistryHandler 暴露授權狀態機（scope registry）的查詢、覆蓋率稽核與核准。
//
// 為什麼需要這個 handler
// ----------------------
// scope_grants 這張表原本只有兩條寫入路徑：scopeimport CLI 與 scope_extension
// 的人工中斷裁決。沒有任何一支 API 可以「看見」registry 的狀態，也沒有任何
// 一條路徑可以把「已起草、待裁決」的授權券轉為生效——所以自動起草出來的券
// 只會永遠躺在資料庫裡。
//
// 這個 handler 補上那條路徑，並且把「按一次」的互動放在兩個地方：
//   - API：POST /api/scope/grants/:id/activate（管理員 RBAC 保護）
//   - Telegram inline 按鈕：人按一次就完成同樣的事
//
// 兩條路徑共用同一個 service 函式，所以行為完全一致。
type ScopeRegistryHandler struct {
	db     *database.DB
	logger *zap.Logger
}

// NewScopeRegistryHandler 建立 scope registry handler。
func NewScopeRegistryHandler(db *database.DB, logger *zap.Logger) *ScopeRegistryHandler {
	return &ScopeRegistryHandler{db: db, logger: logger}
}

// callback 前綴：按鈕資料的格式是 scope_grant:<動作>:<grant id>。
const (
	scopeCallbackPrefix    = "scope_grant"
	scopeCallbackActivate  = "activate"
	scopeCallbackReject    = "reject"
	scopeCallbackSeparator = ":"
)

// ListGrants 列出授權券（含待裁決／已用盡／已過期，供稽核與 UI 顯示）。
//
// GET /api/scope/grants
func (h *ScopeRegistryHandler) ListGrants(c *gin.Context) {
	if h == nil || h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "scope registry 服務不可用"})
		return
	}
	grants, err := database.ListScopeGrants(c.Request.Context(), h.db)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "讀取授權券失敗", "detail": err.Error()})
		return
	}
	counts := map[string]int{}
	for _, grant := range grants {
		counts[strings.ToLower(strings.TrimSpace(grant.Status))]++
	}
	c.JSON(http.StatusOK, gin.H{
		"grants": grants,
		"total":  len(grants),
		"counts": counts,
	})
}

// ListTargets 列出常駐授權集。
//
// GET /api/scope/targets
func (h *ScopeRegistryHandler) ListTargets(c *gin.Context) {
	if h == nil || h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "scope registry 服務不可用"})
		return
	}
	targets, err := database.ListScopeTargets(c.Request.Context(), h.db)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "讀取常駐授權失敗", "detail": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"targets": targets, "total": len(targets)})
}

// Audit 產出授權覆蓋率報告。
//
// GET /api/scope/audit?status=confirmed&severity=critical,high&action_class=db_read_extract
//
// 這是唯讀的：只算不寫，所以可以隨時對線上資料跑。
func (h *ScopeRegistryHandler) Audit(c *gin.Context) {
	if h == nil || h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "scope registry 服務不可用"})
		return
	}
	opts := scopeaudit.DefaultOptions()
	if raw := strings.TrimSpace(c.Query("status")); raw != "" {
		opts.Statuses = splitCSV(raw)
	}
	if raw := strings.TrimSpace(c.Query("severity")); raw != "" {
		opts.Severities = splitCSV(raw)
	}
	actionClass := strings.TrimSpace(c.Query("action_class"))
	if actionClass == "" {
		actionClass = scope.ActionDBReadExtract
	}

	targets, err := scopeaudit.CollectTargets(c.Request.Context(), h.db, opts)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "收集漏洞目標失敗", "detail": err.Error()})
		return
	}
	report, err := scopeaudit.BuildReport(c.Request.Context(), h.db, targets, actionClass)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "產生覆蓋率報告失敗", "detail": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"action_class": actionClass,
		"statuses":     opts.Statuses,
		"severities":   opts.Severities,
		"report":       report,
	})
}

// ActivateGrant 啟用一張待裁決的授權券。
//
// POST /api/scope/grants/:id/activate
//
// 只認 pending → active 的單向轉換（見 database.ActivateScopeGrant）：
// 已生效的券再按一次不會重置使用次數，所以這個端點可以安全重放。
func (h *ScopeRegistryHandler) ActivateGrant(c *gin.Context) {
	if h == nil || h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "scope registry 服務不可用"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	activated, err := h.activateGrant(c.Request.Context(), id, "api:"+c.GetString(security.ContextUsernameKey))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "啟用授權券失敗", "detail": err.Error()})
		return
	}
	if !activated {
		c.JSON(http.StatusConflict, gin.H{
			"error": "授權券無法啟用（不存在、不是待裁決狀態、已過期或已用盡）",
			"id":    id,
		})
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": id, "status": database.ScopeGrantStatusActive})
}

// RevokeGrant 撤銷一張授權券，並記住這個目標已被拒絕。
//
// POST /api/scope/grants/:id/reject
func (h *ScopeRegistryHandler) RevokeGrant(c *gin.Context) {
	if h == nil || h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "scope registry 服務不可用"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if err := h.rejectGrant(c.Request.Context(), id, "api:"+c.GetString(security.ContextUsernameKey)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "撤銷授權券失敗", "detail": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": id, "status": database.ScopeGrantStatusRevoked})
}

// activateGrant 是「待裁決 → 生效」的唯一實作，API 與 Telegram 按鈕共用。
func (h *ScopeRegistryHandler) activateGrant(ctx context.Context, id, activatedBy string) (bool, error) {
	if h == nil || h.db == nil {
		return false, errors.New("scope registry 服務不可用")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return false, errors.New("授權券 ID 為空")
	}
	activated, err := database.ActivateScopeGrant(ctx, h.db, id, activatedBy)
	if err != nil {
		return false, err
	}
	if !activated {
		return false, nil
	}
	if h.logger != nil {
		h.logger.Info("scope 授權券已啟用", zap.String("grant_id", id), zap.String("activated_by", activatedBy))
	}
	return true, nil
}

// rejectGrant 撤銷一張待裁決的券並記下拒絕記憶。
//
// 記拒絕記憶是重點：撤銷只擋掉這一張券，下次 agent 再碰同一個目標還是會
// 重新被問。寫進 scope_denials 才會「不再打擾操作者」。
func (h *ScopeRegistryHandler) rejectGrant(ctx context.Context, id, rejectedBy string) error {
	if h == nil || h.db == nil {
		return errors.New("scope registry 服務不可用")
	}
	id = strings.TrimSpace(id)
	if id == "" {
		return errors.New("授權券 ID 為空")
	}
	grant, err := database.GetScopeGrant(ctx, h.db, id)
	if err != nil {
		return err
	}
	if _, err := database.RevokeScopeGrant(ctx, h.db, id, rejectedBy); err != nil {
		return err
	}
	key := scope.NormalizeTarget(grant.TargetValue).Key()
	if key == "" {
		return nil
	}
	return database.RecordScopeDenial(ctx, h.db, database.ScopeDenial{
		Target:    key,
		Owner:     rejectedBy,
		Reason:    "rejected_by_operator",
		DecidedBy: rejectedBy,
		DecidedAt: time.Now(),
	})
}

// HandleCallback 處理機器人 inline 按鈕點擊（實作 robot.CallbackHandler）。
//
// 按鈕資料格式：scope_grant:activate:<grant id> / scope_grant:reject:<grant id>
//
// 回傳的字串會顯示在按鈕上方的提示框，必須短且講清楚發生了什麼。
func (h *ScopeRegistryHandler) HandleCallback(platform, userID, callbackData string) string {
	if h == nil || h.db == nil {
		return "授權服務不可用"
	}
	parts := strings.Split(strings.TrimSpace(callbackData), scopeCallbackSeparator)
	if len(parts) != 3 || parts[0] != scopeCallbackPrefix {
		return "按鈕資料格式不正確"
	}
	action := strings.ToLower(strings.TrimSpace(parts[1]))
	grantID := strings.TrimSpace(parts[2])
	if grantID == "" {
		return "按鈕資料缺少授權券 ID"
	}
	actor := platform + ":" + userID

	// 核准授權券是「改變安全邊界」的動作。
	//
	// 這道檢查不能省：任何能對機器人說話的人都能看到這則訊息、都能按這個按鈕。
	// 沒有權限檢查的話，等於把核准權交給每一個看到通知的人——
	// 那不是「人按一次就生效」，那是「任何人都能按」。
	// 所以按下按鈕的人必須是平台上擁有 scope:write 的帳號。
	if err := h.requireScopeWrite(platform, userID); err != nil {
		return "無法核准：" + err.Error()
	}

	switch action {
	case scopeCallbackActivate:
		activated, err := h.activateGrant(context.Background(), grantID, actor)
		if err != nil {
			return "啟用失敗：" + err.Error()
		}
		if !activated {
			return "此授權券無法啟用（已處理、已過期或已用盡）"
		}
		return "已核准：" + grantID
	case scopeCallbackReject:
		if err := h.rejectGrant(context.Background(), grantID, actor); err != nil {
			return "撤銷失敗：" + err.Error()
		}
		return "已拒絕並記住此目標：" + grantID
	default:
		return fmt.Sprintf("不支援的動作：%s", action)
	}
}

// requireScopeWrite 確認這個人有核准授權券的權限。
//
// 走的是機器人身分綁定（robot_user_bindings）→ 平台角色 → 權限這條既有的路徑，
// 與機器人在平台上的其他操作（例如漏洞推播收件人）用的是同一套身分解析。
func (h *ScopeRegistryHandler) requireScopeWrite(platform, userID string) error {
	if h == nil || h.db == nil {
		return errors.New("scope registry 服務不可用")
	}
	access, err := h.db.ResolveRobotRBACAccess(platform, userID)
	if err != nil {
		return fmt.Errorf("身分未綁定平台帳號（%v）", err)
	}
	if !access.Permissions["scope:write"] {
		return errors.New("你的平台帳號沒有 scope:write 權限")
	}
	return nil
}

// splitCSV 解析逗號分隔的查詢參數。
func splitCSV(raw string) []string {
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		trimmed := strings.ToLower(strings.TrimSpace(part))
		if trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}
