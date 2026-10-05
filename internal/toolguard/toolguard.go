// Package toolguard applies configurable blocking rules before tool execution.
// It inspects tool names and arguments, including JSON string values and common
// percent escapes. It does not resolve hosts or inspect redirects, files, or
// arbitrary encoded payloads, and is not an exhaustive target authorization check.
package toolguard

import (
	"encoding/json"
	"fmt"
	"net"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync/atomic"
)

const (
	MaxRules         = 100
	MaxIDLength      = 128
	MaxNameLength    = 200
	MaxPatternLength = 4096
	MaxMessageLength = 4096

	// The named group keeps surrounding boundary punctuation out of the reminder.
	governmentDomainPattern = `(?i)(?:^|[^\p{L}\p{M}\p{N}_.-])(?P<match>(?:(?:[\p{L}\p{M}\p{N}_*-]+\.)+gov(?:\.[\p{L}\p{M}\p{N}_*-]+)*|gov(?:\.[\p{L}\p{M}\p{N}_*-]+)+|\.gov(?:\.[\p{L}\p{M}\p{N}_*-]+)*)\.?)(?:$|[^\p{L}\p{M}\p{N}_.-])`
	defaultMessage          = "识别到 {match}，工具调用已被安全规则「{rule}」拦截，请检查目标与授权范围后再试。"
)

type Config struct {
	Enabled bool   `json:"enabled" yaml:"enabled"`
	Rules   []Rule `json:"rules" yaml:"rules"`
	// Scope declares targets covered by a signed engagement. An exact target
	// match inside Scope bypasses the built-in government-domain rule while all
	// unrelated rules and targets continue to be evaluated.
	//
	// A nil or empty Scope preserves historical behaviour exactly. A pointer
	// keeps "absent" distinct from "present but empty" so configs written by
	// this build stay byte-compatible with earlier ones.
	Scope *Scope `json:"scope,omitempty" yaml:"scope,omitempty"`
}

// Scope is an explicit allow-list of authorized targets. All fields are
// optional; a nil or empty Scope matches nothing and changes no behaviour.
type Scope struct {
	// Domains are exact hostnames, e.g. "portal.agency.gov.example".
	Domains []string `json:"domains" yaml:"domains,omitempty"`
	// DomainSuffixes match any host ending with the given suffix, e.g.
	// ".gov.tw" matches "agency.gov.tw" but not "gov.tw.evil.example".
	DomainSuffixes []string `json:"domain_suffixes" yaml:"domain_suffixes,omitempty"`
	// Wildcards use shell-style globs on the full host, e.g. "*.city.gov.example".
	// '*' deliberately does not cross a dot.
	Wildcards []string `json:"wildcards" yaml:"wildcards,omitempty"`
	// CIDRs are textual IPv4/IPv6 blocks, e.g. "192.0.2.10/32".
	CIDRs []string `json:"cidrs" yaml:"cidrs,omitempty"`
}

type Rule struct {
	ID      string `json:"id" yaml:"id"`
	Name    string `json:"name" yaml:"name"`
	Enabled bool   `json:"enabled" yaml:"enabled"`
	Pattern string `json:"pattern" yaml:"pattern"`
	Message string `json:"message" yaml:"message"`
}

type Match struct {
	RuleID      string `json:"ruleId"`
	RuleName    string `json:"ruleName"`
	MatchedText string `json:"matchedText"`
	Message     string `json:"message"`
}

type compiledRule struct {
	rule       Rule
	pattern    *regexp.Regexp
	matchGroup int
}

// compiledScope holds the pre-parsed Scope for fast matching.
type compiledScope struct {
	domains   map[string]struct{}
	suffixes  []string
	wildcards []*regexp.Regexp
	cidrs     []*net.IPNet
	active    bool
}

// Policy is an immutable snapshot safe for concurrent checks.
type Policy struct {
	config Config
	rules  []compiledRule
	scope  compiledScope
}

// DefaultConfig enables a conservative government-domain rule, including .gov,
// .gov.cn and wildcard forms such as *.gov.*. Additional rules can be configured.
//
// The default Scope is nil, so out-of-the-box behaviour is unchanged:
// government and other critical targets stay blocked. Operators running an
// authorized engagement populate Scope to permit exactly the hosts named in
// their engagement letter.
func DefaultConfig() Config {
	return Config{
		Enabled: true,
		Rules: []Rule{{
			ID:      "government-domains",
			Name:    "政府网站保护",
			Enabled: true,
			Pattern: governmentDomainPattern,
			Message: "识别到 {match}，禁止攻击政府网站。请检查目标与授权范围，并更换为已获授权的非政府目标。",
		}},
	}
}

// Compile validates every rule, including disabled ones. Limits are byte counts.
// Rule order determines precedence. An optional named (?P<match>...) group selects
// the text inserted into {match}; otherwise the entire regex match is used.
func Compile(config Config) (*Policy, error) {
	if len(config.Rules) > MaxRules {
		return nil, fmt.Errorf("tool guard: at most %d rules are allowed", MaxRules)
	}
	policy := &Policy{config: cloneConfig(config)}
	ids := make(map[string]struct{}, len(config.Rules))
	for i, rule := range policy.config.Rules {
		prefix := fmt.Sprintf("tool guard rule %d", i+1)
		if strings.TrimSpace(rule.ID) == "" || len(rule.ID) > MaxIDLength {
			return nil, fmt.Errorf("%s: id must be nonempty and at most %d bytes", prefix, MaxIDLength)
		}
		if rule.ID != strings.TrimSpace(rule.ID) {
			return nil, fmt.Errorf("%s: id must not have surrounding whitespace", prefix)
		}
		if _, exists := ids[rule.ID]; exists {
			return nil, fmt.Errorf("%s: duplicate id %q", prefix, rule.ID)
		}
		ids[rule.ID] = struct{}{}
		if strings.TrimSpace(rule.Name) == "" || len(rule.Name) > MaxNameLength {
			return nil, fmt.Errorf("%s: name must be nonempty and at most %d bytes", prefix, MaxNameLength)
		}
		if strings.TrimSpace(rule.Pattern) == "" || len(rule.Pattern) > MaxPatternLength {
			return nil, fmt.Errorf("%s: pattern must be nonempty and at most %d bytes", prefix, MaxPatternLength)
		}
		if len(rule.Message) > MaxMessageLength {
			return nil, fmt.Errorf("%s: message must be at most %d bytes", prefix, MaxMessageLength)
		}
		pattern, err := regexp.Compile(rule.Pattern)
		if err != nil {
			return nil, fmt.Errorf("%s (%s): invalid regular expression: %w", prefix, rule.ID, err)
		}
		if rule.Enabled {
			policy.rules = append(policy.rules, compiledRule{rule: rule, pattern: pattern, matchGroup: pattern.SubexpIndex("match")})
		}
	}
	scope, err := compileScope(policy.config.Scope)
	if err != nil {
		return nil, err
	}
	policy.scope = scope
	return policy, nil
}

const (
	MaxScopeDomains   = 2000
	MaxScopeSuffixes  = 200
	MaxScopeWildcards = 500
	MaxScopeCIDRs     = 500
	MaxScopeEntryLen  = 512
)

// compileScope validates and pre-parses the authorized-target list. A nil or
// empty scope returns an inactive value, so behaviour is identical to a build
// without this feature.
func compileScope(scope *Scope) (compiledScope, error) {
	out := compiledScope{domains: make(map[string]struct{})}
	if scope == nil {
		return out, nil
	}
	if len(scope.Domains) > MaxScopeDomains {
		return out, fmt.Errorf("tool guard: scope.domains exceeds %d entries", MaxScopeDomains)
	}
	if len(scope.DomainSuffixes) > MaxScopeSuffixes {
		return out, fmt.Errorf("tool guard: scope.domain_suffixes exceeds %d entries", MaxScopeSuffixes)
	}
	if len(scope.Wildcards) > MaxScopeWildcards {
		return out, fmt.Errorf("tool guard: scope.wildcards exceeds %d entries", MaxScopeWildcards)
	}
	if len(scope.CIDRs) > MaxScopeCIDRs {
		return out, fmt.Errorf("tool guard: scope.cidrs exceeds %d entries", MaxScopeCIDRs)
	}

	for _, raw := range scope.Domains {
		host := normalizeHost(raw)
		if host == "" {
			return out, fmt.Errorf("tool guard: scope.domains contains an invalid entry %q", raw)
		}
		out.domains[host] = struct{}{}
	}
	for _, raw := range scope.DomainSuffixes {
		suffix := strings.ToLower(strings.TrimSpace(raw))
		if suffix == "" || len(suffix) > MaxScopeEntryLen || !strings.HasPrefix(suffix, ".") {
			return out, fmt.Errorf("tool guard: scope.domain_suffixes entry %q must start with '.'", raw)
		}
		out.suffixes = append(out.suffixes, suffix)
	}
	for _, raw := range scope.Wildcards {
		glob := strings.ToLower(strings.TrimSpace(raw))
		if glob == "" || len(glob) > MaxScopeEntryLen {
			return out, fmt.Errorf("tool guard: scope.wildcards entry %q is empty or too long", raw)
		}
		// Only * and ? are honoured; everything else is quoted so a pattern
		// such as ".gov.tw" cannot smuggle regex metacharacters.
		// '*' deliberately does NOT cross a dot: "*.gov.tw" must not match
		// "a.b.gov.tw", otherwise a one-label scope would silently widen.
		var b strings.Builder
		b.WriteString("^")
		for _, r := range glob {
			switch r {
			case '*':
				b.WriteString(`[^./]*`)
			case '?':
				b.WriteString(`[^./]`)
			default:
				b.WriteString(regexp.QuoteMeta(string(r)))
			}
		}
		b.WriteString("$")
		re, err := regexp.Compile(b.String())
		if err != nil {
			return out, fmt.Errorf("tool guard: scope.wildcards entry %q is invalid: %w", raw, err)
		}
		out.wildcards = append(out.wildcards, re)
	}
	for _, raw := range scope.CIDRs {
		entry := strings.TrimSpace(raw)
		if entry == "" || len(entry) > MaxScopeEntryLen {
			return out, fmt.Errorf("tool guard: scope.cidrs entry %q is empty or too long", raw)
		}
		_, network, err := net.ParseCIDR(entry)
		if err != nil {
			return out, fmt.Errorf("tool guard: scope.cidrs entry %q is invalid: %w", raw, err)
		}
		out.cidrs = append(out.cidrs, network)
	}

	out.active = len(out.domains) > 0 || len(out.suffixes) > 0 ||
		len(out.wildcards) > 0 || len(out.cidrs) > 0
	return out, nil
}

// normalizeHost lowercases a host and strips an optional scheme, userinfo,
// port, path and trailing dot. It returns "" when no host can be recovered.
func normalizeHost(value string) string {
	v := strings.ToLower(strings.TrimSpace(value))
	if v == "" {
		return ""
	}
	if idx := strings.Index(v, "://"); idx >= 0 {
		v = v[idx+3:]
	}
	if idx := strings.LastIndex(v, "@"); idx >= 0 {
		v = v[idx+1:]
	}
	if idx := strings.IndexAny(v, "/?#"); idx >= 0 {
		v = v[:idx]
	}
	// Strip a :port suffix, but keep bracketed IPv6 literals intact.
	if strings.HasPrefix(v, "[") {
		if end := strings.Index(v, "]"); end >= 0 {
			return strings.TrimSuffix(v[1:end], ".")
		}
	} else if idx := strings.LastIndex(v, ":"); idx >= 0 {
		if _, err := strconv.Atoi(v[idx+1:]); err == nil {
			v = v[:idx]
		}
	}
	v = strings.TrimSuffix(v, ".")
	if v == "" {
		return ""
	}
	return v
}

// contains reports whether host is inside the authorized scope.
func (s compiledScope) contains(host string) bool {
	if !s.active || host == "" {
		return false
	}
	if _, ok := s.domains[host]; ok {
		return true
	}
	for _, suffix := range s.suffixes {
		if strings.HasSuffix(host, suffix) && len(host) > len(suffix) {
			return true
		}
	}
	for _, re := range s.wildcards {
		if re.MatchString(host) {
			return true
		}
	}
	if ip := net.ParseIP(host); ip != nil {
		for _, network := range s.cidrs {
			if network.Contains(ip) {
				return true
			}
		}
	}
	return false
}

func hostByte(value byte) bool {
	return value >= 'a' && value <= 'z' || value >= 'A' && value <= 'Z' ||
		value >= '0' && value <= '9' || strings.ContainsRune("._-*?", rune(value))
}

func hostAroundMatch(candidate string, start, end int) string {
	for start > 0 && hostByte(candidate[start-1]) {
		start--
	}
	for end < len(candidate) && hostByte(candidate[end]) {
		end++
	}
	return normalizeHost(candidate[start:end])
}

func (p *Policy) matchedTargetInScope(candidate string, start, end int) bool {
	if p == nil || !p.scope.active {
		return false
	}
	// Expand a short legacy match such as "gov" to the surrounding hostname.
	// This also keeps aggregate JSON candidates precise when they carry multiple
	// targets: each regex match expands only within its own hostname token.
	return p.scope.contains(hostAroundMatch(candidate, start, end))
}

func matchBounds(rule compiledRule, indices []int) (int, int) {
	start, end := indices[0], indices[1]
	if group := rule.matchGroup; group > 0 && indices[group*2] >= 0 {
		start, end = indices[group*2], indices[group*2+1]
	}
	return start, end
}

func renderMatch(rule compiledRule, candidate, toolName string, indices []int) *Match {
	start, end := matchBounds(rule, indices)
	matched := candidate[start:end]
	message := rule.rule.Message
	if strings.TrimSpace(message) == "" {
		message = defaultMessage
	}
	// A single replacement pass prevents matched text from introducing
	// additional template substitutions.
	message = strings.NewReplacer("{match}", matched, "{tool}", toolName, "{rule}", rule.rule.Name).Replace(message)
	return &Match{RuleID: rule.rule.ID, RuleName: rule.rule.Name, MatchedText: matched, Message: message}
}

// Check returns the first blocking rule, or nil when the call is allowed. Args
// should be JSON-compatible and must not be mutated while Check is running.
//
// A government-domain match proceeds when that exact matched host is inside the
// configured authorization Scope. Scope never suppresses unrelated rules or a
// second out-of-scope target carried in the same request.
// allMatches returns every non-overlapping match of re in s, but it does not let
// a consumed boundary character hide the match that follows it.
//
// The built-in rule is anchored on both sides by a *consuming* context group:
// `(?:^|[^\p{L}\p{M}\p{N}_.-])host(?:$|[^\p{L}\p{M}\p{N}_.-])`. Go's RE2 has no
// lookahead, so the character proving the boundary is part of the match.
// FindAllStringSubmatchIndex restarts at the end of the previous match, which
// means that character is already gone and the next hostname has no leading
// boundary left to satisfy. In "authorized.gov.example president.gov.cn" only
// the first hostname was ever examined, so an out-of-scope government target
// riding along behind an in-scope one was never blocked.
//
// Give one character of context back after each match so the following token
// can use it as its own leading boundary.
func allMatches(re *regexp.Regexp, s string) [][]int {
	var out [][]int
	for pos := 0; pos < len(s); {
		loc := re.FindStringSubmatchIndex(s[pos:])
		if loc == nil {
			break
		}
		for i := range loc {
			if loc[i] >= 0 {
				loc[i] += pos
			}
		}
		out = append(out, loc)
		next := loc[1]
		if next > pos {
			next-- // hand one consumed byte back as the next leading boundary
		}
		if next <= pos {
			break // no forward progress; a zero-width match would loop forever
		}
		pos = next
	}
	return out
}

func (p *Policy) Check(toolName string, args map[string]interface{}) *Match {
	if p == nil || !p.config.Enabled || len(p.rules) == 0 {
		return nil
	}
	candidates := candidateTexts(toolName, args)
	for _, rule := range p.rules {
		for _, candidate := range candidates {
			if rule.rule.ID != "government-domains" || !p.scope.active {
				indices := rule.pattern.FindStringSubmatchIndex(candidate)
				if indices != nil {
					return renderMatch(rule, candidate, toolName, indices)
				}
				continue
			}
			for _, indices := range allMatches(rule.pattern, candidate) {
				start, end := matchBounds(rule, indices)
				match := renderMatch(rule, candidate, toolName, indices)
				// Scope is a precise exception to the built-in target rule. Checking
				// this match prevents an allowed hostname elsewhere in the arguments
				// from suppressing an unrelated block.
				if p.matchedTargetInScope(candidate, start, end) {
					continue
				}
				return match
			}
		}
	}
	return nil
}

// Manager atomically replaces validated policy snapshots for live settings.
type Manager struct {
	policy atomic.Pointer[Policy]
}

func NewManager(config Config) (*Manager, error) {
	m := &Manager{}
	if err := m.Update(config); err != nil {
		return nil, err
	}
	return m, nil
}

// Update retains the active policy if validation fails.
func (m *Manager) Update(config Config) error {
	policy, err := Compile(config)
	if err != nil {
		return err
	}
	m.policy.Store(policy)
	return nil
}

func (m *Manager) Config() Config {
	if m == nil {
		return Config{}
	}
	if policy := m.policy.Load(); policy != nil {
		return cloneConfig(policy.config)
	}
	return Config{}
}

func (m *Manager) Check(toolName string, args map[string]interface{}) *Match {
	if m == nil {
		return nil
	}
	return m.policy.Load().Check(toolName, args)
}

func cloneConfig(config Config) Config {
	if config.Rules != nil {
		rules := make([]Rule, len(config.Rules))
		copy(rules, config.Rules)
		config.Rules = rules
	}
	// Deep-copy scope: Manager.Update may run concurrently with Check, and
	// sharing the backing array would let a later reload mutate a live policy.
	// A nil scope stays nil so it remains absent from persisted YAML.
	if config.Scope != nil {
		config.Scope = &Scope{
			Domains:        append([]string(nil), config.Scope.Domains...),
			DomainSuffixes: append([]string(nil), config.Scope.DomainSuffixes...),
			Wildcards:      append([]string(nil), config.Scope.Wildcards...),
			CIDRs:          append([]string(nil), config.Scope.CIDRs...),
		}
	}
	return config
}

func candidateTexts(toolName string, args map[string]interface{}) []string {
	var candidates []string
	seen := make(map[string]struct{})
	add := func(value string) {
		// Decode at most three rounds to cover common nested URL escaping
		// without claiming support for arbitrarily encoded tool inputs.
		for round := 0; round <= 3; round++ {
			if _, exists := seen[value]; !exists {
				seen[value] = struct{}{}
				candidates = append(candidates, value)
			}
			decoded := decodePercentEscapes(value)
			if decoded == value {
				break
			}
			value = decoded
		}
	}
	add(toolName)
	var walk func(interface{}, int)
	walk = func(value interface{}, remainingDepth int) {
		if remainingDepth == 0 {
			return
		}
		switch value := value.(type) {
		case string:
			add(value)
		case map[string]interface{}:
			keys := make([]string, 0, len(value))
			for key := range value {
				keys = append(keys, key)
			}
			sort.Strings(keys)
			for _, key := range keys {
				add(key)
				walk(value[key], remainingDepth-1)
			}
		case []interface{}:
			for _, item := range value {
				walk(item, remainingDepth-1)
			}
		}
	}
	// Unmarshaling also normalizes typed slices/maps, json.RawMessage and
	// escaped JSON keys/values into the recursive representation above.
	if raw, err := json.Marshal(args); err == nil {
		var value interface{}
		if json.Unmarshal(raw, &value) == nil {
			// encoding/json accepts at most 10,000 nesting levels. The decoded
			// tree is acyclic, so inspect every accepted string/key at that depth.
			walk(value, 10001)
		}
		add(string(raw))
	} else {
		// MCP rejects invalid JSON arguments independently; still inspect the
		// ordinary values if a caller supplies a non-JSON value alongside them.
		walk(args, 128)
	}
	return candidates
}

// Decode valid percent triplets even if another part of the string has a stray
// percent sign. Whole-string URL unescaping otherwise misses such mixed inputs.
func decodePercentEscapes(value string) string {
	if !strings.Contains(value, "%") {
		return value
	}
	var out strings.Builder
	out.Grow(len(value))
	for i := 0; i < len(value); i++ {
		if value[i] == '%' && i+2 < len(value) {
			hi, okHi := hexValue(value[i+1])
			lo, okLo := hexValue(value[i+2])
			if okHi && okLo {
				out.WriteByte(hi<<4 | lo)
				i += 2
				continue
			}
		}
		out.WriteByte(value[i])
	}
	return out.String()
}

func hexValue(value byte) (byte, bool) {
	switch {
	case value >= '0' && value <= '9':
		return value - '0', true
	case value >= 'a' && value <= 'f':
		return value - 'a' + 10, true
	case value >= 'A' && value <= 'F':
		return value - 'A' + 10, true
	default:
		return 0, false
	}
}
