package mcp

import (
	"strings"
	"testing"

	"jysecai/internal/secretstore"
)

// 外部 MCP 是第三方行程。它拿到主金鑰就等於拿到整個機密欄位資料庫的解密權，
// 落盤加密形同虛設。這組測試釘住 stdio 子行程的環境建構路徑：把
// secretstore.WithoutSecrets 從 stdioSubprocessEnv 拿掉，這裡就會紅。

func TestStdioSubprocessEnvDropsInheritedMasterKey(t *testing.T) {
	t.Setenv(secretstore.MasterKeyEnvVar, strings.Repeat("ab", 32))
	got := stdioSubprocessEnv(nil)
	for _, e := range got {
		if strings.EqualFold(envVarName(e), secretstore.MasterKeyEnvVar) {
			t.Fatalf("主金鑰被交給外部 MCP 子行程: %q", e)
		}
	}
}

// 無條件回傳：呼叫端若在設定為空時把 cmd.Env 留成 nil，exec 會隱式繼承整包
// os.Environ()，主金鑰照樣外流。這個測試擋的就是那條退路。
func TestStdioSubprocessEnvNeverReturnsNil(t *testing.T) {
	for _, tc := range []struct {
		name  string
		extra map[string]string
	}{
		{"nil", nil},
		{"空 map", map[string]string{}},
		{"有設定", map[string]string{"FOO": "bar"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got := stdioSubprocessEnv(tc.extra)
			if got == nil {
				t.Fatal("回傳 nil：cmd.Env 留 nil 等於隱式繼承 os.Environ()")
			}
			if len(got) == 0 {
				t.Fatal("回傳空切片：子行程連 PATH 都沒有，無法啟動")
			}
		})
	}
}

// 就算有人在設定檔的 env 裡手動塞了主金鑰，也不能送出去。
// 沒有任何合理的外部 MCP 需要 JySecAI 資料庫的解密權。
func TestStdioSubprocessEnvDropsConfiguredMasterKey(t *testing.T) {
	t.Setenv(secretstore.MasterKeyEnvVar, strings.Repeat("cd", 32))
	got := stdioSubprocessEnv(map[string]string{
		secretstore.MasterKeyEnvVar: "injected-by-config",
		"MCP_TOKEN":                 "legit-token",
	})
	for _, e := range got {
		if strings.EqualFold(envVarName(e), secretstore.MasterKeyEnvVar) {
			t.Fatalf("設定檔塞入的主金鑰仍被送出: %q", e)
		}
	}
	if !containsEnv(got, "MCP_TOKEN=legit-token") {
		t.Error("合法的設定項被一併刪除，外部 MCP 會啟動失敗")
	}
}

// 反向保護：擋太寬會讓外部 MCP 壞掉。它們可能真的需要自己的憑證。
func TestStdioSubprocessEnvKeepsLegitimateVars(t *testing.T) {
	t.Setenv(secretstore.MasterKeyEnvVar, strings.Repeat("ef", 32))
	got := stdioSubprocessEnv(map[string]string{
		"ANTHROPIC_API_KEY": "sk-ant-third-party",
		"CUSTOM_FLAG":       "on",
	})
	if !containsEnv(got, "ANTHROPIC_API_KEY=sk-ant-third-party") {
		t.Error("子行程自己的憑證被誤刪")
	}
	if !containsEnv(got, "CUSTOM_FLAG=on") {
		t.Error("設定項未帶入子行程")
	}
	// 基本系統變數必須仍在，否則 exec 起不來。
	if !containsEnvNamed(got, "PATH") && !containsEnvNamed(got, "SystemRoot") {
		t.Errorf("連系統基本變數都沒保留: %q", got)
	}
}

func envVarName(entry string) string {
	if i := strings.IndexByte(entry, '='); i > 0 {
		return entry[:i]
	}
	return ""
}

func containsEnv(env []string, want string) bool {
	for _, e := range env {
		if e == want {
			return true
		}
	}
	return false
}

func containsEnvNamed(env []string, name string) bool {
	for _, e := range env {
		if strings.EqualFold(envVarName(e), name) {
			return true
		}
	}
	return false
}
