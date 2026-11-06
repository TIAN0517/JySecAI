package poc

import (
	"os"
	"strings"
	"testing"

	"jysecai/internal/database"
)

// TestBuildPocDraftMarkdownIncludesControlledRedirectEndpoints 確認受控回連端點
// 會出現在草稿裡：複測開放式跳轉時要改用這組端點，而不是原始紀錄的外部網域。
func TestBuildPocDraftMarkdownIncludesControlledRedirectEndpoints(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:       "v-1",
		Title:    "开放式跳转",
		Severity: "medium",
	}

	markdown := BuildPocDraftMarkdown(vuln, nil, "https://97y.me/tjneJ", "https://97y.me/tjneK")
	if !strings.Contains(markdown, "受控回連端點") {
		t.Fatalf("draft is missing the controlled endpoint section:\n%s", markdown)
	}
	for _, endpoint := range []string{"https://97y.me/tjneJ", "https://97y.me/tjneK"} {
		if !strings.Contains(markdown, endpoint) {
			t.Fatalf("draft is missing endpoint %q:\n%s", endpoint, markdown)
		}
	}
}

// TestBuildPocDraftMarkdownOmitsRedirectSectionWhenUnconfigured 沒有設定端點時
// 不應該多出這一段 —— 草稿不該暗示有受控端點可用。
func TestBuildPocDraftMarkdownOmitsRedirectSectionWhenUnconfigured(t *testing.T) {
	vuln := &database.Vulnerability{
		ID:       "v-2",
		Title:    "开放式跳转",
		Severity: "medium",
	}

	markdown := BuildPocDraftMarkdown(vuln, nil)
	if strings.Contains(markdown, "受控回連端點") {
		t.Fatalf("draft has a controlled endpoint section without configured endpoints:\n%s", markdown)
	}
}

// TestGeneratePocDraftWritesControlledRedirectEndpoints 確認端點清單有寫進檔案，
// 不是只留在記憶體裡。
func TestGeneratePocDraftWritesControlledRedirectEndpoints(t *testing.T) {
	dir := t.TempDir()
	vuln := &database.Vulnerability{
		ID:       "v-3",
		Title:    "开放式跳转",
		Severity: "medium",
	}

	result, err := GeneratePocDraft(nil, vuln, dir, false, "https://97y.me/tjneJ")
	if err != nil {
		t.Fatal(err)
	}
	content, err := os.ReadFile(result.FullPath)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(content), "https://97y.me/tjneJ") {
		t.Fatalf("draft file is missing the controlled endpoint:\n%s", content)
	}
}
