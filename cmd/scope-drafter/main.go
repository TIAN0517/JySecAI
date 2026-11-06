// Command scope-drafter 為「已確認但未授權」的目標自動起草授權券（待裁決狀態）。
//
// 它解決的是什麼問題
// ------------------
// scope.enforcement=off 或 registry 為空時，agent 碰到任何需要授權的目標都只能
// 退化成「我不能做」——因為平台從來沒有問過使用者「這件事該不該做」。
// 人工逐筆審 1038 筆目標不現實，於是整個流程卡死在「什麼都不做」。
//
// 這支工具的做法
// --------------
//  1. 取出已確認且 critical／high 的漏洞目標（這是「該做而且嚴重」的集合）。
//  2. 對照 registry，找出未涵蓋的部分（禁區與永久封鎖類別已經被排除，不會進來）。
//  3. 為每個未涵蓋目標起草一張 status=pending 的授權券：
//     max_uses=1、valid_until=預設 24 小時、action_classes 明確列出。
//  4. 透過 Telegram 推播帶「核准／拒絕」按鈕的通知——人按一次就轉為生效。
//
// 三條不可退讓的規則
// ------------------
//  1. pending 不等於授權：internal/scope 的 matchGrantRows 會略過 pending 的券，
//     所以「起草」只是把問題搬到人面前，不會讓任何未經核准的目標變成可打。
//  2. 冪等：授權券 ID 由目標雜湊推導，同一個目標重跑不會產生第二張。
//  3. 禁區優先：命中 internal/forbidden 的目標永遠不會被起草。
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/robot"
	"jysecai/internal/scope"
	"jysecai/internal/scopeaudit"

	"go.uber.org/zap"
	"gopkg.in/yaml.v3"
)

// draft 是即將寫入的一張待裁決授權券。
type draft struct {
	// GrantID 是冪等鍵（由目標雜湊推導）。
	GrantID string
	// Host 是正規化主機。
	Host string
	// Raw 是原始目標字串。
	Raw string
	// Vulnerabilities 是來源漏洞。
	Vulnerabilities []scopeaudit.VulnerabilityRef
}

func main() {
	var (
		configPath    = flag.String("config", "/var/lib/jysecai/core/config.yaml", "平台 config.yaml 路徑")
		statuses      = flag.String("status", "confirmed", "要納入的漏洞狀態（逗號分隔）")
		severities    = flag.String("severity", "critical,high", "要納入的嚴重度（逗號分隔）")
		actionClasses = flag.String("action-classes", "db_read_extract,harmless_request,local_analysis,offline_replay", "授權券的 action_classes（逗號分隔，必須明確列出）")
		validHours    = flag.Int("valid-hours", 24, "授權券有效期限（小時）")
		maxUses       = flag.Int("max-uses", 1, "授權券可用次數")
		limit         = flag.Int("limit", 50, "最多起草幾張授權券")
		issuedBy      = flag.String("issued-by", "scope-drafter", "寫進 issued_by 的來源標記")
		owner         = flag.String("owner", "auto-drafter", "寫進拒絕記憶的 owner")
		dryRun        = flag.Bool("dry-run", false, "只印出將會起草的項目，不寫資料庫也不發通知")
		notify        = flag.Bool("notify", true, "是否透過 Telegram 推播核准通知")
		chatID        = flag.String("chat-id", "", "Telegram 收件 chat id（留空則自動查綁定表）")
	)
	flag.Parse()

	cfg, err := loadPartialConfig(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: %v\n", err)
		os.Exit(2)
	}
	db, err := database.NewDB(cfg.databasePath, zap.NewNop())
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: 開啟資料庫失敗 (%s): %v\n", cfg.databasePath, err)
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
	report, err := scopeaudit.BuildReport(ctx, db, targets, scope.ActionDBReadExtract)
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: 產生覆蓋率報告失敗: %v\n", err)
		os.Exit(1)
	}

	classes := splitCSV(*actionClasses)
	if len(classes) == 0 {
		fmt.Fprintln(os.Stderr, "錯誤: action-classes 不可為空（空白清單只等於「一般類別」，不會明列 db_read_extract）")
		os.Exit(2)
	}

	drafts := buildDrafts(report, *limit)
	fmt.Printf("未涵蓋目標 %d 個，本次起草上限 %d 個\n", report.Coverage.Uncovered, *limit)
	if len(drafts) == 0 {
		fmt.Println("沒有需要起草的項目。")
		return
	}

	now := time.Now().UTC()
	validUntil := now.Add(time.Duration(*validHours) * time.Hour)
	created := 0
	skipped := 0
	for _, d := range drafts {
		existing, err := database.GetScopeGrant(ctx, db, d.GrantID)
		if err == nil && existing != nil {
			skipped++
			continue
		}
		evidence, err := json.Marshal(map[string]interface{}{
			"source":          "scope-drafter",
			"host":            d.Host,
			"vulnerabilities": d.Vulnerabilities,
			"drafted_at":      now.Format(time.RFC3339),
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, "錯誤: 序列化證據失敗: %v\n", err)
			os.Exit(1)
		}
		grant := database.ScopeGrant{
			ID:            d.GrantID,
			TargetType:    string(scope.TargetHost),
			TargetValue:   d.Host,
			ActionClasses: classes,
			MaxUses:       *maxUses,
			ValidUntil:    &validUntil,
			IssuedBy:      *issuedBy,
			IssuedAt:      now,
			Evidence:      string(evidence),
			Status:        database.ScopeGrantStatusPending,
		}
		if *dryRun {
			fmt.Printf("[dry-run] 起草 %s → %s（%s）\n", grant.ID, grant.TargetValue, strings.Join(grant.ActionClasses, ","))
			created++
			continue
		}
		if err := database.CreateScopeGrant(ctx, db, grant); err != nil {
			fmt.Fprintf(os.Stderr, "錯誤: 寫入授權券失敗 (%s): %v\n", d.Host, err)
			os.Exit(1)
		}
		created++
		fmt.Printf("已起草 %s → %s\n", grant.ID, grant.TargetValue)
	}

	fmt.Printf("\n起草 %d 張、略過 %d 張（已存在）\n", created, skipped)
	if *dryRun {
		return
	}

	if !*notify {
		fmt.Println("未發送通知（--notify=false）。")
		return
	}
	if err := notifyTelegram(ctx, cfg, db, *chatID, drafts, *owner, *validHours); err != nil {
		fmt.Fprintf(os.Stderr, "警告: Telegram 通知失敗: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("已發送 Telegram 核准通知。")
}

// buildDrafts 把未涵蓋目標轉成待起草的授權券清單。
//
// 只取 Uncovered（不含 Denied）：被禁區或永久封鎖類別拒絕的目標，
// 已經被 scope.Resolve 分到拒絕桶裡，永遠不會出現在這裡。
func buildDrafts(report scopeaudit.Report, limit int) []draft {
	out := make([]draft, 0, len(report.Uncovered))
	for _, item := range report.Uncovered {
		host := strings.TrimSpace(item.Host)
		if host == "" {
			continue
		}
		// 防線：只起草「像真的主機」的目標。
		// 報告層已經把雜訊分到 Noisy 桶，這裡再確認一次——
		// 萬一報告邏輯日後改動，也不該讓垃圾進 registry。
		if !scopeaudit.PlausibleHost(host) {
			continue
		}
		out = append(out, draft{
			GrantID:         draftGrantID(host),
			Host:            host,
			Raw:             item.Raw,
			Vulnerabilities: item.Vulnerabilities,
		})
		if len(out) >= limit {
			break
		}
	}
	// 排序：先依最高嚴重度（critical → high），同severity再依主機名。
	// 這樣「先出最嚴重的那批」——操作者有限的眼睛要先看到該看的。
	sort.Slice(out, func(i, j int) bool {
		ri := severityRank(highestSeverity(out[i].Vulnerabilities))
		rj := severityRank(highestSeverity(out[j].Vulnerabilities))
		if ri != rj {
			return ri > rj
		}
		return out[i].Host < out[j].Host
	})
	return out
}

// severityRank 把嚴重度換成可比較的數值（越大越嚴重）。
func severityRank(severity string) int {
	switch strings.ToLower(strings.TrimSpace(severity)) {
	case "critical":
		return 5
	case "high":
		return 4
	case "medium":
		return 3
	case "low":
		return 2
	case "info":
		return 1
	default:
		return 0
	}
}

// draftGrantID 由目標推導穩定的授權券 ID（冪等鍵）。
func draftGrantID(host string) string {
	sum := sha256.Sum256([]byte(strings.ToLower(strings.TrimSpace(host))))
	return "grant_draft_" + hex.EncodeToString(sum[:])[:16]
}

// notifyTelegram 推播帶「核准／拒絕」按鈕的通知。
//
// 每張券一列按鈕（同一則訊息裡多列 inline_keyboard）——所以一則訊息就能
// 讓人一次看完並逐一處理，不必來回切換多則訊息。
func notifyTelegram(ctx context.Context, cfg *partialConfig, db *database.DB, chatID string, drafts []draft, owner string, validHours int) error {
	if !cfg.robots.Telegram.Enabled || strings.TrimSpace(cfg.robots.Telegram.BotToken) == "" {
		return fmt.Errorf("telegram 未啟用或缺少 bot_token")
	}
	recipient := strings.TrimSpace(chatID)
	if recipient == "" {
		recipient = lookupTelegramRecipient(ctx, db)
	}
	if recipient == "" {
		return fmt.Errorf("找不到 Telegram 收件者（robot_user_bindings 沒有啟用的 telegram 綁定）")
	}

	const perMessage = 20
	for start := 0; start < len(drafts); start += perMessage {
		end := start + perMessage
		if end > len(drafts) {
			end = len(drafts)
		}
		chunk := drafts[start:end]
		var b strings.Builder
		fmt.Fprintf(&b, "【scope 授權待裁決】%d 個目標（%d/%d）\n", len(chunk), start+1, end)
		fmt.Fprintf(&b, "有效期限 %d 小時、可用次數依券設定；未按核准前不會生效。\n\n", validHours)
		buttons := make([][]robot.TelegramButton, 0, len(chunk))
		for _, d := range chunk {
			severity := highestSeverity(d.Vulnerabilities)
			fmt.Fprintf(&b, "・%s（%s）\n", d.Host, severity)
			buttons = append(buttons, []robot.TelegramButton{
				{Text: "核准 " + d.Host, CallbackData: "scope_grant:activate:" + d.GrantID},
				{Text: "拒絕 " + d.Host, CallbackData: "scope_grant:reject:" + d.GrantID},
			})
		}
		err := robot.SendProactiveButtons(ctx, cfg.robotsConfig(), "telegram", recipient, b.String(), buttons)
		if err != nil {
			return err
		}
	}
	return nil
}

// lookupTelegramRecipient 從綁定表找啟用中的 telegram 收件者。
func lookupTelegramRecipient(ctx context.Context, db *database.DB) string {
	var external string
	err := db.QueryRowContext(ctx, `
		SELECT external_user_id
		  FROM robot_user_bindings
		 WHERE platform = 'telegram' AND enabled = 1
		 ORDER BY created_at ASC
		 LIMIT 1`).Scan(&external)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(external)
}

// highestSeverity 回傳這組漏洞裡最高嚴重度。
func highestSeverity(refs []scopeaudit.VulnerabilityRef) string {
	rank := map[string]int{"info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}
	best := "unknown"
	bestRank := 0
	for _, ref := range refs {
		if r := rank[strings.ToLower(strings.TrimSpace(ref.Severity))]; r > bestRank {
			bestRank = r
			best = ref.Severity
		}
	}
	return best
}

// partialConfig 是這個工具需要從 config.yaml 讀到的部分。
type partialConfig struct {
	databasePath string
	robots       struct {
		Telegram config.RobotTelegramConfig `yaml:"telegram"`
	}
	db *database.DB
}

// robotsConfig 把機器人設定包成 robot 套件需要的形狀。
func (p *partialConfig) robotsConfig() config.RobotsConfig {
	return config.RobotsConfig{Telegram: p.robots.Telegram}
}

// loadPartialConfig 讀設定檔需要的部分。
func loadPartialConfig(configPath string) (*partialConfig, error) {
	trimmed := strings.TrimSpace(configPath)
	if trimmed == "" {
		trimmed = "config.yaml"
	}
	data, err := os.ReadFile(trimmed)
	if err != nil {
		return nil, fmt.Errorf("讀取設定檔 %s 失敗: %w", trimmed, err)
	}
	var partial struct {
		Database struct {
			Path string `yaml:"path"`
		} `yaml:"database"`
		Robots struct {
			Telegram config.RobotTelegramConfig `yaml:"telegram"`
		} `yaml:"robots"`
	}
	if err := yaml.Unmarshal(data, &partial); err != nil {
		return nil, fmt.Errorf("解析設定檔 %s 失敗: %w", trimmed, err)
	}
	dbPath := strings.TrimSpace(partial.Database.Path)
	if dbPath == "" {
		return nil, fmt.Errorf("設定檔 %s 沒有 database.path", trimmed)
	}
	if !filepath.IsAbs(dbPath) {
		dbPath = filepath.Join(filepath.Dir(trimmed), dbPath)
	}
	cfg := &partialConfig{databasePath: dbPath}
	cfg.robots.Telegram = partial.Robots.Telegram
	return cfg, nil
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
