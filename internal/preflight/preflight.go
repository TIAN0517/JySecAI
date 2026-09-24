// Package preflight defines the generic ToolPreflight interface and the
// first concrete implementation for nuclei. Preflight runs after schema
// validation and target authorization but BEFORE exec.CommandContext, so a
// preflight failure never starts a process.
//
// Preflight failures are non-retryable and never require user input from the
// "missing argument" sense — the Agent loop should surface them as
// infrastructure problems to the operator rather than re-invoking the tool.
package preflight

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"jysecai/internal/failure"
)

// Preflight is the per-tool preflight interface. Implementations must be
// pure: they only read from the tool config, the OS filesystem, and the
// already-normalized target. They MUST NOT start the underlying tool
// process; the version probe is the only execution, and it is bounded.
type Preflight interface {
	// Name is the tool name this preflight applies to (e.g. "nuclei").
	Name() string
	// Run checks the prerequisites for executing the tool with the given
	// normalized target and additional args. It returns a failure.Result
	// whose Code is one of the well-known preflight codes; an empty Result
	// indicates success.
	Run(ctx context.Context, pctx Context) failure.Result
}

// Context carries the inputs a Preflight needs. We keep this deliberately
// small: a Preflight that wants the original tool config can fetch it via
// the toolschema.Registry.
type Context struct {
	// ToolConfig is the resolved ToolConfig for the tool being executed.
	ToolConfig ToolConfigRef
	// Target is the already-normalized target. May be nil for tools that
	// don't operate on a target (e.g. health checks).
	Target *NormalizedTargetRef
	// Args is the validated argument map (post schema validation).
	Args map[string]interface{}
	// AuthAllowed is the outcome of the upstream authorization check; a
	// Preflight may inspect it but MUST NOT re-run authorization itself.
	AuthAllowed bool
}

// ToolConfigRef is a tiny structural copy of config.ToolConfig so this
// package does not need to import the heavy config package. The fields
// here are exactly the ones Preflight implementations consume.
type ToolConfigRef struct {
	Name    string
	Command string
}

// NormalizedTargetRef mirrors tooltarget.Normalized without importing it; the
// pointer fields are kept narrow to avoid cycles.
type NormalizedTargetRef struct {
	Host string
	IP   string
	Kind string
}

// New builds the preflight chain for the given tool. The dispatcher keeps
// the wiring in one place so future tools can be added without touching the
// Executor. If no concrete preflight is registered for a tool, the dispatcher
// returns a no-op that always succeeds.
func New(toolName string) Preflight {
	switch toolName {
	case "nuclei":
		return &Nuclei{}
	}
	return noopPreflight{tool: toolName}
}

type noopPreflight struct{ tool string }

func (n noopPreflight) Name() string { return n.tool }
func (n noopPreflight) Run(_ context.Context, _ Context) failure.Result {
	return failure.Result{}
}

// Nuclei implements Preflight for the nuclei binary.
//
// The checks are intentionally minimal: we do not require a fixed
// /root/nuclei-templates directory (YAML schema does not mandate it), and we
// only validate template paths when the caller supplied one.
type Nuclei struct {
	// LookPath is overridable for tests. Production code leaves it nil and
	// relies on exec.LookPath.
	LookPath func(string) (string, error)
	// RunProbe is overridable for tests; production uses a real
	// exec.CommandContext with a short timeout.
	RunProbe func(ctx context.Context, bin string) error
}

// Name implements Preflight.
func (n *Nuclei) Name() string { return "nuclei" }

// Run implements Preflight. The order of checks is:
//
//	1. binary on PATH (or in the configured Command path)
//	2. binary executable
//	3. version probe responds
//	4. target syntax (delegated to upstream normalization; here we just
//	   confirm the target was supplied when schema requires it)
//	5. template path (only if the caller supplied one)
//
// Any failure here is non-retryable.
func (n *Nuclei) Run(ctx context.Context, pctx Context) failure.Result {
	look := n.LookPath
	if look == nil {
		look = exec.LookPath
	}
	bin := strings.TrimSpace(pctx.ToolConfig.Command)
	if bin == "" {
		return failure.New(failure.CodeBinaryUnavailable, "nuclei",
			"nuclei ToolConfig.Command is empty")
	}
	resolved, err := look(bin)
	if err != nil {
		return failure.New(failure.CodeBinaryUnavailable, "nuclei",
			fmt.Sprintf("nuclei binary %q not on PATH", bin))
	}
	info, statErr := os.Stat(resolved)
	if statErr != nil {
		return failure.New(failure.CodeBinaryUnavailable, "nuclei",
			fmt.Sprintf("nuclei binary %q not accessible: %v", resolved, statErr))
	}
	if info.IsDir() || info.Mode()&0o111 == 0 {
		return failure.New(failure.CodeBinaryUnavailable, "nuclei",
			fmt.Sprintf("nuclei binary %q is not executable", resolved))
	}
	probe := n.RunProbe
	if probe == nil {
		probe = func(ctx context.Context, b string) error {
			cctx, cancel := context.WithTimeout(ctx, versionProbeTimeout)
			defer cancel()
			cmd := exec.CommandContext(cctx, b, "-version")
			cmd.Stdout = nil
			cmd.Stderr = nil
			return cmd.Run()
		}
	}
	if err := probe(ctx, resolved); err != nil {
		return failure.New(failure.CodeBinaryUnavailable, "nuclei",
			fmt.Sprintf("nuclei version probe failed: %v", err))
	}
	if pctx.Target == nil || pctx.Target.Host == "" {
		return failure.New(failure.CodeInvalidTarget, "nuclei",
			"normalized target is empty")
	}
	if tpl, ok := pctx.Args["template"].(string); ok && strings.TrimSpace(tpl) != "" {
		clean := filepath.Clean(tpl)
		if _, err := os.Stat(clean); err != nil {
			return failure.New(failure.CodeTemplateUnavailable, "nuclei",
				fmt.Sprintf("template %q not readable: %v", clean, err))
		}
	}
	return failure.Result{}
}

// versionProbeTimeout bounds the version-probe subprocess. The value is
// deliberately small: nuclei -version should return in well under a second on
// any sane system, and a longer hang here would block the whole preflight.
const versionProbeTimeout = 5 * 1_000_000_000 // 5s in nanoseconds
