package handler

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"sync"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/mcp"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"gopkg.in/yaml.v3"
)

// ExternalMCPHandler 外部MCP处理器
type ExternalMCPHandler struct {
	manager    *mcp.ExternalMCPManager
	config     *config.Config
	configPath string
	logger     *zap.Logger
	audit      *audit.Service
	mu         sync.RWMutex
}

// SetAudit wires platform audit logging.
func (h *ExternalMCPHandler) SetAudit(s *audit.Service) {
	h.audit = s
}

// NewExternalMCPHandler 创建外部MCP处理器
func NewExternalMCPHandler(manager *mcp.ExternalMCPManager, cfg *config.Config, configPath string, logger *zap.Logger) *ExternalMCPHandler {
	return &ExternalMCPHandler{
		manager:    manager,
		config:     cfg,
		configPath: configPath,
		logger:     logger,
	}
}

// GetExternalMCPs 获取所有外部MCP配置
func (h *ExternalMCPHandler) GetExternalMCPs(c *gin.Context) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	configs := h.manager.GetConfigs()

	// 获取所有外部MCP的工具数量
	toolCounts := h.manager.GetToolCounts()

	// 转换为响应格式
	result := make(map[string]ExternalMCPResponse)
	for name, cfg := range configs {
		client, exists := h.manager.GetClient(name)
		status := "disconnected"
		if exists {
			status = client.GetStatus()
		} else if h.isEnabled(cfg) {
			status = "disconnected"
		} else {
			status = "disabled"
		}

		toolCount := toolCounts[name]
		errorMsg := externalMCPStatusError(h.manager, name, status)

		result[name] = ExternalMCPResponse{
			Config:    externalMCPConfigForResponse(c, cfg),
			Status:    status,
			ToolCount: toolCount,
			Error:     errorMsg,
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"servers": result,
		"stats":   h.manager.GetStats(),
	})
}

// GetExternalMCP 获取单个外部MCP配置
func (h *ExternalMCPHandler) GetExternalMCP(c *gin.Context) {
	name := c.Param("name")

	h.mu.RLock()
	defer h.mu.RUnlock()

	configs := h.manager.GetConfigs()
	cfg, exists := configs[name]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "外部MCP配置不存在"})
		return
	}

	client, clientExists := h.manager.GetClient(name)
	status := "disconnected"
	if clientExists {
		status = client.GetStatus()
	} else if h.isEnabled(cfg) {
		status = "disconnected"
	} else {
		status = "disabled"
	}

	// 获取工具数量
	toolCount := 0
	if clientExists && client.IsConnected() {
		if count, err := h.manager.GetToolCount(name); err == nil {
			toolCount = count
		}
	}

	c.JSON(http.StatusOK, ExternalMCPResponse{
		Config:    externalMCPConfigForResponse(c, cfg),
		Status:    status,
		ToolCount: toolCount,
		Error:     externalMCPStatusError(h.manager, name, status),
	})
}

func externalMCPConfigForResponse(_ *gin.Context, cfg config.ExternalMCPServerConfig) config.ExternalMCPServerConfig {
	copyCfg := cfg
	if len(cfg.Env) > 0 {
		copyCfg.Env = make(map[string]string, len(cfg.Env))
		for key := range cfg.Env {
			copyCfg.Env[key] = "***"
		}
	}
	if len(cfg.Headers) > 0 {
		copyCfg.Headers = make(map[string]string, len(cfg.Headers))
		for key := range cfg.Headers {
			copyCfg.Headers[key] = "***"
		}
	}
	// stdio servers routinely receive their credential as a command-line
	// argument (--api-key <secret>), and an http/sse URL can embed one as
	// https://user:token@host/mcp. Reading this endpoint requires only
	// mcp:read while changing the server requires mcp:write, so returning
	// these verbatim would let a read-only role recover credentials that a
	// write role had to set. Mask any argument that looks like a secret and
	// strip userinfo from the URL.
	copyCfg.Args = redactMCPArgs(cfg.Args)
	copyCfg.URL = redactMCPURL(cfg.URL)
	return copyCfg
}

// redactMCPArgs masks the value that follows any flag naming a secret, plus
// any bare token-shaped argument.
func redactMCPArgs(args []string) []string {
	if len(args) == 0 {
		return args
	}
	// -p / -k 这类短选项不含任何关键字，必须显式列出，
	// 否则 `-p <password>` 会让密码原样出现在响应里。
	secretFlag := regexp.MustCompile(`(?i)^(--?[a-z0-9-]*(key|token|secret|password|passwd|auth|credential)[a-z0-9-]*(=|$)|-[pk]$)`)
	tokenish := regexp.MustCompile(`^[A-Za-z0-9_\-]{20,}$`)
	out := make([]string, len(args))
	maskNext := false
	for i, arg := range args {
		switch {
		case maskNext:
			out[i] = "***"
			maskNext = false
		case strings.Contains(arg, "=") && secretFlag.MatchString(arg):
			// --api-key=SECRET -> --api-key=***
			key, _, _ := strings.Cut(arg, "=")
			out[i] = key + "=***"
		case secretFlag.MatchString(arg):
			out[i] = arg
			maskNext = true
		case tokenish.MatchString(arg) && strings.ContainsAny(arg, "0123456789"):
			out[i] = "***"
		default:
			out[i] = arg
		}
	}
	return out
}

// redactMCPURL strips embedded credentials from an MCP endpoint URL.
func redactMCPURL(raw string) string {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return trimmed
	}
	u, err := url.Parse(trimmed)
	if err != nil || u.User == nil {
		return trimmed
	}
	if name := u.User.Username(); name != "" {
		u.User = url.User(name)
	} else {
		u.User = nil
	}
	return u.String()
}

func mergeExternalMCPSecrets(in, current config.ExternalMCPServerConfig) config.ExternalMCPServerConfig {
	mergeMap := func(values, old map[string]string) map[string]string {
		if values == nil {
			if old == nil {
				return nil
			}
			out := make(map[string]string, len(old))
			for key, value := range old {
				out[key] = value
			}
			return out
		}
		out := make(map[string]string, len(values))
		for key, value := range values {
			if value == "***" {
				if oldValue, ok := old[key]; ok {
					value = oldValue
				}
			}
			out[key] = value
		}
		return out
	}
	in.Env = mergeMap(in.Env, current.Env)
	in.Headers = mergeMap(in.Headers, current.Headers)
	// Restore argument values the client echoed back as "***" rather than
	// writing the mask into config.yaml. Matched positionally because a masked
	// argument carries no value to key on.
	if len(in.Args) == len(current.Args) {
		args := make([]string, len(in.Args))
		for i := range in.Args {
			if in.Args[i] == "***" {
				args[i] = current.Args[i]
			} else {
				args[i] = in.Args[i]
			}
		}
		in.Args = args
	}
	if in.URL == "***" {
		in.URL = current.URL
	} else if restored := restoreMCPURLUserinfo(in.URL, current.URL); restored != "" {
		in.URL = restored
	}
	return in
}

// restoreMCPURLUserinfo re-attaches the password that redactMCPURL stripped
// from an http/sse endpoint, preserving any edit the caller made to the rest
// of the URL.
func restoreMCPURLUserinfo(incoming, current string) string {
	cur, err := url.Parse(strings.TrimSpace(current))
	if err != nil || cur.User == nil {
		return ""
	}
	parsed, err := url.Parse(strings.TrimSpace(incoming))
	if err != nil {
		return ""
	}
	parsed.User = cur.User
	return parsed.String()
}

// externalMCPStatusError 在 error/disconnected 状态下返回最近错误（含断连原因）。
func externalMCPStatusError(manager *mcp.ExternalMCPManager, name, status string) string {
	if status != "error" && status != "disconnected" {
		return ""
	}
	return manager.GetError(name)
}

// AddOrUpdateExternalMCP 添加或更新外部MCP配置
func (h *ExternalMCPHandler) AddOrUpdateExternalMCP(c *gin.Context) {
	var req AddOrUpdateExternalMCPRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}

	name := c.Param("name")
	if name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "名称不能为空"})
		return
	}
	if old, ok := h.manager.GetConfigs()[name]; ok {
		req.Config = mergeExternalMCPSecrets(req.Config, old)
	}

	// 验证配置
	if err := h.validateConfig(req.Config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	h.mu.Lock()
	defer h.mu.Unlock()

	cfg := req.Config

	// Normalize the persisted/runtime configuration before handing it to the
	// manager.  The Web JSON format follows the official MCP convention where a
	// server is enabled unless `disabled` is true.  Keeping this normalization
	// here also ensures the manager receives expanded URLs and environment
	// values on the first connection attempt.
	if cfg.Disabled {
		cfg.ExternalMCPEnable = false
	} else if !cfg.ExternalMCPEnable {
		cfg.ExternalMCPEnable = true
	}
	config.ExpandConfigEnv(&cfg)

	// 添加或更新配置
	if err := h.manager.AddOrUpdateConfig(name, cfg); err != nil {
		h.logger.Error("添加或更新外部MCP配置失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "添加或更新配置失败: " + err.Error()})
		return
	}

	// 更新内存中的配置
	if h.config.ExternalMCP.Servers == nil {
		h.config.ExternalMCP.Servers = make(map[string]config.ExternalMCPServerConfig)
	}

	h.config.ExternalMCP.Servers[name] = cfg

	// 保存到配置文件
	if err := h.saveConfig(); err != nil {
		h.logger.Error("保存配置失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "保存配置失败: " + err.Error()})
		return
	}

	h.logger.Info("外部MCP配置已更新", zap.String("name", name))
	if h.audit != nil {
		h.audit.Record(c, audit.Entry{
			Category:     "external_mcp",
			Action:       "upsert",
			Result:       "success",
			ResourceType: "external_mcp",
			ResourceID:   name,
			Message:      "更新外部 MCP 配置",
		})
	}
	c.JSON(http.StatusOK, gin.H{"message": "配置已更新"})
}

// DeleteExternalMCP 删除外部MCP配置
func (h *ExternalMCPHandler) DeleteExternalMCP(c *gin.Context) {
	name := c.Param("name")

	h.mu.Lock()
	defer h.mu.Unlock()

	// 移除配置
	if err := h.manager.RemoveConfig(name); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "配置不存在"})
		return
	}

	// 从内存配置中删除
	if h.config.ExternalMCP.Servers != nil {
		delete(h.config.ExternalMCP.Servers, name)
	}

	// 保存到配置文件
	if err := h.saveConfig(); err != nil {
		h.logger.Error("保存配置失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "保存配置失败: " + err.Error()})
		return
	}

	h.logger.Info("外部MCP配置已删除", zap.String("name", name))
	if h.audit != nil {
		h.audit.Record(c, audit.Entry{
			Category:     "external_mcp",
			Action:       "delete",
			Result:       "success",
			ResourceType: "external_mcp",
			ResourceID:   name,
			Message:      "删除外部 MCP 配置",
		})
	}
	c.JSON(http.StatusOK, gin.H{"message": "配置已删除"})
}

// StartExternalMCP 启动外部MCP
func (h *ExternalMCPHandler) StartExternalMCP(c *gin.Context) {
	name := c.Param("name")

	h.mu.Lock()
	defer h.mu.Unlock()

	if h.config.ExternalMCP.Servers == nil {
		h.config.ExternalMCP.Servers = make(map[string]config.ExternalMCPServerConfig)
	}
	cfg, exists := h.config.ExternalMCP.Servers[name]
	if !exists {
		if mgrCfg, ok := h.manager.GetConfigs()[name]; ok {
			cfg = mgrCfg
			exists = true
		}
	}
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "配置不存在: " + name})
		return
	}
	if cfg.Disabled {
		reason := cfg.DisabledReason
		if reason == "" {
			reason = "已停用"
		}
		c.JSON(http.StatusConflict, gin.H{
			"error":  "MCP 已停用（常住，等待就绪）: " + reason,
			"status": "disabled",
		})
		return
	}
	cfg.ExternalMCPEnable = true
	h.config.ExternalMCP.Servers[name] = cfg

	// 保存到配置文件
	if err := h.saveConfig(); err != nil {
		h.logger.Error("保存配置失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "保存配置失败: " + err.Error()})
		return
	}

	// 启动客户端（立即创建客户端并设置状态为connecting，实际连接在后台进行）
	h.logger.Info("开始启动外部MCP", zap.String("name", name))
	if err := h.manager.StartClient(name); err != nil {
		h.logger.Error("启动外部MCP失败", zap.String("name", name), zap.Error(err))
		c.JSON(http.StatusBadRequest, gin.H{
			"error":  err.Error(),
			"status": "error",
		})
		return
	}

	// 获取客户端状态（应该是connecting）
	client, exists := h.manager.GetClient(name)
	status := "connecting"
	if exists {
		status = client.GetStatus()
	}

	// 立即返回，不等待连接完成
	// 客户端会在后台异步连接，用户可以通过状态查询接口查看连接状态
	c.JSON(http.StatusOK, gin.H{
		"message": "外部MCP启动请求已提交，正在后台连接中",
		"status":  status,
	})
}

// StopExternalMCP 停止外部MCP
func (h *ExternalMCPHandler) StopExternalMCP(c *gin.Context) {
	name := c.Param("name")

	h.mu.Lock()
	defer h.mu.Unlock()

	// 停止客户端
	if err := h.manager.StopClient(name); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 更新配置
	if h.config.ExternalMCP.Servers == nil {
		h.config.ExternalMCP.Servers = make(map[string]config.ExternalMCPServerConfig)
	}
	cfg := h.config.ExternalMCP.Servers[name]
	cfg.ExternalMCPEnable = false
	h.config.ExternalMCP.Servers[name] = cfg

	// 保存到配置文件
	if err := h.saveConfig(); err != nil {
		h.logger.Error("保存配置失败", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "保存配置失败: " + err.Error()})
		return
	}

	h.logger.Info("外部MCP已停止", zap.String("name", name))
	c.JSON(http.StatusOK, gin.H{"message": "外部MCP已停止"})
}

// GetExternalMCPStats 获取统计信息
func (h *ExternalMCPHandler) GetExternalMCPStats(c *gin.Context) {
	stats := h.manager.GetStats()
	c.JSON(http.StatusOK, stats)
}

// validateConfig 验证配置（同时支持官方 type 字段和旧版 transport 字段）
func (h *ExternalMCPHandler) validateConfig(cfg config.ExternalMCPServerConfig) error {
	transport := cfg.GetTransportType()
	if transport == "" {
		return fmt.Errorf("需要指定 command（stdio模式）或 url + type（http/sse模式）")
	}

	switch transport {
	case "http":
		if cfg.URL == "" {
			return fmt.Errorf("HTTP模式需要 url")
		}
	case "stdio":
		if cfg.Command == "" {
			return fmt.Errorf("stdio模式需要 command")
		}
	case "sse":
		if cfg.URL == "" {
			return fmt.Errorf("SSE模式需要 url")
		}
	default:
		return fmt.Errorf("不支持的传输模式: %s，支持的模式: http, stdio, sse", transport)
	}

	return mcp.ValidateExternalMCPServerSecurity(cfg)
}

// isEnabled 检查是否启用。官方 disabled 优先于 external_mcp_enable。
func (h *ExternalMCPHandler) isEnabled(cfg config.ExternalMCPServerConfig) bool {
	return cfg.ExternalMCPEnable && !cfg.Disabled
}

// saveConfig 保存配置到文件
func (h *ExternalMCPHandler) saveConfig() error {
	configFileMu.Lock()
	defer configFileMu.Unlock()
	data, err := os.ReadFile(h.configPath)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	if err := os.WriteFile(h.configPath+".backup", data, 0600); err != nil {
		h.logger.Warn("创建配置备份失败", zap.Error(err))
	}

	root, err := loadYAMLDocument(h.configPath)
	if err != nil {
		return fmt.Errorf("解析配置文件失败: %w", err)
	}
	_, protectedExternalMCP, err := config.ProtectSensitiveConfig(h.configPath, h.config.Robots, h.config.ExternalMCP)
	if err != nil {
		return fmt.Errorf("加密配置凭证失败: %w", err)
	}
	updateExternalMCPConfig(root, protectedExternalMCP)

	if err := writeYAMLDocument(h.configPath, root); err != nil {
		return fmt.Errorf("保存配置文件失败: %w", err)
	}

	h.logger.Info("配置已保存", zap.String("path", h.configPath))
	return nil
}

// updateExternalMCPConfig 更新外部MCP配置
func updateExternalMCPConfig(doc *yaml.Node, cfg config.ExternalMCPConfig) {
	root := doc.Content[0]
	externalMCPNode := ensureMap(root, "external_mcp")
	serversNode := ensureMap(externalMCPNode, "servers")

	// 清空现有服务器配置
	serversNode.Content = nil

	// 添加新的服务器配置
	for name, serverCfg := range cfg.Servers {
		nameNode := &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: name}
		serverNode := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
		serversNode.Content = append(serversNode.Content, nameNode, serverNode)

		// type（官方 MCP 传输类型）
		effectiveType := serverCfg.GetTransportType()
		if effectiveType != "" && effectiveType != "stdio" {
			// stdio 可省略（有 command 时自动推断）
			setStringInMap(serverNode, "type", effectiveType)
		}
		if serverCfg.Command != "" {
			setStringInMap(serverNode, "command", serverCfg.Command)
		}
		if len(serverCfg.Args) > 0 {
			setStringArrayInMap(serverNode, "args", serverCfg.Args)
		}
		if serverCfg.Env != nil && len(serverCfg.Env) > 0 {
			envNode := ensureMap(serverNode, "env")
			for envKey, envValue := range serverCfg.Env {
				setStringInMap(envNode, envKey, envValue)
			}
		}
		if serverCfg.WorkingDirectory != "" {
			setStringInMap(serverNode, "working_directory", serverCfg.WorkingDirectory)
		}
		if serverCfg.CommandSHA256 != "" {
			setStringInMap(serverNode, "command_sha256", serverCfg.CommandSHA256)
		}
		if len(serverCfg.AllowedCommandRoots) > 0 {
			setStringArrayInMap(serverNode, "allowed_command_roots", serverCfg.AllowedCommandRoots)
		}
		if serverCfg.InheritParentEnv {
			setBoolInMap(serverNode, "inherit_parent_env", true)
		}
		if serverCfg.URL != "" {
			setStringInMap(serverNode, "url", serverCfg.URL)
		}
		if serverCfg.Headers != nil && len(serverCfg.Headers) > 0 {
			headersNode := ensureMap(serverNode, "headers")
			for k, v := range serverCfg.Headers {
				setStringInMap(headersNode, k, v)
			}
		}
		if serverCfg.AllowInsecureHTTP {
			setBoolInMap(serverNode, "allow_insecure_http", true)
		}
		if serverCfg.Description != "" {
			setStringInMap(serverNode, "description", serverCfg.Description)
		}
		if serverCfg.Timeout > 0 {
			setIntInMap(serverNode, "timeout", serverCfg.Timeout)
		}
		// 官方标准字段
		if serverCfg.Disabled {
			setBoolInMap(serverNode, "disabled", true)
		}
		if serverCfg.DisabledReason != "" {
			setStringInMap(serverNode, "disabled_reason", serverCfg.DisabledReason)
		}
		if len(serverCfg.AutoApprove) > 0 {
			setStringArrayInMap(serverNode, "autoApprove", serverCfg.AutoApprove)
		}

		// SDK 高级配置
		if serverCfg.MaxRetries > 0 {
			setIntInMap(serverNode, "max_retries", serverCfg.MaxRetries)
		}
		if serverCfg.TerminateDuration > 0 {
			setIntInMap(serverNode, "terminate_duration", serverCfg.TerminateDuration)
		}
		if serverCfg.KeepAlive > 0 {
			setIntInMap(serverNode, "keep_alive", serverCfg.KeepAlive)
		}

		setBoolInMap(serverNode, "external_mcp_enable", serverCfg.ExternalMCPEnable)
		if serverCfg.ToolEnabled != nil && len(serverCfg.ToolEnabled) > 0 {
			toolEnabledNode := ensureMap(serverNode, "tool_enabled")
			for toolName, enabled := range serverCfg.ToolEnabled {
				setBoolInMap(toolEnabledNode, toolName, enabled)
			}
		}
	}
}

// setStringArrayInMap 设置字符串数组
func setStringArrayInMap(mapNode *yaml.Node, key string, values []string) {
	_, valueNode := ensureKeyValue(mapNode, key)
	valueNode.Kind = yaml.SequenceNode
	valueNode.Tag = "!!seq"
	valueNode.Content = nil
	for _, v := range values {
		itemNode := &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: v}
		valueNode.Content = append(valueNode.Content, itemNode)
	}
}

// AddOrUpdateExternalMCPRequest 添加或更新外部MCP请求
type AddOrUpdateExternalMCPRequest struct {
	Config config.ExternalMCPServerConfig `json:"config"`
}

// ExternalMCPResponse 外部MCP响应
type ExternalMCPResponse struct {
	Config    config.ExternalMCPServerConfig `json:"config"`
	Status    string                         `json:"status"`          // "connected", "disconnected", "disabled", "error", "connecting"
	ToolCount int                            `json:"tool_count"`      // 工具数量
	Error     string                         `json:"error,omitempty"` // 错误信息（仅在status为error时存在）
}
