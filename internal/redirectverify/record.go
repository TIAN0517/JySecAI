// Package redirectverify 組合「受控跳轉驗證確認」的漏洞紀錄。
//
// 同一份證據格式有兩條產生路徑：批次 API（internal/handler）與 MCP 工具
// （internal/app）。兩邊若各寫一份，證據區塊、複測紀錄與標題模板會慢慢長得
// 不一樣 —— 同一個漏洞從不同入口進來會長得不同。因此把「組紀錄」收斂到這裡，
// 兩條路徑只差「要不要真的寫進資料庫」。
package redirectverify

import (
	"fmt"
	"strings"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/redirect"
)

// Info 是建立漏洞紀錄所需的批次脈絡。
type Info struct {
	// RunID 是批次 ID（單筆工具呼叫可留空）。
	RunID string
	// Endpoints 是本次使用的受控端點（跳轉目標）。
	Endpoints []string
	// ProjectID 與 ConversationID 決定紀錄歸屬。
	ProjectID      string
	ConversationID string
	// Source 記錄來源（批次 / 工具），寫進證據區塊方便回溯。
	Source string
	// Encoding 是受控端點寫進 payload 時的編碼方式（none／percent／base64…）。
	//
	// 編碼只改變寫出去的字面形式。紀錄裡同時留著原樣端點與編碼後的 payload，
	// 兩者都留才能在複測時還原「實際送出去的字串」。
	Encoding string
}

// BuildConfirmedVulnerability 依驗證結果組出漏洞紀錄（尚未寫入資料庫）。
//
// 只處理 confirmed = true 的結果；未確認的結果不該變成漏洞紀錄。
func BuildConfirmedVulnerability(info Info, result redirect.BatchTargetResult) *database.Vulnerability {
	host := hostOf(result.URL)
	endpoints := strings.Join(info.Endpoints, ", ")
	source := strings.TrimSpace(info.Source)
	if source == "" {
		source = "受控跳轉驗證"
	}

	title := fmt.Sprintf("開放式重定向（受控跳轉驗證確認）- %s", host)
	description := fmt.Sprintf(
		"目標 %s 的跳轉參數 %s 接受任意外部網址，伺服器端直接回應重新導向至外部位址。\n"+
			"以受控端點 %s 代入後，目標回應的 Location 標頭指向受控端點主機，確認存在開放式重定向（Open Redirect，CWE-601）。",
		result.URL, result.Param, endpoints,
	)
	reproSteps := fmt.Sprintf(
		"1. 準備受控端點：%s\n2. 對目標 %s 帶入參數 %s，值設為受控端點。\n3. 觀察回應：HTTP %d，Location: %s\n4. Location 主機與受控端點一致，確認目標未限制跳轉目標。",
		endpoints, result.URL, result.Param, result.Status, result.Location,
	)

	var evidence strings.Builder
	evidence.WriteString(fmt.Sprintf("[%s] %s\n", source, time.Now().Format("2006-01-02 15:04:05")))
	if info.RunID != "" {
		evidence.WriteString("batch_run_id: " + info.RunID + "\n")
	}
	evidence.WriteString(fmt.Sprintf("target: %s\nparam: %s\nrequest: %s\nstatus: %d\nlocation: %s\nendpoints: %s\n",
		result.URL, result.Param, result.RequestURL, result.Status, result.Location, endpoints))
	if encoding := strings.TrimSpace(info.Encoding); encoding != "" && encoding != redirect.PayloadEncodingNone {
		evidence.WriteString(fmt.Sprintf("payload_encoding: %s\n", encoding))
	}
	if result.OwnParam != "" {
		evidence.WriteString("site_own_param: " + result.OwnParam + "\n")
	}
	// 證據等級：location = 真的 3xx 跳轉；body_echo = 只是本文回顯（偽陽性來源，
	// 不會走到這裡，因為 confirmed 必須有 Location 證據）。
	if level := strings.TrimSpace(result.Evidence); level != "" {
		evidence.WriteString("evidence_level: " + level + "\n")
	}
	if result.OwnParamHit {
		evidence.WriteString("own_param_hit: true\n")
	}
	if result.Attempts > 0 {
		evidence.WriteString(fmt.Sprintf("attempts: %d\n", result.Attempts))
	}
	if result.Attempts > 1 {
		evidence.WriteString(fmt.Sprintf("stable: %t\n", result.Stable))
	}

	retestNotes := fmt.Sprintf("- %s %s 確認 | target=%s | param=%s | status=%d | location=%s",
		time.Now().Format("2006-01-02 15:04:05"), source, result.URL, result.Param, result.Status, result.Location)

	return &database.Vulnerability{
		ConversationID: info.ConversationID,
		ProjectID:      info.ProjectID,
		Title:          title,
		Description:    description,
		Severity:       "medium",
		Status:         database.VulnerabilityStatusConfirmed,
		// 有明確的 Location 標頭證據，信心給到確認閘門的門檻值。
		Confidence:     database.VulnerabilityConfirmConfidenceThreshold,
		Type:           "Open Redirect",
		Target:         result.URL,
		Preconditions:  "目標站點公開可達，且跳轉參數未限制目標來源。",
		ReproSteps:     reproSteps,
		Evidence:       evidence.String(),
		Impact:         "可被用於釣魚與流量洗白：攻擊者讓受害者從可信網域跳向惡意站點，或以受害者身分對第三方系統發出請求。",
		Recommendation: "對跳轉參數做白名單驗證（僅允許站內或已核准的外部網域），或直接移除任意跳轉功能。",
		RetestNotes:    retestNotes,
	}
}

// hostOf 取出目標的主機名；解析不出來時退回整個 URL。
func hostOf(raw string) string {
	value := strings.TrimSpace(raw)
	if idx := strings.Index(value, "://"); idx >= 0 {
		value = value[idx+3:]
	}
	if idx := strings.IndexAny(value, "/?#"); idx >= 0 {
		value = value[:idx]
	}
	if idx := strings.LastIndex(value, "@"); idx >= 0 {
		value = value[idx+1:]
	}
	if value == "" {
		return raw
	}
	return value
}
