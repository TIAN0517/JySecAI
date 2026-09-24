package security

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"go.uber.org/zap"
	"jysecai/internal/config"
	"jysecai/internal/observability"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"
)

// TestExecutionTargetPreservation asserts that the argv passed to nuclei
// contains the FULL canonical target (scheme + host + port + path +
// query), not just the host. The test uses a fake nuclei binary that
// writes its argv to a file under TempDir; we then read the file and
// assert the exact "-u <value>" pair and the full argv shape.
func TestExecutionTargetPreservation(t *testing.T) {
	cases := []struct {
		name             string
		input            string
		authorizedHost   string
		wantArgvContains string
		wantTargetIndex  int // argv index where the canonical target appears
	}{
		{
			name:             "URL with port path and query",
			input:            "http://127.0.0.1:18080/path?q=1",
			authorizedHost:   "127.0.0.1",
			wantArgvContains: "http://127.0.0.1:18080/path?q=1",
			wantTargetIndex:  1,
		},
		{
			name:             "HTTPS URL with explicit port and path",
			input:            "https://example.com:8443/a",
			authorizedHost:   "example.com",
			wantArgvContains: "https://example.com:8443/a",
			wantTargetIndex:  1,
		},
		{
			name:             "Bare IPv4 literal",
			input:            "192.0.2.10",
			authorizedHost:   "192.0.2.10",
			wantArgvContains: "192.0.2.10",
			wantTargetIndex:  1,
		},
		{
			name:             "Bare hostname",
			input:            "example.com",
			authorizedHost:   "example.com",
			wantArgvContains: "example.com",
			wantTargetIndex:  1,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			policy := tooltarget.NewConfigAuthorizedTargetPolicy()
			policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
				{Tool: "nuclei", Host: tc.authorizedHost},
			}})

			binDir := t.TempDir()
			fakeBin := filepath.Join(binDir, "nuclei")
			argvDump := filepath.Join(binDir, "argv.txt")
			// Print argv one element per line, separated by NUL. The
			// leading NUL lets us read the file back as-is and split.
			script := "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"" + argvDump + "\"\nexit 0\n"
			if err := os.WriteFile(fakeBin, []byte(script), 0o755); err != nil {
				t.Fatalf("write fake nuclei: %v", err)
			}

			cfg := &config.SecurityConfig{
				Tools: []config.ToolConfig{
					{
						Name: "nuclei", Command: fakeBin, Enabled: true,
						Parameters: []config.ParameterConfig{
							{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
						},
					},
				},
			}

			e := NewExecutor(cfg, nil, zap.NewNop())
			registry := toolschema.NewRegistry()
			registry.Set(toolschema.NewSnapshot(cfg.Tools))
			metrics := observability.New()
			e.SetScannerHooks(registry, policy, metrics, ExecutionModeAgent)

			res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
				"target": tc.input,
			})
			if err != nil {
				t.Fatalf("execute: %v", err)
			}
			if res == nil || len(res.Content) == 0 {
				t.Fatalf("empty result")
			}
			body, err := os.ReadFile(argvDump)
			if err != nil {
				t.Fatalf("argv dump not created (did the binary run?): %v", err)
			}
			argv := strings.Split(strings.TrimRight(string(body), "\n"), "\n")
			if len(argv) < 2 {
				t.Fatalf("argv too short: %v", argv)
			}
			if argv[0] != "-u" {
				t.Fatalf("argv[0]: want \"-u\", got %q (full argv=%v)", argv[0], argv)
			}
			if argv[tc.wantTargetIndex] != tc.wantArgvContains {
				t.Fatalf("argv[%d]: want %q, got %q (full argv=%v)",
					tc.wantTargetIndex, tc.wantArgvContains, argv[tc.wantTargetIndex], argv)
			}
			// Defense in depth: if input was a full URL, the argv must
			// contain the scheme. This catches accidental host-only
			// truncation at the executor level.
			if strings.HasPrefix(tc.input, "http://") || strings.HasPrefix(tc.input, "https://") {
				all := strings.Join(argv, " ")
				if !strings.Contains(all, "://") {
					t.Fatalf("argv lost scheme: %v", argv)
				}
			}
			if got := metrics.Count(observability.CounterToolExecutionTotal, "nuclei", ""); got != 1 {
				t.Fatalf("execution count: want 1, got %d", got)
			}
		})
	}
}

// TestExecutionTargetPreservation_LowercasedScheme verifies the
// canonical form lower-cases the scheme but preserves the rest verbatim.
func TestExecutionTargetPreservation_LowercasedScheme(t *testing.T) {
	policy := tooltarget.NewConfigAuthorizedTargetPolicy()
	policy.Replace(tooltarget.Config{Entries: []tooltarget.Entry{
		{Tool: "nuclei", Host: "example.com"},
	}})

	binDir := t.TempDir()
	fakeBin := filepath.Join(binDir, "nuclei")
	argvDump := filepath.Join(binDir, "argv.txt")
	script := "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"" + argvDump + "\"\nexit 0\n"
	if err := os.WriteFile(fakeBin, []byte(script), 0o755); err != nil {
		t.Fatalf("write fake: %v", err)
	}

	cfg := &config.SecurityConfig{
		Tools: []config.ToolConfig{{
			Name: "nuclei", Command: fakeBin, Enabled: true,
			Parameters: []config.ParameterConfig{
				{Name: "target", Type: "string", Required: true, Flag: "-u", Format: "flag"},
			},
		}},
	}

	e := NewExecutor(cfg, nil, zap.NewNop())
	registry := toolschema.NewRegistry()
	registry.Set(toolschema.NewSnapshot(cfg.Tools))
	metrics := observability.New()
	e.SetScannerHooks(registry, policy, metrics, ExecutionModeAgent)

	res, err := e.ExecuteTool(context.Background(), "nuclei", map[string]interface{}{
		"target": "HTTPS://Example.COM:8443/A/B?x=1",
	})
	if err != nil {
		t.Fatalf("execute: %v", err)
	}
	if res == nil || len(res.Content) == 0 {
		t.Fatalf("empty result")
	}
	body, err := os.ReadFile(argvDump)
	if err != nil {
		t.Fatalf("argv dump not created: %v", err)
	}
	argv := strings.Split(strings.TrimRight(string(body), "\n"), "\n")
	want := "https://example.com:8443/A/B?x=1"
	if len(argv) < 2 || argv[0] != "-u" || argv[1] != want {
		t.Fatalf("argv mismatch: want [-u %q], got %v", want, argv)
	}
}
