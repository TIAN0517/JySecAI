// triage-drain 把自動分流的待處理佇列一次排空。
//
// 排程版（StartAutoTriage）每 2 小時跑一批，幾百筆積壓要用天來算；這個工具走
// 完全相同的 RunAutoTriage 路徑連跑到底，適合一次性清庫。安全邊界不變：
//   - 稽核署名一樣是 auto-triage，與真人操作可區分；
//   - actor 必須持有 all 範圍角色，否則拒絕啟動（與排程版同一條規則）；
//   - false_positive 仍然要求模型提出具體理由，說不出的留在 open。
//
// 用法：
//
//	go run ./cmd/triage-drain --config config.yaml [--db data/conversations.db]
//	                          [--batch 20] [--max-rounds 120] [--pause 3s]
package main

import (
	"context"
	"flag"
	"fmt"
	"sort"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/handler"

	"go.uber.org/zap"
)

// roundTimeout 與排程版的 autoTriageTimeout 一致：單輪上限十分鐘，避免卡住時
// 整個排空作業永久停擺。
const roundTimeout = 10 * time.Minute

// stallLimit 連續幾輪「沒有任何漏洞離開 open」就停手。
//
// 輪替機制（排除前 3 輪看過的）保證佇列會往前推；若連續多輪零進展，代表模型
// 反覆分不動同一批，繼續燒 token 只是浪費——留下來交給下一輪排程或人工。
const stallLimit = 3

// errorLimit 連續幾輪失敗就中止。偶發的模型逾時靠重試吸收，連續失敗代表
// 設定或上游壞了，不是多跑幾輪能解決的。
const errorLimit = 3

func main() {
	configPath := flag.String("config", "config.yaml", "設定檔路徑")
	dbPath := flag.String("db", "", "SQLite 路徑（預設 data/conversations.db，與伺服器一致）")
	batch := flag.Int("batch", 0, "每輪送幾筆給模型（0 = 用設定檔 auto_triage.batch）")
	maxRounds := flag.Int("max-rounds", 120, "安全上限：最多跑幾輪")
	pause := flag.Duration("pause", 3*time.Second, "每輪之間的停頓，避免連續打模型")
	flag.Parse()

	logger, _ := zap.NewProduction()
	defer func() { _ = logger.Sync() }()
	sugar := logger.Sugar()

	cfg, err := config.Load(*configPath)
	if err != nil {
		sugar.Fatalf("讀取設定檔失敗: %v", err)
	}
	if !cfg.AutoTriage.Enabled {
		sugar.Fatalf("auto_triage.enabled 為 false；排空工具沿用同一組安全邊界，請先在設定檔啟用")
	}
	actor := cfg.AutoTriage.ActorUserID
	if actor == "" {
		sugar.Fatalf("auto_triage.actor_user_id 未設定")
	}

	path := *dbPath
	if path == "" {
		path = "data/conversations.db"
	}
	db, err := database.NewDB(path, logger)
	if err != nil {
		sugar.Fatalf("開啟資料庫失敗: %v", err)
	}
	defer func() { _ = db.Close() }()

	// 與排程版的 widestRoleScope 同一條規則：帳號必須真的持有 all 範圍角色，
	// 否則拒絕啟動，不降級成較小範圍繼續跑。
	if err := requireAllScope(db, actor); err != nil {
		sugar.Fatalf("自動分流的 actor_user_id 無效: %v", err)
	}

	batchN := *batch
	if batchN <= 0 {
		batchN = cfg.AutoTriage.Batch
	}
	if batchN <= 0 || batchN > 60 {
		batchN = 20
	}

	vh := handler.NewVulnerabilityHandler(db, logger)
	vh.SetTriageConfig(&cfg.OpenAI)

	openFilter := database.VulnerabilityListFilter{Status: database.VulnerabilityStatusOpen}
	openNow, err := db.CountVulnerabilities(openFilter)
	if err != nil {
		sugar.Fatalf("統計待處理數量失敗: %v", err)
	}
	sugar.Infof("開始排空：open=%d 筆，batch=%d，model=%s，actor=%s",
		openNow, batchN, cfg.OpenAI.Model, actor)
	if openNow == 0 {
		printSummary(db, sugar)
		return
	}

	access := database.RBACListAccess{UserID: actor, Scope: database.RBACScopeAll}
	totalApplied, totalSkipped := 0, 0
	stallRounds, errorRounds := 0, 0

	for round := 1; round <= *maxRounds; round++ {
		ctx, cancel := context.WithTimeout(context.Background(), roundTimeout)
		applied, skipped, err := vh.RunAutoTriage(ctx, access, batchN)
		cancel()

		if err != nil {
			errorRounds++
			sugar.Warnf("第 %d 輪失敗（連續 %d/%d）: %v", round, errorRounds, errorLimit, err)
			if errorRounds >= errorLimit {
				sugar.Fatalf("連續 %d 輪失敗，中止", errorLimit)
			}
			time.Sleep(*pause)
			continue
		}
		errorRounds = 0
		totalApplied += applied
		totalSkipped += len(skipped)

		remaining, err := db.CountVulnerabilities(openFilter)
		if err != nil {
			sugar.Warnf("第 %d 輪後統計失敗: %v", round, err)
			remaining = -1
		}
		sugar.Infof("第 %d 輪：applied=%d skipped=%d open 剩餘=%d", round, applied, len(skipped), remaining)

		if remaining == 0 {
			sugar.Infof("佇列已排空，共 %d 輪。", round)
			break
		}
		// 零進展判定：這輪沒有套用任何變更、open 數也沒下降。輪替機制通常會
		// 在 3 輪內把卡住的目標推開，推不動就別再燒 token。
		if applied == 0 && (remaining < 0 || remaining >= openNow) {
			stallRounds++
			if stallRounds >= stallLimit {
				sugar.Warnf("連續 %d 輪零進展（剩 %d 筆模型分不動），停止；留給排程或人工處理",
					stallLimit, remaining)
				break
			}
		} else {
			stallRounds = 0
		}
		openNow = remaining
		time.Sleep(*pause)
	}

	printSummary(db, sugar)
	sugar.Infof("合計：applied=%d skipped=%d", totalApplied, totalSkipped)
}

// requireAllScope 與 handler.widestRoleScope 相同的檢查，複製一份是因為那是
// 未導出方法，而這個檢查是「防止設定填錯時無聲升權」的唯一機會，不能省。
func requireAllScope(db *database.DB, actor string) error {
	roleIDs, err := db.ListRBACUserRoleIDs(actor)
	if err != nil {
		return err
	}
	if len(roleIDs) == 0 {
		return fmt.Errorf("帳號 %s 沒有任何角色", actor)
	}
	roles, err := db.ListRBACRoles()
	if err != nil {
		return err
	}
	scopeByID := make(map[string]string, len(roles))
	for _, r := range roles {
		scopeByID[r.ID] = r.Scope
	}
	for _, id := range roleIDs {
		if scope, ok := scopeByID[id]; ok && scope == database.RBACScopeAll {
			return nil
		}
	}
	return fmt.Errorf("帳號 %s 沒有 all 範圍的角色（自動分流需要看見所有對話的漏洞）", actor)
}

// printSummary 列出排空後的分類結果：狀態 × 嚴重度，讓「審計完畢」有個收據。
func printSummary(db *database.DB, sugar *zap.SugaredLogger) {
	rows, err := db.Query("SELECT status, severity, COUNT(*) FROM vulnerabilities GROUP BY status, severity")
	if err != nil {
		sugar.Warnf("統計分類結果失敗: %v", err)
		return
	}
	defer func() { _ = rows.Close() }()
	type key struct {
		Status string
		Sev    string
	}
	counts := map[key]int{}
	for rows.Next() {
		var st, sev string
		var n int
		if err := rows.Scan(&st, &sev, &n); err != nil {
			sugar.Warnf("讀取統計列失敗: %v", err)
			return
		}
		counts[key{st, sev}] = n
	}
	if err := rows.Err(); err != nil {
		sugar.Warnf("統計分類結果失敗: %v", err)
		return
	}

	statuses := []string{}
	seen := map[string]bool{}
	for k := range counts {
		if !seen[k.Status] {
			seen[k.Status] = true
			statuses = append(statuses, k.Status)
		}
	}
	sort.Strings(statuses)
	severities := []string{"critical", "high", "medium", "low", "info"}
	sugar.Infof("分類結果：")
	for _, st := range statuses {
		total := 0
		parts := ""
		for _, sev := range severities {
			if n := counts[key{st, sev}]; n > 0 {
				total += n
				parts += fmt.Sprintf(" %s=%d", sev, n)
			}
		}
		sugar.Infof("  %-14s 共 %4d 筆 (%s )", st, total, parts)
	}
}
