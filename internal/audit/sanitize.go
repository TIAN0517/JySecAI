package audit

import (
	"encoding/json"
	"strings"
	"unicode/utf8"
)

// 遮罩判斷分三層，比第一版的「子字串比對」精準得多。
//
// 為什麼不能用子字串比對：`token`、`secret`、`credential` 這三個詞在稽核紀錄裡
// 最常出現的地方，其實是**計量欄位**而不是憑證欄位 —— max_tokens、prompt_tokens、
// completion_tokens、token_usage、token_count、secret_count。對一個 LLM 平台來說，
// token 用量正是成本稽核與計費對帳的第一手資料，遮掉等於把稽核紀錄最核心的價值
// 連同稽核本身一起摧毀。實測（tools/redact_probe）顯示子字串比對會連帶誤傷 12 個
// 這類欄位。
//
// 因此改成：**完整 segment 比對 + 明確的計量豁免**。
// 未列入豁免的未知欄位一律遮罩 —— 判斷錯誤時的預設方向是「多遮」而不是「漏遮」。

// sensitiveSegments 以「完整 segment」比對，不做子字串比對。
//
// 差異很關鍵：`tokenizer` 不是 `token`，`sort_key` 不是機密，`max_tokens` 的
// 複數也不是憑證。單字敏感詞一律列出（含必要的複數形），因為欄位名可能整個
// 就是憑證名。
var sensitiveSegments = map[string]bool{
	// 帳號憑證
	"password": true, "passwords": true, "passwd": true, "passphrase": true,
	"pass": true,
	// 機密 / 金鑰
	"secret": true, "secrets": true, "apikey": true, "secmaster": true,
	"signature": true,
	// 權杖 / 身分
	"token": true, "tokens": true, "jwt": true,
	"credential": true, "credentials": true,
	"authorization": true, "bearer": true,
	// 傳輸層
	"cookie": true, "cookies": true,
}

// sensitivePhrases 是會被底線拆開、但整個詞才有意義的複合名。
//
// 之所以要另外維護：`api_key` 拆成 segment 就是 `api` + `key`，而 `key` 單獨
// 不能算敏感（sort_key、cache_key、key_id 對稽核有意義）。用「詞邊界比對」
// 而非子字串比對，才不會把 `api_keyword` 這種欄位誤判成機密。
var sensitivePhrases = []string{
	"api_key", "private_key", "access_key", "secret_key", "signing_key",
	"encryption_key", "master_key",
}

// measurementSegments 說明「這個欄位記的是量，不是值」。
//
// 命中時即使欄位名含有敏感詞也不遮罩 —— 這是本檔唯一的放行條款，列在這裡的
// 每一個詞都必須是「計數／描述」語意的名詞，不能是「內容」語意。
//
// 安全性前提：稽核 detail 的鍵全部是程式碼裡的字面值（已於 internal/audit、
// internal/handler 逐處確認，無任何由請求內容反序列化而來的鍵），攻擊者無法
// 藉由命名欄位來騙過豁免。因此「程式設計師不要把機密值塞進計量欄位」是可
// 維護的契約，而不是需要假設的信任邊界。
var measurementSegments = map[string]bool{
	// 計數與統計
	"count": true, "counts": true, "usage": true, "used": true,
	"total": true, "num": true, "number": true, "len": true, "length": true,
	"size": true, "sizes": true, "bytes": true, "chars": true, "words": true,
	"lines": true, "rate": true, "ratio": true, "percent": true,
	"average": true, "avg": true, "median": true, "limit": true, "limits": true,
	"max": true, "min": true, "remaining": true,
	// LLM 專屬計量限定詞
	"prompt": true, "completion": true, "input": true, "output": true,
	"cached": true, "reasoning": true, "thinking": true,
	// 識別與描述（記的是名稱或類別，不是內容）
	"id": true, "ids": true, "type": true, "types": true,
	"name": true, "names": true, "kind": true, "variant": true,
	"version": true, "index": true, "algorithm": true, "algo": true,
	"prefix": true, "suffix": true, "enabled": true, "disabled": true,
}

// keySeparator 決定哪些字元算 segment 分隔。HTTP 標頭用連字號、程式碼用底線、
// 巢狀路徑用句點，統一成底線才能讓 X-API-Key 與 api_key 走同一條判斷。
const keySeparator = "_-_./ []:"

// normalizeKey 轉小寫並把各種分隔符號統一成底線。
func normalizeKey(key string) string {
	lower := strings.ToLower(key)
	var b strings.Builder
	b.Grow(len(lower))
	for i := 0; i < len(lower); i++ {
		c := lower[i]
		if strings.IndexByte(keySeparator, c) >= 0 {
			b.WriteByte('_')
			continue
		}
		b.WriteByte(c)
	}
	return b.String()
}

// keyIsSensitive 判斷欄位名是否需要遮罩。segments 必須是 normalized 以底線切開的結果。
//
// 順序刻意是「先找敏感，再看計量」而不是先看計量：找不到敏感詞就直接不遮，
// 計量詞只有真的命中敏感詞時才有機會放行。這樣放行條款不會變成繞過點。
func keyIsSensitive(normalized string, segments []string) bool {
	hit := false
	for _, s := range segments {
		if sensitiveSegments[s] {
			hit = true
			break
		}
	}
	if !hit {
		for _, p := range sensitivePhrases {
			if containsPhrase(normalized, p) {
				hit = true
				break
			}
		}
	}
	if !hit {
		return false
	}
	// 含有敏感詞，但整個欄位語意是「量」→ 這是 LLM 平台稽核紀錄的主要內容，
	// 遮掉等於摧毀紀錄價值。只有 measurementSegments 裡明確列出的詞能放行。
	for _, s := range segments {
		if measurementSegments[s] {
			return false
		}
	}
	return true
}

// containsPhrase 比對複合詞，只檢查**右側**詞邊界。
//
// 右邊界是必要的：否則 api_key 會命中 api_keyword、master_key 會命中 master_keyboard。
//
// 左邊界刻意不做，原因有二。其一，每個片語本身都含底線，左側本來就已被分隔符
// 或更長的單字擋住，加檢查不會多擋下任何非機密欄位 —— 實測把左邊界拿掉，
// 整組測試沒有任何一條會紅（這是突變測試 M21 找出來的）。
// 其二，它會製造**漏遮**：myapi_key 這類真憑證因為左邊接著字母而被放行。
// 遮罩的方向必須是寧可多遮不可漏遮，因此左側一律不做判斷。
func containsPhrase(normalized, phrase string) bool {
	for from := 0; ; {
		i := strings.Index(normalized[from:], phrase)
		if i < 0 {
			return false
		}
		i += from
		if end := i + len(phrase); end == len(normalized) || !isNameByte(normalized[end]) {
			return true
		}
		from = i + 1
	}
}

// isNameByte 視為「詞的一部分」的字元。底線不算在內：normalizeKey 已把分隔符
// 統一成底線，底線的兩側是獨立 segment，因此 x_api_key 必須能命中 api_key。
// 排除底線同時擋下複數形：api_keys 不會被當成 api_key。
func isNameByte(c byte) bool {
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
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
	normalized := normalizeKey(key)
	if normalized != "" && keyIsSensitive(normalized, splitKey(normalized)) {
		return "***"
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

func splitKey(normalized string) []string {
	return strings.Split(normalized, "_")
}
