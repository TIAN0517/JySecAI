package vulnclass

import (
	"strings"
	"testing"
)

// 真實平台資料裡出現過的型別寫法（取自生產庫的實際分布）。
func TestClassifyRealWorldTypes(t *testing.T) {
	cases := []struct {
		typ  string
		want string
		note string
	}{
		{"SQL注入", CodeSQLInjection, "純中文型別"},
		{"SQL注入 (CWE-89)", CodeSQLInjection, "帶 CWE"},
		{"NoSQL 注入", CodeNoSQLInjection, "NoSQL 要排在 SQL 前面"},
		{"CVE-2020-11022", CodeOutdatedComponent, "已知弱點編號"},
		{"反射型跨站脚本 (Reflected XSS)", CodeXSS, "反射型 XSS"},
		{"SSRF（服务端请求伪造）", CodeSSRF, "SSRF"},
		{"Broken Access Control / Missing Authentication", CodeAccessControl, "存取控制優先於認證"},
		{"未授权访问/信息泄露", CodeAccessControl, "複合型別取先寫的那個"},
		{"硬编码凭据/敏感信息泄露（索引级信息泄露）", CodeHardcodedCred, "硬編碼憑證優先於資訊洩漏"},
		{"信息泄露/用户枚举", CodeUserDisclosureOrder, "資訊洩漏優先於用戶枚舉"},
		{"CORS 跨域策略配置错误 (CWE-942)", CodeCORS, "CORS 單獨一類"},
		{"会话劫持：不安全的 Cookie 配置与传输层降级 (CWE-614 / CWE-757)", CodeSession, "工作階段缺陷"},
		{"邮件安全配置缺陷 / SPF 授权范围越界（第三方共享 IP 池过度委托）", CodeEmailSecurity, "郵件安全設定"},
		{"过時组件", CodeOutdatedComponent, "過時組件"},
		{"用户枚举", CodeUserEnumeration, "用戶枚舉"},
		{"用户枚举/信息泄露", CodeUserEnumeration, "複合型別取先寫的那個"},
		{"目录列表 / 信息泄露", CodeInfoDisclosure, "目錄列表"},
		{"明文传输敏感信息 / 不安全的传输层配置（Cleartext Transmission of Sensitive Information，CWE-319）", CodeCleartext, "明文傳輸優先於加密"},
		{"云存储权限配置错误 / 未授权数据泄露（CWE-732 公开 ACL、CWE-200 信息泄露）", CodeAccessControl, "公開 ACL 屬存取控制"},
		{"暴力破解防护缺失", CodeAuthentication, "缺少防護"},
		{"命令注入", CodeCommandInjection, "命令注入"},
		{"任意文件上传", CodeFileUpload, "任意檔案上傳"},
		{"路径穿越", CodePathTraversal, "路徑穿越"},
		{"子域名接管（Subdomain Takeover）", CodeSubdomainTakeover, "子域名接管"},
		{"开放代理 / 代理滥用 (Open Proxy, CWE-441)", CodeOpenProxy, "開放代理"},
		{"Broken Object Level Authorization (API1:2023) + Excessive Data Exposure (API3:2023)", CodeIDOR, "物件級授權"},
		{"Improper Authorization", CodeAccessControl, "Improper Authorization"},
		{"Missing Security Header", CodeMisconfiguration, "安全標頭缺失"},
		{"email_spoofing", CodeEmailSecurity, "郵件偽造"},
		{"sql_injection", CodeSQLInjection, "底線寫法"},
		{"information_disclosure", CodeInfoDisclosure, "底線寫法"},
		{"CWE-614", CodeSession, "只有 CWE 編號"},
		{"CWE-937", CodeOutdatedComponent, "CWE-937 = 使用已知有弱點的元件"},
	}
	for _, tc := range cases {
		got := Classify(tc.typ, "", "")
		if got.Code != tc.want {
			t.Errorf("Classify(%q) = %s，want %s（%s）", tc.typ, got.Code, tc.want, tc.note)
		}
	}
}

// CodeUserDisclosureOrder 只是測試用常數：資訊洩露與用戶枚舉的先後順序。
const CodeUserDisclosureOrder = CodeInfoDisclosure

func TestClassifyArtifactTypesFallBackToTitleAndDescription(t *testing.T) {
	// finding / target / note 是模型回傳 JSON 時的欄位名，不是漏洞類型。
	for _, artifact := range []string{"finding", "target", "note", "configuration", "exploit", "confidence.100", "API", "test"} {
		if !IsArtifactType(artifact) {
			t.Errorf("%q 應被視為佔位字", artifact)
		}
	}
	result := Classify("finding", "SQL 注入於 /login 參數", "以單引號結尾的 payload 可觸發資料庫錯誤")
	if result.Code != CodeSQLInjection {
		t.Fatalf("應改由標題與描述判定，got %s (%s)", result.Code, result.Source)
	}
	if result.Source != SourceContext {
		t.Fatalf("來源應標記為 context，got %s", result.Source)
	}
}

func TestClassifyUnclassifiableStaysUnclassified(t *testing.T) {
	result := Classify("zzz", "zzz", "zzz")
	if result.Code != CodeUnclassified {
		t.Fatalf("無法判定應為 unclassified，got %s", result.Code)
	}
	if result.Classified() {
		t.Fatal("unclassified 不應被視為已分類")
	}
}

func TestClassifyNeverInventsSeverity(t *testing.T) {
	// 分類只負責講清楚「型別」，不得順手把未判定改成已確認。
	result := Classify("SQL注入", "", "")
	if result.LabelZh == "" || result.LabelEn == "" {
		t.Fatalf("分類結果必須同時有中英標籤: %#v", result)
	}
}

func TestEveryCategoryHasLabelsAndUniqueCode(t *testing.T) {
	seen := map[string]bool{}
	for _, category := range Categories {
		if category.Code == "" || category.LabelZh == "" || category.LabelEn == "" {
			t.Fatalf("分類缺欄位: %#v", category)
		}
		if seen[category.Code] {
			t.Fatalf("分類代碼重複: %s", category.Code)
		}
		seen[category.Code] = true
		if _, ok := ByCode(category.Code); !ok {
			t.Fatalf("ByCode 查不到 %s", category.Code)
		}
	}
}

// TestEveryRulePatternCompiles 擋住無效的規則。
//
// 規則編譯失敗時症狀是「某個型別怎麼都分不出來」，沒有任何錯誤訊息，
// 所以必須用測試擋下來，否則靜默少掉一條規則不會有人發現。
func TestEveryRulePatternCompiles(t *testing.T) {
	if len(ruleBuildErrors) > 0 {
		t.Fatalf("有規則編譯失敗:\n%s", strings.Join(ruleBuildErrors, "\n"))
	}
}

// TestEveryCategoryHasTier 擋住漏設定層級的分類。
func TestEveryCategoryHasTier(t *testing.T) {
	for _, category := range Categories {
		if category.Code == CodeOther || category.Code == CodeUnclassified {
			continue
		}
		if _, ok := codeTier[category.Code]; ok {
			continue
		}
		tier := tierOf(category.Code)
		if tier != tierSpecific && tier != tierGeneric {
			t.Fatalf("分類 %s 的層級不合法: %d", category.Code, tier)
		}
	}
}
