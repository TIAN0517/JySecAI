package database

import (
	"fmt"
	"strings"

	"jysecai/internal/redirect"
)

// 自動巡站的種子來源。
//
// 「掃哪一批站點」不該靠人工複製網址：漏洞庫裡本來就有分類（娛樂城、SEO 投毒、
// 現金版…），每一筆都帶著目標主機與既有證據。依關鍵字撈出來，就是操作者
// 想要「自動巡站 + 自動植入」的對象。

const (
	// RedirectVerifySeedSourceManual 是使用請求內附的目標清單。
	RedirectVerifySeedSourceManual = "manual"
	// RedirectVerifySeedSourceAssets 是從資產庫依關鍵字挑站點。
	RedirectVerifySeedSourceAssets = "assets"
	// RedirectVerifySeedSourceVulns 是從漏洞紀錄依關鍵字挑站點。
	RedirectVerifySeedSourceVulns = "vulns"
)

// MaxRedirectVerifySeeds 是單批種子站點數上限。
//
// 上限的理由很實際：種子站點會各自觸發一次巡站，沒有上限時一個寬鬆的關鍵字
// 就可能讓平台對幾百個站點發出請求。
const MaxRedirectVerifySeeds = 200

// CollectRedirectVerifySeeds 依來源與分類關鍵字收集可巡站的站點。
//
// source 為 manual 時回傳空 slice（那種情況種子來自請求本身）。
// keyword 為空時視為沒有分類條件 —— 這時會退化成「取最近建立的漏洞紀錄」，
// 而不是讓 LIKE '%%' 掃全表後回傳整份資料庫。
func (db *DB) CollectRedirectVerifySeeds(source string, keyword string, limit int) ([]string, error) {
	source = strings.ToLower(strings.TrimSpace(source))
	if source == "" || source == RedirectVerifySeedSourceManual {
		return nil, nil
	}
	if limit <= 0 || limit > MaxRedirectVerifySeeds {
		limit = MaxRedirectVerifySeeds
	}
	keyword = strings.TrimSpace(keyword)

	switch source {
	case RedirectVerifySeedSourceAssets:
		return db.collectSeedFromAssets(keyword, limit)
	case RedirectVerifySeedSourceVulns:
		return db.collectSeedFromVulnerabilities(keyword, limit)
	default:
		return nil, fmt.Errorf("不支援的種子來源: %q", source)
	}
}

// collectSeedFromAssets 從資產庫依關鍵字挑站點。
func (db *DB) collectSeedFromAssets(keyword string, limit int) ([]string, error) {
	query := `SELECT host FROM assets WHERE host <> ''`
	args := []interface{}{}
	if keyword != "" {
		pattern := "%" + keyword + "%"
		query += ` AND (host LIKE ? OR title LIKE ? OR business_system LIKE ? OR source_query LIKE ? OR environment LIKE ?)`
		args = append(args, pattern, pattern, pattern, pattern, pattern)
	}
	query += ` ORDER BY updated_at DESC LIMIT ?`
	args = append(args, limit*4)

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("查詢資產庫種子失敗: %w", err)
	}
	defer rows.Close()

	out := make([]string, 0, limit)
	seen := make(map[string]struct{}, limit)
	for rows.Next() {
		var host string
		if err := rows.Scan(&host); err != nil {
			return nil, fmt.Errorf("掃描資產庫種子失敗: %w", err)
		}
		for _, candidate := range redirect.TargetHosts(host) {
			if !isSeedHostUsable(candidate) {
				continue
			}
			if _, dup := seen[candidate]; dup {
				continue
			}
			seen[candidate] = struct{}{}
			out = append(out, "https://"+candidate)
			if len(out) >= limit {
				return out, nil
			}
		}
	}
	return out, rows.Err()
}

// collectSeedFromVulnerabilities 從漏洞紀錄依關鍵字挑站點。
//
// 目標欄位不是乾淨的網址（「example.com (1.2.3.4)」「標題：… 目標：…」），
// 而且站點常常只出現在標題或描述裡 —— 所以四個欄位都拿去抽主機。
func (db *DB) collectSeedFromVulnerabilities(keyword string, limit int) ([]string, error) {
	query := `SELECT title, description, target, evidence FROM vulnerabilities WHERE 1=1`
	args := []interface{}{}
	if keyword != "" {
		pattern := "%" + keyword + "%"
		query += ` AND (title LIKE ? OR description LIKE ? OR target LIKE ? OR evidence LIKE ?)`
		args = append(args, pattern, pattern, pattern, pattern)
	}
	query += ` ORDER BY updated_at DESC LIMIT ?`
	args = append(args, limit*8)

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("查詢漏洞紀錄種子失敗: %w", err)
	}
	defer rows.Close()

	out := make([]string, 0, limit)
	seen := make(map[string]struct{}, limit)
	for rows.Next() {
		var title, description, target, evidence string
		if err := rows.Scan(&title, &description, &target, &evidence); err != nil {
			return nil, fmt.Errorf("掃描漏洞紀錄種子失敗: %w", err)
		}
		// 標題與描述通常先出現、比較接近「這個站是什麼類別」；
		// 目標欄位最準；證據欄最後補漏。
		for _, field := range []string{target, title, description, evidence} {
			for _, candidate := range redirect.TargetHosts(field) {
				if !isSeedHostUsable(candidate) {
					continue
				}
				if _, dup := seen[candidate]; dup {
					continue
				}
				seen[candidate] = struct{}{}
				out = append(out, "https://"+candidate)
				if len(out) >= limit {
					return out, nil
				}
			}
		}
	}
	return out, rows.Err()
}

// isSeedHostUsable 判斷抽出來的主機能不能當巡站種子。
//
// 私有／回環位址要擋掉：那通常是受害者自己系統的內網架構，不是可以對外巡站的站點。
func isSeedHostUsable(host string) bool {
	host = strings.ToLower(strings.TrimSpace(host))
	if host == "" || host == "localhost" {
		return false
	}
	if redirect.PrivateHost(host) {
		return false
	}
	return redirect.HostOf("https://"+host) != ""
}
