package app

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"
	"jysecai/internal/poc"

	"go.uber.org/zap"
)

const pocDraftDirName = "poc_drafts"

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

	// 注册 POC 在线弱验证工具
	verifyTool := mcp.Tool{
		Name:             builtin.ToolVerifyPoc,
		Description:      "对 HTTP/HTTPS 漏洞进行在线非破坏性弱探测与特征验证。支持指定 vulnerability_id（自动读取其目标与上下文）或直接指定 target_url；支持配置 HTTP 方法、自定义标头、请求体，以及匹配预期 HTTP 状态码、响应体文本子串或正则表达式。若验证匹配成功且 update_status=true，会自动将漏洞状态标记为 confirmed 并追加验证证据。",
		ShortDescription: "对 HTTP 目标执行非破坏性 POC 在线弱验证与特征匹配",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"vulnerability_id": map[string]interface{}{
					"type":        "string",
					"description": "可选：指定要验证的系统漏洞 ID；若未提供 target_url 则自动提取该漏洞记录的 target",
				},
				"target_url": map[string]interface{}{
					"type":        "string",
					"description": "可选：直接指定待探测的完整 HTTP/HTTPS URL；若与 vulnerability_id 同时提供则优先使用 target_url",
				},
				"method": map[string]interface{}{
					"type":        "string",
					"description": "HTTP 请求方法：GET, POST, HEAD, OPTIONS, PUT, DELETE, PATCH，默认 GET",
					"enum":        []string{"GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"},
				},
				"headers": map[string]interface{}{
					"type":        "object",
					"description": "可选：自定义 HTTP 请求标头 Key-Value 映射",
				},
				"body": map[string]interface{}{
					"type":        "string",
					"description": "可选：POST/PUT 等请求的 Payload 内容（仅限最小化无害探测数据）",
				},
				"match_status": map[string]interface{}{
					"type":        "integer",
					"description": "可选：预期响应 HTTP 状态码（如 200, 403, 500 等）",
				},
				"match_string": map[string]interface{}{
					"type":        "string",
					"description": "可选：预期在响应体中包含的关键特征子字符串",
				},
				"match_regex": map[string]interface{}{
					"type":        "string",
					"description": "可选：预期在响应体中命中的正则表达式模式",
				},
				"timeout_seconds": map[string]interface{}{
					"type":        "integer",
					"description": "请求超时时间（秒），默认 10，最大 30",
				},
				"update_status": map[string]interface{}{
					"type":        "boolean",
					"description": "若验证成功且提供了 vulnerability_id，是否自动将漏洞状态更新为 confirmed 并追加验证标记，默认 true",
				},
			},
		},
	}

	mcpServer.RegisterTool(verifyTool, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		vulnID := strings.TrimSpace(strArg(args, "vulnerability_id"))
		targetURL := strings.TrimSpace(strArg(args, "target_url"))
		method := strings.TrimSpace(strArg(args, "method"))
		body := strArg(args, "body")
		matchStatus := intArg(args, "match_status", 0)
		matchString := strings.TrimSpace(strArg(args, "match_string"))
		matchRegex := strings.TrimSpace(strArg(args, "match_regex"))
		timeoutSec := intArg(args, "timeout_seconds", 10)
		updateStatus := boolArgDefault(args, "update_status", true)

		var headersMap map[string]string
		if hRaw, ok := args["headers"].(map[string]interface{}); ok {
			headersMap = make(map[string]string)
			for k, v := range hRaw {
				headersMap[k] = fmt.Sprint(v)
			}
		}

		convID := conversationIDFromToolCtx(ctx)
		if vulnID != "" && db != nil {
			vuln, err := db.GetVulnerability(vulnID)
			if err != nil {
				return textResult("错误: 指定的漏洞 ID 不存在", true), nil
			}
			projectID, _ := db.GetConversationProjectID(convID)
			if convID != "" && !canAccessVulnerability(vuln, convID, projectID) {
				return textResult("错误: 无权访问该漏洞记录", true), nil
			}
		}

		spec := &poc.VerifyPocSpec{
			VulnerabilityID: vulnID,
			TargetURL:       targetURL,
			Method:          method,
			Headers:         headersMap,
			Body:            body,
			MatchStatus:     matchStatus,
			MatchString:     matchString,
			MatchRegex:      matchRegex,
			TimeoutSeconds:  timeoutSec,
		}

		res, err := poc.VerifyPoc(ctx, db, spec, updateStatus)
		if err != nil {
			return textResult("POC 验证失败: "+err.Error(), true), nil
		}

		var b strings.Builder
		b.WriteString("# POC 在线弱验证结果\n\n")
		b.WriteString(fmt.Sprintf("- **目标 URL**: `%s`\n", res.TargetURL))
		b.WriteString(fmt.Sprintf("- **请求方法**: `%s`\n", res.Method))
		if res.Error != "" {
			b.WriteString(fmt.Sprintf("- **执行状态**: ❌ **请求失败** (`%s`)\n", res.Error))
		} else {
			if res.Verified {
				b.WriteString("- **验证判定**: 🎯 **验证通过 (Vulnerability Confirmed)**\n")
			} else {
				b.WriteString("- **验证判定**: ⚠️ **特征未完全匹配 / 未确认**\n")
			}
			b.WriteString(fmt.Sprintf("- **HTTP 状态码**: %d (%s)\n", res.StatusCode, res.StatusText))
			b.WriteString(fmt.Sprintf("- **响应耗时**: %d ms\n", res.ResponseTimeMs))
			if len(res.MatchedConditions) > 0 {
				b.WriteString(fmt.Sprintf("- **命中匹配项**: %s\n", strings.Join(res.MatchedConditions, " | ")))
			}
			if res.UpdatedVulnerability {
				b.WriteString(fmt.Sprintf("- **漏洞库联动**: 漏洞 `%s` 状态已自动更新为 `confirmed` 并回写证据\n", res.VulnerabilityID))
			}
			if len(res.ResponseHeaders) > 0 {
				b.WriteString("\n### 关键响应头\n```http\n")
				for k, v := range res.ResponseHeaders {
					b.WriteString(fmt.Sprintf("%s: %s\n", k, v))
				}
				b.WriteString("```\n")
			}
			if res.ResponseSnippet != "" {
				b.WriteString("\n### 响应内容预览 (Safe Snippet)\n```\n")
				b.WriteString(res.ResponseSnippet)
				b.WriteString("\n```\n")
			}
		}

		return textResult(b.String(), false), nil
	})

	if logger != nil {
		logger.Info("POC/EXP 工具注册成功",
			zap.Strings("tools", []string{
				builtin.ToolGeneratePocDraft,
				builtin.ToolVerifyPoc,
			}),
		)
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

// Forwarding wrappers to internal/poc to ensure single source of truth and full test compatibility:
func pocFilenameFor(v *database.Vulnerability) string {
	return poc.PocFilenameFor(v)
}

func pocContextFacts(db *database.DB, vuln *database.Vulnerability, projectID string) []*database.ProjectFact {
	return poc.PocContextFacts(db, vuln, projectID)
}

func buildPocDraftMarkdown(v *database.Vulnerability, facts []*database.ProjectFact) string {
	return poc.BuildPocDraftMarkdown(v, facts)
}

func appendPocDraftMarker(db *database.DB, vuln *database.Vulnerability, relPath string) error {
	return poc.AppendPocDraftMarker(db, vuln, relPath)
}

func renderNumberedBlocks(text string) string {
	return poc.RenderNumberedBlocks(text)
}
