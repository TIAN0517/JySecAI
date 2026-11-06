package attackchain

import (
	"net"
	"net/url"
	"strings"

	"jysecai/internal/database"
)

// 攻擊鏈沉淀（PromoteToProject）建立的所有 fact_key 一律掛在目標 DNS 下。
//
// 命名格式：
//
//	target/<dns>            目標節點
//	finding/<dns>-<slug>    發現節點
//	chain/<dns>-<slug>      動作節點
//
// 為什麼必須掛 DNS（三個真實會出事的地方）：
//
//  1. 同一個目標在多次委任中要落在同一組 key 上。用 AI 生成的標籤當 key，
//     「example.com 存在 SQL 注入」這種標籤每次措辭都不同 —— 事實會碎成幾十筆
//     看起來不同、其實是同一件事的記錄。
//  2. 同一個專案裡不同目標的 slug 很容易撞名（都叫 login-sqli）。
//     掛上 DNS 之後命名空間就分開了。
//  3. fact_key 會出現在報告、專案圖譜與稽核軌跡裡，必須人看得懂。
//
// 拿不到 DNS 時退回舊行為（只用 slug），不讓這條路徑失敗 ——
// 命名不統一是問題，寫不進資料是更大的問題。

// promoteTargetDNSFallback 找不到 DNS 時的命名空間前綴，避免 key 變成空字串。
const promoteTargetDNSFallback = "unknown-target"

// resolvePromoteTargetDNS 找出這條攻擊鏈的目標 DNS。
//
// 來源依可信度排序：攻擊鏈的目標節點 → 對話的漏洞目標 → 專案資產的 domain。
// IP 不算 DNS：命名要能跨委任保持穩定，IP 會變、DNS 不會。
// 多個候選時取出現次最多的那個 —— 那通常就是本次委任的主目標。
func resolvePromoteTargetDNS(db *database.DB, projectID, conversationID string, nodes []Node) string {
	counts := map[string]int{}
	order := []string{}
	add := func(host string) {
		host = normalizePromoteDNS(host)
		if host == "" {
			return
		}
		if _, ok := counts[host]; !ok {
			order = append(order, host)
		}
		counts[host]++
	}

	// 1) 攻擊鏈自己的目標節點最可信 —— 那是這條鏈明確指認的目標。
	for _, n := range nodes {
		if strings.EqualFold(strings.TrimSpace(n.Type), "target") {
			add(extractPromoteHost(n.Label))
		}
	}

	if db != nil {
		// 2) 對話的漏洞目標：這是實際下過手的地方。
		if conversationID != "" {
			// 這是平台內部操作（呼叫端已確認對話屬於該專案），所以用 all 範圍讀取。
			// 零值 RBACListAccess{} 會 fail-closed 成 0 筆，那會讓命名退回舊行為。
			vulns, err := db.ListVulnerabilitiesForAccess(200, 0, database.VulnerabilityListFilter{
				ConversationID: conversationID,
			}, database.RBACListAccess{Scope: database.RBACScopeAll})
			if err == nil {
				for _, v := range vulns {
					add(extractPromoteHost(v.Target))
				}
			}
		}

		// 3) 專案資產的 domain：前面兩者都沒命中時的最後一線。
		if projectID != "" {
			assets, _, err := db.ListAssets(200, 0, database.AssetListFilter{
				ProjectID: projectID,
			}, database.RBACListAccess{Scope: database.RBACScopeAll})
			if err == nil {
				for _, a := range assets {
					add(a.Domain)
				}
			}
		}
	}

	best, bestCount := "", 0
	for _, h := range order {
		if counts[h] > bestCount {
			best, bestCount = h, counts[h]
		}
	}
	return best
}

// normalizePromoteDNS 把字串整理成可用的 DNS 名稱；不合法就回空字串。
func normalizePromoteDNS(raw string) string {
	host := strings.ToLower(strings.TrimSpace(raw))
	host = strings.Trim(host, "[]")
	if host == "" {
		return ""
	}
	if net.ParseIP(host) != nil {
		return "" // IP 不是 DNS
	}
	if !strings.Contains(host, ".") {
		return "" // 單一標籤的主機名不是可穩定引用的 DNS
	}
	for _, r := range host {
		switch {
		case r >= 'a' && r <= 'z':
		case r >= '0' && r <= '9':
		case r == '.' || r == '-' || r == '_':
		default:
			return ""
		}
	}
	return strings.Trim(host, ".-")
}

// extractPromoteHost 從目標字串取出主機名（URL、host:port、純主機名都支援）。
func extractPromoteHost(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	if strings.Contains(raw, "://") {
		if parsed, err := url.Parse(raw); err == nil && parsed.Hostname() != "" {
			return parsed.Hostname()
		}
		return ""
	}
	// 去掉路徑與查詢字串。
	if i := strings.IndexAny(raw, "/?#"); i >= 0 {
		raw = raw[:i]
	}
	// host:port
	if h, _, err := net.SplitHostPort(raw); err == nil {
		return h
	}
	return raw
}

// namespaceSlugByDNS 把 slug 放進目標 DNS 的命名空間，並避免重複前綴。
func namespaceSlugByDNS(slug, dns string) string {
	slug = strings.Trim(strings.TrimSpace(slug), "-")
	dns = strings.Trim(strings.TrimSpace(dns), "-")
	if dns == "" {
		return slug
	}
	if slug == "" {
		return dns
	}
	if slug == dns {
		return dns
	}
	if strings.HasPrefix(slug, dns+"-") {
		// 已經在命名空間裡了，不要疊成 example.com-example.com-xxx
		return slug
	}
	return dns + "-" + slug
}
