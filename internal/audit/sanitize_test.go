package audit

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
	"unicode/utf8"
)

// SanitizeDetail 是稽核紀錄寫入前的最後一道防線：detail 會被原樣存進資料庫並
// 透過 API 回傳，任何沒被遮罩的憑證都會變成長期有效的外洩來源。
// internal/audit 原本沒有任何測試。

func TestSanitizeDetailMasksSensitiveKeys(t *testing.T) {
	// 逐項列舉，而非只抽樣：新增片段時若忘了對應測試，這裡會先失效。
	keys := []string{
		"password", "passwd", "api_key", "apikey", "secret", "token",
		"authorization", "credential", "private_key", "access_key",
		"cookie", "bearer", "jwt", "encryption_key", "master_key", "signing_key",
	}
	for _, key := range keys {
		t.Run(key, func(t *testing.T) {
			got := SanitizeDetail(map[string]interface{}{key: "SENTINEL-VALUE"}, 0)
			v, ok := got[key]
			if !ok {
				t.Fatalf("欄位 %q 被整個刪掉了，應保留欄位並遮罩內容", key)
			}
			if v == "SENTINEL-VALUE" {
				t.Fatalf("欄位 %q 未被遮罩", key)
			}
		})
	}
}

// 比對不分大小寫：HTTP 標頭是 Cookie / Authorization，程式碼裡常寫成 cookie。
func TestSanitizeDetailMaskIsCaseInsensitive(t *testing.T) {
	for _, key := range []string{"Cookie", "COOKIE", "Set-Cookie", "Authorization", "Bearer"} {
		got := SanitizeDetail(map[string]interface{}{key: "SENTINEL"}, 0)
		if got[key] == "SENTINEL" {
			t.Errorf("欄位 %q 未被遮罩", key)
		}
	}
}

// 遮罩要能擋下以敏感詞夾帶的情況，例如 x-api-key、user_password。
func TestSanitizeDetailMasksSubstringMatches(t *testing.T) {
	for _, key := range []string{
		"x-api-key", "user_password", "db_password", "bot_token",
		"encryption_key", "JY_SECMASTER_KEY", "old_cookie_jar",
	} {
		got := SanitizeDetail(map[string]interface{}{key: "SENTINEL"}, 0)
		if got[key] == "SENTINEL" {
			t.Errorf("欄位 %q 未被遮罩", key)
		}
	}
}

// 反向保護：稽核紀錄的價值在於保留非機密脈絡。全被遮掉等於沒有稽核。
func TestSanitizeDetailKeepsNonSensitiveFields(t *testing.T) {
	detail := map[string]interface{}{
		"action":      "c2.task.create",
		"user_id":     "u_123",
		"session_id":  "s_abc",
		"sort_key":    "created_at",
		"cache_key":   "v1",
		"key_id":      "k_1",
		"auth_method": "password", // 值含 password 沒關係，欄位名才重要
		"task_type":   "ls",
		"duration_ms": float64(42),
		"ok":          true,
		"attempts":    float64(3),
		"status_code": float64(200),
	}
	got := SanitizeDetail(detail, 0)
	for k, want := range detail {
		if got[k] != want {
			t.Errorf("欄位 %q = %v, want %v（非機密欄位不應被遮罩）", k, got[k], want)
		}
	}
}

// 反向保護（LLM 專屬）：token 用量是這個平台成本稽核的第一手資料。
//
// 第一版用「子字串比對」時，下列欄位全部被遮成 ***，等於把稽核紀錄最核心的
// 內容連同稽核本身一起摧毀。這個測試就是為了擋住那次回退。
func TestSanitizeDetailKeepsLLMUsageMetrics(t *testing.T) {
	detail := map[string]interface{}{
		"max_tokens":         float64(4096),
		"prompt_tokens":      float64(120),
		"completion_tokens":  float64(880),
		"total_tokens":       float64(1000),
		"token_count":        float64(1000),
		"tokens_used":        float64(1000),
		"token_usage":        map[string]interface{}{"input": 120.0, "output": 880.0},
		"tokenizer":          "jy-tokenizer-v3",
		"token_type":         "bearer",
		"token_id":           "tok_123",
		"secret_count":       float64(0),
		"credential_type":    "api_key",
		"prompt_token_count": float64(120),
		"max_token_usage":    float64(4096),
	}
	got := SanitizeDetail(detail, 0)
	for k, want := range detail {
		if toStr(got[k]) == "***" {
			t.Errorf("計量欄位 %q 被遮罩：稽核紀錄會失去用量與成本對帳能力", k)
		}
		if !reflect.DeepEqual(got[k], want) {
			t.Errorf("欄位 %q = %#v, want %#v", k, got[k], want)
		}
	}
	// 巢狀的用量明細也必須原樣保留。
	usage := got["token_usage"].(map[string]interface{})
	if usage["input"] != 120.0 || usage["output"] != 880.0 {
		t.Errorf("巢狀 token_usage 被破壞: %#v", usage)
	}
}

// 計量豁免不能變成繞過點：同樣帶著計量詞的憑證欄位仍必須遮。
func TestSanitizeDetailMasksCredentialsDespiteMeasurementWord(t *testing.T) {
	for _, key := range []string{
		"token", "tokens", "access_token", "refresh_token", "bot_token",
		"password", "user_password", "client_secret", "jwt",
		"signature", "credential", "api_key",
	} {
		got := SanitizeDetail(map[string]interface{}{key: "SENTINEL"}, 0)
		if toStr(got[key]) != "***" {
			t.Errorf("欄位 %q 未被遮罩: %#v", key, got[key])
		}
	}
}

// 複合詞比對必須有右側詞邊界，否則 api_keyword 這類欄位會被誤判成機密。
func TestSanitizeDetailPhraseMatchRespectsWordBoundary(t *testing.T) {
	detail := map[string]interface{}{
		"api_keyword":     "關鍵字", // 不是機密
		"master_keyboard": "鍵盤",  // 不是機密
		"sort_key":        "created_at",
	}
	got := SanitizeDetail(detail, 0)
	for k, want := range detail {
		if toStr(got[k]) == "***" {
			t.Errorf("欄位 %q 被誤判為機密", k)
		}
		if !reflect.DeepEqual(got[k], want) {
			t.Errorf("欄位 %q = %#v, want %#v", k, got[k], want)
		}
	}
	// 但確實是機密的複合詞，含底線前後綴都要命中。
	for _, key := range []string{
		"api_key", "x-api-key", "user_api_key", "JY_SECMASTER_KEY",
		// 左邊界刻意不判斷：myapi_key 左側接著字母，但它確實是憑證，
		// 放行就是漏遮（見 containsPhrase 的說明）。
		"myapi_key",
	} {
		got := SanitizeDetail(map[string]interface{}{key: "SENTINEL"}, 0)
		if toStr(got[key]) != "***" {
			t.Errorf("欄位 %q 未被遮罩", key)
		}
	}
}

// 遮罩與否只看欄位名，值本身帶敏感字串不影響判斷。
func TestSanitizeDetailMaskingDecidesOnKeyNotValue(t *testing.T) {
	got := SanitizeDetail(map[string]interface{}{
		"token_usage": "access_token=abc", // 值像憑證，但欄位名是計量
		"auth_method": "password",
	}, 0)
	if got["token_usage"] != "access_token=abc" {
		t.Errorf("計量欄位被遮罩: %#v", got["token_usage"])
	}
}

func TestSanitizeDetailMasksNestedMaps(t *testing.T) {
	detail := map[string]interface{}{
		"request": map[string]interface{}{
			"method": "POST",
			"headers": map[string]interface{}{
				"Cookie":        "session=SENTINEL",
				"Content-Type":  "application/json",
				"Authorization": "Bearer SENTINEL",
			},
		},
	}
	out := SanitizeDetail(detail, 0)
	headers := out["request"].(map[string]interface{})["headers"].(map[string]interface{})
	if headers["Cookie"] == "session=SENTINEL" {
		t.Error("巢狀的 Cookie 未被遮罩")
	}
	if headers["Authorization"] == "Bearer SENTINEL" {
		t.Error("巢狀的 Authorization 未被遮罩")
	}
	if headers["Content-Type"] != "application/json" {
		t.Error("非機密的 Content-Type 不應被遮罩")
	}
	if out["request"].(map[string]interface{})["method"] != "POST" {
		t.Error("非機密的 method 不應被遮罩")
	}
}

func TestSanitizeDetailMasksInsideSlices(t *testing.T) {
	detail := map[string]interface{}{
		"targets": []interface{}{
			map[string]interface{}{"host": "10.0.0.1", "token": "SENTINEL"},
			map[string]interface{}{"host": "10.0.0.2", "token": "SENTINEL2"},
		},
	}
	out := SanitizeDetail(detail, 0)
	for i, item := range out["targets"].([]interface{}) {
		m := item.(map[string]interface{})
		if strings.Contains(toStr(m["token"]), "SENTINEL") {
			t.Errorf("targets[%d].token 未被遮罩: %v", i, m["token"])
		}
		if m["host"] == "" {
			t.Errorf("targets[%d].host 被誤遮罩", i)
		}
	}
}

// 整個欄位就是敏感詞時，連值一起遮掉（含巢狀結構）。
func TestSanitizeDetailMasksWholeSensitiveBranch(t *testing.T) {
	got := SanitizeDetail(map[string]interface{}{
		"credentials": map[string]interface{}{"user": "admin", "pass": "x"},
	}, 0)
	if v, _ := got["credentials"].(string); v != "***" {
		t.Errorf("整個 credentials 分支未被遮罩: %#v", got["credentials"])
	}
}

func TestSanitizeDetailNilReturnsNil(t *testing.T) {
	if got := SanitizeDetail(nil, 0); got != nil {
		t.Errorf("SanitizeDetail(nil) = %#v, want nil", got)
	}
}

func TestSanitizeDetailTruncatesOversizedPayload(t *testing.T) {
	detail := map[string]interface{}{"blob": strings.Repeat("A", 5000)}
	got := SanitizeDetail(detail, 512)
	tr, ok := got["_truncated"]
	if !ok || tr != true {
		t.Fatalf("超量內容未被標記截斷: %#v", got)
	}
	preview := toStr(got["_preview"])
	if len(preview) > 512 {
		t.Errorf("preview 長度 = %d，超過 maxBytes 512", len(preview))
	}
	if !strings.Contains(preview, "A") {
		t.Errorf("preview 未保留任何內容: %q", preview)
	}
}

// 核心修正：按位元組截斷會切破多位元組字元，產生無效 UTF-8。
// 那段亂碼之後會被寫進稽核紀錄與 API 回應，等於憑證以亂碼形式外洩。
func TestSanitizeDetailTruncationKeepsValidUTF8(t *testing.T) {
	// 每個中文字元 3 bytes，刻意讓切點落在字元中間。
	detail := map[string]interface{}{"note": strings.Repeat("機敏資料", 2000)}
	for _, maxBytes := range []int{1, 2, 3, 4, 5, 7, 11, 16, 31, 64, 100, 255, 512} {
		got := SanitizeDetail(detail, maxBytes)
		preview := toStr(got["_preview"])
		if len(preview) > maxBytes {
			t.Errorf("maxBytes=%d：preview 長度 %d 超出上限", maxBytes, len(preview))
		}
		if !utf8.ValidString(preview) {
			t.Errorf("maxBytes=%d：preview 含無效 UTF-8：%q", maxBytes, preview)
		}
		// 整份輸出仍必須能正常序列化。
		if _, err := json.Marshal(got); err != nil {
			t.Errorf("maxBytes=%d：輸出無法序列化: %v", maxBytes, err)
		}
	}
}

// emoji 是 4 bytes 的 rune，最容易在切分時被破壞。
func TestSanitizeDetailTruncationHandlesFourByteRunes(t *testing.T) {
	detail := map[string]interface{}{"note": strings.Repeat("🔑", 500)}
	for _, maxBytes := range []int{3, 4, 5, 6, 7, 8, 9, 13, 17} {
		got := SanitizeDetail(detail, maxBytes)
		preview := toStr(got["_preview"])
		if !utf8.ValidString(preview) {
			t.Errorf("maxBytes=%d：preview 含無效 UTF-8", maxBytes)
		}
	}
}

func TestSanitizeDetailUsesDefaultLimitWhenNonPositive(t *testing.T) {
	detail := map[string]interface{}{"blob": strings.Repeat("A", 20000)}
	for _, maxBytes := range []int{0, -1, -8192} {
		got := SanitizeDetail(detail, maxBytes)
		if _, ok := got["_truncated"]; !ok {
			t.Errorf("maxBytes=%d 未套用預設上限", maxBytes)
		}
	}
	// 預設上限 8192：小於它的內容不該被截斷。
	small := SanitizeDetail(map[string]interface{}{"blob": strings.Repeat("A", 100)}, 0)
	if _, ok := small["_truncated"]; ok {
		t.Error("小內容不應被截斷")
	}
}

func TestTruncateAtRuneBoundary(t *testing.T) {
	cases := []struct {
		in       string
		maxBytes int
	}{
		{"abc", 10}, // 不需截斷
		{"abc", 3},  // 剛好
		{"機密", 3},   // 剛好一個字
		{"機密", 4},   // 切在第二個字中間 -> 保留第一個字
		{"機密", 1},   // 切在第一個字中間 -> 退到 0
		{"🔑x", 4},   // 剛好一個 emoji
		{"🔑x", 3},   // 切在 emoji 中間 -> 退到 0
		{"🔑x", 5},   // emoji + x
	}
	for _, tc := range cases {
		got := truncateAtRuneBoundary([]byte(tc.in), tc.maxBytes)
		if len(got) > tc.maxBytes {
			t.Errorf("truncate(%q, %d) = %q，超出上限", tc.in, tc.maxBytes, got)
		}
		if !utf8.ValidString(got) {
			t.Errorf("truncate(%q, %d) = %q，無效 UTF-8", tc.in, tc.maxBytes, got)
		}
		if tc.maxBytes < len(tc.in) && got == tc.in {
			t.Errorf("truncate(%q, %d) 未截斷", tc.in, tc.maxBytes)
		}
	}
}

func toStr(v interface{}) string {
	s, _ := v.(string)
	return s
}
