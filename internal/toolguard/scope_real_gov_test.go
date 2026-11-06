package toolguard

import "testing"

// 真實政府網域後綴的授權範圍測試。
//
// 為什麼要另外寫一份
//   scope_test.go 用的是 portal.agency.gov.example 這類 .gov.example 假網域。
//   實際案件（台灣／中國政府黑客松獎金） targets 是 .gov.tw / .gov.cn，
//   兩者的 label 結構與多層子網域都不一樣，必須直接用真實後綴驗證過，
//   否則「測試全綠」不代表實際掃得到。
//
// 這裡驗證三件事：
//  1. 授權範圍內的政府網域真的放行（工具可對該目標執行）。
//  2. 範圍外的政府網域照樣阻擋（保護沒有被弱化）。
//  3. 後綴／子網域混淆不會意外放行。

func mustCompile(t *testing.T, scope Scope) *Policy {
	t.Helper()
	p, err := Compile(scopedConfig(scope))
	if err != nil {
		t.Fatal(err)
	}
	return p
}

func mustBlock(t *testing.T, p *Policy, url, why string) {
	t.Helper()
	if m := p.Check("http_request", map[string]interface{}{"target": url}); m == nil {
		t.Errorf("%s：%q 應該被 government-domains 阻擋，卻放行了（%s）", why, url, why)
	}
}

func mustAllow(t *testing.T, p *Policy, url, why string) {
	t.Helper()
	if m := p.Check("http_request", map[string]interface{}{"target": url}); m != nil {
		t.Errorf("%s：%q 應該放行，卻被規則 %s 擋下（%v）", why, url, m.RuleID, m)
	}
}

// 這是實際要確認的主流程：把一個授權的 .gov.tw 目標加入 scope 後，
// 對它下工具指令要能過，其他政府網域仍然要擋。
func TestRealTWGovTargetInScopeIsAllowed(t *testing.T) {
	policy := mustCompile(t, Scope{Domains: []string{"case-a.gov.tw"}})

	mustAllow(t, policy, "https://case-a.gov.tw/", "授權目標")
	mustAllow(t, policy, "https://case-a.gov.tw/api/v1/cases", "授權目標的子路徑")
	// 帶 port 也要視為同一個 host
	mustAllow(t, policy, "https://case-a.gov.tw:8443/login", "授權目標帶 port")

	// 同一層級的其他政府網域必須照擋
	mustBlock(t, policy, "https://case-b.gov.tw/", "未授權的政府網域")
	mustBlock(t, policy, "https://other-agency.gov.tw/admin", "未授權的政府網域")
}

func TestRealCNGovTargetInScopeIsAllowed(t *testing.T) {
	policy := mustCompile(t, Scope{Domains: []string{"case-c.gov.cn"}})

	mustAllow(t, policy, "https://case-c.gov.cn/", "授權目標")
	mustBlock(t, policy, "https://case-d.gov.cn/", "未授權的政府網域")
	// 中國政府網域很多是多層子網域，例如 xxx.yyy.gov.cn
	mustBlock(t, policy, "https://deep.nested.case-d.gov.cn/x", "未授權的多層子網域")
}

// 混淆測試：授權一個 host 不得意外放行後綴拼接或近似字串。
func TestScopeDoesNotLeakThroughSuffixConfusion(t *testing.T) {
	policy := mustCompile(t, Scope{Domains: []string{"case-a.gov.tw"}})

	// 把授權 host 當成字串前綴的其他網域 —— 必須仍被擋
	mustBlock(t, policy, "https://case-a.gov.tw.evil.test/", "後綴拼接")
	mustBlock(t, policy, "https://notcase-a.gov.tw/", "名稱包含")
	// gov 不是獨立 label 時不應命中規則，也不該因 scope 而改變
	if m := policy.Check("http_request", map[string]interface{}{"target": "https://notgov.tw/"}); m != nil {
		t.Errorf("notgov.tw 不含獨立的 gov label，不該被規則命中，卻被 %s 擋下", m.RuleID)
	}
}

// 萬用字元授權 *.gov.tw 的一個子網域：只放行該子網域，不放行整個 gov.tw。
func TestWildcardScopedToOneSubdomainDoesNotOpenWholeSuffix(t *testing.T) {
	policy := mustCompile(t, Scope{Wildcards: []string{"*.agency.gov.tw"}})

	mustAllow(t, policy, "https://api.agency.gov.tw/", "萬用字元涵蓋的子網域")
	mustAllow(t, policy, "https://www.agency.gov.tw/x", "萬用字元涵蓋的子網域")
	// 頂層與其他機構不受影響
	mustBlock(t, policy, "https://agency.gov.tw/", "萬用字元不涵蓋頂層")
	mustBlock(t, policy, "https://api.other.gov.tw/", "萬用字元不涵蓋其他機構")
	mustBlock(t, policy, "https://a.b.agency.gov.tw/", "多層子網域不應被單層萬用字元放行")
}

// 與 grant-scope-target.py 的負向控制對應：控制組必須真的會被規則命中，
// 否則「負向控制通過」只是因為探測字串根本沒觸發規則，等於什麼都沒測。
func TestNegativeControlHostActuallyTriggersRule(t *testing.T) {
	// 沒有任何 scope 時，下列主機都必須被擋，否則拿它當負向控制是無效的。
	policy := mustCompile(t, Scope{Domains: []string{"case-a.gov.tw"}})
	for _, host := range []string{
		"https://portal.agency.gov.example/", // 腳本目前的 CONTROL_HOST
		"https://status.city.gov.example/",   // scope_test.go 用的控制組
		"https://case-b.gov.tw/",             // 真實後綴
	} {
		mustBlock(t, policy, host, "負向控制必須會被規則命中")
	}
}

// 規則的實際覆蓋範圍。規則只認「gov 這個獨立 label」，所以判斷結果完全取決於
// 主機名裡有沒有一層剛好叫 gov，跟國家無關。
//
// 實測（2026-10-03，見 issue：教育網域不在保護範圍內）：
//
//	.gov.tw / .gov.cn / .gov.hk / .gov.com   阻擋
//	.gov.uk / .gov.au / .gov.jp / .gov.sg / .gov.in  阻擋
//	直接 .gov TLD（whitehouse.gov）            阻擋
//	多層子網域（deep.nested.gov.cn）            阻擋
//
//	.edu.tw / .edu.cn / .edu.hk / .edu        放行 ← 不在保護範圍
//	notgov.tw / a.govx.tw                     放行（gov 非獨立 label，正確）
func TestRuleSuffixCoverage(t *testing.T) {
	policy := mustCompile(t, Scope{}) // 空 scope = 純規則行為

	blocked := []string{
		"a.gov.tw", "a.gov.cn", "a.gov.hk", "a.gov.com",
		"api.agency.gov.tw", "deep.nested.gov.cn",
		"whitehouse.gov", "a.gov.uk", "a.gov.au", "a.gov.jp", "a.gov.sg", "a.gov.in",
	}
	for _, h := range blocked {
		mustBlock(t, policy, "https://"+h+"/", "gov 網域應被保護")
	}

	// 這組是刻意的：整個主機名裡必須完全沒有獨立叫 gov 的 label 才算數。
	// 注意 govx.gov.tw 反而「應該」被擋 —— 它的 label 是 govx / gov / tw，
	// 中間那層就是 gov，是真的政府網域。
	for _, h := range []string{"notgov.tw", "a.govx.tw", "www.govx.org"} {
		if m := policy.Check("http_request", map[string]interface{}{"target": "https://" + h + "/"}); m != nil {
			t.Errorf("%q 沒有獨立的 gov label，不該被規則命中，卻被 %s 擋下", h, m.RuleID)
		}
	}
	mustBlock(t, policy, "https://govx.gov.tw/", "中層 label 就是 gov，應被保護")
}

// TestEduIsNotCoveredByGovernmentRule 記錄一個**刻意的決定**，不是 bug。
//
// 2026-10-03 確認：government-domains 規則的 pattern 裡沒有 edu，
// 所以教育網域一律放行，不需要任何 scope 授權。
//
// 決定：維持不保護。使用者實際承接的案件中edu佔比高，且edu目標本來就在
// 明確的授權案件範圍內，額外要求授權只增加摩擦、不增加實質防護。
//
// 取捨（知情選擇，不是遺漏）：edu 目標不會留下 scope 授權紀錄。
// 若日後要 enforce「只掃已授權目標」，edu 會是缺口，需先把 edu 納入規則，
// 並同步更新本測試與 internal/config 的範例設定 —— 不要默默改掉這裡。
func TestEduIsNotCoveredByGovernmentRule(t *testing.T) {
	policy := mustCompile(t, Scope{})
	for _, h := range []string{
		"a.edu.tw", "a.edu.cn", "a.edu.hk", "a.edu",
		"ntu.edu.tw", "edu.tw", "www.nthu.edu.tw",
	} {
		if m := policy.Check("http_request", map[string]interface{}{"target": "https://" + h + "/"}); m != nil {
			t.Errorf("%q 目前不在 government-domains 保護範圍，卻被 %s 擋下；"+
				"若這是預期變更，請更新本測試的說明", h, m.RuleID)
		}
	}
}
