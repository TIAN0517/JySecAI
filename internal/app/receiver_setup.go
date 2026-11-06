package app

import (
	"errors"
	"time"

	"go.uber.org/zap"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/receiver"
)

// setupExternalReceiver 建立外部 MySQL 接收端並掛上資料庫鉤子。
//
// 回傳 nil 代表沒有啟用 —— 那是正常狀態，不是錯誤。
func setupExternalReceiver(cfg *config.Config, db *database.DB, logger *zap.Logger) *receiverBridge {
	if cfg == nil || db == nil || logger == nil {
		return nil
	}
	mc := cfg.ExternalMySQL
	if !mc.Enabled {
		return nil
	}
	if !mc.EnabledEffective() {
		logger.Warn("外部 MySQL 接收端已開啟但設定不完整，已略過（host/user/database 必填）")
		return nil
	}

	// 本地寄件箱：收割成果的安全落地點。
	// 建不起來就不啟動接收端 —— 沒有寄件箱的接收端會「看起來在工作、
	// 其實在漏資料」，那比明確不啟動更糟。
	outbox, err := receiver.NewSQLiteOutbox(db.DB, logger)
	if err != nil {
		logger.Error("建立接收端本地寄件箱失敗，接收端未啟動（平台不受影響）", zap.Error(err))
		return nil
	}

	bridge := newReceiverBridge(outbox, mc, logger)
	bridge.Start()

	sinkCfg := receiver.MySQLConfig{
		Host:            mc.Host,
		Port:            mc.Port,
		User:            mc.User,
		Password:        mc.Password,
		Database:        mc.Database,
		TablePrefix:     mc.TablePrefix,
		Timeout:         time.Duration(mc.TimeoutSeconds) * time.Second,
		MaxOpenConns:    mc.MaxOpenConns,
		MaxIdleConns:    mc.MaxIdleConns,
		ConnMaxLifetime: time.Duration(mc.ConnMaxLifetimeSeconds) * time.Second,
	}

	sink, err := receiver.NewMySQLSink(sinkCfg, logger)
	if err != nil {
		// 連不上不是致命的：成果先落在本地寄件箱，MySQL 回來就會送出。
		// 錯誤訊息裡的主機位址要遮掉 —— 日誌是最常被外帶的載體。
		logger.Warn("外部 MySQL 接收端初次連線失敗，已進入背景重連（成果留在本地寄件箱）",
			zap.Error(errors.New(sinkCfg.MaskHost(err.Error()))))
		go bridge.reconnectLoop(sinkCfg)
	} else {
		bridge.SetSink(sink)
		// 這裡刻意不記主機位址與連接埠：要查設定檔就有，而日誌會被貼到
		// 聊天與工單裡，內網位址不該跟著到處跑。
		logger.Info("外部 MySQL 接收端已啟動",
			zap.String("database", mc.Database),
			zap.Int("batch_size", mc.BatchSize),
			zap.Int("poll_interval_seconds", mc.PollIntervalSeconds),
		)
	}

	db.AddVulnerabilityPersistedHook(bridge.OnVulnerabilityPersisted)
	db.AddProjectFactUpsertedHook(bridge.OnProjectFactUpserted)
	return bridge
}

// reconnectLoop 背景重連。
//
// MySQL 晚點才開機、網路抖動、帳號被鎖 —— 這些都不該讓接收端永久罷工。
// 成果本來就安全躺在寄件箱裡，重連只是「開始送」的時間點問題。
func (b *receiverBridge) reconnectLoop(cfg receiver.MySQLConfig) {
	delay := 10 * time.Second
	for {
		select {
		case <-b.ctx.Done():
			return
		case <-time.After(delay):
		}
		sink, err := receiver.NewMySQLSink(cfg, b.logger)
		if err != nil {
			b.logger.Warn("外部 MySQL 接收端重連失敗",
				zap.Error(errors.New(cfg.MaskHost(err.Error()))))
			if delay < 2*time.Minute {
				delay *= 2
			}
			continue
		}
		b.SetSink(sink)
		b.logger.Info("外部 MySQL 接收端已連線")
		return
	}
}
