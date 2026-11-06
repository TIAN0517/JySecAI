package toolguard

import (
	"net"
	"regexp"
	"strings"
)

// 專案授權範圍（TargetScope）。
//
// 專案的測試範圍（projects.scope_json）原本只寫進提示層：模型看得到「這是授權範圍」，
// 但沒有任何強制力。TargetScope 把同一份範圍帶進攔截層：
//
//   - Allow（targets）：命中者豁免內建的 government-domains 規則，其他規則照常判斷。
//   - Deny（exclude）：命中者一律攔截，且優先於 Allow。
//
// 本檔案只用標準函式庫，維持 internal/toolguard 零內部 import 的性質。

const (
	// ProjectScopeExcludeRuleID 是專案排除清單攔截時使用的規則 ID。
	ProjectScopeExcludeRuleID = "project-scope-exclude"

	// ProjectScopeExcludeRuleName 是專案排除清單攔截時顯示的規則名稱。
	ProjectScopeExcludeRuleName = "專案排除目標"

	// projectScopeExcludeMessage 是專案排除清單攔截時的提醒文字。
	projectScopeExcludeMessage = "识别到 {match}，该目标在本项目的 exclude 排除清单内，工具调用已被拦截，请调整测试范围后再试。"
)

// TargetScope 是編譯後的專案授權範圍，可安全並行使用。
type TargetScope struct {
	allow  compiledScope
	deny   compiledScope
	active bool
	// allowSource / denySource 保留原始項目，供顯示與回溯（報告、提示層）。
	allowSource *Scope
	denySource  *Scope
}

// NewTargetScope 編譯專案授權範圍。
//
// allow 是已授權目標，命中者豁免內建的 government-domains 規則；deny 是明確排除的目標，
// 命中者一律攔截。兩者皆為 nil 或空時回傳 nil，代表這次呼叫不套用任何專案範圍。
func NewTargetScope(allow, deny *Scope) (*TargetScope, error) {
	if allow == nil && deny == nil {
		return nil, nil
	}
	compiledAllow, err := compileScopeWithLabel("project scope allow", allow)
	if err != nil {
		return nil, err
	}
	compiledDeny, err := compileScopeWithLabel("project scope deny", deny)
	if err != nil {
		return nil, err
	}
	scope := &TargetScope{
		allow:       compiledAllow,
		deny:        compiledDeny,
		allowSource: allow,
		denySource:  deny,
	}
	scope.active = compiledAllow.active || compiledDeny.active
	if !scope.active {
		return nil, nil
	}
	return scope, nil
}

// AllowEntries 回傳允許清單的原始項目（domains、domain_suffixes、wildcards、cidrs）。
func (s *TargetScope) AllowEntries() []string {
	if s == nil {
		return nil
	}
	return scopeSourceEntries(s.allowSource)
}

// DenyEntries 回傳排除清單的原始項目。
func (s *TargetScope) DenyEntries() []string {
	if s == nil {
		return nil
	}
	return scopeSourceEntries(s.denySource)
}

// scopeSourceEntries 把 Scope 攤平成固定順序的項目清單。
func scopeSourceEntries(scope *Scope) []string {
	if scope == nil {
		return nil
	}
	out := make([]string, 0, len(scope.Domains)+len(scope.DomainSuffixes)+len(scope.Wildcards)+len(scope.CIDRs))
	out = append(out, scope.Domains...)
	out = append(out, scope.DomainSuffixes...)
	out = append(out, scope.Wildcards...)
	out = append(out, scope.CIDRs...)
	return out
}

// denyMatch 回傳第一個命中排除清單的目標。
//
// 排除清單獨立於規則生效：即使沒有任何規則命中該目標，只要落在專案的 exclude 內就攔截。
func (s *TargetScope) denyMatch(candidates []string, toolName string) *Match {
	if s == nil || !s.deny.active {
		return nil
	}
	for _, candidate := range candidates {
		for _, host := range candidateHosts(candidate) {
			if !s.deny.contains(host) {
				continue
			}
			message := strings.NewReplacer(
				"{match}", host,
				"{tool}", toolName,
				"{rule}", ProjectScopeExcludeRuleName,
			).Replace(projectScopeExcludeMessage)
			return &Match{
				RuleID:      ProjectScopeExcludeRuleID,
				RuleName:    ProjectScopeExcludeRuleName,
				MatchedText: host,
				Message:     message,
			}
		}
	}
	return nil
}

var (
	// ipv6BracketPattern 抓出以方括號包住的 IPv6 位址（例如 [2001:db8::1]）。
	ipv6BracketPattern = regexp.MustCompile(`\[[0-9A-Fa-f:.]+\]`)
	// hostTokenPattern 抓出看起來像主機的片段（允許數字、底線、星號、問號、點、減號）。
	hostTokenPattern = regexp.MustCompile(`[A-Za-z0-9_*][A-Za-z0-9_*.-]*`)
)

// candidateHosts 從自由文字中抽出可能的主機。
//
// 攔截層比對的是文字而不是已解析的網址，因此這裡盡可能保守：只取含點的片段與方括號
// 包住的 IPv6。誤抽到的片段（例如 "report.txt"）只有在真的落在排除清單時才會造成
// 攔截，因此誤判的方向是安全的（寧可多抽，不可漏抽）。
func candidateHosts(text string) []string {
	var out []string
	seen := make(map[string]struct{})
	add := func(value string) {
		host := normalizeHost(value)
		if host == "" {
			return
		}
		if _, exists := seen[host]; exists {
			return
		}
		seen[host] = struct{}{}
		out = append(out, host)
	}
	for _, literal := range ipv6BracketPattern.FindAllString(text, -1) {
		add(literal)
	}
	for _, token := range hostTokenPattern.FindAllString(text, -1) {
		if strings.Contains(token, ".") {
			add(token)
		}
	}
	return out
}

// scopeEntryKind 是自由字串解析後的分類。
type scopeEntryKind int

const (
	scopeEntryDomain scopeEntryKind = iota
	scopeEntryWildcard
	scopeEntrySuffix
	scopeEntryCIDR
)

// ParseScopeEntries 把自由格式的目標字串轉成 Scope。
//
// 分類順序固定：
//   - 合法 CIDR（不含 scheme 且含 "/"）→ cidrs
//   - 含 "*" 或 "?" → wildcards
//   - 開頭為 "." → domain_suffixes
//   - 其餘含點或為 IP → domains
//
// 無法解讀成主機的項目（例如 "n/a"、"待補"）會被忽略，不讓整份範圍失效。
func ParseScopeEntries(entries []string) (*Scope, error) {
	out := &Scope{}
	for _, raw := range entries {
		value := strings.TrimSpace(raw)
		if value == "" {
			continue
		}
		kind, entry, ok := classifyScopeEntry(value)
		if !ok {
			continue
		}
		switch kind {
		case scopeEntryCIDR:
			out.CIDRs = append(out.CIDRs, entry)
		case scopeEntryWildcard:
			out.Wildcards = append(out.Wildcards, entry)
		case scopeEntrySuffix:
			out.DomainSuffixes = append(out.DomainSuffixes, entry)
		default:
			out.Domains = append(out.Domains, entry)
		}
	}
	return out, nil
}

// classifyScopeEntry 判斷單一自由字串屬於哪一種範圍型別。
func classifyScopeEntry(value string) (scopeEntryKind, string, bool) {
	// CIDR 必須在剝掉路徑之前判斷，否則 "192.0.2.0/24" 只會剩下主機。
	if !strings.Contains(value, "://") && strings.Contains(value, "/") {
		if _, _, err := net.ParseCIDR(value); err == nil {
			return scopeEntryCIDR, value, true
		}
	}
	host := normalizeHost(value)
	if host == "" {
		return scopeEntryDomain, "", false
	}
	if strings.ContainsAny(host, "*?") {
		return scopeEntryWildcard, host, true
	}
	if strings.HasPrefix(host, ".") {
		return scopeEntrySuffix, host, true
	}
	if net.ParseIP(host) != nil || strings.Contains(host, ".") {
		return scopeEntryDomain, host, true
	}
	return scopeEntryDomain, "", false
}
