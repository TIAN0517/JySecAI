package redirect

import (
	"net"
	"net/url"
	"regexp"
	"sort"
	"strings"

	"golang.org/x/net/publicsuffix"
)

// 改寫漏洞紀錄裡的回連端點。
//
// 為什麼需要這一段：漏洞紀錄裡的跳轉 payload 幾乎都帶著攻擊者自己的網域
// （記錄別人的站就是這樣）。複測時直接照抄，等於把回連送到別人的伺服器：
// 結果無法歸因、也拿不到能當證據的東西。這個函式把「payload 位置」上的
// 外部網址換成操作者自己的受控端點，讓整批紀錄可以用同一組端點重跑。
//
// 只換 payload 位置，不換整段文字：
//   - 目標站自己的網址（Target 及其子網域）永遠保留 —— 那是受害者，不是 payload。
//   - 同一個可註冊網域下的兄弟子網域也保留（uat-*.chailease.com.tw 與 www.chailease.com.tw）。
//   - 描述性欄位（Impact / Recommendation）不在改寫範圍內，由呼叫端決定要不要帶進來。
//   - 已經是受控端點的值不動 —— 改寫必須可以重複執行（idempotent）。
//   - 私有／回環／link-local IP 預設不動 —— 那通常是被害者自己的內網架構，不是回連端點。

// rewritePayloadParamNames 是「跳轉參數」名稱：這些參數的值就是攻擊者控制的回連位址。
//
// 與 DetectRedirectParams 用同一組常見名單，但這裡是「比對既有文字」而不是
// 「猜參數名」，所以大小寫不敏感（ReturnUrl / returnurl 都算）。
var rewritePayloadParamNames = []string{
	"url",
	"redirect",
	"redirect_uri",
	"redirecturl",
	"returnurl",
	"next",
	"goto",
	"dest",
	"destination",
	"continue",
	"redirect_to",
	"targeturl",
	"target",
	"link",
	"u",
}

var (
	// rewriteURLChars 是網址字元的排除集合。
	//
	// 中文標點一定要排除：中文句子裡常有「（明文降級）」這種括號說明，
	// 沒有排除的話會把「（明文降級）」一起吃進網址，替換時連說明文字都沒了。
	rewriteURLChars = `[^\s"'<>` + "`" + `，。；、：（《【「『）】]`

	// rewriteParamPattern：?url=<url> / &redirect=<url> / 文字裡的 url=<url> ——
	// query 裡的跳轉參數值，或證據文字裡直接寫出的參數值。
	//
	// 前綴字元集含全形標點：中文紀錄常寫成「回應參數：returnUrl=…」，只認半形
	// 空白會整段漏掉。
	rewriteParamPattern = regexp.MustCompile(
		`(?i)(?:[?&]|[\s'"` + "`" + `({\[：，；、（）【】「『《》])(` + joinPatternAlternation(rewritePayloadParamNames) + `)=([^&\s"'<>` + "`" + `，。；、：（《【「『）】]+)`)

	// rewriteLocationPattern：Location: <url> —— 目標回應標頭裡的跳轉目標。
	rewriteLocationPattern = regexp.MustCompile(
		`(?i)(Location\s*:\s*)(https?://` + rewriteURLChars + `+)`)

	// rewriteAssignPattern：targetUrl="<url>" / "callbackUrl":"<url>" —— 樣本或
	// 設定片段裡的 payload 指派（JS 用 =，JSON 用 :）。
	rewriteAssignPattern = regexp.MustCompile(
		`(?i)\b(targetUrl|redirectUrl|callbackUrl|jumpUrl|landUrl|destUrl|goUrl|payload)` +
			`\s*["']?\s*[:=]\s*["']?(https?://` + rewriteURLChars + `+)`)

	// rewriteLabelPattern：受控端點：<url> / callback endpoint: <url> —— 文字描述。
	rewriteLabelPattern = regexp.MustCompile(
		`(?i)(受控回[连連]端[点點]|受控端[点點]|回[连連]端[点點]|回[连連]地址|回[连連][网網][域址]|` +
			`跳[转轉]目標|跳[转轉][网網][域址]|callback\s+(?:url|endpoint|domain)?|redirect\s+(?:target|url|endpoint))` +
			`\s*[:：]?\s*(https?://` + rewriteURLChars + `+)`)
)

// joinPatternAlternation 把名稱清單組成 regex 的 alternation。
func joinPatternAlternation(names []string) string {
	if len(names) == 0 {
		return "(?!)" // 不可能命中的空 alternation
	}
	quoted := make([]string, 0, len(names))
	for _, name := range names {
		quoted = append(quoted, regexp.QuoteMeta(name))
	}
	return strings.Join(quoted, "|")
}

// rewriteCandidate 是「可能要被換掉的 payload 位置」。
type rewriteCandidate struct {
	start int    // 在原文中的起始位置
	end   int    // 在原文中的結束位置（不含）
	value string // 原文片段（可能是 percent-encoded）
	url   string // 解碼後的網址
}

// RewriteOptions 控制改寫範圍。
type RewriteOptions struct {
	// Endpoint 是要寫入的受控端點。
	Endpoint string
	// KeepHosts 是永遠不改寫的主機：目標站自己、標題裡提到的主機。
	KeepHosts []string
	// KeepSiteHosts 是「同一個站」要保留的主機，比對時用可註冊網域（eTLD+1）而不是
	// 完整主機名。
	//
	// 為什麼需要：目標欄位常只寫其中一個子網域（例如 uat-member-center-frontstage-service
	// .chailease.com.tw），但證據裡同時出現 www.chailease.com.tw、lite.dmz.apac.fedex.com
	// 這類兄弟子網域。只比對完整主機名會把它們當成 payload 換掉，直接改寫了受害者
	// 自己的網址 —— 那是毀證據，不是代入回連端點。
	//
	// 只放「目標欄位」抽出來的主機；標題裡的主機仍走 KeepHosts 的完整比對，
	// 避免標題提到攻擊者網域時反而擋掉該改寫的位置。
	KeepSiteHosts []string
	// OnlyHosts 非空時，只有這組主機會被改寫（其他主機一律保留）。
	// 這是「資料遷移」該用的模式：先掃描出候選主機清單，由操作者挑過再改。
	OnlyHosts []string
	// ExcludeHosts 是永不改寫的主機（即使在 OnlyHosts 裡）。
	ExcludeHosts []string
	// IncludeObserved 為 true 時，連「觀測到的回應值」（Location 標頭）也一併改寫。
	//
	// 預設 false：Location 標頭是「當時確實看到什麼」的證據，寫掉它等於竄改證據。
	// 真正該換的是我們自己送出的 payload 值（query 參數值、樣本指派、端點標籤），
	// 因為那些才是下一次複測要代入的東西。
	IncludeObserved bool
	// AllowPrivateIPs 為 true 時，私有／回環／link-local IP 也照改。
	//
	// 預設 false。這類位址在漏洞紀錄裡幾乎都是「被害者自己的內網架構」
	// （Dockerfile 洩漏的 10.5.0.2、開發前端 localhost:4200、雲端 metadata 網段），
	// 把它們換成受控端點會直接摧毀證據。真的要驗 SSRF 可達性時再打開。
	AllowPrivateIPs bool
}

// RewriteControlledEndpoints 把文字中 payload 位置的外部回連網址換成受控端點。
//
// keepHosts 是要保留的主機（通常是該筆紀錄的目標站）。回傳改寫後的文字、
// 替換次數，以及被替換掉的原始網址清單（去重、依出現順序）。
//
// 找不到 payload 位置、或位置上的網址本來就是受控端點 / 目標站時，文字原樣回傳。
func RewriteControlledEndpoints(text string, endpoint string, keepHosts []string) (string, int, []string) {
	return RewriteControlledEndpointsWithOptions(text, RewriteOptions{
		Endpoint:  endpoint,
		KeepHosts: keepHosts,
	})
}

// RewriteControlledEndpointsWithOptions 是可控範圍的改寫版本。
func RewriteControlledEndpointsWithOptions(text string, opts RewriteOptions) (string, int, []string) {
	if strings.TrimSpace(text) == "" || strings.TrimSpace(opts.Endpoint) == "" {
		return text, 0, nil
	}
	endpoint := strings.TrimSpace(opts.Endpoint)
	endpointHost := rewriteHost(endpoint)
	if endpointHost == "" {
		return text, 0, nil
	}
	protected := rewriteNormalizeHosts(opts.KeepHosts)
	protected = append(protected, rewriteNormalizeHosts(opts.ExcludeHosts)...)
	site := rewriteNormalizeHosts(opts.KeepSiteHosts)
	only := rewriteNormalizeHosts(opts.OnlyHosts)

	candidates := collectRewriteCandidates(text, opts.IncludeObserved)
	if len(candidates) == 0 {
		return text, 0, nil
	}
	sort.SliceStable(candidates, func(i, j int) bool { return candidates[i].start < candidates[j].start })

	var out strings.Builder
	last := 0
	replaced := 0
	replacedURLs := make([]string, 0, 4)
	seen := map[string]bool{}

	for _, candidate := range candidates {
		if candidate.start < last {
			continue // 與前一筆重疊，只留先出現的那個
		}
		host := rewriteHost(candidate.url)
		if host == "" || host == endpointHost {
			continue
		}
		if len(only) > 0 && !rewriteHostProtected(host, only) {
			continue // 只改寫指定的主機
		}
		if rewriteHostProtected(host, protected) || rewriteHostSameSite(host, site) {
			continue
		}
		if !opts.AllowPrivateIPs && rewriteHostIsPrivate(host) {
			continue // 私有／回環／link-local 位址通常是受害者自己的內網，不是回連端點
		}
		out.WriteString(text[last:candidate.start])
		out.WriteString(rewriteEncodeLike(candidate.value, endpoint))
		last = candidate.end
		replaced++
		if !seen[candidate.url] {
			seen[candidate.url] = true
			replacedURLs = append(replacedURLs, candidate.url)
		}
	}
	out.WriteString(text[last:])
	return out.String(), replaced, replacedURLs
}

// CandidateEndpoints 找出文字裡 payload 位置的網址（不改寫）。
//
// 這是「先掃描、再挑主機」的入口：資料遷移前先看清楚整庫有哪些主機出現在
// payload 位置，再由操作者決定要換掉哪些。
//
// includeObserved 為 true 時連觀測到的 Location 值一起列出。
func CandidateEndpoints(text string, includeObserved bool) []string {
	candidates := collectRewriteCandidates(text, includeObserved)
	out := make([]string, 0, len(candidates))
	seen := map[string]bool{}
	for _, candidate := range candidates {
		if seen[candidate.url] {
			continue
		}
		seen[candidate.url] = true
		out = append(out, candidate.url)
	}
	return out
}

// collectRewriteCandidates 掃出文字裡所有「payload 位置」的網址。
//
// includeObserved 為 false 時不收「Location: <url>」這類觀測到的回應值。
func collectRewriteCandidates(text string, includeObserved bool) []rewriteCandidate {
	var out []rewriteCandidate

	// query / 文字跳轉參數值（第 2 組）。
	for _, match := range rewriteParamPattern.FindAllStringSubmatchIndex(text, -1) {
		start, end := match[4], match[5]
		if start < 0 || end < 0 {
			continue
		}
		raw := text[start:end]
		value := trimRewriteTrailingPunctuation(raw)
		decoded := rewriteDecode(value)
		if !strings.HasPrefix(decoded, "http://") && !strings.HasPrefix(decoded, "https://") {
			continue
		}
		out = append(out, rewriteCandidate{start: start, end: end - (len(raw) - len(value)), value: value, url: decoded})
	}

	// Location 標頭值、樣本指派、標籤描述：第 2 組。
	patterns := []*regexp.Regexp{rewriteAssignPattern, rewriteLabelPattern}
	if includeObserved {
		patterns = append([]*regexp.Regexp{rewriteLocationPattern}, patterns...)
	}
	for _, pattern := range patterns {
		for _, match := range pattern.FindAllStringSubmatchIndex(text, -1) {
			start, end := match[4], match[5]
			if start < 0 || end < 0 {
				continue
			}
			raw := text[start:end]
			value := trimRewriteTrailingPunctuation(raw)
			if !strings.HasPrefix(value, "http://") && !strings.HasPrefix(value, "https://") {
				continue
			}
			out = append(out, rewriteCandidate{start: start, end: end - (len(raw) - len(value)), value: value, url: value})
		}
	}
	return out
}

// trimRewriteTrailingPunctuation 去掉網址尾端的標點（句號、逗號…），
// 但把標點留在原文裡 —— 那是句子的部分，不是網址的一部分。
func trimRewriteTrailingPunctuation(value string) string {
	trimmed := value
	for len(trimmed) > 0 {
		last := trimmed[len(trimmed)-1]
		if !strings.ContainsRune(".,;:!?、，。；：", rune(last)) {
			break
		}
		trimmed = trimmed[:len(trimmed)-1]
	}
	return trimmed
}

// rewriteDecode 嘗試把 percent-encoded 的參數值解回原網址。
func rewriteDecode(value string) string {
	if !strings.Contains(value, "%3") {
		return value
	}
	if decoded, err := url.QueryUnescape(value); err == nil {
		return decoded
	}
	return value
}

// rewriteEncodeLike 依原值的編碼風格輸出新的受控端點：
// 原文是 percent-encoded 就維持 percent-encoded，否則用原樣。
func rewriteEncodeLike(original string, endpoint string) string {
	if strings.Contains(original, "%3A") || strings.Contains(original, "%3a") {
		return url.QueryEscape(endpoint)
	}
	return endpoint
}

// TargetHosts 從漏洞紀錄的目標欄位取出要保留的主機。
//
// 目標欄位不是乾淨的 URL：常見寫法是 "example.com (1.2.3.4)" 或 "https://example.com/x"。
// 這裡把能當主機的部分都取出來 —— 受控端點改寫時一律保留，那是受害者，不是 payload。
func TargetHosts(target string) []string {
	hosts := make([]string, 0, 3)
	seen := map[string]bool{}
	add := func(host string) {
		host = strings.ToLower(strings.TrimSpace(host))
		host = strings.Trim(host, "[]")
		if host == "" || seen[host] {
			return
		}
		seen[host] = true
		hosts = append(hosts, host)
	}

	fields := strings.FieldsFunc(target, func(r rune) bool {
		switch r {
		case ' ', '\t', '\n', '\r', '(', ')', '[', ']', '{', '}', ',', ';', '"', '\'', '`':
			return true
		// 全形標點：中文紀錄裡的 Target 欄位幾乎都用全形括號包補充說明，
		// 例如「103.129.178.179（www.pacific-prt.com）主機級防火牆…」。
		// 不切開的話整串會被當成一個主機名，受害者自己的網址就會被當成 payload 換掉。
		case '（', '）', '，', '、', '；', '：', '／', '【', '】', '「', '」', '《', '》', '　':
			return true
		}
		return false
	})
	for _, field := range fields {
		if field == "" {
			continue
		}
		if strings.Contains(field, "://") {
			if parsed, err := url.Parse(field); err == nil && parsed.Hostname() != "" {
				add(parsed.Hostname())
			}
			continue
		}
		// key=value 形式：證據裡常寫「证书 CN=*.alibabacorp.com」這種。
		// 只在等號後面看起來像主機名時才切，避免把 query 字串切壞。
		if idx := strings.Index(field, "="); idx >= 0 {
			after := field[idx+1:]
			if strings.Contains(after, ".") && !strings.ContainsAny(after, "/:") {
				field = after
			}
		}
		// 萬用字號主機名：*.alibabacorp.com → alibabacorp.com
		field = strings.TrimPrefix(field, "*.")
		if field == "" {
			continue
		}
		// host:port —— 目標欄位常寫成「154.84.99.175:10943 (m.bc-galaxy.com)」。
		// 埠號不是主機，只取主機名部分；不處理的話目標站自己的位址會被當成 payload 換掉。
		if host, _, ok := strings.Cut(field, ":"); ok && strings.Contains(host, ".") {
			add(host)
			continue
		}
		// 純主機名或 IP；帶冒號的（host:port）不在此處理。
		if strings.Contains(field, ".") && !strings.Contains(field, ":") {
			add(field)
		}
	}
	return hosts
}

// rewriteHost 取出網址的主機名；不是 http/https 或解析不出來時回空字串。
func rewriteHost(raw string) string {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || parsed.Host == "" {
		return ""
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return ""
	}
	hostname := strings.ToLower(strings.TrimSuffix(parsed.Hostname(), "."))
	if hostname == "" {
		return ""
	}
	// 沒有點的單字主機不是真實主機。
	//
	// 漏洞紀錄裡到處是這種被破壞的殘值 —— 例如 WordPress 的 siteurl/home 被改壞成
	// 「https://www.」（不是合法網址）。那是被害者自己系統的設定殘留，不是攻擊者的
	// payload；把它換成受控端點只會改壞證據。
	if !strings.Contains(hostname, ".") && net.ParseIP(hostname) == nil && hostname != "localhost" {
		return ""
	}
	return hostname
}

// rewriteNormalizeHosts 正規化要保留的主機清單。
func rewriteNormalizeHosts(hosts []string) []string {
	out := make([]string, 0, len(hosts))
	for _, host := range hosts {
		normalized := strings.ToLower(strings.TrimSpace(host))
		normalized = strings.Trim(normalized, "[]")
		if normalized == "" || strings.ContainsAny(normalized, " \t\r\n/") {
			continue
		}
		out = append(out, normalized)
	}
	return out
}

// HostOf 取出網址的主機名；不是 http/https、不是真實主機或解析不出來時回空字串。
//
// 盤點與改寫都要用同一個判斷，否則會出現「盤點列了但實際沒換」的落差。
func HostOf(raw string) string {
	return rewriteHost(raw)
}

// ProtectedHost 判斷某個主機是否屬於這筆紀錄自己的站。
//
// keepHosts 以完整主機名比對（目標欄位 + 標題提到的主機）；
// keepSiteHosts 以可註冊網域（eTLD+1）比對，用來涵蓋兄弟子網域。
//
// 盤點（-scan）與實際改寫必須用同一個判斷，否則「盤點說會換」和「實際換掉」
// 會對不起來 —— 那正是改寫工具最容易出事的地方。
func ProtectedHost(host string, keepHosts []string, keepSiteHosts []string) bool {
	return rewriteHostProtected(host, rewriteNormalizeHosts(keepHosts)) ||
		rewriteHostSameSite(host, rewriteNormalizeHosts(keepSiteHosts))
}

// PrivateHost 判斷主機是不是私有／回環／link-local 位址。
//
// 預設不改寫這類位址（見 RewriteOptions.AllowPrivateIPs）。
func PrivateHost(host string) bool {
	return rewriteHostIsPrivate(host)
}

// rewriteHostProtected 判斷主機是否屬於要保留的目標站。
//
// 不只比對完全相同：`www.example.com` 與 `example.com` 視為同一個站；
// 反過來 `example.com.evil.tld` 也不會因為字串包含就被誤判成同一個站。
func rewriteHostProtected(host string, keepHosts []string) bool {
	for _, keep := range keepHosts {
		if host == keep {
			return true
		}
		if strings.HasSuffix(host, "."+keep) || strings.HasSuffix(keep, "."+host) {
			return true
		}
	}
	return false
}

// rewriteHostSameSite 判斷兩個主機是否屬於同一個可註冊網域（eTLD+1）。
//
// 用途：目標欄位只寫了其中一個子網域時，兄弟子網域（www / uat / api / staging…）
// 仍然是同一個站，是「受害者自己的網址」而不是攻擊者的 payload，不該被換掉。
func rewriteHostSameSite(host string, keepHosts []string) bool {
	if len(keepHosts) == 0 {
		return false
	}
	hostSite := rewriteSiteDomain(host)
	if hostSite == "" {
		return false
	}
	for _, keep := range keepHosts {
		keepSite := rewriteSiteDomain(keep)
		if keepSite == "" {
			continue
		}
		if hostSite == keepSite {
			return true
		}
	}
	return false
}

// rewriteSiteDomain 取出主機的可註冊網域（eTLD+1）。
//
// 拿不到公開後綴資訊時（內部網域、非真實 TLD）退回主機本身，
// 這時比較結果等同於完整主機名比對 —— 行為退回舊的嚴格模式，不會誤放行。
func rewriteSiteDomain(host string) string {
	host = strings.ToLower(strings.TrimSuffix(strings.TrimSpace(host), "."))
	if host == "" {
		return ""
	}
	if net.ParseIP(host) != nil {
		return host // IP 沒有網域概念
	}
	domain, err := publicsuffix.EffectiveTLDPlusOne(host)
	if err != nil || domain == "" {
		return host
	}
	return strings.ToLower(domain)
}

// rewriteHostIsPrivate 判斷主機是不是私有／回環／link-local 位址。
//
// 這類位址在漏洞紀錄裡通常是「被害者自己的內網架構」（Dockerfile 洩漏的 10.5.0.2、
// 開發前端 localhost:4200、雲端 metadata 的 169.254.169.254），把它們換成受控端點
// 會直接改寫了證據本身，而不是代入下一次複測要用的回連端點。
func rewriteHostIsPrivate(host string) bool {
	host = strings.ToLower(strings.TrimSpace(host))
	if host == "" {
		return false
	}
	if host == "localhost" || strings.HasSuffix(host, ".localhost") {
		return true
	}
	ip := net.ParseIP(host)
	if ip == nil {
		return false
	}
	if ip.IsLoopback() || ip.IsPrivate() || ip.IsUnspecified() ||
		ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() || ip.IsMulticast() {
		return true
	}
	// CGNAT 100.64.0.0/10：不是 RFC1918，但同樣不對外可達。
	if v4 := ip.To4(); v4 != nil {
		if v4[0] == 100 && v4[1] >= 64 && v4[1] <= 127 {
			return true
		}
	}
	return false
}
