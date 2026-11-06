package app

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"
	"jysecai/internal/proxypool"
	"jysecai/internal/redirect"

	"go.uber.org/zap"
)

// redirectProbeTimeout 是單次跳轉探測的逾時上限。
const redirectProbeTimeout = 10 * time.Second

// registerRedirectTools 註冊受控跳轉（回連）探測工具。
//
// 註冊規則只有一條，初次註冊與設定熱套用後的重新註冊走同一條：
// redirect.enabled 為 true、或 redirect.urls 非空，任一者成立才註冊。
// 不成立時把工具下架，Agent 才不會看到一個沒有端點可用的工具。
func registerRedirectTools(mcpServer *mcp.Server, db *database.DB, cfg *config.Config, logger *zap.Logger, proxyPools ...*proxypool.Manager) {
	if mcpServer == nil {
		return
	}
	if cfg == nil || !cfg.Redirect.EnabledEffective() {
		mcpServer.UnregisterTool(builtin.ToolRedirectProbe)
		if logger != nil {
			logger.Debug("受控跳轉探測工具未註冊（未設定受控端點清單）")
		}
		return
	}

	tool := mcp.Tool{
		Name:             builtin.ToolRedirectProbe,
		Description:      "用受控回連端點複測開放式跳轉（open redirect）。工具會把受控端點塞進目標的跳轉參數、送出一次請求，然後只讀回應的 Location 標頭判斷有沒有真的跳向你的端點（絕不跟隨重新導向）。預設使用平台設定的 redirect.urls；可用 urls 參數單次覆蓋。未指定 param 時會依常見跳轉參數名（url、redirect、next、returnUrl…）逐一嘗試並在命中時停止。指定 vulnerability_id 可把結果寫回該漏洞的證據與複測紀錄（需具備漏洞寫入權限）。",
		ShortDescription: "用受控回連端點複測開放式跳轉",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"target_url": map[string]interface{}{
					"type":        "string",
					"description": "要測的端點 URL（必需），例如 https://victim.example/login。",
				},
				"param": map[string]interface{}{
					"type":        "string",
					"description": "跳轉參數名（可選）。省略時依常見參數名逐一嘗試（url、redirect、redirect_uri、returnUrl、next、goto、u…），第一個命中的即停止。",
				},
				"method": map[string]interface{}{
					"type":        "string",
					"enum":        []string{"GET", "POST"},
					"description": "請求方式，預設 GET。",
				},
				"urls": map[string]interface{}{
					"type":        "array",
					"items":       map[string]interface{}{"type": "string"},
					"description": "本次要使用的受控端點清單（可選）。省略時使用平台設定的 redirect.urls。",
				},
				"vulnerability_id": map[string]interface{}{
					"type":        "string",
					"description": "要寫回結果的漏洞 ID（可選）。需對該漏洞具備寫入權限，否則不會寫入。",
				},
				"target_urls": map[string]interface{}{
					"type":        "array",
					"items":       map[string]interface{}{"type": "string"},
					"description": "要批次測的端點 URL 清單（可選）。給多筆時會一次跑完並回傳每筆結果；target_url 仍可同時使用。",
				},
				"auto_record": map[string]interface{}{
					"type":        "boolean",
					"description": "驗證成功時是否自動建立漏洞紀錄（預設 false）。需具備漏洞寫入權限。",
				},
				"proxy": map[string]interface{}{
					"type":        "string",
					"description": "代理出口（可選）。支援 http、https、socks5、socks5h、socks4、socks4a。",
				},
				"proxy_group": map[string]interface{}{
					"type":        "string",
					"description": "使用平台代理池的群組名稱（可選，例如 residential）。與 proxy 同時指定時以 proxy 為準。",
				},
			},
			"required": []string{"target_url"},
		},
	}

	mcpServer.RegisterTool(tool, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		targetURL := strings.TrimSpace(strArg(args, "target_url"))
		targetURLs := redirectListArg(args, "target_urls")
		if targetURL == "" && len(targetURLs) == 0 {
			return textResult("错误: target_url 或 target_urls 必填且不能为空", true), nil
		}
		if targetURL != "" {
			targetURLs = append([]string{targetURL}, targetURLs...)
		}

		method := strings.ToUpper(strings.TrimSpace(strArg(args, "method")))
		if method == "" {
			method = http.MethodGet
		}
		if method != http.MethodGet && method != http.MethodPost {
			return textResult("错误: method 仅支持 GET 或 POST", true), nil
		}

		endpoints := redirect.NormalizeURLs(redirectListArg(args, "urls"))
		if len(endpoints) == 0 {
			endpoints = redirect.NormalizeURLs(cfg.Redirect.URLs)
		}
		if len(endpoints) == 0 {
			return textResult("错误: 没有可用的受控端点。请在平台设置中配置 redirect.urls，或在本次调用传入 urls。", true), nil
		}

		param := strings.TrimSpace(strArg(args, "param"))

		client, err := redirect.NewVerifyClient(strings.TrimSpace(strArg(args, "proxy")), redirectProbeTimeout)
		if err != nil {
			return textResult("错误: "+err.Error(), true), nil
		}
		if group := strings.TrimSpace(strArg(args, "proxy_group")); group != "" && len(proxyPools) > 0 && proxyPools[0] != nil {
			client = proxyPools[0].ClientGroup(redirectProbeTimeout, group)
		}

		// 批次模式：多筆目標一次跑完，每筆獨立結果。
		if len(targetURLs) > 1 {
			batchResults, err := redirect.VerifyTargets(ctx, client, targetURLs, redirect.BatchOptions{
				Endpoints:   endpoints,
				Param:       param,
				Method:      method,
				Concurrency: redirectBatchConcurrencyArg(args),
			})
			if err != nil {
				return textResult("错误: "+err.Error(), true), nil
			}
			summary := formatRedirectBatchResults(targetURLs, method, endpoints, batchResults)
			batchConfirmed := 0
			for _, item := range batchResults {
				if item.Confirmed {
					batchConfirmed++
				}
			}
			logRedirectBatchSummary(logger, len(batchResults), batchConfirmed)
			recorded, recordErr := recordRedirectBatchResults(ctx, db, endpoints, batchResults, boolArg(args, "auto_record"))
			if recordErr != nil {
				summary += "\n\n自动记录漏洞失败: " + recordErr.Error()
			} else if recorded > 0 {
				summary += fmt.Sprintf("\n\n已自动建立 %d 条漏洞记录。", recorded)
			}
			return textResult(summary, false), nil
		}

		targetURL = targetURLs[0]
		results := make([]redirect.ProbeResult, 0, len(endpoints))

		for _, endpoint := range endpoints {
			if param != "" {
				results = append(results, redirect.ProbeWithMethod(ctx, client, method, targetURL, param, endpoint))
				continue
			}
			// 沒指定參數名：依常見跳轉參數逐一試，命中就停，不再對同一端點繼續敲。
			for _, candidate := range redirect.DetectRedirectParams(targetURL) {
				result := redirect.ProbeWithMethod(ctx, client, method, targetURL, candidate, endpoint)
				results = append(results, result)
				if result.Reflected {
					break
				}
			}
		}

		summary := formatRedirectProbeResults(targetURL, method, endpoints, results)

		vulnerabilityID := strings.TrimSpace(strArg(args, "vulnerability_id"))
		if vulnerabilityID == "" {
			if boolArg(args, "auto_record") {
				recorded, recordErr := recordRedirectBatchResults(ctx, db, endpoints, []redirect.BatchTargetResult{{
					URL:        targetURL,
					Confirmed:  redirectProbeConfirmed(results),
					Param:      redirectProbeParam(results),
					RequestURL: redirectProbeRequestURL(results),
					Status:     redirectProbeStatus(results),
					Location:   redirectProbeLocation(results),
				}}, true)
				if recordErr != nil {
					return textResult(summary+"\n\n自动记录漏洞失败: "+recordErr.Error(), true), nil
				}
				if recorded > 0 {
					summary += fmt.Sprintf("\n\n已自动建立 %d 条漏洞记录。", recorded)
				}
			}
			return textResult(summary, false), nil
		}

		if db == nil {
			return textResult("错误: 无法写回漏洞记录（数据库不可用）\n\n"+summary, true), nil
		}
		vuln, err := db.GetVulnerability(vulnerabilityID)
		if err != nil || vuln == nil {
			return textResult("错误: 漏洞不存在或查询失败\n\n"+summary, true), nil
		}
		// 寫入權限沿用 update_vulnerability 的判定：目前專案／會話，或持有
		// vulnerability:write 的帳號。權限不足就明確回報，不寫入。
		convID := conversationIDFromToolCtx(ctx)
		projectID := ""
		if pid, perr := db.GetConversationProjectID(convID); perr == nil {
			projectID = strings.TrimSpace(pid)
		}
		if !canAccessVulnerabilityWithPrincipal(ctx, db, vuln, convID, projectID, "vulnerability:write") {
			return textResult("错误: 无权更新该漏洞（仅可更新当前项目或当前会话下的记录）\n\n"+summary, true), nil
		}

		evidenceBlock, retestLine := buildRedirectProbeNotes(targetURL, method, endpoints, results)
		updated := *vuln
		updated.Evidence = appendBlock(vuln.Evidence, evidenceBlock)
		updated.RetestNotes = appendBlock(vuln.RetestNotes, retestLine)
		if err := db.UpdateVulnerability(vuln.ID, &updated); err != nil {
			return textResult("更新漏洞失败: "+err.Error()+"\n\n"+summary, true), nil
		}
		vuln.Evidence = updated.Evidence
		vuln.RetestNotes = updated.RetestNotes

		if logger != nil {
			logger.Info("受控跳轉複測結果已寫回漏洞",
				zap.String("vulnerability_id", vuln.ID),
				zap.String("target_url", targetURL),
				zap.Int("probes", len(results)),
			)
		}
		return textResult(summary+"\n\n已写入漏洞 "+vuln.ID+" 的证据与复测记录。", false), nil
	})

	if logger != nil {
		logger.Debug("受控跳轉探測工具註冊成功", zap.Int("endpoints", len(cfg.Redirect.URLs)))
	}
}

// formatRedirectProbeResults 把探測結果整理成給 Agent 看的文字摘要。
func formatRedirectProbeResults(targetURL string, method string, endpoints []string, results []redirect.ProbeResult) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("受控跳轉複測完成\n\n目標: %s\n方法: %s\n受控端點: %s\n\n", targetURL, method, strings.Join(endpoints, ", ")))
	reflected := 0
	for _, result := range results {
		status := "未命中"
		if result.Reflected {
			status = "已回連"
			reflected++
		}
		line := fmt.Sprintf("- endpoint=%s param=%s status=%d location=%s => %s",
			result.RequestURL, result.Param, result.Status, result.Location, status)
		if result.Error != "" {
			line += fmt.Sprintf(" (error: %s)", result.Error)
		}
		b.WriteString(line + "\n")
	}
	b.WriteString(fmt.Sprintf("\n共 %d 次探測，其中 %d 次確認跳向受控端點。", len(results), reflected))
	return b.String()
}

// buildRedirectProbeNotes 產生要寫進漏洞紀錄的證據區塊與複測摘要。
func buildRedirectProbeNotes(targetURL string, method string, endpoints []string, results []redirect.ProbeResult) (string, string) {
	var evidence strings.Builder
	evidence.WriteString(fmt.Sprintf("[受控跳轉複測] %s\n", time.Now().Format("2006-01-02 15:04:05")))
	evidence.WriteString(fmt.Sprintf("target: %s\nmethod: %s\nendpoints: %s\n", targetURL, method, strings.Join(endpoints, ", ")))
	for _, result := range results {
		evidence.WriteString(fmt.Sprintf("- request: %s\n  param: %s\n  status: %d\n  location: %s\n  reflected: %v\n",
			result.RequestURL, result.Param, result.Status, result.Location, result.Reflected))
		if result.Error != "" {
			evidence.WriteString(fmt.Sprintf("  error: %s\n", result.Error))
		}
	}

	var retest strings.Builder
	retest.WriteString(fmt.Sprintf("- %s 受控跳轉複測：%s", time.Now().Format("2006-01-02 15:04:05"), targetURL))
	for _, result := range results {
		retest.WriteString(fmt.Sprintf(" | endpoint=%s param=%s status=%d reflected=%v",
			result.RequestURL, result.Param, result.Status, result.Reflected))
	}
	return evidence.String(), retest.String()
}

// appendBlock 把新內容接到舊內容後面；舊內容為空時直接回傳新內容。
func appendBlock(existing string, addition string) string {
	existing = strings.TrimRight(strings.TrimSpace(existing), "\n")
	addition = strings.TrimRight(addition, "\n")
	switch {
	case existing == "":
		return addition + "\n"
	case addition == "":
		return existing + "\n"
	default:
		return existing + "\n\n" + addition + "\n"
	}
}

// redirectListArg 讀取字串陣列參數；型別不符時回傳空清單（由呼叫端決定錯誤訊息）。
func redirectListArg(args map[string]interface{}, key string) []string {
	switch typed := args[key].(type) {
	case []string:
		return typed
	case []interface{}:
		values := make([]string, 0, len(typed))
		for _, item := range typed {
			if value, ok := item.(string); ok {
				values = append(values, value)
			}
		}
		return values
	default:
		return nil
	}
}
