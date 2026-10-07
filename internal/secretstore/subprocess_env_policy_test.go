package secretstore

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// 這個檔案是 repo 層級的回歸防線。
//
// 單元測試只能守住自己那個函式；把 secretstore.WithoutSecrets 從某個
// exec 呼叫點移除，該處的測試不會紅。落盤加密的前提是「拿到資料庫也解不開」，
// 而子行程繼承 os.Environ() 會讓這個前提失效 —— 所以在這裡直接掃原始碼。

// 匹配「把 os.Environ() 拿來組子行程環境」的寫法。
var rawEnvironIntoCmdEnv = regexp.MustCompile(`\b(cmd\.Env|Env)\s*(:?=)\s*.*os\.Environ\(`)

// moduleRoot 從套件目錄往上找到 go.mod。
func moduleRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatalf("取得工作目錄: %v", err)
	}
	for {
		if b, err := os.ReadFile(filepath.Join(dir, "go.mod")); err == nil {
			if strings.Contains(string(b), "module jysecai") {
				return dir
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("找不到 go.mod")
		}
		dir = parent
	}
}

// 掃描 internal/ 下所有非測試 Go 原始碼。
func TestNoRawEnvironIntoSubprocessEnv(t *testing.T) {
	root := moduleRoot(t)
	// secretstore 本身是 ChildEnv 的定義處，os.Environ() 出現在那裡是刻意的。
	skipDir := filepath.Join(root, "internal", "secretstore")

	var findings []string
	err := filepath.WalkDir(filepath.Join(root, "internal"), func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if path == skipDir {
				return fs.SkipDir
			}
			return nil
		}
		name := d.Name()
		if !strings.HasSuffix(name, ".go") || strings.HasSuffix(name, "_test.go") {
			return nil
		}
		// 平台專用檔在 Windows 上可能不存在，略過找不到的情況。
		b, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(root, path)
		for i, line := range strings.Split(string(b), "\n") {
			if rawEnvironIntoCmdEnv.MatchString(line) {
				findings = append(findings, sprintfLoc(rel, i+1, strings.TrimSpace(line)))
			}
		}
		return nil
	})
	if err != nil {
		t.Fatalf("掃描 internal/ 失敗: %v", err)
	}

	if len(findings) > 0 {
		t.Errorf("有 %d 處把 os.Environ() 直接交給子行程，主金鑰會外流。\n"+
			"請改用 secretstore.ChildEnv(...) 或 secretstore.WithoutSecrets(...):\n  %s",
			len(findings), strings.Join(findings, "\n  "))
	}
}

func sprintfLoc(file string, line int, text string) string {
	return fmt.Sprintf("%s:%d: %s", file, line, text)
}
