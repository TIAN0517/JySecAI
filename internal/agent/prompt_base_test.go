package agent

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// TestResolveWithinPromptBaseRejectsEscapes guards the arbitrary-file-read fix.
// system_prompt_path is writable through PUT /api/config, and its contents
// become the LLM system prompt and are echoed back in conversation, so reading
// ~/.ssh/id_rsa through it is a credential exfiltration primitive.
func TestResolveWithinPromptBaseRejectsEscapes(t *testing.T) {
	base := t.TempDir()
	inside := filepath.Join(base, "prompts", "system.txt")
	if err := os.MkdirAll(filepath.Dir(inside), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(inside, []byte("hello"), 0o644); err != nil {
		t.Fatal(err)
	}

	// A secret outside the base directory.
	outside := filepath.Join(t.TempDir(), "id_rsa")
	if err := os.WriteFile(outside, []byte("PRIVATE KEY"), 0o600); err != nil {
		t.Fatal(err)
	}

	// A link planted inside the base that points outward. Path-prefix
	// comparison alone would accept this; EvalSymlinks is what stops it.
	// Windows needs a directory junction, which does not require elevation.
	escapeLink := filepath.Join(base, "escape")
	if err := os.Symlink(outside, escapeLink); err != nil {
		if runtime.GOOS == "windows" {
			t.Logf("symlink unavailable (%v); covering traversal without it", err)
		} else {
			t.Fatalf("symlink: %v", err)
		}
	} else {
		if _, err := resolveWithinPromptBase(base, "escape"); err == nil {
			t.Error("symlink out of the base was accepted")
		}
	}

	allowed := []string{
		"prompts/system.txt",
		"prompts",
		"prompts/../prompts/system.txt",
	}
	for _, p := range allowed {
		if _, err := resolveWithinPromptBase(base, p); err != nil {
			t.Errorf("resolveWithinPromptBase(%q) = %v, want allowed", p, err)
		}
	}

	denied := []string{
		"../escape.txt",
		"../../etc/passwd",
		"prompts/../../etc/passwd",
		outside,       // absolute path outside the base
		"/etc/passwd", // absolute path outside the base
		"prompts/../../" + filepath.Base(outside),
	}
	for _, p := range denied {
		got, err := resolveWithinPromptBase(base, p)
		if err == nil {
			t.Errorf("resolveWithinPromptBase(%q) = %q, want error", p, got)
		}
	}
}

// TestResolveWithinPromptBaseWithoutBaseRejectsAbsolute covers the
// promptBaseDir-is-empty case: relative paths still work, absolute and rooted
// ones do not.
func TestResolveWithinPromptBaseWithoutBaseRejectsAbsolute(t *testing.T) {
	// On Windows filepath.IsAbs(`\Windows\System32\config\SAM`) is false while
	// filepath.Abs happily resolves it to C:\Windows\System32\config\SAM, so an
	// IsAbs-only check leaves the SAM hive readable.
	denied := []string{
		"/etc/passwd",
		`\Windows\System32\config\SAM`,
		`\etc\shadow`,
		`C:\Windows\System32\config\SAM`,
		`..\..\Windows\win.ini`,
		"../escape.txt",
		"..",
		"   ",
	}
	for _, p := range denied {
		if got, err := resolveWithinPromptBase("", p); err == nil {
			t.Errorf("resolveWithinPromptBase(%q) = %q, want error", p, got)
		}
	}
	if _, err := resolveWithinPromptBase("   ", `C:\Windows\System32\config\SAM`); err == nil {
		t.Error("absolute path accepted with blank base configured")
	}

	got, err := resolveWithinPromptBase("", "prompts/system.txt")
	if err != nil {
		t.Fatalf("relative path rejected with no base: %v", err)
	}
	if !filepath.IsAbs(got) {
		t.Errorf("expected an absolute path, got %q", got)
	}
}

// TestResolveWithinPromptBaseRejectsSiblingPrefix is the classic prefix bug:
// "C:\prompts" must not admit "C:\prompts-evil". The separator check is what
// separates containment from string-prefix coincidence.
func TestResolveWithinPromptBaseRejectsSiblingPrefix(t *testing.T) {
	parent := t.TempDir()
	base := filepath.Join(parent, "prompts")
	evil := filepath.Join(parent, "prompts-evil")
	for _, d := range []string{base, evil} {
		if err := os.MkdirAll(d, 0o755); err != nil {
			t.Fatal(err)
		}
	}
	secret := filepath.Join(evil, "secret.txt")
	if err := os.WriteFile(secret, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}

	if _, err := resolveWithinPromptBase(base, secret); err == nil {
		t.Errorf("sibling directory with a shared string prefix was accepted: %s", secret)
	}
	if _, err := resolveWithinPromptBase(base, evil); err == nil {
		t.Error("sibling directory was accepted")
	}
}

// TestResolveWithinPromptBaseBaseItself pins that the base directory is a
// valid target, not just its children.
func TestResolveWithinPromptBaseBaseItself(t *testing.T) {
	base := t.TempDir()
	got, err := resolveWithinPromptBase(base, ".")
	if err != nil {
		t.Fatalf("base itself rejected: %v", err)
	}
	// t.TempDir() may hand back an 8.3 short path (ADMINI~1) while the function
	// returns the expanded form, so compare resolved paths.
	want, _ := filepath.EvalSymlinks(base)
	if resolvedGot, err := filepath.EvalSymlinks(got); err == nil {
		got = resolvedGot
	}
	if !strings.EqualFold(filepath.Clean(got), filepath.Clean(want)) {
		t.Errorf("got %q, want %q", got, want)
	}
}
