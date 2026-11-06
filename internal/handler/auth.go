package handler

import (
	"net/http"
	"strings"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// setAuthCookie 寫入驗證 cookie。
//
// 安全設定：HttpOnly（前端讀不到，避免 XSS 竊取）、SameSite=Lax（防 CSRF 跨站帶 cookie）、
// Secure 只在確定是 https 時才開（區網內的 http 部署會讓 cookie 被瀏覽器丟棄）。
func setAuthCookie(c *gin.Context, token string, expiresAt time.Time) {
	secure := c.Request.TLS != nil || strings.EqualFold(c.GetHeader("X-Forwarded-Proto"), "https")
	maxAge := int(time.Until(expiresAt).Seconds())
	if maxAge <= 0 {
		maxAge = 1
	}
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", token, maxAge, "/", "", secure, true)
}

// AuthHandler handles authentication-related endpoints.
type AuthHandler struct {
	manager    *security.AuthManager
	config     *config.Config
	configPath string
	logger     *zap.Logger
	audit      *audit.Service
}

// SetAudit wires platform audit logging.
func (h *AuthHandler) SetAudit(s *audit.Service) {
	h.audit = s
}

// NewAuthHandler creates a new AuthHandler.
func NewAuthHandler(manager *security.AuthManager, cfg *config.Config, configPath string, logger *zap.Logger) *AuthHandler {
	return &AuthHandler{
		manager:    manager,
		config:     cfg,
		configPath: configPath,
		logger:     logger,
	}
}

type loginRequest struct {
	Username string `json:"username"`
	Password string `json:"password" binding:"required"`
}

type changePasswordRequest struct {
	OldPassword string `json:"oldPassword"`
	NewPassword string `json:"newPassword"`
}

// Login verifies password and returns a session token.
func (h *AuthHandler) Login(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "密码不能为空"})
		return
	}

	token, expiresAt, err := h.manager.Authenticate(req.Username, req.Password)
	if err != nil {
		if h.audit != nil {
			h.audit.Record(c, audit.Entry{
				Level:    "warn",
				Category: "auth",
				Action:   "login",
				Result:   "failure",
				Message:  "登录失败：密码错误",
				Actor:    strings.TrimSpace(req.Username),
			})
		}
		c.JSON(http.StatusUnauthorized, gin.H{"error": "密码错误"})
		return
	}
	session, _ := h.manager.ValidateToken(token)

	if h.audit != nil {
		h.audit.Record(c, audit.Entry{
			Category:    "auth",
			Action:      "login",
			Result:      "success",
			SessionHint: audit.HintFromToken(token),
			Message:     "登录成功",
			Actor:       session.Username,
			Detail: map[string]interface{}{
				"expires_at": expiresAt.UTC().Format(time.RFC3339),
			},
		})
	}

	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	// 直接用連結開啟的下載（<a download>、貼到瀏覽器網址列）不會帶
	// Authorization 標頭，而 token 只存在 localStorage —— 這條路徑會拿到 401，
	// 使用者看到的就是「下載失敗」。補一個 HttpOnly cookie，讓非 fetch 的
	// 取用路徑也能通過驗證；Bearer 標頭仍然優先。
	setAuthCookie(c, token, expiresAt)

	c.JSON(http.StatusOK, gin.H{
		"token":               token,
		"expires_at":          expiresAt.UTC().Format(time.RFC3339),
		"session_duration_hr": h.manager.SessionDurationHours(),
		"user": gin.H{
			"id":           session.UserID,
			"username":     session.Username,
			"display_name": session.DisplayName,
		},
		"roles":             session.Roles,
		"permissions":       permissionKeys(session.Permissions),
		"permission_scopes": session.PermissionScopes,
		"scope":             session.Scope,
	})
}

// Logout revokes the current session token.
func (h *AuthHandler) Logout(c *gin.Context) {
	token := c.GetString(security.ContextAuthTokenKey)
	if token == "" {
		authHeader := c.GetHeader("Authorization")
		if len(authHeader) > 7 && strings.EqualFold(authHeader[:7], "Bearer ") {
			token = strings.TrimSpace(authHeader[7:])
		} else {
			token = strings.TrimSpace(authHeader)
		}
	}

	h.manager.RevokeToken(token)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	// 同一組憑證也要讓 cookie 失效，否則已登入的瀏覽器仍能用 cookie 存取。
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie("auth_token", "", -1, "/", "", false, true)
	if h.audit != nil {
		h.audit.Record(c, audit.Entry{
			Category: "auth",
			Action:   "logout",
			Result:   "success",
			Message:  "退出登录",
		})
	}
	c.JSON(http.StatusOK, gin.H{"message": "已退出登录"})
}

// ChangePassword updates the login password.
func (h *AuthHandler) ChangePassword(c *gin.Context) {
	var req changePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "参数无效"})
		return
	}

	oldPassword := strings.TrimSpace(req.OldPassword)
	newPassword := strings.TrimSpace(req.NewPassword)

	if oldPassword == "" || newPassword == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "当前密码和新密码均不能为空"})
		return
	}

	if len(newPassword) < 8 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "新密码长度至少需要 8 位"})
		return
	}

	if oldPassword == newPassword {
		c.JSON(http.StatusBadRequest, gin.H{"error": "新密码不能与旧密码相同"})
		return
	}

	// 解析不出 session 就拒絕，不要退化成 admin：原本的
	// `session.Username == "" → "admin"` 讓這條路徑在沒有 session 時
	// 變成「攻擊者指定要改哪個帳號的密碼」。AuthMiddleware 目前擋住了
	// 無 session 的請求，所以這是預設值本身的問題：安全預設應該是
	// 拒絕，而不是猜。
	session, ok := security.CurrentSession(c)
	if !ok || session.Username == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未授权访问，请先登录"})
		return
	}
	if !h.manager.CheckUserPassword(session.Username, oldPassword) {
		if h.audit != nil {
			h.audit.Record(c, audit.Entry{
				Level:    "warn",
				Category: "auth",
				Action:   "change_password",
				Result:   "failure",
				Message:  "修改密码失败：当前密码不正确",
			})
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "当前密码不正确"})
		return
	}

	if session.UserID == "" {
		// 与上面同理：没有 user id 就没有身份，猜一个等于授权给猜测。
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未授权访问，请先登录"})
		return
	}
	if err := h.manager.UpdateUserPassword(session.UserID, newPassword); err != nil {
		if h.logger != nil {
			h.logger.Error("更新用户密码失败", zap.Error(err))
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "更新用户密码失败"})
		return
	}

	if h.logger != nil {
		h.logger.Info("登录密码已更新，所有会话已失效")
	}

	if h.audit != nil {
		h.audit.Record(c, audit.Entry{
			Category: "auth",
			Action:   "change_password",
			Result:   "success",
			Message:  "登录密码已修改",
		})
	}

	c.JSON(http.StatusOK, gin.H{"message": "密码已更新，请使用新密码重新登录"})
}

// Validate returns the current session status.
func (h *AuthHandler) Validate(c *gin.Context) {
	token := c.GetString(security.ContextAuthTokenKey)
	if token == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "会话无效"})
		return
	}

	session, ok := h.manager.ValidateToken(token)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "会话已过期"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token":      session.Token,
		"expires_at": session.ExpiresAt.UTC().Format(time.RFC3339),
		"user": gin.H{
			"id":           session.UserID,
			"username":     session.Username,
			"display_name": session.DisplayName,
		},
		"roles":             session.Roles,
		"permissions":       permissionKeys(session.Permissions),
		"permission_scopes": session.PermissionScopes,
		"scope":             session.Scope,
	})
}

func permissionKeys(perms map[string]bool) []string {
	keys := make([]string, 0, len(perms))
	for key, ok := range perms {
		if ok {
			keys = append(keys, key)
		}
	}
	return keys
}
