package multiagent

import (
	"encoding/json"
	"strings"
)

// stopForInputEnvelope mirrors the wire shape emitted by
// internal/security.scannerErrorEnvelope. We keep a local copy here
// instead of importing internal/security directly to avoid a circular
// package dependency. Any field-name drift between the two MUST be
// kept in sync.
//
// Wire shape:
//
//	{
//	  "code": "MISSING_REQUIRED_ARGUMENT",
//	  "tool": "nuclei",
//	  "requires_user_input": true,
//	  ...
//	}
type stopForInputEnvelope struct {
	Code              string   `json:"code"`
	Tool              string   `json:"tool"`
	RequiresUserInput bool     `json:"requires_user_input"`
	Message           string   `json:"message"`
	MissingFields     []string `json:"missing_fields"`
}

// einoToolResultRequiresUserInput reports whether a tool result body
// is a STOP_FOR_INPUT envelope that the orchestration MUST surface to
// the user (and NOT silently feed back to the model for re-invocation).
//
// The Scanner Runtime Optimization v2 pre-exec pipeline emits this
// envelope when validation fails with a code whose semantics are
// "needs user input" (MISSING_REQUIRED_ARGUMENT, INVALID_ARGUMENT
// without auto-fill). Without this signal, the model loop would treat
// the envelope as a normal tool result and re-issue the same call
// indefinitely.
//
// The helper is intentionally conservative: it requires both the
// requires_user_input=true marker AND the MISSING_REQUIRED_ARGUMENT
// (or INVALID_ARGUMENT) code to avoid false positives from any other
// tool that happens to emit JSON.
func einoToolResultRequiresUserInput(body string) bool {
	body = strings.TrimSpace(body)
	if body == "" {
		return false
	}
	if !strings.HasPrefix(body, "{") {
		return false
	}
	var env stopForInputEnvelope
	if err := json.Unmarshal([]byte(body), &env); err != nil {
		return false
	}
	if !env.RequiresUserInput {
		return false
	}
	if env.Tool == "" {
		// No tool name => not a STOP_FOR_INPUT envelope we trust.
		// Bare {"code":"MISSING_REQUIRED_ARGUMENT","requires_user_input":true}
		// from non-scanner sources would otherwise false-positive here.
		return false
	}
	switch env.Code {
	case "MISSING_REQUIRED_ARGUMENT", "INVALID_ARGUMENT":
		return true
	}
	return false
}

// einoToolResultEnvelopeTool returns the tool name from a STOP_FOR_INPUT
// envelope, or "" if the body is not such an envelope. Useful for
// logging/audit so the operator knows which tool surfaced the request.
func einoToolResultEnvelopeTool(body string) string {
	body = strings.TrimSpace(body)
	if body == "" || !strings.HasPrefix(body, "{") {
		return ""
	}
	var env stopForInputEnvelope
	if err := json.Unmarshal([]byte(body), &env); err != nil {
		return ""
	}
	if !env.RequiresUserInput {
		return ""
	}
	return env.Tool
}
