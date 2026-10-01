package secretstore

import (
	"os"
	"strings"
	"testing"
)

// 這組測試守的是一條邊界：主金鑰只存在於 JySecAI server 行程本身，
// 任何子行程都拿不到。落盤加密的整個前提就是「拿到資料庫也解不開」，
// 一旦主金鑰跟著 exec.Command 交出去，這個前提就不成立。

// 核心防線：主金鑰不得出現在子行程環境。
func TestWithoutSecretsRemovesMasterKey(t *testing.T) {
	got := WithoutSecrets([]string{
		"PATH=/usr/bin",
		MasterKeyEnvVar + "=" + strings.Repeat("ab", 32),
		"HOME=/root",
	})
	for _, e := range got {
		if strings.HasPrefix(strings.ToUpper(e), strings.ToUpper(MasterKeyEnvVar)+"=") {
			t.Fatalf("主金鑰仍留在子行程環境中: %q", e)
		}
	}
	if len(got) != 2 {
		t.Errorf("應保留 2 個變數，實際 %d: %q", len(got), got)
	}
}

// Windows 上 os.Getenv 大小寫不敏感，但字串比對不是。
// 不做不分大小寫的話，jy_secmaster_key 就是現成的繞過路徑。
func TestWithoutSecretsIsCaseInsensitive(t *testing.T) {
	for _, name := range []string{
		MasterKeyEnvVar,
		strings.ToLower(MasterKeyEnvVar),
		strings.ToUpper(MasterKeyEnvVar),
		"jy_SecMaster_Key",
	} {
		got := WithoutSecrets([]string{name + "=LEAKED"})
		if len(got) != 0 {
			t.Errorf("變數名 %q 未被移除: %q", name, got)
		}
	}
}

// 反向保護：擋太寬會讓外部 MCP 與工具子行程壞掉。
// ANTHROPIC_API_KEY 之類是子行程自己可能需要的憑證，不屬於本專案的機密。
func TestWithoutSecretsKeepsUnrelatedCredentials(t *testing.T) {
	keep := []string{
		"PATH=/usr/local/bin:/usr/bin",
		"HOME=/root",
		"TMPDIR=/tmp",
		"ANTHROPIC_API_KEY=sk-ant-third-party",
		"AWS_SECRET_ACCESS_KEY=wJalr",
		"HTTP_PROXY=http://proxy:8080",
		"GOPATH=/root/go",
		"GOCACHE=/root/.cache/go-build",
		"COLUMNS=256",
	}
	got := WithoutSecrets(keep)
	if len(got) != len(keep) {
		t.Fatalf("被誤刪 %d 個變數，應全部保留。\n傳入: %q\n傳出: %q", len(keep)-len(got), keep, got)
	}
	for i := range keep {
		if got[i] != keep[i] {
			t.Errorf("第 %d 項被改動: %q -> %q", i, keep[i], got[i])
		}
	}
}

// 名稱必須完全相符。用子字串比對會誤殺 JY_SECMASTER_KEY_BACKUP 這類變數。
func TestWithoutSecretsRequiresExactNameMatch(t *testing.T) {
	keep := []string{
		"MY_" + MasterKeyEnvVar + "=x",
		MasterKeyEnvVar + "_BACKUP=old-value",
		"X_" + MasterKeyEnvVar + "_SUFFIX=y",
	}
	got := WithoutSecrets(keep)
	if len(got) != len(keep) {
		t.Errorf("以子字串誤刪變數: %q", got)
	}
}

// 比的是變數名，不是值。值裡剛好出現同名字串不該被刪。
func TestWithoutSecretsDoesNotInspectValues(t *testing.T) {
	entry := "LOG_LINE=" + MasterKeyEnvVar + "=not-really-a-key"
	got := WithoutSecrets([]string{entry})
	if len(got) != 1 || got[0] != entry {
		t.Errorf("值內容不應影響比對，實際: %q", got)
	}
}

// 畸形項目（沒有 "="）不是具名環境變數，也不是機密，原樣保留。
func TestWithoutSecretsKeepsMalformedEntries(t *testing.T) {
	keep := []string{"NO_EQUALS_SIGN", "", "=empty-name", "A=1", MasterKeyEnvVar + "=x"}
	got := WithoutSecrets(keep)
	want := []string{"NO_EQUALS_SIGN", "", "=empty-name", "A=1"}
	if len(got) != len(want) {
		t.Fatalf("got %q, want %q", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("第 %d 項: got %q, want %q", i, got[i], want[i])
		}
	}
}

// 端到端：真的設了主金鑰，ChildEnv 的輸出就不該再含它。
func TestChildEnvFiltersInheritedMasterKey(t *testing.T) {
	t.Setenv(MasterKeyEnvVar, strings.Repeat("cd", 32))
	got := ChildEnv()
	for _, e := range got {
		if strings.EqualFold(envName(e), MasterKeyEnvVar) {
			t.Fatalf("ChildEnv 仍交出主金鑰: %q", e)
		}
	}
	// 同一個函式也必須保留一般的環境變數，否則子行程連 PATH 都沒有。
	if !hasEnvNamed(got, "PATH") && !hasEnvNamed(got, "SystemRoot") {
		t.Errorf("ChildEnv 連系統基本變數都沒保留，會讓子行程無法啟動: %q", got)
	}
}

func TestChildEnvAppendsExtras(t *testing.T) {
	t.Setenv(MasterKeyEnvVar, strings.Repeat("ef", 32))
	got := ChildEnv("GOOS=linux", "CGO_ENABLED=0", "COLUMNS=256")
	for _, want := range []string{"GOOS=linux", "CGO_ENABLED=0", "COLUMNS=256"} {
		if !hasEnv(got, want) {
			t.Errorf("附加項 %q 遺失", want)
		}
	}
}

// 就算有人在 MCP 設定的 env 裡手動塞了主金鑰，也不能把它送出去。
// 沒有任何合理的外部 MCP 需要 JySecAI 資料庫的解密權。
func TestChildEnvExtrasCannotReintroduceMasterKey(t *testing.T) {
	t.Setenv(MasterKeyEnvVar, strings.Repeat("12", 32))
	got := ChildEnv(MasterKeyEnvVar+"=injected-by-config", "GOARCH=amd64")
	for _, e := range got {
		if strings.EqualFold(envName(e), MasterKeyEnvVar) {
			t.Fatalf("額外項目把主金鑰帶回子行程環境: %q", e)
		}
	}
	if !hasEnv(got, "GOARCH=amd64") {
		t.Error("合法額外項目被一併刪除")
	}
}

// 真正「未設定」的情況下不影響任何行為 —— 沒設金鑰的部署照常運作。
// 注意不能用 t.Setenv(name, "") 代替：那會讓變數「存在但為空」，
// 那是刻意濾掉的另一種情況（見下一個測試）。
func TestChildEnvIsTransparentWhenMasterKeyUnset(t *testing.T) {
	unsetForTest(t, MasterKeyEnvVar)
	before := os.Environ()
	got := ChildEnv("TERM=dumb")
	if len(got) != len(before)+1 {
		t.Errorf("未設定主金鑰時不應刪任何變數: got %d, want %d", len(got), len(before)+1)
	}
	if !hasEnv(got, "TERM=dumb") {
		t.Error("附加項遺失")
	}
}

// 變數存在但值為空時仍然要拿掉。空值擋下來沒有副作用（沒有子行程需要
// 一個空的主金鑰），但放著不管就等於留下一個可被填入的出口。
func TestChildEnvStripsMasterKeyEvenWhenEmpty(t *testing.T) {
	t.Setenv(MasterKeyEnvVar, "")
	got := ChildEnv()
	for _, e := range got {
		if strings.EqualFold(envName(e), MasterKeyEnvVar) {
			t.Fatalf("空值的主金鑰仍被保留: %q", e)
		}
	}
}

// 空輸入不應 panic（exec 在某些路徑上會拿到空 Env）。
func TestWithoutSecretsHandlesEmptyInput(t *testing.T) {
	if got := WithoutSecrets(nil); len(got) != 0 {
		t.Errorf("WithoutSecrets(nil) = %q, want 空", got)
	}
	if got := WithoutSecrets([]string{}); len(got) != 0 {
		t.Errorf("WithoutSecrets([]) = %q, want 空", got)
	}
}

// 輸出必須是新切片，不能與來源共用 backing array，否則 append 會回頭改寫輸入。
func TestWithoutSecretsDoesNotAliasInput(t *testing.T) {
	in := []string{"A=1", "B=2"}
	out := WithoutSecrets(in)
	out = append(out, "C=3")
	if len(in) != 2 {
		t.Errorf("來源切片被回頭修改: %q", in)
	}
}

func envName(entry string) string {
	if i := strings.IndexByte(entry, '='); i > 0 {
		return entry[:i]
	}
	return ""
}

// unsetForTest 真正移除環境變數並在測試結束後還原。
// t.Setenv 只能設值，設不了「不存在」，而「不存在」正是這個測試要驗的情況。
func unsetForTest(t *testing.T, name string) {
	t.Helper()
	prev, had := os.LookupEnv(name)
	if err := os.Unsetenv(name); err != nil {
		t.Fatalf("unset %s: %v", name, err)
	}
	t.Cleanup(func() {
		if had {
			os.Setenv(name, prev)
		} else {
			os.Unsetenv(name)
		}
	})
}

func hasEnvNamed(env []string, name string) bool {
	for _, e := range env {
		if strings.EqualFold(envName(e), name) {
			return true
		}
	}
	return false
}

func hasEnv(env []string, want string) bool {
	for _, e := range env {
		if e == want {
			return true
		}
	}
	return false
}
