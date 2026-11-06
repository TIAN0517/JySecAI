// Command rewrite-endpoints 離線批次改寫漏洞紀錄裡的受控回連端點。
//
// 為什麼需要這支工具：平台上有 API（POST /api/vulnerabilities/rewrite-controlled-endpoints）
// 與控制台按鈕，但那些需要登入且走 HTTP。維運時常見的狀況是「拿不到網頁密碼、
// 但要立刻把整批紀錄的 payload 換成自己的受控端點」——這時直接對資料庫跑一次
// 比請人登入更快，而且用的是同一套改寫邏輯（internal/redirect）。
//
// 用法：
//
//	# 1) 先盤點：整庫有哪些主機出現在 payload 位置、各自幾筆
//	rewrite-endpoints -db /path/conversations.db -endpoint https://97y.me/tjneJ -scan
//
//	# 2) 預演：不寫入，只看會改哪些
//	rewrite-endpoints -db /path/conversations.db -endpoint https://97y.me/tjneJ
//
//	# 3) 確認無誤後才真的寫入（會先留下可回滾的備份 JSON）
//	rewrite-endpoints -db /path/conversations.db -endpoint https://97y.me/tjneJ \
//	  -apply -backup /path/rewrite-backup.json
//
//	# 需要時可以明確指定要換掉的主機（逗號分隔），或明確排除某些主機
//	rewrite-endpoints ... -hosts gofun222.com,dlg8888.com
//	rewrite-endpoints ... -exclude-hosts www.aarp.org
//
// 安全設計：
//   - 預設是 dry-run；沒有 -apply 就不會寫任何東西。
//   - -apply 前一定先寫備份 JSON（原始欄位），出事可以照著還原。
//   - 目標站自己的網址（Target / 標題裡的主機）永遠保留；Impact / Recommendation 不動。
//   - 證據欄位（evidence）預設不動 —— 它是逐字擷取到的觀察結果，換掉等於讓紀錄
//     聲稱「我們親眼看到站方跳到我們的 URL」，而實際上沒有這樣的觀察。要改它必須
//     明確加 -include-evidence。
//   - 已經是受控端點的值不動 → 可以重複執行。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"

	"jysecai/internal/audit"
	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/redirect"

	"go.uber.org/zap"
)

// backupRecord 是備份檔裡的一筆：原始欄位 + 改寫後欄位。
type backupRecord struct {
	ID           string   `json:"id"`
	Title        string   `json:"title"`
	Target       string   `json:"target"`
	Original     fields   `json:"original"`
	Rewritten    fields   `json:"rewritten"`
	ReplacedURLs []string `json:"replaced_urls"`
}

// fields 是會被改寫的四個欄位。
type fields struct {
	Description string `json:"description"`
	ReproSteps  string `json:"reproduction_steps"`
	Evidence    string `json:"evidence"`
	RetestNotes string `json:"retest_notes"`
}

// sampleLine 是給人看的單筆結果。
type sampleLine struct {
	ID       string   `json:"id"`
	Title    string   `json:"title"`
	Target   string   `json:"target"`
	Replaced int      `json:"replaced"`
	URLs     []string `json:"replaced_urls"`
	Fields   []string `json:"fields"`
}

// hostStat 是盤點模式下單一主機的統計。
type hostStat struct {
	Host string `json:"host"`
	// Count 是該主機出現在 payload 位置的總次數。
	Count int `json:"count"`
	// Records 是涉及該主機的紀錄筆數。
	Records int `json:"records"`
	// ExternalRecords 是「該主機不屬於這筆紀錄自己的站」的紀錄筆數 ——
	// 這才是可能屬於攻擊者回連端點、值得替換的對象。
	ExternalRecords int      `json:"external_records"`
	Examples        []string `json:"examples"`
}

func main() {
	var (
		dbPath      = flag.String("db", "", "conversations.db 路徑（必填）")
		endpoint    = flag.String("endpoint", "", "要寫入的受控端點，例如 https://97y.me/tjneJ（必填）")
		apply       = flag.Bool("apply", false, "真的寫入；未加時只 dry-run")
		backupPath  = flag.String("backup", "", "-apply 時的備份 JSON 路徑（預設 <db>.rewrite-backup.json）")
		limit       = flag.Int("limit", 5000, "最多處理筆數")
		sampleMax   = flag.Int("samples", 30, "最多列幾筆範例")
		scan        = flag.Bool("scan", false, "只盤點 payload 位置出現過的主機，不做任何替換")
		onlyHosts   = flag.String("hosts", "", "只改寫這組主機（逗號分隔）；留空 = 改寫所有非保護主機")
		exclude     = flag.String("exclude-hosts", "", "永不改寫的主機（逗號分隔）")
		observed    = flag.Bool("include-observed", false, "連觀測到的 Location 回應值也一併改寫（預設不改：那是證據）")
		allowPriv   = flag.Bool("allow-private-ips", false, "連私有/回環/link-local IP 也改寫（預設不改：那通常是受害者自己的內網架構）")
		incEvidence = flag.Bool("include-evidence", false, "連證據欄位一起改寫（預設不改：證據是逐字擷取的觀察結果，改掉等於偽造證據）")
	)
	flag.Parse()

	if strings.TrimSpace(*dbPath) == "" || strings.TrimSpace(*endpoint) == "" {
		fmt.Fprintln(os.Stderr, "用法：rewrite-endpoints -db <conversations.db> -endpoint <https://...> [-scan | -apply] [-hosts a,b] [-exclude-hosts c]")
		os.Exit(2)
	}
	if _, err := os.Stat(*dbPath); err != nil {
		fmt.Fprintf(os.Stderr, "找不到資料庫 %s: %v\n", *dbPath, err)
		os.Exit(1)
	}

	logger := zap.NewNop()
	db, err := database.NewDB(*dbPath, logger)
	if err != nil {
		fmt.Fprintf(os.Stderr, "開啟資料庫失敗: %v\n", err)
		os.Exit(1)
	}
	defer db.Close()

	items, err := db.ListVulnerabilitiesForAccess(*limit, 0, database.VulnerabilityListFilter{}, database.RBACListAccess{Scope: database.RBACScopeAll})
	if err != nil {
		fmt.Fprintf(os.Stderr, "列出漏洞失敗: %v\n", err)
		os.Exit(1)
	}

	onlyList := splitHosts(*onlyHosts)
	excludeList := splitHosts(*exclude)

	if *scan {
		runScan(items, *observed)
		return
	}

	changed := 0
	replacedTotal := 0
	samples := make([]sampleLine, 0, *sampleMax)
	backups := make([]backupRecord, 0, 16)

	for _, vuln := range items {
		if vuln == nil {
			continue
		}
		// 保護名單＝目標欄位的主機 ＋ 標題裡提到的主機。
		// 目標欄位的主機另外以「同一個可註冊網域」比對，避免兄弟子網域被當成 payload 換掉。
		targetHosts := redirect.TargetHosts(vuln.Target)
		keepHosts := append(append([]string{}, targetHosts...), redirect.TargetHosts(vuln.Title)...)

		updated := *vuln
		hits := 0
		touched := make([]string, 0, 4)
		urls := make([]string, 0, 2)

		parts := []struct {
			name string
			get  func() string
			set  func(string)
		}{
			{"description", func() string { return updated.Description }, func(v string) { updated.Description = v }},
			{"reproduction_steps", func() string { return updated.ReproSteps }, func(v string) { updated.ReproSteps = v }},
			{"retest_notes", func() string { return updated.RetestNotes }, func(v string) { updated.RetestNotes = v }},
		}
		// 證據欄位預設不動：它是逐字擷取到的觀察結果（curl 輸出、響應標頭、檔案內容），
		// 換成我們的受控端點會讓紀錄讀起來像「我們親眼看到站方跳到我們的 URL」，
		// 而實際上沒有這樣的觀察 —— 報告裡那就是偽證。
		if *incEvidence {
			parts = append(parts, struct {
				name string
				get  func() string
				set  func(string)
			}{"evidence", func() string { return updated.Evidence }, func(v string) { updated.Evidence = v }})
		}
		for _, part := range parts {
			original := part.get()
			if strings.TrimSpace(original) == "" {
				continue
			}
			rewritten, count, replaced := redirect.RewriteControlledEndpointsWithOptions(original, redirect.RewriteOptions{
				Endpoint:        *endpoint,
				KeepHosts:       keepHosts,
				KeepSiteHosts:   targetHosts,
				OnlyHosts:       onlyList,
				ExcludeHosts:    excludeList,
				IncludeObserved: *observed,
				AllowPrivateIPs: *allowPriv,
			})
			if count == 0 {
				continue
			}
			hits += count
			touched = append(touched, part.name)
			urls = append(urls, replaced...)
			part.set(rewritten)
		}
		if hits == 0 {
			continue
		}
		changed++
		replacedTotal += hits

		record := backupRecord{
			ID:           vuln.ID,
			Title:        vuln.Title,
			Target:       vuln.Target,
			ReplacedURLs: urls,
		}
		record.Original = fields{
			Description: vuln.Description,
			ReproSteps:  vuln.ReproSteps,
			Evidence:    vuln.Evidence,
			RetestNotes: vuln.RetestNotes,
		}
		record.Rewritten = fields{
			Description: updated.Description,
			ReproSteps:  updated.ReproSteps,
			Evidence:    updated.Evidence,
			RetestNotes: updated.RetestNotes,
		}
		backups = append(backups, record)

		if len(samples) < *sampleMax {
			samples = append(samples, sampleLine{
				ID:       vuln.ID,
				Title:    vuln.Title,
				Target:   vuln.Target,
				Replaced: hits,
				URLs:     urls,
				Fields:   touched,
			})
		}

		if *apply {
			if err := db.UpdateVulnerability(vuln.ID, &updated); err != nil {
				fmt.Fprintf(os.Stderr, "更新 %s 失敗: %v\n", vuln.ID, err)
				continue
			}
		}
	}

	summary := map[string]interface{}{
		"db":               *dbPath,
		"endpoint":         *endpoint,
		"apply":            *apply,
		"include_evidence": *incEvidence,
		"only_hosts":       onlyList,
		"exclude_hosts":    excludeList,
		"scanned":          len(items),
		"changed":          changed,
		"replaced_total":   replacedTotal,
		"samples":          samples,
	}
	encoded, _ := json.MarshalIndent(summary, "", "  ")
	fmt.Println(string(encoded))

	if !*apply {
		fmt.Println("\n[dry-run] 沒有寫入任何資料。加上 -apply 才會真的改寫。")
		return
	}

	if len(backups) > 0 {
		target := *backupPath
		if strings.TrimSpace(target) == "" {
			target = *dbPath + ".rewrite-backup.json"
		}
		payload, err := json.MarshalIndent(backups, "", "  ")
		if err != nil {
			fmt.Fprintf(os.Stderr, "序列化備份失敗: %v\n", err)
			os.Exit(1)
		}
		if err := os.WriteFile(target, payload, 0o600); err != nil {
			fmt.Fprintf(os.Stderr, "寫入備份失敗: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("\n已備份 %d 筆原始記錄到 %s\n", len(backups), target)
	}

	// 稽核留痕：離線執行沒有 HTTP 內容，所以用 RecordSystem。
	auditEnabled := true
	auditCfg := &config.Config{Audit: config.AuditConfig{Enabled: &auditEnabled, RetentionDays: 15}}
	auditSvc := audit.NewService(db, auditCfg, logger)
	auditSvc.RecordSystem(audit.Entry{
		Level:        "info",
		Category:     "vulnerability",
		Action:       "rewrite_endpoints",
		Result:       "success",
		ResourceType: "vulnerability",
		Message:      "離線批次改寫漏洞記錄的回連端點",
		Detail: map[string]interface{}{
			"endpoint":       *endpoint,
			"only_hosts":     onlyList,
			"exclude_hosts":  excludeList,
			"scanned":        len(items),
			"changed":        changed,
			"replaced_total": replacedTotal,
			"source":         "cmd/rewrite-endpoints",
			"at":             time.Now().Format(time.RFC3339),
		},
	})

	fmt.Printf("已改寫 %d 筆（共替換 %d 個網址），稽核已留痕。\n", changed, replacedTotal)
}

// runScan 盤點整庫裡 payload 位置出現過的主機。
//
// 這是資料遷移的第一步：先看清楚有哪些主機、分布在幾筆紀錄裡，
// 再由操作者挑要換掉的主機（-hosts）或要保留的主機（-exclude-hosts）。
func runScan(items []*database.Vulnerability, includeObserved bool) {
	stats := map[string]*hostStat{}
	for _, vuln := range items {
		if vuln == nil {
			continue
		}
		// 保護名單：目標欄位的主機（含同網域兄弟子網域）＋ 標題裡提到的主機。
		targetHosts := redirect.TargetHosts(vuln.Target)
		keepHosts := append(append([]string{}, targetHosts...), redirect.TargetHosts(vuln.Title)...)
		siteHosts := targetHosts
		seenInRecord := map[string]bool{}
		externalInRecord := map[string]bool{}
		for _, text := range []string{vuln.Description, vuln.ReproSteps, vuln.Evidence, vuln.RetestNotes} {
			if strings.TrimSpace(text) == "" {
				continue
			}
			for _, candidate := range redirect.CandidateEndpoints(text, includeObserved) {
				host := hostOf(candidate)
				if host == "" {
					continue
				}
				stat, ok := stats[host]
				if !ok {
					stat = &hostStat{Host: host}
					stats[host] = stat
				}
				stat.Count++
				if !seenInRecord[host] {
					seenInRecord[host] = true
					stat.Records++
					if len(stat.Examples) < 3 {
						stat.Examples = append(stat.Examples, vuln.ID+" | "+truncate(vuln.Title, 48))
					}
				}
				if !hostProtected(host, keepHosts, siteHosts) && !redirect.PrivateHost(host) && !externalInRecord[host] {
					externalInRecord[host] = true
					stat.ExternalRecords++
				}
			}
		}
	}

	list := make([]hostStat, 0, len(stats))
	for _, stat := range stats {
		list = append(list, *stat)
	}
	sort.Slice(list, func(i, j int) bool {
		if list[i].Count != list[j].Count {
			return list[i].Count > list[j].Count
		}
		return list[i].Host < list[j].Host
	})
	encoded, _ := json.MarshalIndent(map[string]interface{}{
		"scanned_records": len(items),
		"hosts":           list,
	}, "", "  ")
	fmt.Println(string(encoded))
}

// hostOf 取出網址主機名。
// hostOf 取出網址的主機名；委派給 redirect.HostOf 讓盤點與改寫用同一個判斷。
func hostOf(raw string) string {
	return redirect.HostOf(raw)
}

// splitHosts 把逗號分隔的主機清單拆開。
func splitHosts(raw string) []string {
	out := make([]string, 0, 4)
	for _, item := range strings.Split(raw, ",") {
		host := strings.ToLower(strings.TrimSpace(item))
		if host == "" {
			continue
		}
		out = append(out, host)
	}
	return out
}

// hostProtected 判斷主機是否屬於這筆紀錄自己的站（目標欄位或標題裡提到的主機）。
//
// 委派給 redirect.ProtectedHost：盤點與實際改寫必須用同一個判斷。
func hostProtected(host string, keepHosts []string, siteHosts []string) bool {
	return redirect.ProtectedHost(host, keepHosts, siteHosts)
}

// truncate 截短標題。
func truncate(value string, limit int) string {
	runes := []rune(value)
	if len(runes) <= limit {
		return value
	}
	return string(runes[:limit]) + "…"
}
