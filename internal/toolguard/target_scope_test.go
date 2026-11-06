package toolguard

import (
	"strings"
	"testing"
)

// 專案授權範圍（TargetScope）測試。
//
// 設計目標：讓「專案測試範圍」從提示層升級成攔截層的強制條件。
//   - Allow（targets）：命中者豁免內建的 government-domains 規則，其餘規則照常判斷。
//   - Deny（exclude）：命中者一律攔截，且優先於 Allow。
//   - 未注入範圍時，行為必須與原本完全一致。

func projectScope(t *testing.T, allow, deny *Scope) *TargetScope {
	t.Helper()
	scope, err := NewTargetScope(allow, deny)
	if err != nil {
		t.Fatal(err)
	}
	return scope
}

func TestTargetScopeDenyBlocksEvenWhenAlsoAllowed(t *testing.T) {
	// exclude 優先否決：同一主機同時出現在 targets 與 exclude 時仍要攔截。
	scope := projectScope(t,
		&Scope{Domains: []string{"legacy.gov.tw"}},
		&Scope{Domains: []string{"legacy.gov.tw"}},
	)
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://legacy.gov.tw/old"}, scope)
	if match == nil {
		t.Fatal("exclude target must be blocked")
	}
	if match.RuleID != ProjectScopeExcludeRuleID {
		t.Fatalf("expected rule %q, got %q", ProjectScopeExcludeRuleID, match.RuleID)
	}
	if match.MatchedText != "legacy.gov.tw" {
		t.Fatalf("expected matched host legacy.gov.tw, got %q", match.MatchedText)
	}
}

func TestTargetScopeDenyBlocksTargetNoRuleMatches(t *testing.T) {
	// 排除清單獨立於規則生效：沒有任何規則命中的目標也要被擋下。
	scope := projectScope(t, nil, &Scope{Domains: []string{"internal.corp.example"}})
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://internal.corp.example/api"}, scope)
	if match == nil || match.RuleID != ProjectScopeExcludeRuleID {
		t.Fatalf("expected project-scope-exclude, got %#v", match)
	}
}

func TestTargetScopeDenyBlocksWhenGlobalGuardDisabled(t *testing.T) {
	// 專案 exclude 的強制力獨立於 tool_guard.enabled（安全優先）。
	cfg := DefaultConfig()
	cfg.Enabled = false
	policy, err := Compile(cfg)
	if err != nil {
		t.Fatal(err)
	}
	scope := projectScope(t, nil, &Scope{Domains: []string{"internal.corp.example"}})
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://internal.corp.example/api"}, scope); match == nil {
		t.Fatal("project exclude must still block when the global guard is disabled")
	}
	// 但關閉全域攔截後，規則本身不該再生效。
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example"}, scope); match != nil {
		t.Fatalf("disabled guard must not block by rule, got %#v", match)
	}
}

func TestTargetScopeAllowExemptsGovernmentRule(t *testing.T) {
	scope := projectScope(t, &Scope{Domains: []string{"portal.agency.gov.example"}}, nil)
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://portal.agency.gov.example/x"}, scope); match != nil {
		t.Fatalf("authorized project target must be allowed, got %#v", match)
	}
	// 範圍外的政府目標仍應攔截
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://status.city.gov.example"}, scope); match == nil {
		t.Fatal("out-of-scope government target must still be blocked")
	}
}

func TestTargetScopeAllowDoesNotExemptCustomRules(t *testing.T) {
	// 與全域 scope 語意一致：允許清單只豁免內建政府規則，自訂規則照常判斷。
	cfg := DefaultConfig()
	cfg.Rules = append(cfg.Rules, Rule{
		ID:      "internal-only",
		Name:    "內部網段",
		Enabled: true,
		Pattern: `(?i)\.corp\.example`,
		Message: "命中 {match}",
	})
	policy, err := Compile(cfg)
	if err != nil {
		t.Fatal(err)
	}
	scope := projectScope(t, &Scope{Domains: []string{"api.corp.example"}}, nil)
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://api.corp.example/x"}, scope); match == nil {
		t.Fatal("custom rule must still block an allow-listed target")
	}
}

func TestCheckScopedWithoutScopeMatchesCheck(t *testing.T) {
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	args := map[string]interface{}{"target": "https://portal.agency.gov.example"}
	if policy.CheckScoped("http_request", args, nil) == nil {
		t.Fatal("nil scope must keep blocking government targets")
	}
	// 空範圍（沒有任何條目）等同沒有範圍。
	empty := projectScope(t, &Scope{}, &Scope{})
	if empty != nil {
		t.Fatal("an entirely empty scope must compile to nil")
	}
	if policy.CheckScoped("http_request", args, empty) == nil {
		t.Fatal("empty scope must keep blocking government targets")
	}
}

func TestTargetScopeDenyMatchesCIDRAndWildcard(t *testing.T) {
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	scope := projectScope(t, nil, &Scope{
		CIDRs:     []string{"192.0.2.0/24"},
		Wildcards: []string{"*.blocked.example"},
	})
	for _, target := range []string{
		"https://192.0.2.10/api",
		"https://192.0.2.255/api",
		"https://a.blocked.example/api",
	} {
		match := policy.CheckScoped("http_request", map[string]interface{}{"target": target}, scope)
		if match == nil || match.RuleID != ProjectScopeExcludeRuleID {
			t.Fatalf("target %q must be blocked by project exclude, got %#v", target, match)
		}
	}
	// 同一網段外的位址不受影響
	if match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://198.51.100.5/api"}, scope); match != nil {
		t.Fatalf("out-of-CIDR target must not be blocked, got %#v", match)
	}
}

func TestTargetScopeDenyIgnoresUnrelatedText(t *testing.T) {
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	scope := projectScope(t, nil, &Scope{Domains: []string{"internal.corp.example"}})
	args := map[string]interface{}{"command": "cat /var/log/app.log && echo done"}
	if match := policy.CheckScoped("shell", args, scope); match != nil {
		t.Fatalf("non-host text must not be blocked, got %#v", match)
	}
}

func TestTargetScopeDenyFindsHostInsideJSONArgument(t *testing.T) {
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	scope := projectScope(t, nil, &Scope{Domains: []string{"internal.corp.example"}})
	args := map[string]interface{}{
		"payload": `{"hosts":["a.internal.corp.example","b.example.org"],"note":"internal.corp.example"}`,
	}
	match := policy.CheckScoped("http_request", args, scope)
	if match == nil || match.RuleID != ProjectScopeExcludeRuleID {
		t.Fatalf("host nested in JSON argument must be blocked, got %#v", match)
	}
}

func TestParseScopeEntriesClassifiesEntries(t *testing.T) {
	scope, err := ParseScopeEntries([]string{
		"https://app.example.com/path?q=1",
		"app.example.com:8443",
		"*.cdn.example.com",
		".gov.tw",
		"192.0.2.0/24",
		"198.51.100.7",
		"  ",
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(scope.Domains) != 3 {
		t.Fatalf("expected 3 domains, got %#v", scope.Domains)
	}
	if scope.Domains[0] != "app.example.com" || scope.Domains[1] != "app.example.com" || scope.Domains[2] != "198.51.100.7" {
		t.Fatalf("unexpected domains: %#v", scope.Domains)
	}
	if len(scope.Wildcards) != 1 || scope.Wildcards[0] != "*.cdn.example.com" {
		t.Fatalf("unexpected wildcards: %#v", scope.Wildcards)
	}
	if len(scope.DomainSuffixes) != 1 || scope.DomainSuffixes[0] != ".gov.tw" {
		t.Fatalf("unexpected suffixes: %#v", scope.DomainSuffixes)
	}
	if len(scope.CIDRs) != 1 || scope.CIDRs[0] != "192.0.2.0/24" {
		t.Fatalf("unexpected cidrs: %#v", scope.CIDRs)
	}
}

func TestParseScopeEntriesIgnoresUnusableEntries(t *testing.T) {
	scope, err := ParseScopeEntries([]string{"n/a", "待補", "app.example.com"})
	if err != nil {
		t.Fatal(err)
	}
	if len(scope.Domains) != 1 || scope.Domains[0] != "app.example.com" {
		t.Fatalf("unexpected domains: %#v", scope.Domains)
	}
}

func TestTargetScopeRefusalMessageUsesSingleSource(t *testing.T) {
	// 攔截回執必須能被既有的 ParseRefusal 辨識，否則舊紀錄升級與攔截統計會失效。
	scope := projectScope(t, nil, &Scope{Domains: []string{"internal.corp.example"}})
	policy, err := Compile(DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	match := policy.CheckScoped("http_request", map[string]interface{}{"target": "https://internal.corp.example/api"}, scope)
	if match == nil {
		t.Fatal("expected a match")
	}
	text := RefusalMessage(match)
	if !strings.HasPrefix(text, BlockedPrefix) {
		t.Fatalf("refusal must start with the shared prefix, got %q", text)
	}
	name, id, matched, ok := ParseRefusal(text)
	if !ok {
		t.Fatalf("refusal must be parseable, got %q", text)
	}
	if id != ProjectScopeExcludeRuleID || name != ProjectScopeExcludeRuleName {
		t.Fatalf("unexpected rule %q / %q", name, id)
	}
	if matched != "internal.corp.example" {
		t.Fatalf("unexpected matched text %q", matched)
	}
}
