package handler

import (
	"context"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/forbidden"
	"jysecai/internal/proxypool"
	"jysecai/internal/redirect"
	"jysecai/internal/redirectverify"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// 批次受控跳轉驗證。
//
// 單筆複測走 MCP 工具 redirect_probe；這裡是「一次送很多筆」的版本：
// 控制台貼上多個目標 → 建立批次 → 背景執行 → 查進度 → 匯出報告，
// 驗證成功的目標可自動建立漏洞紀錄（自動上鍊）。
//
// 這是長跑工作，所以批次與每筆結果都落資料庫：頁面重新整理不會消失，
// 進度可查、可取消。

const (
	// redirectVerifyDefaultConcurrency 是批次預設併發數。
	redirectVerifyDefaultConcurrency = 4
	// redirectVerifyMaxConcurrency 是批次併發上限。
	redirectVerifyMaxConcurrency = 16
	// redirectVerifyMaxTargets 是單批目標數上限，避免一次把批次撐爆。
	redirectVerifyMaxTargets = 5000
	// redirectVerifyDefaultTimeoutSeconds 是單次探測預設逾時（秒）。
	redirectVerifyDefaultTimeoutSeconds = 10
	// redirectVerifyCancelPollInterval 是背景工作輪詢取消旗標的間隔。
	redirectVerifyCancelPollInterval = 2 * time.Second
	// redirectVerifyMaxRepeat 是單一目標重複探測的上限。
	redirectVerifyMaxRepeat = 5
)

// RedirectVerifyHandler 處理批次受控跳轉驗證的 API。
type RedirectVerifyHandler struct {
	cfg    *config.Config
	db     *database.DB
	logger *zap.Logger

	proxyPool *proxypool.Manager

	mu      sync.Mutex
	cancels map[string]context.CancelFunc
	// proxies 保存執行中的批次所用的「原始」代理網址（含帳密）。
	//
	// 落庫的只留遮蔽版（報告與 API 都不該出現真實密碼），因此執行時的憑證只存在
	// 記憶體：批次本來就是同一個行程內跑完的東西，重啟後本來也接不起來。
	proxies map[string]string
}

// SetProxyPoolManager 注入代理池，讓批次可以走既有輪替出口（例如住宅群組）。
func (h *RedirectVerifyHandler) SetProxyPoolManager(manager *proxypool.Manager) {
	h.proxyPool = manager
}

// NewRedirectVerifyHandler 建立批次驗證 handler。
func NewRedirectVerifyHandler(cfg *config.Config, db *database.DB, logger *zap.Logger) *RedirectVerifyHandler {
	return &RedirectVerifyHandler{
		cfg:     cfg,
		db:      db,
		logger:  logger,
		cancels: make(map[string]context.CancelFunc),
		proxies: make(map[string]string),
	}
}

type redirectVerifyRunRequest struct {
	Targets        []string `json:"targets"`
	Endpoints      []string `json:"endpoints"`
	Param          string   `json:"param"`
	Method         string   `json:"method"`
	ProjectID      string   `json:"project_id"`
	ConversationID string   `json:"conversation_id"`
	AutoRecord     bool     `json:"auto_record"`
	Concurrency    int      `json:"concurrency"`
	TimeoutSeconds int      `json:"timeout_seconds"`
	// Proxy 是代理網址；支援 http、https、socks5、socks5h、socks4、socks4a。
	Proxy string `json:"proxy"`
	// ProxyGroup 是使用平台代理池的群組名稱（例如 residential）。
	ProxyGroup string `json:"proxy_group"`
	// Crawl 開啟「自動巡站」：先巡每個種子站點，找出站上本來就有的跳轉入口，
	// 再把受控端點代入那些入口去驗證。
	//
	// 這是「自動植入」的開關：關閉時只對請求內附的目標盲試參數名，
	// 站點本來的跳轉方法用不上（實測常見結果是 confirmed=0）。
	Crawl bool `json:"crawl"`
	// CrawlMaxPages / CrawlMaxDepth 是每個種子站點的巡站上限。
	CrawlMaxPages int `json:"crawl_max_pages"`
	CrawlMaxDepth int `json:"crawl_max_depth"`
	// SeedSource 是種子來源：manual（用本請求的 targets）、assets、vulns。
	SeedSource string `json:"seed_source"`
	// SeedKeyword 是從資產庫／漏洞紀錄挑站點時的分類關鍵字（例如 娛樂城、SEO、現金版）。
	SeedKeyword string `json:"seed_keyword"`
	// SeedLimit 是種子站點數上限。
	SeedLimit int `json:"seed_limit"`
	// Encoding 是受控端點寫進 payload 的編碼方式（none／percent／base64…）。
	//
	// 編碼只改變寫出去的字面形式，不改變它指向哪裡；驗證時會解回來比對，
	// 所以「編碼植入 → 目標解碼跳轉」仍然算命中。
	Encoding string `json:"encoding"`
	// Repeat 是同一個目標重複探測幾次（1 = 不重複，上限 5）。
	//
	// 命中一次可能是巧合；重複複測都一致才算可信。預設 1，因為每次都會
	// 真的送出請求，對第三方站點是額外噪音。
	Repeat int `json:"repeat"`
	// ScanInjections 開啟「注入點偵測」：巡站時順便找出頁面裡「他們塞的」
	// 外部網址（script src／iframe src／meta refresh／inline JS 字串…），
	// 那是「把他們注入的換成我們的 URL」的替換位置。
	ScanInjections bool `json:"scan_injections"`
}

// ListEndpoints 回傳目前可用的受控端點（跳轉目標）。
func (h *RedirectVerifyHandler) ListEndpoints(c *gin.Context) {
	endpoints := []string{}
	if h.cfg != nil {
		endpoints = redirect.NormalizeURLs(h.cfg.Redirect.URLs)
	}
	c.JSON(http.StatusOK, gin.H{"endpoints": endpoints})
}

type redirectVerifyCrawlRequest struct {
	// Seeds 是要巡站的站點（通常是情蒐取得的 host）。
	Seeds []string `json:"seeds"`
	// MaxPages / MaxDepth 是每個站點的走訪上限。
	MaxPages int `json:"max_pages"`
	MaxDepth int `json:"max_depth"`
	// SameHostOnly 是否只走訪與種子同主機的頁面（預設 true）。
	SameHostOnly *bool `json:"same_host_only"`
	// TimeoutSeconds 是抓取單頁的逾時。
	TimeoutSeconds int `json:"timeout_seconds"`
	// Proxy 是代理出口；支援 http、https、socks5、socks5h、socks4、socks4a。
	Proxy string `json:"proxy"`
	// ProxyGroup 是使用平台代理池的群組名稱（例如 residential）。
	ProxyGroup string `json:"proxy_group"`
}

// Crawl 走訪站點並找出帶著跳轉參數的候選入口。
//
// 這是「巡站發掘」步驟：候選 URL 會帶著原本的跳轉參數與值，交給批次驗證時
// 再把參數值換成受控端點。
func (h *RedirectVerifyHandler) Crawl(c *gin.Context) {
	var req redirectVerifyCrawlRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}
	seeds := dedupeNonEmptyStrings(req.Seeds)
	if len(seeds) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请至少提供一个种子站点"})
		return
	}
	// 巡站同樣不得走進 119／EPCR／消防救護永久禁區。
	allowedSeeds, forbiddenSeeds := forbidden.FilterTargets(seeds)
	if len(allowedSeeds) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":             "所有种子站点都属于 119／EPCR／消防救护永久禁区，已拒绝执行",
			"forbidden_targets": forbiddenSeeds,
		})
		return
	}
	seeds = allowedSeeds
	timeoutSeconds := req.TimeoutSeconds
	if timeoutSeconds <= 0 {
		timeoutSeconds = redirectVerifyDefaultTimeoutSeconds
	}
	proxyGroup := strings.TrimSpace(req.ProxyGroup)
	if proxyGroup != "" && h.proxyPool == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "代理池未启用，无法使用 proxy_group"})
		return
	}
	client, err := redirect.NewVerifyClient(strings.TrimSpace(req.Proxy), time.Duration(timeoutSeconds)*time.Second)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "代理设置无效: " + err.Error()})
		return
	}
	// 明確指定的代理網址優先；只有沒指定網址時才改走代理池群組，
	// 與批次驗證（clientForRun）的優先順序一致。
	if strings.TrimSpace(req.Proxy) == "" && proxyGroup != "" {
		client = h.proxyPool.ClientGroup(time.Duration(timeoutSeconds)*time.Second, proxyGroup)
	}
	sameHostOnly := true
	if req.SameHostOnly != nil {
		sameHostOnly = *req.SameHostOnly
	}

	result := redirect.DiscoverRedirectCandidates(c.Request.Context(), client, seeds, redirect.CrawlOptions{
		MaxPages:     req.MaxPages,
		MaxDepth:     req.MaxDepth,
		SameHostOnly: sameHostOnly,
		Timeout:      time.Duration(timeoutSeconds) * time.Second,
		// 巡站時不把我們自己的受控端點當成「他們注入的」——
		// 否則自動植入會拿自己植入的東西去替換自己。
		IgnoreInjectionHosts: h.endpointHosts(),
	})
	c.JSON(http.StatusOK, gin.H{
		"pages_visited":          result.PagesVisited,
		"candidates":             result.Candidates,
		"visited":                result.Visited,
		"injections":             result.Injections,
		"injection_count":        result.InjectionCount,
		"third_party_injections": result.ThirdPartyInjections,
		"forbidden_skipped":      len(forbiddenSeeds),
	})
}

// endpointHosts 回傳我們自己受控端點的主機名清單。
//
// 偵測注入點時必須把這些主機排除 —— 否則「我們自己植入的片段」
// 會被回報成「他們注入的」，自動植入就變成拿自己的東西替換自己。
func (h *RedirectVerifyHandler) endpointHosts() []string {
	endpoints := []string{}
	if h.cfg != nil {
		endpoints = redirect.NormalizeURLs(h.cfg.Redirect.URLs)
	}
	hosts := make([]string, 0, len(endpoints))
	for _, endpoint := range endpoints {
		if host := redirect.EndpointHost(endpoint); host != "" {
			hosts = append(hosts, host)
		}
	}
	return hosts
}

// redirectVerifyInjectionRequest 是「掃描單一頁面的注入點並產生替換片段」的請求。
type redirectVerifyInjectionRequest struct {
	// URL 是要掃描的頁面。
	URL string `json:"url"`
	// Endpoint 是我們的受控端點；留空時用平台設定的第一個端點。
	Endpoint string `json:"endpoint"`
	// Encoding 是寫入時的編碼方式。
	Encoding string `json:"encoding"`
	// Proxy / ProxyGroup 是出口設定（與其他端點一致）。
	Proxy      string `json:"proxy"`
	ProxyGroup string `json:"proxy_group"`
	// TimeoutSeconds 是抓取單頁的逾時。
	TimeoutSeconds int `json:"timeout_seconds"`
	// SkipSelfHost 為 true 時不回報指向站方自己資源的注入點。
	SkipSelfHost bool `json:"skip_self_host"`
	// VerifyEndpoint 為 true 時順帶探一次受控端點，確認片段配得上這個端點。
	VerifyEndpoint bool `json:"verify_endpoint"`
	// WithImplant 為 true 時為每個注入點產生「換成我們的 URL」的片段。
	WithImplant bool `json:"with_implant"`
}

// ScanInjections 掃描單一頁面的注入點，並可一併產生替換片段。
//
// 這是「把他們注入的換成我們的」的第一段：先定位（哪些位置被塞了外部網址），
// 再產生替換片段（我們的受控端點，可編碼），最後由操作者貼進受控站。
//
// 這裡只讀不改：平台不會自己去動目標站的頁面。
func (h *RedirectVerifyHandler) ScanInjections(c *gin.Context) {
	var req redirectVerifyInjectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}
	pageURL := strings.TrimSpace(req.URL)
	if pageURL == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请提供要扫描的页面 URL"})
		return
	}
	// 119／EPCR／消防救護類永久禁區：這裡會真的對外發出 HTTP 請求。
	if reason := forbidden.Reason("", pageURL, "", pageURL, ""); reason != "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":  "目标属于 119／EPCR／消防救护永久禁区，已拒绝执行",
			"reason": reason,
		})
		return
	}

	endpoint := strings.TrimSpace(req.Endpoint)
	if endpoint == "" && h.cfg != nil {
		if endpoints := redirect.NormalizeURLs(h.cfg.Redirect.URLs); len(endpoints) > 0 {
			endpoint = endpoints[0]
		}
	}
	if req.WithImplant && endpoint == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请提供 endpoint（受控端点），或先在平台设置中配置 redirect.urls。"})
		return
	}

	timeoutSeconds := req.TimeoutSeconds
	if timeoutSeconds <= 0 {
		timeoutSeconds = redirectVerifyDefaultTimeoutSeconds
	}
	proxyGroup := strings.TrimSpace(req.ProxyGroup)
	if proxyGroup != "" && h.proxyPool == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "代理池未启用，无法使用 proxy_group"})
		return
	}
	client, err := redirect.NewVerifyClient(strings.TrimSpace(req.Proxy), time.Duration(timeoutSeconds)*time.Second)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "代理设置无效: " + err.Error()})
		return
	}
	if strings.TrimSpace(req.Proxy) == "" && proxyGroup != "" {
		client = h.proxyPool.ClientGroup(time.Duration(timeoutSeconds)*time.Second, proxyGroup)
	}

	ctx := c.Request.Context()
	req2, err := http.NewRequestWithContext(ctx, http.MethodGet, pageURL, nil)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "页面 URL 无效: " + err.Error()})
		return
	}
	req2.Header.Set("User-Agent", redirect.DefaultCrawlUserAgent)
	req2.Header.Set("Accept", "text/html,application/xhtml+xml")
	resp, err := client.Do(req2)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "抓取页面失败: " + err.Error()})
		return
	}
	defer resp.Body.Close()
	body, readErr := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if readErr != nil && len(body) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "读取页面内容失败: " + readErr.Error()})
		return
	}

	ignoreHosts := h.endpointHosts()
	if host := redirect.EndpointHost(endpoint); host != "" {
		ignoreHosts = append(ignoreHosts, host)
	}
	points := redirect.ScanInjections(pageURL, body, redirect.InjectionScanOptions{
		IgnoreHosts: ignoreHosts,
	})

	thirdParty := 0
	kept := make([]redirect.InjectionPoint, 0, len(points))
	for _, point := range points {
		if req.SkipSelfHost && point.SelfHost {
			continue
		}
		if !point.SelfHost {
			thirdParty++
		}
		kept = append(kept, point)
	}

	// 替換片段：把「他們塞的」換成「我們的」。
	implants := make([]redirect.PointImplantResult, 0, len(kept))
	if req.WithImplant {
		for _, point := range kept {
			implant, buildErr := redirect.BuildPointImplant(redirect.PointImplantOptions{
				Point:    point,
				Endpoint: endpoint,
				Encoding: req.Encoding,
			})
			if buildErr != nil {
				continue
			}
			implants = append(implants, implant)
		}
	}

	// 受控端點自我驗證：片段配得上這個端點才算「實」。
	var check *redirect.EndpointCheck
	if req.VerifyEndpoint && endpoint != "" {
		probe := redirect.CheckEndpoint(ctx, client, endpoint, "")
		check = &probe
	}

	c.JSON(http.StatusOK, gin.H{
		"url":                     pageURL,
		"status":                  resp.StatusCode,
		"injections":              kept,
		"injection_count":         len(kept),
		"third_party_injections":  thirdParty,
		"implants":                implants,
		"endpoint":                endpoint,
		"endpoint_check":          check,
		"point_encodings_by_kind": redirect.InjectionEncodingMatrix(),
	})
}

// redirectVerifyImplantRequest 是產生植入載荷的請求。
type redirectVerifyImplantRequest struct {
	// Endpoint 是要植入的受控端點；留空時用平台設定的第一個端點。
	Endpoint string `json:"endpoint"`
	// Encoding 是編碼方式（none／percent／base64／hex／js_unicode…）。
	Encoding string `json:"encoding"`
	// Kind 是載荷型態（js_redirect／js_window_open／js_location_replace／meta_refresh／url_param）。
	Kind string `json:"kind"`
	// Param 是 url_param 型態的參數名。
	Param string `json:"param"`
	// Point 是「要替換的既有注入點」。
	//
	// 有帶 point 時走「把他們注入的換成我們的」這條路：型態沿用原注入點，
	// 編碼則受原型態限制（見 redirect.ImplantEncodingsForPointKind）。
	Point *redirect.InjectionPoint `json:"point"`
}

// ImplantCapabilities 回傳植入載荷產生器的能力矩陣。
//
// 前端據此把不相容的「型態 × 編碼」組合停用，避免使用者送出注定失敗的請求。
// 規則只存在 redirect 套件裡一份（ImplantEncodingMatrix），前端不另外複製。
func (h *RedirectVerifyHandler) ImplantCapabilities(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"kinds":                   redirect.ImplantKinds(),
		"encodings":               redirect.PayloadEncodings(),
		"encodings_by_kind":       redirect.ImplantEncodingMatrix(),
		"point_kinds":             redirect.InjectionKinds(),
		"point_encodings_by_kind": redirect.InjectionEncodingMatrix(),
	})
}

// BuildImplant 產生帶著受控端點的植入片段。
//
// 這是「把他們植入的換成我們的 URL」的產出端：把受控端點包成可以直接放進
// 受控頁面的片段，並可選擇把網址編碼（js_unicode 是純跳脫、不需解碼器；
// base64／hex 會自動附上 atob／String.fromCharCode）。
func (h *RedirectVerifyHandler) BuildImplant(c *gin.Context) {
	var req redirectVerifyImplantRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}
	endpoint := strings.TrimSpace(req.Endpoint)
	if endpoint == "" && h.cfg != nil {
		if endpoints := redirect.NormalizeURLs(h.cfg.Redirect.URLs); len(endpoints) > 0 {
			endpoint = endpoints[0]
		}
	}
	if endpoint == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请提供 endpoint（受控端点），或先在平台设置中配置 redirect.urls。"})
		return
	}
	// 替換既有注入點：型態與編碼規則都由注入點本身決定。
	if req.Point != nil {
		point := *req.Point
		if strings.TrimSpace(point.Kind) == "" {
			point.Kind = strings.TrimSpace(req.Kind)
		}
		pointResult, pointErr := redirect.BuildPointImplant(redirect.PointImplantOptions{
			Point:    point,
			Endpoint: endpoint,
			Encoding: req.Encoding,
			Param:    req.Param,
		})
		if pointErr != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error":     pointErr.Error(),
				"supported": redirect.ImplantEncodingsForPointKind(point.Kind),
			})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"implant":           pointResult,
			"point_encodings":   redirect.ImplantEncodingsForPointKind(point.Kind),
			"encodings":         redirect.PayloadEncodings(),
			"encodings_by_kind": redirect.ImplantEncodingMatrix(),
			"kinds":             redirect.ImplantKinds(),
		})
		return
	}

	result, err := redirect.BuildImplant(redirect.ImplantOptions{
		Endpoint: endpoint,
		Encoding: req.Encoding,
		Kind:     req.Kind,
		Param:    req.Param,
	})
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"implant":           result,
		"encodings":         redirect.PayloadEncodings(),
		"encodings_by_kind": redirect.ImplantEncodingMatrix(),
		"kinds":             redirect.ImplantKinds(),
	})
}

// CreateRun 建立批次並在背景執行。
func (h *RedirectVerifyHandler) CreateRun(c *gin.Context) {
	var req redirectVerifyRunRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数: " + err.Error()})
		return
	}

	targets := dedupeNonEmptyStrings(req.Targets)
	seedSource := strings.ToLower(strings.TrimSpace(req.SeedSource))
	if seedSource == "" {
		seedSource = database.RedirectVerifySeedSourceManual
	}

	// 種子來源不是 manual 時，站點從平台的資產庫／漏洞紀錄依分類關鍵字撈。
	//
	// 這是「掃哪一批站點」不靠人工複製網址的來源：漏洞庫裡本來就有分類
	// （娛樂城、SEO 投毒、現金版…），每筆都帶著目標主機與既有證據。
	if seedSource != database.RedirectVerifySeedSourceManual {
		if h.db == nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
			return
		}
		keyword := strings.TrimSpace(req.SeedKeyword)
		if keyword == "" {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "使用资产库／漏洞记录当种子来源时必须提供分类关键字（例如 娛樂城、SEO、現金版）",
			})
			return
		}
		seedLimit := req.SeedLimit
		if seedLimit <= 0 {
			seedLimit = 50
		}
		collected, collectErr := h.db.CollectRedirectVerifySeeds(seedSource, keyword, seedLimit)
		if collectErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": collectErr.Error()})
			return
		}
		if len(collected) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{
				"error":  fmt.Sprintf("没有符合关键字 %q 的站点可作为种子", keyword),
				"source": seedSource,
			})
			return
		}
		targets = collected
	}

	if len(targets) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请至少提供一个目标 URL"})
		return
	}
	if len(targets) > redirectVerifyMaxTargets {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("单批最多 %d 个目标", redirectVerifyMaxTargets)})
		return
	}

	// 119／EPCR／消防救護類永久禁區：批次會真的對外發 HTTP 請求，禁區目標必須擋下。
	// 目標多半是從漏洞庫匯入的，而漏洞庫裡確實有禁區資產的紀錄。
	// 禁區目標保留在清單裡（執行時逐筆跳過並在結果列標示原因），只有全部被禁時才整批拒絕。
	allowedTargets, forbiddenTargets := forbidden.FilterTargets(targets)
	if len(allowedTargets) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":             "所有目标都属于 119／EPCR／消防救护永久禁区，已拒绝执行",
			"forbidden_targets": forbiddenTargets,
		})
		return
	}
	if len(forbiddenTargets) > 0 && h.logger != nil {
		h.logger.Warn("跳轉驗證批次含永久禁區目標，執行時會逐筆跳過",
			zap.Int("skipped", len(forbiddenTargets)),
			zap.Strings("targets", forbiddenTargets))
	}

	endpoints := redirect.NormalizeURLs(req.Endpoints)
	if len(endpoints) == 0 && h.cfg != nil {
		endpoints = redirect.NormalizeURLs(h.cfg.Redirect.URLs)
	}
	if len(endpoints) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "没有可用的受控端点（跳转目标）。请在平台设置中配置 redirect.urls，或在本次请求传入 endpoints。"})
		return
	}

	method := strings.ToUpper(strings.TrimSpace(req.Method))
	if method == "" {
		method = http.MethodGet
	}
	if method != http.MethodGet && method != http.MethodPost {
		c.JSON(http.StatusBadRequest, gin.H{"error": "method 仅支持 GET 或 POST"})
		return
	}

	// 編碼方式：寫進 payload 的形式。先驗證，不要等到批次跑到一半才整批失敗。
	encoding, encodingErr := redirect.NormalizePayloadEncoding(req.Encoding)
	if encodingErr != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":     encodingErr.Error(),
			"supported": redirect.PayloadEncodings(),
		})
		return
	}

	concurrency := req.Concurrency
	if concurrency <= 0 {
		concurrency = redirectVerifyDefaultConcurrency
	}
	if concurrency > redirectVerifyMaxConcurrency {
		concurrency = redirectVerifyMaxConcurrency
	}
	timeoutSeconds := req.TimeoutSeconds
	if timeoutSeconds <= 0 {
		timeoutSeconds = redirectVerifyDefaultTimeoutSeconds
	}
	// 重複複測次數：1 = 不重複（預設），上限 5。
	//
	// 預設關閉，因為每次探測都會真的送出請求，對第三方站點是額外噪音；
	// 需要「穩不穩定」證據時才開。
	repeat := req.Repeat
	if repeat <= 0 {
		repeat = 1
	}
	if repeat > redirectVerifyMaxRepeat {
		repeat = redirectVerifyMaxRepeat
	}

	session, hasSession := security.CurrentSession(c)
	ownerUserID := ""
	if hasSession {
		ownerUserID = session.UserID
	}
	projectID := strings.TrimSpace(req.ProjectID)
	conversationID := strings.TrimSpace(req.ConversationID)

	// 綁定專案或對話時，必須真的看得到那個資源。
	if hasSession && h.db != nil && session.Scope != database.RBACScopeAll {
		if projectID != "" && !h.db.UserCanAccessResource(session.UserID, session.Scope, "project", projectID) {
			c.JSON(http.StatusForbidden, gin.H{"error": "无权在该项目下执行跳转验证"})
			return
		}
		if conversationID != "" && !h.db.UserCanAccessResource(session.UserID, session.Scope, "conversation", conversationID) {
			c.JSON(http.StatusForbidden, gin.H{"error": "无权关联该对话"})
			return
		}
	}

	proxyURL := strings.TrimSpace(req.Proxy)
	if proxyURL != "" {
		// 先驗證代理網址可用（協定是否支援），不要等到批次跑到一半才整批失敗。
		if _, err := redirect.NewProxyClient(proxyURL, time.Duration(timeoutSeconds)*time.Second); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "代理设置无效: " + err.Error()})
			return
		}
	}
	proxyGroup := strings.TrimSpace(req.ProxyGroup)
	if proxyGroup != "" && h.proxyPool == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "代理池未启用，无法使用 proxy_group"})
		return
	}

	run := &database.RedirectVerifyRun{
		Status:         database.RedirectVerifyStatusPending,
		Endpoints:      endpoints,
		Param:          strings.TrimSpace(req.Param),
		Method:         method,
		Concurrency:    concurrency,
		Total:          len(targets),
		ProjectID:      projectID,
		ConversationID: conversationID,
		OwnerUserID:    ownerUserID,
		AutoRecord:     req.AutoRecord,
		// 代理網址常帶帳密，落庫前先遮蔽；原始值只留在記憶體供執行時使用。
		Proxy:      redirect.MaskProxyURL(proxyURL),
		ProxyGroup: proxyGroup,
		// 自動巡站：先找出站上本來就有的跳轉入口，再代入受控端點。
		CrawlEnabled:  req.Crawl,
		CrawlMaxPages: req.CrawlMaxPages,
		CrawlMaxDepth: req.CrawlMaxDepth,
		SeedSource:    seedSource,
		SeedKeyword:   strings.TrimSpace(req.SeedKeyword),
		SeedCount:     len(targets),
		Encoding:      encoding,
		Repeat:        repeat,
	}
	if run.CrawlMaxPages <= 0 {
		run.CrawlMaxPages = redirect.DefaultCrawlMaxPages
	}
	if run.CrawlMaxDepth < 0 {
		run.CrawlMaxDepth = 0
	}
	if proxyURL != "" {
		h.mu.Lock()
		h.proxies[run.ID] = proxyURL
		h.mu.Unlock()
	}
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
		return
	}
	if err := h.db.CreateRedirectVerifyRun(run); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "创建批次失败: " + err.Error()})
		return
	}
	if ownerUserID != "" {
		_ = h.db.SetResourceOwner("redirect_verify_run", run.ID, ownerUserID)
		_ = h.db.AssignResourceToUser(ownerUserID, "redirect_verify_run", run.ID)
	}

	// 背景執行：HTTP 請求立刻結束，進度另外查。
	go h.executeRun(run, targets, time.Duration(timeoutSeconds)*time.Second)

	c.JSON(http.StatusAccepted, gin.H{"run": run, "forbidden_skipped": len(forbiddenTargets)})
}

// ListRuns 列出批次。
func (h *RedirectVerifyHandler) ListRuns(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
		return
	}
	session, ok := security.CurrentSession(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "未登录"})
		return
	}
	limit := 50
	if raw := strings.TrimSpace(c.Query("limit")); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed > 0 && parsed <= 200 {
			limit = parsed
		}
	}
	runs, err := h.db.ListRedirectVerifyRunsForAccess(limit, session.UserID, session.Scope)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询批次失败: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"runs": runs})
}

// GetRun 回傳單一批次與其結果。
func (h *RedirectVerifyHandler) GetRun(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
		return
	}
	run, err := h.db.GetRedirectVerifyRun(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	results, err := h.db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询批次结果失败: " + err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"run":      run,
		"results":  results,
		"accuracy": redirectverify.ComputeAccuracy(run, results),
	})
}

// CancelRun 請求取消批次。
func (h *RedirectVerifyHandler) CancelRun(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
		return
	}
	runID := strings.TrimSpace(c.Param("id"))
	accepted, err := h.db.RequestRedirectVerifyRunCancel(runID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if !accepted {
		c.JSON(http.StatusConflict, gin.H{"error": "批次已结束或不存在，无法取消"})
		return
	}
	// 同一個行程內立刻叫停；跨行程則由背景工作輪詢資料庫旗標。
	h.mu.Lock()
	if cancel, ok := h.cancels[runID]; ok {
		cancel()
	}
	h.mu.Unlock()
	c.JSON(http.StatusAccepted, gin.H{"run_id": runID, "cancelling": true})
}

// RunReport 匯出批次報告。
func (h *RedirectVerifyHandler) RunReport(c *gin.Context) {
	if h.db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "数据库不可用"})
		return
	}
	run, err := h.db.GetRedirectVerifyRun(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	results, err := h.db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询批次结果失败: " + err.Error()})
		return
	}

	format := strings.ToLower(strings.TrimSpace(c.DefaultQuery("format", "markdown")))
	switch format {
	case "csv":
		c.Header("Content-Type", "text/csv; charset=utf-8")
		c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=\"redirect-verify-%s.csv\"", run.ID))
		c.Status(http.StatusOK)
		if err := writeRedirectVerifyCSV(c.Writer, run, results); err != nil {
			if h.logger != nil {
				h.logger.Warn("导出跳轉驗證 CSV 失敗", zap.Error(err))
			}
		}
	case "json":
		c.JSON(http.StatusOK, gin.H{
			"run":      run,
			"results":  results,
			"accuracy": redirectverify.ComputeAccuracy(run, results),
		})
	default:
		c.Header("Content-Type", "text/markdown; charset=utf-8")
		c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=\"redirect-verify-%s.md\"", run.ID))
		c.Status(http.StatusOK)
		_, _ = c.Writer.Write([]byte(buildRedirectVerifyMarkdown(run, results)))
	}
}

// executeRun 在背景執行批次。
func (h *RedirectVerifyHandler) executeRun(run *database.RedirectVerifyRun, targets []string, timeout time.Duration) {
	ctx, cancel := context.WithCancel(context.Background())
	h.mu.Lock()
	h.cancels[run.ID] = cancel
	h.mu.Unlock()
	defer func() {
		cancel()
		h.mu.Lock()
		delete(h.cancels, run.ID)
		delete(h.proxies, run.ID)
		h.mu.Unlock()
	}()

	// 跨行程的取消：輪詢資料庫旗標。
	stopPolling := make(chan struct{})
	defer close(stopPolling)
	go h.watchCancelFlag(run.ID, cancel, stopPolling)

	if err := h.db.StartRedirectVerifyRun(run.ID); err != nil && h.logger != nil {
		h.logger.Warn("標記跳轉驗證批次開始失敗", zap.String("run_id", run.ID), zap.Error(err))
	}

	client, err := h.buildClient(run, timeout)
	if err != nil {
		if h.logger != nil {
			h.logger.Warn("建立跳轉驗證 HTTP client 失敗", zap.String("run_id", run.ID), zap.Error(err))
		}
		_ = h.db.FinishRedirectVerifyRun(run.ID, database.RedirectVerifyStatusFailed, err.Error())
		return
	}

	// 階段一：自動巡站，找出站上本來就有的跳轉入口。
	//
	// 這是「自動植入」的關鍵：關閉巡站時只能用猜的參數名盲試，站點多半不理會
	// 陌生參數（實測 20 個目標全部回 200、沒有任何 Location，confirmed=0）；
	// 開啟巡站後，送進驗證的是站上真的存在的跳轉入口 —— 那些入口的參數值
	// 會被換成操作者指定的受控端點。
	verifyTargets := targets
	if run.CrawlEnabled {
		_ = h.db.UpdateRedirectVerifyRunCrawl(run.ID, len(targets), 0, "crawl")
		crawlResult := redirect.DiscoverRedirectCandidates(ctx, client, targets, redirect.CrawlOptions{
			MaxPages:     run.CrawlMaxPages,
			MaxDepth:     run.CrawlMaxDepth,
			SameHostOnly: true,
			Timeout:      timeout,
			// 巡站時不把我們自己的受控端點算成「他們注入的」。
			IgnoreInjectionHosts: h.endpointHosts(),
		})
		verifyTargets = crawlResult.Candidates
		_ = h.db.UpdateRedirectVerifyRunCrawl(run.ID, len(targets), len(verifyTargets), "verify")
		// 注入點統計落到批次上：前端才知道「可自動植入幾個」。
		_ = h.db.UpdateRedirectVerifyRunInjections(run.ID, crawlResult.InjectionCount, crawlResult.ThirdPartyInjections, crawlResult.Injections)
		if h.logger != nil {
			h.logger.Info("跳轉驗證巡站完成",
				zap.String("run_id", run.ID),
				zap.Int("seeds", len(targets)),
				zap.Int("candidates", len(verifyTargets)),
				zap.Int("pages_visited", crawlResult.PagesVisited),
				zap.Int("injections", crawlResult.InjectionCount),
				zap.Int("third_party_injections", crawlResult.ThirdPartyInjections),
			)
		}
		if len(verifyTargets) == 0 {
			_ = h.db.FinishRedirectVerifyRun(run.ID, database.RedirectVerifyStatusCompleted,
				"巡站沒有找到帶著跳轉參數的連結，沒有可驗證的入口")
			return
		}
		// 目標總數改成候選數：進度條要反映實際要驗的筆數。
		_ = h.db.UpdateRedirectVerifyRunTotal(run.ID, len(verifyTargets))
	} else {
		_ = h.db.UpdateRedirectVerifyRunCrawl(run.ID, len(targets), 0, "verify")
	}

	results, err := redirect.VerifyTargets(ctx, client, verifyTargets, redirect.BatchOptions{
		Endpoints:   run.Endpoints,
		Param:       run.Param,
		Method:      run.Method,
		Concurrency: run.Concurrency,
		Encoding:    run.Encoding,
		Repeat:      run.Repeat,
	})
	if err != nil && h.logger != nil {
		h.logger.Warn("跳轉驗證批次執行失敗", zap.String("run_id", run.ID), zap.Error(err))
	}

	completed := 0
	confirmed := 0
	for _, result := range results {
		if ctx.Err() != nil && result.Error == "" {
			result.Error = "已取消"
		}
		record := &database.RedirectVerifyResult{
			RunID:       run.ID,
			URL:         result.URL,
			Confirmed:   result.Confirmed,
			Param:       result.Param,
			OwnParam:    result.OwnParam,
			ParamsTried: result.ParamsTried,
			RequestURL:  result.RequestURL,
			Status:      result.Status,
			Location:    result.Location,
			Error:       result.Error,
			// 證據等級與精準度指標一併落地，之後報告不必重算。
			Evidence:    result.Evidence,
			BodyEcho:    result.BodyEcho,
			OwnParamHit: result.OwnParamHit,
			Attempts:    result.Attempts,
			Stable:      result.Stable,
		}
		if result.Confirmed {
			confirmed++
			if run.AutoRecord {
				if vulnID, recordErr := h.recordConfirmedResult(run, record); recordErr != nil {
					record.Error = strings.TrimSpace(record.Error + " " + recordErr.Error())
				} else if vulnID != "" {
					record.VulnerabilityID = vulnID
				}
			}
		}
		if appendErr := h.db.AppendRedirectVerifyResult(record); appendErr != nil && h.logger != nil {
			h.logger.Warn("寫入跳轉驗證結果失敗", zap.String("run_id", run.ID), zap.Error(appendErr))
		}
		completed++
		if h.db != nil {
			_ = h.db.UpdateRedirectVerifyRunProgress(run.ID, completed, confirmed, database.RedirectVerifyStatusRunning)
		}
	}

	status := database.RedirectVerifyStatusCompleted
	message := ""
	if ctx.Err() != nil {
		status = database.RedirectVerifyStatusCancelled
		message = "批次已取消"
	}
	if err := h.db.FinishRedirectVerifyRun(run.ID, status, message); err != nil && h.logger != nil {
		h.logger.Warn("標記跳轉驗證批次結束失敗", zap.String("run_id", run.ID), zap.Error(err))
	}
	if h.logger != nil {
		h.logger.Info("跳轉驗證批次完成",
			zap.String("run_id", run.ID),
			zap.Int("total", run.Total),
			zap.Int("confirmed", confirmed),
			zap.String("status", status),
		)
	}
}

// buildClient 依批次的代理設定建立 HTTP client。
//
// 優先序：明確指定的代理網址 → 平台代理池群組 → 直連。
func (h *RedirectVerifyHandler) buildClient(run *database.RedirectVerifyRun, timeout time.Duration) (*http.Client, error) {
	// 代理憑證只存在記憶體（落庫的是遮蔽版），所以這裡不能拿 run.Proxy 去連線。
	if strings.TrimSpace(run.Proxy) != "" {
		h.mu.Lock()
		proxyURL := h.proxies[run.ID]
		h.mu.Unlock()
		if proxyURL == "" {
			return nil, fmt.Errorf("代理凭证只存在于原始行程，批次无法在重启后继续执行")
		}
		client, err := redirect.NewVerifyClient(proxyURL, timeout)
		if err != nil {
			return nil, err
		}
		return client, nil
	}
	if group := strings.TrimSpace(run.ProxyGroup); group != "" && h.proxyPool != nil {
		return h.proxyPool.ClientGroup(timeout, group), nil
	}
	return &http.Client{Timeout: timeout}, nil
}

// watchCancelFlag 輪詢資料庫的取消旗標，讓跨行程的取消也能生效。
func (h *RedirectVerifyHandler) watchCancelFlag(runID string, cancel context.CancelFunc, stop <-chan struct{}) {
	ticker := time.NewTicker(redirectVerifyCancelPollInterval)
	defer ticker.Stop()
	for {
		select {
		case <-stop:
			return
		case <-ticker.C:
			asked, err := h.db.IsRedirectVerifyRunCancelAsked(runID)
			if err != nil {
				continue
			}
			if asked {
				cancel()
				return
			}
		}
	}
}

// recordConfirmedResult 把驗證成功的結果自動建立成漏洞紀錄（上鍊）。
//
// 紀錄格式由 internal/redirectverify 統一提供，與 MCP 工具那條路徑共用同一份。
func (h *RedirectVerifyHandler) recordConfirmedResult(run *database.RedirectVerifyRun, result *database.RedirectVerifyResult) (string, error) {
	vuln := redirectverify.BuildConfirmedVulnerability(redirectverify.Info{
		RunID:          run.ID,
		Endpoints:      run.Endpoints,
		ProjectID:      run.ProjectID,
		ConversationID: run.ConversationID,
		Source:         "批次受控跳轉驗證",
		Encoding:       run.Encoding,
	}, redirect.BatchTargetResult{
		URL:         result.URL,
		Confirmed:   result.Confirmed,
		Param:       result.Param,
		OwnParam:    result.OwnParam,
		ParamsTried: result.ParamsTried,
		RequestURL:  result.RequestURL,
		Status:      result.Status,
		Location:    result.Location,
		Error:       result.Error,
		Evidence:    result.Evidence,
		BodyEcho:    result.BodyEcho,
		OwnParamHit: result.OwnParamHit,
		Attempts:    result.Attempts,
		Stable:      result.Stable,
	})

	created, err := h.db.CreateVulnerability(vuln)
	if err != nil {
		return "", fmt.Errorf("自动建立漏洞记录失败: %w", err)
	}
	return created.ID, nil
}

// dedupeNonEmptyStrings 去除空白與重複字串，保留輸入順序。
func dedupeNonEmptyStrings(values []string) []string {
	out := make([]string, 0, len(values))
	seen := make(map[string]struct{}, len(values))
	for _, value := range values {
		trimmed := strings.TrimSpace(value)
		if trimmed == "" {
			continue
		}
		if _, exists := seen[trimmed]; exists {
			continue
		}
		seen[trimmed] = struct{}{}
		out = append(out, trimmed)
	}
	return out
}

// buildRedirectVerifyMarkdown 組出批次報告（Markdown）。
func buildRedirectVerifyMarkdown(run *database.RedirectVerifyRun, results []database.RedirectVerifyResult) string {
	var b strings.Builder
	b.WriteString("# 批次受控跳轉驗證報告\n\n")
	b.WriteString(fmt.Sprintf("- 批次 ID: %s\n", run.ID))
	b.WriteString(fmt.Sprintf("- 狀態: %s\n", run.Status))
	b.WriteString(fmt.Sprintf("- 受控端點（跳轉目標）: %s\n", strings.Join(run.Endpoints, ", ")))
	b.WriteString(fmt.Sprintf("- 請求方式: %s\n", run.Method))
	if run.Proxy != "" {
		b.WriteString(fmt.Sprintf("- 代理出口: %s\n", run.Proxy))
	}
	if run.ProxyGroup != "" {
		b.WriteString(fmt.Sprintf("- 代理群組: %s\n", run.ProxyGroup))
	}
	if run.Param != "" {
		b.WriteString(fmt.Sprintf("- 跳轉參數: %s\n", run.Param))
	}
	if run.ProjectID != "" {
		b.WriteString(fmt.Sprintf("- 專案: %s\n", run.ProjectID))
	}
	b.WriteString(fmt.Sprintf("- 建立時間: %s\n", run.CreatedAt.Format("2006-01-02 15:04:05")))
	b.WriteString(fmt.Sprintf("- 目標總數: %d，已完成: %d，確認可跳轉: %d\n\n",
		run.Total, run.Completed, run.Confirmed))

	// 精準度段落：先回答「實不實」，再回答「精不精準」。
	accuracy := redirectverify.ComputeAccuracy(run, results)
	b.WriteString("## 精準度\n\n")
	b.WriteString(fmt.Sprintf("- 真跳轉（Location 指向受控端點）: %d\n", accuracy.LocationEvidence))
	b.WriteString(fmt.Sprintf("- 本文回顯（偽陽性來源，不計入確認）: %d\n", accuracy.BodyEcho))
	b.WriteString(fmt.Sprintf("- 偽陽性率: %s（以「看起來像跳轉」的全部命中為分母）\n",
		redirectverify.FormatPercent(accuracy.FalsePositiveRate)))
	b.WriteString(fmt.Sprintf("- 命中原有跳轉參數: %d（占確認的 %s）\n",
		accuracy.OwnParamHit, redirectverify.FormatPercent(accuracy.OwnParamHitRate)))
	b.WriteString(fmt.Sprintf("- 靠猜測參數名命中: %d（占確認的 %s）\n",
		accuracy.GuessParamHit, redirectverify.FormatPercent(accuracy.GuessParamHitRate)))
	if accuracy.Repeated > 0 {
		b.WriteString(fmt.Sprintf("- 重複複測: %d 個目標、一致 %d 個（穩定率 %s）\n",
			accuracy.Repeated, accuracy.Stable, redirectverify.FormatPercent(accuracy.StabilityRate)))
	} else {
		b.WriteString("- 重複複測: 未啟用（單次命中可能是巧合，開啟 repeat 才量得到穩定度）\n")
	}
	b.WriteString(fmt.Sprintf("- 實際探測次數: %d\n\n", accuracy.Attempts))

	// 注入點：可自動替換成我們受控端點的位置。
	if len(run.Injections) > 0 {
		b.WriteString("## 可自動植入的注入點\n\n")
		b.WriteString("| 型態 | 原始網址（他們塞的） | 頁面 | 站方自有 |\n")
		b.WriteString("| --- | --- | --- | --- |\n")
		for _, point := range run.Injections {
			self := "否（第三方注入）"
			if point.SelfHost {
				self = "是"
			}
			b.WriteString(fmt.Sprintf("| %s | %s | %s | %s |\n",
				point.Kind, point.URL, point.Page, self))
		}
		b.WriteString("\n")
	}

	confirmed := make([]database.RedirectVerifyResult, 0, len(results))
	for _, result := range results {
		if result.Confirmed {
			confirmed = append(confirmed, result)
		}
	}

	b.WriteString("## 確認可跳轉的目標\n\n")
	if len(confirmed) == 0 {
		b.WriteString("（無）\n\n")
	} else {
		b.WriteString("| 目標 URL | 站上原有跳轉參數 | 參數 | 狀態碼 | Location | 漏洞紀錄 |\n")
		b.WriteString("| --- | --- | --- | --- | --- | --- |\n")
		for _, result := range confirmed {
			vuln := result.VulnerabilityID
			if vuln == "" {
				vuln = "—"
			}
			own := result.OwnParam
			if own == "" {
				own = "—"
			}
			b.WriteString(fmt.Sprintf("| %s | %s | %s | %d | %s | %s |\n",
				result.URL, own, result.Param, result.Status, result.Location, vuln))
		}
		b.WriteString("\n")
	}

	b.WriteString("## 全部結果\n\n")
	if len(results) == 0 {
		b.WriteString("（無結果）\n")
		return b.String()
	}
	b.WriteString("| 目標 URL | 結果 | 證據 | 站上原有跳轉參數 | 參數 | 試過的參數數 | 狀態碼 | 穩定 | 錯誤 |\n")
	b.WriteString("| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
	for _, result := range results {
		verdict := "未確認"
		if result.Confirmed {
			verdict = "已確認"
		}
		own := result.OwnParam
		if own == "" {
			own = "—"
		}
		evidence := result.Evidence
		if evidence == "" {
			evidence = "—"
		}
		stable := "—"
		if result.Attempts > 1 {
			stable = "一致"
			if !result.Stable {
				stable = "不一致"
			}
		}
		b.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s | %d | %d | %s | %s |\n",
			result.URL, verdict, evidence, own, result.Param, len(result.ParamsTried), result.Status, stable, result.Error))
	}
	b.WriteString("\n")
	b.WriteString("> 「站上原有跳轉參數」為空代表該目標網址本身沒有跳轉參數，")
	b.WriteString("這筆是用猜的參數名盲試的；「試過的參數數」是實際送出的探測次數（每個參數各送一次）。\n")
	b.WriteString("> 證據欄 `location` = 伺服器真的 3xx 跳轉；`body_echo` = 只是本文回顯受控端點，屬偽陽性來源。\n")
	return b.String()
}

// writeRedirectVerifyCSV 輸出 CSV 報告。
func writeRedirectVerifyCSV(writer interface{ Write([]byte) (int, error) }, run *database.RedirectVerifyRun, results []database.RedirectVerifyResult) error {
	cw := csv.NewWriter(writer)
	header := []string{
		"url", "confirmed", "own_param", "param", "params_tried", "request_url",
		"status", "location", "error", "vulnerability_id",
		"evidence", "body_echo", "own_param_hit", "attempts", "stable",
	}
	if err := cw.Write(header); err != nil {
		return err
	}
	for _, result := range results {
		record := []string{
			result.URL,
			strconv.FormatBool(result.Confirmed),
			result.OwnParam,
			result.Param,
			strings.Join(result.ParamsTried, "|"),
			result.RequestURL,
			strconv.Itoa(result.Status),
			result.Location,
			result.Error,
			result.VulnerabilityID,
			result.Evidence,
			strconv.FormatBool(result.BodyEcho),
			strconv.FormatBool(result.OwnParamHit),
			strconv.Itoa(result.Attempts),
			strconv.FormatBool(result.Stable),
		}
		if err := cw.Write(record); err != nil {
			return err
		}
	}
	cw.Flush()
	return cw.Error()
}
