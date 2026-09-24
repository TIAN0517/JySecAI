// Package toolschema provides a read-only facade over already-loaded
// config.ToolConfig. It is the single source of truth for tool schema lookups
// at runtime: argument validation, tool_search fast path, and preflight all
// read from the same immutable snapshot.
//
// The registry MUST NOT re-read YAML on every query. The snapshot is replaced
// atomically when the surrounding config reload happens (see Snapshot.Replace).
package toolschema

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"

	"jysecai/internal/config"
)

// Field describes one tool parameter as exposed by the registry.
type Field struct {
	Name        string
	Type        string
	Required    bool
	Description string
}

// SchemaSnapshot is an immutable view of all enabled tools.
//
// Once published via Registry.Set, a snapshot is never mutated; callers may
// freely share it across goroutines.
type SchemaSnapshot struct {
	// byName is keyed by the canonical tool name (case-insensitive lookup
	// through Registry). Storing the ToolConfig allows callers to access the
	// original Command / Args / ArgMapping without an extra indirection.
	byName map[string]*config.ToolConfig
}

// Empty returns true when the snapshot contains no enabled tools.
func (s *SchemaSnapshot) Empty() bool {
	return s == nil || len(s.byName) == 0
}

// Names returns the sorted list of enabled tool names. The order is
// deterministic so callers can rely on it for error messages and tests.
func (s *SchemaSnapshot) Names() []string {
	if s == nil {
		return nil
	}
	out := make([]string, 0, len(s.byName))
	for n := range s.byName {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// Has reports whether a tool with the given (case-insensitive) name exists.
func (s *SchemaSnapshot) Has(name string) bool {
	if s == nil {
		return false
	}
	_, ok := s.byName[canonical(name)]
	return ok
}

// Get returns the underlying *config.ToolConfig for the given name.
// Callers MUST treat the returned pointer as read-only.
func (s *SchemaSnapshot) Get(name string) (*config.ToolConfig, bool) {
	if s == nil {
		return nil, false
	}
	tc, ok := s.byName[canonical(name)]
	return tc, ok
}

// RequiredFields returns the parameter names that the tool declares as required.
func (s *SchemaSnapshot) RequiredFields(name string) []string {
	tc, ok := s.Get(name)
	if !ok || tc == nil {
		return nil
	}
	out := make([]string, 0)
	for _, p := range tc.Parameters {
		if p.Required {
			out = append(out, p.Name)
		}
	}
	return out
}

// OptionalFields returns the parameter names that the tool declares as optional.
func (s *SchemaSnapshot) OptionalFields(name string) []string {
	tc, ok := s.Get(name)
	if !ok || tc == nil {
		return nil
	}
	out := make([]string, 0)
	for _, p := range tc.Parameters {
		if !p.Required {
			out = append(out, p.Name)
		}
	}
	return out
}

// SchemaHash returns a stable hash over the tool's full parameter contract.
// The hash changes whenever any of Name/Type/Required/Flag/Format/Options
// changes; it is stable across processes and platforms.
func (s *SchemaSnapshot) SchemaHash(name string) string {
	tc, ok := s.Get(name)
	if !ok || tc == nil {
		return ""
	}
	h := sha256.New()
	h.Write([]byte(tc.Name))
	h.Write([]byte{0})
	// Sort parameters by Name so the hash is independent of YAML ordering.
	ps := append([]config.ParameterConfig(nil), tc.Parameters...)
	sort.Slice(ps, func(i, j int) bool { return ps[i].Name < ps[j].Name })
	for _, p := range ps {
		h.Write([]byte(p.Name))
		h.Write([]byte{0})
		h.Write([]byte(p.Type))
		h.Write([]byte{0})
		if p.Required {
			h.Write([]byte("1"))
		} else {
			h.Write([]byte("0"))
		}
		h.Write([]byte{0})
		h.Write([]byte(p.Flag))
		h.Write([]byte{0})
		h.Write([]byte(p.Format))
		h.Write([]byte{0})
		h.Write([]byte(p.Template))
		h.Write([]byte{0})
		// Sort Options to make the hash stable.
		opts := append([]string(nil), p.Options...)
		sort.Strings(opts)
		for _, o := range opts {
			h.Write([]byte(o))
			h.Write([]byte{0x1f})
		}
	}
	return hex.EncodeToString(h.Sum(nil))
}

// ToolSearchEntry is the JSON-safe shape returned to the agent for exact-lookup
// tool_search matches. The Envelope field preserves the existing wire format
// ({"selectedTools":[...]}) so downstream consumers do not need to change.
type ToolSearchEntry struct {
	Name         string                 `json:"name"`
	SchemaHash   string                 `json:"schema_hash"`
	InputSchema  map[string]interface{} `json:"input_schema"`
	Description  string                 `json:"description,omitempty"`
	MatchCount   int                    `json:"-"` // number of tools that matched the regex
	Disambiguated bool                  `json:"-"`
}

// ToolSearchResult is what the tool_search fast path returns.
//
// Count == 0 means TOOL_NOT_FOUND, Count == 1 means an exact lookup that
// should also expose SchemaSnapshot to the agent, Count > 1 means
// TOOL_AMBIGUOUS. SelectedTools remains valid in all three cases so callers
// that only read selectedTools continue to work.
type ToolSearchResult struct {
	Regex         string             `json:"regex_pattern"`
	Count         int                `json:"count"`
	SelectedTools []string           `json:"selectedTools"`
	Entries       []ToolSearchEntry  `json:"entries,omitempty"`
	Ambiguous     bool               `json:"ambiguous,omitempty"`
}

// LookupByRegex finds tools whose Name matches re and returns a
// ToolSearchResult. The match is exact-name-only for `^name$` patterns and
// substring for plain regex. Returns Count == 0 if no match.
func (s *SchemaSnapshot) LookupByRegex(re string) ToolSearchResult {
	if s == nil {
		return ToolSearchResult{Regex: re, Count: 0, SelectedTools: []string{}}
	}
	names := s.Names()
	matched := make([]string, 0)
	exactAnchor := isExactAnchor(re)
	for _, n := range names {
		if matchRegexName(n, re, exactAnchor) {
			matched = append(matched, n)
		}
	}
	res := ToolSearchResult{Regex: re, Count: len(matched), SelectedTools: matched}
	if len(matched) == 1 {
		if tc, ok := s.Get(matched[0]); ok && tc != nil {
			res.Entries = []ToolSearchEntry{{
				Name:        tc.Name,
				SchemaHash:  s.SchemaHash(tc.Name),
				InputSchema: BuildInputSchema(tc),
				Description: tc.Description,
				MatchCount:  1,
			}}
		}
	} else if len(matched) > 1 {
		res.Ambiguous = true
	}
	return res
}

// BuildInputSchema renders the JSON-Schema-style argument map for a tool.
// Mirrors the shape produced by (*Executor).buildInputSchema but does not
// require an Executor instance; used by the registry facade so that
// validation and tool_search share one source of truth.
func BuildInputSchema(tc *config.ToolConfig) map[string]interface{} {
	if tc == nil {
		return map[string]interface{}{"type": "object", "properties": map[string]interface{}{}}
	}
	props := make(map[string]interface{}, len(tc.Parameters))
	required := make([]string, 0)
	for _, p := range tc.Parameters {
		props[p.Name] = map[string]interface{}{
			"type":        p.Type,
			"description": p.Description,
		}
		if len(p.Options) > 0 {
			props[p.Name].(map[string]interface{})["enum"] = p.Options
		}
		if p.Required {
			required = append(required, p.Name)
		}
	}
	out := map[string]interface{}{
		"type":       "object",
		"properties": props,
	}
	if len(required) > 0 {
		out["required"] = required
	}
	return out
}

// NewSnapshot builds an immutable snapshot from a slice of ToolConfig.
// Disabled tools are skipped. The returned snapshot is safe for concurrent
// reads and is the value type carried by Snapshot.
func NewSnapshot(tools []config.ToolConfig) *SchemaSnapshot {
	byName := make(map[string]*config.ToolConfig, len(tools))
	for i := range tools {
		tc := tools[i]
		if !tc.Enabled {
			continue
		}
		key := canonical(tc.Name)
		if key == "" {
			continue
		}
		// Keep the latest occurrence on name collision; matches the existing
		// behavior in (*Executor).buildToolIndex.
		entry := tc
		byName[key] = &entry
	}
	return &SchemaSnapshot{byName: byName}
}
