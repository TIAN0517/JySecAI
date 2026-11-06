package skillpackage

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// SafeRelPath 對 rel 的驗證是正確的：它擋掉 `..`，並用 filepath.Rel 重新確認
// 包含性。但它驗證的基準 root 來自 SkillDir(skillsRoot, skillID)，而 skillID
// 來自 gin 路由參數。在 ValidateSkillID 之前，一個 `..\..\` 的 skillID 會讓
// root 本身就落在 skillsRoot 之外，此時 filepath.Rel 證明的是「沒跳出 root」
// —— 而 root 本身已經是錯的。
//
// 這些測試守住的是 base，不是 rel。

func writeSkill(t *testing.T, skillsRoot, id string) string {
	t.Helper()
	dir := filepath.Join(skillsRoot, id)
	if err := os.MkdirAll(dir, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte("---\nname: "+id+"\n---\nbody"), 0644); err != nil {
		t.Fatal(err)
	}
	return dir
}

// 建立一個 skillsRoot，並在它「外面」放一個看起來很有价值的檔案。
func outsideLoot(t *testing.T) (skillsRoot string, secretPath string) {
	t.Helper()
	base := t.TempDir()
	skillsRoot = filepath.Join(base, "skills")
	if err := os.MkdirAll(skillsRoot, 0755); err != nil {
		t.Fatal(err)
	}
	secretPath = filepath.Join(base, "id_rsa")
	if err := os.WriteFile(secretPath, []byte("PRIVATE-KEY-MATERIAL"), 0600); err != nil {
		t.Fatal(err)
	}
	return skillsRoot, secretPath
}

func TestSkillDirRejectsEscapingIDs(t *testing.T) {
	skillsRoot := t.TempDir()
	for name, id := range map[string]string{
		"dotdot":            "..",
		"dotdot-win":        `..\..\..\..\..\`,
		"absolute":          filepath.Join(string(filepath.Separator), "etc"),
		"drive-letter":      `C:\`,
		"nested":            "a/b",
		"nested-win":        `a\b`,
		"empty":             "",
		"leading-dot":       ".hidden",
		"trailing-space":    "name ",
		"percent":           "%2e%2e",
		"newline":           "name\n..",
		"too-long":          strings.Repeat("a", 101),
		"null-ish":          "name\x00",
		"unicode-fullwidth": "．．",
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := SkillDir(skillsRoot, id); err == nil {
				t.Errorf("SkillDir accepted %q and produced %q", id, filepath.Join(skillsRoot, id))
			}
		})
	}
}

// 合法名稱必須仍然通過 —— 否則這個修補只是把功能關掉而已。
func TestSkillDirAcceptsValidIDs(t *testing.T) {
	skillsRoot := t.TempDir()
	for _, id := range []string{"pentest-agent-os", "c2-infra", "vuln-triage-automation", "a", "skill2", strings.Repeat("a", 100)} {
		got, err := SkillDir(skillsRoot, id)
		if err != nil {
			t.Errorf("SkillDir rejected valid id %q: %v", id, err)
			continue
		}
		if want := filepath.Join(skillsRoot, id); got != want {
			t.Errorf("SkillDir(%q) = %q, want %q", id, got, want)
		}
	}
}

func TestReadPackageFileCannotEscapeSkillsRoot(t *testing.T) {
	skillsRoot, _ := outsideLoot(t)
	writeSkill(t, skillsRoot, "demo-skill")

	for _, id := range []string{"..", `..\..`, filepath.Join("..", "..")} {
		if b, err := ReadPackageFile(skillsRoot, id, "id_rsa", 0); err == nil {
			t.Errorf("ReadPackageFile(%q) read outside skillsRoot: %q", id, string(b))
		}
	}
	// 同一個 skill 內的檔案仍然讀得到 —— 邊界不能收得太緊。
	if _, err := ReadPackageFile(skillsRoot, "demo-skill", "SKILL.md", 0); err != nil {
		t.Errorf("ReadPackageFile refused a legitimate read: %v", err)
	}
}

// WritePackageFile 與 ListPackageFiles 原本有 ResolveSKILLPath 守衛，但那個守衛
// 只證明「目標目錄裡有 SKILL.md」，不證明它在 skillsRoot 之內 —— 在任何地方放一個
// SKILL.md 就能通過。
func TestWriteAndListCannotEscapeSkillsRoot(t *testing.T) {
	skillsRoot, _ := outsideLoot(t)
	// 在 skillsRoot 外面放一個帶 SKILL.md 的目錄，專門用來骗過 ResolveSKILLPath。
	trap := filepath.Join(filepath.Dir(skillsRoot), "trap")
	if err := os.MkdirAll(trap, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(trap, "SKILL.md"), []byte("x"), 0644); err != nil {
		t.Fatal(err)
	}

	if err := WritePackageFile(skillsRoot, `..\trap`, "pwned.txt", []byte("x")); err == nil {
		t.Error("WritePackageFile wrote outside skillsRoot")
	} else {
		if _, err := os.Stat(filepath.Join(trap, "pwned.txt")); err == nil {
			t.Error("a file appeared outside skillsRoot despite the error")
		}
	}
	if files, err := ListPackageFiles(skillsRoot, `..\trap`); err == nil {
		t.Errorf("ListPackageFiles listed %d entries outside skillsRoot", len(files))
	}
}

// listScripts 是第三個組 base 的地方，而且它的錯誤回傳是 (nil, nil) —— 沒有 SKILL.md
// 時靜靜地回空。驗證失敗時必須維持同樣語意，不能變成一個「看起來像錯誤」的行為。
func TestListScriptsRejectsEscapingID(t *testing.T) {
	skillsRoot, _ := outsideLoot(t)
	scripts, err := listScripts(skillsRoot, "..")
	if err == nil {
		t.Errorf("listScripts accepted an escaping id and returned %d scripts", len(scripts))
	}
}
