// Command scan-runner — 指定 DNS／URL 的併發探測器（跑到次數上限才停）
//
// 為什麼需要這一支
// ----------------
// 平台的既有掃描（Web 安全掃描／批次任務）都是「對一個起點掃一次就結束」，
// 沒有「持續跑到預算用完」的執行器，也沒有「指定 DNS 解析器」的入口。
// 而實際取證時要的是：給一個網域或 URL，**一直掃到預算用完**，
// 過程中任何錯誤都不能中斷整輪，最後把結果直接灌進提取記錄庫。
//
// 核心語意（這是重點，不要改掉）
// --------------------------------
//  1. 併發：固定數量的 worker 從任務佇列取件，沒有「一遇到錯就停」的邏輯。
//  2. 不提前停：單一請求失敗只會被記錄，掃描繼續。
//  3. 只在預算觸底才停：
//     --max-requests  請求數上限（觸底即停，最常見的停止條件）
//     --max-duration  時間上限（保險，避免無盡掃）
//     任一先到就停，並在報告裡寫明 stop reason。
//  4. 任務集用完但預算還有 → 進入下一輪（--cycle，預設開），
//     所以「不停止」是真的不停止，直到次數上限。
//
// 產出（可直接 records-ingest 進平台）
// ------------------------------------
//
//	scan_raw.jsonl          每一次嘗試一行（目標、狀態、錯誤、耗時、位元組數）
//	payload_asset.json      asset 型別：主機／埠／協定／服務／標題
//	payload_endpoints.json  generic 型別：主機／路徑／狀態／標題
//	scan_report.md          摘要（嘗試數、唯一端點、狀態分布、錯誤、停止原因）
//	SHA256SUMS              雜湊鏈
//
// 用法
// ----
//
//	# 單一 URL
//	scan-runner --url https://target.tld/ --paths /,/api,/admin --max-requests 500
//
//	# 指定 DNS 解析器解析網域（多 A 記錄全掃）
//	scan-runner --dns target.tld --dns-server 8.8.8.8:53 --ports 80,443 \
//	            --concurrency 16 --max-requests 5000 --max-duration 10m
//
//	# 走代理出口
//	scan-runner --url https://target.tld/ --proxy socks5h://user:pass@host:1080 \
//	            --max-requests 200
package main

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type attempt struct {
	Round     int    `json:"round"`
	Host      string `json:"host"`
	IP        string `json:"ip"`
	Port      int    `json:"port"`
	Scheme    string `json:"scheme"`
	Path      string `json:"path"`
	URL       string `json:"url"`
	Status    int    `json:"status,omitempty"`
	Title     string `json:"title,omitempty"`
	Bytes     int64  `json:"bytes,omitempty"`
	Server    string `json:"server,omitempty"`
	LatencyMS int64  `json:"latency_ms"`
	Error     string `json:"error,omitempty"`
	At        string `json:"at"`
}

type task struct {
	host   string
	ip     string
	port   int
	scheme string
	path   string
}

var (
	titleRe = regexp.MustCompile(`(?is)<title[^>]*>(.*?)</title>`)
)

func main() {
	var (
		urlsFlag    = flag.String("url", "", "起始 URL（可逗號分隔多個）")
		dnsFlag     = flag.String("dns", "", "要解析的網域名稱（可逗號分隔）")
		dnsServer   = flag.String("dns-server", "", "指定 DNS 解析器，例如 8.8.8.8:53")
		hostsFile   = flag.String("hosts-file", "", "主機清單檔（每行一個）")
		hostsFlag   = flag.String("hosts", "", "額外主機（可逗號分隔）")
		portsFlag   = flag.String("ports", "80,443", "要掃的埠")
		pathsFlag   = flag.String("paths", "", "路徑字典（逗號分隔）；留空用內建常見路徑")
		pathsFile   = flag.String("paths-file", "", "路徑字典檔（每行一個）")
		concurrency = flag.Int("concurrency", 8, "併發 worker 數")
		maxRequests = flag.Int("max-requests", 200, "請求數上限（觸底即停）")
		maxDuration = flag.Duration("max-duration", 10*time.Minute, "時間上限（保險）")
		reqTimeout  = flag.Duration("timeout", 10*time.Second, "單一請求逾時")
		outDir      = flag.String("out", "scan-out", "輸出目錄")
		proxyFlag   = flag.String("proxy", "", "出口代理，例如 socks5h://user:pass@host:port")
		insecure    = flag.Bool("insecure", false, "略過 TLS 憑證驗證")
		noCycle     = flag.Bool("no-cycle", false, "任務集用完就停（預設是繼續下一輪直到次數上限）")
		verbose     = flag.Bool("v", false, "逐筆輸出")
	)
	flag.Parse()

	if err := run(*urlsFlag, *dnsFlag, *dnsServer, *hostsFile, *hostsFlag,
		*portsFlag, *pathsFlag, *pathsFile, *concurrency, *maxRequests, *maxDuration,
		*reqTimeout, *outDir, *proxyFlag, *insecure, !*noCycle, *verbose); err != nil {
		fmt.Fprintln(os.Stderr, "scan-runner:", err)
		os.Exit(1)
	}
}

// ------------------------------------------------------------------ 目標展開

type target struct {
	host   string
	ip     string
	port   int
	scheme string
}

func resolveHosts(names []string, dnsServer string) (map[string][]string, error) {
	out := map[string][]string{}
	resolver := net.DefaultResolver
	if dnsServer != "" {
		server := dnsServer
		if !strings.Contains(server, ":") {
			server = net.JoinHostPort(server, "53")
		}
		resolver = &net.Resolver{
			PreferGo: true,
			Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
				d := net.Dialer{Timeout: 5 * time.Second}
				return d.DialContext(ctx, network, server)
			},
		}
	}
	for _, n := range names {
		n = strings.TrimSpace(n)
		if n == "" {
			continue
		}
		addrs, err := resolver.LookupHost(context.Background(), n)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[dns] %s 解析失敗: %v\n", n, err)
			continue
		}
		sort.Strings(addrs)
		out[n] = addrs
		fmt.Fprintf(os.Stderr, "[dns] %s → %v\n", n, addrs)
	}
	return out, nil
}

func buildTargets(urls, dnsNames, dnsServer, hostsFile, hostsFlag, portsFlag string) ([]target, error) {
	ports := []int{}
	for _, p := range strings.Split(portsFlag, ",") {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		var n int
		if _, err := fmt.Sscanf(p, "%d", &n); err == nil && n > 0 && n < 65536 {
			ports = append(ports, n)
		}
	}
	if len(ports) == 0 {
		ports = []int{80, 443}
	}

	var set []target
	seen := map[string]bool{}
	add := func(host, ip string, port int, scheme string) {
		key := fmt.Sprintf("%s|%s|%d|%s", host, ip, port, scheme)
		if seen[key] {
			return
		}
		seen[key] = true
		set = append(set, target{host: host, ip: ip, port: port, scheme: scheme})
	}

	// URL 來源的目標：主機 + 路徑基準
	urlHosts := map[string]string{}
	for _, u := range splitList(urls) {
		pu, err := url.Parse(u)
		if err != nil {
			return nil, fmt.Errorf("URL 解析失敗 %q: %w", u, err)
		}
		if pu.Hostname() == "" {
			return nil, fmt.Errorf("URL 沒有主機: %q", u)
		}
		scheme := pu.Scheme
		if scheme == "" {
			scheme = "https"
		}
		port := 443
		if scheme == "http" {
			port = 80
		}
		if ps := pu.Port(); ps != "" {
			fmt.Sscanf(ps, "%d", &port)
		}
		urlHosts[pu.Hostname()] = scheme
		add(pu.Hostname(), "", port, scheme)
	}

	// 額外主機
	extra := splitList(hostsFlag)
	if hostsFile != "" {
		b, err := os.ReadFile(hostsFile)
		if err != nil {
			return nil, err
		}
		for _, l := range strings.Split(string(b), "\n") {
			if l = strings.TrimSpace(l); l != "" && !strings.HasPrefix(l, "#") {
				extra = append(extra, l)
			}
		}
	}

	// DNS 解析
	names := splitList(dnsNames)
	resolved, err := resolveHosts(names, dnsServer)
	if err != nil {
		return nil, err
	}
	for name, ips := range resolved {
		scheme := urlHosts[name]
		if scheme == "" {
			scheme = "https"
		}
		for _, p := range ports {
			for _, ip := range ips {
				add(name, ip, p, scheme)
			}
		}
	}

	// 額外主機（不解析，直接用主機名）
	for _, h := range extra {
		scheme := urlHosts[h]
		if scheme == "" {
			scheme = "https"
		}
		for _, p := range ports {
			add(h, "", p, scheme)
		}
	}
	return set, nil
}

func splitList(s string) []string {
	out := []string{}
	for _, p := range strings.Split(s, ",") {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}

var builtinPaths = []string{
	"/", "/robots.txt", "/sitemap.xml", "/.well-known/security.txt",
	"/api", "/api/", "/api/v1", "/api/v2", "/admin", "/admin/", "/administrator",
	"/login", "/signin", "/logout", "/register", "/auth", "/oauth", "/token",
	"/swagger", "/swagger/", "/swagger/index.html", "/swagger/v1/swagger.json",
	"/openapi.json", "/api-docs", "/graphql", "/graphiql", "/actuator",
	"/health", "/healthz", "/status", "/metrics", "/info", "/debug",
	"/config", "/configuration", "/env", "/.env", "/settings",
	"/console", "/dashboard", "/panel", "/manager", "/wp-admin", "/phpmyadmin",
	"/server-status", "/server-info", "/trace.axd", "/elmah.axd",
	"/login.jsp", "/index.jsp", "/index.html", "/default.aspx",
	"/backup", "/backup.zip", "/dump.sql", "/db", "/database",
	"/.git/HEAD", "/.git/config", "/.svn/entries", "/.DS_Store",
	"/wp-content", "/uploads", "/upload", "/files", "/download",
	"/user", "/users", "/customer", "/customers", "/member", "/members",
	"/product", "/products", "/order", "/orders", "/payment", "/payments",
	"/search", "/query", "/report", "/reports", "/stat", "/stats",
}

func buildPaths(pathsFlag, pathsFile string) ([]string, error) {
	if pathsFile != "" {
		b, err := os.ReadFile(pathsFile)
		if err != nil {
			return nil, err
		}
		out := []string{}
		for _, l := range strings.Split(string(b), "\n") {
			if l = strings.TrimSpace(l); l != "" && !strings.HasPrefix(l, "#") {
				out = append(out, l)
			}
		}
		if len(out) > 0 {
			return out, nil
		}
	}
	if p := splitList(pathsFlag); len(p) > 0 {
		return p, nil
	}
	return builtinPaths, nil
}

// ------------------------------------------------------------------ 主流程

func run(urls, dnsNames, dnsServer, hostsFile, hostsFlag, portsFlag, pathsFlag, pathsFile string,
	concurrency, maxRequests int, maxDuration, reqTimeout time.Duration,
	outDir, proxyFlag string, insecure, cycle, verbose bool) error {

	if concurrency < 1 {
		concurrency = 1
	}
	if maxRequests < 1 {
		maxRequests = 1
	}
	if maxDuration <= 0 {
		maxDuration = 24 * time.Hour
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return err
	}

	targets, err := buildTargets(urls, dnsNames, dnsServer, hostsFile, hostsFlag, portsFlag)
	if err != nil {
		return err
	}
	paths, err := buildPaths(pathsFlag, pathsFile)
	if err != nil {
		return err
	}
	if len(targets) == 0 {
		return fmt.Errorf("沒有任何目標：請給 --url 或 --dns 或 --hosts")
	}

	// 代理
	tr := &http.Transport{
		MaxIdleConns:        concurrency * 2,
		MaxIdleConnsPerHost: concurrency,
		IdleConnTimeout:     30 * time.Second,
		TLSHandshakeTimeout: 10 * time.Second,
	}
	if proxyFlag != "" {
		pu, err := url.Parse(proxyFlag)
		if err != nil {
			return fmt.Errorf("proxy 解析失敗: %w", err)
		}
		tr.Proxy = http.ProxyURL(pu)
	}
	if insecure {
		tr.TLSClientConfig = insecureTLS()
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   reqTimeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 3 {
				return http.ErrUseLastResponse
			}
			return nil
		},
	}

	deadline := time.Now().Add(maxDuration)
	var used int64
	var stopped atomic.Value
	stopReason := "task_queue_exhausted"
	var stopMu sync.Mutex
	setStop := func(reason string) {
		stopMu.Lock()
		defer stopMu.Unlock()
		if _, loaded := stopped.Load().(string); !loaded {
			stopped.Store(reason)
			stopReason = reason
		}
	}

	taskCh := make(chan task, 256)
	results := make(chan attempt, 512)
	var wg sync.WaitGroup

	// 任務生產者：任務集用完且預算還有 → 下一輪
	// 注意：results 由主流程在 worker 全數結束後才 close，
	// 生產者絕不能自己 close（否則 worker 會 send on closed channel）。
	go func() {
		defer close(taskCh)
		round := 1
		for {
			for _, tg := range targets {
				for _, p := range paths {
					if atomic.LoadInt64(&used) >= int64(maxRequests) || time.Now().After(deadline) {
						return
					}
					select {
					case taskCh <- task{host: tg.host, ip: tg.ip, port: tg.port, scheme: tg.scheme, path: p}:
					case <-time.After(50 * time.Millisecond):
						if atomic.LoadInt64(&used) >= int64(maxRequests) || time.Now().After(deadline) {
							return
						}
					}
				}
			}
			if !cycle {
				return
			}
			round++
			if round > 1000 { // 安全上限
				return
			}
		}
	}()

	// worker：失敗只記錄，繼續下一件
	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for t := range taskCh {
				if atomic.LoadInt64(&used) >= int64(maxRequests) || time.Now().After(deadline) {
					continue
				}
				n := atomic.AddInt64(&used, 1)
				if n > int64(maxRequests) {
					atomic.AddInt64(&used, -1)
					continue
				}
				at := probe(client, t, reqTimeout)
				if verbose {
					fmt.Fprintf(os.Stderr, "[%d] %s status=%d %dms %s\n",
						n, at.URL, at.Status, at.LatencyMS, at.Error)
				}
				select {
				case results <- at:
				case <-time.After(2 * time.Second):
				}
				if atomic.LoadInt64(&used) >= int64(maxRequests) {
					setStop("max_requests")
					break
				}
				if time.Now().After(deadline) {
					setStop("max_duration")
					break
				}
			}
		}()
	}

	// 收集
	rawFile, err := os.Create(filepath.Join(outDir, "scan_raw.jsonl"))
	if err != nil {
		return err
	}
	defer rawFile.Close()
	enc := json.NewEncoder(rawFile)

	all := []attempt{}
	endpoints := map[string]attempt{}
	hosts := map[string]attempt{}
	statusCount := map[int]int{}
	errCount := map[string]int{}
	totalBytes := int64(0)

	done := make(chan struct{})
	go func() {
		defer close(done)
		for at := range results {
			_ = enc.Encode(at)
			all = append(all, at)
			if at.Error != "" {
				errCount[at.Error]++
				continue
			}
			statusCount[at.Status]++
			totalBytes += at.Bytes
			epKey := fmt.Sprintf("%s|%s|%d", at.Host, at.Path, at.Port)
			endpoints[epKey] = at
			hKey := fmt.Sprintf("%s|%d", at.Host, at.Port)
			if old, ok := hosts[hKey]; !ok || len(at.Title) > len(old.Title) {
				hosts[hKey] = at
			}
		}
	}()

	wg.Wait()
	close(results)
	<-done
	rawFile.Close()

	if atomic.LoadInt64(&used) >= int64(maxRequests) {
		setStop("max_requests")
	} else if time.Now().After(deadline) {
		setStop("max_duration")
	}

	// ---- payload：asset ----
	assetRecs := []map[string]any{}
	for k, at := range hosts {
		parts := strings.SplitN(k, "|", 2)
		port := 0
		fmt.Sscanf(parts[1], "%d", &port)
		service := guessService(at.Scheme, at.Server, at.Title)
		assetRecs = append(assetRecs, map[string]any{
			"key":   k,
			"title": at.Host,
			"fields": map[string]string{
				"host": at.Host, "port": fmt.Sprintf("%d", port),
				"protocol": at.Scheme, "service": service,
				"product": "", "version": "",
				"title": at.Title, "source": "scan-runner", "confidence": "verified",
			},
			"evidence": map[string]any{"source": "scan-runner", "url": at.URL,
				"status": at.Status, "bytes": at.Bytes},
			"extracted_at": nowISO(),
		})
	}
	sort.Slice(assetRecs, func(i, j int) bool {
		return fmt.Sprint(assetRecs[i]["key"]) < fmt.Sprint(assetRecs[j]["key"])
	})
	writeJSON(filepath.Join(outDir, "payload_asset.json"), map[string]any{
		"type_id": "asset", "dataset": "scan_runner", "source": "scan-runner",
		"records": assetRecs,
	})

	// ---- payload：端點 ----
	epRecs := []map[string]any{}
	for k, at := range endpoints {
		parts := strings.SplitN(k, "|", 3)
		port := 0
		fmt.Sscanf(parts[2], "%d", &port)
		epRecs = append(epRecs, map[string]any{
			"key":   k,
			"title": at.Host + at.Path,
			"fields": map[string]string{
				"host": at.Host, "path": at.Path, "method": "GET",
				"status": fmt.Sprintf("%d", at.Status), "source": "scan-runner",
				"category": "scan", "note": at.URL,
				"scheme": at.Scheme, "origin": "scan-runner",
				"bytes": fmt.Sprintf("%d", at.Bytes),
			},
			"evidence": map[string]any{"source": "scan-runner", "url": at.URL,
				"server": at.Server, "latency_ms": at.LatencyMS},
			"extracted_at": nowISO(),
		})
	}
	sort.Slice(epRecs, func(i, j int) bool {
		return fmt.Sprint(epRecs[i]["key"]) < fmt.Sprint(epRecs[j]["key"])
	})
	writeJSON(filepath.Join(outDir, "payload_endpoints.json"), map[string]any{
		"type_id": "generic", "dataset": "scan_runner", "source": "scan-runner",
		"records": epRecs,
	})

	// ---- 報告 ----
	var sb strings.Builder
	sb.WriteString("# scan-runner 掃描報告\n\n")
	sb.WriteString(fmt.Sprintf("- 產出時間：%s\n", nowISO()))
	sb.WriteString(fmt.Sprintf("- 停止原因：**%s**（%s）\n", stopReason, explainStop(stopReason)))
	sb.WriteString(fmt.Sprintf("- 目標數：%d（主機×埠）　路徑字典：%d 條\n", len(targets), len(paths)))
	sb.WriteString(fmt.Sprintf("- 併發 worker：%d　請求上限：%d　時間上限：%s\n", concurrency, maxRequests, maxDuration))
	sb.WriteString(fmt.Sprintf("- 實際嘗試：**%d** 次（唯一端點 %d、主機 %d）\n", len(all), len(endpoints), len(hosts)))
	sb.WriteString(fmt.Sprintf("- 回應位元組合計：%d\n\n", totalBytes))
	sb.WriteString("## 狀態碼分布\n\n| 狀態 | 數量 |\n|---|---|\n")
	keys := []int{}
	for k := range statusCount {
		keys = append(keys, k)
	}
	sort.Ints(keys)
	for _, k := range keys {
		sb.WriteString(fmt.Sprintf("| %d | %d |\n", k, statusCount[k]))
	}
	if len(errCount) > 0 {
		sb.WriteString("\n## 錯誤（不中斷掃描，只記錄）\n\n| 錯誤 | 次數 |\n|---|---|\n")
		ek := []string{}
		for k := range errCount {
			ek = append(ek, k)
		}
		sort.Strings(ek)
		for _, k := range ek {
			sb.WriteString(fmt.Sprintf("| %s | %d |\n", k, errCount[k]))
		}
	}
	sb.WriteString("\n## 入庫\n\n```bash\n")
	sb.WriteString(fmt.Sprintf("records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload %s\n",
		filepath.Join(outDir, "payload_asset.json")))
	sb.WriteString(fmt.Sprintf("records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload %s\n",
		filepath.Join(outDir, "payload_endpoints.json")))
	sb.WriteString("```\n")
	os.WriteFile(filepath.Join(outDir, "scan_report.md"), []byte(sb.String()), 0o644)

	// ---- 雜湊 ----
	sumPath := filepath.Join(outDir, "SHA256SUMS")
	files := []string{}
	entries, _ := os.ReadDir(outDir)
	for _, e := range entries {
		if e.Name() == "SHA256SUMS" {
			continue
		}
		files = append(files, e.Name())
	}
	sort.Strings(files)
	var sum strings.Builder
	for _, f := range files {
		b, _ := os.ReadFile(filepath.Join(outDir, f))
		h := sha256.Sum256(b)
		sum.WriteString(hex.EncodeToString(h[:]) + "  " + f + "\n")
	}
	os.WriteFile(sumPath, []byte(sum.String()), 0o644)

	fmt.Printf("嘗試 %d 次｜唯一端點 %d｜主機 %d｜停止原因 %s\n", len(all), len(endpoints), len(hosts), stopReason)
	fmt.Printf("→ %s\n", outDir)
	return nil
}

func explainStop(reason string) string {
	switch reason {
	case "max_requests":
		return "已達請求數上限"
	case "max_duration":
		return "已達時間上限"
	default:
		return "任務集已用完（加 --no-cycle 才會這樣停；預設會續掃到次數上限）"
	}
}

func probe(client *http.Client, t task, timeout time.Duration) attempt {
	host := t.host
	port := t.port
	u := fmt.Sprintf("%s://%s%s", t.scheme, net.JoinHostPort(host, fmt.Sprintf("%d", port)), t.path)
	if t.ip != "" {
		u = fmt.Sprintf("%s://%s%s", t.scheme, net.JoinHostPort(t.ip, fmt.Sprintf("%d", port)), t.path)
	}
	start := time.Now()
	req, err := http.NewRequest(http.MethodGet, u, nil)
	if err != nil {
		return attempt{URL: u, Error: err.Error(), At: nowISO()}
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; JySecAI-scan-runner/1.0)")
	req.Header.Set("Accept", "*/*")
	resp, err := client.Do(req)
	lat := time.Since(start).Milliseconds()
	if err != nil {
		msg := err.Error()
		if len(msg) > 160 {
			msg = msg[:160]
		}
		return attempt{Host: host, IP: t.ip, Port: port, Scheme: t.scheme, Path: t.path,
			URL: u, Error: msg, LatencyMS: lat, At: nowISO()}
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 512*1024))
	title := ""
	if m := titleRe.FindSubmatch(body); len(m) == 2 {
		title = strings.TrimSpace(strings.Trim(string(m[1]), " \t\r\n"))
		if len(title) > 200 {
			title = title[:200]
		}
	}
	return attempt{Host: host, IP: t.ip, Port: port, Scheme: t.scheme, Path: t.path,
		URL: u, Status: resp.StatusCode, Title: title, Bytes: int64(len(body)),
		Server: resp.Header.Get("Server"), LatencyMS: lat, At: nowISO()}
}

func guessService(scheme, server, title string) string {
	s := strings.ToLower(server + " " + title)
	switch {
	case strings.Contains(s, "nginx"):
		return "nginx"
	case strings.Contains(s, "apache"):
		return "apache"
	case strings.Contains(s, "iis"):
		return "iis"
	case strings.Contains(s, "cloudflare"):
		return "cloudflare"
	case scheme == "https":
		return "https"
	default:
		return "http"
	}
}

func writeJSON(path string, obj any) {
	b, _ := json.MarshalIndent(obj, "", " ")
	os.WriteFile(path, b, 0o644)
}

func nowISO() string {
	return time.Now().UTC().Format(time.RFC3339)
}

// insecureTLS 略過憑證驗證（只在授權靶站且對方自簽憑證時使用）。
func insecureTLS() *tls.Config {
	return &tls.Config{InsecureSkipVerify: true}
}
