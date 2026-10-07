// 稽核脫敏的精準度探針。
//
// 用途：internal/audit/sanitize.go 的遮罩規則改了之後，用這個工具確認「該遮的
// 有沒有遮、不該遮的有沒有被誤傷」。sanitize_test.go 負責防回歸，這個工具負責
// 讓人**看得到**當前分類結果 —— 遮罩規則本質上是一份會隨需求增減的名單，看表格
// 比看斷言好溝通。
//
// 用法：go run ./tools/redact_probe
// 退出碼非 0 代表有欄位落在非預期的分類上。
package main

import (
	"fmt"
	"os"
	"sort"

	"jysecai/internal/audit"
)

// wrong 由 report 累積，最後由 main 檢查。
var wrong []string

var shouldMask = []string{
	// 帳號憑證
	"password", "db_password", "user_password", "pass", "passwd",
	// 金鑰
	"api_key", "user_api_key", "apikey", "client_secret", "master_key",
	"JY_SECMASTER_KEY", "private_key", "signing_key", "access_key",
	// 權杖 / 身分
	"authorization", "cookie", "jwt", "access_token", "refresh_token",
	"bot_token", "signature",
	// 大小寫與標頭寫法
	"Cookie", "Set-Cookie", "Authorization", "Bearer", "X-API-Key",
}

var shouldKeep = []string{
	// LLM 用量計量 —— 對這個平台是成本稽核的第一手資料，遮掉等於毀掉紀錄價值
	"max_tokens", "prompt_tokens", "completion_tokens", "total_tokens",
	"token_count", "tokens_used", "token_usage", "tokenizer", "token_type",
	"token_id", "prompt_token_count", "max_token_usage",
	// 其他計量 / 識別欄位
	"secret_count", "credential_type", "duration_ms", "status_code",
	"expires_in_seconds", "tools_count", "user_id", "session_id",
	"auth_method", "key_id", "sort_key", "cache_key", "signature_algorithm",
	// 明確不該被連累的
	"api_keyword", "master_keyboard", "tokenize", "task_type",
}

func probe(key string) bool {
	got := audit.SanitizeDetail(map[string]interface{}{key: "SENTINEL"}, 0)
	return got[key] == "***"
}

func main() {
	var wrong []string

	masked := report(shouldMask, true)
	kept := report(shouldKeep, false)

	fmt.Println("=== 已遮罩（應遮）===")
	for _, k := range masked {
		fmt.Println("  ", k)
	}
	fmt.Println("=== 已保留（應保留）===")
	for _, k := range kept {
		fmt.Println("  ", k)
	}

	if len(wrong) > 0 {
		fmt.Fprintln(os.Stderr, "\n分類不符預期：")
		for _, w := range wrong {
			fmt.Fprintln(os.Stderr, "  "+w)
		}
		os.Exit(1)
	}
	fmt.Printf("\n全部 %d 個欄位分類正確。\n", len(shouldMask)+len(shouldKeep))
}

func report(keys []string, wantMasked bool) []string {
	var hit []string
	for _, k := range keys {
		got := probe(k)
		if got != wantMasked {
			wrong = append(wrong, fmt.Sprintf("%s：實際=%v，預期=%v", k, got, wantMasked))
			continue
		}
		hit = append(hit, k)
	}
	sort.Strings(hit)
	return hit
}
