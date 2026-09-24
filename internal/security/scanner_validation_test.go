package security

import (
	"context"
	"strings"
	"testing"

	"jysecai/internal/config"
	"jysecai/internal/failure"
	"jysecai/internal/observability"
	"jysecai/internal/preflight"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"
	"go.uber.org/zap"
)

// makeExecutor wires a minimal Executor with scanner hooks enabled.
// The preflight function is replaceable so tests can plug a no-op without
// depending on a real nuclei binary on PATH.
func makeExecutor(t *testing.T, policy tooltarget.Policy, mode ExecutionMode) (*Executor, *observability.Registry) {
	t.Helper()
	cfg := &config.SecurityConfig{
		Tools: []config.ToolConfig{
			{
				Name: "nuclei", Command: "nuclei", Enabled: true,
				Parameters: []config.ParameterConfig{
					{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
					{Name: "severity", Type: "string", Required: false, Flag: "-s", Format: "flag"},
				},
			},
		},
	}
	logger := zap.NewNop()
	e := NewExecutor(cfg, nil, logger)
	reg := toolschema.NewRegistry()
	reg.Set(toolschema.NewSnapshot(cfg.Tools))
	metrics := observability.New()
	e.SetScannerHooks(reg, policy, metrics, mode)
	return e, metrics
}

// noopPreflight always succeeds. Used so tests do not depend on a real
// nuclei binary being installed.
type noopPreflight struct{}

func (noopPreflight) Name() string                                               { return "stub" }
func (noopPreflight) Run(_ context.Context, _ preflight.Context) failure.Result   { return failure.Result{} }

// bypassPreflight replaces the preflight dispatcher with a no-op so tests
// past the validation/authorization layer do not need nuclei on PATH.
func bypassPreflight(e *Executor) {
	e.hooksMu.Lock()
	defer e.hooksMu.Unlock()
	e.hooks.preflightReg = func(string) preflight.Preflight { return noopPreflight{} }
}

// Test 13: agent wants nuclei but args={} → STOP_FOR_INPUT, no retry storm.
//
// We invoke ExecuteTool 20 times with empty args and assert that:
//
//	- STOP_FOR_INPUT envelopes returned: 20
//	- tool_execution_total stays 0 (no exec started)
func TestRetryStormRegressionAgentEmptyArgs(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "example.com"},
	}})
	e, metrics := makeExecutor(t, policy, ExecutionModeAgent)
	bypassPreflight(e)

	const attempts = 20
	stopForInput := 0
	for i := 0; i < attempts; i++ {
		res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{})
		if err != nil {
			t.Fatalf("attempt %d: unexpected error: %v", i, err)
		}
		if res == nil || len(res.Content) == 0 {
			t.Fatalf("attempt %d: empty result", i)
		}
		text := res.Content[0].Text
		if strings.Contains(text, `"code":"MISSING_REQUIRED_ARGUMENT"`) {
			stopForInput++
		}
	}
	if stopForInput != attempts {
		t.Fatalf("expected %d STOP_FOR_INPUT envelopes, got %d", attempts, stopForInput)
	}
	if got := metrics.Count(observability.CounterToolStopForInputTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != int64(attempts) {
		t.Fatalf("stop_for_input metric: want %d, got %d", attempts, got)
	}
	if got := metrics.Count(observability.CounterToolExecutionTotal, "nuclei", ""); got != 0 {
		t.Fatalf("execution metric must stay 0, got %d", got)
	}
}

// Test 13b: once the user supplies a target, the next invocation passes
// validation/authorization. Exec may fail (no nuclei binary) but the
// failure must NOT be a STOP_FOR_INPUT.
func TestRetryStormRegressionUserProvidesTarget(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "example.com"},
	}})
	e, metrics := makeExecutor(t, policy, ExecutionModeAgent)
	bypassPreflight(e)

	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target": "https://example.com",
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if res != nil && len(res.Content) > 0 {
		text := res.Content[0].Text
		if strings.Contains(text, "MISSING_REQUIRED_ARGUMENT") {
			t.Fatalf("validation should have passed: %s", text)
		}
	}
	if got := metrics.Count(observability.CounterToolStopForInputTotal, "nuclei", string(failure.CodeMissingRequiredArgument)); got != 0 {
		t.Fatalf("after providing target, stop_for_input should be 0, got %d", got)
	}
}

// Test 12: agent additional_args rejected with POLICY_DENIED.
func TestAgentAdditionalArgsRejected(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "example.com"},
	}})
	e, _ := makeExecutor(t, policy, ExecutionModeAgent)
	bypassPreflight(e)

	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target":          "https://example.com",
		"additional_args": "-stats",
	})
	if err != nil {
		t.Fatalf("unexpected: %v", err)
	}
	if !strings.Contains(res.Content[0].Text, `"code":"POLICY_DENIED"`) {
		t.Fatalf("expected POLICY_DENIED, got %s", res.Content[0].Text)
	}
}

// Test 13c: manual additional_args remains compatible (legacy behavior).
func TestManualAdditionalArgsCompatible(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "example.com"},
	}})
	e, _ := makeExecutor(t, policy, ExecutionModeManual)
	bypassPreflight(e)

	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target":          "https://example.com",
		"additional_args": "-stats",
	})
	if err != nil {
		t.Fatalf("unexpected: %v", err)
	}
	if res != nil && len(res.Content) > 0 {
		text := res.Content[0].Text
		if strings.Contains(text, "POLICY_DENIED") {
			t.Fatalf("manual mode must allow additional_args, got %s", text)
		}
	}
}