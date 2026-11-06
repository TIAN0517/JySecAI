// Package authletter 產生「資訊安全測試授權書」。
//
// 定位：這是**給委託方簽署的授權憑據**，不是平台自用的資料。平台可以負責把案件事實
// 排版成一份專業、可直接送審的授權書，但授權人、授權編號、授權期間、授權範圍這些
// 構成法律事實的欄位，一律只能來自人 —— 缺哪一項就在文件上留白並列為缺口，
// 絕不由程式代填。
//
// 這條底線是刻意的：一旦平台能自己填出「授權人」與「已取得授權」的事實，平台就變成
// 自己出具自己的授權憑據，範圍閘門也就失去意義。專業排版可以自動化，法律事實不行。
package authletter

import (
	"encoding/json"
	"fmt"
	"html"
	"sort"
	"strings"
	"time"
)

// MaxAuthorizationDays 是授權期間上限，與平台授權閘門的 90 日一致。
const MaxAuthorizationDays = 90

// OperationLabel 是授權操作模式的人類可讀名稱與範圍說明。
type OperationLabel struct {
	Code  string
	Label string
	Scope string
}

// SupportedOperations 是平台授權閘門接受的模式。
var SupportedOperations = []OperationLabel{
	{
		Code:  "passive_discovery",
		Label: "被動偵察",
		Scope: "在不直接對目標發送攻擊性流量前提下，進行公開資訊蒐集、弱點比對與資產指紋辨識。",
	},
	{
		Code:  "active_scan",
		Label: "主動掃描",
		Scope: "對授權範圍內之目標發送掃描流量，進行弱點偵測、服務與版本辨識。",
	},
	{
		Code:  "exploit_validation",
		Label: "利用驗證",
		Scope: "以受控手法驗證已辨識弱點是否可被實際利用，並留存可復現之證據。",
	},
}

// operationLabel 查模式說明；未知模式原樣列出，不臆測語意。
func operationLabel(code string) (OperationLabel, bool) {
	code = strings.ToLower(strings.TrimSpace(code))
	for _, op := range SupportedOperations {
		if op.Code == code {
			return op, true
		}
	}
	return OperationLabel{Code: code, Label: code, Scope: "（未定義之操作模式，請由甲方確認）"}, false
}

// Input 是產生授權書所需的案件事實。
//
// 每個欄位都對應一件「由人輸入的事實」。Build 不會替任何一個欄位補值。
type Input struct {
	// 授權編號（甲方或工單編號）。
	DocumentID string `json:"document_id,omitempty"`
	// 簽發日期；留空使用 Build 的時間。
	IssuedAt time.Time `json:"issued_at,omitempty"`

	// 甲方（委託方）。
	ClientName         string `json:"client_name,omitempty"`
	ClientTaxID        string `json:"client_tax_id,omitempty"`
	ClientAddress      string `json:"client_address,omitempty"`
	ClientApprover     string `json:"client_approver,omitempty"` // 授權人（姓名）
	ClientApproverRole string `json:"client_approver_role,omitempty"`
	ClientContact      string `json:"client_contact,omitempty"` // 緊急聯絡窗口

	// 乙方（受託方）。
	VendorName      string `json:"vendor_name,omitempty"`
	VendorTaxID     string `json:"vendor_tax_id,omitempty"`
	VendorAddress   string `json:"vendor_address,omitempty"`
	VendorLead      string `json:"vendor_lead,omitempty"`
	VendorReference string `json:"vendor_reference,omitempty"`

	// 專案。
	ProjectID   string `json:"project_id,omitempty"`
	ProjectName string `json:"project_name,omitempty"`
	Objective   string `json:"objective,omitempty"`

	// 授權範圍：每行一個精確網域、*.子域或 CIDR。
	Patterns []string `json:"patterns,omitempty"`
	// 授權操作模式。
	Operations []string `json:"operations,omitempty"`
	// 授權期間。
	ValidFrom  time.Time `json:"valid_from,omitempty"`
	ValidUntil time.Time `json:"valid_until,omitempty"`

	// SourceAttested 表示這份授權事實已經由人工確認過（平台的授權勾選）。
	// 沒有勾選就只是草稿，輸出文件會明確標示。
	SourceAttested bool `json:"source_attested,omitempty"`

	// Basis 是「授權依據」的說明文字：這份授權書轉錄自哪一筆記錄、由誰確認、何時確認。
	// 沿用既有授權時這行很重要 —— 沒有它，讀文件的人會以為是這一次才簽的。
	Basis string `json:"basis,omitempty"`

	// SourceRunID / Inherited / InheritedAt 是授權沿用的來源記錄。
	SourceRunID string    `json:"source_run_id,omitempty"`
	Inherited   bool      `json:"inherited,omitempty"`
	InheritedAt time.Time `json:"inherited_at,omitempty"`

	// 附加條款。
	Notes []string `json:"notes,omitempty"`
}

// Record 是授權書的機器可讀版本。
//
// 欄位與平台 security_ops_runs.authorization_json 的結構一致，因此可以直接回填成
// 平台的授權記錄 —— 不需要另外造一套格式。
type Record struct {
	ID             string    `json:"id"`
	ProjectID      string    `json:"projectId"`
	TargetPatterns []string  `json:"targetPatterns"`
	Operations     []string  `json:"operations"`
	ValidFrom      time.Time `json:"validFrom"`
	ValidUntil     time.Time `json:"validUntil"`
	ApprovedBy     string    `json:"approvedBy"`
	Attested       bool      `json:"attested"`
	// SourceRunID / Inherited / InheritedAt 是授權沿用的來源記錄。
	// 平台的授權記錄結構有同樣的欄位，所以這份 JSON 可以無損回填。
	SourceRunID string    `json:"sourceRunId,omitempty"`
	Inherited   bool      `json:"inherited,omitempty"`
	InheritedAt time.Time `json:"inheritedAt,omitempty"`
}

// Result 是授權書的產出。
type Result struct {
	DocumentID string   // 文件編號（AUTH-...）
	Qualified  bool     // 是否具備成為正式授權書的完整條件
	Gaps       []string // 尚缺的條件（草稿時列於文件開頭）
	Attested   bool     // 是否已由人工確認授權事實
	Markdown   string
	HTML       string
	HTMLBody   string // 只有章節內容（不含 html/head 外殼），供嵌入滲透測試報告
	Record     Record // 機器可讀授權記錄
}

// Build 產生授權書。
//
// Build 是純函式：不讀資料庫、不猜事實。缺的事實一律留白並記在 Gaps 裡。
func Build(in Input, now time.Time) Result {
	if now.IsZero() {
		now = time.Now().UTC()
	}
	if in.IssuedAt.IsZero() {
		in.IssuedAt = now
	}

	patterns := normalizeList(in.Patterns)
	operations := normalizeList(in.Operations)

	documentID := strings.TrimSpace(in.DocumentID)
	if documentID == "" {
		documentID = "AUTH-" + in.IssuedAt.UTC().Format("20060102")
	}

	gaps := qualificationGaps(in, patterns, operations)

	attested := in.SourceAttested && len(gaps) == 0

	record := Record{
		ID:             documentID,
		ProjectID:      strings.TrimSpace(in.ProjectID),
		TargetPatterns: patterns,
		Operations:     operations,
		ValidFrom:      in.ValidFrom,
		ValidUntil:     in.ValidUntil,
		ApprovedBy:     strings.TrimSpace(in.ClientApprover),
		Attested:       attested,
		SourceRunID:    strings.TrimSpace(in.SourceRunID),
		Inherited:      in.Inherited,
		InheritedAt:    in.InheritedAt,
	}

	body := htmlBody(in, documentID, patterns, operations, gaps, attested)

	return Result{
		DocumentID: documentID,
		Qualified:  len(gaps) == 0,
		Gaps:       gaps,
		Attested:   attested,
		Markdown:   Markdown(in, documentID, patterns, operations, gaps, attested),
		HTML:       wrapHTML(documentID, body),
		HTMLBody:   body,
		Record:     record,
	}
}

// wrapHTML 把章節內容包成可列印的完整 HTML 文件。
func wrapHTML(documentID, body string) string {
	var b strings.Builder
	b.WriteString("<!DOCTYPE html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">")
	b.WriteString("<title>資訊安全測試授權書 " + html.EscapeString(documentID) + "</title><style>")
	b.WriteString(PageCSS)
	b.WriteString(CSS)
	b.WriteString("</style></head><body><article class=\"sheet letter\">")
	b.WriteString(body)
	b.WriteString("</article></body></html>")
	return b.String()
}

// qualificationGaps 列出還缺什麼。
//
// 這份清單同時是「文件開頭的草稿提示」與「平台授權閘門的同一組條件」——
// 兩邊一致，才不會出現「文件寫得完整但平台判定未授權」或反過來。
func qualificationGaps(in Input, patterns, operations []string) []string {
	var gaps []string
	if strings.TrimSpace(in.ClientName) == "" {
		gaps = append(gaps, "缺少甲方（委託方）名稱")
	}
	if strings.TrimSpace(in.ClientApprover) == "" {
		gaps = append(gaps, "缺少授權人（甲方簽署人）姓名")
	}
	if strings.TrimSpace(in.VendorName) == "" {
		gaps = append(gaps, "缺少乙方（受託方）名稱")
	}
	if len(patterns) == 0 {
		gaps = append(gaps, "缺少授權範圍")
	}
	if len(operations) == 0 {
		gaps = append(gaps, "缺少授權操作模式")
	}
	if in.ValidFrom.IsZero() || in.ValidUntil.IsZero() {
		gaps = append(gaps, "缺少授權期間")
	} else {
		if !in.ValidUntil.After(in.ValidFrom) {
			gaps = append(gaps, "授權期間的結束時間必須晚於開始時間")
		}
		if in.ValidUntil.Sub(in.ValidFrom) > MaxAuthorizationDays*24*time.Hour {
			gaps = append(gaps, fmt.Sprintf("授權期間超過 %d 日上限", MaxAuthorizationDays))
		}
	}
	if !in.SourceAttested {
		gaps = append(gaps, "尚未由人工確認授權事實（甲方授權勾選未完成）")
	}
	return gaps
}

// normalizeList 去空白、去重、保持順序。
func normalizeList(values []string) []string {
	seen := map[string]bool{}
	out := make([]string, 0, len(values))
	for _, value := range values {
		trimmed := strings.TrimSpace(value)
		if trimmed == "" || seen[trimmed] {
			continue
		}
		seen[trimmed] = true
		out = append(out, trimmed)
	}
	return out
}

// SortedPatterns 回傳排序後的範圍清單，讓文件每次產出順序一致（便於比對與稽核）。
func SortedPatterns(patterns []string) []string {
	out := append([]string(nil), patterns...)
	sort.Strings(out)
	return out
}

// RecordJSON 輸出機器可讀的授權記錄。
func RecordJSON(record Record) (string, error) {
	data, err := json.MarshalIndent(record, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// Markdown 產生授權書（Markdown）。
func Markdown(in Input, documentID string, patterns, operations []string, gaps []string, attested bool) string {
	var b strings.Builder
	b.WriteString("# 資訊安全測試授權書\n\n")

	if len(gaps) > 0 {
		b.WriteString("> **草稿：尚有 ")
		b.WriteString(fmt.Sprintf("%d", len(gaps)))
		b.WriteString(" 項條件未完成，簽署前請補齊**\n>\n")
		for _, gap := range gaps {
			b.WriteString("> - ")
			b.WriteString(gap)
			b.WriteString("\n")
		}
		b.WriteString("\n")
	} else if attested {
		b.WriteString("> 授權事實已由甲方確認；本文件僅待甲方簽署。\n\n")
	}

	b.WriteString("| 項目 | 內容 |\n|---|---|\n")
	writeRow(&b, "授權編號", documentID)
	writeRow(&b, "簽發日期", formatDate(in.IssuedAt))
	writeRow(&b, "甲方（委託方）", in.ClientName)
	writeRow(&b, "乙方（受託方）", in.VendorName)
	writeRow(&b, "專案名稱", in.ProjectName)
	writeRow(&b, "授權期間", formatRange(in.ValidFrom, in.ValidUntil))
	b.WriteString("\n")

	b.WriteString("## 一、當事人\n\n")
	if strings.TrimSpace(in.Basis) != "" {
		b.WriteString("> 授權依據：" + strings.TrimSpace(in.Basis) + "\n\n")
	}
	b.WriteString("甲方（委託方）：")
	b.WriteString(orBlank(in.ClientName))
	b.WriteString("\n\n")
	if strings.TrimSpace(in.ClientTaxID) != "" {
		b.WriteString("- 統一編號／識別證號：" + in.ClientTaxID + "\n")
	}
	if strings.TrimSpace(in.ClientAddress) != "" {
		b.WriteString("- 地址：" + in.ClientAddress + "\n")
	}
	if strings.TrimSpace(in.ClientApprover) != "" {
		b.WriteString("- 授權人：" + in.ClientApprover)
		if strings.TrimSpace(in.ClientApproverRole) != "" {
			b.WriteString("（" + in.ClientApproverRole + "）")
		}
		b.WriteString("\n")
	}
	if strings.TrimSpace(in.ClientContact) != "" {
		b.WriteString("- 緊急聯絡窗口：" + in.ClientContact + "\n")
	}
	b.WriteString("\n乙方（受託方）：")
	b.WriteString(orBlank(in.VendorName))
	b.WriteString("\n\n")
	if strings.TrimSpace(in.VendorTaxID) != "" {
		b.WriteString("- 統一編號／識別證號：" + in.VendorTaxID + "\n")
	}
	if strings.TrimSpace(in.VendorAddress) != "" {
		b.WriteString("- 地址：" + in.VendorAddress + "\n")
	}
	if strings.TrimSpace(in.VendorLead) != "" {
		b.WriteString("- 專案負責人：" + in.VendorLead + "\n")
	}
	if strings.TrimSpace(in.VendorReference) != "" {
		b.WriteString("- 乙方內部案件編號：" + in.VendorReference + "\n")
	}

	b.WriteString("\n## 二、授權事項\n\n")
	b.WriteString("甲方茲授權乙方就下列目標執行資訊安全測試。乙方得於本授權書有效期間內、")
	b.WriteString("於第三條列示之授權範圍內，依第四條之操作模式進行測試並交付結果。\n\n")
	if strings.TrimSpace(in.Objective) != "" {
		b.WriteString("本次測試目標為：" + in.Objective + "\n\n")
	}

	b.WriteString("## 三、授權範圍（目標）\n\n")
	if len(patterns) == 0 {
		b.WriteString("- （待填：授權範圍）\n")
	}
	for _, pattern := range SortedPatterns(patterns) {
		b.WriteString("- `" + pattern + "`\n")
	}
	b.WriteString("\n前開範圍以外之任何系統、網路、帳號、資料及第三方服務，均不在本授權範圍內；\n")
	b.WriteString("乙方不得以本授權書為由對其進行任何測試或操作。\n\n")

	b.WriteString("## 四、授權操作模式\n\n")
	if len(operations) == 0 {
		b.WriteString("- （待填：授權操作模式）\n")
	}
	for _, code := range operations {
		op, known := operationLabel(code)
		b.WriteString("- **" + op.Label + "**（" + op.Code + "）：" + op.Scope)
		if !known {
			b.WriteString(" ⚠ 未知模式，請甲方確認")
		}
		b.WriteString("\n")
	}

	b.WriteString("\n## 五、授權期間\n\n")
	b.WriteString("- 起始：" + formatDate(in.ValidFrom) + "\n")
	b.WriteString("- 截止：" + formatDate(in.ValidUntil) + "\n")
	b.WriteString(fmt.Sprintf("- 本授權最長有效期間為 %d 日；逾期未經甲方書面延期，乙方應即停止一切測試作業。\n", MaxAuthorizationDays))

	b.WriteString("\n## 六、測試方法與限制\n\n")
	b.WriteString("1. 乙方應以最小影響原則執行測試，優先採用被動或低影響手法；需主動驗證時，應先確認目標系統之承載狀況。\n")
	b.WriteString("2. 乙方不得對 119／EPCR／消防救護等緊急救援系統、政府網站與關鍵基礎設施進行測試。\n")
	b.WriteString("3. 乙方不得執行破壞性操作、刪除或竄改資料、對真實交易或正式流程進行操作。\n")
	b.WriteString("4. 乙方不得於未經甲方另行書面同意前，將授權範圍擴大至第三方系統或關聯服務。\n")
	b.WriteString("5. 乙方發現高風險問題時，應於發現後即時通知甲方緊急聯絡窗口。\n")
	b.WriteString("6. 甲方應提供必要之測試環境、帳號權限與連線支援，並指定一名緊急聯絡窗口。\n")

	b.WriteString("\n## 七、資料處理與保密\n\n")
	b.WriteString("1. 乙方對測試過程中取得之資料、帳密、Token、截圖、日誌與報告負保密義務。\n")
	b.WriteString("2. 測試期間取得之憑證與資料，乙方應於測試結束後依甲方指示返還或刪除。\n")
	b.WriteString("3. 乙方不得將測試結果用於甲方未書面同意之用途，亦不得對外揭露；法律主管機關要求除外。\n")
	b.WriteString("4. 乙方交付之報告與佐證文件之密級為「委託方內部」。\n")

	b.WriteString("\n## 八、交付物\n\n")
	b.WriteString("1. 滲透測試報告（含漏洞清單、證據、影響與修復建議）。\n")
	b.WriteString("2. 必要之複測紀錄與佐證截圖。\n")
	b.WriteString("3. 本授權書之簽署正本，作為交付與稽核依據。\n")

	b.WriteString("\n## 九、責任歸屬\n\n")
	b.WriteString("1. 乙方應於授權範圍內依約執行；因測試作業造成之系統異常，應即時協助甲方處理。\n")
	b.WriteString("2. 乙方逾越授權範圍或未經甲方指示之操作，所生損害由乙方自行負責。\n")
	b.WriteString("3. 甲方應確保其提供之測試環境與資料已取得必要之內部同意。\n")

	b.WriteString("\n## 十、合約終止\n\n")
	b.WriteString("甲方得於任何時間以書面或電子郵件通知終止本授權書；乙方應於收到通知後立即停止測試作業，\n")
	b.WriteString("並依第八條處理資料。終止後，已完成之測試結果之保密義務仍繼續有效。\n")

	if len(in.Notes) > 0 {
		b.WriteString("\n## 十一、附註\n\n")
		for _, note := range in.Notes {
			trimmed := strings.TrimSpace(note)
			if trimmed == "" {
				continue
			}
			b.WriteString("- " + trimmed + "\n")
		}
	}

	b.WriteString("\n## 十二、簽署\n\n")
	b.WriteString("本授權書自甲方簽署之日起生效，一式兩份，雙方各執一份為憑。\n\n")
	b.WriteString("**甲方（委託方）：**" + orBlank(in.ClientName) + "\n\n")
	b.WriteString("授權人簽名：" + blankLine() + "\n\n")
	b.WriteString("職稱：" + orBlank(in.ClientApproverRole) + "\n\n")
	b.WriteString("（用印）\n\n")
	b.WriteString("日期：　　年　　月　　日\n\n")
	b.WriteString("**乙方（受託方）：**" + orBlank(in.VendorName) + "\n\n")
	b.WriteString("專案負責人簽名：" + blankLine() + "\n\n")
	b.WriteString("（用印）\n\n")
	b.WriteString("日期：　　年　　月　　日\n")

	return b.String()
}

// htmlBody 產生授權書的章節內容（不含 html/head 外殼），樣式沿用平台交付物的排版風格。
func htmlBody(in Input, documentID string, patterns, operations []string, gaps []string, attested bool) string {
	var b strings.Builder
	b.WriteString("<header class=\"cover\"><p class=\"kicker\">滲透測試授權憑據</p><h1>資訊安全測試授權書</h1>")
	b.WriteString("<p class=\"meta\">文件編號 " + html.EscapeString(documentID))
	b.WriteString(" · 簽發日期 " + html.EscapeString(formatDate(in.IssuedAt)))
	b.WriteString(" · 密級：委託方內部</p>")
	if len(gaps) > 0 {
		b.WriteString("<p class=\"badge draft\">草稿：尚缺 " + fmt.Sprintf("%d", len(gaps)) + " 項才能簽署生效</p><ul class=\"gaps\">")
		for _, gap := range gaps {
			b.WriteString("<li>" + html.EscapeString(gap) + "</li>")
		}
		b.WriteString("</ul>")
	} else if attested {
		b.WriteString("<p class=\"badge ok\">授權事實已確認，待甲方簽署</p>")
	}
	b.WriteString("</header>")

	writeHTMLSection(&b, "一、當事人", basisBlock(in)+partyTable(in))
	writeHTMLSection(&b, "二、授權事項", objectiveBody(in.Objective))
	writeHTMLSection(&b, "三、授權範圍（目標）", patternList(patterns))
	writeHTMLSection(&b, "四、授權操作模式", operationList(operations))
	writeHTMLSection(&b, "五、授權期間", periodBody(in))
	writeHTMLSection(&b, "六、測試方法與限制", clauseList(
		"乙方應以最小影響原則執行測試，優先採用被動或低影響手法；需主動驗證時，應先確認目標系統之承載狀況。",
		"乙方不得對 119／EPCR／消防救護等緊急救援系統、政府網站與關鍵基礎設施進行測試。",
		"乙方不得執行破壞性操作、刪除或竄改資料、對真實交易或正式流程進行操作。",
		"乙方不得於未經甲方另行書面同意前，將授權範圍擴大至第三方系統或關聯服務。",
		"乙方發現高風險問題時，應於發現後即時通知甲方緊急聯絡窗口。",
		"甲方應提供必要之測試環境、帳號權限與連線支援，並指定一名緊急聯絡窗口。",
	))
	writeHTMLSection(&b, "七、資料處理與保密", clauseList(
		"乙方對測試過程中取得之資料、帳密、Token、截圖、日誌與報告負保密義務。",
		"測試期間取得之憑證與資料，乙方應於測試結束後依甲方指示返還或刪除。",
		"乙方不得將測試結果用於甲方未書面同意之用途，亦不得對外揭露；法律主管機關要求除外。",
		"乙方交付之報告與佐證文件之密級為「委託方內部」。",
	))
	writeHTMLSection(&b, "八、交付物", clauseList(
		"滲透測試報告（含漏洞清單、證據、影響與修復建議）。",
		"必要之複測紀錄與佐證截圖。",
		"本授權書之簽署正本，作為交付與稽核依據。",
	))
	writeHTMLSection(&b, "九、責任歸屬", clauseList(
		"乙方應於授權範圍內依約執行；因測試作業造成之系統異常，應即時協助甲方處理。",
		"乙方逾越授權範圍或未經甲方指示之操作，所生損害由乙方自行負責。",
		"甲方應確保其提供之測試環境與資料已取得必要之內部同意。",
	))
	writeHTMLSection(&b, "十、合約終止", "<p>甲方得於任何時間以書面或電子郵件通知終止本授權書；乙方應於收到通知後立即停止測試作業，並依第七條處理資料。終止後，已完成之測試結果之保密義務仍繼續有效。</p>")
	if len(in.Notes) > 0 {
		writeHTMLSection(&b, "十一、附註", clauseList(in.Notes...))
	}
	writeHTMLSection(&b, "十二、簽署", signatureBlock(in))

	b.WriteString("<footer>文件編號 " + html.EscapeString(documentID) + " · 本文件取代口頭授權；測試作業應以本文件所載範圍與期間為準</footer>")
	return b.String()
}

// basisBlock 產生「授權依據」說明段落；沒有依據時回空字串。
func basisBlock(in Input) string {
	if strings.TrimSpace(in.Basis) == "" {
		return ""
	}
	return "<p class=\"basis\"><strong>授權依據：</strong>" + html.EscapeString(strings.TrimSpace(in.Basis)) + "</p>"
}

// partyTable 產生當事人資訊表。
func partyTable(in Input) string {
	var b strings.Builder
	b.WriteString("<table><tr><th>角色</th><th>名稱</th><th>識別證號</th><th>地址</th><th>授權人／負責人</th><th>職稱</th><th>聯絡窗口</th></tr>")
	b.WriteString("<tr><td>甲方（委託方）</td><td>" + html.EscapeString(orBlank(in.ClientName)) + "</td><td>" +
		html.EscapeString(orBlank(in.ClientTaxID)) + "</td><td>" + html.EscapeString(orBlank(in.ClientAddress)) + "</td><td>" +
		html.EscapeString(orBlank(in.ClientApprover)) + "</td><td>" + html.EscapeString(orBlank(in.ClientApproverRole)) + "</td><td>" +
		html.EscapeString(orBlank(in.ClientContact)) + "</td></tr>")
	b.WriteString("<tr><td>乙方（受託方）</td><td>" + html.EscapeString(orBlank(in.VendorName)) + "</td><td>" +
		html.EscapeString(orBlank(in.VendorTaxID)) + "</td><td>" + html.EscapeString(orBlank(in.VendorAddress)) + "</td><td>" +
		html.EscapeString(orBlank(in.VendorLead)) + "</td><td>專案負責人</td><td>—</td></tr>")
	b.WriteString("</table>")
	return b.String()
}

// patternList 產生範圍清單。
func patternList(patterns []string) string {
	if len(patterns) == 0 {
		return "<p class=\"pending\">（待填：授權範圍）</p>"
	}
	var b strings.Builder
	b.WriteString("<ol class=\"targets\">")
	for _, pattern := range SortedPatterns(patterns) {
		b.WriteString("<li><code>" + html.EscapeString(pattern) + "</code></li>")
	}
	b.WriteString("</ol>")
	b.WriteString("<p>前開範圍以外之任何系統、網路、帳號、資料及第三方服務，均不在本授權範圍內；乙方不得以本授權書為由對其進行任何測試或操作。</p>")
	return b.String()
}

// operationList 產生授權模式清單。
func operationList(operations []string) string {
	if len(operations) == 0 {
		return "<p class=\"pending\">（待填：授權操作模式）</p>"
	}
	var b strings.Builder
	b.WriteString("<ul>")
	for _, code := range operations {
		op, known := operationLabel(code)
		b.WriteString("<li><strong>" + html.EscapeString(op.Label) + "</strong>（" + html.EscapeString(op.Code) + "）：" + html.EscapeString(op.Scope))
		if !known {
			b.WriteString(" <span class=\"warn\">⚠ 未知模式，請甲方確認</span>")
		}
		b.WriteString("</li>")
	}
	b.WriteString("</ul>")
	return b.String()
}

// periodBody 產生授權期間段落。
func periodBody(in Input) string {
	var b strings.Builder
	b.WriteString("<p>起始：" + html.EscapeString(formatDate(in.ValidFrom)) + "<br>截止：" + html.EscapeString(formatDate(in.ValidUntil)) + "</p>")
	b.WriteString("<p>本授權最長有效期間為 " + fmt.Sprintf("%d", MaxAuthorizationDays) + " 日；逾期未經甲方書面延期，乙方應即停止一切測試作業。</p>")
	return b.String()
}

// clauseList 產生條列段落。
func clauseList(clauses ...string) string {
	var b strings.Builder
	b.WriteString("<ol>")
	for _, clause := range clauses {
		trimmed := strings.TrimSpace(clause)
		if trimmed == "" {
			continue
		}
		b.WriteString("<li>" + html.EscapeString(trimmed) + "</li>")
	}
	b.WriteString("</ol>")
	return b.String()
}

// signatureBlock 產生簽署欄。
func signatureBlock(in Input) string {
	var b strings.Builder
	b.WriteString("<p>本授權書自甲方簽署之日起生效，一式兩份，雙方各執一份為憑。</p>")
	b.WriteString("<div class=\"sign-grid\">")
	b.WriteString("<div class=\"sign\"><p class=\"sign-role\">甲方（委託方）：" + html.EscapeString(orBlank(in.ClientName)) + "</p>")
	b.WriteString("<p>授權人簽名：________________</p><p>職稱：" + html.EscapeString(orBlank(in.ClientApproverRole)) + "</p><p>（用印）</p><p>日期：　　年　　月　　日</p></div>")
	b.WriteString("<div class=\"sign\"><p class=\"sign-role\">乙方（受託方）：" + html.EscapeString(orBlank(in.VendorName)) + "</p>")
	b.WriteString("<p>專案負責人簽名：________________</p><p>（用印）</p><p>日期：　　年　　月　　日</p></div>")
	b.WriteString("</div>")
	return b.String()
}

// objectiveBody 產生「二、授權事項」段落。
func objectiveBody(text string) string {
	if strings.TrimSpace(text) == "" {
		return "<p>甲方茲授權乙方就下列目標執行資訊安全測試。乙方得於本授權書有效期間內、於第三條列示之授權範圍內，依第四條之操作模式進行測試並交付結果。</p>"
	}
	return "<p>甲方茲授權乙方就下列目標執行資訊安全測試。乙方得於本授權書有效期間內、於第三條列示之授權範圍內，依第四條之操作模式進行測試並交付結果。</p><p>本次測試目標為：" + html.EscapeString(text) + "</p>"
}

// writeRow 寫 Markdown 表格列。
func writeRow(b *strings.Builder, label, value string) {
	b.WriteString("| " + label + " | " + strings.ReplaceAll(value, "|", "\\|") + " |\n")
}

// writeHTMLSection 寫 HTML 章節。
func writeHTMLSection(b *strings.Builder, title, body string) {
	b.WriteString("<section><h2>" + html.EscapeString(title) + "</h2>")
	b.WriteString(body)
	b.WriteString("</section>")
}

// orBlank 缺值時顯示待填標記。
func orBlank(value string) string {
	if strings.TrimSpace(value) == "" {
		return "（待填）"
	}
	return value
}

// blankLine 產生簽名線。
func blankLine() string {
	return "________________"
}

// formatDate 格式化日期；零值顯示待填。
func formatDate(t time.Time) string {
	if t.IsZero() {
		return "（待填）"
	}
	return t.Format("2006-01-02")
}

// formatRange 格式化期間。
func formatRange(from, until time.Time) string {
	if from.IsZero() && until.IsZero() {
		return "（待填）"
	}
	return formatDate(from) + " 至 " + formatDate(until)
}

// CSS 是授權書的排版樣式。所有選擇器都收在 .letter 底下，因此可以安全地併進
// 滲透測試報告的樣式區塊，不會把報告自己的 h1/h2/table/footer 規則蓋掉。
const CSS = `
.letter{color:#1c1915;font:15px/1.6 "Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif}
.letter .cover{border-bottom:2px solid #1c1915;padding-bottom:16px;margin-bottom:8px}
.letter .kicker{letter-spacing:.08em;color:#7a6240;font-size:12px;margin:0}
.letter h1{margin:8px 0 0;font-size:30px}
.letter .meta{color:#655c52;margin:6px 0 0}
.letter .badge{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:700;font-size:13px;margin-top:10px}
.letter .badge.ok{background:#e6f4ea;color:#1e6b3a}
.letter .badge.draft{background:#fdf0e2;color:#8a5a12}
.letter .gaps{color:#8a5a12;font-size:13px;margin:8px 0 0;padding-left:20px}
.letter section{margin-top:26px}
.letter h2{font-size:17px;border-left:4px solid #7a6240;padding-left:10px;margin:0 0 12px}
.letter table{width:100%;border-collapse:collapse;font-size:13px}
.letter th,.letter td{border:1px solid #ddd6c8;padding:7px 9px;text-align:left;vertical-align:top}
.letter th{background:#f4f1ea;font-weight:600}
.letter ol,.letter ul{margin:6px 0 6px 20px;padding:0}
.letter li{margin:4px 0}
.letter code{background:#f4f1ea;padding:1px 5px;border-radius:3px}
.letter .pending{color:#8a5a12;font-style:italic}
.letter .basis{background:#f4f1ea;border-left:3px solid #7a6240;padding:8px 12px;margin:0 0 12px}
.letter .warn{color:#8a5a12;font-weight:600}
.letter .targets code{font-size:14px}
.letter .sign-grid{display:flex;gap:28px;margin-top:12px}
.letter .sign{flex:1;border:1px solid #ddd6c8;padding:14px 16px;min-height:180px}
.letter .sign-role{font-weight:700;margin-top:0}
.letter footer{margin-top:32px;padding-top:12px;border-top:1px solid #ddd6c8;color:#655c52;font-size:12px}
`

// PageCSS 是授權書獨立文件的外頁樣式（body / .sheet）。
// 刻意與 CSS 分開：只有獨立文件才需要動到頁面層級的排版，嵌進報告時不能動。
const PageCSS = `
body{margin:0;background:#f4f1ea;color:#1c1915;font:15px/1.6 "Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif}
.sheet{max-width:880px;margin:24px auto;background:#fff;padding:44px 52px;box-shadow:0 8px 30px rgba(0,0,0,.06)}
@media print{body{background:#fff}.sheet{box-shadow:none;margin:0;max-width:none;padding:0}}
`
