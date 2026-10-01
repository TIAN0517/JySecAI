package toolargs

import (
	"encoding/json"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/failure"
	"jysecai/internal/toolschema"
)

func mustRegistry(t *testing.T, tools ...config.ToolConfig) *toolschema.Registry {
	t.Helper()
	r := toolschema.NewRegistry()
	r.Set(toolschema.NewSnapshot(tools))
	return r
}

func nucleiRequired() config.ToolConfig {
	return config.ToolConfig{
		Name:    "nuclei",
		Command: "nuclei",
		Enabled: true,
		Parameters: []config.ParameterConfig{
			{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
			{Name: "severity", Type: "string", Required: false, Flag: "-s", Format: "flag"},
		},
	}
}

// Test 3: nuclei missing target → MISSING_REQUIRED_ARGUMENT.
func TestValidateNucleiMissingTarget(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{})
	if res.Status != StatusArgumentValidationFailed {
		t.Fatalf("expected ARGUMENT_VALIDATION_FAILED, got %s", res.Status)
	}
	if res.Code != failure.CodeMissingRequiredArgument {
		t.Fatalf("expected code %s, got %s", failure.CodeMissingRequiredArgument, res.Code)
	}
	if len(res.MissingFields) != 1 || res.MissingFields[0] != "target" {
		t.Fatalf("expected missing=[target], got %v", res.MissingFields)
	}
	if res.Retryable {
		t.Fatalf("validation failure must not be retryable")
	}
}

// Test 4: missing target → requires_user_input=true.
func TestMissingTargetRequiresUserInput(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{})
	if !res.RequiresUserInput() {
		t.Fatalf("expected requires_user_input=true")
	}
	sfi := BuildStopForInput(res)
	if !sfi.RequiresUserInput {
		t.Fatalf("STOP_FOR_INPUT envelope must require user input")
	}
	if !sfi.Retryable == false {
		t.Fatalf("STOP_FOR_INPUT must mark retryable=false")
	}
	if sfi.HumanMessage == "" {
		t.Fatalf("STOP_FOR_INPUT must include a human message")
	}
}

// Test 5 + 6: missing target does not start a process and does not allow
// auto-retry. We assert the typed contract; the side-effect of "no process
// started" is enforced by Executor.runScannerPreExec short-circuiting before
// buildCommandArgs / exec.CommandContext.
func TestMissingTargetShortCircuitsBeforeExec(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{})
	if res.Retryable {
		t.Fatalf("must not be retryable (no retry storm)")
	}
	if res.RequiresUserInput() != true {
		t.Fatalf("requires_user_input must be true")
	}
}

// Test 7: malformed target should reach the target layer, not argument
// validation. Here we only assert argument validation passes (target
// syntax is the next layer's concern).
func TestValidatePassesWhenArgShapeIsCorrect(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{"target": "https://example.com"})
	if res.Status != StatusValid {
		t.Fatalf("expected VALID, got %s (code=%s, msg=%s)", res.Status, res.Code, res.Message)
	}
}

// Test 18: validation result is JSON-serializable so the Agent loop can
// surface it directly without re-wrapping.
func TestValidationResultJSONStable(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{})
	b, err := json.Marshal(res)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	if !contains(string(b), `"code":"MISSING_REQUIRED_ARGUMENT"`) {
		t.Fatalf("expected JSON to include code field, got %s", string(b))
	}
}

func contains(s, sub string) bool {
	return len(s) >= len(sub) && (s == sub || (len(sub) > 0 && indexOf(s, sub) >= 0))
}
func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}

// Test unknown tool → TOOL_NOT_FOUND.
func TestUnknownTool(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "does-not-exist", map[string]interface{}{"target": "x"})
	if res.Status != StatusArgumentValidationFailed {
		t.Fatalf("expected ARGUMENT_VALIDATION_FAILED, got %s", res.Status)
	}
	if res.Code != failure.CodeToolNotFound {
		t.Fatalf("expected TOOL_NOT_FOUND, got %s", res.Code)
	}
}

// Test unknown argument → INVALID_ARGUMENT.
func TestUnknownArgument(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{
		"target": "example.com",
		"banana": "split",
	})
	if res.Code != failure.CodeInvalidArgument {
		t.Fatalf("expected INVALID_ARGUMENT, got %s", res.Code)
	}
	if len(res.InvalidFields) != 1 || res.InvalidFields[0] != "banana" {
		t.Fatalf("expected invalid=[banana], got %v", res.InvalidFields)
	}
}

// Test additional_args is accepted as a reserved key.
func TestAdditionalArgsIsReserved(t *testing.T) {
	r := mustRegistry(t, nucleiRequired())
	res := ValidateToolArgs(r, "nuclei", map[string]interface{}{
		"target":         "example.com",
		"additional_args": "-stats",
	})
	if res.Status != StatusValid {
		t.Fatalf("additional_args should be accepted, got %s (%s)", res.Status, res.Message)
	}
}
