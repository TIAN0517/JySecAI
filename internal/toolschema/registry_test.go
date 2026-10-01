package toolschema

import (
	"encoding/json"
	"testing"

	"jysecai/internal/config"
)

func newToolConfig(name string, params []config.ParameterConfig) config.ToolConfig {
	return config.ToolConfig{
		Name:       name,
		Command:    name,
		Enabled:    true,
		Parameters: params,
	}
}

func p(name, t string, required bool) config.ParameterConfig {
	return config.ParameterConfig{
		Name:     name,
		Type:     t,
		Required: required,
		Flag:     "-" + name,
		Format:   "flag",
	}
}

// Test 1 + 2: tool_search ^nuclei$ returns exactly one; exact lookup
// returns the full schema snapshot.
func TestLookupExactNameReturnsOneEntryWithSchema(t *testing.T) {
	snap := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{p("target", "string", true)}),
		newToolConfig("amass", []config.ParameterConfig{p("target", "string", true)}),
	})
	res := snap.LookupByRegex("^nuclei$")
	if res.Count != 1 {
		t.Fatalf("expected count=1, got %d (selected=%v)", res.Count, res.SelectedTools)
	}
	if res.SelectedTools[0] != "nuclei" {
		t.Fatalf("expected nuclei, got %v", res.SelectedTools)
	}
	if len(res.Entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(res.Entries))
	}
	e := res.Entries[0]
	if e.Name != "nuclei" {
		t.Fatalf("expected name nuclei, got %s", e.Name)
	}
	if e.SchemaHash == "" {
		t.Fatalf("expected non-empty schema hash")
	}
	if _, ok := e.InputSchema["properties"].(map[string]interface{}); !ok {
		t.Fatalf("expected properties object in InputSchema")
	}
	if _, ok := e.InputSchema["required"]; !ok {
		t.Fatalf("expected required array in InputSchema")
	}
}

// Test 9: tool_search envelope backward compatibility — the JSON wire
// format MUST still include selectedTools even when entries are present.
func TestLookupEnvelopeBackwardCompatible(t *testing.T) {
	snap := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{p("target", "string", true)}),
	})
	res := snap.LookupByRegex("^nuclei$")
	b, err := json.Marshal(res)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	var got map[string]interface{}
	if err := json.Unmarshal(b, &got); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if _, ok := got["selectedTools"]; !ok {
		t.Fatalf("envelope missing selectedTools: %s", string(b))
	}
	if got["count"].(float64) != 1 {
		t.Fatalf("expected count=1 in envelope, got %v", got["count"])
	}
}

// Test that schema hash is stable across builds and reorders.
func TestSchemaHashStable(t *testing.T) {
	a := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{
			p("target", "string", true),
			p("severity", "string", false),
		}),
	})
	b := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{
			p("severity", "string", false),
			p("target", "string", true),
		}),
	})
	if a.SchemaHash("nuclei") != b.SchemaHash("nuclei") {
		t.Fatalf("hash not stable across parameter reorder: %s vs %s",
			a.SchemaHash("nuclei"), b.SchemaHash("nuclei"))
	}
}

// Test that disabled tools are excluded from snapshots.
func TestDisabledToolsExcluded(t *testing.T) {
	tc := newToolConfig("nuclei", []config.ParameterConfig{p("target", "string", true)})
	tc.Enabled = false
	snap := NewSnapshot([]config.ToolConfig{tc})
	if snap.Has("nuclei") {
		t.Fatalf("disabled tool should not be visible")
	}
	if r := snap.LookupByRegex("^nuclei$"); r.Count != 0 {
		t.Fatalf("expected TOOL_NOT_FOUND, got count=%d", r.Count)
	}
}

// Test Registry atomic snapshot replace.
func TestRegistryReplace(t *testing.T) {
	r := NewRegistry()
	if got := r.LookupByRegex("^nuclei$"); got.Count != 0 {
		t.Fatalf("empty registry should report no matches, got %d", got.Count)
	}
	snap := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{p("target", "string", true)}),
	})
	r.Set(snap)
	if got := r.LookupByRegex("^nuclei$"); got.Count != 1 {
		t.Fatalf("expected 1 match after Set, got %d", got.Count)
	}
	// Replace with empty snapshot.
	r.Set(NewSnapshot(nil))
	if got := r.LookupByRegex("^nuclei$"); got.Count != 0 {
		t.Fatalf("expected 0 matches after empty Set, got %d", got.Count)
	}
}

// Test RequiredFields and OptionalFields.
func TestRequiredAndOptionalFields(t *testing.T) {
	snap := NewSnapshot([]config.ToolConfig{
		newToolConfig("nuclei", []config.ParameterConfig{
			p("target", "string", true),
			p("severity", "string", false),
		}),
	})
	req := snap.RequiredFields("nuclei")
	if len(req) != 1 || req[0] != "target" {
		t.Fatalf("expected required=[target], got %v", req)
	}
	opt := snap.OptionalFields("nuclei")
	if len(opt) != 1 || opt[0] != "severity" {
		t.Fatalf("expected optional=[severity], got %v", opt)
	}
}
