package toolguard

import (
	"strconv"
	"strings"
)

// 攔截回執（refusal）的格式由本檔案單一定義。
//
// 這份格式原本分散在三處：internal/mcp 組裝回執、internal/database 解析舊紀錄
// 以升級狀態、internal/mcp/execution_service.go 內嵌一份字面值。任何一處單獨
// 改動都會讓另外兩處靜默失配（解析不到 → 舊紀錄不會升級成 blocked；字面值不一致
// → 攔截統計漂移）。組裝與解析必須同源，否則「回執長什麼樣」就有多份真相。

const (
	// BlockedPrefix 是所有攔截回執的固定前綴。
	// 新舊版本的執行紀錄都靠它辨識，不應改動。
	BlockedPrefix = "工具调用已被安全规则拦截"

	// BlockedMetaKey 是 MCP protocol meta 中標記攔截的欄位鍵。
	BlockedMetaKey = "jytech.ai/blocked"

	// refusalRuleSection 與 refusalMatchSection 是回執內文的小節標題。
	refusalRuleSection  = "\n规则: "
	refusalMatchSection = "\n匹配内容: "
)

// RefusalMessage 依 Match 組出標準攔截回執文字。
//
// 回執同時送給模型、寫入執行紀錄、並作為 MCP 回應本文，因此格式必須穩定：
//
//	<前綴>[:<提醒文字>]
//	规则: <規則名稱> (<規則 ID>)
//	匹配内容: "<命中文字>"
func RefusalMessage(m *Match) string {
	if m == nil {
		return ""
	}
	message := BlockedPrefix
	if custom := strings.TrimSpace(m.Message); custom != "" {
		message += "：" + custom
	}
	return message + refusalRuleSection + m.RuleName + " (" + m.RuleID + ")" +
		refusalMatchSection + strconv.Quote(m.MatchedText)
}

// ParseRefusal 解析 RefusalMessage 產生的回執。
//
// 回傳 ok=false 表示文字不是本格式（例如一般工具執行錯誤）。呼叫端據此區分
// 「被政策攔截」與「執行失敗」——兩者在監控統計與權限語意上不同，不可混為一談。
//
// 只接受完整且格式正確的回執：前綴、規則小節、匹配內容三段都必須齊備且可解析，
// 半截文字一律視為非攔截回執。
func ParseRefusal(text string) (ruleName, ruleID, matchedText string, ok bool) {
	if !strings.HasPrefix(text, BlockedPrefix+"：") &&
		!strings.HasPrefix(text, BlockedPrefix+refusalRuleSection) {
		return "", "", "", false
	}
	matchIndex := strings.LastIndex(text, refusalMatchSection)
	if matchIndex < 0 {
		return "", "", "", false
	}
	matched, err := strconv.Unquote(text[matchIndex+len(refusalMatchSection):])
	if err != nil {
		return "", "", "", false
	}
	ruleIndex := strings.LastIndex(text[:matchIndex], refusalRuleSection)
	if ruleIndex < 0 {
		return "", "", "", false
	}
	rule := text[ruleIndex+len(refusalRuleSection) : matchIndex]
	idIndex := strings.LastIndex(rule, " (")
	if idIndex <= 0 || !strings.HasSuffix(rule, ")") {
		return "", "", "", false
	}
	id := rule[idIndex+2 : len(rule)-1]
	if id == "" || strings.Contains(rule, "\n") {
		return "", "", "", false
	}
	return rule[:idIndex], id, matched, true
}
