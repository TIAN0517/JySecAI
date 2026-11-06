package poc

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"unicode/utf8"

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

// ossPublicReadTitle 是實際打中過位元組截斷缺陷的標題。
// 以位元組切 60 位元組時，會剛好切在「任」的首位元組 0xE4 上，
// 留下孤立前導位元組，寫進檔名與 evidence 欄位後兩者都不是合法 UTF-8。
const ossPublicReadTitle = "OSS 桶 b9jiyun 为 public-read，未签名即可匿名下载任意已知 key 对象"

func TestPocFilenameForKeepsTitleIntactForMultibyteRunes(t *testing.T) {
	name := PocFilenameFor(&database.Vulnerability{
		ID:    "eee53302-f563-4a64-8c43-abf390cf8c38",
		Title: ossPublicReadTitle,
	})
	if !utf8.ValidString(name) {
		t.Fatalf("filename is not valid UTF-8: %q", name)
	}
	// 以 rune 計的 60 字上限之下，整段標題都應保留。
	if !strings.Contains(name, "未签名即可匿名下载任意已知") {
		t.Fatalf("filename lost the tail of the title: %q", name)
	}
	if strings.ContainsRune(name, utf8.RuneError) {
		t.Fatalf("filename contains a replacement character: %q", name)
	}
}

func TestPocFilenameForTruncatesOnRuneBoundary(t *testing.T) {
	// 240 個中文字元 = 720 位元組，必然超過兩種上限。
	title := strings.Repeat("測", 240)
	name := PocFilenameFor(&database.Vulnerability{ID: "vuln", Title: title})
	if !utf8.ValidString(name) {
		t.Fatalf("filename is not valid UTF-8: %q", name)
	}
	slug := strings.TrimSuffix(strings.TrimPrefix(name, "vuln-"), ".md")
	if got := utf8.RuneCountInString(slug); got != maxFilenameRunes {
		t.Fatalf("slug rune count = %d, want %d", got, maxFilenameRunes)
	}
	if strings.ContainsRune(name, utf8.RuneError) {
		t.Fatalf("filename contains a replacement character: %q", name)
	}
}

func TestPocFilenameForNormalizesInvalidUTF8Input(t *testing.T) {
	name := PocFilenameFor(&database.Vulnerability{
		ID:    "vuln",
		Title: "壞標題\xE4截斷", // 0xE4 是孤立前導位元組，非法 UTF-8
	})
	if !utf8.ValidString(name) {
		t.Fatalf("filename is not valid UTF-8: %q", name)
	}
}

// 端到端確認：寫進資料庫的 evidence 必須是合法 UTF-8，
// 而且它引用的檔案必須真的存在於草稿目錄中。
func TestGeneratePocDraftKeepsEvidenceValidUTF8AndResolvable(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "poc.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	vuln, err := db.CreateVulnerability(&database.Vulnerability{
		Title:    ossPublicReadTitle,
		Severity: "critical",
	})
	if err != nil {
		t.Fatal(err)
	}
	output := filepath.Join(t.TempDir(), DraftDirName)
	result, err := GeneratePocDraft(db, vuln, output, true)
	if err != nil {
		t.Fatal(err)
	}
	stored, err := db.GetVulnerability(vuln.ID)
	if err != nil {
		t.Fatal(err)
	}
	if !utf8.ValidString(stored.Evidence) {
		t.Fatalf("evidence is not valid UTF-8: %q", stored.Evidence)
	}
	rel := ""
	if idx := strings.LastIndex(stored.Evidence, DefaultMarker); idx >= 0 {
		rel = strings.TrimSpace(stored.Evidence[idx+len(DefaultMarker):])
	}
	if rel == "" {
		t.Fatalf("evidence does not reference a draft path: %q", stored.Evidence)
	}
	// evidence 內的路徑必須指得到實際落盘的檔案。
	// output 本身就是草稿目錄，evidence 記的是相對於其父層的 "poc_drafts/<檔名>"。
	want := filepath.Join(output, filepath.Base(rel))
	if got := mustAbs(t, result.FullPath); got != mustAbs(t, want) {
		t.Fatalf("evidence path %q does not resolve to the written draft %q", rel, result.FullPath)
	}
	if _, err := os.Stat(want); err != nil {
		t.Fatalf("evidence references a missing draft file %q: %v", want, err)
	}
}

func mustAbs(t *testing.T, p string) string {
	t.Helper()
	abs, err := filepath.Abs(p)
	if err != nil {
		t.Fatal(err)
	}
	return abs
}
