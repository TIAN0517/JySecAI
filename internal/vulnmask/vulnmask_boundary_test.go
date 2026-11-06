package vulnmask

import (
	"strings"
	"testing"
)

// TestMaskCatchesIPAfterURLEncodedSpace 擋住最危險的漏遮情境。
//
// 生產資料實測：證據欄位裡有
//
//	set-cookie: vsf-IPAddress=52.128.238.210%2C%2010.1.0.213
//
// 其中 10.1.0.213 因為前面緊接著「%20」的數字（word char）而整組被跳過，
// 內網位址就這樣原封不動寫進了外部 MySQL。
func TestMaskCatchesIPAfterURLEncodedSpace(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("set-cookie: vsf-IPAddress=52.128.238.210%2C%2010.1.0.213; Path=/")
	if strings.Contains(got, "52.128.238.210") {
		t.Fatalf("公網位址未被遮蔽: %s", got)
	}
	if strings.Contains(got, "10.1.0.213") {
		t.Fatalf("內網位址未被遮蔽: %s", got)
	}
	if !strings.Contains(got, InternalRedacted) {
		t.Fatalf("內網位址應歸為 %s: %s", InternalRedacted, got)
	}
	if !strings.Contains(got, "%2C%20") {
		t.Fatalf("編碼本身不該被破壞: %s", got)
	}
}

// TestMaskCatchesIPAdjacentToWordCharacters 擋住「位址緊接字母或底線」的漏遮。
func TestMaskCatchesIPAdjacentToWordCharacters(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"來源IP10.1.0.213 回應",
		"src_52.128.238.210 命中",
		"X-Forwarded-For:52.128.238.210",
	} {
		got := policy.Mask(text)
		if strings.Contains(got, "10.1.0.213") || strings.Contains(got, "52.128.238.210") {
			t.Errorf("位址未被遮蔽: %s", got)
		}
	}
}

// TestMaskCatchesIPBeforeSentencePunctuation 擋住句末句點讓位址漏掉。
func TestMaskCatchesIPBeforeSentencePunctuation(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("連線到 118.163.168.146.")
	if strings.Contains(got, "118.163.168.146") {
		t.Fatalf("句末的位址未被遮蔽: %s", got)
	}
	if !strings.Contains(got, "ip-") {
		t.Fatalf("應換成穩定代號: %s", got)
	}
	if !strings.HasSuffix(got, ".") {
		t.Fatalf("句點屬於句子，不該被吃掉: %s", got)
	}
}

// TestMaskKeepsNonAddressNumbersIntact 確認遮蔽沒有變成「數字全殺」。
func TestMaskKeepsNonAddressNumbersIntact(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"nginx/1.24.0 回應正常",
		"2026-10-22 基站線",
		"HTTP/1.1 302 Found",
		"row_count=12345 byte_size=6789",
	} {
		got := policy.Mask(text)
		if got != text {
			t.Errorf("非位址內容被改動: %q -> %q", text, got)
		}
	}
}

// TestMaskCatchesIPInsideLongerDottedRun 擋住 tcpdump 的 ip.port 記法。
//
// 生產資料實測：證據裡有「223.200.50.93.25: Flags [S]」——
// 那是真實公網位址加上埠號。只認「整段剛好四段」的規則會整組漏掉它。
func TestMaskCatchesIPInsideLongerDottedRun(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("tcpdump 抓包: 16:57:31.726 源 -> 223.200.50.93.25: Flags [S]")
	if strings.Contains(got, "223.200.50.93") {
		t.Fatalf("五段寫法的位址未被遮蔽: %s", got)
	}
	if !strings.Contains(got, "ip-") {
		t.Fatalf("應換成穩定代號: %s", got)
	}
	if !strings.Contains(got, ".25") {
		t.Fatalf("埠號不該被吃掉: %s", got)
	}
}

// TestMaskKeepsFourDigitOctetIntact 確認不會把較長的數字組拆成位址。
func TestMaskKeepsFourDigitOctetIntact(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("10.1.0.2134 不是位址")
	if strings.Contains(got, "ip-") {
		t.Fatalf("四段數字不該被當成位址遮蔽: %s", got)
	}
}

// TestMaskCatchesNonWhitelistedCredentialParams 擋住「參數名不在白名單」的憑證外洩。
//
// 生產資料實測：userpassword=、client_secret=、csrfToken=、jsessionid=、
// OSSAccessKeyId=、X-Amz-Credential=、Signature= 全都曾原樣進入外部 MySQL。
func TestMaskCatchesNonWhitelistedCredentialParams(t *testing.T) {
	policy := DefaultPolicy()
	cases := []struct {
		text string
		leak string
	}{
		{"userid=bob&userpassword=TaipeiCityFireDep2016", "TaipeiCityFireDep2016"},
		{"client_id=x&client_secret=invalid", "invalid"},
		{"--data 'csrfToken=abc123XYZ'", "abc123XYZ"},
		{";jsessionid=4C518E72C8BE1B3DC1A79B2F54BEFC6C", "4C518E72C8BE1B3DC1A79B2F54BEFC6C"},
		{"OSSAccessKeyId=LTAI5t5jvFcXA8DDvSbtqeSy", "LTAI5t5jvFcXA8DDvSbtqeSy"},
		{"X-Amz-Credential=AKIAXXXXXXXXXXXXXXXX%2F20261016", "AKIAXXXXXXXXXXXXXXXX"},
		{"Signature=jf%2BqqSHaCGkoxGvcw%2FxxPoyJu", "jf%2BqqSHaCGkoxGvcw"},
		{"?accessToken=eyJhbGciOiJIUzI1NiJ9", "eyJhbGciOiJIUzI1NiJ9"},
		{"_txtPassword=RS106&_txtUsername=admin", "RS106"},
	}
	for _, item := range cases {
		got := policy.Mask(item.text)
		if strings.Contains(got, item.leak) {
			t.Errorf("憑證 %s 未被遮蔽 (%s): %s", item.leak, item.text, got)
		}
		if !strings.Contains(got, RedactedSecret) {
			t.Errorf("應換成 %s: %s", RedactedSecret, got)
		}
	}
}

// TestMaskCatchesInlineCredentialForms 擋住本文中的憑證（含嵌在識別碼裡的）。
func TestMaskCatchesInlineCredentialForms(t *testing.T) {
	policy := DefaultPolicy()
	cases := []struct {
		text string
		leak string
	}{
		{"password: Sup3rSecret", "Sup3rSecret"},
		{"myPassword=Sup3rSecret", "Sup3rSecret"},
		{"csrfToken=eyJhbGciOiJIUzI1NiJ9", "eyJhbGciOiJIUzI1NiJ9"},
		{"Authorization: Bearer eyJhbGciOiJIUzI1NiJ9", "eyJhbGciOiJIUzI1NiJ9"},
	}
	for _, item := range cases {
		got := policy.Mask(item.text)
		if strings.Contains(got, item.leak) {
			t.Errorf("憑證 %s 未被遮蔽 (%s): %s", item.leak, item.text, got)
		}
	}
}

// TestMaskKeepsNonCredentialQueryParams 確認一般查詢參數沒有被誤殺。
func TestMaskKeepsNonCredentialQueryParams(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"?author=1",
		"?page=3&size=20",
		"?Keyword=1&PageInfo.CurrentPageNumber=1",
	} {
		got := policy.Mask(text)
		if got != text {
			t.Errorf("非憑證參數被改動: %q -> %q", text, got)
		}
	}
}

// TestMaskCatchesJSONAndProseCredentials 擋住 JSON 形式與散文形式的憑證。
//
// 生產資料實測（這兩種在第一次修補後仍漏在外部 MySQL 裡）：
//   "PWD":"TestPwd_20260928"                      ← JSON 欄位
//   IAM Access Key ID : AKIAXXXXXXXXXXXXXXXX      ← 標頭列印
//   立即轮换已暴露的 AccessKeyId `LTAI5t5jvFcXA8DDvSbtqeSy`
//   立即轮换泄露的北水处凭据 TaipeiCityFireDep/TaipeiCityFireDep2016
//   泄露 OSS AccessKeyId（LTAI5t5jvFcXA8DDvSbtqeSy）与 bucket 名
func TestMaskCatchesJSONAndProseCredentials(t *testing.T) {
	policy := DefaultPolicy()
	cases := []struct {
		text string
		leak string
	}{
		{`"PWD":"TestPwd_20260928"`, "TestPwd_20260928"},
		{`"AccessKeyId": "LTAI5t5jvFcXA8DDvSbtqeSy"`, "LTAI5t5jvFcXA8DDvSbtqeSy"},
		{`{"password":"hunter2xyz"}`, "hunter2xyz"},
		{"IAM Access Key ID : AKIAXXXXXXXXXXXXXXXX", "AKIAXXXXXXXXXXXXXXXX"},
		{"立即轮换已暴露的 AccessKeyId `LTAI5t5jvFcXA8DDvSbtqeSy`，按最小权限重新签发", "LTAI5t5jvFcXA8DDvSbtqeSy"},
		{"立即轮换泄露的北水处凭据 TaipeiCityFireDep/TaipeiCityFireDep2016，并同步通知", "TaipeiCityFireDep2016"},
		{"泄露 OSS AccessKeyId（LTAI5t5jvFcXA8DDvSbtqeSy）与 bucket 名", "LTAI5t5jvFcXA8DDvSbtqeSy"},
		{"立即轮换北水处 API 凭证（TaipeiCityFireDep / TaipeiCityFireDep2016 已在公网暴露）", "TaipeiCityFireDep2016"},
		{"登录页硬编码默认凭据 RS106/RS106（本资产凭据已失效，CWE-798）", "RS106/RS106"},
	}
	for _, item := range cases {
		got := policy.Mask(item.text)
		if strings.Contains(got, item.leak) {
			t.Errorf("憑證 %s 未被遮蔽 (%s): %s", item.leak, item.text, got)
		}
		if !strings.Contains(got, RedactedSecret) {
			t.Errorf("應換成 %s: %s", RedactedSecret, got)
		}
	}
}

// TestMaskCatchesHardcodedFormCredentials 擋住硬編碼預設帳密的表單／HTML 寫法。
func TestMaskCatchesHardcodedFormCredentials(t *testing.T) {
	policy := DefaultPolicy()
	cases := []struct {
		text string
		leak string
	}{
		{`<input type="password" name="_txtPassword" value="RS106">`, "RS106"},
		{`<input name="txtPassword" value='RS106'>`, "RS106"},
		{`_txtPassword 的 value="RS106"`, "RS106"},
	}
	for _, item := range cases {
		got := policy.Mask(item.text)
		if strings.Contains(got, item.leak) {
			t.Errorf("預設憑證 %s 未被遮蔽 (%s): %s", item.leak, item.text, got)
		}
	}
}

// TestMaskKeepsProseWithoutCredentialShapedValues 確認散文不會被無差別洗掉。
func TestMaskKeepsProseWithoutCredentialShapedValues(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"建议立即轮换凭据并通知 Taipei自来水处处理",
		"password rotation recommended for all accounts",
		"密碼強度要求至少 12 位",
		"token 使用者可完全控制该请求头",
	} {
		got := policy.Mask(text)
		if got != text {
			t.Errorf("散文被誤判成憑證: %q -> %q", text, got)
		}
	}
}

// TestMaskCatchesPercentEncodedIP 擋住「整段編碼的位址」。
func TestMaskCatchesPercentEncodedIP(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("目標 %31%32%2E%33%2E%34%2E%35 連線")
	if strings.Contains(got, "%31%32%2E%33%2E%34%2E%35") {
		t.Fatalf("percent 編碼的位址未被遮蔽: %s", got)
	}
	if !strings.Contains(got, "ip-") {
		t.Fatalf("應換成穩定代號: %s", got)
	}
}

// TestMaskCatchesIPv6 確認壓縮形式的 IPv6 也會被遮。
func TestMaskCatchesIPv6(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("代理 fe80::1 與 2001:db8::1 回應")
	for _, leak := range []string{"fe80::1", "2001:db8::1"} {
		if strings.Contains(got, leak) {
			t.Errorf("IPv6 %s 未被遮蔽: %s", leak, got)
		}
	}
	if got := policy.Mask("回環 ::1 已封鎖"); strings.Contains(got, "::1") {
		t.Errorf("回環 IPv6 未被遮蔽: %s", got)
	}
}

// TestMaskKeepsScopeOperator 確認 C++/Python 的 scope 運算子不會被誤判成位址。
func TestMaskKeepsScopeOperator(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("std::vector 與 Class::Method 都在")
	if got != "std::vector 與 Class::Method 都在" {
		t.Fatalf("scope 運算子不該被當成位址遮蔽: %s", got)
	}
}

// TestMaskCatchesCloudKeyAbbreviation 擋住「雲端金鑰縮寫」漏遮。
//
// 生產證據實測（MySQL 命中 10 筆）：
//
//	受影响 bucket：b9jiyun（OSS AK LTAI5t5jvFcXA8DDvSbtqeSy），租户 jiyun
//	5) 轮换已暴露的 AK（LTAI5t5jvFcXA8DDvSbtqeSy）与 appSecret
//
// 這裡用的是簡寫 AK／SK，不是 AccessKey／SecretKey，
// 所以只認長關鍵字的規則完全抓不到。
func TestMaskCatchesCloudKeyAbbreviation(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"受影响 bucket：b9jiyun（OSS AK LTAI5t5jvFcXA8DDvSbtqeSy），租户 jiyun",
		"5) 轮换已暴露的 AK（LTAI5t5jvFcXA8DDvSbtqeSy）与 appSecret，回溯 OSS 访问日志核查历史异常读取。",
		"OSS SK LTAI5t5jvFcXA8DDvSbtqeSy",
	} {
		got := policy.Mask(text)
		if strings.Contains(got, "LTAI5t5jvFcXA8DDvSbtqeSy") {
			t.Errorf("雲端金鑰未被遮蔽: %s", got)
		}
	}
}

// TestCloudKeyAbbreviationKeepsOrdinaryWords 確認縮寫關鍵字不會誤傷一般單字。
//
// AK／SK 只有兩三個字母，若不要求「獨立詞」，
// task／risk／ask／back／MASK 裡相鄰的字母都會被誤判。
func TestCloudKeyAbbreviationKeepsOrdinaryWords(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		"task 排程失敗",
		"risk assessment 報告",
		"ask for approval 流程",
		"back to safety 流程",
		"MASK 遮罩機制",
		"skateboard 稽核",
	} {
		if got := policy.Mask(text); got != text {
			t.Errorf("一般文字被誤遮: 原文=%q 遮蔽後=%q", text, got)
		}
	}
}

// TestSessionScrubsCredentialAcrossFields 擋住「同一組預設帳密跨欄位外洩」。
//
// 生產證據實測（MySQL 命中 104 筆）：同一個值 RS106 既是帳號也是密碼，
//
//	<input type="password" name="_txtPassword" value="RS106">
//	<input type="text"   name="_txtUsername" value="RS106">
//
// 只遮 password 欄位，username 欄位就會把同一個密碼值帶出去；
// 「grep 'value="RS106"'」這種純引號包起來的形式更是完全沒有憑據語境。
// 正確做法是：這一筆資料裡只要有地方被辨識為憑證，其他欄位一併抹掉。
func TestSessionScrubsCredentialAcrossFields(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()

	evidence := session.Mask(`<input type="password" name="_txtPassword" value="RS106">`)
	description := session.Mask(`_txtUsername 的 value="RS106"、_txtPassword 的 value="RS106"`)
	steps := session.Mask(`grep 'value="RS106"' → 命中 _txtUsername 与 _txtPassword 两处硬编码默认值`)
	plain := session.Mask(`（账号输入框预填 RS106）`)

	// 第二輪：把收集到的憑證值在所有欄位裡一併抹掉。
	evidence = session.Scrub(evidence)
	description = session.Scrub(description)
	steps = session.Scrub(steps)
	plain = session.Scrub(plain)

	for name, text := range map[string]string{
		"evidence": evidence, "description": description, "steps": steps, "plain": plain,
	} {
		if strings.Contains(text, "RS106") {
			t.Errorf("%s 欄位仍帶著憑證值: %s", name, text)
		}
	}
	if !strings.Contains(evidence, RedactedSecret) {
		t.Errorf("密碼欄位應被遮蔽: %s", evidence)
	}
}

// TestSessionScrubDoesNotEatLongerTokens 確認抹除已知憑證時不會誤傷更長的字串。
//
// 注意：「RS1065」本身包含「RS106」這段字串，所以不能用 strings.Contains 斷言
// 「RS1065 不存在」——那會把正確的輸出判成失敗。要比對的是「獨立的 RS106 被抹掉、
// 而 RS1065 完整保留」。
func TestSessionScrubDoesNotEatLongerTokens(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()
	session.Mask(`<input type="password" name="_txtPassword" value="RS106">`)
	got := session.Scrub("編號 RS1065 與 RS106 都要看")
	want := "編號 RS1065 與 *** 都要看"
	if got != want {
		t.Fatalf("抹除範圍不對:\n得到=%q\n預期=%q", got, want)
	}
}

// TestSessionDoesNotScrubShortValues 確認過短的值不會被拿去散播抹除。
//
// 太短的值（例如 "2024"）在自然文字裡出現太頻繁，
// 拿來當「已知憑證值」散播會把無關內容洗掉。
func TestSessionDoesNotScrubShortValues(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()
	session.Mask(`<input type="password" name="_txtPassword" value="2024">`)
	if got := session.Scrub("版本 2024 仍在使用"); got != "版本 2024 仍在使用" {
		t.Fatalf("過短的值不該被散播抹除: %s", got)
	}
}

// TestSessionScrubsAdjacentCredentialPair 擋住「帳密同值、相鄰出現」的漏抹。
//
// 生產資料實測（修正後 MySQL 仍命中 68 筆）：證據把帳號與密碼寫成一組，
//
//	POST ***/RS106 + 通过校验的验证码 1766
//	本资产（ip-0fbe2c5b）上 ***/RS106 组合实测被服务端拒绝
//
// 舊的實作把「邊界字元」一起納入正規表示式比對。邊界被吃掉之後，
// 第二次出現就沒有左邊界可用 → 只抹掉前一段，密碼就這樣留在外部資料庫裡。
//
// 修法：邊界改成零寬度判斷（自己掃描匹配位置），不消耗任何字元。
func TestSessionScrubsAdjacentCredentialPair(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()
	session.Mask(`<input type="password" name="_txtPassword" value="RS106">`)

	for _, text := range []string{
		"验证性登录测试：POST ***/RS106 + 通过校验的验证码 1766",
		"本资产（ip-0fbe2c5b）上 ***/RS106 组合实测被服务端拒绝",
		"登录页硬编码默认凭据 RS106/RS106（本资产凭据已失效，CWE-798）",
	} {
		got := session.Scrub(text)
		if strings.Contains(got, "RS106") {
			t.Errorf("相鄰出現的憑證值沒被抹乾淨: %s", got)
		}
	}
}

// TestSessionScrubsCaseVariantsOfCredential 擋住「同一組憑證的大小寫變體」。
//
// 生產證據實測：口令變體清單裡同一組預設帳密以不同大小寫出現，
//
//	口令变体 rs106、RS106!、106RS、RS106@2026、RS106␣、USER106
//
// 只擋完全相同的大小寫等於把一半的變體留在外部資料庫裡。
// 大小寫不同的同一組憑證仍然是同一組憑證，所以抹除必須大小寫不敏感。
func TestSessionScrubsCaseVariantsOfCredential(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()
	session.Mask(`<input type="password" name="_txtPassword" value="RS106">`)

	got := session.Scrub("口令变体：WRONG1/WRONG2/rs106/RS106!/RS106@2026")
	for _, variant := range []string{"rs106", "RS106"} {
		if strings.Contains(got, variant) {
			t.Errorf("大小寫變體 %q 沒被抹掉: %s", variant, got)
		}
	}
	// 相鄰的變體也要各自被抹掉（不是只抹第一個）：
	// "rs106"、"RS106!"、"RS106@2026" 三個都要變成 ***。
	if strings.Count(got, RedactedSecret) != 3 {
		t.Errorf("相鄰的三個變體都要被抹掉: %s", got)
	}
}

// TestMaskCatchesUsernameFieldCredentials 擋住「只遮密碼欄位、帳號欄位帶出去」。
//
// 生產證據實測（MySQL 命中 18 筆）：那組預設測試帳號 RS106 既是密碼也是帳號，
// 而且平台報告指出「該帳號本身可能仍有效」（實測帳號仍被服務端接受處理）。
// 只遮密碼欄位，帳號欄位會把同一組憑證的另一半帶出去：
//
//	<input name="_txtUsername" value="RS106" ...>
//	<input name="_txtPassword" value="RS106" ...>
//	&_txtUsername=RS106&_txtPassword=wrongpw
//	（漏洞 a83c38e5，_txtUsername=RS106 / _txtPassword=***"凭据已泄露"）
//
// 值要通過 looksLikeCredential 才會被遮：admin／guest 不是秘密。
func TestMaskCatchesUsernameFieldCredentials(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		`<input name="_txtUsername" value="RS106" ...>`,
		`<input type="text" name="_txtUsername" value="RS106">`,
		`&_txtUsername=RS106&_txtPassword=wrongpw&hidFlag=`,
		`（漏洞 a83c38e5，_txtUsername=RS106 / _txtPassword=***"凭据已泄露"）`,
		`仅把 ` + "`_txtUsername`" + ` 改回 ` + "`RS106`" + ` 重复步骤`,
	} {
		got := policy.Mask(text)
		if strings.Contains(got, "RS106") {
			t.Errorf("帳號欄位的憑證值未被遮蔽: %s", got)
		}
	}
}

// TestMaskKeepsOrdinaryUsernameValues 確認一般帳號不會被無差別洗掉。
//
// 帳號欄位規則的守衛是「值看起來像憑證」：admin、guest、user 這類值不該被遮，
// 否則證據會變得難讀，而且會誤傷 IDOR 證據裡的查詢參數。
//
// 注意：同一個字串裡的「密碼」欄位本來就該被遮 —— 這條測試盯的是帳號值。
func TestMaskKeepsOrdinaryUsernameValues(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		`<input name="_txtUsername" value="admin">`,
		`username=user`,
	} {
		if got := policy.Mask(text); got != text {
			t.Errorf("一般帳號值被誤遮: 原文=%q 遮蔽後=%q", text, got)
		}
	}
	// 表單參數寫法：帳號保留、密碼照舊被遮。
	got := policy.Mask("&_txtUsername=guest&_txtPassword=wrongpw")
	if !strings.Contains(got, "_txtUsername=guest") {
		t.Errorf("一般帳號值被誤遮: %s", got)
	}
	if !strings.Contains(got, "_txtPassword=***") {
		t.Errorf("密碼欄位仍應被遮蔽: %s", got)
	}
}

// TestMaskDoesNotMaskIDORQueryParameters 確認 IDOR 證據的查詢參數不被洗掉。
//
// ?author=1 這類參數正是漏洞成立的要點；遮掉等於毀掉證據。
// 這條測試盯住「帳號家族關鍵字不進寬鬆規則」這個決定。
func TestMaskDoesNotMaskIDORQueryParameters(t *testing.T) {
	policy := DefaultPolicy()
	for _, text := range []string{
		`GET /api/user?account=12345 → HTTP 200`,
		`GET /api/order?account=abc123 → HTTP 200`,
		`?author=1`,
	} {
		if got := policy.Mask(text); got != text {
			t.Errorf("IDOR 查詢參數被誤遮: 原文=%q 遮蔽後=%q", text, got)
		}
	}
}

// TestMaskKeepsVersionWithLongFourthSegment 確認「第 4 段超過 3 位」的版本號不被當成位址。
//
// 生產資料實測：IDExpert SSO Portal 的版本是 "2.8.2.20241122"。
// 舊的外洩驗證腳本用「四段數字」的寬鬆比對把它截成 "2.8.2.202"，
// 當成真實位址而報出假的 LEAK-IP。
//
// 遮蔽層的判準是「數字點號序列取前四段，每段 1–3 位且 ≤255」，
// 第 4 段有 8 位的 "20241122" 直接否決 → 這個版本不該被動到。
// 這條測試把遮蔽層與驗證腳本的判準綁在一起，避免兩邊各說各話。
func TestMaskKeepsVersionWithLongFourthSegment(t *testing.T) {
	policy := DefaultPolicy()
	text := "IDExpert SSO Portal v2.8.2.20241122，IDP 组件，会话 Cookie jsessionid"
	if got := policy.Mask(text); got != text {
		t.Fatalf("版本號不該被當成位址遮掉:\n得到=%q\n預期=%q", got, text)
	}
}

// TestMaskWashesFourSegmentVersionPrefix 記錄一個刻意的取捨。
//
// 四段前綴的產品版本（"WebLogic Server 10.3.6.0.0"）會被洗成 "internal-redacted.0"，
// 因為它與 tcpdump 的 ip.port 記法（"223.200.50.93.25"）結構完全相同，
// 無法用形狀分辨哪一個是位址。遮蔽必須偏保守（寧可多洗），所以版本被洗掉是已知成本。
//
// 這條測試的存在目的是：不要有人只看到「版本被洗掉」就單方面把規則改寬，
// 那會讓真實位址重新長出來。版本完整值仍保留在平台原始資料裡。
func TestMaskWashesFourSegmentVersionPrefix(t *testing.T) {
	policy := DefaultPolicy()
	got := policy.Mask("WebLogic Server 10.3.6.0.0")
	if strings.Contains(got, "10.3.6.0") {
		t.Fatalf("四段版本前綴應被洗掉: %s", got)
	}
	if !strings.Contains(got, InternalRedacted) {
		t.Fatalf("應歸為 %s: %s", InternalRedacted, got)
	}
}

// productionCredentialMatrix 是生產資料裡真實出現過的一段證據（原樣保留）。
//
// 這段矩陣把同一組用戶端靜態金鑰以七種形式並列：原值、去 padding、全小寫、
// 全大寫、首字元改、末兩字元改、追加字元、前置空白。
// 生產資料庫裡就是這一段讓遮蔽層一次認出九個「看起來像憑據」的值。
const productionCredentialMatrix = `data 值                              响应
w4xJPDvfxV1k00uKcIhGog==  (精确)     HTTP 200, Content-Length: 0, 空 body
oSoMIBnEp0vrG7JyF/E2yw==            不合法的TOKEN
w4xJpdvfxv1k00ukcihgoog==  (小写)   不合法的TOKEN
W4XJPDVFXV1K00UKCIHGOG==  (大写)   不合法的TOKEN
w4xJPDvfxV1k00uKcIhGog   (去=)      不合法的TOKEN
X4xJPDvfxV1k00uKcIhGog==  (首字符改) 不合法的TOKEN
w4xJPDvfxV1k00uKcIhGogXY=  (末2改)  不合法的TOKEN
w4xJPDvfxV1k00uKcIhGog==A (追加)    不合法的TOKEN
 w4xJPDvfxV1k00uKcIhGog== (前空格)  不合法的TOKEN`

// TestSessionScrubIsDeterministic 擋住「遮蔽結果會漂移」這個最難察覺的缺陷。
//
// 缺陷：抹除已知憑據時原本直接遍歷 Go 的 map，而 map 的迭代順序是隨機的。
// 抹除是「有順序」的 —— 先抹掉短的形式，長的形式就只剩尾巴。
// 同一組金鑰在證據裡有九種形式（帶／不帶 base64 padding、大小寫變體、
// 多一個字元），所以九種抹除順序會給出九種不同的結果。
//
// 實際後果（不是理論問題）：
//   - 同一筆記錄在兩次匯入之間 checksum 改變 → 接收端帳本永遠收斂不了，
//     每次匯入都會重送同一筆資料。
//   - 外部庫裡同一筆資料會同時存在多種遮蔽後的內容。
//   - 「同一個位址永遠對應同一個代號」這個承諾也失去可預測性。
//
// 實測：修正前對這一筆跑 500 次會得到 8 種不同的 checksum；
// 修正後（抹除依長度優先、同長度依字典序排序）只會得到 1 種。
func TestSessionScrubIsDeterministic(t *testing.T) {
	policy := DefaultPolicy()

	baseline := ""
	for i := 0; i < 200; i++ {
		session := policy.NewSession()
		// 跟正式外送路徑一樣：先各欄位獨立遮蔽（認出憑據），再統一抹除。
		masked := session.Mask(productionCredentialMatrix)
		got := session.Scrub(masked)
		if i == 0 {
			baseline = got
			continue
		}
		if got != baseline {
			t.Fatalf("第 %d 次遮蔽結果與第 1 次不同 —— 遮蔽必須是確定性的:\n第一次=%q\n這一次=%q", i, baseline, got)
		}
	}
}

// TestSessionScrubRemovesLongestCredentialForm 確認「最長形式優先」真的生效。
//
// 順序排錯時會出現的典型殘留：只抹掉 "w4xJPDvfxV1k00uKcIhGog"，
// 讓 base64 的 padding "==" 留在原地變成 "***==" ——
// 憑據的尾巴還在外部庫裡，而且看起來像一段無害的 base64 padding。
func TestSessionScrubRemovesLongestCredentialForm(t *testing.T) {
	policy := DefaultPolicy()
	session := policy.NewSession()
	got := session.Scrub(session.Mask(productionCredentialMatrix))

	for _, form := range []string{
		"w4xJPDvfxV1k00uKcIhGog",
		"w4xJpdvfxv1k00ukcihgoog",
		"W4XJPDVFXV1K00UKCIHGOG",
		"X4xJPDvfxV1k00uKcIhGog",
	} {
		if strings.Contains(got, form) {
			t.Fatalf("金鑰變體 %q 仍在輸出中: %s", form, got)
		}
	}
	if strings.Contains(got, "***==") {
		t.Fatalf("base64 padding 尾巴沒被一起抹掉（代表抹除順序錯了）: %s", got)
	}
	if !strings.Contains(got, RedactedSecret) {
		t.Fatalf("應該要有遮蔽後的 %s: %s", RedactedSecret, got)
	}
}
