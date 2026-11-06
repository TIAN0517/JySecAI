package vulnclass

import "testing"

// TestClassifyProductionUnclassifiedStrings 回歸測試。
//
// 這些字串全部來自生產資料庫實際出現過、而且在第一版分類器下被判為
// 「待人工歸類」的型別。每一筆都對應一個真實的分類缺口，
// 修好規則後如果又被改回去，這支測試會擋下來。
func TestClassifyProductionUnclassifiedStrings(t *testing.T) {
	cases := []struct {
		typ  string
		want string
		note string
	}{
		{"路径遍历", CodePathTraversal, "遍歷不是穿越"},
		{"点击劫持 Clickjacking（CWE-1021）", CodeMisconfiguration, "點擊劫持屬安全標頭缺失"},
		{"点击劫持 / UI Redressing (Clickjacking)", CodeMisconfiguration, "點擊劫持"},
		{"未授权数据泄露", CodeAccessControl, "未授權即存取控制"},
		{"信息暴露 / 配置不当", CodeInfoDisclosure, "曝露也是洩漏"},
		{"信息暴露/敏感数据泄露", CodeInfoDisclosure, "曝露也是洩漏"},
		{"敏感数据泄露/账号枚举", CodeInfoDisclosure, "敏感資料洩漏"},
		{"敏感个人资料泄露 / 公开存储桶中的 PII 暴露", CodeInfoDisclosure, "個人資料洩漏"},
		{"文件泄露", CodeSourceDisclosure, "檔案外洩"},
		{"环境变量泄露", CodeInfoDisclosure, "環境變數外洩"},
		{"证书过期/合规问题", CodeMisconfiguration, "憑證到期"},
		{"证书管理（Certificate Management）", CodeMisconfiguration, "憑證管理"},
		{"安全配置缺失", CodeMisconfiguration, "安全設定缺失"},
		{"安全配置缺失 / 缺少安全响应头", CodeMisconfiguration, "安全設定缺失"},
		{"安全响应头缺失 / CSP 缺失", CodeMisconfiguration, "安全回應標頭缺失"},
		{"传输层安全缺陷", CodeCrypto, "傳輸層安全屬加密弱點"},
		{"不安全的重定向 / 协议降级", CodeOpenRedirect, "不安全的重定向"},
		{"缺失鉴权 / Webhook 签名校验缺失（消息伪造注入）", CodeAuthentication, "缺少鑑權"},
		{"默认应用 + HTTP 明文 + TRACE 启用", CodeCleartext, "明文傳輸"},
		{"输入校验缺失 / 业务参数污染", CodeMisconfiguration, "輸入驗證缺失"},
		{"配置管理缺陷 / 部署一致性缺失（版本漂移导致安全控制不一致）", CodeMisconfiguration, "配置管理缺陷"},
		{"弱默认凭据 / 凭据生成算法泄露", CodeWeakCredential, "預設憑證"},
		{"不安全的默认配置 / 预发布环境暴露", CodeMisconfiguration, "預設設定"},
		{"网站入侵/恶意脚本注入", CodeCodeInjection, "惡意腳本注入"},
		{"服务端模板渲染缺陷（Template Placeholder Leakage）", CodeCodeInjection, "模板渲染缺陷"},
		{"悬空CNAME/子域接管", CodeSubdomainTakeover, "子域接管沒有「名」字"},
		{"暴露的诱捕/仿真服务 (Deception/Honeypot Endpoint) + 公网开放 Telnet 入口", CodeExposedService, "公網開放"},
		{"CWE-707", CodeCodeInjection, "Improper Neutralization"},
		{"CWE-829", CodeOutdatedComponent, "Untrusted Control Sphere"},
		{"CWE-830", CodeOutdatedComponent, "Untrusted Control Sphere"},
		{"CWE-1321", CodeCodeInjection, "Prototype Pollution"},
		{"CWE-353", CodeOutdatedComponent, "Missing Support for Integrity Check"},
		{"CWE-359", CodeInfoDisclosure, "Exposure of Private Personal Information"},
		{"CWE-1021", CodeMisconfiguration, "Clickjacking"},
	}
	for _, tc := range cases {
		got := Classify(tc.typ, "", "")
		if got.Code != tc.want {
			t.Errorf("Classify(%q) = %s，want %s（%s）", tc.typ, got.Code, tc.want, tc.note)
		}
	}
}

// TestClassifyKeepsNonTypeValuesUnclassified 確保不是漏洞型別的值不會被硬塞一個分類。
//
// 例如「重複記錄」「邊界條件記錄」是掃描器的產出標記，不是漏洞類型；
// 把它們歸進任何一個受控分類都是錯的，留待人工歸類才是正確答案。
func TestClassifyKeepsNonTypeValuesUnclassified(t *testing.T) {
	for _, value := range []string{
		"重复记录（Duplicate）",
		"边界条件记录",
		"合规风险",
		"暴露面管理",
		"安全暴露面审计/信息级",
		"欺骗环境识别 / Honeypot Detection（资产归属与测试有效性）",
	} {
		got := Classify(value, "", "")
		if got.Code != CodeUnclassified {
			t.Errorf("Classify(%q) = %s，應保持待人工歸類", value, got.Code)
		}
	}
}
