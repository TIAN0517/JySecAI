// Package redirect 提供「受控跳轉（回連）端點」的正規化與探測邏輯。
//
// 這個包刻意保持純函式、零外部相依：它只負責把操作者設定的端點清單整理乾淨、
// 把跳轉參數組進目標 URL、以及判斷 Location 是否真的指向受控端點。
// 送出請求的策略（HTTP client、逾時）由呼叫端決定，探測本身在 Probe()。
package redirect

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// defaultRedirectParams 是常見的「下一頁跳轉」參數名。
//
// 順序固定：url、redirect 這類最常見的排前面，罕見的排後面。
// 呼叫端沒指定參數名時，會依這個順序逐一嘗試，先命中者為準。
var defaultRedirectParams = []string{
	"url",
	"redirect",
	"redirect_uri",
	"returnUrl",
	"returnurl",
	"ReturnUrl",
	"next",
	"targeturl",
	"target",
	"dest",
	"destination",
	"continue",
	"redirect_to",
	"goto",
	"link",
	"u",
}

// DefaultProbeTimeout 是 Probe 沒有指定逾時時的預設上限。
const DefaultProbeTimeout = 10 * time.Second

// maxProbeBodyBytes 是探測時最多讀掉的回應本文量。
//
// 只讀一小段就足夠確認連線與標頭；讀完也讓 keep-alive 連線可以正常回收。
const maxProbeBodyBytes = 4096

// NormalizeURLs 整理受控端點清單：去空白、丟掉沒有 http/https scheme 的項目、
// 依輸入順序去重。
//
// 輸出對同一組輸入永遠相同（map 只用來查重，不參與輸出順序），
// 因此同一份設定重複載入不會讓端點順序漂移。
func NormalizeURLs(raw []string) []string {
	if len(raw) == 0 {
		return nil
	}
	out := make([]string, 0, len(raw))
	seen := make(map[string]struct{}, len(raw))
	for _, item := range raw {
		value := strings.TrimSpace(item)
		if value == "" {
			continue
		}
		parsed, err := url.Parse(value)
		if err != nil {
			continue
		}
		if parsed.Scheme != "http" && parsed.Scheme != "https" {
			continue
		}
		if parsed.Host == "" {
			continue
		}
		if _, dup := seen[value]; dup {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	if len(out) == 0 {
		return nil
	}
	return out
}

// RedirectParamNames 回傳常見跳轉參數名的固定清單（副本；呼叫端可安全修改）。
func RedirectParamNames() []string {
	out := make([]string, len(defaultRedirectParams))
	copy(out, defaultRedirectParams)
	return out
}

// IsRedirectParam 判斷查詢參數名是否屬於常見跳轉參數（大小寫不敏感）。
//
// 巡站時用它挑出「帶著跳轉參數的連結」：那通常就是站上真的存在的跳轉入口。
func IsRedirectParam(name string) bool {
	trimmed := strings.TrimSpace(name)
	if trimmed == "" {
		return false
	}
	for _, candidate := range defaultRedirectParams {
		if strings.EqualFold(candidate, trimmed) {
			return true
		}
	}
	return false
}

// OwnRedirectParams 回傳目標網址「本來就帶著」的跳轉參數名（依固定順序）。
//
// 這是「站點本來跳轉的方法」：目標 URL 的 query 裡本來就有這個參數，代表
// 站上真的有這條跳轉路徑 —— 複測時應該沿用它，而不是用猜的參數名盲試。
//
// 與 DetectRedirectParams 的差別：那個函式回傳「要試的全部候選」（含猜的），
// 這個只回傳「站上本來就有的」。
func OwnRedirectParams(target string) []string {
	present := map[string]bool{}
	if parsed, err := url.Parse(strings.TrimSpace(target)); err == nil {
		for key := range parsed.Query() {
			present[key] = true
		}
	}
	out := make([]string, 0, len(defaultRedirectParams))
	for _, name := range defaultRedirectParams {
		if present[name] {
			out = append(out, name)
		}
	}
	return out
}

// DetectRedirectParams 回傳呼叫端沒指定參數名時要試的跳轉參數。//
// target 既有 query 裡已經出現的參數會排前面 —— 那通常就是真正的參數名；
// 其餘依固定順序補在後面。輸出順序對同一組輸入固定。
func DetectRedirectParams(target string) []string {
	present := map[string]bool{}
	if parsed, err := url.Parse(strings.TrimSpace(target)); err == nil {
		for key := range parsed.Query() {
			present[key] = true
		}
	}
	out := make([]string, 0, len(defaultRedirectParams))
	for _, name := range defaultRedirectParams {
		if present[name] {
			out = append(out, name)
		}
	}
	for _, name := range defaultRedirectParams {
		if !present[name] {
			out = append(out, name)
		}
	}
	return out
}

// BuildProbeURL 把 payload 設到 target 的 query 參數上。
//
// 既有 query 與 fragment 都會保留；target 本來就有該參數時改寫它的值。
// target 不是合法的 http/https URL 時回傳錯誤。
func BuildProbeURL(target string, param string, payload string) (string, error) {
	trimmed := strings.TrimSpace(target)
	if trimmed == "" {
		return "", errors.New("目标 URL 为空")
	}
	name := strings.TrimSpace(param)
	if name == "" {
		return "", errors.New("跳转参数名为空")
	}
	parsed, err := url.Parse(trimmed)
	if err != nil {
		return "", fmt.Errorf("目标 URL 解析失败: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return "", fmt.Errorf("目标 URL 仅支持 http/https，当前为 %q", parsed.Scheme)
	}
	if parsed.Host == "" {
		return "", errors.New("目标 URL 缺少主机名")
	}
	query := parsed.Query()
	query.Set(name, payload)
	parsed.RawQuery = query.Encode()
	return parsed.String(), nil
}

// ExtractLocation 取回 Location 標頭值（大小寫不敏感）。
func ExtractLocation(header http.Header) string {
	if len(header) == 0 {
		return ""
	}
	if value := strings.TrimSpace(header.Get("Location")); value != "" {
		return value
	}
	// 直接塞進 map 的非正規化 key（例如 "location"）Get() 抓不到，這裡補掃一次。
	for key, values := range header {
		if !strings.EqualFold(key, "Location") {
			continue
		}
		for _, value := range values {
			if trimmed := strings.TrimSpace(value); trimmed != "" {
				return trimmed
			}
		}
	}
	return ""
}

// IsReflected 判斷 Location 是否真的指向受控端點的主機。
//
// 判定方式是比较「主機名」，不是字串包含：
//   - payload 與 location 都可以是絕對 URL 或 protocol-relative（//host/path）。
//   - userinfo 會被剝掉：https://user@evil.example/ 與 https://evil.example/ 是同一個主機。
//   - 主機名必須完全相同：victim.com.evil.example 不算 evil.example（避免後綴比對誤判）。
//   - 受害者自己的主機不算命中。
//
// location 是相對路徑（沒有主機）時，只有在受控端點字面出現在 Location 內
// 才算命中；純粹相對跳轉不會被誤判成回連。
//
// payload 可能是編碼過的（見 encode.go）：比對前會先解回原樣，
// 因此「植入的是編碼形式、目標站解回來跳轉」也算命中。
func IsReflected(location string, payload string) bool {
	loc := strings.TrimSpace(location)
	pl := strings.TrimSpace(payload)
	if loc == "" || pl == "" {
		return false
	}
	payloadHost := extractHost(DecodeEndpoint(pl))
	locHost := extractHost(DecodeEndpoint(loc))
	if payloadHost == "" {
		// payload 本身不是可解析的主機，退而比對字面量。
		return strings.Contains(loc, pl)
	}
	if locHost != "" {
		return payloadHost == locHost
	}
	return strings.Contains(loc, payloadHost)
}

// extractHost 取出 URL 的主機名；沒有主機（相對路徑等）時回傳空字串。
func extractHost(raw string) string {
	value := strings.TrimSpace(raw)
	if value == "" {
		return ""
	}
	parsed, err := url.Parse(value)
	if err != nil {
		return ""
	}
	if parsed.Host == "" {
		return ""
	}
	return normalizeHost(parsed.Hostname())
}

// normalizeHost 主機名正規化：DNS 不分大小寫，結尾的點是同一台主機。
func normalizeHost(host string) string {
	normalized := strings.ToLower(strings.TrimSpace(host))
	return strings.TrimSuffix(normalized, ".")
}

// ProbeResult 是單次探測的結果。
type ProbeResult struct {
	URL        string `json:"url"`
	Param      string `json:"param"`
	RequestURL string `json:"request_url"`
	Status     int    `json:"status"`
	Location   string `json:"location"`
	Reflected  bool   `json:"reflected"`
	Error      string `json:"error,omitempty"`
	// Evidence 是這次結果的證據等級（見 Evidence* 常數）。
	//
	// 為什麼要分級：Location 指向受控端點是「真的跳轉」；但有些站方只是把
	// 參數原樣印在頁面上（200 + 內文回顯）—— 那不是跳轉，只是回顯。
	// 兩者混在一起當 confirmed 會讓「準確率」完全失真。
	Evidence string `json:"evidence,omitempty"`
	// BodyEcho 為 true 表示受控端點的字串出現在回應本文裡（疑似回顯偽陽性）。
	BodyEcho bool `json:"body_echo,omitempty"`
}

// 證據等級。
const (
	// EvidenceNone 沒有任何證據（連站都沒跳）。
	EvidenceNone = "none"
	// EvidenceLocation 是 3xx 且 Location 指向受控端點 —— 強證據，真跳轉。
	EvidenceLocation = "location"
	// EvidenceBodyEcho 是回應本文裡出現受控端點，但沒有 Location —— 弱證據，
	// 站方多半只是把參數回顯在頁面上，不是真跳轉。
	EvidenceBodyEcho = "body_echo"
)

// Probe 對 target 送出一次 GET 請求，永遠不跟隨重新導向。
//
// 重新導向必須被擋下來：跳轉漏洞的證據就是 Location 標頭本身，
// 跟著跳下去只會拿到最終頁面，反而看不出原始的跳轉目標。
// 逾時與網路錯誤都寫進結果，不會 panic。
func Probe(ctx context.Context, client *http.Client, target string, param string, payload string) ProbeResult {
	return ProbeWithMethod(ctx, client, http.MethodGet, target, param, payload)
}

// ProbeWithMethod 是 Probe 的 method 變體，供需要 POST 的呼叫端使用。
func ProbeWithMethod(ctx context.Context, client *http.Client, method string, target string, param string, payload string) ProbeResult {
	result := ProbeResult{
		URL:   strings.TrimSpace(target),
		Param: strings.TrimSpace(param),
	}
	if ctx == nil {
		ctx = context.Background()
	}
	requestMethod := strings.ToUpper(strings.TrimSpace(method))
	if requestMethod == "" {
		requestMethod = http.MethodGet
	}

	requestURL, err := BuildProbeURL(result.URL, result.Param, payload)
	if err != nil {
		result.Error = err.Error()
		return result
	}
	result.RequestURL = requestURL

	req, err := http.NewRequestWithContext(ctx, requestMethod, requestURL, nil)
	if err != nil {
		result.Error = err.Error()
		return result
	}

	probeClient := newProbeClient(client)
	resp, err := probeClient.Do(req)
	if err != nil {
		result.Error = err.Error()
		return result
	}
	defer resp.Body.Close()
	// 讀一小段本文：除了讓 keep-alive 連線正常回收，還要拿來判斷
	// 「站方只是把參數回顯在頁面上」這種偽陽性。
	body, _ := io.ReadAll(io.LimitReader(resp.Body, maxProbeBodyBytes))

	result.Status = resp.StatusCode
	result.Location = ExtractLocation(resp.Header)
	result.Reflected = IsReflected(result.Location, payload)
	result.BodyEcho = !result.Reflected && bodyEchoesEndpoint(body, payload)
	switch {
	case result.Reflected:
		result.Evidence = EvidenceLocation
	case result.BodyEcho:
		result.Evidence = EvidenceBodyEcho
	default:
		result.Evidence = EvidenceNone
	}
	return result
}

// bodyEchoesEndpoint 判斷回應本文裡是否出現受控端點。
//
// 這是「偽陽性」的典型樣子：站方沒有真的跳轉，只是把整個網址印在頁面上
// （例如「你將被導向 <url>」）。把這種結果算成 confirmed 會嚴重灌水，
// 所以單獨標成 body_echo，不計入 confirmed。
func bodyEchoesEndpoint(body []byte, payload string) bool {
	if len(body) == 0 {
		return false
	}
	trimmed := strings.TrimSpace(payload)
	if trimmed == "" {
		return false
	}
	lower := string(body)
	if strings.Contains(lower, trimmed) {
		return true
	}
	// 編碼後的 payload 不會原樣出現，用解碼後的主機名比對。
	decoded := DecodeEndpoint(trimmed)
	if decoded != trimmed && strings.Contains(lower, decoded) {
		return true
	}
	if host := extractHost(decoded); host != "" && strings.Contains(strings.ToLower(lower), host) {
		return true
	}
	return false
}

// newProbeClient 複製一份 client 並強制關閉重新導向。
//
// 複製而不是直接改 client，是為了不污染呼叫端共用同一個 client 的其他呼叫。
func newProbeClient(client *http.Client) *http.Client {
	probeClient := &http.Client{Timeout: DefaultProbeTimeout}
	if client != nil {
		copied := *client
		probeClient = &copied
		if probeClient.Timeout <= 0 {
			probeClient.Timeout = DefaultProbeTimeout
		}
	}
	probeClient.CheckRedirect = func(req *http.Request, via []*http.Request) error {
		return http.ErrUseLastResponse
	}
	return probeClient
}
