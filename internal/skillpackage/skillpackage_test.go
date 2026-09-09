package skillpackage

import (
	"os"
	"path/filepath"
	"testing"
)

func TestExtractSkillMDFrontMatterYAML(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		wantErr  bool
		wantName string
		wantBody string
	}{
		{
			name:     "standard front matter",
			input:    "---\nname: my-skill\ndescription: A test skill\n---\n# Body Content",
			wantErr:  false,
			wantName: "my-skill",
			wantBody: "# Body Content",
		},
		{
			name:     "with CRLF line endings",
			input:    "---\r\nname: my-skill\r\ndescription: A test skill\r\n---\r\n# Body Content",
			wantErr:  false,
			wantName: "my-skill",
			wantBody: "# Body Content",
		},
		{
			name:     "with UTF-8 BOM",
			input:    "\ufeff---\nname: my-skill\ndescription: A test skill\n---\n# Body Content",
			wantErr:  false,
			wantName: "my-skill",
			wantBody: "# Body Content",
		},
		{
			name:     "with leading blank lines",
			input:    "\n\n---\nname: my-skill\ndescription: A test skill\n---\n# Body Content",
			wantErr:  false,
			wantName: "my-skill",
			wantBody: "# Body Content",
		},
		{
			name:     "with duplicate opening delimiter",
			input:    "---\n---\nname: my-skill\ndescription: A test skill\n---\n# Body Content",
			wantErr:  false,
			wantName: "my-skill",
			wantBody: "# Body Content",
		},
		{
			name:    "missing closing delimiter",
			input:   "---\nname: my-skill\ndescription: A test skill\n",
			wantErr: true,
		},
		{
			name:    "empty input",
			input:   "",
			wantErr: true,
		},
		{
			name:    "missing opening delimiter",
			input:   "name: my-skill\ndescription: A test skill\n---\n",
			wantErr: true,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			_, body, err := ExtractSkillMDFrontMatterYAML([]byte(tc.input))
			if tc.wantErr {
				if err == nil {
					t.Fatalf("expected error, got nil")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if tc.wantBody != "" && body != tc.wantBody {
				t.Errorf("got body %q, want %q", body, tc.wantBody)
			}
			man, _, err := ParseSkillMD([]byte(tc.input))
			if err != nil {
				t.Fatalf("ParseSkillMD failed: %v", err)
			}
			if man.Name != tc.wantName {
				t.Errorf("got name %q, want %q", man.Name, tc.wantName)
			}
		})
	}
}

func TestListSkillSummariesRealDir(t *testing.T) {
	skillsRoot := filepath.Join("..", "..", "skills")
	if fi, err := os.Stat(skillsRoot); err != nil || !fi.IsDir() {
		t.Skip("skills directory not found at ../../skills, skipping real dir test")
	}

	summaries, err := ListSkillSummaries(skillsRoot)
	if err != nil {
		t.Fatalf("ListSkillSummaries failed: %v", err)
	}

	if len(summaries) == 0 {
		t.Fatalf("expected at least 1 skill, got 0")
	}

	t.Logf("Successfully loaded %d skill packages from %s", len(summaries), skillsRoot)
	for _, s := range summaries {
		if s.Name == "" {
			t.Errorf("skill %s has empty name", s.ID)
		}
		if s.Description == "" {
			t.Errorf("skill %s has empty description", s.ID)
		}
	}
}
