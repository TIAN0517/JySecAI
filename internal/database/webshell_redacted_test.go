package database

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestWebShellConnectionRedactedHidesPassword(t *testing.T) {
	conn := WebShellConnection{
		ID:       "ws-1",
		URL:      "http://target/shell.php",
		Password: "super-secret-webshell-key",
		Type:     "php",
		Method:   "post",
	}
	got := conn.Redacted()
	if got.Password != RedactedSecretPlaceholder {
		t.Errorf("密碼未遮罩：got %q, want %q", got.Password, RedactedSecretPlaceholder)
	}
	// 其餘欄位必須完整保留，否則設定頁會失去可用性
	if got.ID != conn.ID || got.URL != conn.URL || got.Type != conn.Type || got.Method != conn.Method {
		t.Errorf("遮罩時遺失非機密欄位：%+v", got)
	}
	// 原始值不得被就地修改
	if conn.Password != "super-secret-webshell-key" {
		t.Errorf("Redacted() 改動了原物件的密碼：%q", conn.Password)
	}
}

func TestWebShellConnectionRedactedEmptyPasswordStaysEmpty(t *testing.T) {
	conn := WebShellConnection{ID: "ws-2", URL: "http://target/shell.php"}
	if got := conn.Redacted(); got.Password != "" {
		t.Errorf("未設定密碼應保持空字串，實際 %q", got.Password)
	}
}

func TestWebShellConnectionRedactedJSONCarriesNoSecret(t *testing.T) {
	const secret = "S3CRET-WEBSHELL-KEY"
	list := []WebShellConnection{
		{ID: "a", URL: "http://a", Password: secret},
		{ID: "b", URL: "http://b", Password: secret},
	}
	raw, err := json.Marshal(RedactedWebshellConnections(list))
	if err != nil {
		t.Fatalf("序列化失敗: %v", err)
	}
	if strings.Contains(string(raw), secret) {
		t.Fatalf("序列化結果仍含原始密碼：%s", string(raw))
	}
}

func TestRedactedWebshellConnectionsNilBecomesEmptySlice(t *testing.T) {
	got := RedactedWebshellConnections(nil)
	if got == nil {
		t.Fatal("nil 輸入應回傳空切片，否則 JSON 會變成 null 而非 []")
	}
	raw, err := json.Marshal(got)
	if err != nil {
		t.Fatalf("序列化失敗: %v", err)
	}
	if string(raw) != "[]" {
		t.Errorf("期望 []，實際 %s", string(raw))
	}
}
