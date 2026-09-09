package poc

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"
)

func TestPocFilenameFor(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:    "vuln-12345",
		Title: "SQL Injection in /api/login?user=admin",
	}
	name := PocFilenameFor(vuln)
	if name == "" {
		t.Fatalf("expected non-empty filename")
	}
	if filepath.Ext(name) != ".md" {
		t.Fatalf("expected .md extension, got %s", name)
	}
}

func TestBuildPocDraftMarkdown(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:          "vuln-test",
		Title:       "Sample Command Injection",
		Severity:    "high",
		Status:      "open",
		Type:        "RCE",
		Target:      "https://example.com/exec",
		Description: "Target is vulnerable to command injection via ping utility",
		ReproSteps:  "Send POST /exec with cmd=;id",
		Evidence:    "uid=0(root) gid=0(root)",
		CreatedAt:   time.Now(),
	}

	md := BuildPocDraftMarkdown(vuln, nil)
	if len(md) == 0 {
		t.Fatalf("expected non-empty markdown")
	}
	if !containsStr(md, "Sample Command Injection") {
		t.Errorf("markdown missing title")
	}
	if !containsStr(md, "https://example.com/exec") {
		t.Errorf("markdown missing target")
	}
}

func TestGeneratePocDraft(t *testing.T) {
	tmpDir := t.TempDir()
	vuln := &database.Vulnerability{
		ID:       "vuln-unit-1",
		Title:    "Test Vulnerability Draft",
		Severity: "medium",
		Target:   "https://test.local",
	}

	res, err := GeneratePocDraft(nil, vuln, tmpDir, false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if res.Filename == "" {
		t.Fatalf("expected non-empty filename")
	}

	content, err := os.ReadFile(res.FullPath)
	if err != nil {
		t.Fatalf("failed to read generated file: %v", err)
	}
	if len(content) == 0 {
		t.Fatalf("generated file is empty")
	}
}

func containsStr(haystack, needle string) bool {
	return len(haystack) >= len(needle) && (haystack == needle || len(needle) == 0 || stringContains(haystack, needle))
}

func stringContains(s, substr string) bool {
	for i := 0; i+len(substr) <= len(s); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func TestHasPocDraftMarker(t *testing.T) {
	cases := []struct {
		evidence string
		expected bool
	}{
		{"", false},
		{"normal evidence text", false},
		{"> [自動生成 POC/EXP 草稿] poc_drafts/vuln-1.md", true},
		{"> [自动生成 POC/EXP 草稿] poc_drafts/vuln-2.md", true},
		{"prefix\n\n> [自動生成 POC/EXP 草稿] test.md\nsuffix", true},
		{"prefix\n\n> [自动生成 POC/EXP 草稿] test.md\nsuffix", true},
	}

	for _, c := range cases {
		got := HasPocDraftMarker(c.evidence)
		if got != c.expected {
			t.Errorf("HasPocDraftMarker(%q) = %v, want %v", c.evidence, got, c.expected)
		}
	}
}
