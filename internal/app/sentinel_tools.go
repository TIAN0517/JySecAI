package app

import (
	"context"
	"fmt"
	"strings"
	"time"

	"jysecai/internal/authctx"
	"jysecai/internal/database"
	"jysecai/internal/handler"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"
	"jysecai/internal/sentinel"

	"go.uber.org/zap"
)

// registerSentinelTools 註冊「零零哨兵 Sentinel 暴露面測繪」MCP 工具集
func registerSentinelTools(server *mcp.Server, db *database.DB, h *handler.SentinelHandler, logger *zap.Logger) {
	if server == nil || h == nil {
		return
	}

	// 1. sentinel_scan: 發起暴露面巡檢
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolSentinelScan,
		ShortDescription: "發起目標暴露面測繪與巡檢",
		Description:      "對目標主域名（如 example.com）或公網 IPv4 執行零零哨兵（Sentinel）全維度暴露面測繪。主動探測子域存活、開放端口、30 種資料庫握手與未授權風險（MySQL/Redis/PostgreSQL/MongoDB/Elasticsearch/ClickHouse等）、登入頁面與敏感介面。預設同步等待完成（wait=true，最長支援 300 秒），亦可非同步發起（wait=false）獲取 scan_id。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"target": map[string]interface{}{
					"type":        "string",
					"description": "探測目標：二級主域名（如 example.com）或公網 IPv4 位址",
				},
				"wait": map[string]interface{}{
					"type":        "boolean",
					"description": "是否同步等待探測完成並回傳完整摘要，預設 true；設為 false 則立即回傳 scan_id",
				},
				"timeout_seconds": map[string]interface{}{
					"type":        "integer",
					"description": "同步等待超時時間（秒），預設 180，最大 300",
				},
			},
			"required": []string{"target"},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		target := strings.TrimSpace(strArg(args, "target"))
		if target == "" {
			return textResult("錯誤: 請提供有效的探測目標 target", true), nil
		}

		wait := boolArgDefault(args, "wait", true)
		timeoutSec := intArg(args, "timeout_seconds", 180)
		if timeoutSec <= 0 {
			timeoutSec = 180
		} else if timeoutSec > 300 {
			timeoutSec = 300
		}

		if !wait {
			snapshot, err := h.StartScanTarget(target)
			if err != nil {
				return textResult("發起暴露面探測失敗: "+err.Error(), true), nil
			}
			msg := fmt.Sprintf("已成功在後台發起暴露面探測任務！\n- 任務 ID: `%s`\n- 目標: `%s`\n- 狀態: `running`\n\n提示：探測約需 30-120 秒，後續可呼叫 `get_sentinel_scan` 工具傳入 scan_id=`%s` 查詢最新進度與結果。",
				snapshot.ID, snapshot.Target, snapshot.ID)
			return textResult(msg, false), nil
		}

		scanCtx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSec)*time.Second)
		defer cancel()

		snapshot, err := h.RunScanSync(scanCtx, target)
		if err != nil {
			if snapshot != nil && snapshot.ID != "" {
				return textResult(fmt.Sprintf("暴露面探測執行中斷或超時: %v\n已保留任務快照 ID: %s（可稍後用 get_sentinel_scan 檢查）", err, snapshot.ID), true), nil
			}
			return textResult("暴露面探測失敗: "+err.Error(), true), nil
		}

		return textResult(formatSentinelSnapshotMarkdown(snapshot), false), nil
	})

	// 2. get_sentinel_scan: 查詢巡檢快照
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolGetSentinelScan,
		ShortDescription: "查詢暴露面巡檢狀態與結果快照",
		Description:      "查詢暴露面哨兵任務的目前執行狀態與完整快照（包含主機資產、開放端口、資料庫風險、登入入口等）。若不傳 scan_id 則預設查詢最新一次巡檢快照。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"scan_id": map[string]interface{}{
					"type":        "string",
					"description": "巡檢任務 ID；留空則自動獲取系統最近一次巡檢記錄",
				},
			},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		scanID := strings.TrimSpace(strArg(args, "scan_id"))
		snapshot, err := h.GetScanByID(scanID)
		if err != nil {
			return textResult("查詢巡檢快照失敗: "+err.Error(), true), nil
		}
		if snapshot == nil {
			return textResult("未找到對應的暴露面探測快照", true), nil
		}

		return textResult(formatSentinelSnapshotMarkdown(snapshot), false), nil
	})

	// 3. sentinel_sync_assets: 同步資產
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolSentinelSyncAssets,
		ShortDescription: "將暴露面發現的主機與端口同步至資產庫",
		Description:      "將暴露面哨兵巡檢發現的主機資產與開放端口批量匯入/合併至系統資產庫（自動按 Host+Port 進行去重與更新）。若不傳 scan_id 則使用最新一次巡檢；若不傳 project_id 則自動綁定當前對話所屬專案。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"scan_id": map[string]interface{}{
					"type":        "string",
					"description": "巡檢任務 ID；留空則使用最近一次完成的巡檢",
				},
				"project_id": map[string]interface{}{
					"type":        "string",
					"description": "歸屬專案 ID；留空則自動繼承當前對話綁定的專案",
				},
			},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		scanID := strings.TrimSpace(strArg(args, "scan_id"))
		projectID := strings.TrimSpace(strArg(args, "project_id"))

		// 自動推導當前對話專案
		convID := conversationIDFromToolCtx(ctx)
		if projectID == "" && convID != "" && db != nil {
			if pid, err := db.GetConversationProjectID(convID); err == nil {
				projectID = strings.TrimSpace(pid)
			}
		}

		userID := "admin"
		if principal, ok := authctx.PrincipalFromContext(ctx); ok && principal.UserID != "" {
			userID = principal.UserID
		}

		result, total, err := h.SyncAssetsDirect(scanID, projectID, userID)
		if err != nil {
			return textResult("同步資產庫失敗: "+err.Error(), true), nil
		}

		var b strings.Builder
		b.WriteString("### 暴露面哨兵資產同步成功\n\n")
		b.WriteString(fmt.Sprintf("- **處理主機/端口總數**: %d\n", total))
		b.WriteString(fmt.Sprintf("- **新建立資產數**: %d\n", result.Created))
		b.WriteString(fmt.Sprintf("- **更新現有資產數**: %d\n", result.Updated))
		b.WriteString(fmt.Sprintf("- **已跳過/無變更數**: %d\n", result.Skipped))
		if projectID != "" {
			b.WriteString(fmt.Sprintf("- **關聯專案 ID**: `%s`\n", projectID))
		} else {
			b.WriteString("- **專案歸屬**: （全域資產，未綁定單一專案）\n")
		}
		b.WriteString("\n提示：資產已建立標籤 `sentinel` 與 `surface-watch`，可使用 `query_assets` 工具或在 Web 前端「資產管理」查看。")
		return textResult(b.String(), false), nil
	})

	// 4. sentinel_sync_vulnerabilities: 同步漏洞
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolSentinelSyncVulnerabilities,
		ShortDescription: "將暴露面高/中危風險項同步入庫至漏洞管理",
		Description:      "將暴露面哨兵發現的高危與中危風險項（如資料庫未授權存取、公網暴露敏感管理入口等）批量去重入庫至系統漏洞清單。若不傳 scan_id 則使用最新一次巡檢；若不傳 project_id 則自動綁定當前對話所屬專案。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"scan_id": map[string]interface{}{
					"type":        "string",
					"description": "巡檢任務 ID；留空則使用最近一次完成的巡檢",
				},
				"project_id": map[string]interface{}{
					"type":        "string",
					"description": "歸屬專案 ID；留空則自動繼承當前對話綁定的專案",
				},
			},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		scanID := strings.TrimSpace(strArg(args, "scan_id"))
		projectID := strings.TrimSpace(strArg(args, "project_id"))

		// 自動推導當前對話專案
		convID := conversationIDFromToolCtx(ctx)
		if projectID == "" && convID != "" && db != nil {
			if pid, err := db.GetConversationProjectID(convID); err == nil {
				projectID = strings.TrimSpace(pid)
			}
		}

		created, skipped, err := h.SyncVulnsDirect(scanID, projectID)
		if err != nil {
			return textResult("同步漏洞庫失敗: "+err.Error(), true), nil
		}

		var b strings.Builder
		b.WriteString("### 暴露面哨兵風險發現同步入庫成功\n\n")
		b.WriteString(fmt.Sprintf("- **新建立漏洞記錄**: %d 條\n", created))
		b.WriteString(fmt.Sprintf("- **已存在/去重跳過**: %d 條\n", skipped))
		if projectID != "" {
			b.WriteString(fmt.Sprintf("- **關聯專案 ID**: `%s`\n", projectID))
		}
		b.WriteString("\n提示：已入庫漏洞標籤包含 `sentinel-scan`。可使用 `list_vulnerabilities` 檢視，或使用 `generate_poc_draft` 一鍵產生複現草稿，或使用 `verify_poc` 進行連線弱驗證。")
		return textResult(b.String(), false), nil
	})

	if logger != nil {
		logger.Info("暴露面哨兵 (Sentinel) MCP 工具集註冊成功",
			zap.Strings("tools", []string{
				builtin.ToolSentinelScan,
				builtin.ToolGetSentinelScan,
				builtin.ToolSentinelSyncAssets,
				builtin.ToolSentinelSyncVulnerabilities,
			}),
		)
	}
}

// formatSentinelSnapshotMarkdown 將巡檢快照格式化為對 AI 與人類友好的結構化 Markdown
func formatSentinelSnapshotMarkdown(s *sentinel.ScanSnapshot) string {
	if s == nil {
		return "（無巡檢快照）"
	}

	var b strings.Builder
	b.WriteString(fmt.Sprintf("# 暴露面哨兵巡檢報告 · %s\n\n", s.Target))
	b.WriteString(fmt.Sprintf("- **任務 ID**: `%s`\n", s.ID))
	b.WriteString(fmt.Sprintf("- **目標類型**: %s\n", s.TargetKind))
	b.WriteString(fmt.Sprintf("- **狀態**: **%s**\n", strings.ToUpper(s.Status)))
	if s.DurationMs > 0 {
		b.WriteString(fmt.Sprintf("- **耗時**: %.2f 秒\n", float64(s.DurationMs)/1000.0))
	}
	if s.Error != "" {
		b.WriteString(fmt.Sprintf("- **錯誤資訊**: %s\n", s.Error))
	}
	b.WriteString("\n")

	// 指標統計卡
	b.WriteString("## 巡檢核心指標\n\n")
	b.WriteString(fmt.Sprintf("| 解析主機 | 存活主機 | 開放端口 | 30種資料庫識別 | 登入入口/端點 | 高危風險 | 中危風險 |\n"))
	b.WriteString(fmt.Sprintf("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"))
	b.WriteString(fmt.Sprintf("| %d | %d | %d | %d | %d | **%d** | %d |\n\n",
		s.Summary.HostCount,
		s.Summary.AliveCount,
		s.Summary.OpenPortCount,
		s.Summary.DatabaseCount,
		s.Summary.LoginCount,
		s.Summary.HighCount,
		s.Summary.MediumCount,
	))

	// 資料庫暴露與未授權
	if len(s.Databases) > 0 {
		b.WriteString("## 數據庫暴露與指紋識別\n\n")
		for _, db := range s.Databases {
			riskBadge := db.Risk
			if db.Risk == "unauth" {
				riskBadge = "🚨 **未授權存取 (HIGH)**"
			} else {
				riskBadge = "⚠️ 握手/開放 (" + db.Risk + ")"
			}
			b.WriteString(fmt.Sprintf("- **%s** | `%s:%d` | 風險: %s\n", db.EngineName, db.Host, db.Port, riskBadge))
			if db.Evidence != "" {
				b.WriteString(fmt.Sprintf("  - *特徵證據*: `%s`\n", db.Evidence))
			}
		}
		b.WriteString("\n")
	}

	// 高中危風險發現
	if len(s.Findings) > 0 {
		b.WriteString("## 重點安全發現 (Findings)\n\n")
		highMedCount := 0
		for _, f := range s.Findings {
			if f.Severity == "high" || f.Severity == "medium" {
				highMedCount++
				sevIcon := "⚠️"
				if f.Severity == "high" {
					sevIcon = "🚨 [高危]"
				} else {
					sevIcon = "🟡 [中危]"
				}
				b.WriteString(fmt.Sprintf("### %s %s\n", sevIcon, f.Title))
				b.WriteString(fmt.Sprintf("- **主機/目標**: `%s`\n", f.Host))
				b.WriteString(fmt.Sprintf("- **分類**: %s\n", f.Category))
				if f.URL != "" {
					b.WriteString(fmt.Sprintf("- **URL**: %s\n", f.URL))
				}
				if f.Detail != "" {
					b.WriteString(fmt.Sprintf("- **詳細說明**: %s\n", f.Detail))
				}
				b.WriteString("\n")
			}
		}
		if highMedCount == 0 {
			b.WriteString("（未檢測出高危或中危風險）\n\n")
		}
	}

	// 存活主機與開放端口摘要
	if len(s.Ports) > 0 {
		b.WriteString("## 開放端口與服務\n\n")
		limit := 15
		for i, p := range s.Ports {
			if i >= limit {
				b.WriteString(fmt.Sprintf("- ... 其餘 %d 個開放端口已省略（可透過資產同步檢視完整明細）\n", len(s.Ports)-limit))
				break
			}
			banner := ""
			if p.Banner != "" {
				banner = fmt.Sprintf(" (`%s`)", p.Banner)
			}
			b.WriteString(fmt.Sprintf("- `%s:%d` — %s%s\n", p.Host, p.Port, strings.ToUpper(p.Service), banner))
		}
		b.WriteString("\n")
	}

	// 後續操作建議引導
	b.WriteString("## 後續行動建議\n\n")
	b.WriteString("1. 呼叫 `sentinel_sync_assets` 工具：將上述發現的全部在線主機與開放端口同步至系統資產庫。\n")
	b.WriteString("2. 呼叫 `sentinel_sync_vulnerabilities` 工具：將檢測到的未授權資料庫及關鍵風險同步入庫為漏洞記錄。\n")
	b.WriteString("3. 呼叫 `generate_poc_draft` 工具：按產生的漏洞自動生成複現草稿 Markdown 檔案。\n")
	b.WriteString("4. 呼叫 `verify_poc` 工具：對 HTTP/HTTPS 漏洞進行在線弱驗證與特徵匹配。\n")

	return b.String()
}
