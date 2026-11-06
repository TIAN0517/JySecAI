// Command scopeimport 把既有的授權 JSON（例如 all/漏洞庫/_授權.json）
// 匯入平台的 Scope Registry（scope_targets 常駐集）。
//
// 為什麼需要這個工具
// ------------------
// P0 把授權變成平台資料庫裡的唯一權威，但既有 engagements 的授權資料還散在
// Python 端的靜態 JSON 裡。這個 CLI 負責把那份資料一次性搬進 registry，
// 讓之後的授權擴充只需要按一次（scope_extension 中斷），不用再手改 JSON。
//
// 三條不可退讓的規則
// ------------------
//  1. 禁區優先：命中 internal/forbidden（119／EPCR／消防救護）的目標一律跳過，
//     絕不寫進 registry——即使來源檔案裡有它。
//  2. 冪等：同一份來源重跑不會產生重複列（冪等鍵＝owner + target_type + target_value，
//     並據此推導穩定的 scope_targets.id）。
//  3. 單筆壞掉不拖垮整份匯入：authorized_until 解析失敗只警告、留空有效期限，
//     不讓整份匯入失敗。
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

	"jysecai/internal/database"
	"jysecai/internal/forbidden"
	"jysecai/internal/scope"

	"go.uber.org/zap"
	"gopkg.in/yaml.v3"
)

// authScope 是授權 JSON 裡單一 scope 的內容（只認必要欄位，其餘忽略）。
type authScope struct {
	// Authorized 表示這一筆 scope 是否真的被授權（false 就跳過）。
	Authorized bool `json:"authorized"`
	// AuthorizedUntil 是授權有效期限（RFC3339 或 YYYY-MM-DD）。
	AuthorizedUntil string `json:"authorized_until"`
	// AuthorizedBy 是授權人／來源說明（寫進 provenance）。
	AuthorizedBy string `json:"authorized_by"`
	// AllowedHosts 是這一筆 scope 涵蓋的主機清單。
	AllowedHosts []string `json:"allowed_hosts"`
	// AllowedActionClasses 是這一筆 scope 容許的動作類別。
	AllowedActionClasses []string `json:"allowed_action_classes"`
}

// authScopeEntry 是一筆 scope 加上它在來源檔案裡的鍵（用來當 owner 的預設值）。
type authScopeEntry struct {
	// Key 是來源檔案 scopes 物件的鍵（陣列格式時是 name/scope/id 欄位）。
	Key string
	// Scope 是該筆 scope 的內容。
	Scope authScope
}

// importTarget 是「即將寫入的一列常駐授權」。
type importTarget struct {
	// ID 是穩定推導出來的 scope_targets.id（冪等鍵）。
	ID string
	// Owner 是授權擁有者。
	Owner string
	// TargetType 是 host／wildcard／cidr／url_prefix。
	TargetType string
	// TargetValue 是目標值。
	TargetValue string
	// ActionClasses 是容許的動作類別（空陣列＝一般類別）。
	ActionClasses []string
	// ValidUntil 是有效期限（nil＝無期限）。
	ValidUntil *time.Time
	// Provenance 是來源說明。
	Provenance database.ScopeProvenance
}

// importResult 是一份來源的匯入結果統計。
type importResult struct {
	// Imported 是寫入（或模擬寫入）的筆數。
	Imported int
	// Skipped 是跳過的筆數。
	Skipped int
	// Errors 是錯誤筆數。
	Errors int
	// Warnings 是警告訊息。
	Warnings []string
}

func main() {
	var (
		configPath = flag.String("config", "config.yaml", "平台 config.yaml 路徑（取資料庫位置）")
		sourcePath = flag.String("source", "", "要匯入的授權 JSON（可重複指定；也可以給目錄）")
		ownerFlag  = flag.String("owner", "", "覆寫匯入項目的 owner（留空則用來源檔的 scope 鍵）")
		dryRun     = flag.Bool("dry-run", false, "只印出將會寫入的項目，不寫資料庫")
		showHelp   = flag.Bool("help", false, "顯示說明")
	)
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, `scopeimport — 把既有授權 JSON 匯入 Scope Registry（scope_targets）

用法:
  scopeimport --config <config.yaml> --source <_授權.json> [選項]

選項:
  --config <path>    平台 config.yaml 路徑（用來取得 database.path）；未指定時預設 config.yaml
  --source <path>    要匯入的授權 JSON；可重複指定，或指定一個目錄（會匯入目錄內所有 *.json）
  --owner <name>     覆寫匯入項目的 owner（留空則用來源檔的 scope 鍵）
  --dry-run          只印出將會寫入的項目，完全不碰資料庫
  --help             顯示這份說明

行為:
  - 禁區（119／EPCR／消防救護）目標一律跳過並警告，不會寫進 registry。
  - 冪等：同一份來源重跑不會產生重續列（冪等鍵 = owner + target_type + target_value）。
  - authorized_until 解析失敗只警告並留空有效期限，不會讓整份匯入失敗。
`)
	}
	flag.Parse()

	if *showHelp {
		flag.Usage()
		return
	}

	sources, err := collectSources(*sourcePath, flag.Args())
	if err != nil {
		fmt.Fprintf(os.Stderr, "錯誤: %v\n", err)
		os.Exit(2)
	}
	if len(sources) == 0 {
		fmt.Fprintln(os.Stderr, "錯誤: 沒有指定 --source（可重複指定或給一個目錄）")
		flag.Usage()
		os.Exit(2)
	}

	if *dryRun {
		runImport(sources, *ownerFlag, nil)
		return
	}

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

	fmt.Printf("資料庫: %s\n", dbPath)
	runImport(sources, *ownerFlag, db)
}

// runImport 匯入所有來源。
//
// q 為 nil 代表 dry-run（只統計與列印，不寫資料庫）。
func runImport(sources []string, ownerOverride string, q database.QueryerLike) {
	total := importResult{}
	for _, source := range sources {
		result := importOne(source, ownerOverride, q)
		total.Imported += result.Imported
		total.Skipped += result.Skipped
		total.Errors += result.Errors
		total.Warnings = append(total.Warnings, result.Warnings...)
	}
	fmt.Println()
	fmt.Println("==================== 匯入結果 ====================")
	fmt.Printf("匯入筆數: %d\n", total.Imported)
	fmt.Printf("跳過筆數: %d\n", total.Skipped)
	fmt.Printf("錯誤筆數: %d\n", total.Errors)
	if len(total.Warnings) > 0 {
		fmt.Printf("警告筆數: %d\n", len(total.Warnings))
		for _, warning := range total.Warnings {
			fmt.Printf("  ! %s\n", warning)
		}
	}
}

// importOne 匯入單一來源檔。
func importOne(path, ownerOverride string, q database.QueryerLike) importResult {
	result := importResult{}
	fmt.Printf("\n--- 來源: %s ---\n", path)

	data, err := os.ReadFile(path)
	if err != nil {
		result.Errors++
		fmt.Printf("  讀取失敗: %v\n", err)
		return result
	}
	entries, err := parseAuthFile(data)
	if err != nil {
		result.Errors++
		fmt.Printf("  解析失敗: %v\n", err)
		return result
	}
	sourceName := filepath.Base(path)

	for _, entry := range entries {
		targets, skipped, warnings := buildImportTargets(entry, ownerOverride, sourceName)
		result.Skipped += skipped
		result.Warnings = append(result.Warnings, warnings...)
		for _, target := range targets {
			if q == nil {
				result.Imported++
				fmt.Printf("  [dry-run] %-8s %-24s owner=%s classes=%v valid_until=%s\n",
					target.TargetType, target.TargetValue, target.Owner,
					target.ActionClasses, formatValidUntil(target.ValidUntil))
				continue
			}
			if err := database.UpsertScopeTarget(context.Background(), q, database.ScopeTarget{
				ID:            target.ID,
				Owner:         target.Owner,
				TargetType:    target.TargetType,
				TargetValue:   target.TargetValue,
				ActionClasses: target.ActionClasses,
				Conditions:    database.ScopeConditions{},
				ValidUntil:    target.ValidUntil,
				Provenance:    target.Provenance,
				Status:        database.ScopeTargetStatusActive,
				CreatedAt:     time.Now(),
			}); err != nil {
				result.Errors++
				fmt.Printf("  寫入失敗 (%s): %v\n", target.TargetValue, err)
				continue
			}
			result.Imported++
			fmt.Printf("  已匯入 %-8s %-24s owner=%s classes=%v valid_until=%s\n",
				target.TargetType, target.TargetValue, target.Owner,
				target.ActionClasses, formatValidUntil(target.ValidUntil))
		}
	}
	return result
}

// buildImportTargets 把一筆 scope 轉成要寫入的常駐授權列。
//
// 回傳：targets（要寫入的列）、skipped（跳過筆數）、warnings（警告）。
func buildImportTargets(entry authScopeEntry, ownerOverride, sourceName string) ([]importTarget, int, []string) {
	var (
		targets  []importTarget
		skipped  int
		warnings []string
	)
	if !entry.Scope.Authorized {
		skipped++
		fmt.Printf("  跳過（authorized=false）: %s\n", entry.Key)
		return nil, skipped, warnings
	}

	owner := strings.TrimSpace(ownerOverride)
	if owner == "" {
		owner = strings.TrimSpace(entry.Key)
	}
	if owner == "" {
		owner = "imported"
	}

	classes := normalizeClasses(entry.Scope.AllowedActionClasses)

	var validUntil *time.Time
	if raw := strings.TrimSpace(entry.Scope.AuthorizedUntil); raw != "" {
		parsed, err := parseValidUntil(raw)
		if err != nil {
			// 單筆時間壞掉不讓整份匯入失敗：留空有效期限並警告。
			warnings = append(warnings, fmt.Sprintf("%s: authorized_until %q 解析失敗，已留空有效期限", entry.Key, raw))
		} else {
			utc := parsed.UTC()
			validUntil = &utc
		}
	}

	decidedBy := strings.TrimSpace(entry.Scope.AuthorizedBy)
	note := fmt.Sprintf("由 scopeimport 匯入來源 %s 的 scope %q", sourceName, entry.Key)

	seen := make(map[string]struct{})
	for _, raw := range entry.Scope.AllowedHosts {
		host := strings.TrimSpace(raw)
		if host == "" {
			continue
		}
		// 禁區優先：119／EPCR／消防救護一律跳過，不寫進 registry。
		if reason := forbidden.Reason("", host, "", "", ""); reason != "" {
			skipped++
			warnings = append(warnings, fmt.Sprintf("%s: 目標 %s 命中禁區（%s），已跳過未匯入", entry.Key, host, reason))
			fmt.Printf("  跳過（禁區）: %s（%s）\n", host, reason)
			continue
		}
		targetType, targetValue := classifyHost(host)
		if targetValue == "" {
			skipped++
			warnings = append(warnings, fmt.Sprintf("%s: 目標 %q 無法解析，已跳過", entry.Key, host))
			continue
		}
		key := owner + "|" + targetType + "|" + targetValue
		if _, dup := seen[key]; dup {
			skipped++
			continue
		}
		seen[key] = struct{}{}
		targets = append(targets, importTarget{
			ID:            scopeTargetID(owner, targetType, targetValue),
			Owner:         owner,
			TargetType:    targetType,
			TargetValue:   targetValue,
			ActionClasses: classes,
			ValidUntil:    validUntil,
			Provenance: database.ScopeProvenance{
				Source:    sourceName,
				DecidedBy: decidedBy,
				DecidedAt: time.Now(),
				Note:      note,
			},
		})
	}
	return targets, skipped, warnings
}

// classifyHost 把來源檔的主機字串分類成 registry 的 (target_type, target_value)。
//
// 規則：*. 開頭 → wildcard；其餘 → host（URL／CIDR 也照原樣保留語意）。
func classifyHost(host string) (string, string) {
	trimmed := strings.TrimSpace(host)
	if trimmed == "" {
		return "", ""
	}
	target := scope.NormalizeTarget(trimmed)
	switch target.Kind {
	case scope.TargetWildcard:
		return database.ScopeTargetTypeWildcard, target.Host
	case scope.TargetCIDR:
		return database.ScopeTargetTypeCIDR, target.Host
	case scope.TargetURLPrefix:
		if target.URL != "" {
			return database.ScopeTargetTypeURLPrefix, target.URL
		}
		return database.ScopeTargetTypeHost, target.Host
	default:
		return database.ScopeTargetTypeHost, target.Host
	}
}

// scopeTargetID 依冪等鍵推導穩定的 scope_targets.id。
//
// 用雜湊而不是隨機 uuid：同一份來源重跑會 upsert 同一列，不會產生重複列。
func scopeTargetID(owner, targetType, targetValue string) string {
	sum := sha256.Sum256([]byte(strings.Join([]string{owner, targetType, targetValue}, "|")))
	return "scope_" + hex.EncodeToString(sum[:])[:32]
}

// parseAuthFile 解析授權 JSON。
//
// scopes 欄位同時支援「物件（鍵 → scope）」與「陣列」兩種形狀：
// 既有來源是物件，但別的工具產出的格式不保證一致。
func parseAuthFile(data []byte) ([]authScopeEntry, error) {
	var root struct {
		Version   int             `json:"version"`
		UpdatedAt string          `json:"updated_at"`
		Scopes    json.RawMessage `json:"scopes"`
	}
	if err := json.Unmarshal(data, &root); err != nil {
		return nil, fmt.Errorf("解析授權 JSON 失敗: %w", err)
	}
	if len(root.Scopes) == 0 {
		return nil, fmt.Errorf("授權 JSON 缺少 scopes 欄位")
	}
	var byKey map[string]authScope
	if err := json.Unmarshal(root.Scopes, &byKey); err == nil {
		keys := make([]string, 0, len(byKey))
		for key := range byKey {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		out := make([]authScopeEntry, 0, len(keys))
		for _, key := range keys {
			out = append(out, authScopeEntry{Key: key, Scope: byKey[key]})
		}
		return out, nil
	}
	var list []authScope
	if err := json.Unmarshal(root.Scopes, &list); err == nil {
		out := make([]authScopeEntry, 0, len(list))
		for index, item := range list {
			out = append(out, authScopeEntry{Key: fmt.Sprintf("scope_%d", index+1), Scope: item})
		}
		return out, nil
	}
	return nil, fmt.Errorf("無法解析 scopes 欄位（既不是物件也不是陣列）")
}

// normalizeClasses 正規化動作類別清單（去空白、去重、保持順序）。
func normalizeClasses(classes []string) []string {
	out := make([]string, 0, len(classes))
	seen := make(map[string]struct{})
	for _, class := range classes {
		trimmed := strings.TrimSpace(class)
		if trimmed == "" {
			continue
		}
		if _, dup := seen[trimmed]; dup {
			continue
		}
		seen[trimmed] = struct{}{}
		out = append(out, trimmed)
	}
	return out
}

// parseValidUntil 解析有效期限（RFC3339 或單純日期）。
func parseValidUntil(raw string) (time.Time, error) {
	layouts := []string{
		time.RFC3339Nano,
		time.RFC3339,
		"2006-01-02T15:04:05",
		"2006-01-02 15:04:05",
		"2006-01-02",
	}
	for _, layout := range layouts {
		if parsed, err := time.Parse(layout, raw); err == nil {
			return parsed, nil
		}
	}
	return time.Time{}, fmt.Errorf("不支援的時間格式")
}

// formatValidUntil 顯示有效期限。
func formatValidUntil(value *time.Time) string {
	if value == nil {
		return "-"
	}
	return value.UTC().Format(time.RFC3339)
}

// collectSources 收集要匯入的來源（檔案或目錄）。
func collectSources(source string, extra []string) ([]string, error) {
	var out []string
	add := func(path string) error {
		info, err := os.Stat(path)
		if err != nil {
			return err
		}
		if !info.IsDir() {
			out = append(out, path)
			return nil
		}
		entries, err := os.ReadDir(path)
		if err != nil {
			return err
		}
		for _, item := range entries {
			if item.IsDir() || !strings.EqualFold(filepath.Ext(item.Name()), ".json") {
				continue
			}
			out = append(out, filepath.Join(path, item.Name()))
		}
		return nil
	}
	if trimmed := strings.TrimSpace(source); trimmed != "" {
		if err := add(trimmed); err != nil {
			return nil, fmt.Errorf("讀取來源 %s 失敗: %w", trimmed, err)
		}
	}
	for _, item := range extra {
		if err := add(item); err != nil {
			return nil, fmt.Errorf("讀取來源 %s 失敗: %w", item, err)
		}
	}
	return out, nil
}

// resolveDatabasePath 從 config.yaml 取得資料庫位置（相對路徑以 config 所在目錄為準）。
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
