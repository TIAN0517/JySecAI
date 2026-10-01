package app

import (
	"go.uber.org/zap"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/xsshook"
)

// App owns the collector lifecycle separately from management API handlers.
func startXSSCollector(db *database.DB, cfg config.XssConfig, log *zap.Logger) (*xsshook.Collector, error) {
	collector := xsshook.NewCollector(db, cfg, log)
	if err := collector.Start(); err != nil {
		return nil, err
	}
	return collector, nil
}
