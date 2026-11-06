package vulnclass

// Category 受控的漏洞分類。平台上的每一筆漏洞都必須落在其中一類，
// 讓「漏洞類型」從自由文字變成可以篩選、統計、匯出的欄位。
type Category struct {
	// Code 機器可讀代碼（英文 kebab-case），API、匯出與 MySQL 都用這個值。
	Code string
	// LabelZh / LabelEn 顯示用標籤。
	LabelZh string
	LabelEn string
	// CWEs 對應的 CWE 編號（可為空）。用於 CWE 反查與報告對照。
	CWEs []string
	// Description 分類的判定範圍說明（寫給維護者看的）。
	Description string
}

// 受控分類代碼。
const (
	CodeSQLInjection      = "sql-injection"
	CodeNoSQLInjection    = "nosql-injection"
	CodeCommandInjection  = "command-injection"
	CodeCodeInjection     = "code-injection"
	CodeXSS               = "xss"
	CodeCSRF              = "csrf"
	CodeXXE               = "xxe"
	CodeSSRF              = "ssrf"
	CodePathTraversal     = "path-traversal"
	CodeFileUpload        = "file-upload"
	CodeIDOR              = "idor"
	CodeAccessControl     = "broken-access-control"
	CodeAuthentication    = "missing-authentication"
	CodeWeakCredential    = "weak-credentials"
	CodeHardcodedCred     = "hardcoded-credentials"
	CodeSession           = "session-management"
	CodeUserEnumeration   = "user-enumeration"
	CodeInfoDisclosure    = "info-disclosure"
	CodeCrypto            = "crypto-weakness"
	CodeCleartext         = "cleartext-transmission"
	CodeCORS              = "cors-misconfiguration"
	CodeMisconfiguration  = "security-misconfiguration"
	CodeExposedService    = "exposed-service"
	CodeOutdatedComponent = "outdated-component"
	CodeBusinessLogic     = "business-logic"
	CodeResourceExhaust   = "resource-exhaustion"
	CodeEmailSecurity     = "email-security"
	CodeOpenRedirect      = "open-redirect"
	CodeHostHeader        = "host-header-injection"
	CodeSourceDisclosure  = "source-disclosure"
	CodeCaptchaAbuse      = "captcha-abuse"
	CodeSubdomainTakeover = "subdomain-takeover"
	CodeOpenProxy         = "open-proxy"
	CodeExcessiveData     = "excessive-data-exposure"
	CodeOther             = "other"
	CodeUnclassified      = "unclassified"
)

// Categories 受控漏洞分類詞彙表。
//
// 分類碼排序刻意從「可被直接利用」往「需要條件」排列：
// 分類器比對多個規則時取第一個命中的類別，順序即優先序。
var Categories = []Category{
	{Code: CodeSQLInjection, LabelZh: "SQL 注入", LabelEn: "SQL Injection", CWEs: []string{"CWE-89"},
		Description: "SQL 語句被未驗證的輸入拼接或改寫（MySQL/PostgreSQL/MSSQL/Oracle 等）。"},
	{Code: CodeNoSQLInjection, LabelZh: "NoSQL 注入", LabelEn: "NoSQL Injection", CWEs: []string{"CWE-943"},
		Description: "MongoDB 等 NoSQL 查詢語句被注入，例如以物件或運算子改變查詢語意。"},
	{Code: CodeCommandInjection, LabelZh: "命令注入與遠端程式碼執行", LabelEn: "Command Injection & RCE", CWEs: []string{"CWE-78", "CWE-77", "CWE-94"},
		Description: "系統指令或反序列化路徑可被遠端程式碼執行。"},
	{Code: CodeCodeInjection, LabelZh: "代碼與模板注入", LabelEn: "Code & Template Injection", CWEs: []string{"CWE-94", "CWE-95", "CWE-1336"},
		Description: "PHP/程式碼片段或樣板引擎被注入並執行。"},
	{Code: CodeXSS, LabelZh: "跨站腳本", LabelEn: "Cross-Site Scripting", CWEs: []string{"CWE-79"},
		Description: "反射型、儲存型或 DOM 型 XSS。"},
	{Code: CodeCSRF, LabelZh: "跨站請求偽造", LabelEn: "Cross-Site Request Forgery", CWEs: []string{"CWE-352"},
		Description: "缺少 CSRF 權杖或 SameSite 防護，導致以受害者身分執行操作。"},
	{Code: CodeXXE, LabelZh: "XML 外部實體注入", LabelEn: "XML External Entity Injection", CWEs: []string{"CWE-611"},
		Description: "XML 解析器允許外部實體或 DTD 處理。"},
	{Code: CodeSSRF, LabelZh: "服務端請求偽造", LabelEn: "Server-Side Request Forgery", CWEs: []string{"CWE-918"},
		Description: "服務端可被誘導請求內網或第三方資源。"},
	{Code: CodePathTraversal, LabelZh: "路徑穿越與任意檔案存取", LabelEn: "Path Traversal & Arbitrary File Access", CWEs: []string{"CWE-22", "CWE-23", "CWE-36", "CWE-73"},
		Description: "路徑參數可穿越到預期目錄之外，或可讀寫任意檔案。"},
	{Code: CodeFileUpload, LabelZh: "任意檔案上傳", LabelEn: "Unrestricted File Upload", CWEs: []string{"CWE-434"},
		Description: "上傳副檔名或內容未受限，可寫入可執行檔或覆寫既有檔案。"},
	{Code: CodeIDOR, LabelZh: "不安全直接物件引用", LabelEn: "Insecure Direct Object Reference", CWEs: []string{"CWE-639", "CWE-639"},
		Description: "以可預期的識別碼存取他人資料，未檢查物件歸屬。"},
	{Code: CodeAccessControl, LabelZh: "存取控制缺陷與越權", LabelEn: "Broken Access Control", CWEs: []string{"CWE-284", "CWE-862", "CWE-863", "CWE-269"},
		Description: "未授權存取、垂直或水平越權、功能未做授權檢查。"},
	{Code: CodeAuthentication, LabelZh: "缺少認證與認證繞過", LabelEn: "Missing or Broken Authentication", CWEs: []string{"CWE-287", "CWE-306", "CWE-307", "CWE-305"},
		Description: "關鍵功能缺少認證、認證可繞過，或缺少登入爆破防護。"},
	{Code: CodeWeakCredential, LabelZh: "弱密碼與預設帳號", LabelEn: "Weak or Default Credentials", CWEs: []string{"CWE-521", "CWE-798"},
		Description: "弱密碼政策、預設密碼或可猜測帳號。"},
	{Code: CodeHardcodedCred, LabelZh: "硬編碼憑證", LabelEn: "Hardcoded Credentials", CWEs: []string{"CWE-798"},
		Description: "程式碼、設定檔或前端包內含明文密鑰、Token、API Key。"},
	{Code: CodeSession, LabelZh: "工作階段與 Cookie 管理缺陷", LabelEn: "Session & Cookie Management", CWEs: []string{"CWE-384", "CWE-614", "CWE-757", "CWE-1004"},
		Description: "Cookie 缺少 Secure/HttpOnly/SameSite、工作階段固定或未及時失效。"},
	{Code: CodeUserEnumeration, LabelZh: "用戶枚舉", LabelEn: "User Enumeration", CWEs: []string{"CWE-204", "CWE-203"},
		Description: "可藉由回應差異辨識帳號是否存在。"},
	{Code: CodeInfoDisclosure, LabelZh: "資訊洩漏", LabelEn: "Information Disclosure", CWEs: []string{"CWE-200", "CWE-209", "CWE-215", "CWE-538"},
		Description: "錯誤訊息、目錄列表、敏感欄位或內部實作細節外洩。"},
	{Code: CodeCrypto, LabelZh: "加密與雜湊弱點", LabelEn: "Cryptographic Weakness", CWEs: []string{"CWE-327", "CWE-326", "CWE-328", "CWE-916", "CWE-310"},
		Description: "弱演算法、ECB、固定 IV、不安全隨機數或雜湊用途錯誤。"},
	{Code: CodeCleartext, LabelZh: "明文傳輸", LabelEn: "Cleartext Transmission", CWEs: []string{"CWE-319", "CWE-311"},
		Description: "敏感資料以未加密的 HTTP 或弱 TLS 傳輸。"},
	{Code: CodeCORS, LabelZh: "CORS 跨域策略設定缺陷", LabelEn: "CORS Misconfiguration", CWEs: []string{"CWE-942"},
		Description: "Access-Control-Allow-Origin 反射任意來源或搭配憑證放行。"},
	{Code: CodeMisconfiguration, LabelZh: "安全設定缺陷", LabelEn: "Security Misconfiguration", CWEs: []string{"CWE-16", "CWE-693", "CWE-1188"},
		Description: "安全標頭缺失、除錯模式、寬鬆權限或其他組態問題。"},
	{Code: CodeExposedService, LabelZh: "服務與管理介面暴露", LabelEn: "Exposed Service or Admin Interface", CWEs: []string{"CWE-284", "CWE-200"},
		Description: "後台、管理端點、actuator、swagger 或不該對外開放的服務。"},
	{Code: CodeOutdatedComponent, LabelZh: "過時組件與已知弱點", LabelEn: "Outdated Component & Known Vulnerabilities", CWEs: []string{"CWE-1035", "CWE-1104", "CWE-937"},
		Description: "使用已知存在弱點的套件、框架或版本（含 CVE 編號）。"},
	{Code: CodeBusinessLogic, LabelZh: "業務邏輯缺陷", LabelEn: "Business Logic Flaw", CWEs: []string{"CWE-840", "CWE-841"},
		Description: "流程、金額、優惠或狀態機可被濫用。"},
	{Code: CodeResourceExhaust, LabelZh: "資源耗盡與拒絕服務", LabelEn: "Resource Exhaustion & DoS", CWEs: []string{"CWE-400", "CWE-770", "CWE-1333"},
		Description: "可被無上限呼叫、遞迴或大 payload 耗盡資源。"},
	{Code: CodeEmailSecurity, LabelZh: "郵件安全設定缺陷", LabelEn: "Email Security Misconfiguration", CWEs: []string{"CWE-16"},
		Description: "SPF/DKIM/DMARC/MTA-STS 設定錯誤或缺少郵件驗證。"},
	{Code: CodeOpenRedirect, LabelZh: "開放重定向", LabelEn: "Open Redirect", CWEs: []string{"CWE-601"},
		Description: "未驗證的跳轉參數可導向任意外部網址。"},
	{Code: CodeHostHeader, LabelZh: "Host 標頭注入", LabelEn: "Host Header Injection", CWEs: []string{"CWE-644"},
		Description: "可污染 Host/X-Forwarded-Host 等標頭影響後端行為。"},
	{Code: CodeSourceDisclosure, LabelZh: "原始碼與備份檔外洩", LabelEn: "Source Code & Backup Disclosure", CWEs: []string{"CWE-530", "CWE-538"},
		Description: ".git、備份檔、設定檔等可直接下載原始碼。"},
	{Code: CodeCaptchaAbuse, LabelZh: "驗證碼與簡訊轟炸", LabelEn: "CAPTCHA & SMS Abuse", CWEs: []string{"CWE-799", "CWE-307"},
		Description: "驗證碼可重送、缺少人機驗證或簡訊可被轟炸。"},
	{Code: CodeSubdomainTakeover, LabelZh: "子域名接管", LabelEn: "Subdomain Takeover", CWEs: []string{"CWE-1034"},
		Description: "已釋放的第三方資源仍被 DNS 指向，可被接管。"},
	{Code: CodeOpenProxy, LabelZh: "開放代理", LabelEn: "Open Proxy", CWEs: []string{"CWE-441"},
		Description: "可被當成跳板或轉發內部請求。"},
	{Code: CodeExcessiveData, LabelZh: "API 過度資料暴露", LabelEn: "Excessive Data Exposure", CWEs: []string{"CWE-213"},
		Description: "API 回傳超出需求欄位，包含不該給該使用者的資料。"},
	{Code: CodeOther, LabelZh: "其他", LabelEn: "Other", Description: "可辨識但尚未納入受控分類的漏洞類型。"},
	{Code: CodeUnclassified, LabelZh: "待人工歸類", LabelEn: "Unclassified", Description: "原始型別無法判定，需要人工歸類。"},
}

var categoryIndex = func() map[string]Category {
	index := make(map[string]Category, len(Categories))
	for _, category := range Categories {
		index[category.Code] = category
	}
	return index
}()

// ByCode 依代碼取得分類；找不到回傳 false。
func ByCode(code string) (Category, bool) {
	category, ok := categoryIndex[code]
	return category, ok
}

// LabelZh 回傳分類的中文標籤；未知代碼回傳代碼本身。
func LabelZh(code string) string {
	if category, ok := categoryIndex[code]; ok {
		return category.LabelZh
	}
	return code
}

// LabelEn 回傳分類的英文標籤；未知代碼回傳代碼本身。
func LabelEn(code string) string {
	if category, ok := categoryIndex[code]; ok {
		return category.LabelEn
	}
	return code
}

// Codes 回傳所有受控分類代碼（順序與詞彙表一致）。
func Codes() []string {
	codes := make([]string, 0, len(Categories))
	for _, category := range Categories {
		codes = append(codes, category.Code)
	}
	return codes
}
