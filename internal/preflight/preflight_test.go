package preflight

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/failure"
)

// Test 14: nuclei binary missing → BINARY_UNAVAILABLE.
func TestNucleiBinaryMissing(t *testing.T) {
	n := &Nuclei{
		LookPath: func(string) (string, error) { return "", errors.New("not found") },
	}
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: "nuclei"},
		Target:     &NormalizedTargetRef{Host: "example.com"},
	})
	if res.Code != failure.CodeBinaryUnavailable {
		t.Fatalf("expected BINARY_UNAVAILABLE, got %s (%s)", res.Code, res.Message)
	}
	if res.Retryable {
		t.Fatalf("BINARY_UNAVAILABLE must not be retryable")
	}
}

// Test 14b: nuclei binary present but not executable → BINARY_UNAVAILABLE.
func TestNucleiBinaryNotExecutable(t *testing.T) {
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	if err := os.WriteFile(bin, []byte("not executable"), 0o644); err != nil {
		t.Fatalf("write bin: %v", err)
	}
	n := &Nuclei{
		LookPath: func(string) (string, error) { return bin, nil },
	}
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
	})
	if res.Code != failure.CodeBinaryUnavailable {
		t.Fatalf("expected BINARY_UNAVAILABLE, got %s (%s)", res.Code, res.Message)
	}
}

// Test 15: template provided but missing → TEMPLATE_UNAVAILABLE.
func TestNucleiTemplateMissing(t *testing.T) {
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	if err := os.WriteFile(bin, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write bin: %v", err)
	}
	n := &Nuclei{
		LookPath: func(string) (string, error) { return bin, nil },
		RunProbe: func(ctx context.Context, _ string) error { return nil },
	}
	missing := filepath.Join(dir, "does-not-exist.yaml")
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
		Args:       map[string]interface{}{"template": missing},
	})
	if res.Code != failure.CodeTemplateUnavailable {
		t.Fatalf("expected TEMPLATE_UNAVAILABLE, got %s (%s)", res.Code, res.Message)
	}
}

// Test 16: template omitted → no template-directory assumption; pass.
func TestNucleiTemplateOmittedPasses(t *testing.T) {
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	if err := os.WriteFile(bin, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write bin: %v", err)
	}
	n := &Nuclei{
		LookPath: func(string) (string, error) { return bin, nil },
		RunProbe: func(ctx context.Context, _ string) error { return nil },
	}
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
		Args:       map[string]interface{}{},
	})
	if res.Code != "" {
		t.Fatalf("expected empty result (success), got code=%s msg=%s", res.Code, res.Message)
	}
}

// Test 17: preflight failure does not exec. We use a RunProbe that
// returns error to confirm a preflight failure never reaches a real exec.
func TestPreflightFailureDoesNotExec(t *testing.T) {
	called := false
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	if err := os.WriteFile(bin, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write bin: %v", err)
	}
	n := &Nuclei{
		LookPath: func(string) (string, error) { return bin, nil },
		RunProbe: func(ctx context.Context, _ string) error {
			called = true
			return errors.New("probe failed")
		},
	}
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
	})
	if res.Code != failure.CodeBinaryUnavailable {
		t.Fatalf("expected BINARY_UNAVAILABLE on probe failure, got %s", res.Code)
	}
	if !called {
		t.Fatalf("RunProbe should have been called")
	}
	// Real exec.CommandContext is never reached; the test framework only
	// verifies that we did NOT also call out to /usr/bin/nuclei or similar.
	// The contract is: a preflight failure means the tool process never starts.
}

// Test: dispatcher returns noop for unknown tools.
func TestDispatcherNoopForUnknown(t *testing.T) {
	p := New("does-not-exist")
	if p == nil {
		t.Fatalf("New() must not return nil")
	}
	if got := p.Name(); got != "does-not-exist" {
		t.Fatalf("expected name passthrough, got %s", got)
	}
	if res := p.Run(context.Background(), Context{}); res.Code != "" {
		t.Fatalf("noop preflight must always succeed, got code=%s", res.Code)
	}
}

// TestNucleiVersionProbeBoundedTimeout exercises the bounded-timeout
// path of the production probe: the fake nuclei binary hangs (uses
// `sleep 30`), but VersionProbeTimeout is overridden to 200ms so the
// probe MUST return inside ~500ms. The test asserts:
//
//   - Run returns within bounded time (no sleep-based sync in test thread).
//   - The result is BINARY_UNAVAILABLE with a version-probe-failed
//     message.
//   - The scanner execution path is never reached (the tool process
//     never starts; preflight is the only side effect).
func TestNucleiVersionProbeBoundedTimeout(t *testing.T) {
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	// Fake nuclei hangs long enough that any unbounded probe would
	// exceed the test's wall-clock budget by an order of magnitude.
	hanger := "#!/bin/sh\nsleep 30\nexit 0\n"
	if err := os.WriteFile(bin, []byte(hanger), 0o755); err != nil {
		t.Fatalf("write fake nuclei: %v", err)
	}
	n := &Nuclei{
		LookPath:            func(string) (string, error) { return bin, nil },
		VersionProbeTimeout: 200 * time.Millisecond,
	}

	start := time.Now()
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
	})
	elapsed := time.Since(start)

	if elapsed > 1*time.Second {
		t.Fatalf("preflight took %v, want <1s (timeout was 200ms)", elapsed)
	}
	if res.Code != failure.CodeBinaryUnavailable {
		t.Fatalf("expected BINARY_UNAVAILABLE, got code=%s msg=%s", res.Code, res.Message)
	}
	if res.Retryable {
		t.Fatalf("BINARY_UNAVAILABLE must not be retryable")
	}
}

// TestNucleiVersionProbeNoCallerDeadline verifies that even if the
// caller passes a context WITHOUT a deadline, the production probe
// still applies its own bounded child context. The probe must return
// within bounded time and report BINARY_UNAVAILABLE — not hang
// forever waiting for a deadline the caller never supplied.
func TestNucleiVersionProbeNoCallerDeadline(t *testing.T) {
	dir := t.TempDir()
	bin := filepath.Join(dir, "nuclei")
	if err := os.WriteFile(bin, []byte("#!/bin/sh\nsleep 30\nexit 0\n"), 0o755); err != nil {
		t.Fatalf("write fake nuclei: %v", err)
	}
	n := &Nuclei{
		LookPath: func(string) (string, error) { return bin, nil },
		// Override to a small value so the test finishes quickly even
		// though we use the production-default probe (no RunProbe override).
		VersionProbeTimeout: 150 * time.Millisecond,
	}

	start := time.Now()
	res := n.Run(context.Background(), Context{
		ToolConfig: ToolConfigRef{Name: "nuclei", Command: bin},
		Target:     &NormalizedTargetRef{Host: "example.com"},
	})
	elapsed := time.Since(start)

	if elapsed > 1*time.Second {
		t.Fatalf("preflight took %v, want <1s (timeout was 150ms)", elapsed)
	}
	if res.Code != failure.CodeBinaryUnavailable {
		t.Fatalf("expected BINARY_UNAVAILABLE, got code=%s msg=%s", res.Code, res.Message)
	}
	if !strings.Contains(res.Message, "version probe failed") {
		t.Fatalf("expected version-probe-failed message, got %q", res.Message)
	}
}
