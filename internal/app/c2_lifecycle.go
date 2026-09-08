package app

import (
	"context"
	"errors"
	"strings"
	"time"

	"jysecai/internal/c2"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/handler"

	"go.uber.org/zap"
)

// setupC2Runtime 创建 C2 Manager、看门狗与取消函数；不注册 MCP 工具（由 Apply 统一 ClearTools 后注册）。
func setupC2Runtime(
	cfg *config.Config,
	db *database.DB,
	agentHandler *handler.AgentHandler,
	logger *zap.Logger,
) (*c2.Manager, *c2.SessionWatchdog, context.CancelFunc) {
	if !cfg.C2.EnabledEffective() {
		return nil, nil, nil
	}
	c2Manager := c2.NewManager(db, logger, "tmp/c2")
	c2Manager.Registry().Register(string(c2.ListenerTypeTCPReverse), c2.NewTCPReverseListener)
	c2Manager.Registry().Register(string(c2.ListenerTypeHTTPBeacon), c2.NewHTTPBeaconListener)
	c2Manager.Registry().Register(string(c2.ListenerTypeHTTPSBeacon), c2.NewHTTPSBeaconListener)
	c2Manager.Registry().Register(string(c2.ListenerTypeWebSocket), c2.NewWebSocketListener)
	c2HITLBridge := NewC2HITLBridge(db, logger)
	c2Manager.SetHITLBridge(c2HITLBridge)
	c2Manager.SetHITLDangerousGate(func(conversationID, toolName string) bool {
		return agentHandler.HITLNeedsToolApproval(conversationID, toolName)
	})
	c2Hooks := SetupC2Hooks(&C2HooksConfig{
		DB:     db,
		Logger: logger,
		AttackChainRecord: func(session *database.C2Session, phase string, description string) {
			logger.Info("C2 Attack Chain",
				zap.String("session_id", session.ID),
				zap.String("phase", phase),
				zap.String("desc", description),
			)
		},
		VulnRecord: func(session *database.C2Session, title string, severity string) {
			logger.Info("C2 Vulnerability",
				zap.String("session_id", session.ID),
				zap.String("title", title),
				zap.String("severity", severity),
			)
		},
	})
	c2Manager.SetHooks(c2Hooks)
	c2Manager.RestoreRunningListeners()
	// 高端自动上线：按配置幂等创建/启动默认监听器，让植入体在首启即可自动登记上线。
	if err := reconcileAutoCheckinListeners(c2Manager, cfg.C2.AutoCheckin, logger); err != nil {
		logger.Warn("自动上线监听器协调失败", zap.Error(err))
	}
	minGrace := 30 * time.Second
	if cfg.C2.AutoCheckin != nil && cfg.C2.AutoCheckin.StaleSessionTimeoutSecondsEffective() > 0 {
		minGrace = time.Duration(cfg.C2.AutoCheckin.StaleSessionTimeoutSecondsEffective()) * time.Second
	}
	c2Watchdog := c2.NewSessionWatchdogWithOptions(c2Manager, c2.WithStaleTimeout(minGrace))
	watchdogCtx, watchdogCancel := context.WithCancel(context.Background())
	go c2Watchdog.Run(watchdogCtx)
	return c2Manager, c2Watchdog, watchdogCancel
}

// reconcileAutoCheckinListeners 按 auto_checkin 配置幂等创建并（可选）启动默认监听器。
//
// 幂等性：按 (name, project_id="") 匹配，已存在则跳过创建，仅确保按需启动；因此应用重启
// 或配置热更新都不会产生重复监听器。
func reconcileAutoCheckinListeners(mgr *c2.Manager, ac *config.C2AutoCheckinConfig, logger *zap.Logger) error {
	if mgr == nil || ac == nil {
		return nil
	}
	if !ac.EnabledEffective() {
		logger.Debug("自动上线已关闭，跳过默认监听器协调")
		return nil
	}
	autoStart := ac.AutoStartListenersEffective()
	sleep := ac.DefaultSleepSecondsEffective()
	jitter := ac.DefaultJitterPercentEffective()

	existing, err := mgr.DB().ListC2Listeners()
	if err != nil {
		return err
	}
	byName := make(map[string]*database.C2Listener, len(existing))
	for _, l := range existing {
		if strings.TrimSpace(l.ProjectID) == "" {
			byName[strings.TrimSpace(l.Name)] = l
		}
	}

	registered := 0
	for _, spec := range ac.EnabledAutoListeners() {
		name := strings.TrimSpace(spec.Name)
		if name == "" {
			logger.Warn("忽略无名称的自动上线监听器", zap.Reflect("spec", spec))
			continue
		}
		typ := strings.ToLower(strings.TrimSpace(spec.Type))
		if typ == "" {
			typ = string(c2.ListenerTypeHTTPBeacon)
		}
		bindHost := strings.TrimSpace(spec.BindHost)
		if bindHost == "" {
			bindHost = "0.0.0.0"
		}
		if err := c2.SafeBindPort(spec.BindPort); err != nil {
			logger.Warn("自动上线监听器端口非法，跳过",
				zap.String("name", name),
				zap.Int("bind_port", spec.BindPort),
				zap.Error(err),
			)
			continue
		}

		listener := byName[name]
		if listener == nil {
			created, err := mgr.CreateListener(c2.CreateListenerInput{
				Name:         name,
				Type:         typ,
				BindHost:     bindHost,
				BindPort:     spec.BindPort,
				CallbackHost: strings.TrimSpace(spec.CallbackHost),
				Remark:       "auto_checkin 自动上线",
				Config: &c2.ListenerConfig{
					DefaultSleep:  sleep,
					DefaultJitter: jitter,
				},
			})
			if err != nil {
				logger.Warn("自动上线监听器创建失败",
					zap.String("name", name),
					zap.Error(err),
				)
				continue
			}
			listener = created
			logger.Info("自动上线监听器已创建",
				zap.String("name", name),
				zap.String("type", typ),
				zap.Int("bind_port", spec.BindPort),
			)
		}

		if autoStart {
			if _, err := mgr.StartListener(listener.ID); err != nil && !errors.Is(err, c2.ErrListenerRunning) {
				logger.Warn("自动上线监听器启动失败",
					zap.String("name", name),
					zap.Error(err),
				)
				continue
			}
			logger.Info("自动上线监听器已启动",
				zap.String("name", name),
				zap.String("type", typ),
				zap.Int("bind_port", spec.BindPort),
			)
		}
		registered++
	}
	if registered > 0 {
		logger.Info("C2 自动上线就绪",
			zap.Int("listener_count", registered),
			zap.Bool("auto_start", autoStart),
		)
	}
	return nil
}

// ReconcileC2AfterConfigApply 根据当前内存配置启停 C2（不写盘；在 Apply 中 ClearTools 之前调用）。
func (a *App) ReconcileC2AfterConfigApply() error {
	if !a.config.C2.EnabledEffective() {
		a.shutdownC2()
		return nil
	}
	if a.c2Manager != nil {
		return nil
	}
	if a.db == nil || a.agentHandler == nil {
		return nil
	}
	m, wd, cancel := setupC2Runtime(a.config, a.db, a.agentHandler, a.logger.Logger)
	if m == nil {
		return nil
	}
	a.c2Manager = m
	a.c2Watchdog = wd
	a.c2WatchdogCancel = cancel
	if a.c2Handler != nil {
		a.c2Handler.SetManager(m)
	}
	a.logger.Info("C2 子系统已按配置启动")
	return nil
}

// shutdownC2 停止看门狗与所有监听器，并断开 Handler 引用。
func (a *App) shutdownC2() {
	had := a.c2WatchdogCancel != nil || a.c2Manager != nil
	if a.c2WatchdogCancel != nil {
		a.c2WatchdogCancel()
		a.c2WatchdogCancel = nil
	}
	a.c2Watchdog = nil
	if a.c2Manager != nil {
		a.c2Manager.Close()
		a.c2Manager = nil
	}
	if a.c2Handler != nil {
		a.c2Handler.SetManager(nil)
	}
	if had {
		a.logger.Info("C2 子系统已关闭")
	}
}
