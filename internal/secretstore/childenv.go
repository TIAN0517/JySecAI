package secretstore

import (
	"os"
	"strings"
)

// SecretEnvVars 列出「不得傳給子行程」的環境變數名稱。
//
// 這是本專案自己放進環境的機密清單，不是常見憑證變數的通用清單。通用清單
// （AWS_SECRET_ACCESS_KEY、ANTHROPIC_API_KEY 之類）不能在這裡擋：外部 MCP
// 或工具子行程可能正是靠它們才能運作，擋掉等於刪掉既有功能。職責邊界只到
// 「我們寫進環境的機密不外流」。
var SecretEnvVars = []string{
	MasterKeyEnvVar,
}

// ChildEnv 產生子行程環境：沿用目前行程的環境、附加 extra，並濾掉 SecretEnvVars。
//
// 用它取代 os.Environ()。主金鑰設定在環境變數後，任何 exec.Command 都會把它
// 一起交給子行程 —— 對外部 MCP 這種第三方行程來說，等於交出整個機密欄位
// 資料庫的解密權，落盤加密等於沒做。
func ChildEnv(extra ...string) []string {
	// os.Environ() 每次回傳新切片，append 不會寫到共用 backing array。
	return WithoutSecrets(append(os.Environ(), extra...))
}

// WithoutSecrets 從環境變數陣列中移除 SecretEnvVars 指定的項目，其餘原樣保留。
//
// 比對不分大小寫：Windows 的環境變數名稱大小寫不敏感，os.Getenv 會把
// jy_secmaster_key 當成 JY_SECMASTER_KEY，但字串比對不會。漏掉這個差異，
// 等於在 Windows 上可以用大小寫變體把主金鑰遞出去。
//
// 沒有 "=" 的項目原樣保留：它不可能是具名的機密，也不是合法的環境變數。
func WithoutSecrets(env []string) []string {
	out := make([]string, 0, len(env))
	for _, entry := range env {
		if isSecretEnvName(entry) {
			continue
		}
		out = append(out, entry)
	}
	return out
}

func isSecretEnvName(entry string) bool {
	i := strings.IndexByte(entry, '=')
	if i <= 0 {
		return false
	}
	for _, name := range SecretEnvVars {
		if strings.EqualFold(entry[:i], name) {
			return true
		}
	}
	return false
}
