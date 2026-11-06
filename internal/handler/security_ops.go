package handler

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"
	"jysecai/internal/xalgorix"
)

const xalgorixEngineID = "xalgorix"

// SecurityOpsHandler 把「Web 安全掃描」頁接到操作者自己的 Xalgorix。
// 任務先落在本機，批准後才呼叫外部 API。這裡不組裝利用載荷。
type SecurityOpsHandler struct {
	db        *database.DB
	config    *config.Config
	logger    *zap.Logger
	now       func() time.Time
	newClient func(baseURL, token string) (*xalgorix.Client, error)
}

func NewSecurityOpsHandler(db *database.DB, cfg *config.Config, logger *zap.Logger) *SecurityOpsHandler {
	if logger == nil {
		logger = zap.NewNop()
	}
	return &SecurityOpsHandler{
		db:        db,
		config:    cfg,
		logger:    logger,
		now:       func() time.Time { return time.Now().UTC() },
		newClient: xalgorix.NewClient,
	}
}

type securityOpsAuthorization struct {
	ID             string    `json:"id"`
	ProjectID      string    `json:"projectId"`
	TargetPatterns []string  `json:"targetPatterns"`
	Operations     []string  `json:"operations"`
	ValidFrom      time.Time `json:"validFrom"`
	ValidUntil     time.Time `json:"validUntil"`
	ApprovedBy     string    `json:"approvedBy"`
	Attested       bool      `json:"attested"`
	// SourceRunID 是這筆授權事實的來源記錄：人工確認授權的那一次掃描任務。
	//
	// 授權繼承（見 inheritAuthorization）會把既有授權沿用到同一專案的新任務上，
	// 這三個欄位讓「這筆授權是誰在什麼時候確認的、從哪裡繼承來的」在稽核時查得到。
	// 沒有它們，繼承來的授權看起來會跟人工逐筆填寫的一樣 —— 那就分不出證據強度了。
	SourceRunID string    `json:"sourceRunId,omitempty"`
	Inherited   bool      `json:"inherited,omitempty"`
	InheritedAt time.Time `json:"inheritedAt,omitempty"`
}

type securityOpsCreateRequest struct {
	ProjectID      string                   `json:"projectId"`
	Engine         string                   `json:"engine"`
	Profile        string                   `json:"profile"`
	Targets        []string                 `json:"targets"`
	Objective      string                   `json:"objective"`
	Authorization  securityOpsAuthorization `json:"authorization"`
	IdempotencyKey string                   `json:"idempotencyKey"`
}

func (h *SecurityOpsHandler) Catalog(c *gin.Context) {
	cfg := h.xalgorixConfig()
	engine := gin.H{
		"id":                  xalgorixEngineID,
		"name":                "Xalgorix",
		"description":         "外部 Xalgorix 扫描服务",
		"connector":           "http",
		"active":              false,
		"supportedOperations": []string{"passive_discovery", "active_scan", "exploit_validation"},
		"profiles":            []string{"audit", "standard", "verify"},
	}
	note := "尚未启用 Xalgorix。请在配置里设置 xalgorix.enabled、base_url 和 api_token。"
	connected := false
	if cfg.Enabled && strings.TrimSpace(cfg.BaseURL) != "" && strings.TrimSpace(cfg.APIToken) != "" {
		client, err := h.newClient(cfg.BaseURL, cfg.APIToken)
		if err != nil {
			note = "Xalgorix 地址无效，引擎未启用。"
		} else {
			ctx, cancel := contextWithTimeout(c, 4*time.Second)
			defer cancel()
			if _, err := client.Status(ctx); err != nil {
				note = "Xalgorix 暂时连不上，引擎未启用。"
				h.logger.Warn("xalgorix status", zap.Error(err))
			} else {
				engine["active"] = true
				engine["description"] = "已连接的 Xalgorix。扫描在批准后才会送出。"
				note = ""
				connected = true
			}
		}
	}
	c.JSON(http.StatusOK, gin.H{"engines": []gin.H{engine}, "connected": connected, "note": note})
}

func (h *SecurityOpsHandler) ListRuns(c *gin.Context) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return
	}
	all := session.Scope == database.RBACScopeAll
	runs, err := h.db.ListSecurityOpsRuns(session.UserID, c.Query("projectId"), all, queryLimit(c, 50))
	if err != nil {
		h.logger.Warn("list security ops runs", zap.Error(err))
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取扫描任务")
		return
	}
	items := make([]gin.H, 0, len(runs))
	for i := range runs {
		h.refreshRemote(&runs[i])
		items = append(items, securityOpsRunJSON(&runs[i]))
	}
	c.JSON(http.StatusOK, gin.H{"items": items})
}

func (h *SecurityOpsHandler) CreateRun(c *gin.Context) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return
	}
	var req securityOpsCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		writeSecurityOpsError(c, http.StatusBadRequest, "invalid_body", "请求格式不正确")
		return
	}
	if existing, err := h.db.FindSecurityOpsRunByIdempotency(req.IdempotencyKey, session.UserID); err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "lookup_failed", "无法检查重复任务")
		return
	} else if existing != nil {
		c.JSON(http.StatusOK, gin.H{"run": securityOpsRunJSON(existing)})
		return
	}
	// 授权继承：请求没带完整授权事实时，沿用同一专案既有「人工确认过」的那笔授权，
	// 免得每开一个扫描任务都要把授权编号、授权人与授权期间重打一遍。
	// 沿用的来源一定会被记进 authorization.sourceRunId，稽核时查得到是谁确认的。
	if inherited, ok := h.inheritAuthorization(req); ok {
		req.Authorization = mergeSecurityOpsAuthorization(req.Authorization, inherited)
	}
	if err := validateSecurityOpsCreate(req, h.now()); err != nil {
		writeSecurityOpsError(c, http.StatusBadRequest, "invalid_authorization", err.Error())
		return
	}
	targetsJSON, _ := json.Marshal(trimLines(req.Targets))
	patternsJSON, _ := json.Marshal(trimLines(req.Authorization.TargetPatterns))
	authJSON, _ := json.Marshal(req.Authorization)
	run := &database.SecurityOpsRun{
		ID:                newSecurityOpsID(),
		IdempotencyKey:    strings.TrimSpace(req.IdempotencyKey),
		ProjectID:         strings.TrimSpace(req.ProjectID),
		OwnerID:           session.UserID,
		Engine:            xalgorixEngineID,
		Profile:           strings.TrimSpace(req.Profile),
		Operation:         req.Authorization.Operations[0],
		Objective:         strings.TrimSpace(req.Objective),
		TargetsJSON:       string(targetsJSON),
		PatternsJSON:      string(patternsJSON),
		AuthorizationJSON: string(authJSON),
		Status:            "awaiting_approval",
		StatusReason:      "等待具有审批权限的人员批准后才会送往 Xalgorix",
	}
	if err := h.db.InsertSecurityOpsRun(run); err != nil {
		h.logger.Warn("insert security ops run", zap.Error(err))
		writeSecurityOpsError(c, http.StatusInternalServerError, "create_failed", "无法保存扫描任务")
		return
	}
	c.JSON(http.StatusCreated, gin.H{"run": securityOpsRunJSON(run)})
}

func (h *SecurityOpsHandler) ApproveRun(c *gin.Context) {
	run, ok := h.ownedRun(c)
	if !ok {
		return
	}
	if run.Status != "awaiting_approval" {
		writeSecurityOpsError(c, http.StatusConflict, "not_awaiting_approval", "这个任务现在不能批准")
		return
	}
	var auth securityOpsAuthorization
	if err := json.Unmarshal([]byte(run.AuthorizationJSON), &auth); err != nil || !authorizationCurrent(auth, h.now()) {
		run.Status = "failed"
		run.StatusReason = "授权已过期或无效，未送出扫描"
		_ = h.db.UpdateSecurityOpsRun(run)
		writeSecurityOpsError(c, http.StatusConflict, "authorization_expired", run.StatusReason)
		return
	}
	client, err := h.client()
	if err != nil {
		writeSecurityOpsError(c, http.StatusServiceUnavailable, "xalgorix_unavailable", err.Error())
		return
	}
	targets := decodeStringList(run.TargetsJSON)
	ctx, cancel := contextWithTimeout(c, 20*time.Second)
	defer cancel()
	scanBody := map[string]any{
		"name":        run.ProjectID,
		"targets":     targets,
		"instruction": run.Objective,
		"scan_mode":   scanModeForTargets(targets),
	}
	if phases := phasesForOperation(run.Operation); len(phases) > 0 {
		scanBody["phases"] = phases
	}
	remote, err := client.StartScan(ctx, scanBody)
	if err != nil {
		run.Status = "failed"
		run.StatusReason = "Xalgorix 没有接受这个任务"
		_ = h.db.UpdateSecurityOpsRun(run)
		h.logger.Warn("xalgorix start", zap.Error(err))
		writeSecurityOpsError(c, http.StatusBadGateway, "xalgorix_rejected", run.StatusReason)
		return
	}
	run.RemoteID = firstString(remote, "instance_id", "id")
	run.Status = "running"
	run.StatusReason = "已交给 Xalgorix"
	if err := h.db.UpdateSecurityOpsRun(run); err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "update_failed", "任务已送出，但本地状态没有写入")
		return
	}
	c.JSON(http.StatusOK, gin.H{"run": securityOpsRunJSON(run)})
}

func (h *SecurityOpsHandler) CancelRun(c *gin.Context) {
	run, ok := h.ownedRun(c)
	if !ok {
		return
	}
	if isTerminalSecurityOps(run.Status) {
		writeSecurityOpsError(c, http.StatusConflict, "already_finished", "这个任务已经结束")
		return
	}
	if run.RemoteID != "" {
		if client, err := h.client(); err == nil {
			ctx, cancel := contextWithTimeout(c, 8*time.Second)
			defer cancel()
			if err := client.StopInstance(ctx, run.RemoteID); err != nil {
				h.logger.Warn("xalgorix stop", zap.Error(err))
			}
		}
	}
	run.Status = "cancelled"
	run.StatusReason = "已取消"
	if err := h.db.UpdateSecurityOpsRun(run); err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "update_failed", "无法取消任务")
		return
	}
	c.JSON(http.StatusOK, gin.H{"run": securityOpsRunJSON(run)})
}

func (h *SecurityOpsHandler) ListEvents(c *gin.Context) {
	run, ok := h.ownedRun(c)
	if !ok {
		return
	}
	events := []gin.H{}
	if run.RemoteID != "" {
		if client, err := h.client(); err == nil {
			ctx, cancel := contextWithTimeout(c, 8*time.Second)
			defer cancel()
			if payload, err := client.Events(ctx, run.RemoteID); err == nil {
				events = mapXalgorixEvents(payload)
			}
		}
	}
	c.JSON(http.StatusOK, gin.H{"events": events})
}

func (h *SecurityOpsHandler) ListArtifacts(c *gin.Context) {
	run, ok := h.ownedRun(c)
	if !ok {
		return
	}
	artifacts := []gin.H{{
		"kind":         "pentest_report",
		"objectKey":    "pentest-report.html",
		"sizeBytes":    0,
		"createdAt":    run.UpdatedAt,
		"downloadPath": "/api/projects/" + url.PathEscape(run.ProjectID) + "/pentest-report?runId=" + url.QueryEscape(run.ID),
	}}
	if run.RemoteID != "" && (run.Status == "completed" || run.Status == "running") {
		artifacts = append(artifacts, gin.H{
			"kind":         "report",
			"objectKey":    "report.pdf",
			"sizeBytes":    0,
			"createdAt":    run.UpdatedAt,
			"downloadPath": "/api/security-ops/runs/" + url.PathEscape(run.ID) + "/report",
		})
	}
	c.JSON(http.StatusOK, gin.H{"artifacts": artifacts})
}

func (h *SecurityOpsHandler) DownloadReport(c *gin.Context) {
	run, ok := h.ownedRun(c)
	if !ok {
		return
	}
	if run.RemoteID == "" {
		writeSecurityOpsError(c, http.StatusConflict, "report_not_ready", "扫描还没有送到 Xalgorix，没有报告")
		return
	}
	client, err := h.client()
	if err != nil {
		writeSecurityOpsError(c, http.StatusServiceUnavailable, "xalgorix_unavailable", err.Error())
		return
	}
	ctx, cancel := contextWithTimeout(c, 20*time.Second)
	defer cancel()
	body, contentType, err := client.Report(ctx, run.RemoteID)
	if err != nil {
		writeSecurityOpsError(c, http.StatusBadGateway, "report_failed", "无法从 Xalgorix 取得报告")
		return
	}
	c.Header("Content-Disposition", `attachment; filename="xalgorix-report.pdf"`)
	c.Data(http.StatusOK, contentType, body)
}

func (h *SecurityOpsHandler) ListFindings(c *gin.Context) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return
	}
	projectID := strings.TrimSpace(c.Param("projectId"))
	all := session.Scope == database.RBACScopeAll
	runs, err := h.db.ListSecurityOpsRuns(session.UserID, projectID, all, 200)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取项目任务")
		return
	}
	hosts := map[string]struct{}{}
	for i := range runs {
		if runs[i].ProjectID != projectID {
			continue
		}
		for _, target := range decodeStringList(runs[i].TargetsJSON) {
			if host := targetHost(target); host != "" {
				hosts[strings.ToLower(host)] = struct{}{}
			}
		}
	}
	findings := []gin.H{}
	if len(hosts) > 0 {
		if client, err := h.client(); err == nil {
			ctx, cancel := contextWithTimeout(c, 8*time.Second)
			defer cancel()
			if payload, err := client.Findings(ctx); err == nil {
				findings = filterFindings(payload, hosts)
			}
		}
	}
	stored := 0
	for i := range runs {
		if runs[i].Status == "completed" {
			stored += h.storeRunFindings(&runs[i])
		}
	}
	c.JSON(http.StatusOK, gin.H{"findings": findings, "stored": stored})
}

func (h *SecurityOpsHandler) ownedRun(c *gin.Context) (*database.SecurityOpsRun, bool) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return nil, false
	}
	run, err := h.db.GetSecurityOpsRun(c.Param("id"))
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "lookup_failed", "无法读取任务")
		return nil, false
	}
	if run == nil || (session.Scope != database.RBACScopeAll && run.OwnerID != session.UserID) {
		writeSecurityOpsError(c, http.StatusNotFound, "not_found", "找不到这个任务")
		return nil, false
	}
	return run, true
}

func (h *SecurityOpsHandler) refreshRemote(run *database.SecurityOpsRun) {
	if run == nil || run.RemoteID == "" || isTerminalSecurityOps(run.Status) {
		return
	}
	client, err := h.client()
	if err != nil {
		return
	}
	ctx, cancel := contextWithTimeout(nil, 4*time.Second)
	defer cancel()
	remote, err := client.Instance(ctx, run.RemoteID)
	if err != nil {
		return
	}
	if status := mapRemoteStatus(firstString(remote, "status")); status != "" {
		run.Status = status
	}
	run.CurrentPhase = firstInt(remote, "current_phase")
	run.VulnCount = firstInt(remote, "vuln_count")
	if run.Status == "running" && run.CurrentPhase > 0 {
		run.StatusReason = "Xalgorix 执行中"
	}
	_ = h.db.UpdateSecurityOpsRun(run)
	if run.Status == "completed" {
		stored := h.storeRunFindings(run)
		// #region agent log
		securityOpsIngestDebug("E", "security_ops.go:refreshRemote", "completed run ingested", map[string]any{"stored": stored, "status": run.Status})
		// #endregion
	}
}

func (h *SecurityOpsHandler) storeRunFindings(run *database.SecurityOpsRun) int {
	if h == nil || h.db == nil || run == nil || run.RemoteID == "" || run.Status != "completed" {
		return 0
	}
	client, err := h.client()
	if err != nil {
		return 0
	}
	ctx, cancel := contextWithTimeout(nil, 8*time.Second)
	defer cancel()
	payload, err := client.Findings(ctx)
	if err != nil {
		return 0
	}
	hosts := map[string]struct{}{}
	for _, target := range decodeStringList(run.TargetsJSON) {
		if host := targetHost(target); host != "" {
			hosts[strings.ToLower(host)] = struct{}{}
		}
	}
	if len(hosts) == 0 {
		return 0
	}
	stored := 0
	for _, finding := range filterFindings(payload, hosts) {
		title := strings.TrimSpace(fmt.Sprint(finding["title"]))
		target := strings.TrimSpace(fmt.Sprint(finding["description"]))
		if title == "" || target == "" || title == "<nil>" || target == "<nil>" {
			continue
		}
		severity := strings.ToLower(strings.TrimSpace(fmt.Sprint(finding["severity"])))
		switch severity {
		case "critical", "high", "medium", "low", "info":
		default:
			severity = "info"
		}
		created, err := h.db.CreateVulnerability(&database.Vulnerability{
			ProjectID:   run.ProjectID,
			Title:       title,
			Type:        "scan-finding",
			Target:      target,
			Severity:    severity,
			Status:      database.VulnerabilityStatusOpen,
			Confidence:  40,
			Description: "由已授权扫描自动入库，等待复测",
			Evidence:    "scan:" + run.ID,
		})
		if err != nil || created == nil || created.Deduplicated {
			continue
		}
		_ = h.db.SetResourceOwner("vulnerability", created.ID, run.OwnerID)
		_ = h.db.AssignResourceToUser(run.OwnerID, "vulnerability", created.ID)
		stored++
	}
	if stored > 0 {
		run.StatusReason = fmt.Sprintf("已自动入库 %d 条", stored)
		_ = h.db.UpdateSecurityOpsRun(run)
	}
	return stored
}

func securityOpsIngestDebug(hypothesis, location, message string, data map[string]any) {
	// #region agent log
	payload := map[string]any{"sessionId": "ed2056", "runId": "ingest", "hypothesisId": hypothesis, "location": location, "message": message, "data": data, "timestamp": time.Now().UnixMilli()}
	encoded, err := json.Marshal(payload)
	if err != nil {
		return
	}
	file, err := os.OpenFile("/mnt/c/Users/Administrator/desktop/JySecAI/.cursor/debug-ed2056.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer file.Close()
	_, _ = file.Write(append(encoded, '\n'))
	// #endregion
}

func (h *SecurityOpsHandler) client() (*xalgorix.Client, error) {
	cfg := h.xalgorixConfig()
	if !cfg.Enabled || strings.TrimSpace(cfg.BaseURL) == "" || strings.TrimSpace(cfg.APIToken) == "" {
		return nil, errors.New("Xalgorix 尚未配置")
	}
	return h.newClient(cfg.BaseURL, cfg.APIToken)
}

func (h *SecurityOpsHandler) xalgorixConfig() config.XalgorixConfig {
	if h.config == nil {
		return config.XalgorixConfig{}
	}
	return h.config.Xalgorix
}

func validateSecurityOpsCreate(req securityOpsCreateRequest, now time.Time) error {
	if strings.TrimSpace(req.Engine) != xalgorixEngineID {
		return errors.New("目前只接受 Xalgorix 引擎")
	}
	switch strings.TrimSpace(req.Profile) {
	case "audit", "standard", "verify":
	default:
		return errors.New("执行深度不正确")
	}
	if strings.TrimSpace(req.ProjectID) == "" || len(strings.TrimSpace(req.ProjectID)) > 160 {
		return errors.New("项目 ID 不正确")
	}
	objective := strings.TrimSpace(req.Objective)
	if len([]rune(objective)) < 3 || len([]rune(objective)) > 12000 {
		return errors.New("任务目标长度不正确")
	}
	targets := trimLines(req.Targets)
	if len(targets) == 0 || len(targets) > 50 {
		return errors.New("至少要有一个目标，且一次不超过 50 个")
	}
	auth := req.Authorization
	if !auth.Attested || len(strings.TrimSpace(auth.ApprovedBy)) == 0 || len(strings.TrimSpace(auth.ID)) < 8 {
		return errors.New("需要授权编号、授权人，以及已勾选的授权确认")
	}
	if auth.ProjectID != "" && auth.ProjectID != strings.TrimSpace(req.ProjectID) {
		return errors.New("授权书上的项目和任务项目不一致")
	}
	if len(auth.Operations) != 1 {
		return errors.New("一次任务只能选择一种扫描模式")
	}
	switch auth.Operations[0] {
	case "passive_discovery", "active_scan", "exploit_validation":
	default:
		return errors.New("扫描模式不正确")
	}
	if !authorizationCurrent(auth, now) {
		return errors.New("授权不在有效时间内，或超过 90 天")
	}
	patterns := trimLines(auth.TargetPatterns)
	if len(patterns) == 0 {
		return errors.New("授权范围不能是空的")
	}
	for _, target := range targets {
		if !targetInScope(target, patterns) {
			return errors.New("有目标不在授权范围内")
		}
	}
	return nil
}

func authorizationCurrent(auth securityOpsAuthorization, now time.Time) bool {
	if auth.ValidFrom.IsZero() || auth.ValidUntil.IsZero() || !auth.ValidUntil.After(auth.ValidFrom) {
		return false
	}
	if auth.ValidUntil.Sub(auth.ValidFrom) > 90*24*time.Hour {
		return false
	}
	return !now.Before(auth.ValidFrom) && !now.After(auth.ValidUntil)
}

func targetInScope(target string, patterns []string) bool {
	host := targetHost(target)
	if host == "" {
		return false
	}
	ip := net.ParseIP(host)
	for _, pattern := range patterns {
		pattern = strings.TrimSpace(pattern)
		lower := strings.ToLower(pattern)
		if strings.Contains(pattern, "/") {
			_, network, err := net.ParseCIDR(pattern)
			if err == nil && ip != nil && network.Contains(ip) {
				return true
			}
			continue
		}
		if strings.HasPrefix(lower, "*.") {
			suffix := strings.TrimPrefix(lower, "*.")
			hostLower := strings.ToLower(host)
			if suffix != "" && hostLower != suffix && strings.HasSuffix(hostLower, "."+suffix) {
				return true
			}
			continue
		}
		if strings.EqualFold(host, pattern) {
			return true
		}
	}
	return false
}

func targetHost(target string) string {
	raw := strings.TrimSpace(target)
	if raw == "" {
		return ""
	}
	if strings.Contains(raw, "://") {
		parsed, err := url.Parse(raw)
		if err != nil {
			return ""
		}
		return parsed.Hostname()
	}
	if strings.Contains(raw, "/") && net.ParseIP(raw) == nil {
		parsed, err := url.Parse("http://" + raw)
		if err != nil {
			return ""
		}
		return parsed.Hostname()
	}
	host, _, err := net.SplitHostPort(raw)
	if err == nil {
		return host
	}
	return strings.Trim(raw, "[]")
}

func phasesForOperation(operation string) []int {
	switch operation {
	case "passive_discovery":
		return []int{1}
	case "exploit_validation":
		return []int{20}
	default:
		return nil
	}
}

func scanModeForTargets(targets []string) string {
	for _, target := range targets {
		if strings.Contains(target, "*") {
			return "wildcard"
		}
	}
	if len(targets) > 1 {
		return "wildcard"
	}
	return "single"
}

func mapRemoteStatus(status string) string {
	switch strings.ToLower(strings.TrimSpace(status)) {
	case "running", "paused":
		return "running"
	case "finished", "completed", "stopped":
		return "completed"
	case "failed", "error":
		return "failed"
	case "saved":
		return "queued"
	default:
		return ""
	}
}

func isTerminalSecurityOps(status string) bool {
	switch status {
	case "completed", "failed", "cancelled":
		return true
	default:
		return false
	}
}

func securityOpsRunJSON(run *database.SecurityOpsRun) gin.H {
	// 授權記錄一併回傳：操作者要能看到這筆任務用的是哪一份授權、是人工填的還是沿用來的。
	// 少了這個欄位，「沿用」在介面上就看不出來 —— 只會看到一個不知來源的授權編號。
	var auth securityOpsAuthorization
	_ = json.Unmarshal([]byte(run.AuthorizationJSON), &auth)
	return gin.H{
		"id":            run.ID,
		"projectId":     run.ProjectID,
		"operation":     run.Operation,
		"objective":     run.Objective,
		"status":        run.Status,
		"engine":        run.Engine,
		"profile":       run.Profile,
		"targets":       decodeStringList(run.TargetsJSON),
		"createdAt":     run.CreatedAt,
		"statusReason":  run.StatusReason,
		"currentPhase":  run.CurrentPhase,
		"vulnCount":     run.VulnCount,
		"authorization": auth,
	}
}

func mapXalgorixEvents(payload any) []gin.H {
	items, ok := payload.([]any)
	if !ok {
		return []gin.H{}
	}
	out := make([]gin.H, 0, len(items))
	for i, item := range items {
		object, ok := item.(map[string]any)
		if !ok {
			continue
		}
		out = append(out, gin.H{
			"sequence": i + 1,
			"type":     firstString(object, "type", "tool_name"),
			"at":       firstString(object, "timestamp", "at"),
			"data": gin.H{
				"content": firstString(object, "content"),
				"phase":   firstInt(object, "current_phase"),
			},
		})
	}
	return out
}

func filterFindings(payload any, hosts map[string]struct{}) []gin.H {
	items, ok := payload.([]any)
	if !ok {
		if object, ok := payload.(map[string]any); ok {
			items, _ = object["findings"].([]any)
		}
	}
	out := make([]gin.H, 0)
	for _, item := range items {
		object, ok := item.(map[string]any)
		if !ok {
			continue
		}
		host := strings.ToLower(targetHost(firstString(object, "endpoint", "scan_target", "target")))
		if _, allowed := hosts[host]; !allowed {
			continue
		}
		confidence := 0.5
		if verified, ok := object["verified"].(bool); ok && verified {
			confidence = 1
		}
		out = append(out, gin.H{
			"severity":    strings.ToLower(firstString(object, "severity")),
			"title":       firstString(object, "title"),
			"description": firstString(object, "endpoint", "scan_target"),
			"status":      "open",
			"confidence":  confidence,
		})
	}
	return out
}

func decodeStringList(raw string) []string {
	var items []string
	if err := json.Unmarshal([]byte(raw), &items); err != nil {
		return nil
	}
	return items
}

func trimLines(items []string) []string {
	out := make([]string, 0, len(items))
	seen := map[string]struct{}{}
	for _, item := range items {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		if _, ok := seen[item]; ok {
			continue
		}
		seen[item] = struct{}{}
		out = append(out, item)
	}
	return out
}

func firstString(object map[string]any, keys ...string) string {
	for _, key := range keys {
		switch value := object[key].(type) {
		case string:
			if strings.TrimSpace(value) != "" {
				return value
			}
		}
	}
	return ""
}

func firstInt(object map[string]any, keys ...string) int {
	for _, key := range keys {
		switch value := object[key].(type) {
		case float64:
			return int(value)
		case int:
			return value
		}
	}
	return 0
}

func queryLimit(c *gin.Context, fallback int) int {
	return fallback
}

func writeSecurityOpsError(c *gin.Context, status int, code, message string) {
	c.JSON(status, gin.H{"error": code, "message": message})
}

func contextWithTimeout(c *gin.Context, timeout time.Duration) (context.Context, context.CancelFunc) {
	parent := context.Background()
	if c != nil && c.Request != nil && c.Request.Context() != nil {
		parent = c.Request.Context()
	}
	return context.WithTimeout(parent, timeout)
}

func newSecurityOpsID() string {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return hex.EncodeToString([]byte(time.Now().UTC().Format(time.RFC3339Nano)))
	}
	return hex.EncodeToString(raw[:])
}
