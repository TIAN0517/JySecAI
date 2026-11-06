package redirect

import (
	"context"
	"io"
	"net/http"
	"strings"
	"time"
)

// 受控端點自我驗證：自動植入產出的片段「實不實」要先確認端點本身可用。
//
// 為什麼需要：把「他們注入的」換成「我們的 URL」之後，這段片段會被塞進受控站，
// 訪客的瀏覽器才會真的連回我們。但如果我們的受控端點本身：
//   - 掛了／回 5xx → 整段注入是死的，站方一眼看得出來（而且沒有回連 = 沒有證據）；
//   - 對 <script src> 回了 HTML → 瀏覽器會把它當 JS 解析，直接 syntax error；
//   - 對 <iframe src> 回了 JS → iframe 空白，功能等於沒有。
// 所以產生片段之前先探一次端點，把「這個型態配這個端點能不能用」講清楚。

const (
	// maxEndpointCheckBytes 是端點自我驗證最多讀掉的位元組數。
	maxEndpointCheckBytes = 8192
	// DefaultEndpointCheckTimeout 是端點自我驗證的預設逾時。
	DefaultEndpointCheckTimeout = 8 * time.Second
)

// EndpointCheck 是受控端點的可用性檢查結果。
type EndpointCheck struct {
	// Endpoint 是被檢查的端點。
	Endpoint string `json:"endpoint"`
	// Reachable 為 true 表示端點有回應（不是連線錯誤）。
	Reachable bool `json:"reachable"`
	// Status 是 HTTP 狀態碼（0 = 連線失敗）。
	Status int `json:"status"`
	// ContentType 是回應的 Content-Type。
	ContentType string `json:"content_type,omitempty"`
	// Location 是 3xx 的 Location 標頭。
	Location string `json:"location,omitempty"`
	// ScriptLike 為 true 表示本文看起來是 JavaScript。
	ScriptLike bool `json:"script_like"`
	// Error 是連線層的錯誤訊息。
	Error string `json:"error,omitempty"`
	// Note 是給操作者的結論說明。
	Note string `json:"note,omitempty"`
	// Suitable 為 true 表示這個端點適合放進指定型態的注入片段。
	Suitable bool `json:"suitable"`
}

// CheckEndpoint 探一次受控端點，回傳它是否可用於指定型態。
//
// kind 是注入型態（見 InjectionKind* 常數）；空字串代表不限制型態。
func CheckEndpoint(ctx context.Context, client *http.Client, endpoint string, kind string) EndpointCheck {
	check := EndpointCheck{Endpoint: strings.TrimSpace(endpoint)}
	if check.Endpoint == "" {
		check.Error = "受控端點為空"
		check.Note = "沒有受控端點就沒有可植入的網址。"
		return check
	}
	if ctx == nil {
		ctx = context.Background()
	}
	if client == nil {
		client = &http.Client{Timeout: DefaultEndpointCheckTimeout}
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, check.Endpoint, nil)
	if err != nil {
		check.Error = err.Error()
		check.Note = "受控端點網址無法解析。"
		return check
	}
	req.Header.Set("User-Agent", DefaultCrawlUserAgent)
	req.Header.Set("Accept", "*/*")

	resp, err := client.Do(req)
	if err != nil {
		check.Error = err.Error()
		check.Note = "連不到受控端點：植入後不會有回連，也拿不到證據。"
		return check
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(io.LimitReader(resp.Body, maxEndpointCheckBytes))
	check.Reachable = true
	check.Status = resp.StatusCode
	check.ContentType = resp.Header.Get("Content-Type")
	check.Location = resp.Header.Get("Location")
	check.ScriptLike = looksLikeScript(check.ContentType, body)
	check.Suitable, check.Note = endpointFitsKind(check, kind)
	return check
}

// endpointFitsKind 判斷端點是否適合某個注入型態，並給出結論說明。
func endpointFitsKind(check EndpointCheck, kind string) (bool, string) {
	switch strings.ToLower(strings.TrimSpace(kind)) {
	case InjectionKindScriptSrc:
		if check.Status >= 500 {
			return false, "端點回 5xx：<script src> 會拿到錯誤頁，站方看得出來。"
		}
		if !check.ScriptLike {
			return false, "端點回的不是 JavaScript：<script src> 會直接 syntax error，注入等於無效。"
		}
		return true, "端點會回 JavaScript：可以放進 <script src>。"
	case InjectionKindIframeSrc:
		if check.Status >= 500 {
			return false, "端點回 5xx：iframe 只會顯示錯誤頁。"
		}
		return true, "端點有回應：可以放進 <iframe src>（內容不會被瀏覽器當成 JS 解析）。"
	case InjectionKindMetaRefresh:
		if check.Status >= 400 && check.Status < 500 {
			return false, "端點回 4xx：meta refresh 會把訪客帶到錯誤頁，不會有回連紀錄以外的效果。"
		}
		return true, "端點有回應：可以放進 meta refresh，訪客會被帶走。"
	case InjectionKindFormAction:
		if check.Status >= 400 && check.Status < 500 {
			return false, "端點回 4xx：表單送出會直接失敗。"
		}
		return true, "端點有回應：可以放進 <form action>。"
	case InjectionKindLinkHref, InjectionKindJSString:
		if check.Status >= 500 {
			return false, "端點回 5xx：導向過去會看到錯誤頁。"
		}
		return true, "端點有回應：可以放進連結或 JS 字串。"
	default:
		if check.Status >= 500 {
			return false, "端點回 5xx：植入之後沒有回連。"
		}
		return true, "端點有回應。"
	}
}

// looksLikeScript 判斷回應看起來是不是 JavaScript。
//
// 判斷依據：Content-Type 明確是 JS，或本文看起來像 JS（而且不是 HTML）。
func looksLikeScript(contentType string, body []byte) bool {
	lower := strings.ToLower(strings.TrimSpace(contentType))
	if strings.Contains(lower, "javascript") || strings.Contains(lower, "ecmascript") {
		return true
	}
	text := strings.TrimSpace(string(body))
	if text == "" {
		return false
	}
	if strings.HasPrefix(strings.ToLower(text), "<!doctype html") || strings.HasPrefix(strings.ToLower(text), "<html") {
		return false
	}
	// 明確的 JS 特徵：assignment、function、window.、document.、location.、=>。
	for _, marker := range []string{"function ", "window.", "document.", "location.", "var ", "const ", "let ", "=>"} {
		if strings.Contains(text, marker) {
			return true
		}
	}
	return false
}
