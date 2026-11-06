// Package scopeaudit 把「平台手上的已確認漏洞目標」與「scope registry 的授權」對齊，
// 產出授權覆蓋率報告。
//
// 為什麼獨立成一個套件
// --------------------
// 這件事有兩個消費者：離線的 CLI（cmd/scope-audit、cmd/scope-drafter）與
// 線上的 API（/api/scope/audit）。兩邊必須用同一套「哪些目標算數」的定義，
// 否則離線報告與線上儀表板會給出不同數字，沒有人知道該相信哪一個。
//
// 這裡刻意不 import internal/database：只用最小查詢介面，
// 讓它能在純 *sql.DB 上測試，也避免和 internal/database 形成循環依賴。
package scopeaudit

import (
	"context"
	"database/sql"
	"fmt"
	"net"
	"strings"
	"time"

	"jysecai/internal/scope"
)

// Queryer 是這個套件需要的最小資料庫介面（由 *sql.DB 與 database.DB 滿足）。
//
// 直接沿用 scope.Queryer：報告與執行期判定必須讀同一張表、用同一套介面，
// 才不會出現兩邊對不上況。
type Queryer = scope.Queryer

// Target 是報告中的一個目標：來自漏洞記錄的原始目標 + 正規化後的主機。
type Target struct {
	// VulnerabilityID 是來源漏洞記錄的 ID（多筆指向同一目標時會列出全部）。
	VulnerabilityID string `json:"vulnerability_id"`
	// Title 是漏洞標題（截斷後，用於報告與證據）。
	Title string `json:"title"`
	// Severity 是嚴重度（critical／high／…）。
	Severity string `json:"severity"`
	// Status 是漏洞狀態（confirmed／open／…）。
	Status string `json:"status"`
	// Raw 是原始目標字串（保留原樣供稽核）。
	Raw string `json:"raw"`
	// Host 是正規化後的主機。
	Host string `json:"host"`
	// HostPlausible 表示這個主機像一個真正的目標（不是自由文字殘渣）。
	HostPlausible bool `json:"host_plausible"`
}

// PlausibleHost 判斷正規化後的主機是否像一個真正的目標。
//
// 為什麼需要這個過濾
// ------------------
// vulnerabilities.target 是人手寫的自由文字，常常把描述、埠位清單、括號註記
// 一起塞進去：
//
//	"dns.chailease.com.tw (61.63.14.15 與 61.218.16.228)"
//	"118.163.168.146:110,143 (mail.houseloan.tw)"
//	"post https:"
//	"azure blob storage 存储账号 officialchailease（https:"
//
// 這些雜訊正規化後會變成 "https:"、帶空白的字串之類的東西。
// 如果直接拿去起草授權券，registry 會被垃圾填滿——而且每一張都要人按核准，
// 等於把真正要處理的事項淹掉。所以起草前必須篩掉。
//
// 判定規則（刻意保守，寧可漏掉也不要誤放）：
//   - 純 IP（v4/v6）視為有效目標。
//   - 主機名必須是「標籤.標籤…」且最後一段（TLD）是 2–24 個英文字母。
//   - 任何空白、括號、冒號、全形字元一律視為無效。
func PlausibleHost(host string) bool {
	host = strings.ToLower(strings.TrimSpace(host))
	if host == "" {
		return false
	}
	// 純 IP 是有效目標（滲透測試的目標本來就有很多是直連 IP）。
	if ip := net.ParseIP(host); ip != nil {
		return true
	}
	if strings.ContainsAny(host, " \t\r\n()（）[]{}<>,;:'\"\\|") {
		return false
	}
	labels := strings.Split(host, ".")
	if len(labels) < 2 {
		return false
	}
	for _, label := range labels {
		if label == "" {
			return false
		}
		// 標籤只允許英數字與連字號，且不能以連字號開頭或結尾。
		if len(label) > 63 {
			return false
		}
		if strings.HasPrefix(label, "-") || strings.HasSuffix(label, "-") {
			return false
		}
		for _, r := range label {
			if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
				continue
			}
			return false
		}
	}
	// 最後一段必須是英文字母（TLD）。
	// 例外：punycode TLD（xn--…）含數字與連字號，必須放行。
	tld := labels[len(labels)-1]
	if len(tld) < 2 || len(tld) > 24 {
		return false
	}
	if strings.HasPrefix(tld, "xn--") {
		return true
	}
	for _, r := range tld {
		if r < 'a' || r > 'z' {
			return false
		}
	}
	return true
}

// Options 是篩選條件。
type Options struct {
	// Statuses 是要納入的漏洞狀態；留空預設為 confirmed。
	Statuses []string
	// Severities 是要納入的嚴重度；留空預設為 critical 與 high。
	Severities []string
}

// DefaultOptions 回傳預設篩選：已確認且為 critical／high。
func DefaultOptions() Options {
	return Options{
		Statuses:   []string{"confirmed"},
		Severities: []string{"critical", "high"},
	}
}

// CollectTargets 取出符合條件的漏洞目標。
//
// 只讀 confirmed 且 critical／high：這些是「已經驗證存在、而且嚴重到需要處理」
// 的目標——正是應該要有授權名單、否則 agent 只能退化成拒絕的那一批。
// open／undetermined 的目標連存在性都還沒確認，混進來會讓覆蓋率失真。
func CollectTargets(ctx context.Context, q Queryer, opts Options) ([]Target, error) {
	if q == nil {
		return nil, fmt.Errorf("資料庫連線不能為空")
	}
	statuses := opts.Statuses
	if len(statuses) == 0 {
		statuses = DefaultOptions().Statuses
	}
	severities := opts.Severities
	if len(severities) == 0 {
		severities = DefaultOptions().Severities
	}

	statusPlaceholders := make([]string, 0, len(statuses))
	statusArgs := make([]any, 0, len(statuses))
	for _, s := range statuses {
		statusPlaceholders = append(statusPlaceholders, "?")
		statusArgs = append(statusArgs, strings.ToLower(strings.TrimSpace(s)))
	}
	severityPlaceholders := make([]string, 0, len(severities))
	severityArgs := make([]any, 0, len(severities))
	for _, s := range severities {
		severityPlaceholders = append(severityPlaceholders, "?")
		severityArgs = append(severityArgs, strings.ToLower(strings.TrimSpace(s)))
	}

	query := `
		SELECT id, title, severity, status, target
		  FROM vulnerabilities
		 WHERE LOWER(status) IN (` + strings.Join(statusPlaceholders, ",") + `)
		   AND LOWER(severity) IN (` + strings.Join(severityPlaceholders, ",") + `)
		   AND target IS NOT NULL
		   AND TRIM(target) <> ''
		 ORDER BY updated_at DESC, id ASC`

	rows, err := q.QueryContext(ctx, query, append(statusArgs, severityArgs...)...)
	if err != nil {
		return nil, fmt.Errorf("查詢漏洞目標失敗: %w", err)
	}
	defer rows.Close()

	var out []Target
	for rows.Next() {
		var t Target
		var title sql.NullString
		var severity sql.NullString
		var status sql.NullString
		var raw sql.NullString
		if err := rows.Scan(&t.VulnerabilityID, &title, &severity, &status, &raw); err != nil {
			return nil, fmt.Errorf("掃描漏洞目標失敗: %w", err)
		}
		t.Title = title.String
		t.Severity = strings.ToLower(severity.String)
		t.Status = strings.ToLower(status.String)
		t.Raw = strings.TrimSpace(raw.String)
		t.Host = scope.NormalizeTarget(t.Raw).Host
		t.HostPlausible = PlausibleHost(t.Host)
		out = append(out, t)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("讀取漏洞目標失敗: %w", err)
	}
	return out, nil
}

// Report 是覆蓋率報告 + 目標明細的組合結果。
type Report struct {
	// Coverage 是授權覆蓋率統計。
	Coverage scope.CoverageReport `json:"coverage"`
	// Uncovered 是未涵蓋目標（含來源漏洞資訊）。
	Uncovered []UncoveredTarget `json:"uncovered"`
	// Noisy 是未涵蓋但無法解析成有效主機的目標（自由文字殘渣）。
	// 這些不會被自動起草，但必須被看見——它們代表的是資料品質問題。
	Noisy []NoisyTarget `json:"noisy"`
	// Denied 是被拒絕的目標（含來源漏洞資訊）。
	Denied []DeniedTarget `json:"denied"`
}

// UncoveredTarget 是一個未涵蓋目標與它的來源漏洞。
type UncoveredTarget struct {
	Target
	// Vulnerabilities 是所有指向此目標的漏洞記錄。
	Vulnerabilities []VulnerabilityRef `json:"vulnerabilities"`
}

// DeniedTarget 是一個被拒絕的目標與拒絕原因。
type DeniedTarget struct {
	Target
	// Reason 是拒絕原因（forbidden／permanent_block／previously_denied／…）。
	Reason string `json:"reason"`
	// Detail 是給人看的說明。
	Detail string `json:"detail"`
	// Vulnerabilities 是所有指向此目標的漏洞記錄。
	Vulnerabilities []VulnerabilityRef `json:"vulnerabilities"`
}

// NoisyTarget 是一個無法解析成有效主機的未涵蓋目標。
//
// 它是資料品質問題而不是授權問題：原始 target 是自由文字（描述、埠位清單、
// 括號註記混在一起），正規化後得不到可用的主機。自動起草必須跳過它們，
// 否則 registry 會被垃圾填滿。
type NoisyTarget struct {
	Target
	// Vulnerabilities 是所有指向此目標的漏洞記錄。
	Vulnerabilities []VulnerabilityRef `json:"vulnerabilities"`
}

// VulnerabilityRef 是一筆漏洞記錄的精簡參照。
type VulnerabilityRef struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Severity string `json:"severity"`
	Status   string `json:"status"`
}

// BuildReport 把目標清單與 registry 對齊，產生覆蓋率報告。
//
// 用的是 scope.AuditCoverage（與平台執行期同一套判定），所以報告不會和
// 實際執行的閘門說法不一致。
func BuildReport(ctx context.Context, q Queryer, targets []Target, actionClass string) (Report, error) {
	raws := make([]string, 0, len(targets))
	for _, t := range targets {
		raws = append(raws, t.Raw)
	}
	coverage, err := scope.AuditCoverage(ctx, q, raws, actionClass, time.Time{})
	if err != nil {
		return Report{}, err
	}

	// 依正規化主機把漏洞記錄分組，讓報告不會對同一個目標列出十幾列。
	byHost := map[string][]VulnerabilityRef{}
	for _, t := range targets {
		key := scope.NormalizeTarget(t.Raw).Key()
		if key == "" {
			continue
		}
		byHost[key] = append(byHost[key], VulnerabilityRef{
			ID:       t.VulnerabilityID,
			Title:    t.Title,
			Severity: t.Severity,
			Status:   t.Status,
		})
	}

	report := Report{Coverage: coverage}
	// 判定哪些目標鍵是「真的主機」：只要有一筆記錄的主機合理就算合理。
	plausibleKeys := map[string]bool{}
	for _, t := range targets {
		if t.HostPlausible {
			plausibleKeys[scope.NormalizeTarget(t.Raw).Key()] = true
		}
	}
	for _, uncovered := range coverage.UncoveredTargets {
		key := uncovered.Key()
		if plausibleKeys[key] {
			report.Uncovered = append(report.Uncovered, UncoveredTarget{
				Target:          Target{Host: uncovered.Host, Raw: uncovered.Raw, HostPlausible: true},
				Vulnerabilities: byHost[key],
			})
			continue
		}
		report.Noisy = append(report.Noisy, NoisyTarget{
			Target:          Target{Host: uncovered.Host, Raw: uncovered.Raw, HostPlausible: false},
			Vulnerabilities: byHost[key],
		})
	}
	for _, denial := range coverage.DeniedTargets {
		key := denial.Target.Key()
		report.Denied = append(report.Denied, DeniedTarget{
			Target:          Target{Host: denial.Target.Host, Raw: denial.Target.Raw},
			Reason:          denial.Reason,
			Detail:          denial.Detail,
			Vulnerabilities: byHost[key],
		})
	}
	return report, nil
}
