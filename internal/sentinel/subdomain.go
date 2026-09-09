package sentinel

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

var defaultSubdomainDict = []string{
	"www", "mail", "api", "admin", "portal", "oa", "vpn", "sso", "login", "auth",
	"app", "m", "dev", "test", "staging", "demo", "sample", "sandbox", "beta", "uat",
	"docs", "git", "jenkins", "cloud", "manage", "console", "gateway", "pay", "static", "cdn",
	"bbs", "blog", "forum", "server", "web", "vip", "ops", "monitor",
}

type crtShEntry struct {
	NameValue string `json:"name_value"`
}

// DiscoverHosts 發現目標資產的主機列表（含主域、字典子域、crt.sh 證書透明度發現）
func DiscoverHosts(ctx context.Context, target string, kind string) []AssetItem {
	if kind == "ipv4" {
		// IPv4 目標直接做自身探測
		alive := false
		// 測試常規端口判斷是否存活
		conn, err := net.DialTimeout("tcp", net.JoinHostPort(target, "80"), 1200*time.Millisecond)
		if err == nil {
			alive = true
			_ = conn.Close()
		} else {
			conn, err = net.DialTimeout("tcp", net.JoinHostPort(target, "443"), 1200*time.Millisecond)
			if err == nil {
				alive = true
				_ = conn.Close()
			}
		}

		return []AssetItem{
			{
				ID:       "host-0",
				Host:     target,
				Scope:    "official",
				IP:       target,
				Alive:    alive,
				TLSValid: false,
			},
		}
	}

	// 域名目標
	domain := strings.ToLower(target)
	candidatesMap := make(map[string]bool)

	// 1. 加入主域
	candidatesMap[domain] = true

	// 2. 加入字典前綴
	for _, prefix := range defaultSubdomainDict {
		candidatesMap[prefix+"."+domain] = true
	}

	// 3. 異步嘗試從 crt.sh 獲取證書透明度記錄（超時 5 秒，超時不阻塞掃描）
	crtHosts := queryCrtSh(ctx, domain)
	for _, h := range crtHosts {
		candidatesMap[h] = true
	}

	// 4. 並發 DNS 解析候選主機
	type resolveResult struct {
		host  string
		ip    string
		alive bool
	}

	resultsChan := make(chan resolveResult, len(candidatesMap))
	sem := make(chan struct{}, 20) // 最大 20 並發 DNS 查詢
	var wg sync.WaitGroup

	resolver := net.DefaultResolver

	for host := range candidatesMap {
		wg.Add(1)
		go func(h string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			resolveCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
			defer cancel()

			ips, err := resolver.LookupIPAddr(resolveCtx, h)
			if err == nil && len(ips) > 0 {
				var ipv4 string
				for _, ip := range ips {
					if ip.IP.To4() != nil {
						ipv4 = ip.IP.String()
						break
					}
				}
				if ipv4 == "" {
					ipv4 = ips[0].IP.String()
				}
				resultsChan <- resolveResult{host: h, ip: ipv4, alive: true}
			} else {
				// 主域即時未解析也保留；字典子域未解析且非關鍵則可選擇過濾或標記離線
				resultsChan <- resolveResult{host: h, ip: "", alive: false}
			}
		}(host)
	}

	wg.Wait()
	close(resultsChan)

	var assets []AssetItem
	idx := 0

	for res := range resultsChan {
		// 如果是子域名且解析失敗，跳過未解析的字典碰撞項以保持乾淨清單；但主域始終保留
		if !res.alive && res.host != domain && res.host != "www."+domain {
			continue
		}

		scope := classifyScope(res.host, domain)
		idx++
		assets = append(assets, AssetItem{
			ID:       fmt.Sprintf("asset-%d", idx),
			Host:     res.host,
			Scope:    scope,
			IP:       res.ip,
			Alive:    res.alive,
			TLSValid: false,
		})
	}

	return assets
}

func classifyScope(host, rootDomain string) string {
	if host == rootDomain {
		return "official"
	}
	prefix := strings.TrimSuffix(host, "."+rootDomain)
	switch prefix {
	case "www", "app", "api", "m", "portal", "login", "pay":
		return "product"
	default:
		return "related"
	}
}

func queryCrtSh(ctx context.Context, domain string) []string {
	crtCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	url := fmt.Sprintf("https://crt.sh/?q=%%25.%s&output=json", domain)
	req, err := http.NewRequestWithContext(crtCtx, "GET", url, nil)
	if err != nil {
		return nil
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JySecAI-Sentinel/1.0")

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil || resp.StatusCode != http.StatusOK {
		return nil
	}
	defer resp.Body.Close()

	var entries []crtShEntry
	if err := json.NewDecoder(resp.Body).Decode(&entries); err != nil {
		return nil
	}

	var found []string
	seen := make(map[string]bool)

	for _, entry := range entries {
		lines := strings.Split(entry.NameValue, "\n")
		for _, line := range lines {
			h := strings.TrimSpace(strings.ToLower(line))
			h = strings.TrimPrefix(h, "*.")
			if strings.HasSuffix(h, "."+domain) && !seen[h] {
				seen[h] = true
				found = append(found, h)
			}
		}
	}

	return found
}
