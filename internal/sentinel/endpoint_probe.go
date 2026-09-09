package sentinel

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"regexp"
	"strings"
	"time"
)

var titleRegex = regexp.MustCompile(`(?i)<title[^>]*>([^<]+)</title>`)

type probePathDef struct {
	Path     string
	Tags     []string
	Category string // "login" | "test" | "sample" | "api"
}

var commonProbePaths = []probePathDef{
	// 登錄入口
	{Path: "/login", Tags: []string{"login"}, Category: "login"},
	{Path: "/admin", Tags: []string{"admin", "login"}, Category: "login"},
	{Path: "/admin/login", Tags: []string{"admin", "login"}, Category: "login"},
	{Path: "/signin", Tags: []string{"login"}, Category: "login"},
	{Path: "/auth/login", Tags: []string{"auth", "login"}, Category: "login"},
	{Path: "/portal", Tags: []string{"portal", "login"}, Category: "login"},
	{Path: "/manage", Tags: []string{"admin", "manage"}, Category: "login"},
	{Path: "/console", Tags: []string{"admin", "console"}, Category: "login"},
	{Path: "/mail", Tags: []string{"mail", "login"}, Category: "login"},
	{Path: "/sso/login", Tags: []string{"sso", "login"}, Category: "login"},
	{Path: "/api/login", Tags: []string{"api", "login"}, Category: "login"},

	// 測試與樣例系統
	{Path: "/test", Tags: []string{"test"}, Category: "test"},
	{Path: "/demo", Tags: []string{"demo", "sample"}, Category: "sample"},
	{Path: "/sample", Tags: []string{"sample"}, Category: "sample"},
	{Path: "/sandbox", Tags: []string{"sandbox", "test"}, Category: "test"},
	{Path: "/staging", Tags: []string{"staging", "test"}, Category: "test"},
	{Path: "/dev", Tags: []string{"dev", "test"}, Category: "test"},

	// API 文檔與健康監控
	{Path: "/swagger-ui.html", Tags: []string{"api", "doc"}, Category: "api"},
	{Path: "/swagger/index.html", Tags: []string{"api", "doc"}, Category: "api"},
	{Path: "/api-docs", Tags: []string{"api", "doc"}, Category: "api"},
	{Path: "/actuator/health", Tags: []string{"monitor", "actuator"}, Category: "api"},
	{Path: "/actuator/env", Tags: []string{"monitor", "actuator"}, Category: "api"},
}

// ProbeEndpoints 針對在線主機進行非侵入式路徑暴露面排查（含 SPA 404 回退防誤報機制）
func ProbeEndpoints(ctx context.Context, host string, scheme string, port int) []EndpointItem {
	var baseURL string
	if (scheme == "http" && port == 80) || (scheme == "https" && port == 443) {
		baseURL = fmt.Sprintf("%s://%s", scheme, host)
	} else {
		baseURL = fmt.Sprintf("%s://%s:%d", scheme, host, port)
	}

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	defer tr.CloseIdleConnections()

	client := &http.Client{
		Timeout:   2500 * time.Millisecond,
		Transport: tr,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 3 {
				return http.ErrUseLastResponse
			}
			return nil
		},
	}

	// 1. 先探測隨機不存在的路徑，判斷是否存在 SPA 200 回退（SPA 404 Fallback）
	randomPath := fmt.Sprintf("/__sentinel_404_%d__", rand.Int63n(10000000))
	spaFallbackLen := -1
	spaFallbackTitle := ""

	randomReq, err := http.NewRequestWithContext(ctx, "GET", baseURL+randomPath, nil)
	if err == nil {
		randomReq.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JySecAI-Sentinel/1.0")
		if resp, err := client.Do(randomReq); err == nil {
			if resp.StatusCode == http.StatusOK {
				body, _ := io.ReadAll(io.LimitReader(resp.Body, 8192))
				spaFallbackLen = len(body)
				spaFallbackTitle = extractTitle(string(body))
			}
			_ = resp.Body.Close()
		}
	}

	// 2. 依次排查各路徑
	var items []EndpointItem
	idx := 0

	for _, p := range commonProbePaths {
		select {
		case <-ctx.Done():
			return items
		default:
		}

		url := baseURL + p.Path
		req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			continue
		}
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JySecAI-Sentinel/1.0")

		resp, err := client.Do(req)
		if err != nil {
			continue
		}

		bodyBytes, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		_ = resp.Body.Close()

		statusCode := resp.StatusCode
		// 只記錄成功或跳轉、認證相關代碼
		if statusCode != 200 && statusCode != 301 && statusCode != 302 && statusCode != 401 && statusCode != 403 {
			continue
		}

		bodyStr := string(bodyBytes)
		title := extractTitle(bodyStr)
		if title == "" && resp.Header.Get("Location") != "" {
			title = fmt.Sprintf("Redirect -> %s", resp.Header.Get("Location"))
		}

		isSpa := false
		if statusCode == 200 && spaFallbackLen >= 0 {
			// 如果 404 隨機路徑也返回 200，且頁面長度差異在 32 字節以內且標題一致，判定為 SPA 路由回退
			diff := len(bodyBytes) - spaFallbackLen
			if diff < 0 {
				diff = -diff
			}
			if diff <= 32 && (title == spaFallbackTitle || spaFallbackTitle != "") {
				isSpa = true
			}
		}

		idx++
		snippet := ""
		if len(bodyStr) > 0 {
			cleanSnippet := strings.ReplaceAll(strings.ReplaceAll(bodyStr, "\n", " "), "\r", "")
			if len(cleanSnippet) > 100 {
				snippet = cleanSnippet[:100] + "..."
			} else {
				snippet = cleanSnippet
			}
		}

		items = append(items, EndpointItem{
			ID:          fmt.Sprintf("ep-%d", idx),
			URL:         url,
			Status:      statusCode,
			Tags:        p.Tags,
			SPAFallback: isSpa,
			Title:       title,
			Snippet:     snippet,
		})
	}

	return items
}

func extractTitle(body string) string {
	m := titleRegex.FindStringSubmatch(body)
	if len(m) > 1 {
		return strings.TrimSpace(m[1])
	}
	return ""
}
