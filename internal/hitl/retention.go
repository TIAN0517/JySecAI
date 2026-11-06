package hitl

import (
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/retention"

	"go.uber.org/zap"
)

// Service manages HITL audit log retention (decided hitl_interrupts rows).
//
// 實際的清理流程由 internal/retention 提供，這裡只帶入 HITL 專屬的
// 保留天數來源、purge 函式與日誌文案。
type Service struct {
	db     *database.DB
	cfg    *config.Config
	logger *zap.Logger

	retention *retention.Service
}

// NewService creates a HITL audit log retention service.
func NewService(db *database.DB, cfg *config.Config, logger *zap.Logger) *Service {
	s := &Service{db: db, cfg: cfg, logger: logger}
	s.retention = retention.New(retention.Options{
		RetentionDays: s.RetentionDays,
		Purge:          s.purgeBefore,
		Label:          "人机协同审计日志",
		TickMessage:    "hitl audit log retention tick completed",
		Logger:         logger,
	})
	return s
}

// RetentionDays returns configured retention; 0 means keep forever.
func (s *Service) RetentionDays() int {
	if s == nil || s.cfg == nil {
		return config.HitlConfig{}.RetentionDaysEffective()
	}
	return s.cfg.Hitl.RetentionDaysEffective()
}

// purgeBefore 刪除 cutoff 之前的已決策 HITL 審計記錄。
func (s *Service) purgeBefore(cutoff time.Time) (int64, error) {
	if s == nil || s.db == nil || s.cfg == nil {
		return 0, nil
	}
	return s.db.PurgeHitlInterruptLogsBefore(cutoff)
}

// PurgeExpired deletes decided HITL log rows older than retention_days when configured.
func (s *Service) PurgeExpired() {
	if s == nil || s.retention == nil {
		return
	}
	s.retention.PurgeExpired()
}

// StartRetentionLoop periodically purges expired HITL audit log rows.
func StartRetentionLoop(s *Service, logger *zap.Logger) {
	if s == nil || s.retention == nil {
		return
	}
	s.retention.StartLoop(logger)
}
