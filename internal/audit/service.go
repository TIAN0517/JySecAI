package audit

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// Service persists platform audit logs.
type Service struct {
	db           *database.DB
	cfg          *config.Config
	logger       *zap.Logger
	failThrottle *failureThrottle
}

// NewService creates an audit service.
func NewService(db *database.DB, cfg *config.Config, logger *zap.Logger) *Service {
	return &Service{
		db:           db,
		cfg:          cfg,
		logger:       logger,
		failThrottle: newFailureThrottle(),
	}
}

// Enabled reports whether audit persistence is on.
func (s *Service) Enabled() bool {
	if s == nil || s.cfg == nil {
		return false
	}
	return s.cfg.Audit.EnabledEffective()
}

// Record writes one audit row from a Gin request context.
func (s *Service) Record(c *gin.Context, e Entry) {
	if s == nil || !s.Enabled() || s.db == nil {
		return
	}
	if strings.TrimSpace(e.Category) == "" || strings.TrimSpace(e.Action) == "" {
		return
	}
	if e.Result == "failure" && !s.allowFailureAudit(c, e) {
		return
	}
	if strings.TrimSpace(e.Result) == "" {
		e.Result = "success"
	}
	if strings.TrimSpace(e.Level) == "" {
		if e.Result == "failure" {
			e.Level = "warn"
		} else {
			e.Level = "info"
		}
	}
	if strings.TrimSpace(e.Actor) == "" {
		if c != nil {
			e.Actor = strings.TrimSpace(c.GetString(security.ContextUsernameKey))
		}
		if e.Actor == "" {
			e.Actor = "admin"
		}
	}
	maxDetail := s.cfg.Audit.MaxDetailBytesEffective()
	detail := SanitizeDetail(e.Detail, maxDetail)

	sessionHintVal := e.SessionHint
	if sessionHintVal == "" && c != nil {
		if token := c.GetString(security.ContextAuthTokenKey); token != "" {
			sessionHintVal = sessionHint(token)
		}
	}
	clientIPVal := e.ClientIP
	if clientIPVal == "" {
		clientIPVal = s.clientIP(c)
	}

	row := &database.AuditLog{
		ID:           "audit_" + strings.ReplaceAll(uuid.New().String(), "-", ""),
		CreatedAt:    time.Now(),
		Level:        e.Level,
		Category:     e.Category,
		Action:       e.Action,
		Result:       e.Result,
		Actor:        e.Actor,
		SessionHint:  sessionHintVal,
		ClientIP:     clientIPVal,
		UserAgent:    userAgent(c),
		ResourceType: e.ResourceType,
		ResourceID:   e.ResourceID,
		Message:      e.Message,
		Detail:       detail,
	}
	if err := s.db.AppendAuditLog(row); err != nil && s.logger != nil {
		s.logger.Warn("写入审计日志失败",
			zap.String("action", e.Action),
			zap.Error(err),
		)
	}
}

// RecordSystem writes an audit row without HTTP context (e.g. retention cleanup).
func (s *Service) RecordSystem(e Entry) {
	s.Record(nil, e)
}

// PurgeExpired deletes rows older than retention_days when configured.
func (s *Service) PurgeExpired() {
	if s == nil || s.db == nil || s.cfg == nil {
		return
	}
	days := s.cfg.Audit.RetentionDaysEffective()
	if days <= 0 {
		return
	}
	cutoff := time.Now().AddDate(0, 0, -days)
	n, err := s.db.DeleteAuditLogsBefore(cutoff)
	if err != nil {
		if s.logger != nil {
			s.logger.Warn("清理过期审计日志失败", zap.Error(err))
		}
		return
	}
	if n > 0 && s.logger != nil {
		s.logger.Info("已清理过期审计日志", zap.Int64("deleted", n))
	}
}

// HintFromToken returns a short stable hash prefix for a session token.
func HintFromToken(token string) string {
	return sessionHint(token)
}

func sessionHint(token string) string {
	token = strings.TrimSpace(token)
	if token == "" {
		return ""
	}
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:4])
}

func (s *Service) allowFailureAudit(c *gin.Context, e Entry) bool {
	if !isAuthFailureThrottled(e.Category, e.Action) {
		return true
	}
	cooldown := time.Duration(s.cfg.Audit.AuthFailureCooldownEffective()) * time.Second
	key := authFailureThrottleKey(e.Category, e.Action, s.clientIP(c))
	return s.failThrottle.allow(key, cooldown)
}

// clientIP 回傳這筆稽核紀錄應記錄的客戶端 IP。
//
// 採用平台的安全層解析（見 security.EffectiveClientIP）：當設定開啟
// trust_cf_connecting_ip 時，這條路徑進來的請求會記到真實客戶端 IP，而不是
// 一律 127.0.0.1——否則外部所有使用者的稽核會混在同一個 IP 欄位裡，
// 既看不出是誰，也讓「同一 IP 的失敗冷卻」變成全站共用一個桶。
func (s *Service) clientIP(c *gin.Context) string {
	if c == nil {
		return ""
	}
	if s == nil || s.cfg == nil {
		return security.EffectiveClientIP(c, false)
	}
	return security.EffectiveClientIP(c, s.cfg.Server.TrustCFConnectingIP)
}

func userAgent(c *gin.Context) string {
	if c == nil {
		return ""
	}
	ua := c.GetHeader("User-Agent")
	if len(ua) > 512 {
		return ua[:512]
	}
	return ua
}
