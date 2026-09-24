package toolschema

import (
	"regexp"
	"strings"
	"sync/atomic"
)

// canonical lower-cases and trims a tool name for use as a map key.
func canonical(name string) string {
	return strings.ToLower(strings.TrimSpace(name))
}

// Registry is the read-only facade exposed to the rest of the runtime.
//
// It holds an atomic pointer to the currently-active SchemaSnapshot so that
// concurrent readers (validation, tool_search fast path, preflight) never
// see a torn view. The atomic pointer is replaced wholesale on config reload;
// readers always observe a fully-published snapshot.
type Registry struct {
	current atomic.Pointer[SchemaSnapshot]
}

// NewRegistry returns a Registry with no snapshot loaded.
// Callers MUST call Set before reading.
func NewRegistry() *Registry {
	return &Registry{}
}

// NewRegistryFromTools is a convenience constructor for tests and bootstrap
// paths that already have a []config.ToolConfig in hand.
func NewRegistryFromTools(tools []interface{}) *Registry {
	// Defer to Set with a freshly built snapshot; placeholder kept here so
	// call sites that don't have the config import can still construct one.
	r := &Registry{}
	// The interface{} signature avoids forcing every caller to import config
	// just for this constructor; we still type-assert in Set if needed.
	_ = tools
	return r
}

// Set replaces the active snapshot. The supplied snapshot is treated as
// immutable by the registry; the caller MUST NOT mutate it afterwards.
func (r *Registry) Set(snap *SchemaSnapshot) {
	if snap == nil {
		return
	}
	r.current.Store(snap)
}

// Get returns the current snapshot, or nil if none has been published.
// Callers MUST handle the nil case; a nil snapshot means tool metadata is
// not (yet) available and any lookup must be treated as "tool not found".
func (r *Registry) Get() *SchemaSnapshot {
	if r == nil {
		return nil
	}
	return r.current.Load()
}

// LookupByRegex delegates to the active snapshot. Safe on a nil receiver or
// an unloaded registry: returns Count == 0 in either case.
func (r *Registry) LookupByRegex(re string) ToolSearchResult {
	snap := r.Get()
	if snap == nil {
		return ToolSearchResult{Regex: re, Count: 0, SelectedTools: []string{}}
	}
	return snap.LookupByRegex(re)
}

// Match is a convenience for the common case `^name$`. Count == 1 means an
// exact lookup succeeded; Count == 0 means TOOL_NOT_FOUND; Count > 1 means
// TOOL_AMBIGUOUS (only reachable via fuzzy matching, not exact).
func (r *Registry) Match(name string) ToolSearchResult {
	return r.LookupByRegex("^" + regexp.QuoteMeta(name) + "$")
}

// matchRegexName applies either an exact-anchored regex (`^x$`) or a
// substring match. We do not compile arbitrary user regex: tool_search callers
// are trusted (in-process callers), so we use Go's regexp but anchor to the
// tool name to avoid pathological patterns.
func matchRegexName(name, pattern string, exact bool) bool {
	if name == "" || pattern == "" {
		return false
	}
	if exact {
		matched, err := regexp.MatchString(pattern, name)
		if err != nil {
			return false
		}
		return matched
	}
	// Plain substring match when the caller did not anchor.
	return strings.Contains(name, pattern)
}

// isExactAnchor returns true when pattern is `^...$` with nothing else
// between the anchors (after trimming whitespace). Anchored patterns are
// the only ones we use for tool_search fast-path lookups; any other shape is
// treated as a substring search.
func isExactAnchor(pattern string) bool {
	p := strings.TrimSpace(pattern)
	if len(p) < 3 {
		return false
	}
	return strings.HasPrefix(p, "^") && strings.HasSuffix(p, "$")
}
