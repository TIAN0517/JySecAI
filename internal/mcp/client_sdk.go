// Package mcp 外部 MCP 客户端 - 基于官方 go-sdk 实现，保证协议兼容性
package mcp

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"jysecai/internal/config"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"go.uber.org/zap"
)

const (
	clientName    = "JySecAI"
	clientVersion = "1.0.0"
)

// sdkClient 基于官方 MCP Go SDK 的外部 MCP 客户端，实现 ExternalMCPClient 接口
type sdkClient struct {
	session *mcp.ClientSession
	client  *mcp.Client
	logger  *zap.Logger
	mu      sync.RWMutex
	status  string // "disconnected", "connecting", "connected", "error"
}

// newSDKClientFromSession 用已连接成功的 session 构造（供 createSDKClient 内部使用）
func newSDKClientFromSession(session *mcp.ClientSession, client *mcp.Client, logger *zap.Logger) *sdkClient {
	return &sdkClient{
		session: session,
		client:  client,
		logger:  logger,
		status:  "connected",
	}
}

// lazySDKClient 延迟连接：Initialize() 时才调用官方 SDK 建立连接，对外实现 ExternalMCPClient
type lazySDKClient struct {
	serverCfg     config.ExternalMCPServerConfig
	logger        *zap.Logger
	sessionCancel context.CancelFunc
	inner         ExternalMCPClient // connected SDK client
	mu            sync.RWMutex
	status        string
}

func newLazySDKClient(serverCfg config.ExternalMCPServerConfig, logger *zap.Logger) *lazySDKClient {
	return &lazySDKClient{
		serverCfg: serverCfg,
		logger:    logger,
		status:    "connecting",
	}
}

func (c *lazySDKClient) setStatus(s string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.status = s
}

func (c *lazySDKClient) GetStatus() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if c.inner != nil {
		return c.inner.GetStatus()
	}
	return c.status
}

func (c *lazySDKClient) IsConnected() bool {
	c.mu.RLock()
	inner := c.inner
	c.mu.RUnlock()
	if inner != nil {
		return inner.IsConnected()
	}
	return false
}

func (c *lazySDKClient) Initialize(ctx context.Context) error {
	c.mu.Lock()
	if c.inner != nil {
		c.mu.Unlock()
		return nil
	}
	c.mu.Unlock()

	sessionCtx, sessionCancel := context.WithCancel(context.Background())
	type connectResult struct {
		inner ExternalMCPClient
		err   error
	}
	resultCh := make(chan connectResult)
	abandoned := make(chan struct{})
	go func() {
		inner, err := createSDKClient(sessionCtx, c.serverCfg, c.logger)
		select {
		case resultCh <- connectResult{inner: inner, err: err}:
		case <-abandoned:
			if inner != nil {
				_ = inner.Close()
			}
			sessionCancel()
		}
	}()

	var result connectResult
	select {
	case result = <-resultCh:
	case <-ctx.Done():
		close(abandoned)
		sessionCancel()
		c.setStatus("error")
		return ctx.Err()
	}

	if err := ctx.Err(); err != nil {
		sessionCancel()
		if result.inner != nil {
			_ = result.inner.Close()
		}
		c.setStatus("error")
		return err
	}

	if result.err != nil {
		sessionCancel()
		c.setStatus("error")
		return result.err
	}

	c.mu.Lock()
	if c.inner != nil {
		c.mu.Unlock()
		sessionCancel()
		if result.inner != nil {
			_ = result.inner.Close()
		}
		return nil
	}
	c.inner = result.inner
	c.sessionCancel = sessionCancel
	c.mu.Unlock()
	c.setStatus("connected")
	return nil
}

func (c *lazySDKClient) ListTools(ctx context.Context) ([]Tool, error) {
	c.mu.RLock()
	inner := c.inner
	c.mu.RUnlock()
	if inner == nil {
		return nil, fmt.Errorf("未连接")
	}
	return inner.ListTools(ctx)
}

func (c *lazySDKClient) CallTool(ctx context.Context, name string, args map[string]interface{}) (*ToolResult, error) {
	c.mu.RLock()
	inner := c.inner
	c.mu.RUnlock()
	if inner == nil {
		return nil, fmt.Errorf("未连接")
	}
	return inner.CallTool(ctx, name, args)
}

func (c *lazySDKClient) Ping(ctx context.Context) error {
	c.mu.RLock()
	inner := c.inner
	c.mu.RUnlock()
	if inner == nil {
		return fmt.Errorf("未连接")
	}
	return inner.Ping(ctx)
}

func (c *lazySDKClient) Close() error {
	c.mu.Lock()
	inner := c.inner
	sessionCancel := c.sessionCancel
	c.inner = nil
	c.sessionCancel = nil
	c.mu.Unlock()
	c.setStatus("disconnected")
	if sessionCancel != nil {
		sessionCancel()
	}
	if inner != nil {
		return inner.Close()
	}
	return nil
}

// markDisconnected 在检测到传输层断连时关闭底层 session，避免 IsConnected 仍返回 true。
func (c *lazySDKClient) markDisconnected() {
	c.mu.Lock()
	inner := c.inner
	sessionCancel := c.sessionCancel
	c.inner = nil
	c.sessionCancel = nil
	c.mu.Unlock()
	if sessionCancel != nil {
		sessionCancel()
	}
	if inner != nil {
		_ = inner.Close()
	}
	c.setStatus("disconnected")
}

func (c *sdkClient) setStatus(s string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.status = s
}

func (c *sdkClient) GetStatus() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.status
}

func (c *sdkClient) IsConnected() bool {
	return c.GetStatus() == "connected"
}

func (c *sdkClient) Initialize(ctx context.Context) error {
	// sdkClient 由 createSDKClient 在 Connect 成功后才创建，因此 Initialize 时已经连接
	// 此方法仅用于满足 ExternalMCPClient 接口，实际连接在 createSDKClient 中完成
	return nil
}

func (c *sdkClient) ListTools(ctx context.Context) ([]Tool, error) {
	if c.session == nil {
		return nil, fmt.Errorf("未连接")
	}
	res, err := c.session.ListTools(ctx, nil)
	if err != nil {
		return nil, err
	}
	if res == nil {
		return nil, nil
	}
	return sdkToolsToOur(res.Tools), nil
}

func (c *sdkClient) CallTool(ctx context.Context, name string, args map[string]interface{}) (*ToolResult, error) {
	if c.session == nil {
		return nil, fmt.Errorf("未连接")
	}
	params := &mcp.CallToolParams{
		Name:      name,
		Arguments: args,
	}
	res, err := c.session.CallTool(ctx, params)
	if err != nil {
		return nil, err
	}
	return sdkCallToolResultToOurs(res), nil
}

func (c *sdkClient) Ping(ctx context.Context) error {
	if c.session == nil {
		return fmt.Errorf("未连接")
	}
	return c.session.Ping(ctx, nil)
}

func (c *sdkClient) Close() error {
	c.setStatus("disconnected")
	if c.session != nil {
		err := c.session.Close()
		c.session = nil
		return err
	}
	return nil
}

// sdkToolsToOur 将 SDK 的 []*mcp.Tool 转为我们的 []Tool
func sdkToolsToOur(tools []*mcp.Tool) []Tool {
	if len(tools) == 0 {
		return nil
	}
	out := make([]Tool, 0, len(tools))
	for _, t := range tools {
		if t == nil {
			continue
		}
		schema := make(map[string]interface{})
		if t.InputSchema != nil {
			// SDK InputSchema 可能为 *jsonschema.Schema 或 map，统一转为 map
			if m, ok := t.InputSchema.(map[string]interface{}); ok {
				schema = m
			} else {
				_ = json.Unmarshal(mustJSON(t.InputSchema), &schema)
			}
		}
		desc := t.Description
		shortDesc := desc
		if t.Annotations != nil && t.Annotations.Title != "" {
			shortDesc = t.Annotations.Title
		}
		out = append(out, Tool{
			Name:             t.Name,
			Description:      desc,
			ShortDescription: shortDesc,
			InputSchema:      schema,
		})
	}
	return out
}

// sdkCallToolResultToOurs 将 SDK 的 *mcp.CallToolResult 转为我们的 *ToolResult
func sdkCallToolResultToOurs(res *mcp.CallToolResult) *ToolResult {
	if res == nil {
		return &ToolResult{Content: []Content{}}
	}
	content := sdkContentToOurs(res.Content)
	blocked, _ := res.Meta[toolGuardBlockedMetaKey].(bool)
	return &ToolResult{
		Content: content,
		IsError: res.IsError,
		Blocked: blocked,
	}
}

func sdkContentToOurs(list []mcp.Content) []Content {
	if len(list) == 0 {
		return nil
	}
	out := make([]Content, 0, len(list))
	for _, c := range list {
		switch v := c.(type) {
		case *mcp.TextContent:
			out = append(out, Content{Type: "text", Text: v.Text})
		default:
			out = append(out, Content{Type: "text", Text: fmt.Sprintf("%v", c)})
		}
	}
	return out
}

func mustJSON(v interface{}) []byte {
	b, _ := json.Marshal(v)
	return b
}

// createSDKClient 根据配置创建并连接外部 MCP 客户端（使用官方 SDK），返回实现 ExternalMCPClient 的 *sdkClient
// 若连接失败返回 (nil, error)。ctx 用于连接超时与取消。
func createSDKClient(ctx context.Context, serverCfg config.ExternalMCPServerConfig, logger *zap.Logger) (ExternalMCPClient, error) {
	if err := ValidateExternalMCPServerSecurity(serverCfg); err != nil {
		return nil, err
	}
	timeout := time.Duration(serverCfg.Timeout) * time.Second
	if timeout <= 0 {
		timeout = 30 * time.Second
	}

	transport := serverCfg.GetTransportType()
	if transport == "" {
		return nil, fmt.Errorf("配置缺少 command 或 url，且未指定 type/transport")
	}

	// 构造 ClientOptions：KeepAlive 心跳
	var clientOpts *mcp.ClientOptions
	if serverCfg.KeepAlive > 0 {
		clientOpts = &mcp.ClientOptions{
			KeepAlive: time.Duration(serverCfg.KeepAlive) * time.Second,
		}
	}

	client := mcp.NewClient(&mcp.Implementation{
		Name:    clientName,
		Version: clientVersion,
	}, clientOpts)

	var t mcp.Transport
	switch transport {
	case "stdio":
		if serverCfg.Command == "" {
			return nil, fmt.Errorf("stdio 模式需要配置 command")
		}
		commandPath, err := validateExternalMCPCommand(serverCfg)
		if err != nil {
			return nil, err
		}
		// 必须用 exec.Command 而非 CommandContext：doConnect 返回后 ctx 会被 cancel，
		// 若用 CommandContext(ctx) 会立刻杀掉子进程，导致 ListTools 等后续请求失败、显示 0 工具
		cmd := exec.Command(commandPath, serverCfg.Args...)
		cmd.Dir = strings.TrimSpace(serverCfg.WorkingDirectory)
		cmd.Env = envMapToSlice(serverCfg.Env, serverCfg.InheritParentEnv)
		// 子程序 stderr 接到服務 stderr（journald）：stdio MCP 子程序若啟動即死，
		// 沒有這行的話就只是無聲的 initialize: EOF，完全無法診斷。
		cmd.Stderr = os.Stderr
		ct := &mcp.CommandTransport{Command: cmd}
		if serverCfg.TerminateDuration > 0 {
			ct.TerminateDuration = time.Duration(serverCfg.TerminateDuration) * time.Second
		}
		t = ct
	case "sse":
		if serverCfg.URL == "" {
			return nil, fmt.Errorf("sse 模式需要配置 url")
		}
		// SSE 是长连接（GET 流持续打开），不能设置 http.Client.Timeout（会在超时后杀掉整个连接导致 EOF）。
		// 超时由每次 ListTools/CallTool 的 context 单独控制。
		httpClient := httpClientForLongLived(serverCfg.Headers, serverCfg.AllowInsecureHTTP)
		t = &mcp.SSEClientTransport{
			Endpoint:   serverCfg.URL,
			HTTPClient: httpClient,
		}
	case "http":
		if serverCfg.URL == "" {
			return nil, fmt.Errorf("http 模式需要配置 url")
		}
		httpClient := httpClientWithTimeoutAndHeaders(timeout, serverCfg.Headers, serverCfg.AllowInsecureHTTP)
		st := &mcp.StreamableClientTransport{
			Endpoint:   serverCfg.URL,
			HTTPClient: httpClient,
		}
		if serverCfg.MaxRetries > 0 {
			st.MaxRetries = serverCfg.MaxRetries
		}
		t = st
	default:
		return nil, fmt.Errorf("不支持的传输模式: %s（支持: stdio, sse, http）", transport)
	}

	session, err := client.Connect(ctx, t, nil)
	if err != nil {
		return nil, fmt.Errorf("连接失败: %w", err)
	}

	return newSDKClientFromSession(session, client, logger), nil
}

func envMapToSlice(env map[string]string, inheritParent bool) []string {
	m := make(map[string]string)
	if inheritParent {
		for _, s := range os.Environ() {
			if i := strings.IndexByte(s, '='); i > 0 {
				m[s[:i]] = s[i+1:]
			}
		}
	} else {
		// 保留启动常见运行时所需的非凭证变量；云端 token/API key 不会被隐式继承。
		for _, key := range []string{
			"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
			"HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
			"TMP", "TEMP", "LANG", "LC_ALL", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
			"NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
		} {
			if value, ok := os.LookupEnv(key); ok {
				m[key] = value
			}
		}
	}
	for k, v := range env {
		m[k] = v
	}
	out := make([]string, 0, len(m))
	for k, v := range m {
		out = append(out, k+"="+v)
	}
	return out
}

func ValidateExternalMCPServerSecurity(cfg config.ExternalMCPServerConfig) error {
	transport := cfg.GetTransportType()
	if transport != "http" && transport != "sse" {
		return nil
	}
	u, err := url.Parse(strings.TrimSpace(cfg.URL))
	if err != nil || u.Hostname() == "" {
		return fmt.Errorf("MCP URL 无效")
	}
	if u.User != nil {
		return fmt.Errorf("MCP URL 不允许内嵌账号或凭证，请使用 headers")
	}
	if strings.EqualFold(u.Scheme, "https") {
		return nil
	}
	if !strings.EqualFold(u.Scheme, "http") {
		return fmt.Errorf("MCP URL 仅支持 https；本机相容模式可使用 http")
	}
	host := strings.ToLower(u.Hostname())
	loopback := isLoopbackHost(host)
	if !loopback && !cfg.AllowInsecureHTTP {
		return fmt.Errorf("远端 MCP 必须使用 HTTPS；若为受控旧环境，请显式设置 allow_insecure_http")
	}
	return nil
}

// netParseIP 独立封装，便于测试 URL 主机验证且不触发 DNS。
var netParseIP = net.ParseIP

func isLoopbackHost(host string) bool {
	host = strings.ToLower(strings.TrimSpace(host))
	ip := netParseIP(host)
	return host == "localhost" || (ip != nil && ip.IsLoopback())
}

func validateExternalMCPCommand(cfg config.ExternalMCPServerConfig) (string, error) {
	commandPath, err := exec.LookPath(strings.TrimSpace(cfg.Command))
	if err != nil {
		return "", fmt.Errorf("找不到 MCP 命令: %w", err)
	}
	commandPath, err = filepath.Abs(commandPath)
	if err != nil {
		return "", fmt.Errorf("解析 MCP 命令路径失败: %w", err)
	}
	resolvedPath, err := filepath.EvalSymlinks(commandPath)
	if err != nil {
		return "", fmt.Errorf("解析 MCP 命令符号链接失败: %w", err)
	}
	if len(cfg.AllowedCommandRoots) > 0 {
		allowed := false
		for _, root := range cfg.AllowedCommandRoots {
			rootAbs, rootErr := filepath.Abs(strings.TrimSpace(root))
			if rootErr != nil {
				continue
			}
			rootResolved, rootErr := filepath.EvalSymlinks(rootAbs)
			if rootErr == nil && pathWithinRoot(rootResolved, resolvedPath) {
				allowed = true
				break
			}
		}
		if !allowed {
			return "", fmt.Errorf("MCP 命令不在 allowed_command_roots 内")
		}
	}
	wantHash := strings.ToLower(strings.TrimSpace(cfg.CommandSHA256))
	if wantHash != "" {
		if len(wantHash) != 64 {
			return "", fmt.Errorf("command_sha256 必须是 64 位十六进制")
		}
		f, openErr := os.Open(resolvedPath)
		if openErr != nil {
			return "", fmt.Errorf("读取 MCP 命令失败: %w", openErr)
		}
		h := sha256.New()
		_, copyErr := io.Copy(h, f)
		closeErr := f.Close()
		if copyErr != nil || closeErr != nil {
			return "", fmt.Errorf("计算 MCP 命令摘要失败")
		}
		if fmt.Sprintf("%x", h.Sum(nil)) != wantHash {
			return "", fmt.Errorf("MCP 命令 SHA-256 不匹配")
		}
	}
	// 安全驗證（allowed_command_roots、command_sha256）以 resolvedPath 為準——
	// 它與 commandPath 指向同一個檔案，防護語意不變。
	// 但「執行」必須回傳 commandPath 原路徑：venv 的 bin/python 是指向基礎直譯器的
	// 符號連結，若執行解引用後的路徑會脫離 venv（site-packages 失效），
	// 子程序會因 import mcp 失敗立即死亡，表現為 initialize: EOF。
	return commandPath, nil
}

func pathWithinRoot(root, target string) bool {
	rel, err := filepath.Rel(root, target)
	return err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))
}

func httpClientWithTimeoutAndHeaders(timeout time.Duration, headers map[string]string, allowInsecureHTTP bool) *http.Client {
	transport := http.DefaultTransport
	if len(headers) > 0 {
		transport = &headerRoundTripper{
			headers: headers,
			base:    http.DefaultTransport,
		}
	}
	return &http.Client{
		Timeout:       timeout,
		Transport:     transport,
		CheckRedirect: secureMCPRedirectPolicy(allowInsecureHTTP),
	}
}

// httpClientForLongLived 创建不设超时的 HTTP 客户端，用于 SSE 等长连接传输。
// SSE 的 GET 流会持续打开，http.Client.Timeout 会在超时后强制关闭连接导致 EOF。
// 超时由调用方通过 context 控制。
func httpClientForLongLived(headers map[string]string, allowInsecureHTTP bool) *http.Client {
	transport := http.DefaultTransport
	if len(headers) > 0 {
		transport = &headerRoundTripper{
			headers: headers,
			base:    http.DefaultTransport,
		}
	}
	return &http.Client{
		Transport:     transport,
		CheckRedirect: secureMCPRedirectPolicy(allowInsecureHTTP),
		// 不设 Timeout，SSE 长连接的超时由 per-request context 控制
	}
}

func secureMCPRedirectPolicy(allowInsecureHTTP bool) func(*http.Request, []*http.Request) error {
	return func(req *http.Request, via []*http.Request) error {
		if len(via) >= 10 {
			return errors.New("stopped after 10 redirects")
		}
		if strings.EqualFold(req.URL.Scheme, "https") {
			return nil
		}
		host := strings.ToLower(req.URL.Hostname())
		if strings.EqualFold(req.URL.Scheme, "http") {
			if allowInsecureHTTP {
				return nil
			}
			// localhost HTTP is only a compatibility path for a request that was
			// already local; a remote HTTPS server must not redirect into loopback.
			if isLoopbackHost(host) && len(via) > 0 && isLoopbackHost(via[0].URL.Hostname()) {
				return nil
			}
		}
		return fmt.Errorf("拒绝 MCP 重定向到不安全 URL")
	}
}

type headerRoundTripper struct {
	headers map[string]string
	base    http.RoundTripper
}

func (h *headerRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	for k, v := range h.headers {
		req.Header.Set(k, v)
	}
	return h.base.RoundTrip(req)
}
