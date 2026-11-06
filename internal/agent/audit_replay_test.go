package agent

import (
	"os"
	"path/filepath"
	"testing"
)

// TestCfgAuditReportedPayloadsAreBlocked replays the exact payloads an
// automated audit reported as an exploitable arbitrary file read, to confirm
// the current tree rejects them. The audit quoted pre-fix source; this test
// pins the behaviour rather than trusting either version of the code.
func TestCfgAuditReportedPayloadsAreBlocked(t *testing.T) {
	base := t.TempDir()

	// The secret the audit claimed was readable.
	secret := filepath.Join(t.TempDir(), "id_rsa")
	if err := os.WriteFile(secret, []byte("PRIVATE KEY"), 0o600); err != nil {
		t.Fatal(err)
	}

	payloads := []string{
		`C:\Users\Administrator\.ssh\id_rsa`,
		`../../../../windows/system32/drivers/etc/hosts`,
		secret,
		`..\..\..\config.yaml`,
		`\\server\share\secret.txt`,
		`/etc/passwd`,
	}
	for _, p := range payloads {
		if got, err := resolveWithinPromptBase(base, p); err == nil {
			t.Errorf("payload %q resolved to %q — the arbitrary read is still open", p, got)
		}
	}
	// Same payloads with no base configured at all.
	for _, p := range payloads {
		if got, err := resolveWithinPromptBase("", p); err == nil {
			t.Errorf("payload %q resolved to %q with no base configured", p, got)
		}
	}
}
