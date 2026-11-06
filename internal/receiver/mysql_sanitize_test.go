package receiver

import (
	"strings"
	"testing"
	"unicode/utf8"
)

// TestSanitizeArgsReplacesInvalidUTF8 擋住非法位元組讓整批匯入被拒。
//
// 生產資料庫的證據欄位確實有截斷的多位元組字元（例如只存了「\xE6\x8E」
// 三個位元組的前兩個）。MySQL 的 utf8mb4 會以 Error 1366 (Incorrect string
// value) 拒收整筆 —— 單一筆壞資料就足以讓 4359 筆的匯入全部失敗。
func TestSanitizeArgsReplacesInvalidUTF8(t *testing.T) {
	broken := "證據片段 " + string([]byte{0xE6, 0x8E}) + " 結尾"
	if utf8.ValidString(broken) {
		t.Fatal("測試字串本來就該是非法 UTF-8")
	}
	args := sanitizeArgs([]any{broken, "正常字串", 42})
	got, ok := args[0].(string)
	if !ok {
		t.Fatalf("參數型別被改變: %T", args[0])
	}
	if !utf8.ValidString(got) {
		t.Fatalf("消毒後仍是非法 UTF-8: %q", got)
	}
	if !strings.Contains(got, "證據片段") {
		t.Fatalf("合法片段不該被破壞: %q", got)
	}
	if args[1].(string) != "正常字串" {
		t.Fatalf("正常字串不該被改動: %q", args[1])
	}
	if args[2].(int) != 42 {
		t.Fatalf("非字串參數不該被改動: %v", args[2])
	}
}
