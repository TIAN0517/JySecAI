package handler

import (
	"bytes"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
	"unicode/utf8"

	"jysecai/internal/audit"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
)

// maxWebshellResponseBytes bounds how much of a WebShell response is buffered.
//
// webshell:write is granted to the operator role, so any operator could point a
// connection at a host that streams forever and turn io.ReadAll into an
// out-of-memory kill for every other user on the process. A transport timeout
// does not bound this: a peer sending at line rate fills the heap long before
// the deadline. 32 MiB matches the limit fofa.go already applies to outbound
// search responses.
const maxWebshellResponseBytes = 32 << 20

// readWebshellBody reads at most maxWebshellResponseBytes and reports whether
// the peer sent more, so the caller can tell the operator the output was
// clipped instead of silently returning a short result.
func readWebshellBody(r io.Reader) ([]byte, bool, error) {
	out, err := io.ReadAll(io.LimitReader(r, maxWebshellResponseBytes+1))
	if err != nil {
		return out, false, err
	}
	if len(out) > maxWebshellResponseBytes {
		return out[:maxWebshellResponseBytes], true, nil
	}
	return out, false, nil
}

// webshellSupportedEncodings 允许的 WebShell 响应编码取值（小写，含空串代表 auto）
// 仅暴露目前最常见的几种，其他需求可后续扩展（如 Big5、Shift_JIS 等）。
var webshellSupportedEncodings = map[string]struct{}{
	"":        {}, // 未配置，按 auto 处理
	"auto":    {},
	"utf-8":   {},
	"utf8":    {},
	"gbk":     {},
	"gb18030": {},
}

// normalizeWebshellEncoding 归一化编码标识：统一为小写，未知值回退为 auto，供持久化使用
func normalizeWebshellEncoding(enc string) string {
	enc = strings.ToLower(strings.TrimSpace(enc))
	if _, ok := webshellSupportedEncodings[enc]; !ok {
		return "auto"
	}
	if enc == "" {
		return "auto"
	}
	if enc == "utf8" {
		return "utf-8"
	}
	return enc
}

// decodeWebshellOutput 把 WebShell 返回的字节按指定编码转换为合法 UTF-8 字符串。
// 约定：
//   - "" / "auto"：若已是合法 UTF-8 原样返回，否则依次尝试 GB18030（GBK 超集）解码。
//   - "utf-8" / "utf8"：原样返回，非法字节交由 JSON 层按 U+FFFD 处理（保持原有行为）。
//   - "gbk" / "gb18030"：强制按对应编码解码；失败则回退原始字节。
//
// 该函数对空输入直接返回空串，避免不必要的转换。
func decodeWebshellOutput(raw []byte, encoding string) string {
	if len(raw) == 0 {
		return ""
	}
	enc := normalizeWebshellEncoding(encoding)
	switch enc {
	case "utf-8":
		return string(raw)
	case "gbk":
		if out, _, err := transform.Bytes(simplifiedchinese.GBK.NewDecoder(), raw); err == nil {
			return string(out)
		}
		return string(raw)
	case "gb18030":
		if out, _, err := transform.Bytes(simplifiedchinese.GB18030.NewDecoder(), raw); err == nil {
			return string(out)
		}
		return string(raw)
	default: // auto
		if utf8.Valid(raw) {
			return string(raw)
		}
		// GB18030 是 GBK 的超集，覆盖范围最广，auto 模式统一用它兜底
		if out, _, err := transform.Bytes(simplifiedchinese.GB18030.NewDecoder(), raw); err == nil {
			return string(out)
		}
		return string(raw)
	}
}

// webshellSupportedOS 允许的 WebShell 目标操作系统（小写，空串代表 auto）
var webshellSupportedOS = map[string]struct{}{
	"":        {},
	"auto":    {},
	"linux":   {},
	"windows": {},
}

// normalizeWebshellOS 归一化 OS 标识，未知值回退为 auto，供持久化使用
func normalizeWebshellOS(osTag string) string {
	osTag = strings.ToLower(strings.TrimSpace(osTag))
	if _, ok := webshellSupportedOS[osTag]; !ok {
		return "auto"
	}
	if osTag == "" {
		return "auto"
	}
	return osTag
}

// resolveWebshellOS 根据连接的 os 与 shellType 推断最终目标 OS（仅返回 "linux" 或 "windows"）。
// 规则：
//   - 显式 linux / windows：按用户选择。
//   - auto 或未知：asp/aspx → windows，其他 → linux。保持历史行为，平滑向后兼容。
func resolveWebshellOS(osTag, shellType string) string {
	osTag = strings.ToLower(strings.TrimSpace(osTag))
	switch osTag {
	case "linux":
		return "linux"
	case "windows":
		return "windows"
	}
	t := strings.ToLower(strings.TrimSpace(shellType))
	if t == "asp" || t == "aspx" {
		return "windows"
	}
	return "linux"
}

// quoteCmdPath 把路径按 Windows cmd.exe 规则转义。
// 使用双引号包裹，内部双引号转义为 ""（cmd 接受的写法）。
func quoteCmdPath(p string) string {
	if p == "" {
		return "\".\""
	}
	return "\"" + strings.ReplaceAll(p, "\"", "\"\"") + "\""
}

// normalizeWindowsCmdPath 把前端统一的 "/" 路径转换为 cmd 更稳定识别的 "\"。
// 仅用于 Windows 命令构造，不改变语义（例如 "." / ".." 会保持不变）。
func normalizeWindowsCmdPath(p string) string {
	s := strings.TrimSpace(p)
	if s == "" {
		return s
	}
	return strings.ReplaceAll(s, "/", "\\")
}

// quotePsSingle 把字符串按 PowerShell 单引号字符串规则转义（内部 ' → ”）。
// 供 PowerShell 脚本参数使用，全脚本只用单引号，外层 cmd 再用双引号包裹即可安全传递。
func quotePsSingle(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "''") + "'"
}

// quoteShellSinglePosix 把路径按 POSIX sh 单引号规则转义（内部 ' → '\”）
func quoteShellSinglePosix(p string) string {
	if p == "" {
		return "."
	}
	return "'" + strings.ReplaceAll(p, "'", "'\\''") + "'"
}

// quoteWebshellPath 按目标 OS 选择转义方案：Linux 用 POSIX 单引号，Windows 用 cmd 双引号
func quoteWebshellPath(path, osTag string) string {
	if resolveWebshellOS(osTag, "") == "windows" {
		return quoteCmdPath(path)
	}
	return quoteShellSinglePosix(path)
}

// buildWindowsPowerShellWrite 构造 Windows 端把 base64 内容一次性写入目标路径的 cmd 命令。
// 外层走 cmd.exe 的 powershell 调用，PowerShell 脚本里只用单引号字符串，避免嵌套引号陷阱。
func buildWindowsPowerShellWrite(path, b64 string) string {
	script := "$b=[Convert]::FromBase64String(" + quotePsSingle(b64) + ");" +
		"[IO.File]::WriteAllBytes(" + quotePsSingle(path) + ",$b)"
	return "powershell -NoProfile -NonInteractive -Command \"" + script + "\""
}

// buildWindowsPowerShellAppend 构造 Windows 端把 base64 内容追加写入目标路径的 cmd 命令（用于分块上传）
func buildWindowsPowerShellAppend(path, b64 string) string {
	script := "$b=[Convert]::FromBase64String(" + quotePsSingle(b64) + ");" +
		"$f=[IO.File]::Open(" + quotePsSingle(path) + ",[IO.FileMode]::Append,[IO.FileAccess]::Write,[IO.FileShare]::None);" +
		"try{$f.Write($b,0,$b.Length)}finally{$f.Close()}"
	return "powershell -NoProfile -NonInteractive -Command \"" + script + "\""
}

// fileCommandInput 封装 buildFileCommand 的输入，避免长参数列表
type fileCommandInput struct {
	Action     string
	Path       string
	TargetPath string
	Content    string
	ChunkIndex int
	OS         string
	ShellType  string
}

// buildFileCommand 根据目标 OS 与文件操作类型生成具体的远端命令字符串。
// 同一份实现供 HTTP 入口（FileOp）与 MCP 入口（FileOpWithConnection）共用，避免双份维护。
// 返回值第二位是用户可见的业务错误（如 "path is required"）。
func (h *WebShellHandler) buildFileCommand(in fileCommandInput) (string, error) {
	targetOS := resolveWebshellOS(in.OS, in.ShellType)
	action := strings.ToLower(strings.TrimSpace(in.Action))
	path := strings.TrimSpace(in.Path)

	switch action {
	case "list":
		p := path
		if p == "" {
			p = "."
		}
		if targetOS == "windows" {
			p = normalizeWindowsCmdPath(p)
			return "dir /a " + quoteCmdPath(p), nil
		}
		return "ls -la " + quoteShellSinglePosix(p), nil

	case "read":
		if path == "" {
			return "", errFileOpPathRequired
		}
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			return "type " + quoteCmdPath(path), nil
		}
		return "cat " + quoteShellSinglePosix(path), nil

	case "delete":
		if path == "" {
			return "", errFileOpPathRequired
		}
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			return "del /q /f " + quoteCmdPath(path), nil
		}
		return "rm -f " + quoteShellSinglePosix(path), nil

	case "mkdir":
		if path == "" {
			return "", errFileOpPathRequired
		}
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			// cmd 的 md 默认会自动创建中间目录（等价于 Linux 的 mkdir -p）
			return "md " + quoteCmdPath(path), nil
		}
		return "mkdir -p " + quoteShellSinglePosix(path), nil

	case "rename":
		oldPath := path
		newPath := strings.TrimSpace(in.TargetPath)
		if oldPath == "" || newPath == "" {
			return "", errFileOpRenameNeedsBothPaths
		}
		if targetOS == "windows" {
			oldPath = normalizeWindowsCmdPath(oldPath)
			newPath = normalizeWindowsCmdPath(newPath)
			return "move /y " + quoteCmdPath(oldPath) + " " + quoteCmdPath(newPath), nil
		}
		return "mv -f " + quoteShellSinglePosix(oldPath) + " " + quoteShellSinglePosix(newPath), nil

	case "write":
		if path == "" {
			return "", errFileOpPathRequired
		}
		// 统一策略：先把内容 base64 编码，再用目标平台对应方式解码写回，
		// 这样既能写入任意二进制/含引号的文本，又避免各家 shell 的转义地狱。
		b64 := base64.StdEncoding.EncodeToString([]byte(in.Content))
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			return buildWindowsPowerShellWrite(path, b64), nil
		}
		return "echo '" + b64 + "' | base64 -d > " + quoteShellSinglePosix(path), nil

	case "upload":
		if path == "" {
			return "", errFileOpPathRequired
		}
		if len(in.Content) > 512*1024 {
			return "", errFileOpUploadTooLarge
		}
		// 與 write 相同：先由伺服器端 base64 編碼，遠端再解碼寫入。
		// 原始 content 直接拼進 '...' 會讓其中的單引號終止引號，
		// 其後內容即在目標主機上執行。
		b64 := base64.StdEncoding.EncodeToString([]byte(in.Content))
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			return buildWindowsPowerShellWrite(path, b64), nil
		}
		return "echo '" + b64 + "' | base64 -d > " + quoteShellSinglePosix(path), nil

	case "upload_chunk":
		if path == "" {
			return "", errFileOpPathRequired
		}
		// 同 upload：內容必須先由伺服器端編碼，不能原樣拼進 shell 引號。
		b64 := base64.StdEncoding.EncodeToString([]byte(in.Content))
		if targetOS == "windows" {
			path = normalizeWindowsCmdPath(path)
			if in.ChunkIndex == 0 {
				return buildWindowsPowerShellWrite(path, b64), nil
			}
			return buildWindowsPowerShellAppend(path, b64), nil
		}
		redir := ">>"
		if in.ChunkIndex == 0 {
			redir = ">"
		}
		return "echo '" + b64 + "' | base64 -d " + redir + " " + quoteShellSinglePosix(path), nil
	}

	return "", errFileOpUnsupportedAction(action)
}

// 业务错误常量，便于上层统一返回用户可见提示
var (
	errFileOpPathRequired         = simpleError("path is required")
	errFileOpRenameNeedsBothPaths = simpleError("path and target_path are required for rename")
	errFileOpUploadTooLarge       = simpleError("upload content too large (max 512KB base64)")
)

func errFileOpUnsupportedAction(action string) error {
	return simpleError("unsupported action: " + action)
}

// simpleError 是不带堆栈的轻量错误类型，供 buildFileCommand 报可预期的参数校验错误
type simpleError string

func (e simpleError) Error() string { return string(e) }

// WebShellHandler 代理执行 WebShell 命令（类似冰蝎/蚁剑），避免前端跨域并统一构建请求
type WebShellHandler struct {
	logger *zap.Logger
	client *http.Client
	db     *database.DB
	audit  *audit.Service
}

func (h *WebShellHandler) recordOperationAudit(c *gin.Context, action, result, connectionID, targetURL, subject string, detail map[string]interface{}) {
	if h.audit == nil {
		return
	}
	if detail == nil {
		detail = map[string]interface{}{}
	}
	subjectHash := sha256.Sum256([]byte(subject))
	detail["subject_sha256"] = fmt.Sprintf("%x", subjectHash[:8])
	detail["subject_bytes"] = len(subject)
	if parsed, err := url.Parse(targetURL); err == nil {
		hostHash := sha256.Sum256([]byte(strings.ToLower(parsed.Host)))
		detail["target_host_sha256"] = fmt.Sprintf("%x", hostHash[:8])
	}
	resourceID := strings.TrimSpace(connectionID)
	if resourceID == "" {
		resourceID = "unsaved"
	}
	h.audit.Record(c, audit.Entry{
		Category: "webshell", Action: action, Result: result,
		ResourceType: "webshell", ResourceID: resourceID,
		Message: "WebShell 操作已执行（命令与路径仅记录摘要）", Detail: detail,
	})
}

// SetAudit wires platform audit logging.
func (h *WebShellHandler) SetAudit(s *audit.Service) {
	h.audit = s
}

// NewWebShellHandler 创建 WebShell 处理器，db 可为 nil（连接配置接口将不可用）
func NewWebShellHandler(logger *zap.Logger, db *database.DB) *WebShellHandler {
	return &WebShellHandler{
		logger: logger,
		client: &http.Client{
			Timeout:   30 * time.Second,
			Transport: newWebShellTransport(logger),
		},
		db: db,
	}
}

// newWebShellTransport 构造 WebShell 出站 HTTP 客户端。
//
// 默认相容模式：不校验证书。这是刻意保留的默认行为——政府与关键基础设施目标
// 普遍使用自签或内部 CA 凭证，若默认强制校验，授权范围内���多政府目标将无法探测。
// 需要校验时设置 JYSSECAI_WEBSHELL_CA_FILE / JYSSECAI_WEBSHELL_CA_SERVER 即可恢复。
// 三种模式的优先级：
//
//  1. JYSSECAI_WEBSHELL_INSECURE=1/true  显式相容模式（等价于默认，但用于覆盖 CA 配置）
//
//  2. JYSSECAI_WEBSHELL_CA_FILE / _CA_SERVER 有设置  以该 CA 校验证书
//
//  3. 两者都未设置                        默认相容模式，不校验证书
//
//     示例：
//     JYSSECAI_WEBSHELL_CA_FILE   指定 CA 证书文件（PEM），启用证书校验
//     JYSSECAI_WEBSHELL_CA_SERVER 指定 CA 发行机构（如 DigiCert Global Root G2）
//     JYSSECAI_WEBSHELL_INSECURE  显式设为 1/true 时跳过证书校验（覆盖 CA 配置）
func newWebShellTransport(logger *zap.Logger) *http.Transport {
	tr := &http.Transport{DisableKeepAlives: false}

	caFile := strings.TrimSpace(os.Getenv("JYSSECAI_WEBSHELL_CA_FILE"))
	caServer := strings.TrimSpace(os.Getenv("JYSSECAI_WEBSHELL_CA_SERVER"))
	insecure := strings.TrimSpace(os.Getenv("JYSSECAI_WEBSHELL_INSECURE"))

	// 1. 显式相容模式优先，可用于覆盖下方的 CA 配置。
	if insecure == "1" || strings.EqualFold(insecure, "true") {
		tr.TLSClientConfig = &tls.Config{InsecureSkipVerify: true, MinVersion: tls.VersionTLS12} //nolint:gosec // explicit legacy compatibility switch
		if logger != nil {
			logger.Warn("WebShell TLS: 已显式启用不安全相容模式，证书不会被验证",
				zap.String("insecure", insecure))
		}
		return tr
	}

	// 2. 配置了自定义 CA 时启用校验。
	if caFile != "" || caServer != "" {
		pool, err := buildWebShellCAPool()
		if err != nil {
			// 自定义 CA 配置错误时维持安全默认值；请求会使用系统 CA，而不是静默降级。
			if logger != nil {
				logger.Warn("WebShell TLS: 加载自定义 CA 失败，回退系统 CA", zap.Error(err))
			}
			pool, _ = x509.SystemCertPool()
			tr.TLSClientConfig = &tls.Config{RootCAs: pool, MinVersion: tls.VersionTLS12}
			return tr
		}
		tr.TLSClientConfig = &tls.Config{RootCAs: pool, MinVersion: tls.VersionTLS12}
		if logger != nil {
			logger.Debug("WebShell TLS: 已启用证书校验",
				zap.String("ca_file", caFile),
				zap.String("ca_server", caServer))
		}
		return tr
	}

	// 3. 未配置 CA：默认相容模式，保证授权范围内的自签目标可探测。
	tr.TLSClientConfig = &tls.Config{InsecureSkipVerify: true, MinVersion: tls.VersionTLS12} //nolint:gosec // default compatibility for self-signed authorized targets
	if logger != nil {
		logger.Warn("WebShell TLS: 未设置自定义 CA，已启用默认相容模式（不校验证书）。" +
			"如需校验请设置 JYSSECAI_WEBSHELL_CA_FILE。")
	}
	return tr
}

// buildWebShellCAPool 依据环境变量构建 CA 池。
func buildWebShellCAPool() (*x509.CertPool, error) {
	if caFile := os.Getenv("JYSSECAI_WEBSHELL_CA_FILE"); caFile != "" {
		pem, err := os.ReadFile(caFile)
		if err != nil {
			return nil, fmt.Errorf("读取 CA 文件失败: %w", err)
		}
		pool := x509.NewCertPool()
		if !pool.AppendCertsFromPEM(pem) {
			return nil, errors.New("CA 文件不含有效 PEM 凭证")
		}
		return pool, nil
	}

	// 指定发行机构时，在系统信任池基础上仅追加该机构签发的凭证。
	// 当前实现保留系统池（自签 WebShell 目标通常由内部 CA 签发），
	// CA_SERVER 供后续按需收窄时使用。
	pool, err := x509.SystemCertPool()
	if err != nil {
		return nil, fmt.Errorf("取得系统 CA 池失败: %w", err)
	}
	if pool == nil {
		return nil, errors.New("系统 CA 池为空")
	}
	return pool, nil
}

// CreateConnectionRequest 创建连接请求
type CreateConnectionRequest struct {
	ProjectID string `json:"project_id"`
	URL       string `json:"url" binding:"required"`
	Password  string `json:"password"`
	Type      string `json:"type"`
	Method    string `json:"method"`
	CmdParam  string `json:"cmd_param"`
	Remark    string `json:"remark"`
	Encoding  string `json:"encoding"`
	OS        string `json:"os"`
}

// UpdateConnectionRequest 更新连接请求
type UpdateConnectionRequest struct {
	ProjectID string `json:"project_id"`
	URL       string `json:"url" binding:"required"`
	Password  string `json:"password"`
	Type      string `json:"type"`
	Method    string `json:"method"`
	CmdParam  string `json:"cmd_param"`
	Remark    string `json:"remark"`
	Encoding  string `json:"encoding"`
	OS        string `json:"os"`
}

// ListConnections 列出所有 WebShell 连接（GET /api/webshell/connections）
func (h *WebShellHandler) ListConnections(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	session, ok := security.CurrentSession(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未登录"})
		return
	}
	list, err := h.db.ListWebshellConnectionsForAccess(session.UserID, session.Scope, c.Query("project_id"))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if list == nil {
		list = []database.WebShellConnection{}
	}
	for i := range list {
		list[i].Password = ""
	}
	c.JSON(http.StatusOK, list)
}

// CreateConnection 创建 WebShell 连接（POST /api/webshell/connections）
func (h *WebShellHandler) CreateConnection(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	var req CreateConnectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.URL = strings.TrimSpace(req.URL)
	if req.URL == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "url is required"})
		return
	}
	if _, err := url.Parse(req.URL); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid url"})
		return
	}
	projectID := strings.TrimSpace(req.ProjectID)
	if !h.canAccessProject(c, projectID) {
		c.JSON(http.StatusForbidden, gin.H{"error": "project access denied"})
		return
	}
	method := strings.ToLower(strings.TrimSpace(req.Method))
	if method != "get" && method != "post" {
		method = "post"
	}
	shellType := strings.ToLower(strings.TrimSpace(req.Type))
	if shellType == "" {
		shellType = "php"
	}
	conn := &database.WebShellConnection{
		ID:        "ws_" + strings.ReplaceAll(uuid.New().String(), "-", "")[:12],
		ProjectID: projectID,
		URL:       req.URL,
		Password:  strings.TrimSpace(req.Password),
		Type:      shellType,
		Method:    method,
		CmdParam:  strings.TrimSpace(req.CmdParam),
		Remark:    strings.TrimSpace(req.Remark),
		Encoding:  normalizeWebshellEncoding(req.Encoding),
		OS:        normalizeWebshellOS(req.OS),
		CreatedAt: time.Now(),
	}
	if err := h.db.CreateWebshellConnection(conn); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if session, ok := security.CurrentSession(c); ok {
		_ = h.db.SetResourceOwner("webshell", conn.ID, session.UserID)
		_ = h.db.AssignResourceToUser(session.UserID, "webshell", conn.ID)
	}
	if h.audit != nil {
		host := req.URL
		if u, err := url.Parse(req.URL); err == nil {
			host = u.Host
		}
		h.audit.RecordOK(c, "webshell", "connection_create", "创建 WebShell 连接", "webshell_connection", conn.ID, map[string]interface{}{
			"host": host, "type": shellType,
		})
	}
	conn.Password = ""
	c.JSON(http.StatusOK, conn)
}

// UpdateConnection 更新 WebShell 连接（PUT /api/webshell/connections/:id）
func (h *WebShellHandler) UpdateConnection(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	existing, err := h.db.GetWebshellConnection(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if existing == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "connection not found"})
		return
	}
	var req UpdateConnectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.URL = strings.TrimSpace(req.URL)
	if req.URL == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "url is required"})
		return
	}
	if _, err := url.Parse(req.URL); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid url"})
		return
	}
	projectID := strings.TrimSpace(req.ProjectID)
	if !h.canAccessProject(c, projectID) {
		c.JSON(http.StatusForbidden, gin.H{"error": "project access denied"})
		return
	}
	method := strings.ToLower(strings.TrimSpace(req.Method))
	if method != "get" && method != "post" {
		method = "post"
	}
	shellType := strings.ToLower(strings.TrimSpace(req.Type))
	if shellType == "" {
		shellType = "php"
	}
	password := strings.TrimSpace(req.Password)
	if password == "" {
		password = existing.Password
	}
	conn := &database.WebShellConnection{
		ID:        id,
		ProjectID: projectID,
		URL:       req.URL,
		Password:  password,
		Type:      shellType,
		Method:    method,
		CmdParam:  strings.TrimSpace(req.CmdParam),
		Remark:    strings.TrimSpace(req.Remark),
		Encoding:  normalizeWebshellEncoding(req.Encoding),
		OS:        normalizeWebshellOS(req.OS),
	}
	if err := h.db.UpdateWebshellConnection(conn); err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	updated, _ := h.db.GetWebshellConnection(id)
	if updated != nil {
		updated.Password = ""
		c.JSON(http.StatusOK, updated)
	} else {
		conn.Password = ""
		c.JSON(http.StatusOK, conn)
	}
}

// DeleteConnection 删除 WebShell 连接（DELETE /api/webshell/connections/:id）
func (h *WebShellHandler) DeleteConnection(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	if err := h.db.DeleteWebshellConnection(id); err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if h.audit != nil {
		h.audit.RecordOK(c, "webshell", "connection_delete", "删除 WebShell 连接", "webshell_connection", id, nil)
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// GetConnectionState 获取 WebShell 连接关联的前端持久化状态（GET /api/webshell/connections/:id/state）
func (h *WebShellHandler) GetConnectionState(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	conn, err := h.db.GetWebshellConnection(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if conn == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "connection not found"})
		return
	}
	stateJSON, err := h.db.GetWebshellConnectionState(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	var state interface{}
	if err := json.Unmarshal([]byte(stateJSON), &state); err != nil {
		state = map[string]interface{}{}
	}
	c.JSON(http.StatusOK, gin.H{"state": state})
}

// SaveConnectionState 保存 WebShell 连接关联的前端持久化状态（PUT /api/webshell/connections/:id/state）
func (h *WebShellHandler) SaveConnectionState(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	conn, err := h.db.GetWebshellConnection(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if conn == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "connection not found"})
		return
	}
	var req struct {
		State json.RawMessage `json:"state"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	raw := req.State
	if len(raw) == 0 {
		raw = json.RawMessage(`{}`)
	}
	if len(raw) > 2*1024*1024 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "state payload too large (max 2MB)"})
		return
	}
	var anyJSON interface{}
	if err := json.Unmarshal(raw, &anyJSON); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "state must be valid json"})
		return
	}
	if err := h.db.UpsertWebshellConnectionState(id, string(raw)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// GetAIHistory 获取指定 WebShell 连接的 AI 助手对话历史（GET /api/webshell/connections/:id/ai-history）
func (h *WebShellHandler) GetAIHistory(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	conv, err := h.db.GetConversationByWebshellConnectionID(id)
	if err != nil {
		h.logger.Warn("获取 WebShell AI 对话失败", zap.String("connectionId", id), zap.Error(err))
		c.JSON(http.StatusOK, gin.H{"conversationId": nil, "messages": []database.Message{}})
		return
	}
	if conv == nil {
		c.JSON(http.StatusOK, gin.H{"conversationId": nil, "messages": []database.Message{}})
		return
	}
	c.JSON(http.StatusOK, gin.H{"conversationId": conv.ID, "messages": conv.Messages})
}

// ListAIConversations 列出该 WebShell 连接下的所有 AI 对话（供侧边栏）
func (h *WebShellHandler) ListAIConversations(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "database not available"})
		return
	}
	id := strings.TrimSpace(c.Param("id"))
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id is required"})
		return
	}
	if !h.webshellResourceAllowed(c, id) {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}
	list, err := h.db.ListConversationsByWebshellConnectionID(id)
	if err != nil {
		h.logger.Warn("列出 WebShell AI 对话失败", zap.String("connectionId", id), zap.Error(err))
		c.JSON(http.StatusOK, []database.WebShellConversationItem{})
		return
	}
	if list == nil {
		list = []database.WebShellConversationItem{}
	}
	c.JSON(http.StatusOK, list)
}

// ExecRequest 执行命令请求（前端传入连接信息 + 命令）
type ExecRequest struct {
	URL          string `json:"url" binding:"required"`
	Password     string `json:"password"`
	Type         string `json:"type"`      // php, asp, aspx, jsp, custom
	Method       string `json:"method"`    // GET 或 POST，空则默认 POST
	CmdParam     string `json:"cmd_param"` // 命令参数名，如 cmd/xxx，空则默认 cmd
	Encoding     string `json:"encoding"`  // 响应编码：auto / utf-8 / gbk / gb18030，空则 auto
	OS           string `json:"os"`        // 目标操作系统：auto / linux / windows，当前 exec 不用它，保留字段便于未来扩展
	ConnectionID string `json:"connection_id,omitempty"`
	Command      string `json:"command" binding:"required"`
}

// ExecResponse 执行命令响应
type ExecResponse struct {
	OK       bool   `json:"ok"`
	Output   string `json:"output"`
	Error    string `json:"error,omitempty"`
	HTTPCode int    `json:"http_code,omitempty"`
}

// FileOpRequest 文件操作请求
type FileOpRequest struct {
	URL          string `json:"url" binding:"required"`
	Password     string `json:"password"`
	Type         string `json:"type"`
	Method       string `json:"method"`                    // GET 或 POST，空则默认 POST
	CmdParam     string `json:"cmd_param"`                 // 命令参数名，如 cmd/xxx，空则默认 cmd
	Encoding     string `json:"encoding"`                  // 响应编码：auto / utf-8 / gbk / gb18030，空则 auto
	OS           string `json:"os"`                        // 目标操作系统：auto / linux / windows，空则按 shellType 推断
	ConnectionID string `json:"connection_id,omitempty"`   // 可选：连接 ID；服务端探活出 OS 后会回写到此连接
	Action       string `json:"action" binding:"required"` // list, read, delete, write, mkdir, rename, upload, upload_chunk
	Path         string `json:"path"`
	TargetPath   string `json:"target_path"` // rename 时目标路径
	Content      string `json:"content"`     // write/upload 时使用
	ChunkIndex   int    `json:"chunk_index"` // upload_chunk 时，0 表示首块
}

// FileOpResponse 文件操作响应
type FileOpResponse struct {
	OK         bool   `json:"ok"`
	Output     string `json:"output"`
	Error      string `json:"error,omitempty"`
	DetectedOS string `json:"detected_os,omitempty"` // 仅在 auto 模式且探活成功时返回，前端应更新本地缓存
}

func (h *WebShellHandler) Exec(c *gin.Context) {
	var req ExecRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.URL = strings.TrimSpace(req.URL)
	req.Command = strings.TrimSpace(req.Command)
	if req.URL == "" || req.Command == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "url and command are required"})
		return
	}
	// Pre-save connectivity tests send form credentials without connection_id.
	// Saved connections must go through resource ACL; DB credentials are authoritative.
	if cid := strings.TrimSpace(req.ConnectionID); cid != "" {
		conn, allowed := h.authorizedWebshellConnection(c, cid, req.URL)
		if !allowed {
			c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
			return
		}
		// Never let a caller pair an authorized ID with attacker-controlled
		// transport credentials or a URL.
		req.URL, req.Password, req.Type = conn.URL, conn.Password, conn.Type
		req.Method, req.CmdParam, req.Encoding = conn.Method, conn.CmdParam, conn.Encoding
	} else if !security.SessionHasPermission(c, "webshell:write") ||
		// 省略 connection_id 时使用调用者自带的 url/password，可直达内网任意
		// 目标并把回显当命令输出返回。这是「存库前的连通性测试」，但非管理员
		// 不应拥有该能力：webshell:write 默认授予 Operator，而其 scope 为
		// assigned，本应只能操作自己名下的连接。
		!security.SessionHasPermission(c, "webshell:connect-unsaved") {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}

	parsed, err := url.Parse(req.URL)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid url: only http(s) allowed"})
		return
	}

	useGET := strings.ToUpper(strings.TrimSpace(req.Method)) == "GET"
	cmdParam := strings.TrimSpace(req.CmdParam)
	if cmdParam == "" {
		cmdParam = "cmd"
	}
	var httpReq *http.Request
	if useGET {
		targetURL := h.buildExecURL(req.URL, req.Type, req.Password, cmdParam, req.Command)
		httpReq, err = http.NewRequest(http.MethodGet, targetURL, nil)
	} else {
		body := h.buildExecBody(req.Type, req.Password, cmdParam, req.Command)
		httpReq, err = http.NewRequest(http.MethodPost, req.URL, bytes.NewReader(body))
		httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	if err != nil {
		h.logger.Warn("webshell exec NewRequest", zap.Error(err))
		h.recordOperationAudit(c, "command_execute", "failure", req.ConnectionID, req.URL, req.Command, map[string]interface{}{"stage": "build_request"})
		c.JSON(http.StatusInternalServerError, ExecResponse{OK: false, Error: err.Error()})
		return
	}
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (compatible; JySecAI-WebShell/1.0)")

	resp, err := h.client.Do(httpReq)
	if err != nil {
		h.logger.Warn("webshell exec Do", zap.String("url", req.URL), zap.Error(err))
		h.recordOperationAudit(c, "command_execute", "failure", req.ConnectionID, req.URL, req.Command, map[string]interface{}{"stage": "transport"})
		c.JSON(http.StatusOK, ExecResponse{OK: false, Error: err.Error()})
		return
	}
	defer resp.Body.Close()

	out, truncated, readErr := readWebshellBody(resp.Body)
	if readErr != nil {
		h.logger.Warn("webshell exec read body", zap.Error(readErr))
	}
	if truncated {
		h.logger.Warn("webshell exec response truncated", zap.Int("limit_bytes", maxWebshellResponseBytes))
	}
	output := decodeWebshellOutput(out, req.Encoding)
	if truncated {
		output += fmt.Sprintf("\n[响应超过 %d 字节，已截断]", maxWebshellResponseBytes)
	}
	httpCode := resp.StatusCode

	ok := resp.StatusCode == http.StatusOK
	auditResult := "failure"
	if ok && readErr == nil {
		auditResult = "success"
	}
	h.recordOperationAudit(c, "command_execute", auditResult, req.ConnectionID, req.URL, req.Command, map[string]interface{}{"http_code": httpCode, "response_bytes": len(out)})
	c.JSON(http.StatusOK, ExecResponse{
		OK:       ok,
		Output:   output,
		HTTPCode: httpCode,
	})
}

// buildExecBody 按常见 WebShell 约定构建 POST 体（多数使用 pass + cmd，可配置命令参数名）
func (h *WebShellHandler) buildExecBody(shellType, password, cmdParam, command string) []byte {
	form := h.execParams(shellType, password, cmdParam, command)
	return []byte(form.Encode())
}

// buildExecURL 构建 GET 请求的完整 URL（baseURL + ?pass=xxx&cmd=yyy，cmd 可配置）
func (h *WebShellHandler) buildExecURL(baseURL, shellType, password, cmdParam, command string) string {
	form := h.execParams(shellType, password, cmdParam, command)
	if parsed, err := url.Parse(baseURL); err == nil {
		parsed.RawQuery = form.Encode()
		return parsed.String()
	}
	return baseURL + "?" + form.Encode()
}

func (h *WebShellHandler) execParams(shellType, password, cmdParam, command string) url.Values {
	shellType = strings.ToLower(strings.TrimSpace(shellType))
	if shellType == "" {
		shellType = "php"
	}
	if strings.TrimSpace(cmdParam) == "" {
		cmdParam = "cmd"
	}
	form := url.Values{}
	form.Set("pass", password)
	form.Set(cmdParam, command)
	return form
}

func (h *WebShellHandler) FileOp(c *gin.Context) {
	var req FileOpRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.URL = strings.TrimSpace(req.URL)
	req.Action = strings.ToLower(strings.TrimSpace(req.Action))
	if req.URL == "" || req.Action == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "url and action are required"})
		return
	}
	if cid := strings.TrimSpace(req.ConnectionID); cid != "" {
		conn, allowed := h.authorizedWebshellConnection(c, cid, req.URL)
		if !allowed {
			c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
			return
		}
		req.URL, req.Password, req.Type = conn.URL, conn.Password, conn.Type
		req.Method, req.CmdParam, req.Encoding, req.OS = conn.Method, conn.CmdParam, conn.Encoding, conn.OS
	} else if !security.SessionHasPermission(c, "webshell:write") ||
		// 省略 connection_id 时使用调用者自带的 url/password，可直达内网任意
		// 目标并把回显当命令输出返回。这是「存库前的连通性测试」，但非管理员
		// 不应拥有该能力：webshell:write 默认授予 Operator，而其 scope 为
		// assigned，本应只能操作自己名下的连接。
		!security.SessionHasPermission(c, "webshell:connect-unsaved") {
		c.JSON(http.StatusForbidden, gin.H{"error": "无权访问该资源"})
		return
	}

	parsed, err := url.Parse(req.URL)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid url: only http(s) allowed"})
		return
	}

	// 若 OS 未显式配置，先发一次探活命令，识别出真实 OS 再构造文件操作命令。
	// 这解决了 "Windows + PHP + OS=auto" 场景下旧 fallback 错发 `ls -la` 导致目录列不出来的问题。
	osTag := req.OS
	detectedOS := ""
	if normalizeWebshellOS(osTag) == "auto" {
		if probed := probeWebshellOSViaExec(h.newHTTPExecFn(req.URL, req.Password, req.Type, req.Method, req.CmdParam, req.Encoding)); probed != "" {
			osTag = probed
			detectedOS = probed
			// 若前端带了 connection_id，顺带把探活结果持久化到该连接，后续刷新零成本
			if cid := strings.TrimSpace(req.ConnectionID); cid != "" {
				h.persistDetectedOS(cid, probed)
			}
		}
	}

	command, cmdErr := h.buildFileCommand(fileCommandInput{
		Action:     req.Action,
		Path:       req.Path,
		TargetPath: req.TargetPath,
		Content:    req.Content,
		ChunkIndex: req.ChunkIndex,
		OS:         osTag,
		ShellType:  req.Type,
	})
	if cmdErr != nil {
		h.recordOperationAudit(c, "file_operation", "failure", req.ConnectionID, req.URL, req.Path, map[string]interface{}{"operation": req.Action, "stage": "validation"})
		c.JSON(http.StatusBadRequest, FileOpResponse{OK: false, Error: cmdErr.Error()})
		return
	}

	useGET := strings.ToUpper(strings.TrimSpace(req.Method)) == "GET"
	cmdParam := strings.TrimSpace(req.CmdParam)
	if cmdParam == "" {
		cmdParam = "cmd"
	}
	var httpReq *http.Request
	if useGET {
		targetURL := h.buildExecURL(req.URL, req.Type, req.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodGet, targetURL, nil)
	} else {
		body := h.buildExecBody(req.Type, req.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodPost, req.URL, bytes.NewReader(body))
		httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	if err != nil {
		h.recordOperationAudit(c, "file_operation", "failure", req.ConnectionID, req.URL, req.Path, map[string]interface{}{"operation": req.Action, "stage": "build_request"})
		c.JSON(http.StatusInternalServerError, FileOpResponse{OK: false, Error: err.Error()})
		return
	}
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (compatible; JySecAI-WebShell/1.0)")

	resp, err := h.client.Do(httpReq)
	if err != nil {
		h.recordOperationAudit(c, "file_operation", "failure", req.ConnectionID, req.URL, req.Path, map[string]interface{}{"operation": req.Action, "stage": "transport"})
		c.JSON(http.StatusOK, FileOpResponse{OK: false, Error: err.Error()})
		return
	}
	defer resp.Body.Close()

	out, truncated, readErr := readWebshellBody(resp.Body)
	if readErr != nil {
		h.logger.Warn("webshell fileop read body", zap.Error(readErr))
	}
	if truncated {
		h.logger.Warn("webshell fileop response truncated", zap.Int("limit_bytes", maxWebshellResponseBytes))
	}
	output := decodeWebshellOutput(out, req.Encoding)
	if truncated {
		output += fmt.Sprintf("\n[响应超过 %d 字节，已截断]", maxWebshellResponseBytes)
	}
	ok := resp.StatusCode == http.StatusOK && readErr == nil
	auditResult := "failure"
	if ok {
		auditResult = "success"
	}
	h.recordOperationAudit(c, "file_operation", auditResult, req.ConnectionID, req.URL, req.Path, map[string]interface{}{
		"operation": req.Action, "http_code": resp.StatusCode, "response_bytes": len(out), "content_bytes": len(req.Content),
	})

	c.JSON(http.StatusOK, FileOpResponse{
		OK:         resp.StatusCode == http.StatusOK,
		Output:     output,
		DetectedOS: detectedOS,
	})
}

func (h *WebShellHandler) authorizedWebshellConnection(c *gin.Context, connectionID, requestURL string) (*database.WebShellConnection, bool) {
	connectionID = strings.TrimSpace(connectionID)
	if connectionID == "" {
		return nil, false
	}
	if h.db == nil {
		return nil, false
	}
	session, ok := security.CurrentSession(c)
	if !ok || !h.db.UserCanAccessResource(session.UserID, session.Scope, "webshell", connectionID) {
		return nil, false
	}
	conn, err := h.db.GetWebshellConnection(connectionID)
	if err != nil || conn == nil {
		return nil, false
	}
	if requestURL = strings.TrimSpace(requestURL); requestURL != "" && strings.TrimSpace(conn.URL) != requestURL {
		return nil, false
	}
	return conn, true
}

func (h *WebShellHandler) webshellResourceAllowed(c *gin.Context, connectionID string) bool {
	if h.db == nil {
		return false
	}
	session, ok := security.CurrentSession(c)
	return ok && h.db.UserCanAccessResource(session.UserID, session.Scope, "webshell", strings.TrimSpace(connectionID))
}

func (h *WebShellHandler) canAccessProject(c *gin.Context, projectID string) bool {
	projectID = strings.TrimSpace(projectID)
	if projectID == "" || h.db == nil {
		return true
	}
	session, ok := security.CurrentSession(c)
	if !ok {
		return false
	}
	if session.Scope == database.RBACScopeAll {
		return true
	}
	return h.db.UserCanAccessResource(session.UserID, session.Scope, "project", projectID)
}

// ExecWithConnection 在指定 WebShell 连接上执行命令（供 MCP/Agent 等非 HTTP 调用）
func (h *WebShellHandler) ExecWithConnection(conn *database.WebShellConnection, command string) (output string, ok bool, errMsg string) {
	if conn == nil {
		return "", false, "connection is nil"
	}
	command = strings.TrimSpace(command)
	if command == "" {
		h.recordOperationAudit(nil, "command_execute", "failure", conn.ID, conn.URL, command, map[string]interface{}{"stage": "validation", "source": "internal"})
		return "", false, "command is required"
	}
	useGET := strings.ToUpper(strings.TrimSpace(conn.Method)) == "GET"
	cmdParam := strings.TrimSpace(conn.CmdParam)
	if cmdParam == "" {
		cmdParam = "cmd"
	}
	var httpReq *http.Request
	var err error
	if useGET {
		targetURL := h.buildExecURL(conn.URL, conn.Type, conn.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodGet, targetURL, nil)
	} else {
		body := h.buildExecBody(conn.Type, conn.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodPost, conn.URL, bytes.NewReader(body))
		httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	if err != nil {
		h.recordOperationAudit(nil, "command_execute", "failure", conn.ID, conn.URL, command, map[string]interface{}{"stage": "build_request", "source": "internal"})
		return "", false, err.Error()
	}
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (compatible; JySecAI-WebShell/1.0)")
	resp, err := h.client.Do(httpReq)
	if err != nil {
		h.recordOperationAudit(nil, "command_execute", "failure", conn.ID, conn.URL, command, map[string]interface{}{"stage": "transport", "source": "internal"})
		return "", false, err.Error()
	}
	defer resp.Body.Close()
	out, truncated, readErr := readWebshellBody(resp.Body)
	if readErr != nil {
		h.logger.Warn("webshell ExecWithConnection read body", zap.Error(readErr))
	}
	if truncated {
		h.logger.Warn("webshell ExecWithConnection response truncated", zap.Int("limit_bytes", maxWebshellResponseBytes))
	}
	ok = resp.StatusCode == http.StatusOK
	auditResult := "failure"
	if ok && readErr == nil {
		auditResult = "success"
	}
	h.recordOperationAudit(nil, "command_execute", auditResult, conn.ID, conn.URL, command, map[string]interface{}{"source": "internal", "http_code": resp.StatusCode, "response_bytes": len(out)})
	decoded := decodeWebshellOutput(out, conn.Encoding)
	if truncated {
		decoded += fmt.Sprintf("\n[响应超过 %d 字节，已截断]", maxWebshellResponseBytes)
	}
	return decoded, ok, ""
}

// FileOpWithConnection 在指定 WebShell 连接上执行文件操作（供 MCP/Agent 调用），支持 list / read / write
func (h *WebShellHandler) FileOpWithConnection(conn *database.WebShellConnection, action, path, content, targetPath string) (output string, ok bool, errMsg string) {
	if conn == nil {
		return "", false, "connection is nil"
	}
	action = strings.ToLower(strings.TrimSpace(action))
	// MCP 入口仅开放 list / read / write 三种动作，与工具文档的承诺保持一致
	switch action {
	case "list", "read", "write":
		// 支持的动作
	default:
		h.recordOperationAudit(nil, "file_operation", "failure", conn.ID, conn.URL, path, map[string]interface{}{"operation": action, "stage": "validation", "source": "internal"})
		return "", false, "unsupported action: " + action + " (supported: list, read, write)"
	}

	// 若连接的 OS 为 auto，先探活并持久化，避免 AI/MCP 每次都对 Windows 发 `ls -la`
	osTag := conn.OS
	if normalizeWebshellOS(osTag) == "auto" {
		if probed := probeWebshellOSViaExec(func(cmd string) (string, bool) {
			out, exOk, _ := h.ExecWithConnection(conn, cmd)
			return out, exOk
		}); probed != "" {
			osTag = probed
			conn.OS = probed // 本次请求内使用探活结果
			h.persistDetectedOS(conn.ID, probed)
		}
	}

	command, cmdErr := h.buildFileCommand(fileCommandInput{
		Action:     action,
		Path:       path,
		TargetPath: targetPath,
		Content:    content,
		OS:         osTag,
		ShellType:  conn.Type,
	})
	if cmdErr != nil {
		h.recordOperationAudit(nil, "file_operation", "failure", conn.ID, conn.URL, path, map[string]interface{}{"operation": action, "stage": "validation", "source": "internal"})
		return "", false, cmdErr.Error()
	}
	useGET := strings.ToUpper(strings.TrimSpace(conn.Method)) == "GET"
	cmdParam := strings.TrimSpace(conn.CmdParam)
	if cmdParam == "" {
		cmdParam = "cmd"
	}
	var httpReq *http.Request
	var err error
	if useGET {
		targetURL := h.buildExecURL(conn.URL, conn.Type, conn.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodGet, targetURL, nil)
	} else {
		body := h.buildExecBody(conn.Type, conn.Password, cmdParam, command)
		httpReq, err = http.NewRequest(http.MethodPost, conn.URL, bytes.NewReader(body))
		httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	if err != nil {
		h.recordOperationAudit(nil, "file_operation", "failure", conn.ID, conn.URL, path, map[string]interface{}{"operation": action, "stage": "build_request", "source": "internal"})
		return "", false, err.Error()
	}
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (compatible; JySecAI-WebShell/1.0)")
	resp, err := h.client.Do(httpReq)
	if err != nil {
		h.recordOperationAudit(nil, "file_operation", "failure", conn.ID, conn.URL, path, map[string]interface{}{"operation": action, "stage": "transport", "source": "internal"})
		return "", false, err.Error()
	}
	defer resp.Body.Close()
	out, truncated, readErr := readWebshellBody(resp.Body)
	if readErr != nil {
		h.logger.Warn("webshell FileOpWithConnection read body", zap.Error(readErr))
	}
	if truncated {
		h.logger.Warn("webshell FileOpWithConnection response truncated", zap.Int("limit_bytes", maxWebshellResponseBytes))
	}
	ok = resp.StatusCode == http.StatusOK
	auditResult := "failure"
	if ok && readErr == nil {
		auditResult = "success"
	}
	h.recordOperationAudit(nil, "file_operation", auditResult, conn.ID, conn.URL, path, map[string]interface{}{
		"operation": action, "source": "internal", "http_code": resp.StatusCode, "response_bytes": len(out), "content_bytes": len(content),
	})
	decoded := decodeWebshellOutput(out, conn.Encoding)
	if truncated {
		decoded += fmt.Sprintf("\n[响应超过 %d 字节，已截断]", maxWebshellResponseBytes)
	}
	return decoded, ok, ""
}
