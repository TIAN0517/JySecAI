package redirect

import (
	"context"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"jysecai/internal/forbidden"

	"golang.org/x/net/html"
)

// 自動巡站：走訪站點，找出帶著跳轉參數的連結，作為開放式重定向的驗證候選。
//
// 為什麼只看「連結裡帶跳轉參數」：受控跳轉驗證的證據是伺服器端 3xx 的 Location 標頭，
// 純前端 JS 跳轉（location.href = ...）不會在 Location 標頭裡出現，驗不出來。
// 因此巡站只挑 URL 上真的帶著 url/redirect/next 之類參數的連結。

const (
	// DefaultCrawlMaxPages 是每個種子站點預設最多走訪的頁數。
	DefaultCrawlMaxPages = 20
	// DefaultCrawlMaxDepth 是每個種子站點預設的走訪深度。
	DefaultCrawlMaxDepth = 1
	// DefaultCrawlConcurrency 是巡站預設同時抓取的頁數。
	DefaultCrawlConcurrency = 2
	// DefaultCrawlTimeout 是巡站抓取單頁的預設逾時。
	DefaultCrawlTimeout = 10 * time.Second
	// DefaultCrawlUserAgent 是巡站預設的 User-Agent。
	DefaultCrawlUserAgent = "Mozilla/5.0 (compatible; JySecAI-RedirectVerifier/1.0)"
	// maxCrawlBodyBytes 是巡站最多讀掉的頁面大小；只看開頭足夠解析連結。
	maxCrawlBodyBytes = 2 << 20
)

// CrawlOptions 是巡站選項。
type CrawlOptions struct {
	// MaxPages 是每個種子站點最多走訪的頁數；<=0 時用 DefaultCrawlMaxPages。
	MaxPages int
	// MaxDepth 是每個種子站點的走訪深度；<=0 時用 DefaultCrawlMaxDepth。
	MaxDepth int
	// SameHostOnly 是否只走訪與種子同主機的頁面（預設 true，由呼叫端設定）。
	SameHostOnly bool
	// Timeout 是抓取單頁的逾時。
	Timeout time.Duration
	// Concurrency 是同時抓取的頁數。
	Concurrency int
	// UserAgent 是請求時使用的 UA。
	UserAgent string
	// IgnoreInjectionHosts 是偵測注入點時要忽略的主機。
	//
	// 一定要把我們自己的受控端點放進來 —— 否則「我們自己植入的片段」
	// 會被回報成「他們注入的」，自動植入就會拿自己的東西去替換自己。
	IgnoreInjectionHosts []string
}

// CrawlResult 是巡站結果。
type CrawlResult struct {
	// PagesVisited 是實際走訪的頁數。
	PagesVisited int
	// Candidates 是帶著跳轉參數的候選 URL（去重後）。
	Candidates []string
	// Visited 是走訪過的頁面 URL。
	Visited []string
	// Injections 是頁面裡找到的注入點（「他們塞的」外部網址）。
	Injections []InjectionPoint
	// InjectionCount 是注入點總數（含 SelfHost 的）。
	InjectionCount int
	// ThirdPartyInjections 是指向外部主機的注入點（真正的第三方注入）。
	ThirdPartyInjections int
}

// DiscoverRedirectCandidates 走訪種子站點，找出疑似跳轉入口的候選 URL。
//
// ctx 可中途取消；錯誤不會中斷整批，每個站點各自記錄。
func DiscoverRedirectCandidates(ctx context.Context, client *http.Client, seeds []string, opts CrawlOptions) CrawlResult {
	if ctx == nil {
		ctx = context.Background()
	}
	if opts.MaxPages <= 0 {
		opts.MaxPages = DefaultCrawlMaxPages
	}
	if opts.MaxDepth <= 0 {
		opts.MaxDepth = DefaultCrawlMaxDepth
	}
	if opts.Timeout <= 0 {
		opts.Timeout = DefaultCrawlTimeout
	}
	if opts.Concurrency <= 0 {
		opts.Concurrency = DefaultCrawlConcurrency
	}
	if strings.TrimSpace(opts.UserAgent) == "" {
		opts.UserAgent = DefaultCrawlUserAgent
	}
	if client == nil {
		client = &http.Client{Timeout: opts.Timeout}
	}

	result := CrawlResult{}
	candidateSet := map[string]struct{}{}
	visitedSet := map[string]struct{}{}

	for _, seed := range seeds {
		trimmed := strings.TrimSpace(seed)
		if trimmed == "" {
			continue
		}
		if err := validateTargetURL(trimmed); err != nil {
			continue
		}
		// 巡站也不能走進禁區：種子可能來自情蒐結果，而情蒐結果裡有消防／EPCR 資產。
		if forbidden.Reason("", trimmed, "", trimmed, "") != "" {
			continue
		}
		crawlSeed(ctx, client, trimmed, opts, &result, candidateSet, visitedSet)
	}
	return result
}

// crawlSeed 走訪單一種子站點。
func crawlSeed(ctx context.Context, client *http.Client, seed string, opts CrawlOptions, result *CrawlResult, candidateSet, visitedSet map[string]struct{}) {
	seedHost := hostOf(seed)

	// BFS：每一層是這一輪要走的頁面。
	current := []string{seed}
	for depth := 0; depth <= opts.MaxDepth && len(current) > 0; depth++ {
		jobs := make([]string, 0, len(current))
		for _, page := range current {
			page = strings.TrimSpace(page)
			if page == "" {
				continue
			}
			if _, seen := visitedSet[page]; seen {
				continue
			}
			if result.PagesVisited+len(jobs) >= opts.MaxPages {
				break
			}
			visitedSet[page] = struct{}{}
			jobs = append(jobs, page)
		}
		if len(jobs) == 0 {
			return
		}

		// 併發抓取這一層的頁面。
		//
		// 這裡刻意用「工作索引佇列 + 依索引存結果」，不是把結果塞進 channel：
		// 舊寫法讓每個 worker 都跑完整個 jobs 清單，於是
		//   1. 每個頁面被抓了 workers 次（對外站的請求量倍增）；
		//   2. 結果 channel 容量只有 len(jobs)，但送出總數是 workers×len(jobs)，
		//      而消費者要等 wg.Wait() 之後才開始讀 —— workers≥2 且 jobs≥2 時
		//      必定死鎖，整個巡站永久卡住，連帶 HTTP 請求也 hang 住。
		//
		// 改成索引佇列後：每個頁面只抓一次，結果依索引寫回，不會有容量競爭。
		levelLinks := make([][]string, len(jobs))
		levelInjections := make([][]InjectionPoint, len(jobs))
		jobCh := make(chan int)
		var wg sync.WaitGroup
		workers := opts.Concurrency
		if workers > len(jobs) {
			workers = len(jobs)
		}
		for w := 0; w < workers; w++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for idx := range jobCh {
					scan, err := fetchPageLinks(ctx, client, jobs[idx], opts)
					if err != nil {
						continue
					}
					levelLinks[idx] = scan.links
					levelInjections[idx] = scan.injections
				}
			}()
		}
		for idx := range jobs {
			jobCh <- idx
		}
		close(jobCh)
		wg.Wait()

		next := []string{}
		for _, pageLinks := range levelLinks {
			for _, link := range pageLinks {
				if err := validateTargetURL(link); err != nil {
					continue
				}
				if opts.SameHostOnly && seedHost != "" && !strings.EqualFold(hostOf(link), seedHost) {
					continue
				}
				// 巡出來的連結同樣要過禁區：頁面裡可能連到消防／EPCR 系統。
				if forbidden.Reason("", link, "", link, "") != "" {
					continue
				}
				if IsRedirectParam(redirectParamName(link)) {
					if _, exists := candidateSet[link]; !exists {
						candidateSet[link] = struct{}{}
						result.Candidates = append(result.Candidates, link)
					}
					continue
				}
				if _, seen := visitedSet[link]; !seen {
					next = append(next, link)
				}
			}
		}
		// 收集這一頁的注入點（「他們塞的」外部網址）。
		for _, points := range levelInjections {
			for _, point := range points {
				result.InjectionCount++
				if !point.SelfHost {
					result.ThirdPartyInjections++
				}
				result.Injections = append(result.Injections, point)
			}
		}
		result.PagesVisited += len(jobs)
		result.Visited = append(result.Visited, jobs...)
		current = next
	}
}

// fetchPageLinks 抓取頁面並回傳頁面上的連結（絕對 URL）。
func fetchPageLinks(ctx context.Context, client *http.Client, pageURL string, opts CrawlOptions) (pageScan, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, pageURL, nil)
	if err != nil {
		return pageScan{}, err
	}
	req.Header.Set("User-Agent", opts.UserAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml")

	resp, err := client.Do(req)
	if err != nil {
		return pageScan{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return pageScan{}, nil
	}

	base, err := url.Parse(pageURL)
	if err != nil {
		return pageScan{}, err
	}

	// 先把本文收進來（上限 maxCrawlBodyBytes）：連結與注入點都要從同一份本文解析。
	body, err := io.ReadAll(io.LimitReader(resp.Body, maxCrawlBodyBytes))
	if err != nil && len(body) == 0 {
		return pageScan{}, err
	}

	var links []string
	tokenizer := html.NewTokenizer(strings.NewReader(string(body)))
	for {
		tokenType := tokenizer.Next()
		if tokenType == html.ErrorToken {
			break
		}
		if tokenType != html.StartTagToken && tokenType != html.SelfClosingTagToken {
			continue
		}
		name, hasAttr := tokenizer.TagName()
		tag := strings.ToLower(string(name))
		if tag != "a" && tag != "area" && tag != "link" && tag != "form" {
			continue
		}
		for hasAttr {
			key, value, more := tokenizer.TagAttr()
			hasAttr = more
			attrName := strings.ToLower(string(key))
			if (tag == "form" && attrName != "action") || (tag != "form" && attrName != "href") {
				continue
			}
			resolved, ok := resolveLink(base, string(value))
			if !ok {
				continue
			}
			links = append(links, resolved)
		}
	}

	// 順便找出頁面裡「他們塞的」注入點。
	injections := ScanInjections(pageURL, body, InjectionScanOptions{
		SelfHost:    hostOf(pageURL),
		IgnoreHosts: opts.IgnoreInjectionHosts,
	})

	return pageScan{links: links, injections: injections}, nil
}

// pageScan 是單一頁面的掃描結果。
type pageScan struct {
	links      []string
	injections []InjectionPoint
}

// resolveLink 把頁面上的相對連結解析成絕對 URL；非 http(s) 的連結回傳 false。
func resolveLink(base *url.URL, raw string) (string, bool) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return "", false
	}
	parsed, err := url.Parse(trimmed)
	if err != nil {
		return "", false
	}
	resolved := base.ResolveReference(parsed)
	if resolved.Scheme != "http" && resolved.Scheme != "https" {
		return "", false
	}
	if resolved.Host == "" {
		return "", false
	}
	return resolved.String(), true
}

// redirectParamName 取出 URL 裡第一個屬於跳轉參數的 query key。
func redirectParamName(raw string) string {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil {
		return ""
	}
	for key := range parsed.Query() {
		if IsRedirectParam(key) {
			return key
		}
	}
	return ""
}

// hostOf 取出 URL 的主機名。
func hostOf(raw string) string {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || parsed.Host == "" {
		return ""
	}
	return parsed.Hostname()
}
