package app

import (
	"context"
	"fmt"
	"strings"

	"jysecai/internal/authctx"
	"jysecai/internal/database"
	"jysecai/internal/redirect"
	"jysecai/internal/redirectverify"

	"go.uber.org/zap"
)

// 受控跳轉「批次」模式的共用小工具。
//
// 單筆複測在 redirect_tools.go；批次（多個目標一次跑）與自動上鍊的共用邏輯在這裡，
// 讓 MCP 工具與批次 API 兩條路徑的證據格式一致（格式由 internal/redirectverify 定義）。

// redirectBatchConcurrencyArg 讀取批次併發數；未指定或非正數時交給引擎用預設值。
func redirectBatchConcurrencyArg(args map[string]interface{}) int {
	return intArg(args, "concurrency", 0)
}

// formatRedirectBatchResults 把批次結果整理成給 Agent 看的文字摘要。
func formatRedirectBatchResults(targets []string, method string, endpoints []string, results []redirect.BatchTargetResult) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("受控跳轉批次複測完成\n\n目標數: %d\n方法: %s\n受控端點: %s\n\n", len(targets), method, strings.Join(endpoints, ", ")))
	confirmed := 0
	for _, result := range results {
		status := "未命中"
		if result.Confirmed {
			status = "已回連"
			confirmed++
		}
		line := fmt.Sprintf("- %s param=%s status=%d location=%s => %s",
			result.URL, result.Param, result.Status, result.Location, status)
		if result.Error != "" {
			line += fmt.Sprintf(" (error: %s)", result.Error)
		}
		b.WriteString(line + "\n")
	}
	b.WriteString(fmt.Sprintf("\n共 %d 筆目標，其中 %d 筆確認跳向受控端點。", len(results), confirmed))
	return b.String()
}

// recordRedirectBatchResults 把驗證成功的目標自動建立成漏洞紀錄（上鍊）。
//
// 回傳建立的筆數；autoRecord 為 false 時不寫任何資料、回傳 0。
func recordRedirectBatchResults(
	ctx context.Context,
	db *database.DB,
	endpoints []string,
	results []redirect.BatchTargetResult,
	autoRecord bool,
) (int, error) {
	if !autoRecord || db == nil {
		return 0, nil
	}
	conversationID := conversationIDFromToolCtx(ctx)
	projectID := ""
	if pid, err := db.GetConversationProjectID(conversationID); err == nil {
		projectID = strings.TrimSpace(pid)
	}

	recorded := 0
	var lastErr error
	for _, result := range results {
		if !result.Confirmed {
			continue
		}
		vuln := redirectverify.BuildConfirmedVulnerability(redirectverify.Info{
			Endpoints:      endpoints,
			ProjectID:      projectID,
			ConversationID: conversationID,
			Source:         "受控跳轉批次驗證",
		}, result)
		created, err := db.CreateVulnerability(vuln)
		if err != nil {
			lastErr = err
			continue
		}
		recorded++
		if !created.Deduplicated {
			if principal, ok := authctx.PrincipalFromContext(ctx); ok {
				_ = db.SetResourceOwner("vulnerability", created.ID, principal.UserID)
				_ = db.AssignResourceToUser(principal.UserID, "vulnerability", created.ID)
			}
			db.NotifyVulnerabilityCreated(created)
		}
	}
	if recorded == 0 && lastErr != nil {
		return 0, lastErr
	}
	return recorded, nil
}

// redirectProbeConfirmed 彙整單筆探測結果是否命中受控端點。
func redirectProbeConfirmed(results []redirect.ProbeResult) bool {
	for _, result := range results {
		if result.Reflected {
			return true
		}
	}
	return false
}

// redirectProbeParam 取第一筆命中的探測所使用的參數名。
func redirectProbeParam(results []redirect.ProbeResult) string {
	for _, result := range results {
		if result.Reflected {
			return result.Param
		}
	}
	if len(results) > 0 {
		return results[0].Param
	}
	return ""
}

// redirectProbeRequestURL 取第一筆命中的探測所送出的請求網址。
func redirectProbeRequestURL(results []redirect.ProbeResult) string {
	for _, result := range results {
		if result.Reflected {
			return result.RequestURL
		}
	}
	if len(results) > 0 {
		return results[0].RequestURL
	}
	return ""
}

// redirectProbeStatus 取第一筆命中的探測的回應狀態碼。
func redirectProbeStatus(results []redirect.ProbeResult) int {
	for _, result := range results {
		if result.Reflected {
			return result.Status
		}
	}
	if len(results) > 0 {
		return results[0].Status
	}
	return 0
}

// redirectProbeLocation 取第一筆命中的探測的 Location 標頭。
func redirectProbeLocation(results []redirect.ProbeResult) string {
	for _, result := range results {
		if result.Reflected {
			return result.Location
		}
	}
	if len(results) > 0 {
		return results[0].Location
	}
	return ""
}

// logRedirectBatchSummary 記錄批次驗證摘要（給監控與稽核留痕）。
func logRedirectBatchSummary(logger *zap.Logger, targets int, confirmed int) {
	if logger == nil {
		return
	}
	logger.Info("受控跳轉批次驗證完成",
		zap.Int("targets", targets),
		zap.Int("confirmed", confirmed),
	)
}
