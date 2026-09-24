// Package toolargs provides deterministic argument validation and the
// STOP_FOR_INPUT contract used by the Agent loop.
//
// ValidateToolArgs is the single entry point that turns a raw arg map into a
// typed ValidationResult. The Executor MUST consult this before invoking
// buildCommandArgs: validation failure short-circuits the entire pipeline
// (no normalization, no authorization, no preflight, no exec).
package toolargs

import (
	"fmt"
	"sort"
	"strings"

	"jysecai/internal/failure"
	"jysecai/internal/toolschema"
)

// ValidationStatus enumerates the two outcomes of argument validation.
// Keeping this closed means the Agent loop can switch on the type without
// string-matching error messages.
type ValidationStatus string

const (
	// StatusValid means every required argument is present and every supplied
	// argument is declared in the tool's schema.
	StatusValid ValidationStatus = "VALID"
	// StatusArgumentValidationFailed means one or more arguments are missing
	// or unknown. The Result carries the details; the Executor returns a
	// STOP_FOR_INPUT envelope upstream.
	StatusArgumentValidationFailed ValidationStatus = "ARGUMENT_VALIDATION_FAILED"
)

// ValidationResult is the typed output of ValidateToolArgs.
//
// It is JSON-marshalable so that callers can surface it directly to the
// model without re-wrapping.
type ValidationResult struct {
	Status        ValidationStatus `json:"status"`
	Code          string           `json:"code,omitempty"`
	Tool          string           `json:"tool"`
	MissingFields []string         `json:"missing_fields,omitempty"`
	InvalidFields []string         `json:"invalid_fields,omitempty"`
	SchemaHash    string           `json:"schema_hash,omitempty"`
	Retryable     bool             `json:"retryable"`
	Message       string           `json:"message,omitempty"`
}

// RequiresUserInput reports whether validation failed in a way that the agent
// MUST surface to a human before retrying. Missing required arguments always
// qualify; unknown arguments may or may not, depending on policy.
func (r ValidationResult) RequiresUserInput() bool {
	if r.Status != StatusArgumentValidationFailed {
		return false
	}
	switch r.Code {
	case failure.CodeMissingRequiredArgument:
		return true
	case failure.CodeInvalidArgument:
		// Unknown argument without a known default: still needs user input.
		return len(r.MissingFields) > 0
	}
	return false
}

// ValidateToolArgs is the canonical argument validator.
//
// The registry parameter is the read-only facade; callers MUST NOT pass a nil
// registry. Missing tools are reported as TOOL_NOT_FOUND so the agent loop
// can distinguish "schema missing" from "argument wrong".
func ValidateToolArgs(registry *toolschema.Registry, toolName string, args map[string]interface{}) ValidationResult {
	if registry == nil {
		return ValidationResult{
			Status:    StatusArgumentValidationFailed,
			Code:      failure.CodeToolNotFound,
			Tool:      toolName,
			Retryable: false,
			Message:   "schema registry not initialized",
		}
	}
	snap := registry.Get()
	if snap == nil || !snap.Has(toolName) {
		return ValidationResult{
			Status:    StatusArgumentValidationFailed,
			Code:      failure.CodeToolNotFound,
			Tool:      toolName,
			Retryable: false,
			Message:   fmt.Sprintf("tool %q not found in schema registry", toolName),
		}
	}
	required := snap.RequiredFields(toolName)
	optional := snap.OptionalFields(toolName)
	declared := make(map[string]struct{}, len(required)+len(optional))
	for _, f := range required {
		declared[f] = struct{}{}
	}
	for _, f := range optional {
		declared[f] = struct{}{}
	}
	// additional_args is a reserved convention carried over from existing
	// YAML schemas; treat it as a known field so callers can still pass it
	// through to the executor.
	declared["additional_args"] = struct{}{}

	missing := make([]string, 0)
	for _, f := range required {
		if !hasArg(args, f) {
			missing = append(missing, f)
		}
	}
	sort.Strings(missing)

	invalid := make([]string, 0)
	for k := range args {
		if _, ok := declared[k]; ok {
			continue
		}
		// Allow empty-string placeholders; only the key shape is rejected.
		invalid = append(invalid, k)
	}
	sort.Strings(invalid)

	if len(missing) == 0 && len(invalid) == 0 {
		return ValidationResult{
			Status:     StatusValid,
			Tool:       toolName,
			SchemaHash: snap.SchemaHash(toolName),
		}
	}
	res := ValidationResult{
		Status:        StatusArgumentValidationFailed,
		Tool:          toolName,
		MissingFields: missing,
		InvalidFields: invalid,
		SchemaHash:    snap.SchemaHash(toolName),
		Retryable:     false,
	}
	switch {
	case len(missing) > 0:
		res.Code = failure.CodeMissingRequiredArgument
		res.Message = fmt.Sprintf("%s requires: %s", toolName, strings.Join(missing, ", "))
	default:
		res.Code = failure.CodeInvalidArgument
		res.Message = fmt.Sprintf("%s received unknown arguments: %s", toolName, strings.Join(invalid, ", "))
	}
	return res
}

// hasArg reports whether the supplied map contains a non-empty value for the
// given key. nil, empty string, and empty slices all count as "missing".
func hasArg(args map[string]interface{}, key string) bool {
	if args == nil {
		return false
	}
	v, ok := args[key]
	if !ok || v == nil {
		return false
	}
	if s, isStr := v.(string); isStr && strings.TrimSpace(s) == "" {
		return false
	}
	if sl, isSlice := v.([]interface{}); isSlice && len(sl) == 0 {
		return false
	}
	return true
}

// StopForInputResult is the envelope returned to the Agent loop when
// validation cannot recover without human input. It is deliberately
// distinguishable from ValidationResult so that the Agent loop can route it
// to the human channel rather than treating it as a transient tool failure.
type StopForInputResult struct {
	Code             string   `json:"code"`
	Tool             string   `json:"tool"`
	MissingFields    []string `json:"missing_fields"`
	HumanMessage     string   `json:"human_message"`
	SchemaHash       string   `json:"schema_hash,omitempty"`
	Retryable        bool     `json:"retryable"`
	RequiresUserInput bool    `json:"requires_user_input"`
}

// BuildStopForInput turns a failed ValidationResult into the Agent loop
// STOP_FOR_INPUT envelope. Caller MUST only invoke this when the underlying
// validation actually failed (Status == ARGUMENT_VALIDATION_FAILED) and the
// failure requires user input.
func BuildStopForInput(v ValidationResult) StopForInputResult {
	human := v.Message
	if v.Code == failure.CodeMissingRequiredArgument && len(v.MissingFields) > 0 {
		human = fmt.Sprintf("%s requires %s", v.Tool, humanFieldList(v.MissingFields))
	}
	return StopForInputResult{
		Code:              v.Code,
		Tool:              v.Tool,
		MissingFields:     v.MissingFields,
		HumanMessage:      human,
		SchemaHash:        v.SchemaHash,
		Retryable:         false,
		RequiresUserInput: true,
	}
}

// humanFieldList formats a list of argument names into a natural-language
// prompt ("target" / "target, severity") without leaking the internal
// snake_case verbatim. Stable across versions.
func humanFieldList(fields []string) string {
	switch len(fields) {
	case 0:
		return ""
	case 1:
		return fields[0]
	default:
		return strings.Join(fields[:len(fields)-1], ", ") + " and " + fields[len(fields)-1]
	}
}
