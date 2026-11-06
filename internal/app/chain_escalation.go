package app

import (
	"context"
	"fmt"
	"strings"

	"jysecai/internal/authctx"
	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"

	"go.uber.org/zap"
)

// 攻擊鏈升級：把兩條以上「各自已落庫、已驗證」的發現，串成一條可交付的鏈式發現。
//
// 為什麼要單獨一個工具：record_vulnerability 一次只能記一個缺陷，但真正能讓委託方
// 立即排程修的往往是「A 單看是中危、B 單看是中危、串起來就是接管」。這裡把串接這件事
// 變成平台層的原子操作 —— Agent 只要給出環節與最終影響，鏈的嚴重度、證據、置信度
// 都由平台依既有規則算，不靠模型自述。
//
// 兩條不動的規矩：
//   - 證據紀律：任一環節沒有 evidence，整條鏈不成立（弱環節會拖垮整條鏈）。
//   - 弱鏈決定置信度：鏈的 confidence 取所有環節的最小值。模型不能靠「鏈很酷」抬高分數。

// chainSeverityRank 嚴重度排序，數字越大越嚴重。
func chainSeverityRank(severity string) int {
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

// chainSeverityLabel 把排序值轉回合法 severity 字串。
func chainSeverityLabel(rank int) string {
	switch {
	case rank >= 5:
		return "critical"
	case rank == 4:
		return "high"
	case rank == 3:
		return "medium"
	case rank == 2:
		return "low"
	case rank == 1:
		return "info"
	default:
		return "medium"
	}
}

// chainCriticalImpactKeywords 是「整條鏈足以構成 critical」的影響特徵。
//
// 這是影響面的判斷，不是證據面的判斷 —— 證據面由 confidence 與 evidence 決定。
// 命中只代表「若鏈成立，後果是 critical」，不代表「已證實可利用」。
var chainCriticalImpactKeywords = []string{
	"遠端代碼執行", "遠端代码执行", "遠端程式碼執行", "remote code execution", "rce",
	"命令執行", "命令执行", "系統命令", "系统命令", "os command",
	"拿下 shell", "取得 shell", "獲取 shell", "webshell", "反彈 shell", "反弹shell", "reverse shell",
	"接管", "takeover", "帳號接管", "账号接管", "账户接管", "account takeover",
	"提權", "提权", "權限提升", "权限提升", "privilege escalation",
	"越權", "越权", "跨租戶", "跨租户", "垂直越權", "垂直越权",
	"任意檔案", "任意文件", "任意讀取", "任意读取", "任意寫入", "任意写入", "任意檔案讀寫",
	"資料外洩", "資料泄露", "数据外泄", "数据泄露", "個資外洩", "个资泄露", "個資洩漏",
	"憑據外洩", "凭证外泄", "憑證外洩", "凭证泄露", "金鑰外洩",
	"root 權限", "root权限", "系統權限", "系统权限", "administrator 權限",
	"交易接管", "金流接管", "接管金流",
}

// chainImpactImpliesCritical 判斷最終影響是否達到 critical 級別。
func chainImpactImpliesCritical(impact string) bool {
	lowered := strings.ToLower(impact)
	if strings.TrimSpace(lowered) == "" {
		return false
	}
	for _, keyword := range chainCriticalImpactKeywords {
		if strings.Contains(lowered, strings.ToLower(keyword)) {
			return true
		}
	}
	return false
}

// ChainStep 是攻擊鏈中的一環：一條已落庫、有證據的漏洞。
type ChainStep struct {
	ID         string
	Title      string
	Severity   string
	Confidence int
	Type       string
	TypeRaw    string
	Target     string
	Evidence   string
	ReproSteps string
}

// ChainInput 是鏈式發現的組裝輸入。
type ChainInput struct {
	Steps     []ChainStep
	Impact    string
	Target    string
	Title     string
	StepNotes []string
}

// buildChainVulnerability 依既有平台規則把環節組裝成一條可交付的鏈式漏洞。
//
// 嚴重度：取所有環節的最高嚴重度；若鏈有 2 環以上、且最終影響命中 critical 特徵
// （資料外洩／接管／遠端執行等）且至少一環是 medium 以上，則升為 critical —— 單看
// 每一步都不致命、串起來能接管的情況正是這裡要捕捉的。
//
// 置信度：取所有環節的最小值。鏈上任何一環沒被證實，整條鏈就不能算已確認。
func buildChainVulnerability(in ChainInput) (*database.Vulnerability, error) {
	if len(in.Steps) < 2 {
		return nil, fmt.Errorf("攻擊鏈至少需要 2 個環節，目前 %d 個", len(in.Steps))
	}
	for _, step := range in.Steps {
		if strings.TrimSpace(step.Evidence) == "" {
			return nil, fmt.Errorf("環節 %s（%s）沒有證據：鏈上任何一環缺少可復現證據，整條鏈都不成立。請先補齊該環節的 evidence 再串鏈。",
				step.ID, step.Title)
		}
	}

	maxRank := 0
	minConfidence := 100
	terminal := in.Steps[0]
	for _, step := range in.Steps {
		if rank := chainSeverityRank(step.Severity); rank > maxRank {
			maxRank = rank
		}
		if step.Confidence < minConfidence {
			minConfidence = step.Confidence
		}
		// 終點取最高嚴重度環節；同級時取後面那個（後面＝離最終影響更近）。
		if rank := chainSeverityRank(step.Severity); rank >= chainSeverityRank(terminal.Severity) {
			terminal = step
		}
	}

	severity := chainSeverityLabel(maxRank)
	if maxRank >= chainSeverityRank("medium") && chainImpactImpliesCritical(in.Impact) {
		severity = "critical"
	}

	target := strings.TrimSpace(in.Target)
	if target == "" {
		target = strings.TrimSpace(terminal.Target)
	}

	title := strings.TrimSpace(in.Title)
	if title == "" {
		title = buildChainTitle(in.Steps)
	}

	evidence := buildChainEvidence(in.Steps, in.Impact)
	repro := buildChainReproSteps(in.Steps, in.StepNotes)

	// 型別取終點環節的原始型別，讓分類器照原規則判定（終點決定這條鏈到底是什麼漏洞）。
	chainType := strings.TrimSpace(terminal.TypeRaw)
	if chainType == "" {
		chainType = strings.TrimSpace(terminal.Type)
	}
	if chainType == "" {
		chainType = "business-logic"
	}

	status := database.VulnerabilityStatusOpen
	if minConfidence >= database.VulnerabilityConfirmConfidenceThreshold {
		status = database.VulnerabilityStatusConfirmed
	}

	return &database.Vulnerability{
		Title:          title,
		Description:    buildChainDescription(in.Steps, in.Impact),
		Severity:       severity,
		Status:         status,
		Confidence:     minConfidence,
		Type:           chainType,
		Target:         target,
		Preconditions:  buildChainPreconditions(in.Steps),
		ReproSteps:     repro,
		Evidence:       evidence,
		Impact:         strings.TrimSpace(in.Impact),
		Recommendation: buildChainRecommendation(in.Steps),
		RetestNotes:    buildChainRetestNotes(in.Steps),
	}, nil
}

// buildChainTitle 產生預設標題：攻擊鏈：起點 → 終點。
func buildChainTitle(steps []ChainStep) string {
	parts := make([]string, 0, len(steps))
	for _, step := range steps {
		parts = append(parts, strings.TrimSpace(step.Title))
	}
	title := "攻擊鏈：" + strings.Join(parts, " → ")
	if runes := []rune(title); len(runes) > 160 {
		return string(runes[:160]) + "…"
	}
	return title
}

// buildChainDescription 說明這條鏈是怎麼串起來的。
func buildChainDescription(steps []ChainStep, impact string) string {
	var b strings.Builder
	b.WriteString("多步驟攻擊鏈（")
	for i, step := range steps {
		if i > 0 {
			b.WriteString(" → ")
		}
		b.WriteString(strings.TrimSpace(step.Title))
	}
	b.WriteString("）。單獨看各環節未必是最嚴重的缺陷，串起來後的最終影響為：")
	b.WriteString(strings.TrimSpace(impact))
	b.WriteString("\n各環節對應的已確認漏洞記錄見 evidence 欄位的編號，可逐一複核。")
	return b.String()
}

// buildChainPreconditions 彙整各環節的前置條件。
func buildChainPreconditions(steps []ChainStep) string {
	lines := make([]string, 0, len(steps))
	for i, step := range steps {
		if strings.TrimSpace(step.ReproSteps) == "" {
			continue
		}
		lines = append(lines, fmt.Sprintf("%d. %s", i+1, strings.TrimSpace(step.ReproSteps)))
	}
	if len(lines) == 0 {
		return ""
	}
	return strings.Join(lines, "\n")
}

// buildChainEvidence 把每個環節的證據依序串起來，並標明來源漏洞 ID。
func buildChainEvidence(steps []ChainStep, impact string) string {
	var b strings.Builder
	b.WriteString("攻擊鏈證據（起點 → 終點）：\n")
	for i, step := range steps {
		fmt.Fprintf(&b, "\n[%d] %s\n", i+1, strings.TrimSpace(step.Title))
		fmt.Fprintf(&b, "    來源漏洞 ID: %s | 嚴重度: %s | 證據可信度: %d/100\n",
			step.ID, step.Severity, step.Confidence)
		fmt.Fprintf(&b, "    證據：\n%s\n", strings.TrimSpace(step.Evidence))
	}
	if strings.TrimSpace(impact) != "" {
		fmt.Fprintf(&b, "\n鏈的最終影響：%s", strings.TrimSpace(impact))
	}
	return b.String()
}

// buildChainReproSteps 依序組合各環節的復現步驟；呼叫端有提供 step_notes 時以它為準。
func buildChainReproSteps(steps []ChainStep, notes []string) string {
	var b strings.Builder
	for i, step := range steps {
		if i > 0 {
			b.WriteString("\n")
		}
		note := ""
		if i < len(notes) {
			note = strings.TrimSpace(notes[i])
		}
		if note == "" {
			note = strings.TrimSpace(step.ReproSteps)
		}
		if note == "" {
			note = strings.TrimSpace(step.Title)
		}
		fmt.Fprintf(&b, "%d. %s", i+1, note)
	}
	return b.String()
}

// buildChainRecommendation 依環節彙整修復建議：鏈要斷在任一環節，重點是先斷影響最大的那一環。
func buildChainRecommendation(steps []ChainStep) string {
	var b strings.Builder
	b.WriteString("本條為多步驟攻擊鏈，修復應以「切斷鏈路」為目標：以下任一環節被修好即可中斷整條鏈。\n")
	for i, step := range steps {
		fmt.Fprintf(&b, "%d. [%s] %s —— 針對此環節做存取控制／輸入驗證／最小權限修補，使其無法成為鏈的下一跳。\n",
			i+1, step.ID, strings.TrimSpace(step.Title))
	}
	b.WriteString("另請以「單點高危」為目標做橫向盤點：確認其他端點不存在同型缺陷，避免只補到本鏈的一條路徑。")
	return b.String()
}

// buildChainRetestNotes 說明如何複測整條鏈。
func buildChainRetestNotes(steps []ChainStep) string {
	var b strings.Builder
	b.WriteString("複測時須整條鏈重走，而非只測單一環節：依序重放 evidence 欄位的各環節證據，")
	b.WriteString("確認任一環節已失效（該環節的原始響應不再復現）即視為鏈路中斷。")
	if len(steps) > 0 {
		fmt.Fprintf(&b, "\n起點環節：%s", strings.TrimSpace(steps[0].Title))
		fmt.Fprintf(&b, "\n終點環節：%s", strings.TrimSpace(steps[len(steps)-1].Title))
	}
	return b.String()
}

// registerEscalateFindingsChainTool 註冊攻擊鏈升級工具。
func registerEscalateFindingsChainTool(mcpServer *mcp.Server, db *database.DB, logger *zap.Logger) {
	tool := mcp.Tool{
		Name: builtin.ToolEscalateFindingsChain,
		Description: "把兩條以上已落庫的漏洞串成一條可交付的攻擊鏈發現。用途：多個單點缺陷串起來能造成接管／資料外洩／遠端執行，但每一條單獨看都不夠嚴重。\n" +
			"平台自行計算鏈的嚴重度（取最高影響環節，最終影響命中接管／外洩／遠端執行等特徵時升為 critical）與置信度（取最弱環節，任一環節沒有 evidence 就不成立）。\n" +
			"要求：finding_ids 至少 2 個、每個都必須有 evidence；impact 必填，寫清楚這條鏈最終能做到什麼；step_notes 可選，依序描述每個環節在鏈中的角色。\n" +
			"串接完成後會自動落庫為新漏洞並寫入黑板 chain/ 事實。",
		ShortDescription: "把多條已確認漏洞升級串成攻擊鏈發現",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"finding_ids": map[string]interface{}{
					"type":        "array",
					"description": "要串接的漏洞 ID 列表（至少 2 個，依攻擊順序排列：起點在前）。每條都必須已有 evidence。",
					"minItems":    2,
					"items":       map[string]interface{}{"type": "string"},
				},
				"impact": map[string]interface{}{
					"type":        "string",
					"description": "整條鏈的最終影響（必填）：鏈走完之後實際能做到什麼，例如「取得任意使用者 Session 並接管後台」。這段文字決定鏈的嚴重度判定，請寫具體後果。",
				},
				"target": map[string]interface{}{
					"type":        "string",
					"description": "受影響目標（可選）：留空則取終點環節的 target。",
				},
				"title": map[string]interface{}{
					"type":        "string",
					"description": "鏈的標題（可選）：留空自動產生「攻擊鏈：起點 → 終點」。",
				},
				"step_notes": map[string]interface{}{
					"type":        "array",
					"description": "各環節在鏈中的角色說明（可選），與 finding_ids 一一對應。例如「取得內網 API Token」「以該 Token 呼叫後台匯出功能」「匯出全量客戶資料」。",
					"items":       map[string]interface{}{"type": "string"},
				},
			},
			"required": []string{"finding_ids", "impact"},
		},
	}

	mcpServer.RegisterTool(tool, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		conversationID := conversationIDFromToolCtx(ctx)
		if conversationID == "" {
			return textResult("错误: 无法确定当前对话，请在对话上下文中使用攻击链工具", true), nil
		}

		rawIDs, err := stringSliceArg(args["finding_ids"])
		if err != nil {
			return textResult(fmt.Sprintf("错误: finding_ids 必须是字符串数组: %v", err), true), nil
		}
		if len(rawIDs) < 2 {
			return textResult("错误: 攻击链至少需要 2 个 finding_ids", true), nil
		}

		projectID := ""
		if pid, perr := db.GetConversationProjectID(conversationID); perr == nil {
			projectID = strings.TrimSpace(pid)
		}

		steps := make([]ChainStep, 0, len(rawIDs))
		for _, rawID := range rawIDs {
			id := strings.TrimSpace(rawID)
			if id == "" {
				continue
			}
			vuln, verr := db.GetVulnerability(id)
			if verr != nil {
				return textResult(fmt.Sprintf("错误: 读取漏洞 %s 失败: %v", id, verr), true), nil
			}
			if vuln == nil {
				return textResult(fmt.Sprintf("错误: 找不到漏洞 %s", id), true), nil
			}
			if !canAccessVulnerabilityWithPrincipal(ctx, db, vuln, conversationID, projectID, "vulnerability:write") {
				return textResult(fmt.Sprintf("错误: 无权访问漏洞 %s（%s），无法将其纳入攻击链", id, vuln.Title), true), nil
			}
			steps = append(steps, ChainStep{
				ID:         vuln.ID,
				Title:      vuln.Title,
				Severity:   vuln.Severity,
				Confidence: vuln.Confidence,
				Type:       vuln.Type,
				TypeRaw:    vuln.TypeRaw,
				Target:     vuln.Target,
				Evidence:   vuln.Evidence,
				ReproSteps: vuln.ReproSteps,
			})
		}
		if len(steps) < 2 {
			return textResult("错误: 攻击链至少需要 2 个有效 finding_ids", true), nil
		}

		notes := []string{}
		if rawNotes, nerr := stringSliceArg(args["step_notes"]); nerr == nil {
			notes = rawNotes
		}

		chain, berr := buildChainVulnerability(ChainInput{
			Steps:     steps,
			Impact:    strArg(args, "impact"),
			Target:    strArg(args, "target"),
			Title:     strArg(args, "title"),
			StepNotes: notes,
		})
		if berr != nil {
			return textResult("错误: "+berr.Error(), true), nil
		}

		chain.ConversationID = conversationID
		chain.ProjectID = projectID

		created, cerr := db.CreateVulnerability(chain)
		if cerr != nil {
			if logger != nil {
				logger.Error("记录攻击链失败", zap.Error(cerr))
			}
			return textResult(fmt.Sprintf("记录攻击链失败: %v", cerr), true), nil
		}
		if !created.Deduplicated {
			if principal, ok := authctx.PrincipalFromContext(ctx); ok {
				_ = db.SetResourceOwner("vulnerability", created.ID, principal.UserID)
				_ = db.AssignResourceToUser(principal.UserID, "vulnerability", created.ID)
			}
			db.NotifyVulnerabilityCreated(created)
		}

		// 黑板同步：鏈本身是一條 chain/ 事實，環節之間用 edges 連起來。
		if projectID != "" {
			recordChainFact(db, projectID, conversationID, created, steps)
		}

		if logger != nil {
			logger.Info("攻击链记录完成",
				zap.String("id", created.ID),
				zap.String("severity", created.Severity),
				zap.Int("confidence", created.Confidence),
				zap.Int("steps", len(steps)),
				zap.Bool("deduplicated", created.Deduplicated),
			)
		}

		if created.Deduplicated {
			return textResult(fmt.Sprintf("攻击链已存在，已把这次的更强证据合并进既有记录。\n\n漏洞ID: %s\n标题: %s\n严重程度: %s\n状态: %s\n证据可信度: %d/100",
				created.ID, created.Title, created.Severity, created.Status, created.Confidence), false), nil
		}
		return textResult(fmt.Sprintf("攻击链已记录！\n\n漏洞ID: %s\n标题: %s\n严重程度: %s\n状态: %s\n证据可信度: %d/100\n环节数: %d\n\n置信度取自最弱环节——链上任何一环没有客观证据，这条链就不能算已确认。",
			created.ID, created.Title, created.Severity, created.Status, created.Confidence, len(steps)), false), nil
	})
}
