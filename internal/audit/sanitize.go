package audit

import (
	"encoding/json"
	"strings"
	"unicode/utf8"
)

// sensitiveKeySubstrings 會被整個遮罩的欄位名片段（比對前會轉小寫）。
//
// 收斂原則：用夠具體的名稱，不要用 auth / key 這種會誤傷的寬泛詞。
// sort_key、cache_key、key_id 這類欄位對稽核有意義，遮掉它們只會讓紀錄失去價值；
// 真正的機密欄位名幾乎都帶有下列片段之一。
var sensitiveKeySubstrings = []string{
	"password", "passwd", "api_key", "apikey", "secret", "token", "authorization",
	"credential", "private_key", "access_key",
	// 補上：Cookie / Bearer 這類傳輸層憑證，以及 C2 與本專案自身的金鑰欄位。
	// 過去漏掉 cookie 與 bearer，等於常見的 session 憑證會原樣寫進稽核紀錄。
	"cookie", "bearer", "jwt", "encryption_key", "master_key", "signing_key",
}

// SanitizeDetail redacts sensitive keys and truncates serialized size.
func SanitizeDetail(detail map[string]interface{}, maxBytes int) map[string]interface{} {
	if detail == nil {
		return nil
	}
	if maxBytes <= 0 {
		maxBytes = 8192
	}
	out := sanitizeValue("", detail)
	if m, ok := out.(map[string]interface{}); ok {
		b, _ := json.Marshal(m)
		if len(b) > maxBytes {
			return map[string]interface{}{
				"_truncated": true,
				"_preview":   truncateAtRuneBoundary(b, maxBytes),
			}
		}
		return m
	}
	return map[string]interface{}{"value": out}
}

// truncateAtRuneBoundary 截斷到不超過 maxBytes 個位元組，且不切破 UTF-8 字元。
//
// 直接用 b[:maxBytes] 會把多位元組字元切成兩半，產生無效 UTF-8。該字串之後會
// 被寫進稽核紀錄與 API 回應，無效位元組會在 json.Marshal 時被替換成 U+FFFD，
// 等於憑證內容以亂碼形式外洩且難以追查。從尾部退到最近的完整 rune 邊界即可。
func truncateAtRuneBoundary(b []byte, maxBytes int) string {
	if maxBytes >= len(b) {
		return string(b)
	}
	end := maxBytes
	// 切到最多 4 次即可跨過一個 UTF-8 字元（最長 4 bytes）。
	for i := 0; i < utf8.UTFMax && end > 0; i++ {
		if utf8.Valid(b[:end]) {
			break
		}
		end--
	}
	return string(b[:end])
}

func sanitizeValue(key string, v interface{}) interface{} {
	// 正規化後再比對：HTTP 標頭用連字號（X-API-Key、Set-Cookie），程式碼裡的
	// 欄位名用底線（api_key、set_cookie）。不統一separator 的話，「子字串命中」
	// 對最常見的憑證標頭名直接失效 —— x-api-key 不會命中 api_key。
	kl := strings.ToLower(key)
	kl = strings.ReplaceAll(kl, "-", "_")
	for _, sub := range sensitiveKeySubstrings {
		if strings.Contains(kl, sub) {
			return "***"
		}
	}
	switch t := v.(type) {
	case map[string]interface{}:
		m := make(map[string]interface{}, len(t))
		for k, val := range t {
			m[k] = sanitizeValue(k, val)
		}
		return m
	case []interface{}:
		arr := make([]interface{}, len(t))
		for i, val := range t {
			arr[i] = sanitizeValue(key, val)
		}
		return arr
	default:
		return v
	}
}
