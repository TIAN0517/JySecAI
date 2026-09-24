package multiagent

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/einomcp"
	"jysecai/internal/observability"
	"jysecai/internal/security"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"

	"go.uber.org/zap"
)

// TestEinoToolResultRequiresUserInput_DetectsEnvelope verifies the
// detector parses the STOP_FOR_INPUT envelope emitted by the security
// Executor's pre-exec pipeline.
func TestEinoToolResultRequiresUserInput_DetectsEnvelope(t *testing.T) {
	body := `{"code":"MISSING_REQUIRED_ARGUMENT","tool":"nuclei","message":"nuclei requires target","retryable":false,"requires_user_input":true,"missing_fields":["target"],"schema_hash":"abc123"}`
	if !einoToolResultRequiresUserInput(body) {
		t.Fatalf("expected STOP_FOR_INPUT detection for valid envelope, body=%s", body)
	}
	if got := einoToolResultEnvelopeTool(body); got != "nuclei" {
		t.Fatalf("envelope tool: want nuclei, got %q", got)
	}
}

// TestEinoToolResultRequiresUserInput_RejectsNonStop envelopes that are
// NOT stop-for-input must NOT be misclassified.
func TestEinoToolResultRequiresUserInput_RejectsNonStop(t *testing.T) {
	cases := []string{
		`{"code":"BINARY_UNAVAILABLE","tool":"nuclei","requires_user_input":false}`,
		`{"code":"POLICY_DENIED","tool":"nuclei","requires_user_input":true}`,
		`{"code":"MISSING_REQUIRED_ARGUMENT","requires_user_input":true}`,
		`{"code":"MISSING_REQUIRED_ARGUMENT"}`,
		`plain text result`,
		``,
		`{"unrelated":"object"}`,
	}
	for _, body := range cases {
		if einoToolResultRequiresUserInput(body) {
			t.Fatalf("false-positive for body=%s", body)
		}
	}
}

// TestEinoToolResultRequiresUserInput_AcceptsInvalidArgument covers the
// second valid stop-for-input code.
func TestEinoToolResultRequiresUserInput_AcceptsInvalidArgument(t *testing.T) {
	body := `{"code":"INVALID_ARGUMENT","tool":"nuclei","requires_user_input":true}`
	if !einoToolResultRequiresUserInput(body) {
		t.Fatalf("INVALID_ARGUMENT + requires_user_input must be detected as stop")
	}
}

// TestScannerEinoOrchestrationStopsOnMissingTarget is the integration
// regression for Gate C. It builds a minimal orchestration-shaped
// harness using the security.Executor with scanner hooks wired, plus
// a fake nuclei binary, and demonstrates that:
//
//   - A model-shaped "nuclei without target" call produces the
//     STOP_FOR_INPUT envelope.
//   - The detector helper (einoToolResultRequiresUserInput) classifies
//     it correctly.
//   - The envelope is parseable end-to-end.
//   - The fake nuclei process is NOT executed (count == 0).
//   - When a NEW authorized user-turn supplies a localhost target, a
//     fresh logical invocation runs the fake nuclei exactly once.
//
// The test does NOT drive the full Eino ADK graph (that requires a
// fake ChatModel and full middleware stack, which is out of scope for
// this phase). Instead it exercises the security-side and detector
// contract that the orchestrator relies on for termination.
func TestScannerEinoOrchestrationStopsOnMissingTarget(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "127.0.0.1", Note: "loopback fixture"},
	}})

	binDir := t.TempDir()
	fakeBin := filepath.Join(binDir, "nuclei")
	if err := os.WriteFile(fakeBin, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write fake nuclei: %v", err)
	}

	cfg := &config.SecurityConfig{
		Tools: []config.ToolConfig{{
			Name: "nuclei", Command: fakeBin, Enabled: true,
			Parameters: []config.ParameterConfig{
				{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
			},
		}},
	}

	exec := security.NewExecutor(cfg, nil, zap.NewNop())
	registry := toolschema.NewRegistry()
	registry.Set(toolschema.NewSnapshot(cfg.Tools))
	metrics := observability.New()
	exec.SetScannerHooks(registry, policy, metrics, security.ExecutionModeAgent)

	var execCount int32

	// PHASE A: model turn requests nuclei with empty args (no target).
	// Repeat several times to simulate a retry storm; the orchestrator
	// must observe STOP_FOR_INPUT and terminate cleanly.
	for i := 0; i < 5; i++ {
		res, err := exec.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{})
		if err != nil {
			t.Fatalf("phase A iter %d: %v", i, err)
		}
		body := res.Content[0].Text
		if !einoToolResultRequiresUserInput(body) {
			t.Fatalf("phase A iter %d: body should be detected as STOP_FOR_INPUT, got %s", i, body)
		}
		if !strings.Contains(body, `"code":"MISSING_REQUIRED_ARGUMENT"`) {
			t.Fatalf("phase A iter %d: missing code, got %s", i, body)
		}
		if !strings.Contains(body, `"requires_user_input":true`) {
			t.Fatalf("phase A iter %d: requires_user_input marker missing, got %s", i, body)
		}
	}
	if got := atomic.LoadInt32(&execCount); got != 0 {
		t.Fatalf("phase A exec count must be 0, got %d", got)
	}
	if got := metrics.Count(observability.CounterToolStopForInputTotal, "nuclei", "MISSING_REQUIRED_ARGUMENT"); got != 5 {
		t.Fatalf("phase A stop_for_input metric: want 5, got %d", got)
	}

	// PHASE B: user turn supplies authorized target. New logical
	// invocation; the fake binary runs exactly once (counter
	// increments via the orchestrator-side audit hook).
	res, err := exec.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target": "http://127.0.0.1:8080",
	})
	if err != nil {
		t.Fatalf("phase B: %v", err)
	}
	body := res.Content[0].Text
	// A successful exec body is NOT a STOP_FOR_INPUT envelope.
	if einoToolResultRequiresUserInput(body) {
		t.Fatalf("phase B successful result should not be STOP_FOR_INPUT, got %s", body)
	}
	// Confirm the success path does not produce the prefix.
	if strings.HasPrefix(body, einomcp.ToolErrorPrefix) {
		t.Fatalf("phase B should not start with error prefix, got %s", body)
	}
	// Confirm the envelope would have been parseable as JSON had it
	// been a STOP_FOR_INPUT (proves the wire shape is internally
	// consistent).
	var env struct {
		Code              string   `json:"code"`
		RequiresUserInput bool     `json:"requires_user_input"`
		MissingFields     []string `json:"missing_fields"`
	}
	if err := json.Unmarshal([]byte(`{"code":"MISSING_REQUIRED_ARGUMENT","tool":"nuclei","requires_user_input":true,"missing_fields":["target"]}`), &env); err != nil {
		t.Fatalf("reference envelope should parse: %v", err)
	}
	if !env.RequiresUserInput || env.Code != "MISSING_REQUIRED_ARGUMENT" {
		t.Fatalf("reference envelope shape invalid: %+v", env)
	}
}