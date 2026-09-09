package app

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"jysecai/internal/database"
	"jysecai/internal/handler"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"

	"go.uber.org/zap"
)

// registerAWVSTools 註冊「AWVS 商業級掃描器聯動」MCP 工具集
func registerAWVSTools(server *mcp.Server, db *database.DB, h *handler.AWVSHandler, logger *zap.Logger) {
	if server == nil || h == nil {
		return
	}

	// 1. awvs_status: 檢查 AWVS 連線狀態
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolAWVSStatus,
		ShortDescription: "檢查 AWVS 掃描器連線與帳號狀態",
		Description:      "檢查 AWVS (Acunetix) 商業級漏洞掃描器的連線狀態、API 位址、目前登入帳號角色以及已配置的掃描目標總數。",
		InputSchema: map[string]interface{}{
			"type":       "object",
			"properties": map[string]interface{}{},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		info, err := h.GetStatusInfo()
		if err != nil {
			return textResult("查詢 AWVS 狀態失敗: "+err.Error(), true), nil
		}

		var b strings.Builder
		connected, _ := info["connected"].(bool)
		b.WriteString("# AWVS (Acunetix) 連線狀態\n\n")
		b.WriteString(fmt.Sprintf("- **API 位址**: `%v`\n", info["url"]))
		if connected {
			b.WriteString("- **連線狀態**: 🟢 **正常連線**\n")
			b.WriteString(fmt.Sprintf("- **目前帳號**: `%v`\n", info["email"]))
			b.WriteString(fmt.Sprintf("- **使用者角色**: `%v`\n", info["role"]))
			b.WriteString(fmt.Sprintf("- **已配置目標數**: %v\n", info["target_count"]))
			b.WriteString("\n提示：可使用 `awvs_list_targets` 查看目標清單，或使用 `awvs_start_scan` 發起掃描，或使用 `awvs_sync_vulnerabilities` 同步漏洞。")
		} else {
			b.WriteString("- **連線狀態**: 🔴 **未連線 / 配置錯誤**\n")
			if errMsg, ok := info["error"].(string); ok && errMsg != "" {
				b.WriteString(fmt.Sprintf("- **錯誤原因**: %s\n", errMsg))
			}
			b.WriteString("\n提示：請至 Web 前端「AWVS 聯動」或在系統環境變數設定 `JYSEC_AWVS_API_URL` 與 `JYSEC_AWVS_API_KEY`。")
		}

		return textResult(b.String(), false), nil
	})

	// 2. awvs_list_targets: 列出掃描目標
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolAWVSListTargets,
		ShortDescription: "列出 AWVS 掃描器中配置的目標清單",
		Description:      "列出 AWVS 商業掃描器中配置的所有掃描目標（包含 target_id, address, description, criticality 等），供發起掃描或篩選同步時使用。",
		InputSchema: map[string]interface{}{
			"type":       "object",
			"properties": map[string]interface{}{},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		data, err := h.ListTargetsInfo()
		if err != nil {
			return textResult("獲取 AWVS 目標清單失敗: "+err.Error(), true), nil
		}

		targetsRaw, ok := data["targets"].([]interface{})
		if !ok || len(targetsRaw) == 0 {
			return textResult("AWVS 目前未配置任何掃描目標（targets 列表為空）。", false), nil
		}

		var b strings.Builder
		b.WriteString(fmt.Sprintf("# AWVS 掃描目標清單（共 %d 個）\n\n", len(targetsRaw)))
		b.WriteString("| Target ID | 位址 / URL | 描述 | 嚴重度 |\n")
		b.WriteString("| :--- | :--- | :--- | :---: |\n")

		for _, item := range targetsRaw {
			tmap, ok := item.(map[string]interface{})
			if !ok {
				continue
			}
			tid, _ := tmap["target_id"].(string)
			addr, _ := tmap["address"].(string)
			desc, _ := tmap["description"].(string)
			if desc == "" {
				desc = "-"
			}
			crit := tmap["criticality"]
			b.WriteString(fmt.Sprintf("| `%s` | %s | %s | %v |\n", tid, addr, desc, crit))
		}

		b.WriteString("\n提示：發起掃描請使用 `awvs_start_scan` 工具並傳入對應的 `target_id`。")
		return textResult(b.String(), false), nil
	})

	// 3. awvs_start_scan: 發起掃描
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolAWVSStartScan,
		ShortDescription: "在 AWVS 中發起目標安全掃描",
		Description:      "在 AWVS 掃描器中對指定目標 target_id 發起自動化掃描。可指定 profile_id（預設全量掃描 11111111-1111-1111-1111-111111111111，亦可使用 High Risk 11111111-1111-1111-1111-111111111112 或 XSS/SQLi 等 Profile）。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"target_id": map[string]interface{}{
					"type":        "string",
					"description": "目標 ID（可先呼叫 awvs_list_targets 取得）",
				},
				"profile_id": map[string]interface{}{
					"type":        "string",
					"description": "掃描範本 ID；留空則預設使用 Full Scan (11111111-1111-1111-1111-111111111111)",
				},
			},
			"required": []string{"target_id"},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		targetID := strings.TrimSpace(strArg(args, "target_id"))
		if targetID == "" {
			return textResult("錯誤: target_id 必填", true), nil
		}
		profileID := strings.TrimSpace(strArg(args, "profile_id"))

		resData, err := h.StartScanTarget(targetID, profileID)
		if err != nil {
			return textResult("在 AWVS 發起掃描失敗: "+err.Error(), true), nil
		}

		scanID := ""
		if s, ok := resData["scan_id"].(string); ok {
			scanID = s
		}

		var b strings.Builder
		b.WriteString("### AWVS 掃描任務發起成功！\n\n")
		b.WriteString(fmt.Sprintf("- **目標 ID**: `%s`\n", targetID))
		if scanID != "" {
			b.WriteString(fmt.Sprintf("- **新建立掃描 ID (scan_id)**: `%s`\n", scanID))
		}
		if profileID != "" {
			b.WriteString(fmt.Sprintf("- **掃描範本 ID**: `%s`\n", profileID))
		} else {
			b.WriteString("- **掃描範本**: Full Scan（全量掃描）\n")
		}

		b.WriteString("\n後續操作建議：\n")
		b.WriteString(fmt.Sprintf("1. 使用 `awvs_get_scan_status` 工具傳入 scan_id=`%s` 查詢掃描即時進度。\n", scanID))
		b.WriteString("2. 掃描完成後，使用 `awvs_sync_vulnerabilities` 工具將掃描出的漏洞一鍵同步匯入至系統漏洞庫。\n")

		return textResult(b.String(), false), nil
	})

	// 4. awvs_get_scan_status: 查詢掃描狀態
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolAWVSGetScanStatus,
		ShortDescription: "查詢 AWVS 掃描進度與狀態",
		Description:      "查詢 AWVS 掃描任務的當前進度與狀態（包含 processing, completed, failed，以及高/中/低危漏洞數量統計等）。可指定 scan_id；若留空則列出最近的所有掃描記錄清單。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"scan_id": map[string]interface{}{
					"type":        "string",
					"description": "掃描任務 ID；留空則查詢所有近期掃描記錄",
				},
			},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		scanID := strings.TrimSpace(strArg(args, "scan_id"))
		data, err := h.GetScanStatusInfo(scanID)
		if err != nil {
			return textResult("查詢 AWVS 掃描狀態失敗: "+err.Error(), true), nil
		}

		// 單個掃描詳情
		if scanID != "" {
			var b strings.Builder
			b.WriteString(fmt.Sprintf("# AWVS 掃描狀態詳情 · `%s`\n\n", scanID))
			if target, ok := data["target"].(map[string]interface{}); ok {
				b.WriteString(fmt.Sprintf("- **目標位址**: `%v`\n", target["address"]))
				b.WriteString(fmt.Sprintf("- **目標描述**: %v\n", target["description"]))
			}

			if sess, ok := data["current_session"].(map[string]interface{}); ok {
				b.WriteString(fmt.Sprintf("- **目前狀態**: **%v**\n", strings.ToUpper(fmt.Sprint(sess["status"]))))
				if progress, ok := sess["progress"].(float64); ok {
					b.WriteString(fmt.Sprintf("- **掃描進度**: %.1f%%\n", progress))
				}
				if sevCounts, ok := sess["severity_counts"].(map[string]interface{}); ok {
					b.WriteString("\n### 發現漏洞統計\n\n")
					b.WriteString(fmt.Sprintf("- 🚨 **高危 (High)**: %v\n", sevCounts["high"]))
					b.WriteString(fmt.Sprintf("- 🟡 **中危 (Medium)**: %v\n", sevCounts["medium"]))
					b.WriteString(fmt.Sprintf("- 🔵 **低危 (Low)**: %v\n", sevCounts["low"]))
					b.WriteString(fmt.Sprintf("- ⚪ **資訊 (Info)**: %v\n", sevCounts["info"]))
				}
			}

			b.WriteString("\n提示：掃描完成後，呼叫 `awvs_sync_vulnerabilities` 工具可將發現項一鍵入庫。")
			return textResult(b.String(), false), nil
		}

		// 多個掃描列表
		scansRaw, ok := data["scans"].([]interface{})
		if !ok || len(scansRaw) == 0 {
			return textResult("AWVS 目前無任何掃描記錄。", false), nil
		}

		var b strings.Builder
		b.WriteString(fmt.Sprintf("# AWVS 近期掃描清單（共 %d 個）\n\n", len(scansRaw)))
		b.WriteString("| Scan ID | 目標位址 | 狀態 | 掃描範本 |\n")
		b.WriteString("| :--- | :--- | :---: | :--- |\n")

		limit := 20
		for i, item := range scansRaw {
			if i >= limit {
				b.WriteString(fmt.Sprintf("\n- ... 其餘 %d 個掃描記錄已省略\n", len(scansRaw)-limit))
				break
			}
			smap, ok := item.(map[string]interface{})
			if !ok {
				continue
			}
			sid, _ := smap["scan_id"].(string)
			addr := "-"
			if tinfo, ok := smap["target"].(map[string]interface{}); ok {
				if a, ok := tinfo["address"].(string); ok {
					addr = a
				}
			}
			status := "unknown"
			if sess, ok := smap["current_session"].(map[string]interface{}); ok {
				if st, ok := sess["status"].(string); ok {
					status = st
				}
			}
			profileName := "Full Scan"
			if pinfo, ok := smap["profile_name"].(string); ok && pinfo != "" {
				profileName = pinfo
			}

			b.WriteString(fmt.Sprintf("| `%s` | %s | %s | %s |\n", sid, addr, status, profileName))
		}

		b.WriteString("\n提示：可指定 scan_id 參數查看單一任務詳細漏洞分佈，或呼叫 `awvs_sync_vulnerabilities` 同步漏洞。")
		return textResult(b.String(), false), nil
	})

	// 5. awvs_sync_vulnerabilities: 同步漏洞
	server.RegisterTool(mcp.Tool{
		Name:             builtin.ToolAWVSSyncVulnerabilities,
		ShortDescription: "從 AWVS 批量去重同步漏洞至資料庫",
		Description:      "從 AWVS 商業掃描器分頁拉取漏洞報告（包含請求報文、描述、修復建議、影響與嚴重度），並自動依目標 URL 與漏洞標題去重入庫至 JySecAI 系統漏洞庫。若不傳 project_id 則自動繼承當前對話綁定的專案。",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"target_id": map[string]interface{}{
					"type":        "string",
					"description": "可選：指定 AWVS target_id 僅同步特定目標的漏洞；留空則同步全部",
				},
				"project_id": map[string]interface{}{
					"type":        "string",
					"description": "歸屬專案 ID；留空則自動繼承當前對話綁定的專案",
				},
			},
		},
	}, func(ctx context.Context, args map[string]interface{}) (*mcp.ToolResult, error) {
		targetID := strings.TrimSpace(strArg(args, "target_id"))
		projectID := strings.TrimSpace(strArg(args, "project_id"))

		// 自動推導當前對話專案
		convID := conversationIDFromToolCtx(ctx)
		if projectID == "" && convID != "" && db != nil {
			if pid, err := db.GetConversationProjectID(convID); err == nil {
				projectID = strings.TrimSpace(pid)
			}
		}

		synced, skipped, totalInAwvs, err := h.SyncVulnerabilitiesDirect(projectID, targetID)
		if err != nil {
			return textResult("同步 AWVS 漏洞庫失敗: "+err.Error(), true), nil
		}

		var b strings.Builder
		b.WriteString("### AWVS 漏洞批量同步入庫成功！\n\n")
		b.WriteString(fmt.Sprintf("- **AWVS 遠端漏洞總數**: %d 條\n", totalInAwvs))
		b.WriteString(fmt.Sprintf("- **新建立本機漏洞記錄**: %d 條\n", synced))
		b.WriteString(fmt.Sprintf("- **已存在/自動去重更新**: %d 條\n", skipped))
		if projectID != "" {
			b.WriteString(fmt.Sprintf("- **關聯專案 ID**: `%s`\n", projectID))
		}
		if targetID != "" {
			b.WriteString(fmt.Sprintf("- **限制目標 ID**: `%s`\n", targetID))
		}

		b.WriteString("\n後續操作指引：\n")
		b.WriteString("1. 呼叫 `list_vulnerabilities` 工具：查看同步入庫的漏洞列表。\n")
		b.WriteString("2. 呼叫 `generate_poc_draft` 工具：按 AWVS 漏洞資訊生成包含原始請求報文的復現草稿。\n")
		b.WriteString("3. 呼叫 `verify_poc` 工具：對漏洞目標進行即時在線弱探測與特徵匹配驗證。\n")

		return textResult(b.String(), false), nil
	})

	if logger != nil {
		logger.Info("AWVS 掃描器聯動 MCP 工具集註冊成功",
			zap.Strings("tools", []string{
				builtin.ToolAWVSStatus,
				builtin.ToolAWVSListTargets,
				builtin.ToolAWVSStartScan,
				builtin.ToolAWVSGetScanStatus,
				builtin.ToolAWVSSyncVulnerabilities,
			}),
		)
	}
}

// 避免未使用 import
var _ = json.Marshal
