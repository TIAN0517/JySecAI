// verify-drain 把自動複測的待處理佇列一次排空。
//
// 排程版（StartAutoVerify）每 30 分鐘跑 5 筆，幾百筆積壓要跑一個多月；這個工具
// 一次把整批派完。派工路徑與排程版完全相同——走執行中伺服器的 HTTP API，因此
// 用的是同一套真實堆疊：同一份 BuildAutoVerifyPrompt、同一組 RBAC / HITL /
// Tool Guard / 稽核、同樣的 update_vulnerability 確認閘門。這裡不開任何特權通道。
//
// 為什麼是 HTTP 客戶端而不是另一個行程直接呼叫 handler：
// registerVulnerabilityTools 在 internal/app 裡未導出，獨立行程註冊不出
// update_vulnerability / get_vulnerability——而這兩個工具正是複測提示詞的硬性
// 要求。走 HTTP 也意味著這支工具自己動不了資料：它能做的跟人在 UI 上點的一樣，
// 出了事稽核紀錄一樣查得到。
//
// 用法：
//
//	go run ./cmd/verify-drain --config config.yaml --dry-run
//	go run ./cmd/verify-drain --config config.yaml            # 密碼走 JYSECAI_PASSWORD
//	go run ./cmd/verify-drain --token "$TOKEN" --status open
package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/handler"

	"go.uber.org/zap"
)

// queuePollInterval 輪詢佇列狀態的間隔。佇列子任務是獨立對話、實際執行以分鐘計，
// 這裡只是探詢節奏，太密只是白打 API。
const queuePollInterval = 15 * time.Second

// stallLimit 連續幾輪「agent 一筆都沒寫回」就停手。
//
// 複測失敗最典型的後果是工具不可用或通道不對——提示詞已經要求這種情況收在
// undetermined，於是資料看起來沒動，naive 的迴圈會對同一批 id 無限重派。
const stallLimit = 2

// errorLimit 連續幾輪失敗就中止。偶發逾時靠重試吸收，連續失敗代表設定或上游壞了。
const errorLimit = 3

// queueTimeout 單一佇列的預設等待上限。子任務本身有 6 小時逾時
// （executeOneBatchSubTask），這裡留一樣的量級，避免外層先放棄、內層還在跑。
const queueTimeout = 6 * time.Hour

// queueTerminalStatuses 佇列到達這些狀態就不再推進。paused 也在內：單次執行佇列
// 跑完會落到 paused（見 executeOneBatchSubTask 的 TakeSingleRunTaskIfMatch）。
var queueTerminalStatuses = map[string]bool{
	handler.BatchQueueStatusCompleted: true,
	handler.BatchQueueStatusCancelled: true,
	handler.BatchQueueStatusPaused:    true,
}

type apiClient struct {
	baseURL  string
	token    string
	username string
	scope    string
	http     *http.Client
}

// sessionResponse 同時對應 /api/auth/login 與 /api/auth/validate，兩者欄位一致。
type sessionResponse struct {
	Token string `json:"token"`
	User  struct {
		ID       string `json:"id"`
		Username string `json:"username"`
	} `json:"user"`
	Scope string `json:"scope"`
}

type createQueueResponse struct {
	QueueID string `json:"queueId"`
	Started bool   `json:"started"`
	Err     string `json:"error"`
}

type getQueueResponse struct {
	Queue *handler.BatchTaskQueue `json:"queue"`
	Err   string                  `json:"error"`
}

type listVulnsResponse struct {
	Vulnerabilities []*database.Vulnerability `json:"vulnerabilities"`
	Total           int                       `json:"total"`
}

func main() {
	configPath := flag.String("config", "config.yaml", "設定檔路徑")
	baseURL := flag.String("base-url", "", "伺服器位址（留空則依設定檔的 host/port/tls_enabled 推導）")
	username := flag.String("username", "", "登入帳號（留空則用 auto_verify.actor_user_id）")
	password := flag.String("password", "", "登入密碼（也可用環境變數 JYSECAI_PASSWORD）")
	token := flag.String("token", "", "直接帶入 Bearer token，略過登入")
	status := flag.String("status", database.VulnerabilityStatusUndetermined, "要排空哪一種狀態（open / undetermined）")
	batch := flag.Int("batch", 0, "每輪派幾筆（0 = 用設定檔 auto_verify.batch）")
	maxRounds := flag.Int("max-rounds", 200, "安全上限：最多跑幾輪")
	pause := flag.Duration("pause", 5*time.Second, "每輪之間的停頓")
	poll := flag.Duration("poll", queuePollInterval, "輪詢佇列狀態的間隔")
	wait := flag.Duration("queue-timeout", queueTimeout, "單一佇列的等待上限")
	project := flag.String("project", "", "只排空指定專案的漏洞（留空 = 全部）")
	concurrency := flag.Int("concurrency", 1, "佇列內同時執行的子任務數")
	channel := flag.String("channel", "", "AI 通道（留空 = 用設定檔 auto_verify.ai_channel）")
	excludeSev := flag.String("exclude-severities", "", "不複測的嚴重度，逗號分隔（留空 = 用設定檔）")
	noEvidenceFilter := flag.Bool("no-evidence-filter", false, "關閉「無 target/無證據就跳過」的篩選（會把佔位殘留紀錄也送去複測）")
	reportSkipped := flag.Int("report-skipped", 10, "列出前幾筆被篩掉的紀錄，方便人工確認篩選是否合理")
	dryRun := flag.Bool("dry-run", false, "只列出會派工的漏洞，不建立佇列")
	insecure := flag.Bool("insecure", false, "放行自簽憑證（僅限本機回環位址）")
	flag.Parse()

	logger, _ := zap.NewProduction()
	defer func() { _ = logger.Sync() }()
	sugar := logger.Sugar()

	cfg, err := config.Load(*configPath)
	if err != nil {
		sugar.Fatalf("讀取設定檔失敗: %v", err)
	}
	// 與排程版同一組安全邊界：auto_verify 關閉時這個工具不該跑——它排的是管理員
	// 已經關掉的東西。順帶擋掉「actor 根本沒填」這個最常見的誤植。
	if !cfg.AutoVerify.Enabled {
		sugar.Fatalf("auto_verify.enabled 為 false；排空工具沿用同一組安全邊界，請先在設定檔啟用")
	}
	if strings.TrimSpace(*token) == "" && strings.TrimSpace(cfg.AutoVerify.ActorUserID) == "" {
		sugar.Fatalf("auto_verify.actor_user_id 未設定；請用 --username 指定要派工的帳號")
	}

	targetURL := strings.TrimSpace(*baseURL)
	if targetURL == "" {
		targetURL = deriveBaseURL(cfg)
	}
	client, err := newAPIClient(targetURL, *token, *insecure, sugar)
	if err != nil {
		sugar.Fatalf("建立 API 客戶端失敗: %v", err)
	}
	if err := authenticate(client, cfg, *username, *password, *token); err != nil {
		sugar.Fatalf("認證失敗: %v", err)
	}

	statusFilter := strings.TrimSpace(*status)
	if statusFilter != database.VulnerabilityStatusOpen && statusFilter != database.VulnerabilityStatusUndetermined {
		sugar.Fatalf("--status 只接受 open 或 undetermined，收到 %q", statusFilter)
	}

	batchN := *batch
	if batchN <= 0 {
		batchN = cfg.AutoVerify.Batch
	}
	if batchN <= 0 {
		batchN = 5
	}
	if batchN > 200 {
		batchN = 200
	}

	channelID := strings.TrimSpace(*channel)
	if channelID == "" {
		channelID = strings.TrimSpace(cfg.AutoVerify.AIChannelID)
	}
	if channelID == "" && !*dryRun {
		// 沒有通道就會落到 ai.default_channel。實測 flash 級通道撐不起工具協議，
		// 複測會整批收成「工具不可用」——寧可在這裡擋下來。
		sugar.Fatalf("沒有指定 AI 通道：auto_verify.ai_channel 為空，請用 --channel 指定（否則用預設通道，工具呼叫可能整批失敗）")
	}

	excluded := parseCSV(*excludeSev)
	if strings.TrimSpace(*excludeSev) == "" {
		excluded = cfg.AutoVerify.ExcludeSeverities
	}
	if len(excluded) == 0 {
		excluded = []string{"critical"}
	}

	opts := drainOptions{
		status:         statusFilter,
		project:        strings.TrimSpace(*project),
		batch:          batchN,
		channel:        channelID,
		excluded:       excluded,
		concurrency:    *concurrency,
		filterEvidence: !*noEvidenceFilter,
		maxRounds:      *maxRounds,
		pause:          *pause,
		poll:           *poll,
		queueWait:      *wait,
		dryRun:         *dryRun,
		reportSkipped:  *reportSkipped,
	}

	sugar.Infof("開始排空：status=%s batch=%d channel=%s 排除嚴重度=%v 專案=%s 使用者=%s",
		opts.status, opts.batch, opts.channel, opts.excluded, orAll(opts.project), client.username)
	if opts.dryRun {
		sugar.Infof("dry-run：只會列出會派工的漏洞，不建立任何佇列")
	}

	drain(client, opts, sugar)
}

func deriveBaseURL(cfg *config.Config) string {
	host := strings.TrimSpace(cfg.Server.Host)
	if host == "" || host == "0.0.0.0" || host == "::" {
		host = "127.0.0.1"
	}
	scheme := "http"
	if cfg.Server.TLSEnabled {
		scheme = "https"
	}
	return fmt.Sprintf("%s://%s", scheme, net.JoinHostPort(host, strconv.Itoa(cfg.Server.Port)))
}

// authenticate 走登入或沿用 token，兩條路都必須確認 scope=all。
//
// 這是工具端唯一能自己查的閘。伺服器端的 RBAC 也會擋（scope≠all 的 token 根本
// 看不到別人的漏洞），但那會表現成「筆數對不上」而不是明確拒絕——對一個會批量
// 改狀態的工具來說，明確拒絕比靜默少做一半好。
func authenticate(client *apiClient, cfg *config.Config, username, password, token string) error {
	if strings.TrimSpace(token) == "" {
		user := strings.TrimSpace(username)
		if user == "" {
			user = strings.TrimSpace(cfg.AutoVerify.ActorUserID)
		}
		pass := password
		if pass == "" {
			pass = os.Getenv("JYSECAI_PASSWORD")
		}
		if user == "" || pass == "" {
			return errors.New("需要 --username 與 --password（或環境變數 JYSECAI_PASSWORD），或直接用 --token")
		}
		var out sessionResponse
		if err := client.do(http.MethodPost, "/api/auth/login", map[string]string{
			"username": user, "password": pass,
		}, &out); err != nil {
			return err
		}
		if out.Token == "" {
			return errors.New("登入成功但沒有拿到 token")
		}
		client.token = out.Token
		client.username = out.User.Username
		client.scope = out.Scope
		return client.requireAllScope()
	}

	client.token = strings.TrimSpace(token)
	var out sessionResponse
	if err := client.do(http.MethodGet, "/api/auth/validate", nil, &out); err != nil {
		return err
	}
	client.username = out.User.Username
	client.scope = out.Scope
	return client.requireAllScope()
}

func (c *apiClient) requireAllScope() error {
	if c.scope != database.RBACScopeAll {
		return fmt.Errorf("帳號 %s 的可見範圍是 %q，不是 all；複測要寫回全部漏洞的狀態，範圍不足會讓寫回對不上", c.username, c.scope)
	}
	return nil
}

func newAPIClient(baseURL, token string, insecure bool, sugar *zap.SugaredLogger) (*apiClient, error) {
	u, err := url.Parse(baseURL)
	if err != nil || u.Scheme == "" || u.Host == "" {
		return nil, fmt.Errorf("base-url 必須是完整的 http(s):// 位址，收到 %q", baseURL)
	}
	transport := &http.Transport{}
	// 自簽憑證只在回環位址上允許關閉驗證。伺服器對外也開著同一個 port，非本機
	// 連線卻關掉驗證，等於把 token 與整條派工路徑交給中間人。
	if insecure {
		if !isLoopbackHost(u.Hostname()) {
			return nil, fmt.Errorf("--insecure 只允許用在回環位址（%s 不是）；遠端連線請改用有 CA 憑證的連線", u.Host)
		}
		sugar.Warnf("已停用 TLS 憑證驗證（僅限本機）：%s", baseURL)
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402 -- 僅回環位址，上一行已擋
	}
	return &apiClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		token:   strings.TrimSpace(token),
		http:    &http.Client{Transport: transport, Timeout: 60 * time.Second},
	}, nil
}

func isLoopbackHost(host string) bool {
	if host == "localhost" {
		return true
	}
	ip := net.ParseIP(host)
	return ip != nil && ip.IsLoopback()
}

func (c *apiClient) do(method, path string, body, out interface{}) error {
	var reader io.Reader
	if body != nil {
		raw, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reader = bytes.NewReader(raw)
	}
	req, err := http.NewRequest(method, c.baseURL+path, reader)
	if err != nil {
		return err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer func() { _ = resp.Body.Close() }()
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return err
	}
	switch {
	case resp.StatusCode == http.StatusUnauthorized:
		return errors.New("未授權（token 過期或密碼錯誤）")
	case resp.StatusCode == http.StatusForbidden:
		return fmt.Errorf("沒有權限（%s %s）：%s", method, path, snippet(raw))
	case resp.StatusCode < 200 || resp.StatusCode >= 300:
		return fmt.Errorf("%s %s 回傳 %d: %s", method, path, resp.StatusCode, snippet(raw))
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(raw, out)
}

// listVulnerabilities 逐頁拉完指定狀態的漏洞。單頁上限 100（伺服端硬上限）。
func (c *apiClient) listVulnerabilities(status, project string) ([]*database.Vulnerability, error) {
	const pageSize = 100
	all := make([]*database.Vulnerability, 0, pageSize)
	for offset := 0; ; offset += pageSize {
		q := url.Values{}
		q.Set("status", status)
		q.Set("limit", strconv.Itoa(pageSize))
		q.Set("offset", strconv.Itoa(offset))
		if project != "" {
			q.Set("project_id", project)
		}
		var out listVulnsResponse
		if err := c.do(http.MethodGet, "/api/vulnerabilities?"+q.Encode(), nil, &out); err != nil {
			return nil, err
		}
		all = append(all, out.Vulnerabilities...)
		if len(out.Vulnerabilities) < pageSize || len(all) >= out.Total {
			return all, nil
		}
	}
}

func (c *apiClient) createQueue(req map[string]interface{}) (string, error) {
	var out createQueueResponse
	if err := c.do(http.MethodPost, "/api/batch-tasks", req, &out); err != nil {
		return "", err
	}
	if out.QueueID == "" {
		return "", fmt.Errorf("建立佇列沒有回傳 queueId: %s", out.Err)
	}
	return out.QueueID, nil
}

func (c *apiClient) getQueue(queueID string) (*handler.BatchTaskQueue, error) {
	var out getQueueResponse
	if err := c.do(http.MethodGet, "/api/batch-tasks/"+url.PathEscape(queueID), nil, &out); err != nil {
		return nil, err
	}
	if out.Queue == nil {
		return nil, errors.New("回應沒有 queue 欄位: " + out.Err)
	}
	return out.Queue, nil
}

// waitQueue 輪詢到佇列收工，回傳任務成敗統計。
func (c *apiClient) waitQueue(queueID string, poll, timeout time.Duration, sugar *zap.SugaredLogger) (completed, failed int, err error) {
	deadline := time.Now().Add(timeout)
	lastLine := ""
	for {
		q, getErr := c.getQueue(queueID)
		if getErr != nil {
			return completed, failed, getErr
		}
		done, bad := 0, 0
		for _, t := range q.Tasks {
			if t == nil {
				continue
			}
			switch t.Status {
			case handler.BatchTaskStatusCompleted:
				done++
			case handler.BatchTaskStatusFailed, handler.BatchTaskStatusCancelled:
				bad++
			}
		}
		if line := fmt.Sprintf("status=%s 進度 %d/%d", q.Status, done+bad, len(q.Tasks)); line != lastLine {
			sugar.Infof("  佇列 %s：%s", queueID, line)
			lastLine = line
		}
		if queueTerminalStatuses[q.Status] {
			return done, bad, nil
		}
		if time.Now().After(deadline) {
			return done, bad, fmt.Errorf("等待超過 %s（仍停在 status=%s，進度 %d/%d）", timeout, q.Status, done+bad, len(q.Tasks))
		}
		time.Sleep(poll)
	}
}

type drainOptions struct {
	status         string
	project        string
	batch          int
	channel        string
	excluded       []string
	concurrency    int
	filterEvidence bool
	maxRounds      int
	pause          time.Duration
	poll           time.Duration
	queueWait      time.Duration
	dryRun         bool
	reportSkipped  int
}

func drain(client *apiClient, opts drainOptions, sugar *zap.SugaredLogger) {
	// dispatched 記住本輪已派出去的 id：複測失敗時漏洞會留在原狀態，下一輪若不
	// 排除就會被重新撈到，等於對同一批 id 無限重派。排程版只記最近兩輪，是因為
	// 它每 30 分鐘跑一次還得照顧新漏洞；drain 是排空，不該回頭。
	dispatched := map[string]bool{}
	stallRounds, errorRounds := 0, 0
	totalDispatched, totalCompleted, totalFailed := 0, 0, 0
	firstRound := true

	for round := 1; round <= opts.maxRounds; round++ {
		vulns, err := client.listVulnerabilities(opts.status, opts.project)
		if err != nil {
			errorRounds++
			sugar.Warnf("第 %d 輪拉取失敗（連續 %d/%d）: %v", round, errorRounds, errorLimit, err)
			if errorRounds >= errorLimit {
				sugar.Fatalf("連續 %d 輪拉取失敗，中止", errorLimit)
			}
			time.Sleep(opts.pause)
			continue
		}
		picked, skipByReason, skipped := selectTargets(vulns, opts.excluded, opts.filterEvidence)

		if firstRound {
			reportBacklog(sugar, opts, len(vulns), picked, skipByReason, skipped)
			if opts.dryRun {
				return
			}
			firstRound = false
		}

		tasks, batchIDs := nextBatch(picked, dispatched, opts.batch)
		if len(tasks) == 0 {
			sugar.Infof("佇列已排空，共 %d 輪。", round-1)
			break
		}

		queueID, err := client.createQueue(map[string]interface{}{
			"title":        "驗證排空 " + time.Now().Format("0102-1504"),
			"tasks":        tasks,
			"executeNow":   true,
			"aiChannelId":  opts.channel,
			"concurrency":  opts.concurrency,
			"projectId":    opts.project,
			"scheduleMode": "manual",
		})
		if err != nil {
			errorRounds++
			sugar.Warnf("第 %d 輪建立佇列失敗（連續 %d/%d）: %v", round, errorRounds, errorLimit, err)
			if errorRounds >= errorLimit {
				sugar.Fatalf("連續 %d 輪失敗，中止", errorLimit)
			}
			time.Sleep(opts.pause)
			continue
		}
		errorRounds = 0
		for _, id := range batchIDs {
			dispatched[id] = true
		}

		sugar.Infof("第 %d 輪：派工 %d 筆 → 佇列 %s（通道 %s，並行 %d）", round, len(tasks), queueID, opts.channel, opts.concurrency)
		completed, failed, waitErr := client.waitQueue(queueID, opts.poll, opts.queueWait, sugar)
		if waitErr != nil {
			// 逾時不重派這批：子任務可能還在伺服器上跑，重派會讓同一個漏洞同時
			// 有兩個對話在寫。留給人工確認佇列狀態。
			sugar.Warnf("第 %d 輪等待佇列 %s 失敗（這批不重派）: %v", round, queueID, waitErr)
		}
		totalDispatched += len(batchIDs)
		totalCompleted += completed
		totalFailed += failed
		sugar.Infof("第 %d 輪結束：completed=%d failed=%d 尚未派工=%d", round, completed, failed, countUndispatched(picked, dispatched))

		if completed == 0 && failed == 0 {
			stallRounds++
			if stallRounds >= stallLimit {
				sugar.Warnf("連續 %d 輪零進展（agent 沒寫回任何狀態，通常是工具不可用或通道不對），停止", stallLimit)
				break
			}
		} else {
			stallRounds = 0
		}
		time.Sleep(opts.pause)
	}

	sugar.Infof("合計：dispatched=%d completed=%d failed=%d", totalDispatched, totalCompleted, totalFailed)
}

func nextBatch(picked []*database.Vulnerability, dispatched map[string]bool, batch int) ([]string, []string) {
	tasks := make([]string, 0, batch)
	ids := make([]string, 0, batch)
	for _, v := range picked {
		if v == nil || dispatched[v.ID] {
			continue
		}
		tasks = append(tasks, handler.BuildAutoVerifyPrompt(v))
		ids = append(ids, v.ID)
		if len(tasks) >= batch {
			break
		}
	}
	return tasks, ids
}

func countUndispatched(picked []*database.Vulnerability, dispatched map[string]bool) int {
	n := 0
	for _, v := range picked {
		if v != nil && !dispatched[v.ID] {
			n++
		}
	}
	return n
}

// reportBacklog 把「有多少、會派多少、為什麼跳過」講清楚。dry-run 到這裡就結束。
func reportBacklog(sugar *zap.SugaredLogger, opts drainOptions, total int,
	picked []*database.Vulnerability, skipByReason map[string]int, skipped []*database.Vulnerability) {
	sugar.Infof("%s 共 %d 筆；可派工 %d 筆", opts.status, total, len(picked))
	if len(skipByReason) > 0 {
		sugar.Infof("篩掉的紀錄：%s", formatSkipReasons(skipByReason))
	}
	if n := opts.reportSkipped; n > 0 && len(skipped) > 0 {
		sugar.Infof("被篩掉的樣本（前 %d 筆）：", min(n, len(skipped)))
		for i, v := range skipped {
			if i >= n {
				break
			}
			sugar.Infof("  [%s] %s | target=%q | 原因=%s", v.Severity, truncate(v.Title, 40), v.Target, unverifiableReason(v))
		}
	}
	if !opts.dryRun {
		return
	}
	rounds := (len(picked) + opts.batch - 1) / opts.batch
	sugar.Infof("dry-run：以下 %d 筆會在第 1 輪派進佇列（全部 %d 筆分 %d 輪派完）", min(opts.batch, len(picked)), len(picked), rounds)
	for i, v := range picked {
		if i >= opts.batch {
			break
		}
		sugar.Infof("  %s | [%s] %s | target=%s", v.ID, v.Severity, truncate(v.Title, 50), truncate(v.Target, 60))
	}
}

// unverifiableReason 回傳這筆漏洞不適合直接送去複測的原因，空字串代表可派工。
//
// 為什麼需要這道篩選：資料庫裡有大量從匯入流程留下的佔位紀錄（target 根本是
// "target" 這種欄位名，復現步驟與證據都空）。agent 拿到這種任務只會回一句
// 「工具不可用，未完成複測」，幾百筆就是幾百個燒 token 的對話，而且寫不回任何
// 東西——佔位紀錄要修的是資料，不是複測。
func unverifiableReason(v *database.Vulnerability) string {
	target := strings.TrimSpace(v.Target)
	if target == "" {
		return "target 為空"
	}
	if !strings.Contains(target, "://") && !strings.ContainsAny(target, ".:") {
		return "target 不像主機或 URL"
	}
	if strings.TrimSpace(v.ReproSteps) == "" && strings.TrimSpace(v.Evidence) == "" {
		return "無復現步驟與證據"
	}
	return ""
}

func severityExcluded(severity string, excluded []string) bool {
	s := strings.ToLower(strings.TrimSpace(severity))
	for _, e := range excluded {
		if strings.ToLower(strings.TrimSpace(e)) == s {
			return true
		}
	}
	return false
}

// selectTargets 套用篩選，回傳可派工的漏洞、跳過原因統計與被跳過的紀錄。
func selectTargets(vulns []*database.Vulnerability, excluded []string, filterEvidence bool) (
	picked []*database.Vulnerability, skipByReason map[string]int, skipped []*database.Vulnerability) {
	skipByReason = map[string]int{}
	for _, v := range vulns {
		if v == nil {
			continue
		}
		if severityExcluded(v.Severity, excluded) {
			skipByReason["嚴重度被排除"]++
			skipped = append(skipped, v)
			continue
		}
		if filterEvidence {
			if reason := unverifiableReason(v); reason != "" {
				skipByReason[reason]++
				skipped = append(skipped, v)
				continue
			}
		}
		picked = append(picked, v)
	}
	return picked, skipByReason, skipped
}

func formatSkipReasons(m map[string]int) string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, fmt.Sprintf("%s=%d", k, m[k]))
	}
	return strings.Join(parts, " ")
}

func parseCSV(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}

func orAll(s string) string {
	if strings.TrimSpace(s) == "" {
		return "（全部）"
	}
	return s
}

func truncate(s string, n int) string {
	r := []rune(strings.TrimSpace(s))
	if len(r) <= n {
		return string(r)
	}
	return string(r[:n]) + "…"
}

func snippet(raw []byte) string {
	s := strings.TrimSpace(string(raw))
	if len(s) > 300 {
		return s[:300] + "…"
	}
	return s
}
