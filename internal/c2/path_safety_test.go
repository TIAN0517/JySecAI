package c2

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// symlinkOrSkip 建立符號連結；若目前平台 / 權限不允許就明確跳過並說明原因。
//
// Windows 需要 Developer Mode 或系統管理員權限才能建立 symlink，這是環境限制
// 而非被測邏輯的問題。跳過訊息會寫進測試輸出，不會被靜默吞掉。
func symlinkOrSkip(t *testing.T, target, link string) {
	t.Helper()
	if err := os.Symlink(target, link); err != nil {
		if runtime.GOOS == "windows" {
			t.Skipf("此環境無法建立符號連結（需 Developer Mode 或系統管理員權限）：%v", err)
		}
		t.Fatalf("建立符號連結失敗: %v", err)
	}
}

func TestEnsurePathInDirAcceptsNormalPath(t *testing.T) {
	dir := t.TempDir()
	if err := ensurePathInDir(dir, filepath.Join(dir, "task_abc.bin")); err != nil {
		t.Fatalf("正常路徑應被允許: %v", err)
	}
}

// 目標目錄尚未建立時（例如首次使用）也必須放行 —— 這是正常流程。
func TestEnsurePathInDirAllowsMissingDirectory(t *testing.T) {
	base := t.TempDir()
	dir := filepath.Join(base, "results")
	if err := ensurePathInDir(dir, filepath.Join(dir, "task_abc.bin")); err != nil {
		t.Fatalf("目錄尚未建立時應放行（寫入時才會 mkdir）: %v", err)
	}
}

func TestEnsurePathInDirRejectsTraversal(t *testing.T) {
	dir := t.TempDir()
	cases := []struct {
		name string
		path string
	}{
		{"上層目錄", filepath.Join(dir, "..", "escaped.bin")},
		{"上層目錄前綴偽裝", filepath.Join(dir, "..", "resultsescaped.bin")},
		{"就是上層", filepath.Dir(dir)},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if err := ensurePathInDir(dir, tc.path); err == nil {
				t.Fatalf("穿越路徑未被拒絕: %s", tc.path)
			}
		})
	}
}

// 結果目錄本身被換成指向別處的符號連結時，字面檢查看不出來，
// 但實際寫入會落到預期之外 —— 這是本函式補上的缺口。
func TestEnsurePathInDirRejectsSymlinkedDirectory(t *testing.T) {
	base := t.TempDir()
	elsewhere := filepath.Join(base, "elsewhere")
	if err := os.MkdirAll(elsewhere, 0o755); err != nil {
		t.Fatal(err)
	}
	realDir := filepath.Join(base, "results")
	if err := os.MkdirAll(realDir, 0o755); err != nil {
		t.Fatal(err)
	}
	linkedDir := filepath.Join(base, "linked")
	symlinkOrSkip(t, realDir, linkedDir)

	// linked/task.bin 在字面上位於 linked 之下，純字面檢查會放行。
	if err := ensurePathInDir(linkedDir, filepath.Join(linkedDir, "task.bin")); err == nil {
		t.Fatal("符號連結目錄未被拒絕")
	}
}

// 目標檔案已存在且是符號連結時，os.WriteFile 會跟著穿透寫到別處。
func TestEnsurePathInDirRejectsSymlinkedTargetFile(t *testing.T) {
	dir := t.TempDir()
	outside := filepath.Join(dir, "outside.txt")
	if err := os.WriteFile(outside, []byte("original"), 0o644); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(dir, "task_abc.bin")
	symlinkOrSkip(t, outside, link)

	if err := ensurePathInDir(dir, link); err == nil {
		t.Fatal("目標為符號連結時未被拒絕")
	}
}

// 目標是一般檔案時必須放行 —— 防護不能擋掉正常寫入。
func TestEnsurePathInDirAllowsRegularTargetFile(t *testing.T) {
	dir := t.TempDir()
	target := filepath.Join(dir, "task_abc.bin")
	if err := os.WriteFile(target, []byte("data"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := ensurePathInDir(dir, target); err != nil {
		t.Fatalf("既有的一般檔案應被允許（覆寫是正常流程）: %v", err)
	}
}

// 防護要能擋下實際會發生的寫入，而不只是回傳錯誤字串。
func TestSaveResultBlobRefusesSymlinkedTarget(t *testing.T) {
	dir := t.TempDir()
	storageDir := filepath.Join(dir, "storage")
	if err := os.MkdirAll(storageDir, 0o755); err != nil {
		t.Fatal(err)
	}
	outside := filepath.Join(dir, "outside.txt")
	if err := os.WriteFile(outside, []byte("original"), 0o644); err != nil {
		t.Fatal(err)
	}
	// 在 results 目錄中預置一個指向外部檔案的符號連結。
	resultsDir := filepath.Join(storageDir, "results")
	if err := os.MkdirAll(resultsDir, 0o755); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(resultsDir, "t_abc.bin")
	symlinkOrSkip(t, outside, link)

	m := &Manager{storageDir: storageDir, logger: nil}
	if _, err := m.saveResultBlob("t_abc", "aGVsbG8=", ".bin"); err == nil {
		t.Fatal("saveResultBlob 接受了指向外部檔案的符號連結")
	}

	after, err := os.ReadFile(outside)
	if err != nil {
		t.Fatal(err)
	}
	if string(after) != "original" {
		t.Fatalf("外部檔案被覆寫了：%q", after)
	}
}

func TestEnsureNoSymlinkEscapeErrorMentionsPath(t *testing.T) {
	dir := t.TempDir()
	link := filepath.Join(dir, "link.bin")
	symlinkOrSkip(t, filepath.Join(dir, "target.bin"), link)

	err := ensureNoSymlinkEscape(dir, link)
	if err == nil {
		t.Fatal("預期錯誤")
	}
	// 錯誤訊息要帶上路徑，讓 log 能指出是哪個任務出的問題。
	if !strings.Contains(err.Error(), "link.bin") {
		t.Errorf("錯誤訊息未指出路徑: %v", err)
	}
}
