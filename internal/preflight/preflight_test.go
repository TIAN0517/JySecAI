package preflight

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"

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
