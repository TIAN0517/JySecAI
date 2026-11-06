package toolguard

import (
	"strings"
	"testing"
)

// TestRefusalMessageRoundTrip 證明「組裝」與「解析」來自同一份格式定義。
//
// 背景：回執格式原本分散在 mcp（組裝）與 database（解析舊紀錄）兩處，
// 任一處單獨改動都會讓另一處靜默失配 —— 舊紀錄不會升級成 blocked，
// 而監控統計會漂移。這裡把兩個方向綁在一起測。
func TestRefusalMessageRoundTrip(t *testing.T) {
	cases := []Match{
		{RuleID: "government-domains", RuleName: "政府网站保护", MatchedText: "agency.gov.cn",
			Message: "识别到 {match}，禁止攻击政府网站。"},
		{RuleID: "government-domains", RuleName: "政府网站保护", MatchedText: "example.gov",
			Message: ""},
		{RuleID: "custom-rule", RuleName: "自訂規則", MatchedText: "含\"引號\"與\\反斜線",
			Message: "命中 {match}"},
	}
	for _, m := range cases {
		text := RefusalMessage(&m)
		name, id, matched, ok := ParseRefusal(text)
		if !ok {
			t.Fatalf("ParseRefusal failed for %q", text)
		}
		if name != m.RuleName || id != m.RuleID {
			t.Errorf("rule mismatch: got %q/%q want %q/%q", name, id, m.RuleName, m.RuleID)
		}
		if matched != m.MatchedText {
			t.Errorf("matched mismatch: got %q want %q", matched, m.MatchedText)
		}
	}
}

// TestRefusalMessageFormatIsStable 鎖定回執的實際字面格式。
// 舊資料庫裡既有的紀錄就是這個格式，改動會讓升級路徑失效。
func TestRefusalMessageFormatIsStable(t *testing.T) {
	m := Match{RuleID: "government-domains", RuleName: "政府网站保护",
		MatchedText: "example.gov", Message: "识别到 example.gov，禁止操作。"}
	want := "工具调用已被安全规则拦截：识别到 example.gov，禁止操作。\n" +
		"规则: 政府网站保护 (government-domains)\n" +
		"匹配内容: \"example.gov\""
	if got := RefusalMessage(&m); got != want {
		t.Errorf("refusal format changed:\n got: %q\nwant: %q", got, want)
	}
}

// TestParseRefusalRejectsNonRefusal 確保普通錯誤不會被誤判成政策攔截。
// 誤判會讓執行失敗被記成 blocked，統計與權限語意都會錯。
func TestParseRefusalRejectsNonRefusal(t *testing.T) {
	negative := []string{
		"",
		"工具调用已被安全规则拦截：regular error without the envelope",
		"工具调用已被安全规则拦截：malformed match\n规则: Rule (id)\n匹配内容: unquoted",
		"工具调用已被安全规则拦截：no match section at all",
		"upstream returned: 工具调用已被安全规则拦截：识别到 x.gov",
		"dial tcp 10.0.0.1:3306: connect: connection refused",
		"工具调用已被安全规则拦截\n规则: \n匹配内容: \"x\"",
	}
	for _, text := range negative {
		if _, _, _, ok := ParseRefusal(text); ok {
			t.Errorf("non-refusal text was accepted as a refusal: %q", text)
		}
	}
}

// TestParseRefusalRejectsIncompleteRuleSection 規則小節不完整時必須拒絕。
func TestParseRefusalRejectsIncompleteRuleSection(t *testing.T) {
	negative := []string{
		"工具调用已被安全规则拦截：x\n匹配内容: \"a.gov\"",           // 缺規則小節
		"工具调用已被安全规则拦截：x\n规则: OnlyName\n匹配内容: \"a.gov\"", // 缺規則 ID
		"工具调用已被安全规则拦截：x\n规则: Name ()\n匹配内容: \"a.gov\"",  // 規則 ID 為空
	}
	for _, text := range negative {
		if _, _, _, ok := ParseRefusal(text); ok {
			t.Errorf("incomplete refusal was accepted: %q", text)
		}
	}
}

// TestRefusalMessageNilMatch nil 不得產生 panic。
func TestRefusalMessageNilMatch(t *testing.T) {
	if got := RefusalMessage(nil); got != "" {
		t.Errorf("nil match should produce empty refusal, got %q", got)
	}
}

// TestBlockedPrefixSharedByProducersAndParsers 前綴必須單一來源。
// 任何一方改了字面值，另一方都會失配（舊紀錄不升級 / 統計漂移）。
func TestBlockedPrefixSharedByProducersAndParsers(t *testing.T) {
	if !strings.HasPrefix(BlockedPrefix, "工具调用已被安全规则拦截") {
		t.Fatalf("unexpected blocked prefix: %q", BlockedPrefix)
	}
	text := RefusalMessage(&Match{RuleID: "r", RuleName: "n", MatchedText: "t", Message: "m"})
	if !strings.HasPrefix(text, BlockedPrefix) {
		t.Errorf("refusal does not start with the shared prefix: %q", text)
	}
}
