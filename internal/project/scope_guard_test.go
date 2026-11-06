package project

import (
	"strings"
	"testing"

	"jysecai/internal/database"
)

func TestParseScopeTargetsPrefersStructuredFields(t *testing.T) {
	raw := `{
		"targets": ["ignored.example.com"],
		"exclude": ["also-ignored.example.com"],
		"scope": {
			"allow": {"domains": ["portal.agency.gov.tw"], "domain_suffixes": [".city.gov.tw"]},
			"deny":  {"domains": ["legacy.gov.tw"]}
		}
	}`
	scope, err := ParseScopeTargets(raw)
	if err != nil {
		t.Fatal(err)
	}
	if scope == nil {
		t.Fatal("expected a scope")
	}
	// 結構化欄位優先：舊的自由字串不該混進來。
	allow := strings.Join(scope.AllowEntries(), ",")
	deny := strings.Join(scope.DenyEntries(), ",")
	if !strings.Contains(allow, "portal.agency.gov.tw") {
		t.Fatalf("structured allow missing: %s", allow)
	}
	if strings.Contains(allow, "ignored.example.com") {
		t.Fatalf("free text must not override structured fields: %s", allow)
	}
	if !strings.Contains(deny, "legacy.gov.tw") {
		t.Fatalf("structured deny missing: %s", deny)
	}
}

func TestParseScopeTargetsFallsBackToFreeText(t *testing.T) {
	raw := `{"targets": ["https://app.example.com/path", "*.cdn.example.com"], "exclude": ["legacy.gov.tw"]}`
	scope, err := ParseScopeTargets(raw)
	if err != nil {
		t.Fatal(err)
	}
	if scope == nil {
		t.Fatal("expected a scope")
	}
	got := strings.Join(scope.AllowEntries(), ",") + "," + strings.Join(scope.DenyEntries(), ",")
	for _, want := range []string{"app.example.com", "*.cdn.example.com", "legacy.gov.tw"} {
		if !strings.Contains(got, want) {
			t.Fatalf("expected %q in %s", want, got)
		}
	}
}

func TestParseScopeTargetsIgnoresUnusableEntries(t *testing.T) {
	raw := `{"targets": ["n/a", "app.example.com"]}`
	scope, err := ParseScopeTargets(raw)
	if err != nil {
		t.Fatal(err)
	}
	got := strings.Join(scope.AllowEntries(), ",")
	if strings.Contains(got, "n/a") {
		t.Fatalf("unusable entry must be ignored: %s", got)
	}
	if !strings.Contains(got, "app.example.com") {
		t.Fatalf("usable entry missing: %s", got)
	}
}

func TestParseScopeTargetsEmptyAndInvalid(t *testing.T) {
	scope, err := ParseScopeTargets("   ")
	if err != nil || scope != nil {
		t.Fatalf("blank scope should be empty, got scope=%v err=%v", scope, err)
	}
	if _, err := ParseScopeTargets("{not json"); err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestBuildScopeBlockRendersStructuredScope(t *testing.T) {
	proj := &database.Project{
		ID:   "proj-1",
		Name: "重定向專案",
		ScopeJSON: `{"scope": {
			"allow": {"domains": ["portal.agency.gov.tw"]},
			"deny":  {"domains": ["legacy.gov.tw"]}
		}}`,
	}
	block := BuildScopeBlock(proj)
	if !strings.Contains(block, "portal.agency.gov.tw") {
		t.Fatalf("structured allow missing from block:\n%s", block)
	}
	if !strings.Contains(block, "legacy.gov.tw") {
		t.Fatalf("structured deny missing from block:\n%s", block)
	}
	// 沒有 targets/exclude 欄位時不該落回「未識別欄位」的提示。
	if strings.Contains(block, "未识别 targets/exclude/notes") {
		t.Fatalf("structured scope must not fall back to the raw dump:\n%s", block)
	}
}
