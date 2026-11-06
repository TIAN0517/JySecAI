// 授權書產生工具（離線版）。
//
// 平台本身也有 HTTP 端點（GET/POST /api/projects/:id/authorization-letter），這個 CLI
// 是同一套產生器的離線入口：直接對資料庫產生檔案，不需要啟動服務。
//
//	authletter --db /var/lib/jysecai/core/conversations.db \
//	           --project proj-123 --format md --output 授權書.md
//	authletter --db ... --project proj-123 --facts client.json --format html -o 授權書.html
//
// --facts 是一份 JSON，欄位與 authletter.Input 相同（client_name、client_approver…）。
// 這份檔案是「人填的事實」：工具只負責排版，不會替你補任何法律事實。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"jysecai/internal/authletter"
	"jysecai/internal/config"
	"jysecai/internal/database"

	_ "github.com/mattn/go-sqlite3"
	"go.uber.org/zap"
)

func main() {
	dbPath := flag.String("db", "", "path to the SQLite database")
	configPath := flag.String("config", "", "path to config.yaml (optional, for engagement vendor info)")
	projectID := flag.String("project", "", "project id")
	format := flag.String("format", "md", "output format: md or html")
	output := flag.String("output", "", "output file (stdout when empty)")
	factsPath := flag.String("facts", "", "optional JSON file with the client-side facts")
	flag.Parse()

	if strings.TrimSpace(*dbPath) == "" || strings.TrimSpace(*projectID) == "" {
		fmt.Fprintln(os.Stderr, "需要 --db 與 --project")
		flag.Usage()
		os.Exit(2)
	}

	logger := zap.NewNop()
	db, err := database.NewDB(*dbPath, logger)
	if err != nil {
		fmt.Fprintf(os.Stderr, "無法開啟資料庫: %v\n", err)
		os.Exit(1)
	}
	defer db.Close()

	project, err := db.GetProject(*projectID)
	if err != nil || project == nil {
		fmt.Fprintf(os.Stderr, "找不到專案 %s\n", *projectID)
		os.Exit(1)
	}

	in := authletter.Input{
		ProjectID:   project.ID,
		ProjectName: project.Name,
	}

	// 既有授權掃描任務裡的授權記錄（人工填寫並確認過的那筆）。
	if auth, ok := latestAuthorization(db, project.ID); ok {
		in.DocumentID = auth.ID
		in.Patterns = auth.TargetPatterns
		in.Operations = auth.Operations
		in.ValidFrom = auth.ValidFrom
		in.ValidUntil = auth.ValidUntil
		in.ClientApprover = auth.ApprovedBy
		in.SourceAttested = auth.Attested
	}

	// 人填的委託方資料覆蓋既有值。
	if strings.TrimSpace(*factsPath) != "" {
		raw, readErr := os.ReadFile(*factsPath)
		if readErr != nil {
			fmt.Fprintf(os.Stderr, "無法讀取 %s: %v\n", *factsPath, readErr)
			os.Exit(1)
		}
		var facts authletter.Input
		if jsonErr := json.Unmarshal(raw, &facts); jsonErr != nil {
			fmt.Fprintf(os.Stderr, "無法解析 %s: %v\n", *factsPath, jsonErr)
			os.Exit(1)
		}
		in = mergeFacts(in, facts)
	}

	// 乙方（受託方）來自平台設定。
	if strings.TrimSpace(*configPath) != "" {
		if cfg, cfgErr := config.Load(*configPath); cfgErr == nil {
			applyEngagement(&in, cfg)
		} else {
			fmt.Fprintf(os.Stderr, "警告：讀取設定檔失敗，乙方欄位留白: %v\n", cfgErr)
		}
	}

	result := authletter.Build(in, time.Now().UTC())

	payload := result.Markdown
	if strings.EqualFold(*format, "html") {
		payload = result.HTML
	}

	if strings.TrimSpace(*output) == "" {
		fmt.Print(payload)
	} else {
		if writeErr := os.WriteFile(*output, []byte(payload), 0o600); writeErr != nil {
			fmt.Fprintf(os.Stderr, "無法寫入 %s: %v\n", *output, writeErr)
			os.Exit(1)
		}
	}

	if !result.Qualified {
		fmt.Fprintf(os.Stderr, "\n草稿：尚缺 %d 項條件，簽署前請補齊\n", len(result.Gaps))
		for _, gap := range result.Gaps {
			fmt.Fprintf(os.Stderr, "  - %s\n", gap)
		}
	}
}

// authorizationRecord 是 security_ops_runs.authorization_json 的結構。
type authorizationRecord struct {
	ID             string    `json:"id"`
	ProjectID      string    `json:"projectId"`
	TargetPatterns []string  `json:"targetPatterns"`
	Operations     []string  `json:"operations"`
	ValidFrom      time.Time `json:"validFrom"`
	ValidUntil     time.Time `json:"validUntil"`
	ApprovedBy     string    `json:"approvedBy"`
	Attested       bool      `json:"attested"`
}

// latestAuthorization 取專案最近一筆帶有授權編號的授權記錄。
func latestAuthorization(db *database.DB, projectID string) (authorizationRecord, bool) {
	runs, err := db.ListSecurityOpsRuns("", projectID, true, 50)
	if err != nil {
		return authorizationRecord{}, false
	}
	for _, run := range runs {
		var auth authorizationRecord
		if jsonErr := json.Unmarshal([]byte(run.AuthorizationJSON), &auth); jsonErr != nil {
			continue
		}
		if strings.TrimSpace(auth.ID) != "" {
			return auth, true
		}
	}
	return authorizationRecord{}, false
}

// mergeFacts 以人填的資料覆蓋既有值（空值不覆蓋）。
func mergeFacts(base, overlay authletter.Input) authletter.Input {
	overlayString := func(target *string, value string) {
		if strings.TrimSpace(value) != "" {
			*target = value
		}
	}
	overlayString(&base.DocumentID, overlay.DocumentID)
	overlayString(&base.ClientName, overlay.ClientName)
	overlayString(&base.ClientTaxID, overlay.ClientTaxID)
	overlayString(&base.ClientAddress, overlay.ClientAddress)
	overlayString(&base.ClientApprover, overlay.ClientApprover)
	overlayString(&base.ClientApproverRole, overlay.ClientApproverRole)
	overlayString(&base.ClientContact, overlay.ClientContact)
	overlayString(&base.VendorName, overlay.VendorName)
	overlayString(&base.VendorTaxID, overlay.VendorTaxID)
	overlayString(&base.VendorAddress, overlay.VendorAddress)
	overlayString(&base.VendorLead, overlay.VendorLead)
	overlayString(&base.VendorReference, overlay.VendorReference)
	overlayString(&base.Objective, overlay.Objective)
	if !overlay.IssuedAt.IsZero() {
		base.IssuedAt = overlay.IssuedAt
	}
	if !overlay.ValidFrom.IsZero() {
		base.ValidFrom = overlay.ValidFrom
	}
	if !overlay.ValidUntil.IsZero() {
		base.ValidUntil = overlay.ValidUntil
	}
	if len(overlay.Patterns) > 0 {
		base.Patterns = overlay.Patterns
	}
	if len(overlay.Operations) > 0 {
		base.Operations = overlay.Operations
	}
	if len(overlay.Notes) > 0 {
		base.Notes = overlay.Notes
	}
	if overlay.SourceAttested {
		base.SourceAttested = true
	}
	return base
}

// applyEngagement 套用平台設定的乙方資料。
func applyEngagement(in *authletter.Input, cfg *config.Config) {
	if cfg == nil {
		return
	}
	if strings.TrimSpace(in.VendorName) == "" {
		in.VendorName = cfg.Engagement.VendorName
	}
	if strings.TrimSpace(in.VendorTaxID) == "" {
		in.VendorTaxID = cfg.Engagement.VendorTaxID
	}
	if strings.TrimSpace(in.VendorAddress) == "" {
		in.VendorAddress = cfg.Engagement.VendorAddress
	}
	if strings.TrimSpace(in.VendorLead) == "" {
		in.VendorLead = cfg.Engagement.VendorLead
	}
	if strings.TrimSpace(in.VendorReference) == "" {
		in.VendorReference = cfg.Engagement.VendorReference
	}
}
