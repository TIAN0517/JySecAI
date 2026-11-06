// Package forbidden 判定「119／EPCR／消防救護類永久禁區」。
//
// 為什麼平台端也需要這一份
// ----------------------
// all/ 管線（Python）自 2026-11-01 起有 all/tools/forbidden_scope.py 三層判定，
// 但平台自己的批次受控跳轉驗證（internal/redirect、internal/handler/redirect_verify.go）
// 會直接對使用者給的目標發 HTTP 請求，那條路徑原本沒有任何禁區守門。
// 漏洞庫裡確實存在禁區資產的紀錄（例如 epcr.tpf.gov.tw 的紀錄），
// 只要把漏洞匯入批次就會真的打到消防／EPCR 系統。
//
// 本套件是 all/tools/forbidden_scope.py 的 Go 版，規則逐條對齊：
//   1. 網域層：非 IP 主機比對 FORBIDDEN_DOMAIN
//   2. IP 層  ：FORBIDDEN_IPS 精確清單 + FORBIDDEN_IP_PREFIXES 網段
//   3. 內容層 ：target／title 自曝（逐筆判定，不連坐整個 host）
//
// 兩邊規則必須同步：任何一邊放行、另一邊攔截都不行。
package forbidden

import (
	"regexp"
	"strings"
)

// 禁區原因字串。
const (
	ReasonDomain = "forbidden-119-domain"
	ReasonIP     = "forbidden-119-ip"
	ReasonTarget = "forbidden-119-target"
)

// forbiddenDomainPattern 是網域層規則（只對非 IP 主機生效）。
//
// 注意：Python 版原本還有一條 (?<![0-9])119(?![0-9])，Go 的 RE2 不支援 lookbehind，
// 改由 hasBare119Label 單獨實作，語意一致。
var forbiddenDomainPattern = regexp.MustCompile(`(?i)(?:epcr|tfd\.gov|ttfd\.gov|119\.gov|eocapp\.gov|ndcr|ncr\.nat\.gov|ncdr\.nat\.gov|rescueinfo|emic\.gov\.tw|nfa\.gov\.tw|fdkc\.gov\.tw|kfa\.kcg\.gov\.tw|ylfire\.gov\.tw|119dts|appofficer|femem|tyfd|ohca|ambulance|gaogui|hcfd\.gov|mcitypes|mcicaserecords|dispatchrecords|vitalsignvideoserver|epcrserver)`)

// forbiddenTargetPattern 是內容層規則（target／title 自曝）。
//
// gaogui／gaoguei 在內容層必須是獨立 token（裸子字串會誤殺高雄市政府 SSO 信箱帳號），
// 由 hasBoundedGaogui 單獨實作。
var forbiddenTargetPattern = regexp.MustCompile(`(?i)(?:tyfd|消防|救護|救护|ohca|ambulance|rescueinfo|ndcr|femem|appofficer|epcr|tfd\.gov|tpf\.gov|ttfd\.gov|119\.gov|eocapp\.gov|emic\.gov\.tw|nfa\.gov\.tw|hcfd\.gov|mcitypes|mcicaserecords|dispatchrecords|vitalsignvideoserver|epcrserver|yilanfd|高桂分隊|前金分隊|消防分隊|119救護|緊急救護|救災救護|義消|消防署)`)

// forbiddenIPs 是逐筆查證過的禁區 IP。
var forbiddenIPs = map[string]struct{}{
	"35.234.50.28":    {}, // 臺北市 EPCR（AuthServer / vitalSignVideoServer，GCP）
	"118.163.107.93":  {}, // EPCR 正式站
	"61.222.211.111":  {}, // 台東 EPCR 統計面板
	"61.222.211.10":   {}, // epcrvoip.ttfd.gov.tw 消防 VoIP 視訊系統
	"210.69.43.104":   {}, // dptapp.tfd.gov.tw / service119.tfd.gov.tw
	"210.241.54.57":   {}, // 桃園市消防局 tyfdapp
	"210.241.33.146":  {}, // /tyfdapp
	"210.241.116.220": {}, // /tyfdapp
	"210.65.88.211":   {}, // carsys.hcfd.gov.tw 消防資訊系統
	"123.252.43.71":   {}, // 高雄市消防局「高桂分隊」門戶站
	"163.29.63.21":    {}, // fdkc.gov.tw（高雄市政府消防局）DNS
	"163.29.163.35":   {}, // www.eocapp.gov.taipei（臺北市 EOC）
	// 消防署 tyfdapp 推播目標（使用者明示「那個在推播的」也不拉進白名單）
	"223.200.7.74":    {},
	"223.200.12.38":   {},
	"223.200.44.13":   {},
	"223.200.50.93":   {},
	"223.200.68.74":   {},
	"223.200.93.181":  {}, // 宜蘭縣消防局 YiLanFD
	"223.200.93.182":  {}, // 宜蘭縣消防局管理系統
	"223.200.104.237": {},
}

// forbiddenIPPrefixes 是整段都是該單位基礎設施的網段。
var forbiddenIPPrefixes = []string{
	"117.56.",    // 內政部消防署 MDS 業務網段（tyfdapp / AppOfficer）
	"210.69.42.", // tfd.gov.tw 網段（DNS、dc 域控、message、turnserver…）
}

var (
	schemeURLPattern = regexp.MustCompile(`^[a-z][a-z0-9+.\-]*://([^/?#\s]+)`)
	ipv4Pattern      = regexp.MustCompile(`\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b`)
	ipv4DashPattern  = regexp.MustCompile(`\b(\d{1,3})-(\d{1,3})-(\d{1,3})-(\d{1,3})\b`)
)

// HostOf 從 URL 取主機（含 port）；取不到回空字串。
func HostOf(raw string) string {
	m := schemeURLPattern.FindStringSubmatch(strings.TrimSpace(raw))
	if len(m) < 2 {
		return ""
	}
	host := m[1]
	if at := strings.LastIndex(host, "@"); at >= 0 {
		host = host[at+1:]
	}
	return strings.ToLower(host)
}

// stripPort 去掉 port 與結尾的點。
func stripPort(host string) string {
	host = strings.ToLower(strings.TrimSpace(host))
	if strings.HasPrefix(host, "[") && strings.Contains(host, "]") {
		return strings.TrimSpace(host[1:strings.Index(host, "]")])
	}
	if strings.Count(host, ":") == 1 {
		host = strings.SplitN(host, ":", 2)[0]
	}
	return strings.Trim(host, ".")
}

// ipCandidates 抽出主機字串裡所有 IPv4 字面量（含 223-200-93-182 這種反向寫法）。
func ipCandidates(host string) []string {
	out := make([]string, 0, 4)
	for _, m := range ipv4Pattern.FindAllStringSubmatch(host, -1) {
		out = append(out, m[0])
	}
	for _, m := range ipv4DashPattern.FindAllStringSubmatch(host, -1) {
		out = append(out, m[1]+"."+m[2]+"."+m[3]+"."+m[4])
	}
	return out
}

// hostKind 回傳 'ip' | 'domain' | 'other'。
func hostKind(host string) string {
	h := stripPort(host)
	if h == "" {
		return "other"
	}
	if ipv4Pattern.MatchString(h) && ipv4Pattern.FindString(h) == h {
		return "ip"
	}
	if ipv4DashPattern.MatchString(h) && ipv4DashPattern.FindString(h) == h {
		return "ip"
	}
	return "domain"
}

func ipForbidden(ip string) bool {
	if _, ok := forbiddenIPs[ip]; ok {
		return true
	}
	for _, prefix := range forbiddenIPPrefixes {
		if strings.HasPrefix(ip, prefix) {
			return true
		}
	}
	return false
}

// hasBare119Label 實作 (?<![0-9])119(?![0-9])。
func hasBare119Label(host string) bool {
	for i := 0; i+3 <= len(host); i++ {
		if host[i:i+3] != "119" {
			continue
		}
		if i > 0 && host[i-1] >= '0' && host[i-1] <= '9' {
			continue
		}
		if i+3 < len(host) && host[i+3] >= '0' && host[i+3] <= '9' {
			continue
		}
		return true
	}
	return false
}

// hasBoundedGaogui 實作 (?<![0-9A-Za-z])(?:gaogui|gaoguei)(?![0-9A-Za-z])。
func hasBoundedGaogui(blob string) bool {
	for _, token := range []string{"gaogui", "gaoguei"} {
		for i := 0; i+len(token) <= len(blob); i++ {
			if blob[i:i+len(token)] != token {
				continue
			}
			if i > 0 && isAlnum(blob[i-1]) {
				continue
			}
			end := i + len(token)
			if end < len(blob) && isAlnum(blob[end]) {
				continue
			}
			return true
		}
	}
	return false
}

func isAlnum(c byte) bool {
	return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
}

// Reason 回傳禁區原因字串；空字串代表不在禁區。
//
// 參數對應各資料層的欄位：
//   - host   —— 漏洞庫／console 的 host 欄位
//   - target —— 漏洞記錄的 target（URL 或描述）
//   - title  —— 漏洞標題
//   - url    —— 復測端點的 URL
//   - scope  —— 漏洞庫的 scope（網域或 IP）
func Reason(host, target, title, url, scope string) string {
	// ── 收集候選主機 ───────────────────────────────────────────────
	hosts := make([]string, 0, 4)
	for _, v := range []string{host, url, scope} {
		if strings.TrimSpace(v) != "" {
			hosts = append(hosts, stripPort(v))
		}
	}
	for _, v := range []string{target, url} {
		if strings.TrimSpace(v) == "" {
			continue
		}
		if h := HostOf(v); h != "" {
			hosts = append(hosts, stripPort(h))
		}
	}
	hosts = nonEmpty(hosts)

	// ── 層 1：網域自曝 ／ 層 2：IP 自曝 ────────────────────────────
	for _, h := range hosts {
		switch hostKind(h) {
		case "ip":
			for _, ip := range ipCandidates(h) {
				if ipForbidden(ip) {
					return ReasonIP
				}
			}
		case "domain":
			if forbiddenDomainPattern.MatchString(h) || hasBare119Label(h) {
				return ReasonDomain
			}
		}
	}

	// ── 層 2b：host 欄位缺失時，改從 target／title 抽 IP ────────────
	// 有些紀錄的 host 欄位是空的，但 target／title 裡帶著資產 IP。
	// 只在 host 缺失時才這樣做：host 存在時 target 裡的其他 IP 多半是連帶提到的
	// 第三方（例如 CDN 邊緣節點），那種紀錄的受測資產不是消防系統，不該連坐。
	if len(hosts) == 0 {
		for _, ip := range ipCandidates(target + " " + title) {
			if ipForbidden(ip) {
				return ReasonIP
			}
		}
	}

	// ── 層 3：內容自曝（逐筆）──────────────────────────────────────
	blob := strings.ToLower(strings.TrimSpace(target) + " " + strings.TrimSpace(title))
	if strings.TrimSpace(blob) != "" {
		if forbiddenTargetPattern.MatchString(blob) || hasBoundedGaogui(blob) {
			return ReasonTarget
		}
	}
	return ""
}

// IsForbidden 回傳 true 代表屬於 119／EPCR／消防救護類永久禁區。
func IsForbidden(host, target, title, url, scope string) bool {
	return Reason(host, target, title, url, scope) != ""
}

// FilterTargets 把目標清單分成 (保留, 禁區)。禁區者附上原因字串。
//
// 這是批次驗證的收口點：禁區目標不會被送到 HTTP 探測。
func FilterTargets(targets []string) (keep []string, dropped []string) {
	seen := make(map[string]struct{}, len(targets))
	for _, raw := range targets {
		value := strings.TrimSpace(raw)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		if reason := Reason("", value, "", value, ""); reason != "" {
			dropped = append(dropped, value+" ("+reason+")")
			continue
		}
		keep = append(keep, value)
	}
	return keep, dropped
}

func nonEmpty(values []string) []string {
	out := make([]string, 0, len(values))
	for _, v := range values {
		if v != "" {
			out = append(out, v)
		}
	}
	return out
}
