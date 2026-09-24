// Package failure defines the closed enumeration of scanner/tool failure
// codes that the rest of the runtime emits. Keeping the codes centralized
// prevents accidental string drift between validation, preflight, and the
// Agent loop.
//
// Every code carries a retryable flag and a requires_user_input flag so that
// downstream consumers (the Agent loop, observability counters) can branch
// on the typed values instead of pattern-matching error messages.
package failure

import "strings"

// Code is the closed set of failure codes emitted anywhere a tool call can
// fail in a typed way. Add new codes here; never construct them ad-hoc.
type Code string

const (
	// CodeMissingRequiredArgument means the tool was invoked without one or
	// more required arguments. Always requires_user_input; never retryable
	// from inside the same logical invocation.
	CodeMissingRequiredArgument Code = "MISSING_REQUIRED_ARGUMENT"
	// CodeInvalidArgument means the caller supplied a key not declared in
	// the tool's schema. Retryable only after the caller fixes the arg map.
	CodeInvalidArgument Code = "INVALID_ARGUMENT"
	// CodeTargetNotAuthorized means the requested target was rejected by the
	// AuthorizedTargetPolicy. Never retryable; never user-input-driven in the
	// "missing argument" sense.
	CodeTargetNotAuthorized Code = "TARGET_NOT_AUTHORIZED"
	// CodePolicyDenied means the execution mode (e.g. Agent) rejected the
	// request for a policy reason (additional_args in agent mode, etc.).
	CodePolicyDenied Code = "POLICY_DENIED"
	// CodeToolNotFound means the tool name is unknown to the schema registry.
	CodeToolNotFound Code = "TOOL_NOT_FOUND"
	// CodeToolAmbiguous means the tool_search regex matched more than one
	// tool. The Agent loop should ask the model to disambiguate.
	CodeToolAmbiguous Code = "TOOL_AMBIGUOUS"
	// CodeBinaryUnavailable means the tool's underlying CLI binary is not on
	// PATH (or not executable). Never retryable without operator intervention.
	CodeBinaryUnavailable Code = "BINARY_UNAVAILABLE"
	// CodeTemplateUnavailable means a user-supplied nuclei template path
	// could not be read. Only emitted when the caller supplied template.
	CodeTemplateUnavailable Code = "TEMPLATE_UNAVAILABLE"
	// CodeInvalidTarget means the target string failed syntactic validation
	// (empty host, userinfo URL, control characters).
	CodeInvalidTarget Code = "INVALID_TARGET"
	// CodeTimeout means the underlying exec exceeded the hard timeout.
	CodeTimeout Code = "TIMEOUT"
	// CodeNonzeroExit means the tool exited with a non-zero code outside its
	// allowed_exit_codes list.
	CodeNonzeroExit Code = "NONZERO_EXIT"
	// CodeParserFailure means the tool produced output the parser could not
	// interpret.
	CodeParserFailure Code = "PARSER_FAILURE"
	// CodeResourceLimit means the call was rejected before exec because it
	// would exceed a configured bound (concurrency, output size, etc.).
	CodeResourceLimit Code = "RESOURCE_LIMIT"
	// CodeUnknown is the catch-all for failures that did not match any
	// specific code. Treated as not retryable by default.
	CodeUnknown Code = "UNKNOWN"
)

// AllCodes returns the closed set in stable order. Useful for tests and for
// generating coverage tables in observability.
func AllCodes() []Code {
	return []Code{
		CodeMissingRequiredArgument,
		CodeInvalidArgument,
		CodeTargetNotAuthorized,
		CodePolicyDenied,
		CodeToolNotFound,
		CodeToolAmbiguous,
		CodeBinaryUnavailable,
		CodeTemplateUnavailable,
		CodeInvalidTarget,
		CodeTimeout,
		CodeNonzeroExit,
		CodeParserFailure,
		CodeResourceLimit,
		CodeUnknown,
	}
}

// Result is the canonical structured failure envelope. Tool callers may
// surface this directly; observability counters MUST key on (Code, Tool).
type Result struct {
	Code              Code   `json:"code"`
	Tool              string `json:"tool"`
	Retryable         bool   `json:"retryable"`
	RequiresUserInput bool   `json:"requires_user_input"`
	Message           string `json:"message,omitempty"`
	// MissingFields is non-empty only for MISSING_REQUIRED_ARGUMENT.
	MissingFields []string `json:"missing_fields,omitempty"`
	// SchemaHash is non-empty when the result is anchored to a known schema.
	SchemaHash string `json:"schema_hash,omitempty"`
}

// New constructs a Result for the given code with the supplied message.
// The retryable and requires_user_input flags are filled from the code's
// canonical defaults so callers don't have to remember the matrix.
func New(code Code, tool, message string) Result {
	return Result{
		Code:              code,
		Tool:              tool,
		Message:           message,
		Retryable:         DefaultRetryable(code),
		RequiresUserInput: DefaultRequiresUserInput(code),
	}
}

// DefaultRetryable returns whether the given code is in principle retryable
// (i.e. the underlying failure is transient). Defaults to false for
// pre-execution failures; callers may override on a per-instance basis.
func DefaultRetryable(code Code) bool {
	switch code {
	case CodeTimeout, CodeResourceLimit:
		return true
	}
	return false
}

// DefaultRequiresUserInput returns whether the given code requires human
// intervention before the same logical invocation can be retried.
func DefaultRequiresUserInput(code Code) bool {
	switch code {
	case CodeMissingRequiredArgument:
		return true
	}
	return false
}

// String renders the code; mainly for log messages.
func (c Code) String() string { return string(c) }

// Normalize maps arbitrary upstream error strings onto a known Code. The
// mapping is intentionally narrow: if we cannot pin the failure to a typed
// code we return CodeUnknown rather than guessing. The Agent loop and the
// observability counters rely on this never silently upgrading to a more
// specific code.
func Normalize(toolName, msg string) Result {
	low := strings.ToLower(strings.TrimSpace(msg))
	code := CodeUnknown
	switch {
	case strings.Contains(low, "missing required") || strings.Contains(low, "缺少必需"):
		code = CodeMissingRequiredArgument
	case strings.Contains(low, "unknown argument") || strings.Contains(low, "unknown field"):
		code = CodeInvalidArgument
	case strings.Contains(low, "not authorized") || strings.Contains(low, "未授权"):
		code = CodeTargetNotAuthorized
	case strings.Contains(low, "policy denied") || strings.Contains(low, "additional_args"):
		code = CodePolicyDenied
	case strings.Contains(low, "not found") || strings.Contains(low, "未找到"):
		code = CodeToolNotFound
	case strings.Contains(low, "ambiguous"):
		code = CodeToolAmbiguous
	case strings.Contains(low, "binary") || strings.Contains(low, "executable"):
		code = CodeBinaryUnavailable
	case strings.Contains(low, "template"):
		code = CodeTemplateUnavailable
	case strings.Contains(low, "invalid target") || strings.Contains(low, "userinfo"):
		code = CodeInvalidTarget
	case strings.Contains(low, "timeout") || strings.Contains(low, "deadline"):
		code = CodeTimeout
	case strings.Contains(low, "non-zero exit") || strings.Contains(low, "exit code"):
		code = CodeNonzeroExit
	case strings.Contains(low, "parse"):
		code = CodeParserFailure
	}
	return New(code, toolName, msg)
}
