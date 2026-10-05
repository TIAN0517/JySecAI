package skillpackage

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ValidateSkillID 檢查 skillID 是一個安全的單一目錄名（Agent Skills 標準：
// 小寫字母、數字、連字符，1-100 字元）。
//
// 這必須是第一道防線，因為 skillID 會被原樣當成路徑的 base：
//
//	root := filepath.Join(skillsRoot, skillID)   // skillID = `..\..\` 就已經離開 skillsRoot
//	abs  := filepath.Join(root, relPath)        // relPath 本身完全合法，沒有 ".."
//	SafeRelPath 內部的 filepath.Rel 包含性檢查會拿著這個已經逃逸的 root 去比對，
//	必然通過 —— 它證明的是「沒跳出 root」，而問題出在 root 本身就是錯的。
//
// 也就是說 SafeRelPath 對 rel 的驗證是正確的，但它驗證的是錯誤的基準。
// 反過來說，約束了 skillID 之後，SafeRelPath 就成了第二道防線。
//
// 呼叫端不該在這裡之外各自實作一份字元檢查：本檔案是唯一的規則來源，
// CreateSkill 與所有 :name handler 都走同一個判斷。
func ValidateSkillID(skillID string) error {
	if skillID == "" || len(skillID) > 100 {
		return fmt.Errorf("技能名称 %q 无效：長度須為 1-100", skillID)
	}
	for _, r := range skillID {
		if !((r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-') {
			return fmt.Errorf("技能名称 %q 无效：只允许小写字母、数字与连字符", skillID)
		}
	}
	return nil
}

// SkillDir returns the absolute path to a skill package directory.
//
// 這裡刻意回傳 error 而不是自行「修正」輸入：靜默地 fallback 到某個預設值
// 會讓呼叫端以為操作成功，實際上卻作用在別的目錄上。簽名強制每個呼叫點
// 都必須顯式處理無效的 skillID —— 這正是讓這個漏洞無法在未來重現的原因。
func SkillDir(skillsRoot, skillID string) (string, error) {
	if err := ValidateSkillID(skillID); err != nil {
		return "", err
	}
	return filepath.Join(skillsRoot, skillID), nil
}

// ResolveSKILLPath returns SKILL.md path or error if missing.
func ResolveSKILLPath(skillPath string) (string, error) {
	md := filepath.Join(skillPath, "SKILL.md")
	if st, err := os.Stat(md); err != nil || st.IsDir() {
		return "", fmt.Errorf("missing SKILL.md in %q (Agent Skills standard)", filepath.Base(skillPath))
	}
	return md, nil
}

// SkillsRootFromConfig resolves cfg.SkillsDir relative to the config file directory.
func SkillsRootFromConfig(skillsDir string, configPath string) string {
	if skillsDir == "" {
		skillsDir = "skills"
	}
	configDir := filepath.Dir(configPath)
	if !filepath.IsAbs(skillsDir) {
		skillsDir = filepath.Join(configDir, skillsDir)
	}
	return skillsDir
}

// DirLister lists skill package directory names under SkillsRoot.
type DirLister struct {
	SkillsRoot string
}

// ListSkills returns skill package directory names that contain SKILL.md.
func (d DirLister) ListSkills() ([]string, error) {
	return ListSkillDirNames(d.SkillsRoot)
}

// ListSkillDirNames returns subdirectory names under skillsRoot that contain SKILL.md.
func ListSkillDirNames(skillsRoot string) ([]string, error) {
	if _, err := os.Stat(skillsRoot); os.IsNotExist(err) {
		return nil, nil
	}
	entries, err := os.ReadDir(skillsRoot)
	if err != nil {
		return nil, fmt.Errorf("read skills directory: %w", err)
	}
	var names []string
	for _, entry := range entries {
		if !entry.IsDir() || strings.HasPrefix(entry.Name(), ".") {
			continue
		}
		skillPath := filepath.Join(skillsRoot, entry.Name())
		if _, err := ResolveSKILLPath(skillPath); err == nil {
			names = append(names, entry.Name())
		}
	}
	return names, nil
}
