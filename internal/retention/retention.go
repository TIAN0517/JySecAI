// Package retention 提供「保留天數 + 定期清理」的共用實作。
//
// HITL 審計日誌與 MCP 工具執行記錄的清理流程完全相同（算 cutoff → 呼叫專屬 purge → 記錄日誌），
// 只有保留天數來源、purge 函式與日誌文案不同，因此把流程收斂到這裡，
// 由 internal/hitl 與 internal/monitor 各自帶入參數。
package retention

import (
	"time"

	"go.uber.org/zap"
)

// purgeInterval 清理輪詢間隔。
const purgeInterval = time.Hour

// Options 描述一個清理服務的行為差異。
type Options struct {
	// RetentionDays 回傳保留天數；<= 0 代表永久保留，不清理。
	RetentionDays func() int
	// Purge 刪除 cutoff 之前的資料並回傳刪除筆數。
	Purge func(cutoff time.Time) (int64, error)
	// Label 用於日誌文案，例如「人機協同審計日誌」。
	Label string
	// TickMessage 每次輪詢完成的 debug 日誌文案。
	TickMessage string
	// Logger 日誌輸出；nil 時不輸出。
	Logger *zap.Logger
}

// Service 是共用的保留期清理服務。
type Service struct {
	opts Options
}

// New 建立清理服務。
func New(opts Options) *Service {
	return &Service{opts: opts}
}

// Days 回傳目前的保留天數；0 代表永久保留。
func (s *Service) Days() int {
	if s == nil || s.opts.RetentionDays == nil {
		return 0
	}
	return s.opts.RetentionDays()
}

// PurgeExpired 刪除超過保留期的資料。
func (s *Service) PurgeExpired() {
	if s == nil || s.opts.Purge == nil {
		return
	}
	days := s.Days()
	if days <= 0 {
		return
	}
	cutoff := time.Now().AddDate(0, 0, -days)
	n, err := s.opts.Purge(cutoff)
	if err != nil {
		if s.opts.Logger != nil {
			s.opts.Logger.Warn("清理过期"+s.opts.Label+"失败", zap.Error(err))
		}
		return
	}
	if n > 0 && s.opts.Logger != nil {
		s.opts.Logger.Info("已清理过期"+s.opts.Label, zap.Int64("deleted", n), zap.Int("retention_days", days))
	}
}

// StartLoop 定期執行清理。
func (s *Service) StartLoop(logger *zap.Logger) {
	if s == nil {
		return
	}
	go func() {
		ticker := time.NewTicker(purgeInterval)
		defer ticker.Stop()
		for range ticker.C {
			s.PurgeExpired()
			if logger != nil {
				logger.Debug(s.opts.TickMessage)
			}
		}
	}()
}
