package security

import (
	"context"
	"fmt"
	"strings"

	"jysecai/internal/config"
	"jysecai/internal/failure"
	"jysecai/internal/observability"
	"jysecai/internal/preflight"
	"jysecai/internal/toolargs"
	"jysecai/internal/toolschema"
	"jysecai/internal/tooltarget"
)

// scannerHooks is the optional dependency bundle the Executor uses to run
// the new pre-exec pipeline (PHASE 1-8 of Scanner Runtime Optimization v2).
// All fields are read-only after construction; replace via SetScannerHooks.
type scannerHooks struct {
	registry      *toolschema.Registry
	targetPolicy  tooltarget.Policy
	preflightReg  func(string) preflight.Preflight
	metrics       *observability.Registry
	executionMode ExecutionMode
}

// ExecutionMode is the runtime mode used to gate additional_args policy.
type ExecutionMode string

const (
	// ExecutionModeManual preserves the existing YAML behavior for human /
	// API callers.
	ExecutionModeManual ExecutionMode = "manual"
	// ExecutionModeAgent is the unattended Agent loop; additional_args
	// must be empty.
	ExecutionModeAgent ExecutionMode = "agent"
)

// SetScannerHooks wires the optional pre-exec pipeline into the Executor.
// Any nil field disables the corresponding hook (legacy behavior).
func (e *Executor) SetScannerHooks(registry *toolschema.Registry, policy tooltarget.Policy, metrics *observability.Registry, mode ExecutionMode) {
	e.hooksMu.Lock()
	defer e.hooksMu.Unlock()
	if e.hooks == nil {
		e.hooks = &scannerHooks{}
	}
	e.hooks.registry = registry
	e.hooks.targetPolicy = policy
	e.hooks.metrics = metrics
	e.hooks.executionMode = mode
	e.hooks.preflightReg = preflight.New
}

// scannerPreExecResult is the typed outcome of the pre-exec pipeline.
// Exactly one of (StopForInput, Failure) is non-nil; both nil means "proceed".
type scannerPreExecResult struct {
	StopForInput *toolargs.StopForInputResult
	Failure      *failure.Result
	ToolResult   *scannerErrorEnvelope
}

// scannerErrorEnvelope is the wire shape returned to the Agent loop on a
// pre-exec rejection. The Agent loop distinguishes STOP_FOR_INPUT (which
// must be surfaced to the user) from other failures (which must be retried
// according to the failure taxonomy).
type scannerErrorEnvelope struct {
	Code              string   `json:"code"`
	Tool              string   `json:"tool"`
	Message           string   `json:"message"`
	Retryable         bool     `json:"retryable"`
	RequiresUserInput bool     `json:"requires_user_input"`
	MissingFields     []string `json:"missing_fields,omitempty"`
	SchemaHash        string   `json:"schema_hash,omitempty"`
}

// runScannerPreExec implements the mandatory pre-exec order:
//
//	1. schema validate      (toolargs.ValidateToolArgs)
//	2. target normalize     (tooltarget.Normalize, when the tool has a target)
//	3. authorization        (tooltarget.Policy.Check, when normalize succeeded)
//	4. execution policy     (additional_args gating, etc.)
//	5. preflight            (tool-specific binary / template checks)
//
// Any failure short-circuits the chain. The function never starts the tool
// process. The caller MUST treat a non-nil StopForInput as terminal for the
// current logical invocation.
func (e *Executor) runScannerPreExec(ctx context.Context, toolName string, toolConfig *config.ToolConfig, args map[string]interface{}) scannerPreExecResult {
	e.hooksMu.Lock()
	hooks := e.hooks
	e.hooksMu.Unlock()
	if hooks == nil || hooks.registry == nil {
		// Legacy behavior: hooks not configured means the surrounding system
		// has not opted into the new pipeline. Proceed.
		return scannerPreExecResult{}
	}
	// Step 1: schema validate.
	vres := toolargs.ValidateToolArgs(hooks.registry, toolName, args)
	if vres.Status == toolargs.StatusArgumentValidationFailed {
		if hooks.metrics != nil {
			hooks.metrics.IncValidation(toolName, failure.Code(vres.Code))
		}
		if vres.RequiresUserInput() {
			sfi := toolargs.BuildStopForInput(vres)
			if hooks.metrics != nil {
				hooks.metrics.IncStopForInput(toolName, failure.Code(vres.Code))
			}
			return scannerPreExecResult{StopForInput: &sfi}
		}
		fr := failure.New(failure.Code(vres.Code), toolName, vres.Message)
		fr.MissingFields = vres.MissingFields
		fr.SchemaHash = vres.SchemaHash
		return scannerPreExecResult{Failure: &fr}
	}

	// Step 2 + 3: target normalize then authorize. Only run if the tool
	// declares a target parameter.
	if _, hasTarget := args["target"]; hasTarget {
		raw, _ := args["target"].(string)
		norm, err := tooltarget.Normalize(raw)
		if err != nil {
			fr := failure.New(failure.CodeInvalidTarget, toolName, err.Error())
			if hooks.metrics != nil {
				hooks.metrics.IncValidation(toolName, failure.CodeInvalidTarget)
			}
			return scannerPreExecResult{Failure: &fr}
		}
		if hooks.targetPolicy != nil {
			dec := hooks.targetPolicy.Check(toolName, norm)
			if !dec.Allowed {
				fr := failure.New(dec.Code, toolName,
					fmt.Sprintf("target not authorized: %s", dec.Reason))
				fr.SchemaHash = vres.SchemaHash
				if hooks.metrics != nil {
					hooks.metrics.IncValidation(toolName, dec.Code)
				}
				return scannerPreExecResult{Failure: &fr}
			}
		}
		// Replace the raw target with the normalized form so downstream
		// code (preflight, exec argv) sees the canonical value.
		args["target"] = norm.Host
		if norm.IP != nil {
			args["target_ip"] = norm.IP.String()
		}
	}

	// Step 4: execution policy. additional_args is only legal in manual mode.
	if hooks.executionMode == ExecutionModeAgent {
		if v, ok := args["additional_args"]; ok {
			s := strings.TrimSpace(anyToString(v))
			if s != "" {
				fr := failure.New(failure.CodePolicyDenied, toolName,
					"additional_args not allowed in agent mode")
				if hooks.metrics != nil {
					hooks.metrics.IncPolicyDenied(toolName, failure.CodePolicyDenied)
				}
				return scannerPreExecResult{Failure: &fr}
			}
		}
	}

	// Step 5: preflight (only when we have the tool config in hand).
	if hooks.preflightReg != nil {
		tcRef := preflight.ToolConfigRef{Name: toolConfig.Name, Command: toolConfig.Command}
		pctx := preflight.Context{ToolConfig: tcRef, Args: args, AuthAllowed: true}
		if v, ok := args["target"].(string); ok {
			ref := preflight.NormalizedTargetRef{Host: v}
			pctx.Target = &ref
		}
		pf := hooks.preflightReg(toolName)
		if pf != nil {
			if res := pf.Run(ctx, pctx); res.Code != "" {
				if hooks.metrics != nil {
					hooks.metrics.IncPreflightFailure(toolName, res.Code)
				}
				return scannerPreExecResult{Failure: &res}
			}
		}
	}

	return scannerPreExecResult{}
}

// anyToString is a defensive helper for converting an arbitrary args value
// to a string. Used by the additional_args policy check.
func anyToString(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case []byte:
		return string(t)
	case []string:
		return strings.Join(t, " ")
	case []interface{}:
		parts := make([]string, 0, len(t))
		for _, x := range t {
			parts = append(parts, anyToString(x))
		}
		return strings.Join(parts, " ")
	}
	return fmt.Sprintf("%v", v)
}
