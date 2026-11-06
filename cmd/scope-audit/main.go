// Command scope-audit 產出授權覆蓋率報告。
//
// 它回答一個問題：平台手上有一批已確認的漏洞目標，但 scope registry 授權了幾個？
//
// 為什麼需要它
// ------------
// scope 機制（internal/scope）在 enforcement=off 時完全不評估，所以「沒有被授權」
// 這件事從來沒有被量化過，agent 為什麼一直退化成拒絕只能靠猜。這份報告把
// 「手上有哪些目標」與「授權了哪些目標」放在同一張表上比對，讓缺口變成數字。
//
// 它是唯讀的：不寫任何資料表，也不改設定。
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/scope"
	"jysecai/internal/scopeaudit"

	"go.uber.org/zap"
	"gopkg.in/yaml.v3"
)

func main() {
	var (
		configPath  = flag.String("config", "/var/lib/jysecai/core/config.yaml", "平台 config.yaml 路徑（用來取得 database.path）")
		statuses    = flag.String("status", "confirmed", "要納入的漏洞狀態（逗號分隔）")
		severities  = flag.String("severity", "critical,high", "要納入的嚴重度（逗號分隔）")
		actionClass = flag.String("action-class", scope.ActionDBReadExtract, "評估時使用的動作類別")
		format      = flag.String("format", "text", "輸出格式（text｜json）")
		outPath     = flag.String("out", "", "把報告寫到檔案（留空只印到 stdout）")
		limit       = flag.Int("limit", 60, "文字輸出最多列出多少筆未涵蓋目標")
	)
	flag.Parse()

	dbPath, err := resolveDatabasePath(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: %v\n", err)
		os.Exit(2)
	}
	db, err := database.NewDB(dbPath, zap.NewNop())
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: 開啟資料庫失敗 (%s): %v\n", dbPath, err)
		os.Exit(1)
	}
	defer func() { _ = db.Close() }()

	ctx := context.Background()
	opts := scopeaudit.Options{
		Statuses:   splitCSV(*statuses),
		Severities: splitCSV(*severities),
	}
	targets, err := scopeaudit.CollectTargets(ctx, db, opts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: 收集漏洞目標失敗: %v\n", err)
		os.Exit(1)
	}
	report, err := scopeaudit.BuildReport(ctx, db, targets, *actionClass)
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: 產生覆蓋率報告失敗: %v\n", err)
		os.Exit(1)
	}

	var rendered string
	if strings.EqualFold(strings.TrimSpace(*format), "json") {
		blob, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			fmt.Fprintf(os.Stderr, "錯誤: 序列化報告失敗: %v\n", err)
			os.Exit(1)
		}
		rendered = string(blob)
	} else {
		rendered = renderText(report, targets, *actionClass, *limit)
	}

	if *outPath != "" {
		if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
			fmt.Fprintf(os.Stderr, "錯誤: 建立輸出目錄失敗: %v\n", err)
			os.Exit(1)
		}
		if err := os.WriteFile(*outPath, []byte(rendered+"\n"), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "錯誤: 寫入報告失敗: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("報告已寫入 %s\n", *outPath)
		return
	}
	fmt.Println(rendered)
}

// renderText 把報告排版成給人看的樣子。
func renderText(report scopeaudit.Report, targets []scopeaudit.Target, actionClass string, limit int) string {
	var b strings.Builder
	coverage := report.Coverage
	fmt.Fprintf(&b, "==================== 授權覆蓋率報告 ====================\n")
	fmt.Fprintf(&b, "產生時間      : %s\n", time.Now().Format(time.RFC3339))
	fmt.Fprintf(&b, "動作類別      : %s\n", actionClass)
	fmt.Fprintf(&b, "來源漏洞記錄  : %d 筆（去重後目標 %d 個）\n", len(targets), coverage.Total)
	fmt.Fprintf(&b, "\n")
	fmt.Fprintf(&b, "已涵蓋        : %d 個（常駐集 %d／授權券 %d）\n",
		coverage.Covered, coverage.BySource[scope.SourceScopeTarget], coverage.BySource[scope.SourceScopeGrant])
	fmt.Fprintf(&b, "未涵蓋        : %d 個\n", coverage.Uncovered)
	fmt.Fprintf(&b, "被拒絕        : %d 個（禁區／永久封鎖類別／拒絕記憶）\n", coverage.Denied)
	if coverage.Total > 0 {
		fmt.Fprintf(&b, "覆蓋率        : %.1f%%\n", float64(coverage.Covered)/float64(coverage.Total)*100)
	} else {
		fmt.Fprintf(&b, "覆蓋率        : N/A（沒有可評估的目標）\n")
	}

	if len(report.Denied) > 0 {
		fmt.Fprintf(&b, "\n---- 被拒絕的目標（不會被自動起草）----\n")
		for _, item := range report.Denied {
			fmt.Fprintf(&b, "  [%s] %s — %s\n", item.Reason, item.Host, item.Detail)
		}
	}

	if len(report.Uncovered) == 0 {
		fmt.Fprintf(&b, "\n所有目標都已被授權涵蓋。\n")
		return b.String()
	}

	fmt.Fprintf(&b, "\n---- 未涵蓋的目標（最多列出 %d 筆）----\n", limit)
	shown := report.Uncovered
	if len(shown) > limit {
		shown = shown[:limit]
	}
	for _, item := range shown {
		fmt.Fprintf(&b, "  %-42s  漏洞 %d 筆（最高 %s）\n",
			item.Host, len(item.Vulnerabilities), highestSeverity(item.Vulnerabilities))
	}
	if len(report.Uncovered) > limit {
		fmt.Fprintf(&b, "  ... 另 %d 個未列出（用 --format json 看完整清單）\n", len(report.Uncovered)-limit)
	}
	if len(report.Noisy) > 0 {
		fmt.Fprintf(&b, "\n---- 無法解析成有效主機的目標（%d 個，不會被自動起草）----\n", len(report.Noisy))
		for i, item := range report.Noisy {
			if i >= 10 {
				fmt.Fprintf(&b, "  ... 另 %d 個\n", len(report.Noisy)-10)
				break
			}
			fmt.Fprintf(&b, "  %s\n", truncate(item.Raw, 90))
		}
		fmt.Fprintf(&b, "  （這些是漏洞記錄的 target 欄位塞了自由文字，屬資料品質問題）\n")
	}
	fmt.Fprintf(&b, "\n提示：用 scope-drafter 為未涵蓋目標起草待裁決的授權券。\n")
	return b.String()
}

// truncate 截斷字串到指定長度（以 rune 計）。
func truncate(text string, limit int) string {
	runes := []rune(text)
	if len(runes) <= limit {
		return text
	}
	return string(runes[:limit]) + "…"
}

// highestSeverity 回傳這組漏洞裡最高嚴重度。
func highestSeverity(refs []scopeaudit.VulnerabilityRef) string {
	rank := map[string]int{"info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}
	best := ""
	bestRank := 0
	for _, ref := range refs {
		r := rank[strings.ToLower(strings.TrimSpace(ref.Severity))]
		if r > bestRank {
			bestRank = r
			best = ref.Severity
		}
	}
	if best == "" {
		return "unknown"
	}
	return best
}

// splitCSV 解析逗號分隔的參數。
func splitCSV(raw string) []string {
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		trimmed := strings.ToLower(strings.TrimSpace(part))
		if trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}

// resolveDatabasePath 從 config.yaml 取得資料庫路徑。
func resolveDatabasePath(configPath string) (string, error) {
	trimmed := strings.TrimSpace(configPath)
	if trimmed == "" {
		trimmed = "config.yaml"
	}
	data, err := os.ReadFile(trimmed)
	if err != nil {
		return "", fmt.Errorf("讀取設定檔 %s 失敗: %w", trimmed, err)
	}
	var partial struct {
		Database struct {
			Path string `yaml:"path"`
		} `yaml:"database"`
	}
	if err := yaml.Unmarshal(data, &partial); err != nil {
		return "", fmt.Errorf("解析設定檔 %s 失敗: %w", trimmed, err)
	}
	dbPath := strings.TrimSpace(partial.Database.Path)
	if dbPath == "" {
		return "", fmt.Errorf("設定檔 %s 沒有 database.path", trimmed)
	}
	if !filepath.IsAbs(dbPath) {
		dbPath = filepath.Join(filepath.Dir(trimmed), dbPath)
	}
	return dbPath, nil
}
