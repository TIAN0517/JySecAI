package tooltarget

import (
	"fmt"
	"strings"
	"sync"

	"jysecai/internal/failure"
)

// Scope describes HOW a target matched the allowlist. The Agent loop and
// audit logs may surface this to make the policy decision traceable.
type Scope string

const (
	ScopeExactHost Scope = "exact_host"
	ScopeExactIP   Scope = "exact_ip"
	ScopeNone      Scope = "none"
)

// Decision is the typed outcome of an authorization check.
type Decision struct {
	Allowed          bool         `json:"allowed"`
	Reason           string       `json:"reason,omitempty"`
	NormalizedTarget *Normalized  `json:"normalized_target,omitempty"`
	Scope            Scope        `json:"scope"`
	Code             failure.Code `json:"code,omitempty"`
	Note             string       `json:"note,omitempty"`
}

// Policy is the interface every authorization backend must satisfy. The
// ConfigAuthorizedTargetPolicy below is the first implementation; future
// DB-backed or OPA-backed implementations can swap in without changing the
// Executor.
type Policy interface {
	Check(toolName string, target *Normalized) Decision
}

// Entry is one row of the allowlist configuration. Exactly one of Host or IP
// must be set; mixing both in a single entry is rejected at load time.
type Entry struct {
	// Tool is the tool name this entry applies to (e.g. "nuclei"). Empty
	// means "applies to all tools checked against this policy".
	Tool string `yaml:"tool,omitempty" json:"tool,omitempty"`
	// Host is the exact hostname (case-insensitive) to allow.
	Host string `yaml:"host,omitempty" json:"host,omitempty"`
	// IP is the exact IP literal (v4 or v6) to allow.
	IP string `yaml:"ip,omitempty" json:"ip,omitempty"`
	// Note is an optional free-form comment that surfaces in audit logs.
	Note string `yaml:"note,omitempty" json:"note,omitempty"`
}

// Config is the on-disk shape of the authorized-targets policy. We keep it
// intentionally tiny in this revision: a flat list of exact host/IP entries,
// no wildcards, no CIDRs. Those features were explicitly out of scope for
// Scanner Runtime Optimization v2.
type Config struct {
	Entries []Entry `yaml:"entries" json:"entries"`
}

// ConfigAuthorizedTargetPolicy is the read-only allowlist backend. It is safe
// for concurrent reads; the allowlist is published via Replace and never
// mutated after publication.
type ConfigAuthorizedTargetPolicy struct {
	mu      sync.RWMutex
	entries map[string]map[string]Entry // tool -> lower(host/ip) -> Entry
	anyTool map[string]Entry            // entries with Tool == ""
}

// NewConfigAuthorizedTargetPolicy returns a policy with no entries. Use
// Replace to publish an allowlist before the first Check.
func NewConfigAuthorizedTargetPolicy() *ConfigAuthorizedTargetPolicy {
	return &ConfigAuthorizedTargetPolicy{
		entries: map[string]map[string]Entry{},
		anyTool: map[string]Entry{},
	}
}

// Replace atomically swaps the active allowlist. The supplied Config is
// shallow-copied so subsequent caller mutations do not affect the policy.
func (p *ConfigAuthorizedTargetPolicy) Replace(cfg Config) {
	next := &ConfigAuthorizedTargetPolicy{
		entries: map[string]map[string]Entry{},
		anyTool: map[string]Entry{},
	}
	for _, e := range cfg.Entries {
		entry := e
		key, scope := classifyEntry(entry)
		if key == "" {
			continue
		}
		_ = scope // reserved for future reporting
		if entry.Tool == "" {
			next.anyTool[key] = entry
			continue
		}
		bucket, ok := next.entries[entry.Tool]
		if !ok {
			bucket = map[string]Entry{}
			next.entries[entry.Tool] = bucket
		}
		bucket[key] = entry
	}
	p.mu.Lock()
	p.entries = next.entries
	p.anyTool = next.anyTool
	p.mu.Unlock()
}

// Check applies the allowlist to a normalized target. It returns a Decision
// whose Allowed is true only when the tool-specific entry OR a tool-agnostic
// entry matches the normalized host or IP exactly.
//
// Substring matching is intentionally impossible: the lookup is map-keyed on
// the normalized form, so `example.com.attacker.invalid` will not match an
// entry for `example.com`.
func (p *ConfigAuthorizedTargetPolicy) Check(toolName string, target *Normalized) Decision {
	if target == nil {
		return Decision{
			Allowed: false,
			Reason:  "target is nil",
			Scope:   ScopeNone,
			Code:    failure.CodeInvalidTarget,
		}
	}
	p.mu.RLock()
	defer p.mu.RUnlock()

	key, scope := keyForTarget(target)
	if key == "" {
		return Decision{
			Allowed:          false,
			Reason:           "target has no host or IP",
			NormalizedTarget: target,
			Scope:            ScopeNone,
			Code:             failure.CodeInvalidTarget,
		}
	}
	if entry, ok := p.entries[toolName][key]; ok {
		return Decision{
			Allowed:          true,
			NormalizedTarget: target,
			Scope:            scope,
			Code:             "",
			Note:             entry.Note,
		}
	}
	if entry, ok := p.anyTool[key]; ok {
		return Decision{
			Allowed:          true,
			NormalizedTarget: target,
			Scope:            scope,
			Code:             "",
			Note:             entry.Note,
		}
	}
	return Decision{
		Allowed:          false,
		Reason:           fmt.Sprintf("%s not in authorized target list", key),
		NormalizedTarget: target,
		Scope:            ScopeNone,
		Code:             failure.CodeTargetNotAuthorized,
	}
}

// classifyEntry returns the lookup key and scope for a configuration entry.
// Returns "" if the entry is malformed (neither host nor ip set).
func classifyEntry(e Entry) (string, Scope) {
	h := strings.ToLower(strings.TrimSpace(e.Host))
	if h != "" {
		return h, ScopeExactHost
	}
	ip := strings.TrimSpace(e.IP)
	if ip != "" {
		return ip, ScopeExactIP
	}
	return "", ScopeNone
}

// keyForTarget returns the lookup key (and scope) that the allowlist uses
// for the given normalized target. Empty key means "no usable key".
func keyForTarget(t *Normalized) (string, Scope) {
	switch t.Kind {
	case KindIP:
		return t.Host, ScopeExactIP
	case KindHostname, KindURL:
		return strings.ToLower(t.Host), ScopeExactHost
	}
	return "", ScopeNone
}
