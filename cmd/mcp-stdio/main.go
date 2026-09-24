package main

import (
	"jysecai/internal/config"
	"jysecai/internal/logger"
	"jysecai/internal/mcp"
	"jysecai/internal/security"
	"jysecai/internal/toolguard"
	"flag"
	"fmt"
	"os"

	"go.uber.org/zap"
)

func main() {
	var configPath = flag.String("config", "config.yaml", "配置文件路径")
	flag.Parse()

	// 加载配置
	cfg, err := config.Load(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	// 初始化日志（stdio 模式下使用 stderr 输出日志，避免干扰 JSON-RPC 通信）
	log := logger.New(cfg.Log.Level, "stderr", logger.DiagnosticOptions{
		Dir:           cfg.Log.DiagnosticDir,
		Disabled:      cfg.Log.DiagnosticDisabled,
		RetentionDays: cfg.Log.DiagnosticRetentionDays,
	})
	defer log.Sync()

	// 创建MCP服务器
	mcpServer := mcp.NewServer(log.Logger)
	guard, err := toolguard.NewManager(cfg.EffectiveToolGuard())
	if err != nil {
		fmt.Fprintf(os.Stderr, "初始化调用拦截失败: %v\n", err)
		os.Exit(1)
	}
	mcpServer.SetToolGuard(guard)

	// 创建安全工具执行器
	executor := security.NewExecutor(&cfg.Security, mcpServer, log.Logger)

	// Scanner Runtime Optimization v2：stdio / 操作員路徑使用 Manual 模式。
	// 與 Agent 自動循環的差異：
	//   - ExecutionModeManual：保留 additional_args 向後相容行為（既有
	//     YAML / CLI 操作員可手動傳遞額外 flag）。
	//   - ExecutionModeAgent：  additional_args 非空 → POLICY_DENIED，
	//     防止 Agent 自動呼叫鏈注入任意參數。
	// 同樣的 cfg.Security.Scanner.AuthorizedTargets 仍為單一 allowlist
	// 來源：空清單 = 拒絕所有外部掃描器目標（與 HTTP 主進程一致）。
	scannerMetrics := security.WireScannerRuntime(executor, &cfg.Security, security.ExecutionModeManual)
	log.Logger.Info("stdio scanner runtime hooks wired",
		zap.String("mode", string(security.ExecutionModeManual)),
		zap.Int("authorized_targets", len(cfg.Security.Scanner.AuthorizedTargets)),
		zap.String("metrics_snapshot", scannerMetrics.Snapshot().String()),
	)

	// 注册工具
	executor.RegisterTools(mcpServer)
	mcp.RegisterExecutionControlTools(mcpServer, nil)

	log.Logger.Info("MCP服务器（stdio模式）已启动，等待消息...")

	// 运行 stdio 循环
	if err := mcpServer.HandleStdio(); err != nil {
		log.Logger.Error("MCP服务器运行失败", zap.Error(err))
		os.Exit(1)
	}
}
