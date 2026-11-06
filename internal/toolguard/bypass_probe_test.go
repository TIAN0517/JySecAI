package toolguard

import (
	"regexp"
	"testing"
)

// TestScopeDoesNotHideASecondOutOfScopeTarget is the regression guard for the
// consumed-boundary bypass. The built-in rule wraps its hostname in a
// *consuming* context group on both sides, so a plain FindAll resumes past the
// character the next hostname needed as its own leading boundary. Any argument
// string that put an in-scope government-looking token first therefore had every
// later government target skipped entirely.
//
// The invariant: for one candidate string, an in-scope target must never
// suppress the evaluation of a second, out-of-scope one.
func TestScopeDoesNotHideASecondOutOfScopeTarget(t *testing.T) {
	cfg := DefaultConfig()
	cfg.Scope = &Scope{
		Domains:        []string{"authorized.gov.example"},
		DomainSuffixes: []string{".gov.tw"},
		Wildcards:      []string{"*.city.gov.example"},
		CIDRs:          []string{"192.0.2.0/24"},
	}
	policy, err := Compile(cfg)
	if err != nil {
		t.Fatalf("compile: %v", err)
	}

	// Out-of-scope government targets that MUST be blocked.
	mustBlock := []struct {
		name string
		args map[string]interface{}
	}{
		{"plain other gov", map[string]interface{}{"target": "president.gov.cn"}},
		{"other tld gov", map[string]interface{}{"target": "parliament.gov.uk"}},
		{"gov.cn subdomain", map[string]interface{}{"target": "miit.gov.cn"}},
		{"in-scope token as userinfo, real host is gov", map[string]interface{}{
			"target": "http://authorized.gov.example@president.gov.cn/"}},
		{"gov as path, real host is gov", map[string]interface{}{
			"target": "http://president.gov.cn/?x=authorized.gov.example"}},
		{"space separated, in-scope first", map[string]interface{}{
			"target": "authorized.gov.example president.gov.cn"}},
		{"comma separated, in-scope first", map[string]interface{}{
			"target": "authorized.gov.example,president.gov.cn"}},
		{"at separated, in-scope first", map[string]interface{}{
			"target": "authorized.gov.example@president.gov.cn"}},
		{"three targets, in-scope first", map[string]interface{}{
			"target": "authorized.gov.example a.gov.tw president.gov.cn"}},
		{"nested json arg", map[string]interface{}{
			"options": map[string]interface{}{"hosts": []interface{}{"authorized.gov.example", "president.gov.cn"}}}},
		{"gov host in map key", map[string]interface{}{"president.gov.cn": "1"}},
		{"uppercase", map[string]interface{}{"target": "PRESIDENT.GOV.CN"}},
		{"trailing dot", map[string]interface{}{"target": "president.gov.cn."}},
		{"percent-encoded dot", map[string]interface{}{"target": "president%2egov%2ecn"}},
		{"reversed userinfo", map[string]interface{}{
			"target": "http://president.gov.cn@authorized.gov.example/"}},
		{"explicit port", map[string]interface{}{"target": "president.gov.cn:8080"}},
	}
	for _, tc := range mustBlock {
		if m := policy.Check("nmap", tc.args); m == nil {
			t.Errorf("BYPASS: %s was allowed: %v", tc.name, tc.args)
		}
	}

	// Targets that are genuinely authorized, or that the rule does not cover.
	// These must NOT be blocked, otherwise the fix over-blocks.
	shouldAllow := []struct {
		name string
		args map[string]interface{}
	}{
		{"plain non-gov", map[string]interface{}{"target": "example.com"}},
		{"authorized exact domain", map[string]interface{}{"target": "authorized.gov.example"}},
		{"suffix scope", map[string]interface{}{"target": "agency.gov.tw"}},
		{"wildcard scope", map[string]interface{}{"target": "a.city.gov.example"}},
		{"cidr scope", map[string]interface{}{"target": "192.0.2.5"}},
		{"two in-scope targets together", map[string]interface{}{
			"target": "authorized.gov.example agency.gov.tw"}},
		{"in-scope plus unrelated host", map[string]interface{}{
			"target": "authorized.gov.example example.com"}},
	}
	for _, tc := range shouldAllow {
		if m := policy.Check("nmap", tc.args); m != nil {
			t.Errorf("false positive: %s was blocked by rule %q (matched %q)", tc.name, m.RuleID, m.MatchedText)
		}
	}
}

// TestAllMatchesTerminates guards the manual scan in allMatches. A zero-width
// match with no forward progress would otherwise spin forever on a hostile
// tool argument.
func TestAllMatchesTerminates(t *testing.T) {
	if got := allMatches(regexp.MustCompile(`x*`), "xxxx"); len(got) > len("xxxx")*2+2 {
		t.Errorf("allMatches produced %d matches on a 4-byte input; expected termination", len(got))
	}
	if got := allMatches(regexp.MustCompile(`(?i)gov`), ""); len(got) != 0 {
		t.Errorf("allMatches on empty input = %v, want none", got)
	}
	// A rule pattern that can match empty must still terminate on a long input.
	if got := allMatches(regexp.MustCompile(`(?i)(gov)?`), "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"); len(got) == 0 {
		t.Error("allMatches found nothing on an optional-match pattern")
	}
}

// TestAllMatchesFindsEveryToken pins the fix: every hostname in a
// space-separated list must be returned, not just the first.
func TestAllMatchesFindsEveryToken(t *testing.T) {
	re := regexp.MustCompile(`(?i)(?:^|\s)((?:\w+\.)+gov(?:\.\w+)*)`)
	got := allMatches(re, "a.gov.example b.gov.example c.gov.example")
	if len(got) != 3 {
		t.Fatalf("allMatches returned %d matches, want 3: %v", len(got), got)
	}
	for i, want := range []string{"a.gov.example", "b.gov.example", "c.gov.example"} {
		start, end := got[i][2], got[i][3]
		if s := "a.gov.example b.gov.example c.gov.example"[start:end]; s != want {
			t.Errorf("match %d = %q, want %q", i, s, want)
		}
	}
}
