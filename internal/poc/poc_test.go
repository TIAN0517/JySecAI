package poc

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestPocFilenameForSanitizesEveryComponent(t *testing.T) {
	name := PocFilenameFor(&database.Vulnerability{
		ID:    `../../outside\\payload`,
		Title: `../<script>alert(1)</script>`,
	})
	if name != filepath.Base(name) || strings.Contains(name, "..") || strings.ContainsAny(name, `/\\`) {
		t.Fatalf("unsafe filename %q", name)
	}
	if !strings.HasSuffix(name, ".md") {
		t.Fatalf("filename %q does not have .md suffix", name)
	}
}

func TestGeneratePocDraftWritesOnlyInsideConfiguredDirectory(t *testing.T) {
	dir := t.TempDir()
	vuln := &database.Vulnerability{
		ID:         `../../../escape`,
		Title:      "Example finding",
		Severity:   "high",
		Target:     "https://example.invalid",
		ReproSteps: "1. Capture a harmless request\n2. Verify the response",
	}
	result, err := GeneratePocDraft(nil, vuln, dir, false)
	if err != nil {
		t.Fatal(err)
	}
	rel, err := filepath.Rel(dir, result.FullPath)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		t.Fatalf("draft escaped output directory: path=%q rel=%q err=%v", result.FullPath, rel, err)
	}
	content, err := os.ReadFile(result.FullPath)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(content), "草稿（未驗證）") || !strings.Contains(string(content), "合法授權") {
		t.Fatalf("draft is missing safety labels: %s", content)
	}
	if result.UpdatedEvidence {
		t.Fatal("evidence should not be updated when writeEvidence=false")
	}
}

func TestGeneratePocDraftLinksEvidenceIdempotently(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "poc.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	vuln, err := db.CreateVulnerability(&database.Vulnerability{Title: "Stored finding", Severity: "medium"})
	if err != nil {
		t.Fatal(err)
	}
	output := filepath.Join(t.TempDir(), DraftDirName)
	if _, err := GeneratePocDraft(db, vuln, output, true); err != nil {
		t.Fatal(err)
	}
	if _, err := GeneratePocDraft(db, vuln, output, true); err != nil {
		t.Fatal(err)
	}
	stored, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatal(err)
	}
	if count := strings.Count(stored.Evidence, DefaultMarker); count != 1 {
		t.Fatalf("marker count = %d, want 1; evidence=%q", count, stored.Evidence)
	}
}
