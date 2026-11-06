// Package vulnmask 對外輸出（外部 MySQL 接收端、匯出）做去識別化遮蔽。
//
// 為什麼需要：漏洞記錄裡的 target / evidence / description 會帶著真實目標的
// 公網位址與主機名，也會帶著測試基礎設施的內網位址（10.x、127.0.0.1、
// 雲端 metadata 端點等）。這些資料一旦寫進外部資料庫就是永久留存，
// 而外部資料庫的存取範圍通常比平台本身寬得多。
//
// 遮蔽原則：
//   - 位址一律不保留原值。公網位址換成穩定代號（同一個位址永遠對應同一個代號，
//     可以做關聯分析，但無法還原）；私有／回環／link-local 直接歸為 internal-redacted，
//     連關聯性都不留。
//   - URL 參數裡的憑證（token/key/password/secret/session/jwt）一律換成 ***。
//     憑證外洩比位址外洩更嚴重，而且不遮蔽等於把可用的存取權送出去。
//   - 主機名預設保留：它是分析的最小單位，遮掉就只剩數字。真的要連主機名一起藏，
//     用 Policy.MaskHosts 關掉保留。
package vulnmask

import (
	"crypto/sha256"
	"encoding/hex"
	"net"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// Policy 遮蔽政策。
type Policy struct {
	// MaskIPs 是否遮蔽 IPv4/IPv6 位址。預設為 true。
	MaskIPs bool
	// MaskHosts 是否連主機名一起遮蔽（替換成 host-<hash8>）。預設 false。
	MaskHosts bool
	// MaskSecrets 是否遮蔽 URL 參數與本文中的憑證。預設 true。
	MaskSecrets bool
	// RedactIPs 額外指定要完全抹除（不給代號）的位址，例如測試出口池的公開 IP。
	RedactIPs []string
}

// DefaultPolicy 回傳預設政策：遮蔽位址與憑證，保留主機名。
func DefaultPolicy() Policy {
	return Policy{
		MaskIPs:     true,
		MaskHosts:   false,
		MaskSecrets: true,
		RedactIPs: []string{
			// 雲端 metadata 端點：PoC 常用來證明 SSRF 影響面，
			// 但它同時會把平台的執行環境暴露出去。
			"169.254.169.254",
		},
	}
}

// WithRedactedIPs 回傳附加指定抹除位址的政策。
func (p Policy) WithRedactedIPs(ips ...string) Policy {
	p.RedactIPs = append(append([]string(nil), p.RedactIPs...), ips...)
	return p
}

var (
	urlPattern = regexp.MustCompile(`https?://[^\s"'<>）)，。；;]+`)

	// secretParamPat 遮蔽 URL／表單參數裡的憑證值。
	//
	// 參數名必須「以敏感關鍵字結尾」（可帶 id／] 後綴）才算憑證參數：
	//   - 命中：csrf_token=、client_secret=、x-api-key=、userpassword=、
	//     jsessionid=、OSSAccessKeyId=、X-Amz-Credential=、Signature=、order_token=
	//   - 不命中：author=、Keyword=、max-keys=、token_type=、auth_type=
	//     這些是查詢參數，遮掉會破壞證據本身 —— 例如 IDOR 的 ?author=1
	//     就是漏洞成立的要點。
	//
	// 舊版要求參數名「完全等於」清單字串且前面必須是 ?/&/;，
	// 因此 csrf_token=、userpassword=、jsessionid= 全都漏掉了。
	secretParamPat = regexp.MustCompile(`(?i)([?&;][A-Za-z0-9_.\-\[\]]*(?:token|key|secret|password|passwd|pwd|session|jwt|authorization|credential|credentials|signature|passphrase)(?:[_-]?id)?\]?=)([^&\s"'<>]+)`)

	// secretInline 遮蔽本文中的憑證（"password: xxx"、"myPassword=xxx"）。
	//
	// 關鍵字可以嵌在更長的識別碼裡（csrfToken=、userpassword=），
	// 否則 \b 會把它整組跳過 —— 那正是憑證外洩最常見的樣子。
	secretInline = regexp.MustCompile(`(?i)([A-Za-z0-9_.\-]*(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|credential|signature|passphrase|access[_-]?key)(?:[_-]?id)?[A-Za-z0-9_.\-]*\s*[:=]\s*)([^\s"',;]{4,})`)

	// bearerPat 遮蔽 Authorization 標頭裡的 Bearer / Basic 憑證。
	bearerPat = regexp.MustCompile(`(?i)\b(bearer|basic)\s+([A-Za-z0-9._\-+/=]{8,})`)

	// secretJSONPat 遮蔽 JSON／YAML 形式的憑證欄位：
	//   "PWD": "TestPwd_20260928"
	//   "AccessKeyId": "LTAI5t5jvFcXA8DDvSbtqeSy"
	//   'token': 'eyJhbGciOiJIUzI1NiJ9'
	//
	// 參數形式（?token=xxx）與行內形式（password: xxx）都抓不到這種
	// 「引號包住的 key」—— 生产证据里它是最常见的一种。
	//
	// 註：Go 的 regexp 是 RE2，沒有反向參照可用，所以結尾的引號不在比對範圍內
	// （遮蔽後它會留在原位，結果一樣是 "key":"***"）。
	secretJSONPat = regexp.MustCompile(`(?i)(["']?[A-Za-z0-9_.\-\[\]]*(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|credential|signature|passphrase|access[ _-]?key(?:[ _-]?id)?|session[ _-]?id)["']?\s*:\s*)(["'])([^"']+)`)

	// secretLoosePat 遮蔽「關鍵字 + 看起來像憑證的值」——證據裡的散文寫法：
	//   IAM Access Key ID : AKIAXXXXXXXXXXXXXXXX
	//   立即轮换已暴露的 AccessKeyId `LTAI5t5jvFcXA8DDvSbtqeSy`
	//   立即轮换泄露的北水处凭据 TaipeiCityFireDep/TaipeiCityFireDep2016
	//
	// 值必須「看起來像憑證」，否則散文（例如「token rotation
	// recommended」「密碼強度要求」）會被無差別洗掉 —— 遮蔽規則不能把證據
	// 本身洗成沒有意義的內容。
	// 前綴可選帶一個尾隨空白，讓「IAM Access Key ID : xxx」這種
	// 「前綴與關鍵字之間有空格」的寫法也能命中。
	// 分隔符另允許全形括號（生產證據裡的「AccessKeyId（LTAI…）」）與跳脫引號；
	// 值允許「A / B」這種帳密對（TaipeiCityFireDep / TaipeiCityFireDep2016）。
	//
	// 關鍵字清單也含「帳號」家族（账号／帳號／帐号／账户／用户名…）：
	// 生產證據裡那組預設測試帳號 RS106 是「帳號」也是「密碼」，
	// 只認密碼關鍵字的話，「用户名 RS106／跨用户名 RS106/xyzzy」這些寫法
	// 認不出來，值就不會被記錄，工作階段也抹不掉散文裡的其他出現。
	//
	// 沒有把英文 account／username 放進來：那些常是 IDOR 證據裡的查詢參數
	//（?account=12345），遮掉會直接毀掉漏洞成立的要點。
	// 純數字的值本來就不符合 looksLikeCredential（沒有字母），所以也擋得住。
	secretLoosePat = regexp.MustCompile(`(?i)((?:[A-Za-z0-9_.\-]*[ ]?(?:password|passwd|pwd|secret|token|api[ _-]?key|apikey|credential|signature|passphrase|access[ _-]?key(?:[ _-]?id)?|session[ _-]?id|aws[ _-]?access[ _-]?key[ _-]?id)|凭据|憑證|凭证|密码|密碼|口令|令牌|密钥|金鑰|金钥|账号|帳號|帐号|账戶|账户|帳戶|用户名|用戶名|用戶)\s*[:=]?\s*)([\\?"'\x60（(【\[「]?)([A-Za-z0-9_\-+/=.]{4,}(?:[ ]?/[ ]?[A-Za-z0-9_\-+/=.]{4,}){0,2})`)

	// secretCloudKeyPat 遮蔽雲端金鑰的「縮寫」寫法：
	//   受影响 bucket：b9jiyun（OSS AK LTAI5t5jvFcXA8DDvSbtqeSy）
	//   轮换已暴露的 AK（LTAI5t5jvFcXA8DDvSbtqeSy）与 appSecret
	//
	// 生產證據裡用的是簡寫的 AK／SK，不是 AccessKey／SecretKey，
	// 所以 secretLoosePat 的關鍵字清單完全抓不到（實測 MySQL 命中 10 筆）。
	//
	// 關鍵字必須是「獨立詞」（前後不能緊接英數或底線），
	// 否則 task／risk／back／ask 這類單字裡相鄰的字母會誤中。
	// 值同樣要通過 looksLikeCredential 的守衛。
	secretCloudKeyPat = regexp.MustCompile(`(?i)\b(AK|SK)\b(\s*[:=]?\s*)([\x60（(【\[「'"]?)([A-Za-z0-9_\-+/=.]{4,})`)

	// secretHTMLInputPat 遮蔽密碼欄位 input 的預設值：
	//   <input type="password" name="_txtPassword" value="RS106">
	//   <input name="txtPassword" value='RS106'>
	//
	// 這是「硬編碼預設帳密」這類漏洞的證據本體，但預設值本身就是一組
	// 可用的憑證，留在外部庫等於送出一組可登入的帳密。
	secretHTMLInputPat = regexp.MustCompile(`(?i)(<input[^>]*?\b(?:name|id)\s*=\s*\\?["'][^"'>]*(?:password|passwd|pwd|token|secret)[^"'>]*["'][^>]*?\bvalue\s*=\s*\\?["'])([^"']+)`)

	// secretHTMLInputValueFirstPat 處理 value 屬性排在 name/id 前面的情況。
	secretHTMLInputValueFirstPat = regexp.MustCompile(`(?i)(<input[^>]*?\bvalue\s*=\s*\\?["'])([^"']+)([^>]*?\b(?:name|id)\s*=\s*\\?["'][^"'>]*(?:password|passwd|pwd|token|secret)[^"'>]*["'])`)

	// secretFieldValuePat 遮蔽「憑證欄位名 → value=」這種表單/HTML 寫法：
	//   _txtPassword 的 value="RS106"
	//   txtPassword="RS106"
	//
	// 欄位名與 value 之間允許少量夾雜文字（中文的「的」之類）。
	secretFieldValuePat = regexp.MustCompile(`(?i)((?:[A-Za-z0-9_.\-]*(?:password|passwd|pwd|token|secret)[A-Za-z0-9_.\-]*)[^"'\n]{0,20}?\bvalue\s*=\s*\\?["'])([^"']+)`)

	// 帳號欄位：同一組預設憑證的「另一半」。
	//
	// 生產證據裡那組預設測試帳號 RS106 既是密碼也是帳號，
	// 而且平台報告指出「該帳號本身可能仍有效」（實測帳號仍被服務端接受處理）。
	// 只遮密碼欄位，帳號欄位會把同一組憑證的另一半帶出去 —— 實測 MySQL 命中 18 筆：
	//   <input name="_txtUsername" value="RS106" ...>
	//   &_txtUsername=RS106&_txtPassword=wrongpw
	//   实测 RS106 账号仍被服务端接受处理（散文，靠工作階段抹除）
	//
	// 欄位名限於「登入表單」常見的名字（username／uname／loginid／accountid…），
	// 不含通用的 account／user／login：那會把 IDOR 證據裡的查詢參數
	// （例如 ?account=12345）洗掉，而那正是漏洞成立的要點。
	//
	// 值一律要通過 looksLikeCredential：一般的 admin／guest 不是秘密。
	secretUsernameInputPat = regexp.MustCompile(`(?i)(<input[^>]*?\b(?:name|id)\s*=\s*\\?["'][^"'>]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[^"'>]*["'][^>]*?\bvalue\s*=\s*\\?["'])([^"']+)`)

	// value 屬性排在 name/id 前面的情況。
	secretUsernameInputValueFirstPat = regexp.MustCompile(`(?i)(<input[^>]*?\bvalue\s*=\s*\\?["'])([^"']+)([^>]*?\b(?:name|id)\s*=\s*\\?["'][^"'>]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[^"'>]*["'])`)

	// 「欄位名 的 value="..."」寫法。
	secretUsernameFieldValuePat = regexp.MustCompile(`(?i)((?:[A-Za-z0-9_.\-]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[A-Za-z0-9_.\-]*)[^"'\n]{0,20}?\bvalue\s*=\s*\\?["'])([^"']+)`)

	// 表單／查詢參數寫法：&_txtUsername=RS106
	secretUsernameParamPat = regexp.MustCompile(`(?i)([?&;][A-Za-z0-9_.\-]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[A-Za-z0-9_.\-]*=)([^&\s"'<>]+)`)

	// 帳號欄位的行內寫法：_txtUsername=RS106
	//
	// 為什麼要另外一條：參數規則要求前面有 ?/&/;，
	// 但同一個參數也會出現在散文與 JSON 片段裡
	// （例如「（漏洞 a83c38e5，_txtUsername=RS106 / _txtPassword=***」），
	// 那裡前面是逗號不是參數分隔符 → 只靠參數規則會整組漏掉。
	// 值的字元類必須排除 &，否則 "_txtUsername=guest&_txtPassword=xxx"
	// 會把後半段整包當成一個值（連帶把密碼參數一起吃掉），
	// 而且 "guest&_txtPassword=wrongpw" 含有 "=" → 通過 looksLikeCredential 守衛 → 被誤遮。
	secretUsernameInlinePat = regexp.MustCompile(`(?i)([A-Za-z0-9_.\-]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[A-Za-z0-9_.\-]*\s*[:=]\s*)([^&\s"',;<>]{4,})`)

	// 帳號欄位名後面接著「引號包住的值」，中間夾一點中文敘述：
	//   仅把 `_txtUsername` 改回 `RS106`
	//   把 "username" 設為 "RS106"
	//
	// 這是同一個值在散文裡的第三種寫法；值仍然要通過 looksLikeCredential 才會被遮。
	secretUsernameQuotedValuePat = regexp.MustCompile("(?i)([A-Za-z0-9_.\\-]*(?:username|user_name|uname|loginid|login_id|accountid|userid|user_id)[A-Za-z0-9_.\\-]*[^\\n]{0,20}?[\\?\"'`（(【\\[「])([A-Za-z0-9_\\-+/=.]{4,})")

	// ipTokenPattern 切出兩類片段：
	//   - %XX：URL 編碼（%20 是空白、%2C 是逗號…），必須視為不可分割的單一令牌；
	//   - 數字點號序列：IPv4 的候選。
	//
	// 為什麼不能只靠 \b 單詞邊界：「%2052.128.238.210」裡，IP 前面緊接的是
	// 「%20」的 0（數字＝word char），\b 不成立 → 整組 IP 被跳過，
	// 內網位址就這樣原封不動進了外部資料庫。切掉 %XX 之後邊界才落在正確位置。
	ipTokenPattern = regexp.MustCompile(`%[0-9A-Fa-f]{2}|[0-9][0-9.]*`)

	// ipv6TokenPattern 抓 IPv6 候選：至少兩個字元的十六進位／冒號序列。
	ipv6TokenPattern = regexp.MustCompile(`%[0-9A-Fa-f]{2}|[0-9A-Fa-f:]{2,}`)

	// percentEncodedIPPattern 抓「整段被 percent-編碼的位址」，
	// 例如 %31%32%2E%33%2E%34%2E%35（=1.2.3.4）。編碼是位址外洩的變體。
	percentEncodedIPPattern = regexp.MustCompile(`(?:%[0-9A-Fa-f]{2}){4,}`)
)

const (
	// InternalRedacted 私有／回環／link-local 位址的統一代號。
	InternalRedacted = "internal-redacted"
	// RedactedSecret 憑證的统一代號。
	RedactedSecret = "***"
)

// Mask 依政策遮蔽一段文字。
//
// 單段遮蔽不會知道「同一筆資料裡的其他欄位」有沒有出現同一個憑證值。
// 需要跨欄位一致地去識別化時請用 NewSession。
func (p Policy) Mask(text string) string {
	return p.NewSession().Mask(text)
}

// Session 是「單一筆資料」的遮蔽工作階段。
//
// 為什麼需要：同一組預設帳密會以不同欄位、不同語境出現在同一筆資料裡。
// 生產證據的實例（同一個值 RS106 既是帳號也是密碼）：
//
//	<input type="password" name="_txtPassword" value="RS106">
//	<input type="text"   name="_txtUsername" value="RS106">
//
// 只遮 password 欄位，username 欄位就會把**同一個密碼值**原樣帶進外部庫
// （實測 MySQL 命中 104 筆）。
//
// Session 會記下本筆資料裡被辨識為憑證的字面值，
// 讓其他欄位（以及後續一輪）能把同一個值一併抹掉。
type Session struct {
	policy    Policy
	secrets   map[string]struct{}
	scrubbers map[string]*regexp.Regexp
	// ordered 是 secrets 的穩定排序快取（長度優先、同長度按字典序）。
	// 抹除有順序依賴，所以必須固定順序 —— 見 sortedSecrets 的說明。
	ordered []string
}

// NewSession 建立一個遮蔽工作階段。
func (p Policy) NewSession() *Session {
	return &Session{
		policy:    p,
		secrets:   make(map[string]struct{}),
		scrubbers: make(map[string]*regexp.Regexp),
	}
}

// Mask 遮蔽一段文字，並把本段裡被辨識為憑證的字面值記進工作階段。
func (s *Session) Mask(text string) string {
	if text == "" {
		return text
	}
	// 先把非法 UTF-8 位元組換掉：生產資料庫裡有些欄位存了截斷的多位元組字元
	// （例如證據片段只寫了「\xE6\x8E」三個位元組的前兩個），原樣送到 MySQL
	// 會被 utf8mb4 以 Error 1366 整筆拒收。
	text = strings.ToValidUTF8(text, "\uFFFD")
	out := text
	if s.policy.MaskSecrets {
		out = s.policy.maskSecrets(out, s)
	}
	if s.policy.MaskHosts {
		out = urlPattern.ReplaceAllStringFunc(out, func(raw string) string {
			return s.policy.maskHostInURL(raw)
		})
		out = hostTokenPattern.ReplaceAllStringFunc(out, func(raw string) string {
			host := strings.TrimSuffix(strings.TrimPrefix(raw, "`"), "'")
			return "`" + pseudonym("host", host) + "`"
		})
	}
	if s.policy.MaskIPs {
		out = s.policy.maskIPv4(out)
		out = s.policy.maskIPv6(out)
		out = s.policy.maskPercentEncodedIPv4(out)
	}
	return out
}

// Scrub 把工作階段已知的憑證值從文字裡抹掉。
//
// 這是「跨欄位一致去識別化」的第二輪：某個值只要在這一筆資料的任何一個地方
// 被辨識為憑證，它在其他欄位裡就一起被抹掉。
func (s *Session) Scrub(text string) string {
	if text == "" || len(s.secrets) == 0 {
		return text
	}
	for _, secret := range s.sortedSecrets() {
		text = s.scrubLiteral(text, secret)
	}
	return text
}

// sortedSecrets 回傳穩定排序後的憑據清單：長度優先、同長度再按字典序。
//
// 為什麼一定要排序：抹除是「有順序」的 —— 先抹掉短的會讓長的只被抹掉一部分。
// 生產資料裡同一組 base64 常數會以兩種形式被認出（帶 padding 的 "AbC…==" 與
// 不帶的 "AbC…"），先抹短的那個會留下 "==" 尾巴，先抹長的那個才會整段消失。
//
// 為什麼這是硬性要求（不只是美觀）：Go 的 map 迭代順序是隨機的，
// 不排序的話同一筆資料每次遮蔽出來的結果可能不同 ——
// 實測同一筆記錄在兩次匯入之間 checksum 改變，接收端帳本永遠收斂不了，
// 而且外部庫裡同一筆資料會有兩種內容。遮蔽必須是確定性的函式。
func (s *Session) sortedSecrets() []string {
	if s.ordered != nil {
		return s.ordered
	}
	ordered := make([]string, 0, len(s.secrets))
	for secret := range s.secrets {
		ordered = append(ordered, secret)
	}
	sort.Slice(ordered, func(i, j int) bool {
		if len(ordered[i]) != len(ordered[j]) {
			return len(ordered[i]) > len(ordered[j])
		}
		return ordered[i] < ordered[j]
	})
	s.ordered = ordered
	// TEMP-DETERMINISM-PROBE
	// return ordered
	return s.ordered
}

// record 記下一個被遮蔽的值，讓它能在同一筆資料的其他欄位裡一併抹掉。
//
// 只記錄「看起來像憑證」且長度足夠的值：
//   - 太短的值（例如 "2024"）在自然文字裡出現太頻繁，抹掉會傷到無關內容；
//   - 散文（例如 "recommendation"）根本不該被當成憑證值散播。
func (s *Session) record(value string) {
	if s == nil || value == "" {
		return
	}
	value = strings.TrimSpace(value)
	if len(value) < 5 {
		return
	}
	// 帳密對（TaipeiCityFireDep / TaipeiCityFireDep2016）要分開記，
	// 否則只有「整對」的字面值會被抹掉，單獨出現的密碼不會。
	for _, part := range strings.Split(value, "/") {
		part = strings.TrimSpace(part)
		if len(part) < 5 || !looksLikeCredential(part) {
			continue
		}
		if _, exists := s.secrets[part]; !exists {
			s.secrets[part] = struct{}{}
			// 新增憑據 → 排序快取失效（見 sortedSecrets）。
			s.ordered = nil
		}
	}
}

// scrubLiteral 把一個字面值從文字裡抹掉，並避免誤傷更長的字串。
//
// 例：已知憑證 "RS106" 不該把 "RS1065" 一起吃掉。
//
// 為什麼不用「邊界一起吃掉」的正規表示式：
// Go 的 RE2 沒有 lookaround，要表達「左右都不能接著 word 字元」就只能把邊界
// 納入比對，而邊界一旦被比對吃掉，相鄰的兩次出現就會漏掉後面那一次 ——
// "RS106/RS106"（帳號與密碼是同一組預設值）會變成 "***/RS106"，
// 密碼就這樣留在外部資料庫裡（實測 MySQL 命中 68 筆）。
//
// 所以改成自己掃描匹配位置：邊界用零寬度判斷，不消耗任何字元。
//
// 為什麼大小寫不敏感：
// 生產證據裡同一組預設帳密會以不同大小寫出現（口令變體清單裡的 "rs106"、
// "RS106!"、"RS106@2026"）。大小寫不同的同一組憑證仍然是同一組憑證，
// 只擋大小寫等於把一半的變體留在外面（實測仍命中多筆）。
func (s *Session) scrubLiteral(text, secret string) string {
	if secret == "" || text == "" {
		return text
	}
	re, ok := s.scrubbers[secret]
	if !ok {
		// (?i)：同一組憑證的大小寫變體一起抹掉。
		re = regexp.MustCompile(`(?i)` + regexp.QuoteMeta(secret))
		s.scrubbers[secret] = re
	}

	matches := re.FindAllStringIndex(text, -1)
	if len(matches) == 0 {
		return text
	}

	// 值的首尾若不是 word 字元，本來就不需要那一側的邊界
	// （例如值本身以符號開頭時，左邊接著字母不構成誤傷）。
	requireLeft := isWordByte(secret[0])
	requireRight := isWordByte(secret[len(secret)-1])

	var builder strings.Builder
	last := 0
	replaced := false
	for _, match := range matches {
		start, end := match[0], match[1]
		if requireLeft && start > 0 && isWordByte(text[start-1]) {
			continue
		}
		if requireRight && end < len(text) && isWordByte(text[end]) {
			continue
		}
		builder.WriteString(text[last:start])
		builder.WriteString(RedactedSecret)
		last = end
		replaced = true
	}
	if !replaced {
		return text
	}
	builder.WriteString(text[last:])
	return builder.String()
}

// maskSecrets 遮蔽文字中的憑證。
//
// 順序有意義：先處理 Bearer／Basic 標頭，再處理行內的 key=value。
// 反過來的話，行內規則會先把「Bearer」這個方案名換掉，
// 真正的 token 就變成沒有前綴的孤兒字串而漏掉。
//
// rec 可能是 nil（單段遮蔽時）；給了它就會把被遮蔽的值記錄下來，
// 讓同一筆資料的其他欄位能把同一個值一併抹掉。
func (p Policy) maskSecrets(text string, rec *Session) string {
	out := replaceSecretValue(secretParamPat, text, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValue(bearerPat, out, rec, 2, func(groups []string) string {
		return groups[1] + " " + RedactedSecret
	})
	out = replaceSecretValue(secretJSONPat, out, rec, 3, func(groups []string) string {
		return groups[1] + groups[2] + RedactedSecret
	})
	out = replaceSecretValue(secretHTMLInputPat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValue(secretHTMLInputValueFirstPat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret + groups[3]
	})
	out = replaceSecretValue(secretFieldValuePat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	// 帳號欄位：值必須看起來像憑證才遮（admin／guest 不是秘密），
	// 而且欄位名限於登入表單常見的名字，避免洗掉 IDOR 證據裡的查詢參數。
	out = replaceSecretValueGuarded(secretUsernameInputPat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValueGuarded(secretUsernameInputValueFirstPat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret + groups[3]
	})
	out = replaceSecretValueGuarded(secretUsernameFieldValuePat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValueGuarded(secretUsernameParamPat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValueGuarded(secretUsernameInlinePat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = replaceSecretValueGuarded(secretUsernameQuotedValuePat, out, rec, 2, func(groups []string) string {
		return groups[1] + RedactedSecret
	})
	out = secretInline.ReplaceAllStringFunc(out, func(match string) string {
		groups := secretInline.FindStringSubmatch(match)
		if len(groups) < 3 {
			return match
		}
		// 「Authorization: Bearer xxx」裡的 Bearer 只是方案名，不是憑證本身；
		// 真正的 token 已經由 bearerPat 處理掉了，這裡不要動它。
		value := strings.TrimSpace(groups[2])
		if strings.EqualFold(value, "bearer") || strings.EqualFold(value, "basic") {
			return match
		}
		rec.record(value)
		return groups[1] + RedactedSecret
	})
	out = secretCloudKeyPat.ReplaceAllStringFunc(out, func(match string) string {
		groups := secretCloudKeyPat.FindStringSubmatch(match)
		if len(groups) < 5 {
			return match
		}
		value := groups[4]
		if !looksLikeCredential(value) {
			return match
		}
		rec.record(value)
		return groups[1] + groups[2] + groups[3] + RedactedSecret
	})
	out = secretLoosePat.ReplaceAllStringFunc(out, func(match string) string {
		groups := secretLoosePat.FindStringSubmatch(match)
		if len(groups) < 4 {
			return match
		}
		if !looksLikeCredential(groups[3]) {
			return match
		}
		rec.record(groups[3])
		return groups[1] + groups[2] + RedactedSecret
	})
	return out
}

// replaceSecretValue 把比對到的憑證值換成 ***，並把值記錄到工作階段。
//
// valueGroup 是「被遮蔽的值」在比對結果裡的群組編號；
// rebuild 負責組出替換後的字串（有些規則的群組編號不連續）。
func replaceSecretValue(re *regexp.Regexp, text string, rec *Session, valueGroup int, rebuild func(groups []string) string) string {
	return re.ReplaceAllStringFunc(text, func(match string) string {
		groups := re.FindStringSubmatch(match)
		if len(groups) <= valueGroup {
			return match
		}
		rec.record(groups[valueGroup])
		return rebuild(groups)
	})
}

// replaceSecretValueGuarded 與 replaceSecretValue 相同，但值必須先通過
// looksLikeCredential 才會被遮蔽與記錄。
//
// 為什麼需要守衛：帳號欄位（username／uname…）的值很多時候不是秘密
// （admin、guest、test），無條件遮掉只會讓證據變難讀；
// 反過來，「看起來像憑證」的帳號值（例如 RS106這種預設測試帳號）
// 就是憑證的一部分，必須遮。
func replaceSecretValueGuarded(re *regexp.Regexp, text string, rec *Session, valueGroup int, rebuild func(groups []string) string) string {
	return re.ReplaceAllStringFunc(text, func(match string) string {
		groups := re.FindStringSubmatch(match)
		if len(groups) <= valueGroup {
			return match
		}
		if !looksLikeCredential(groups[valueGroup]) {
			return match
		}
		rec.record(groups[valueGroup])
		return rebuild(groups)
	})
}

// looksLikeCredential 判斷一個值「看起來像憑證」而不是散文。
//
// 判準（三者任一成立即可）：
//   - 含數字：hunter2、TestPwd_20260928、LTAI5t5jvFcXA8DDvSbtqeSy
//   - 含分隔符（- _ / = .）：JWT（eyJ….abc.def）、base64、駝峰式識別碼
//   - 長度 ≥ 16 且有大寫連續片段：AWS AccessKeyId 這類全大寫代號
//     （實測過 AKIAXXXXXXXXXXXXXXXX —— 20 個字母、**一個數字都沒有**，
//      所以「必須含數字」這種簡單判準會把它整組漏掉）
//
// 反過來，「recommendation」「exploitation」「authorization」這類散文
// 三個判準都不成立 → 不會被洗掉。
func looksLikeCredential(value string) bool {
	if !hasLetter(value) {
		return false
	}
	if hasDigit(value) {
		return true
	}
	for i := 0; i < len(value); i++ {
		switch value[i] {
		case '-', '_', '/', '=', '.':
			return true
		}
	}
	return len(value) >= 16 && hasUpperRun(value, 3)
}

// hasUpperRun 判斷字串裡是否有一段連續 run 個以上的大寫字母。
func hasUpperRun(text string, run int) bool {
	count := 0
	for i := 0; i < len(text); i++ {
		if text[i] >= 'A' && text[i] <= 'Z' {
			count++
			if count >= run {
				return true
			}
			continue
		}
		count = 0
	}
	return false
}

// hasLetter 判斷字串是否含英文字母。
func hasLetter(text string) bool {
	for i := 0; i < len(text); i++ {
		char := text[i]
		if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') {
			return true
		}
	}
	return false
}

// hasDigit 判斷字串是否含數字。
func hasDigit(text string) bool {
	for i := 0; i < len(text); i++ {
		if text[i] >= '0' && text[i] <= '9' {
			return true
		}
	}
	return false
}

// maskIPv4 遮蔽文字裡的 IPv4 位址。
//
// 判斷方式是「整段數字點號序列看起來像位址就遮」，而不是靠 \b 判斷左右邊界：
// 前面接著 %20（URL 編碼空白）、字母或底線時 \b 會整組失效，
// 真實位址就這樣漏出去（已在生產資料驗證到內網位址被原樣寫進外部 MySQL）。
func (p Policy) maskIPv4(text string) string {
	if !p.MaskIPs || text == "" {
		return text
	}
	var builder strings.Builder
	builder.Grow(len(text))
	last := 0
	for _, loc := range ipTokenPattern.FindAllStringIndex(text, -1) {
		token := text[loc[0]:loc[1]]
		if strings.HasPrefix(token, "%") {
			// %XX 是編碼令牌，本身不含位址原文。
			continue
		}
		address, ok := extractIPv4(token)
		if !ok {
			continue
		}
		builder.WriteString(text[last:loc[0]])
		builder.WriteString(p.maskIP(address))
		last = loc[0] + len(address)
	}
	builder.WriteString(text[last:])
	return builder.String()
}

// extractIPv4 從數字點號序列裡取出 IPv4 字面量。
//
// 取「前四段」而不是要求整段剛好四段，因為真實資料裡這兩種都存在：
//   - tcpdump 的 ip.port 記法："223.200.50.93.25"（前面是真實位址）
//   - 產品版本："WebLogic Server 10.3.6.0.0"
// 只認整段四段的話，前者會整組漏掉 —— 那正是真實位址。
//
// 第四段必須是完整的 1-3 位數字，"10.1.0.2134" 不能被拆成 "10.1.0.213"；
// "1.18.0"（版本）、"1.2.3.4.5"（五段）也各自有各自的處理。
func extractIPv4(token string) (string, bool) {
	parts := strings.Split(token, ".")
	if len(parts) < 4 {
		return "", false
	}
	head := parts[:4]
	for _, part := range head {
		if len(part) == 0 || len(part) > 3 {
			return "", false
		}
		value := 0
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return "", false
			}
			value = value*10 + int(part[i]-'0')
		}
		if value > 255 {
			return "", false
		}
	}
	return strings.Join(head, "."), true
}

// maskIPv6 遮蔽文字裡的 IPv6 位址。
//
// IPv6 的邊界比 IPv4 嚴格：位址兩側不能緊接著 word 字元，
// 否則 C++/Python 的 scope 運算子（Class::Method、std::vector）會被整片遮掉。
func (p Policy) maskIPv6(text string) string {
	if !p.MaskIPs || !strings.Contains(text, ":") {
		return text
	}
	var builder strings.Builder
	builder.Grow(len(text))
	last := 0
	for _, loc := range ipv6TokenPattern.FindAllStringIndex(text, -1) {
		token := text[loc[0]:loc[1]]
		if strings.HasPrefix(token, "%") {
			continue
		}
		if !isIPv6Literal(token) {
			continue
		}
		if !tokenBoundaryOK(text, loc[0], loc[1]) {
			continue
		}
		builder.WriteString(text[last:loc[0]])
		builder.WriteString(p.maskIP(token))
		last = loc[1]
	}
	builder.WriteString(text[last:])
	return builder.String()
}

// tokenBoundaryOK 判斷 token 的左右邊界是否可接受。
//
// 規則：token 前後不能緊接著 word 字元（字母／數字／底線）——
// 那多半表示它是識別碼的一部分（scope 運算子、版本字串）而不是獨立位址。
// 例外：前面是 %XX 編碼時放行 —— 「%20fe80::1」裡的 fe80 才是位址起點。
func tokenBoundaryOK(text string, start, end int) bool {
	if start > 0 && isWordByte(text[start-1]) && !endsWithEscape(text, start) {
		return false
	}
	if end < len(text) && isWordByte(text[end]) {
		return false
	}
	return true
}

// endsWithEscape 判斷 token 開頭前是不是接著一段 %XX 編碼。
func endsWithEscape(text string, start int) bool {
	if start < 3 || text[start-3] != '%' {
		return false
	}
	return isHexByte(text[start-2]) && isHexByte(text[start-1])
}

// isWordByte 判斷是否為 ASCII 的 word 字元（字母／數字／底線）。
func isWordByte(char byte) bool {
	switch {
	case char >= 'a' && char <= 'z':
		return true
	case char >= 'A' && char <= 'Z':
		return true
	case char >= '0' && char <= '9':
		return true
	case char == '_':
		return true
	default:
		return false
	}
}

// isHexByte 判斷是否為十六進位數字。
func isHexByte(char byte) bool {
	switch {
	case char >= '0' && char <= '9':
		return true
	case char >= 'a' && char <= 'f':
		return true
	case char >= 'A' && char <= 'F':
		return true
	default:
		return false
	}
}

// isIPv6Literal 判斷字串是不是 IPv6 位址字面量。
//
// 額外要求「至少兩個十六進位數字」：C++/Python 的 scope 運算子（std::vector）
// 也長得像位址（d::），但它不是位址，遮掉會把程式碼片段變成亂碼。
// ::1 與 :: 這種特殊形式另外放行。
func isIPv6Literal(token string) bool {
	if strings.Count(token, ":") < 2 {
		return false
	}
	parsed := net.ParseIP(token)
	if parsed == nil || parsed.To4() != nil {
		return false
	}
	digits := 0
	for i := 0; i < len(token); i++ {
		char := token[i]
		if (char >= '0' && char <= '9') || (char >= 'a' && char <= 'f') || (char >= 'A' && char <= 'F') {
			digits++
		}
	}
	if digits >= 2 {
		return true
	}
	return token == "::1" || token == "::"
}

// maskPercentEncodedIPv4 遮蔽「整段被 percent-編碼的位址」。
//
// 編碼後的位址對人眼不可見，但對倉儲來說一樣是位址；
// 這是位址外洩最容易被忽略的變體。
func (p Policy) maskPercentEncodedIPv4(text string) string {
	if !p.MaskIPs || !strings.Contains(text, "%") {
		return text
	}
	return percentEncodedIPPattern.ReplaceAllStringFunc(text, func(raw string) string {
		address, ok := extractIPv4(decodePercentEscapes(raw))
		if !ok {
			return raw
		}
		return p.maskIP(address)
	})
}

// decodePercentEscapes 把 %XX 還原成字元。
func decodePercentEscapes(raw string) string {
	var builder strings.Builder
	builder.Grow(len(raw))
	for i := 0; i < len(raw); i++ {
		if raw[i] == '%' && i+2 < len(raw) {
			if value, err := strconv.ParseUint(raw[i+1:i+3], 16, 8); err == nil {
				builder.WriteByte(byte(value))
				i += 2
				continue
			}
		}
		builder.WriteByte(raw[i])
	}
	return builder.String()
}

// hostTokenPattern 抓出獨立的網域名稱（URL 之外的文字）。
var hostTokenPattern = regexp.MustCompile("`[a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,}`")

func (p Policy) maskHostInURL(raw string) string {
	parsed, err := url.Parse(raw)
	if err != nil || parsed.Host == "" {
		return raw
	}
	parsed.Host = pseudonym("host", parsed.Host)
	return parsed.String()
}

// maskIP 遮蔽單一 IP 位址。
func (p Policy) maskIP(raw string) string {
	for _, redacted := range p.RedactIPs {
		if redacted != "" && strings.EqualFold(redacted, raw) {
			return InternalRedacted
		}
	}
	if isPrivateIP(raw) {
		// 私有、回環、link-local 位址一律歸為 internal-redacted：
		// 這些位址沒有分析價值（不是目標），卻會暴露測試環境的網段拓撲。
		return InternalRedacted
	}
	return pseudonym("ip", raw)
}

// isPrivateIP 判斷是否為私有／回環／link-local／未指定位址。
func isPrivateIP(raw string) bool {
	parts := strings.Split(raw, ".")
	if len(parts) != 4 {
		// IPv6 交由呼叫端處理；這裡保守視為需要遮蔽。
		return true
	}
	numbers := make([]int, 0, 4)
	for _, part := range parts {
		value := 0
		for _, char := range part {
			if char < '0' || char > '9' {
				return false
			}
			value = value*10 + int(char-'0')
		}
		if value > 255 {
			return false
		}
		numbers = append(numbers, value)
	}
	switch {
	case numbers[0] == 10:
		return true
	case numbers[0] == 127:
		return true
	case numbers[0] == 0:
		return true
	case numbers[0] == 169 && numbers[1] == 254:
		return true
	case numbers[0] == 172 && numbers[1] >= 16 && numbers[1] <= 31:
		return true
	case numbers[0] == 192 && numbers[1] == 168:
		return true
	case numbers[0] == 100 && numbers[1] >= 64 && numbers[1] <= 127:
		return true
	default:
		return false
	}
}

// pseudonym 產生穩定代號：同一個輸入永遠得到同一個代號。
func pseudonym(prefix, value string) string {
	sum := sha256.Sum256([]byte(value))
	return prefix + "-" + hex.EncodeToString(sum[:])[:8]
}

// Pseudonym 對外提供穩定代號產生器，讓匯出端與查詢端對得上。
func Pseudonym(prefix, value string) string {
	return pseudonym(prefix, value)
}
