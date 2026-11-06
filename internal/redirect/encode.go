package redirect

import (
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
)

// 受控端點的編碼方式。
//
// 為什麼需要：把受控端點寫進目標站的 payload 位置時，明文網址會被兩種東西擋住 ——
//   - 站方（或 CDN／WAF）的規則會直接命中字串裡的網域；
//   - 瀏覽器與中間設備的日誌會把這段文字原樣記下來。
//
// 所以植入端點時可以選一種編碼形式。重要的是：**編碼只改變「寫出去的字串」，
// 不改變它指向哪裡** —— 目標站若照樣把它解回來跳轉，驗證仍然成立
// （IsReflected 會把編碼形式解回來再比對主機名）。

const (
	// PayloadEncodingNone 原樣寫入。
	PayloadEncodingNone = "none"
	// PayloadEncodingPercent 以 URL percent-encoding 寫入（https%3A%2F%2F…）。
	PayloadEncodingPercent = "percent"
	// PayloadEncodingDoublePercent 雙重 percent-encoding。
	//
	// 站方若自己解一次編碼，仍會得到一次編碼的形式；常見於會先做一次
	// url-decode 的框架或中介層。
	PayloadEncodingDoublePercent = "double_percent"
	// PayloadEncodingBase64 以標準 base64 寫入。
	PayloadEncodingBase64 = "base64"
	// PayloadEncodingBase64URL 以 URL-safe base64 寫入（無 + / = 補位）。
	PayloadEncodingBase64URL = "base64url"
	// PayloadEncodingHex 以十六進位寫入（可用於 JS 的 \x 跳脫或樣本常數）。
	PayloadEncodingHex = "hex"
	// PayloadEncodingJSUnicode 以 JS unicode 跳脫寫入（https → \u0068\u0074\u0070…）。
	PayloadEncodingJSUnicode = "js_unicode"
)

// PayloadEncodings 是所有支援的編碼方式。
func PayloadEncodings() []string {
	return []string{
		PayloadEncodingNone,
		PayloadEncodingPercent,
		PayloadEncodingDoublePercent,
		PayloadEncodingBase64,
		PayloadEncodingBase64URL,
		PayloadEncodingHex,
		PayloadEncodingJSUnicode,
	}
}

// NormalizePayloadEncoding 正規化編碼方式；空字串等同 none。
func NormalizePayloadEncoding(mode string) (string, error) {
	trimmed := strings.ToLower(strings.TrimSpace(mode))
	if trimmed == "" {
		return PayloadEncodingNone, nil
	}
	for _, candidate := range PayloadEncodings() {
		if trimmed == candidate {
			return candidate, nil
		}
	}
	return "", errors.New("不支援的編碼方式: " + mode)
}

// EncodeEndpoint 依指定的編碼方式把受控端點轉成要寫進 payload 的字串。
//
// 輸出只改變字面形式，不改變指向的位址。
func EncodeEndpoint(endpoint string, mode string) (string, error) {
	normalized, err := NormalizePayloadEncoding(mode)
	if err != nil {
		return "", err
	}
	trimmed := strings.TrimSpace(endpoint)
	if trimmed == "" {
		return "", errors.New("受控端點為空")
	}
	switch normalized {
	case PayloadEncodingNone:
		return trimmed, nil
	case PayloadEncodingPercent:
		return url.QueryEscape(trimmed), nil
	case PayloadEncodingDoublePercent:
		return url.QueryEscape(url.QueryEscape(trimmed)), nil
	case PayloadEncodingBase64:
		return base64.StdEncoding.EncodeToString([]byte(trimmed)), nil
	case PayloadEncodingBase64URL:
		return base64.RawURLEncoding.EncodeToString([]byte(trimmed)), nil
	case PayloadEncodingHex:
		return hex.EncodeToString([]byte(trimmed)), nil
	case PayloadEncodingJSUnicode:
		var b strings.Builder
		for _, r := range trimmed {
			if r > 0xFFFF {
				// 超出 BMP 的字元沒有單一 \u 跳脫，改用 \u{...}（ES6 支援）。
				b.WriteString(fmt.Sprintf("\\u{%x}", r))
				continue
			}
			b.WriteString(fmt.Sprintf("\\u%04x", r))
		}
		return b.String(), nil
	default:
		return trimmed, nil
	}
}

// DecodeEndpoint 嘗試把字串解回原始網址。
//
// 這是編碼植入的另一半：驗證時目標站若把編碼過的端點解回來跳轉，
// Location 裡會是「原樣的網址」。要判定命中，就必須把兩邊都解回來比。
//
// 會依次嘗試：原樣、percent-decode（最多兩層）、base64、hex。
// 任何一項解出來像網址就回傳；都不是就回傳原值。
func DecodeEndpoint(value string) string {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return trimmed
	}
	candidates := []string{trimmed}

	// percent-decode：最多兩層（double_percent）。
	current := trimmed
	for i := 0; i < 2; i++ {
		decoded, err := url.QueryUnescape(current)
		if err != nil || decoded == current {
			break
		}
		candidates = append(candidates, decoded)
		current = decoded
	}

	// base64（標準與 URL-safe，兩種補位形式）。
	for _, enc := range []*base64.Encoding{
		base64.StdEncoding, base64.RawStdEncoding,
		base64.URLEncoding, base64.RawURLEncoding,
	} {
		if decoded, err := enc.DecodeString(trimmed); err == nil {
			candidates = append(candidates, string(decoded))
		}
	}

	// hex。
	if len(trimmed)%2 == 0 && len(trimmed) >= 8 {
		if decoded, err := hex.DecodeString(trimmed); err == nil {
			candidates = append(candidates, string(decoded))
		}
	}

	// JS unicode 跳脫（\u0068\u0074…）。
	if decoded, ok := decodeJSUnicode(trimmed); ok {
		candidates = append(candidates, decoded)
	}

	// 回傳第一個看起來像網址的候選。
	for _, candidate := range candidates {
		if looksLikeEndpoint(candidate) {
			return candidate
		}
	}
	return trimmed
}

// jsUnicodePattern 抓 JS 的 \uXXXX 跳脫。
var jsUnicodePattern = regexp.MustCompile(`\\u([0-9a-fA-F]{4})`)

// decodeJSUnicode 把 \uXXXX 跳脫解回字元。
func decodeJSUnicode(value string) (string, bool) {
	if !strings.Contains(value, `\u`) {
		return "", false
	}
	found := false
	decoded := jsUnicodePattern.ReplaceAllStringFunc(value, func(m string) string {
		parsed, err := strconv.ParseUint(m[2:], 16, 32)
		if err != nil {
			return m
		}
		found = true
		return string(rune(parsed))
	})
	if !found {
		return "", false
	}
	return decoded, true
}

// looksLikeEndpoint 判斷字串看起來像一個 http(s) 網址。
func looksLikeEndpoint(value string) bool {
	lower := strings.ToLower(strings.TrimSpace(value))
	return strings.HasPrefix(lower, "http://") || strings.HasPrefix(lower, "https://")
}
