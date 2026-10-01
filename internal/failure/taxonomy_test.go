package failure

import "testing"

// Test 10: failure code set is closed and stable.
func TestAllCodesIsClosed(t *testing.T) {
	want := []Code{
		CodeMissingRequiredArgument, CodeInvalidArgument, CodeTargetNotAuthorized,
		CodePolicyDenied, CodeToolNotFound, CodeToolAmbiguous,
		CodeBinaryUnavailable, CodeTemplateUnavailable, CodeInvalidTarget,
		CodeTimeout, CodeNonzeroExit, CodeParserFailure, CodeResourceLimit, CodeUnknown,
	}
	got := AllCodes()
	if len(got) != len(want) {
		t.Fatalf("code set changed: want %d, got %d", len(want), len(got))
	}
	for i, c := range want {
		if got[i] != c {
			t.Fatalf("code[%d] changed: want %s, got %s", i, c, got[i])
		}
	}
}

func TestDefaultsForMissingTarget(t *testing.T) {
	if !DefaultRequiresUserInput(CodeMissingRequiredArgument) {
		t.Fatalf("MISSING_REQUIRED_ARGUMENT must require user input")
	}
	if DefaultRetryable(CodeMissingRequiredArgument) {
		t.Fatalf("MISSING_REQUIRED_ARGUMENT must not be retryable")
	}
}

func TestNormalizeMapsKnownStrings(t *testing.T) {
	cases := []struct {
		in   string
		want Code
	}{
		{"tool nuclei missing required", CodeMissingRequiredArgument},
		{"unknown argument 'foo'", CodeInvalidArgument},
		{"target not authorized", CodeTargetNotAuthorized},
		{"policy denied: additional_args not allowed", CodePolicyDenied},
		{"tool not found", CodeToolNotFound},
		{"ambiguous match", CodeToolAmbiguous},
		{"binary not found", CodeBinaryUnavailable},
		{"template not readable", CodeTemplateUnavailable},
		{"invalid target", CodeInvalidTarget},
		{"deadline exceeded", CodeTimeout},
		{"non-zero exit code", CodeNonzeroExit},
		{"parse error in output", CodeParserFailure},
	}
	for _, tc := range cases {
		got := Normalize("nuclei", tc.in)
		if got.Code != tc.want {
			t.Fatalf("Normalize(%q): want %s, got %s", tc.in, tc.want, got.Code)
		}
	}
}

func TestNormalizeFallsBackToUnknown(t *testing.T) {
	got := Normalize("nuclei", "this string matches no known pattern at all")
	if got.Code != CodeUnknown {
		t.Fatalf("expected UNKNOWN fallback, got %s", got.Code)
	}
	if got.Retryable {
		t.Fatalf("UNKNOWN should not be retryable by default")
	}
}

func TestNewAppliesDefaults(t *testing.T) {
	r := New(CodeMissingRequiredArgument, "nuclei", "needs target")
	if !r.RequiresUserInput {
		t.Fatalf("New should copy requires_user_input from defaults")
	}
	if r.Retryable {
		t.Fatalf("New should copy retryable from defaults")
	}
}
