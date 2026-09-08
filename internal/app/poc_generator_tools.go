package app

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"cyberstrike-ai/internal/config"
	"cyberstrike-ai/internal/database"
	"cyberstrike-ai/internal/mcp"
	"cyberstrike-ai/internal/mcp/builtin"

	"go.uber.org/zap"
)

const pocDraftDirName = "poc_drafts"

var pocFilenameCleanRe = regexp.MustCompile(`[^\p{L}\p{N}\-_]+`)

// pocGeneratorOptions 是 generate_poc_draft 的執行參數。
type pocGeneratorOptions struct {
	vulnerabilityID     string
	scope               string
	severity            string
	status              string
	search              string
	limit               int
	onlyMissingEvidence bool
	writeEvidence       bool
	outputDir           string
}

// registerPocGeneratorTools 註冊「自動生成 POC/EXP 草稿」MCP 工具。
// 僅產生 markdown 草稿文件（並可選擇回寫到漏洞記錄的 evidence 欄位），不執行任何實際攻擊。
func registerPocGeneratorTools(mcpServer *mcp.Server, db *database.DB, cfg *config.Config, logger *zap.Logger) {
	tool := mcp.Tool{
		Name:             builtin.ToolGeneratePocDraft,
		Description:      "根据既有漏洞记录自动生成 POC/EXP 草稿文件（markdown，含复现步骤/验证要点/攻击链上下文），不执行任何实际攻击。可指定单条 vulnerability_id，或按 scope/severity/status 批量生成。生成的文件默认写入 data/poc_drafts/，并把草稿路径回写到漏洞记录的 evidence 栏位（仅追加，不覆盖）。",
		ShortDescription: "按漏洞记录生成 POC/EXP 草稿文件（仅草稿，不实际攻击）",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"vulnerability_id": map[string]interface{}{
					"type":        "string",
					"description": "指定单条漏洞 ID 生成；不传则按以下筛选条件批量生成",
				},
				"scope": map[string]interface{}{
					"type":        "string",
					"description": "批量范围：project（默认，需对话绑定项目）| conversation（仅当前会话）",
					"enum":        []string{"project", "conversation"},
				},
				"severity": map[string]interface{}{
					"type":        "string",
					"description": "按严重程度筛选：critical、high、medium、low、info",
					"enum":        []string{"critical", "high", "medium", "low", "info"},
				},
				"status": map[string]interface{}{
					"type":        "string",
					"description": "按状态筛选：open、confirmed、fixed、false_positive、ignored",
					"enum":        []string{"open", "confirmed", "fixed", "false_positive", "ignored"},
				},
				"q": map[string]interface{}{
					"type":        "string",
					"description": "关键词搜索（标题、描述、类型、目标等）",
				},
				"limit": map[string]interface{}{
					"type":        "integer",
					"description": "批量生成条数上限，默认 20，最大 100",
				},
				"only_missing_evidence": map[string]interface{}{
					"type":        "boolean",
					"description": "只处理尚无证据/POC 的漏洞，默认 true；false 则全部生成",
				},
				"write_evidence": map[string]interface{}{
					"type":        "boolean",
					"description": "生成后将草稿文件路径追加回写漏洞记录的 evidence 字段（仅追加标记，不覆盖已有内容），默认 true",
				},
				"output_dir": map[string]interface{}{
					"type":        "string",
					"description": "草稿输出目录，默认 <数据目录>/poc_drafts",
				},
			},
		},
	}

	mcpServer.RegisterTool(tool, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		convID := conversationIDFromToolCtx(ctx)
		if convID == "" {
			return textResult("错误: 无法确定当前对话，请在对话上下文中使用本工具", true), nil
		}

		opts := pocGeneratorOptions{
			vulnerabilityID:     strings.TrimSpace(strArg(args, "vulnerability_id")),
			scope:               strings.TrimSpace(strArg(args, "scope")),
			severity:            strings.TrimSpace(strArg(args, "severity")),
			status:              strings.TrimSpace(strArg(args, "status")),
			search:              strings.TrimSpace(strArg(args, "q")),
			limit:               intArg(args, "limit", 20),
			onlyMissingEvidence: boolArgDefault(args, "only_missing_evidence", true),
			writeEvidence:       boolArgDefault(args, "write_evidence", true),
			outputDir:           strings.TrimSpace(strArg(args, "output_dir")),
		}
		if opts.limit <= 0 || opts.limit > 100 {
			opts.limit = 20
		}

		targets := make([]*database.Vulnerability, 0)
		if opts.vulnerabilityID != "" {
			vuln, err := db.GetVulnerability(opts.vulnerabilityID)
			if err != nil {
				return textResult("错误: 漏洞不存在或查询失败", true), nil
			}
			projectID, _ := db.GetConversationProjectID(convID)
			if !canAccessVulnerability(vuln, convID, projectID) {
				return textResult("错误: 无权访问该漏洞（仅可访问当前项目或当前会话下的记录）", true), nil
			}
			targets = append(targets, vuln)
		} else {
			projectID := ""
			if pid, perr := db.GetConversationProjectID(convID); perr == nil {
				projectID = strings.TrimSpace(pid)
			}
			scope := opts.scope
			if scope == "" {
				if projectID != "" {
					scope = "project"
				} else {
					scope = "conversation"
				}
			}
			var filter database.VulnerabilityListFilter
			switch scope {
			case "project":
				if projectID == "" {
					return textResult("错误: 当前对话未绑定项目，无法按项目批量生成；请使用 scope=conversation，或先在对话中绑定项目", true), nil
				}
				filter.ProjectID = projectID
			case "conversation":
				filter.ConversationID = convID
			default:
				return textResult(fmt.Sprintf("错误: scope 仅支持 project 或 conversation，当前值: %s", scope), true), nil
			}
			filter.Severity = opts.severity
			filter.Status = opts.status
			filter.Search = opts.search

			list, err := db.ListVulnerabilities(opts.limit, 0, filter)
			if err != nil {
				return textResult("错误: "+err.Error(), true), nil
			}
			for _, v := range list {
				if opts.onlyMissingEvidence && strings.TrimSpace(v.Evidence) != "" {
					continue
				}
				targets = append(targets, v)
			}
		}

		if len(targets) == 0 {
			return textResult("（没有符合条件的漏洞需要生成 POC/EXP 草稿）", false), nil
		}

		dataDir, err := resolveDataDir(cfg)
		if err != nil {
			return textResult("错误: "+err.Error(), true), nil
		}
		outDir := opts.outputDir
		if outDir == "" {
			outDir = filepath.Join(dataDir, pocDraftDirName)
		}
		if err := os.MkdirAll(outDir, 0o755); err != nil {
			return textResult("错误: 创建输出目录失败: "+err.Error(), true), nil
		}

		var b strings.Builder
		b.WriteString("POC/EXP 草稿生成结果\n\n")
		generated := 0
		for _, vuln := range targets {
			projectID, _ := db.GetConversationProjectID(convID)
			facts := pocContextFacts(db, vuln, projectID)
			content := buildPocDraftMarkdown(vuln, facts)
			relPath := pocFilenameFor(vuln)
			absPath := filepath.Join(outDir, relPath)
			if err := os.WriteFile(absPath, []byte(content+"\n"), 0o644); err != nil {
				b.WriteString(fmt.Sprintf("- %s | %s | 写入失败: %v\n", vuln.ID, vuln.Title, err))
				continue
			}
			if opts.writeEvidence {
				if err := appendPocDraftMarker(db, vuln, relPath); err != nil {
					b.WriteString(fmt.Sprintf("- %s | %s | evidence 回写失败: %v\n", vuln.ID, vuln.Title, err))
				}
			}
			b.WriteString(fmt.Sprintf("- id=%s | %s | 草稿: %s\n", vuln.ID, fmtVulnTitle(vuln), absPath))
			generated++
		}
		b.WriteString(fmt.Sprintf("\n共生成 %d 份草稿，保存至: %s\n", generated, outDir))
		b.WriteString("\n说明：以上为自动生成的 POC/EXP 草稿（含复现步骤与验证要点），未执行任何实际攻击；正式利用前须按 pentest-verification 规则人工验证并确认授权范围。")
		return textResult(b.String(), false), nil
	})

	if logger != nil {
		logger.Info("POC/EXP 草稿生成 MCP 工具注册成功", zap.String("tool", builtin.ToolGeneratePocDraft))
	}
}

// resolveDataDir 由数据库配置推导数据目录（config.yaml database.path 所在目录）。
func resolveDataDir(cfg *config.Config) (string, error) {
	if cfg == nil || strings.TrimSpace(cfg.Database.Path) == "" {
		return "data", nil
	}
	abs, err := filepath.Abs(filepath.Dir(cfg.Database.Path))
	if err != nil {
		return "data", err
	}
	return abs, nil
}

func fmtVulnTitle(v *database.Vulnerability) string {
	title := strings.TrimSpace(v.Title)
	if title == "" {
		return "（无标题）"
	}
	return title
}

// pocFilenameFor 生成安全的草稿文件名。
func pocFilenameFor(v *database.Vulnerability) string {
	slug := pocFilenameCleanRe.ReplaceAllString(strings.ToLower(v.Title), "-")
	slug = strings.Trim(slug, "-")
	if slug == "" {
		slug = "vuln"
	}
	if len(slug) > 60 {
		slug = slug[:60]
	}
	return fmt.Sprintf("%s-%s.md", v.ID, slug)
}

// pocContextFacts 收集与漏洞相关的项目事实（攻击链/利用/POC 上下文）。
func pocContextFacts(db *database.DB, vuln *database.Vulnerability, projectID string) []*database.ProjectFact {
	if db == nil || strings.TrimSpace(projectID) == "" {
		return nil
	}
	facts, err := db.ListProjectFactsForIndex(projectID, false)
	if err != nil {
		return nil
	}
	related := make([]*database.ProjectFact, 0)
	for _, f := range facts {
		cat := strings.ToLower(strings.TrimSpace(f.Category))
		if cat != "finding" && cat != "chain" && cat != "exploit" && cat != "poc" && cat != "note" {
			continue
		}
		if strings.TrimSpace(f.RelatedVulnerabilityID) != "" && strings.TrimSpace(f.RelatedVulnerabilityID) != vuln.ID {
			continue
		}
		related = append(related, f)
	}
	sort.SliceStable(related, func(i, j int) bool {
		return related[i].FactKey < related[j].FactKey
	})
	if len(related) > 10 {
		related = related[:10]
	}
	return related
}

// buildPocDraftMarkdown 根据漏洞记录与相关项目事实生成 POC/EXP 草稿。
func buildPocDraftMarkdown(v *database.Vulnerability, facts []*database.ProjectFact) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("# POC/EXP 草稿 - %s\n\n", fmtVulnTitle(v)))
	b.WriteString(fmt.Sprintf("> 自动生成时间: %s  |  状态: **草稿（未验证）**  |  文件: `%s`\n\n", time.Now().Format("2006-01-02 15:04:05"), pocFilenameFor(v)))

	b.WriteString("## 漏洞信息\n\n")
	fmtKV := func(label, value string) {
		if strings.TrimSpace(value) == "" {
			value = "（未记录）"
		}
		b.WriteString(fmt.Sprintf("- **%s**: %s\n", label, strings.ReplaceAll(value, "\n", " ")))
	}
	fmtKV("漏洞ID", v.ID)
	fmtKV("严重程度", v.Severity)
	fmtKV("状态", v.Status)
	fmtKV("类型", v.Type)
	fmtKV("目标", v.Target)
	if !v.CreatedAt.IsZero() {
		b.WriteString(fmt.Sprintf("- **发现时间**: %s\n", v.CreatedAt.Format("2006-01-02 15:04:05")))
	}
	b.WriteString("\n")

	if strings.TrimSpace(v.Description) != "" {
		b.WriteString("## 描述\n\n")
		b.WriteString(v.Description + "\n\n")
	}

	if strings.TrimSpace(v.Preconditions) != "" {
		b.WriteString("## 前置条件\n\n")
		b.WriteString(v.Preconditions + "\n\n")
	}

	b.WriteString("## POC/EXP 草稿\n\n")
	if respSteps := strings.TrimSpace(v.ReproSteps); respSteps != "" {
		b.WriteString("### 复现步骤（来自漏洞记录）\n\n")
		b.WriteString(renderNumberedBlocks(respSteps) + "\n\n")
	} else {
		b.WriteString("### 复现步骤（待补充）\n\n- （漏洞记录未保存复现步骤，请人工补全验证流程）\n\n")
	}

	b.WriteString("### 验证要点\n\n")
	verification := []string{
		"确认目标属于授权测试范围，且仅在正当授权下进行验证",
		"先复核漏洞类型与已知 CVE/公开信息（可用 cve-poc-emerging-intel / vuln-intel 交叉校验版本与 EXP 候选）",
		"使用最小化请求/命令逐步验证，记录原始请求/响应或命令输出作为证据",
		"验证失败时应记录负结果，避免误报；未经实际验证不得将状态改为 confirmed",
	}
	for _, line := range verification {
		b.WriteString(fmt.Sprintf("- [ ] %s\n", line))
	}
	b.WriteString("\n")

	if strings.TrimSpace(v.Evidence) != "" {
		b.WriteString("### 既有证据\n\n")
		b.WriteString("```\n" + strings.TrimRight(v.Evidence, "\n") + "\n```\n\n")
	}

	if len(facts) > 0 {
		b.WriteString("## 相关项目事实（攻击链上下文）\n\n")
		for _, f := range facts {
			b.WriteString(fmt.Sprintf("### %s (%s)\n\n", f.FactKey, f.Confidence))
			if strings.TrimSpace(f.Summary) != "" {
				b.WriteString(fmt.Sprintf("> %s\n\n", f.Summary))
			}
			if strings.TrimSpace(f.Body) != "" {
				b.WriteString(f.Body + "\n\n")
			}
		}
	}

	if strings.TrimSpace(v.Impact) != "" {
		b.WriteString("## 影响\n\n")
		b.WriteString(v.Impact + "\n\n")
	}
	if strings.TrimSpace(v.Recommendation) != "" {
		b.WriteString("## 修复建议\n\n")
		b.WriteString(v.Recommendation + "\n\n")
	}
	if strings.TrimSpace(v.RetestNotes) != "" {
		b.WriteString("## 复测方式\n\n")
		b.WriteString(v.RetestNotes + "\n\n")
	}

	b.WriteString("## 免责声明\n\n")
	b.WriteString("本文档由 generate_poc_draft 自动生成，仅为复现与验证参考，未执行任何实际攻击行为。请在获得明确书面授权的测试环境中使用。\n")
	return b.String()
}

// appendPocDraftMarker 把草稿路径回写到漏洞记录的 evidence 字段（仅追加，不覆盖）。
func appendPocDraftMarker(db *database.DB, vuln *database.Vulnerability, relPath string) error {
	marker := fmt.Sprintf("> [自动生成 POC/EXP 草稿] %s", relPath)
	if strings.Contains(vuln.Evidence, marker) {
		return nil
	}
	newEvidence := strings.TrimRight(vuln.Evidence, "\n")
	if newEvidence != "" {
		newEvidence += "\n\n"
	}
	newEvidence += marker
	updated := *vuln
	updated.Evidence = newEvidence
	return db.UpdateVulnerability(vuln.ID, &updated)
}

// renderNumberedBlocks 把记录中的步骤按行渲染为编号清单。
func renderNumberedBlocks(text string) string {
	lines := strings.Split(strings.TrimSpace(text), "\n")
	var staged []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		staged = append(staged, strings.TrimPrefix(strings.TrimPrefix(line, "- "), "1. "))
	}
	var b strings.Builder
	for i, line := range staged {
		b.WriteString(fmt.Sprintf("%d. %s\n", i+1, line))
	}
	return b.String()
}
