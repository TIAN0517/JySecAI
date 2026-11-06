package toolguard

import (
	"encoding/json"
	"strings"
	"testing"
)

// 授權範圍（Scope）測試。
//
// 設計目標：讓有正式授權的政府／關鍵基礎設施案件可以正常進行，
// 同時維持預設的保護行為（未設定 Scope 時一律阻擋）。

func scopedConfig(scope Scope) Config {
	cfg := DefaultConfig()
	cfg.Scope = &scope
	return cfg
}

func TestScopeEmptyPreservesDefaultBehaviour(t *testing.T) {
	// 未設定 Scope 時，行為必須與原本完全一致
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example"}); match == nil {
		t.Fatal("empty scope must keep blocking government targets")
	}
	// nil scope
	policy, err = Compile(scopedConfig(Scope{}))
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example"}); match == nil {
		t.Fatal("nil-equivalent scope must keep blocking")
	}
}

func TestScopeAllowsAuthorizedGovernmentTargets(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{
		Domains: []string{"portal.agency.gov.example", "api.department.gov.example"},
	}))
	if err != nil {
		t.Fatal(err)
	}
	for _, target := range []string{
		"https://portal.agency.gov.example:4000/config",
		"https://portal.agency.gov.example",
		"http://api.department.gov.example/cases",
		"curl https://portal.agency.gov.example:4004/login",
		"nmap -p 4000-4008 portal.agency.gov.example",
	} {
		if match := policy.Check("http_request", map[string]interface{}{"target": target}); match != nil {
			t.Fatalf("scoped target %q must be allowed, got %+v", target, match)
		}
	}
	// 範圍外的政府目標仍應阻擋
	if match := policy.Check("http_request", map[string]interface{}{"target": "https://status.city.gov.example"}); match == nil {
		t.Fatal("out-of-scope government target must still be blocked")
	}
}

func TestScopeDomainSuffixes(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{DomainSuffixes: []string{".city.gov.example", ".department.gov.example"}}))
	if err != nil {
		t.Fatal(err)
	}
	for _, target := range []string{
		"https://status.city.gov.example/app",
		"https://dispatch.city.gov.example/",
		"https://api.department.gov.example/service",
		"https://apps.department.gov.example/",
	} {
		if match := policy.Check("request", map[string]interface{}{"target": target}); match != nil {
			t.Fatalf("%q should be in scope, got %+v", target, match)
		}
	}
	// 防禦：後綴不能被用來繞過，後綴後再加其他網域時不應命中。
	for _, target := range []string{
		"https://city.gov.example.evil.test/",
		"https://status.city.gov.example.evil.test/",
		"https://other.gov.example/",
	} {
		if match := policy.Check("request", map[string]interface{}{"target": target}); match == nil {
			t.Fatalf("%q must remain blocked (suffix smuggling)", target)
		}
	}
}

func TestScopeWildcards(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{Wildcards: []string{"*.portal.agency.gov.example"}}))
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("request", map[string]interface{}{"target": "https://a.portal.agency.gov.example/x"}); match != nil {
		t.Fatalf("wildcard match should be allowed, got %+v", match)
	}
	// 單層通配：多一層子網域不應命中 *（不跨越層級）。
	if match := policy.Check("request", map[string]interface{}{"target": "https://a.b.portal.agency.gov.example/"}); match == nil {
		t.Fatal("wildcard must not span multiple labels")
	}
	// 未跳脫的 regex 元字元不可繞過
	policy, err = Compile(scopedConfig(Scope{Wildcards: []string{".gov.tw"}}))
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("request", map[string]interface{}{"target": "https://evil.gov.tw/"}); match == nil {
		t.Fatal("plain suffix wildcard must not act as a substring match")
	}
}

func TestScopeCIDRs(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{CIDRs: []string{"192.0.2.10/32", "198.51.100.0/24"}}))
	if err != nil {
		t.Fatal(err)
	}
	for _, target := range []string{
		"https://192.0.2.10:8000/config",
		"http://198.51.100.93:4000/",
		"nmap 198.51.100.200",
	} {
		if match := policy.Check("request", map[string]interface{}{"target": target}); match != nil {
			t.Fatalf("%q should be in scope, got %+v", target, match)
		}
	}
	// 網段外的位址不應被視為授權目標。
	// 注意：政府域名規則只比對網域文字，纯 IP 不會被該規則阻擋；
	// 這裡驗證的是 scope 不會過度授權，而非規則是否攔截。
	for _, target := range []string{
		"https://198.51.101.93/",
		"https://192.0.2.11/",
	} {
		if policy.scope.contains(normalizeHost(target)) {
			t.Fatalf("%q is outside the CIDR and must not be in scope", target)
		}
	}
	// 但若該位址同時是政府域名且不在 scope，仍必須被規則阻擋
	if match := policy.Check("request", map[string]interface{}{"target": "https://status.city.gov.example"}); match == nil {
		t.Fatal("out-of-scope government domain must still be blocked")
	}
}

func TestScopeDecodesPercentEscapes(t *testing.T) {
	// 編碼過的目標也應被視為在範圍內，否則 scope 可被繞過
	policy, err := Compile(scopedConfig(Scope{Domains: []string{"portal.agency.gov.example"}}))
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("request", map[string]interface{}{"target": "https://portal%2Eagency%2Egov%2Eexample/"}); match != nil {
		t.Fatalf("percent-encoded in-scope target should be allowed, got %+v", match)
	}
}

func TestScopeInNestedArgs(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{Domains: []string{"portal.agency.gov.example"}}))
	if err != nil {
		t.Fatal(err)
	}
	for _, args := range []map[string]interface{}{
		{"targets": []interface{}{map[string]interface{}{"target": "https://portal.agency.gov.example"}}},
		{"payload": json.RawMessage(`{"target":"https://portal\u002Eagency\u002Egov\u002Eexample"}`)},
		{"nested": map[string]interface{}{"a": map[string]interface{}{"b": "https://portal.agency.gov.example:4000"}}},
	} {
		if match := policy.Check("request", args); match != nil {
			t.Fatalf("nested in-scope target should be allowed: %+v", match)
		}
	}
}

func TestScopeOnlyExemptsTheMatchedAuthorizedTarget(t *testing.T) {
	policy, err := Compile(scopedConfig(Scope{Domains: []string{"portal.agency.gov.example"}}))
	if err != nil {
		t.Fatal(err)
	}

	match := policy.Check("request", map[string]interface{}{
		"authorized": "https://portal.agency.gov.example/status",
		"other":      "https://unrelated.gov.tw/admin",
	})
	if match == nil || !strings.EqualFold(match.MatchedText, "unrelated.gov.tw") {
		t.Fatalf("out-of-scope target in a mixed request must still be blocked, got %+v", match)
	}

	match = policy.Check("request", map[string]interface{}{
		"targets": "https://portal.agency.gov.example/status https://unrelated.gov.tw/admin",
	})
	if match == nil || !strings.EqualFold(match.MatchedText, "unrelated.gov.tw") {
		t.Fatalf("later out-of-scope target in the same string must still be blocked, got %+v", match)
	}
}

func TestScopePreciselyHandlesLegacyShortGovernmentMatch(t *testing.T) {
	policy, err := Compile(Config{
		Enabled: true,
		Rules: []Rule{{
			ID: "government-domains", Name: "government", Enabled: true,
			Pattern: `(?i)gov`, Message: "blocked {match}",
		}},
		Scope: &Scope{Domains: []string{"portal.agency.gov.example"}},
	})
	if err != nil {
		t.Fatal(err)
	}
	match := policy.Check("request", map[string]interface{}{
		"targets": []string{"https://portal.agency.gov.example/status", "https://unrelated.gov.tw/admin"},
	})
	if match == nil {
		t.Fatal("short legacy match must still find the out-of-scope host")
	}
}

func TestScopeInvalidEntriesRejected(t *testing.T) {
	for name, scope := range map[string]Scope{
		"suffix without dot": {DomainSuffixes: []string{"gov.tw"}},
		"bad cidr":           {CIDRs: []string{"999.1.1.1/24"}},
		"empty domain":       {Domains: []string{"   "}},
		"empty wildcard":     {Wildcards: []string{""}},
	} {
		if _, err := Compile(scopedConfig(scope)); err == nil {
			t.Fatalf("%s: expected compile error", name)
		}
	}
}

func TestNormalizeHost(t *testing.T) {
	for input, want := range map[string]string{
		"https://Portal.Agency.gov.Example:4000/config": "portal.agency.gov.example",
		"portal.agency.gov.example.":                    "portal.agency.gov.example",
		"http://user:pass@host.gov.tw/x":                "host.gov.tw",
		"192.0.2.10":                                    "192.0.2.10",
		"[2001:db8::1]:443":                             "2001:db8::1",
		"":                                              "",
		"   ":                                           "",
	} {
		if got := normalizeHost(input); got != want {
			t.Errorf("normalizeHost(%q) = %q, want %q", input, got, want)
		}
	}
}

func TestScopeDoesNotDisableOtherRules(t *testing.T) {
	// 自訂阻擋規則仍應對範圍內目標生效（scope 只豁免目標類規則）
	cfg := Config{
		Enabled: true,
		Rules: []Rule{{
			ID: "no-destructive", Name: "禁止破坏", Enabled: true,
			Pattern: "DROP\\s+TABLE", Message: "禁止 {match}",
		}},
		Scope: &Scope{Domains: []string{"portal.agency.gov.example"}},
	}
	policy, err := Compile(cfg)
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.Check("sql", map[string]interface{}{"q": "DROP TABLE t"}); match == nil {
		t.Fatal("non-target blocking rule must still apply inside scope")
	}
	if match := policy.Check("sql", map[string]interface{}{"q": "SELECT 1"}); match != nil {
		t.Fatalf("safe statement should pass: %+v", match)
	}
}

func TestManagerUpdateKeepsScopeIsolated(t *testing.T) {
	mgr, err := NewManager(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	cfg := scopedConfig(Scope{Domains: []string{"portal.agency.gov.example"}})
	if err := mgr.Update(cfg); err != nil {
		t.Fatal(err)
	}
	// 外部改動原 slice 不應影響已生效的 policy
	cfg.Scope.Domains[0] = "evil.example"
	if match := mgr.Check("request", map[string]interface{}{"target": "https://portal.agency.gov.example/"}); match != nil {
		t.Fatalf("policy must snapshot its scope, got %+v", match)
	}
	got := mgr.Config()
	if got.Scope == nil || len(got.Scope.Domains) != 1 || !strings.EqualFold(got.Scope.Domains[0], "portal.agency.gov.example") {
		t.Fatalf("Config() must return a copy, got %+v", got.Scope)
	}
}

func TestDefaultConfigScopeIsNil(t *testing.T) {
	// 預設必須是 nil，否則設定檔會多出 scope 欄位而偏離舊格式
	if got := DefaultConfig().Scope; got != nil {
		t.Fatalf("DefaultConfig().Scope = %+v, want nil", got)
	}
}
