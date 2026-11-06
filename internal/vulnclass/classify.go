package vulnclass

import (
	"fmt"
	"regexp"
	"strings"
)

// 分類來源。
const (
	// SourceRule 由型別（或標題/描述）文字命中關鍵字規則。
	SourceRule = "rule"
	// SourceCWE 文字裡只有 CWE 編號，靠 CWE 對照表判定。
	SourceCWE = "cwe"
	// SourceContext 型別是無意義佔位字，改由標題與描述判定。
	SourceContext = "context"
	// SourceDefault 完全無法判定。
	SourceDefault = "default"
)

// Classification 一筆漏洞的分類結果。
type Classification struct {
	Code     string
	LabelZh  string
	LabelEn  string
	Source   string
	Evidence string
}

// Classified 是否已落在受控分類內。
func (c Classification) Classified() bool {
	return c.Code != CodeUnclassified && c.Code != ""
}

type rule struct {
	code     string
	pattern  *regexp.Regexp
	evidence string
}

// rules 分類關鍵字規則表。
//
// 關鍵字寫成字元類（例：[認认][證证]）而不是單一寫法，因為生產資料的繁簡是混用的：
// 同一個漏洞，模型可能寫「資訊洩露」也可能寫「信息泄露」。逐一手寫兩份容易漏，
// 用字元類一次收��兩邊。
//
// 規則之間的相對順序只在「同樣長度、同一位置」時才用來破平手；
// 實際挑選規則時看的是「哪個概念在型別文字裡最完整」。
var rules = buildRules()

func buildRules() []rule {
	specs := []struct {
		code     string
		patterns []string
	}{
		{CodeNoSQLInjection, []string{`nosql`, `nosql\s*注入`, `mongodb\s*注入`, `cwe-943`}},
		{CodeSQLInjection, []string{`sql\s*注入`, `sql[\s_-]*injection`, `\bsqli\b`, `cwe-89`}},
		{CodeCommandInjection, []string{`命令注入`, `指令注入`, `命令執行`, `command[\s_-]*injection`, `[遠远]端[程程]?[代碼码]執行`, `\brce\b`, `cwe-7[78]`, `os\s*command`, `shell\s*exec`}},
		{CodeCodeInjection, []string{`[代代][碼码]注入`, `code[\s_-]*injection`, `[模樣][板板]注入`, `\bssti\b`, `[惡恶][意意][脚腳][本本][註注][入入]`, `[模樣][板板][渲][染]`, `cwe-9[45]`, `cwe-1336`, `cwe-707`, `cwe-1321`}},
		{CodeXSS, []string{`\bxss\b`, `跨站[腳脚]本`}},
		{CodeCSRF, []string{`\bcsrf\b`, `跨站[請请][求][偽伪][造]`}},
		{CodeXXE, []string{`\bxxe\b`, `xml\s*外部[實实]體`, `cwe-611`}},
		{CodeSSRF, []string{`\bssrf\b`, `[服][務务]端[請请][求][偽伪][造]`}},
		{CodePathTraversal, []string{
			`[路路][徑径][穿][越]`,
			`[路路][徑径][遍][歷历]`,
			`[目][錄录][遍][歷历]`,
			`任意([檔档][案]|文件)([讀读][取寫写]|存取|下載|下载)`,
			`任意([檔档][案]|文件)`,
			`path[\s_-]*traversal`, `\blfi\b`, `\brfi\b`, `cwe-2[236]`, `cwe-73`,
		}},
		{CodeFileUpload, []string{
			`(任意)?([檔档][案]|文件)上[傳传]`,
			`file[\s_-]*upload`, `cwe-434`,
		}},
		{CodeIDOR, []string{`\bidor\b`, `\bbola\b`, `[物對对][件件]級`, `[物對对][件件][引應]用`, `object\s*level\s*authorization`, `cwe-639`}},
		{CodeAccessControl, []string{
			`越[權权]`, `[訪访][問问][控]制(失效|缺陷)?`, `[存取][控]制(失效|缺陷)?`,
			`broken\s*access`, `未[授授權权][權权][訪访][問问]`, `未[授授權权][權权]`,
			`improper\s*authorization`, `[權权]限[配設][置]?[錯错][誤误]`,
			`cwe-2[46]`, `cwe-8[26]`, `cwe-863`,
		}},
		{CodeCaptchaAbuse, []string{`[驗验][證证][碼码]`, `[簡简][訊息][轟轰][炸]`, `[短][信][轟轰][炸]`, `\bcaptcha\b`, `[人机][機机][驗验][證证]`, `cwe-799`}},
		{CodeAuthentication, []string{
			`[認认][證证](缺陷|繞过|绕过|失效|缺失)?`,
			`[鑑鉴][權权]`,
			`authentication`, `暴力破解`, `brute\s*force`, `[撞][庫库][撞库]`,
			`缺少[認认][證证]`, `缺失[身][份分][驗验][證证]`, `[認认][證证][繞过绕过]`,
			`cwe-287`, `cwe-305`, `cwe-306`, `cwe-307`,
		}},
		{CodeWeakCredential, []string{`弱密[碼码]`, `[預预][設设][密碼码]`, `[預预][設设][帳账][號号]`, `默[認认][憑凭][據据]`, `[預预][設设][憑凭][據据]`, `default\s*credential`, `weak\s*password`, `cwe-521`}},
		{CodeHardcodedCred, []string{`硬[編编][碼码]`, `hardcode`, `明文密[鑰钥]`, `明文密[碼码]`, `api[\s_-]*key`, `cwe-798`}},
		{CodeSession, []string{`cookie`, `[工會会][作作][階阶][段段]`, `[會会][話话][劫劫]持`, `session\s*(id|fixation|management|管理)`, `cwe-384`, `cwe-614`, `cwe-757`, `cwe-1004`}},
		{CodeUserEnumeration, []string{`[用帐賬][戶户][枚][舉举]`, `user\s*enumeration`, `cwe-20[34]`}},
		{CodeCleartext, []string{`明文[傳传][輸输]`, `明文`, `未加密`, `cleartext`, `cwe-31[19]`}},
		{CodeCrypto, []string{`加密`, `[雜杂][湊凑]`, `哈希算法`, `weak\s*crypt`, `\becb\b`, `[傳传][輸输][層层][安][全]`, `cwe-31[06]`, `cwe-32[678]`, `cwe-916`, `cwe-29[57]`}},
		{CodeInfoDisclosure, []string{
			// 注意：「暴露」的「暴」在生產資料裡是 U+66B4（暴），不是 U+66DD（曝）。
			// 兩個字長得幾乎一樣但字碼不同，只寫其中一個會整批漏掉。
			`[資信][訊息][洩泄曝暴][露]`, `information[\s_-]*disclosure`, `info[\s_-]*disclosure`,
			`敏感([個个][人]?)?[數数资][據据料][洩泄曝暴][露]?`, `敏感[資信][訊息]`,
			`情[報报][曝暴]露`, `[環环][境境][變变][量數数][洩泄][露]?`,
			`[目][錄录][列][表]`,
			`[錯错][誤误][資信][訊息]`, `cwe-2(00|09|15)`, `cwe-53[28]`, `cwe-359`,
		}},
		{CodeCORS, []string{`\bcors\b`, `跨[域域]`}},
		{CodeEmailSecurity, []string{`[郵邮][件]`, `\bspf\b`, `\bdkim\b`, `\bdmarc\b`, `mta-sts`, `email[\s_-]*spoof`}},
		{CodeMisconfiguration, []string{
			// 「缺失」與「缺陷」是同一個意思的兩種寫法，字元類要一起收。
			`安全[配設][置][缺][陷失]`, `[配設][置][缺][陷失]`, `[配設][置][錯错][誤误]`,
			`[配設][置][不][當当]`, `[配設][置][管管][理理][缺][陷失]`,
			`[輸输][入入]校[驗验][缺][陷失]?`, `[錯错][誤误][處处][理理][缺][陷]`,
			`[證证][書书][配設][置]`, `tls[_\s-]*(configuration|config)`,
			`misconfiguration`, `missing[_\s-]*security[_\s-]*header`,
			`安全[標标][頭头]`, `安全[響响][應应][頭头]`,
			`默[認认][配設][置]`, `[證证][書书][管管][理理]`, `[證证][書书][過过][期期]`,
			`[點点][擊击][劫劫][持]`, `clickjacking`, `ui\s*redressing`,
			`[組组][態态]`, `cwe-16`, `cwe-693`, `cwe-1188`, `cwe-1021`,
		}},
		{CodeExposedService, []string{
			// 裸的「曝露」太貪心（"敏感資料曝露" 會被誤判成服務暴露），
			// 所以後面必須接著服務、埠、管理介面這類詞才算命中。
			`(服[務务]|端[口口]|[內内][部部]|[管管][理理]|[後后][臺台]|admin|panel)[^，,;；/]{0,8}[曝暴]露`,
			`exposed`, `[管管][理理][面版板介]`, `\bactuator\b`, `\bswagger\b`,
			`admin\s*(panel|interface)`, `[開开][放][埠端]`, `[對对]外[開开][放]`, `公[網网][開开][放]`,
		}},
		{CodeOutdatedComponent, []string{`[過过][時时][組组]件`, `[過过][期期][組组]件`, `[舊旧][版]本`, `cve-\d{4}`, `outdated`, `[已知][弱弱][點点]`, `[已知][漏洞]`, `cwe-937`, `cwe-1035`, `cwe-1104`, `cwe-829`, `cwe-830`, `cwe-353`}},
		{CodeBusinessLogic, []string{`[業业][務务][邏逻][輯辑]`, `business\s*logic`, `abuse_of_functionality`, `[濫滥][用功]`, `cwe-84[01]`}},
		{CodeResourceExhaust, []string{`[資资][源][耗][盡尽]`, `[資资][源][消]耗`, `[拒][絕绝][服][務务]`, `denial\s*of\s*service`, `availability[_\s-]*(weakness|issue)`, `\bavailability\b`, `無上限`, `[无][限][次]`, `cwe-400`, `cwe-770`, `cwe-1333`}},
		{CodeHostHeader, []string{`host\s*header`, `cwe-644`}},
		{CodeOpenRedirect, []string{`[開开][放][重][定][向]`, `重[定][向]`, `open\s*redirect`, `cwe-601`}},
		{CodeSourceDisclosure, []string{`\.git\b`, `[原][始][碼码][洩泄][露]`, `[備备][份][檔档]`, `文件[洩泄][露]`, `backup\s*file`, `cwe-530`}},
		{CodeSubdomainTakeover, []string{`子[域域][名]?[接接][管管]`, `subdomain\s*takeover`, `cwe-1034`}},
		{CodeOpenProxy, []string{`[開开][放][代][理]`, `open\s*proxy`, `cwe-441`}},
		{CodeExcessiveData, []string{`excessive\s*data\s*exposure`, `[過过][度][資资][料料][曝暴]露`, `api3:2023`}},
	}
	built := make([]rule, 0, len(specs)*2)
	for _, spec := range specs {
		for _, pattern := range spec.patterns {
			re, err := regexp.Compile(pattern)
			if err != nil {
				// 規則編譯失敗會讓那條分類永遠失效，而且症狀是「某個型別怎麼都
				// 分不出來」而不是任何錯誤訊息。所以記下來，讓測試可以擋住。
				ruleBuildErrors = append(ruleBuildErrors, fmt.Sprintf("%s / %s: %v", spec.code, pattern, err))
				continue
			}
			built = append(built, rule{code: spec.code, pattern: re, evidence: pattern})
		}
	}
	return built
}

// ruleBuildErrors 記錄編譯失敗的規則（正常情況必須是空的）。
var ruleBuildErrors []string

// cweCategories CWE 編號到受控分類的對照。
var cweCategories = map[string]string{
	"89":   CodeSQLInjection,
	"943":  CodeNoSQLInjection,
	"77":   CodeCommandInjection,
	"78":   CodeCommandInjection,
	"88":   CodeCommandInjection,
	"94":   CodeCodeInjection,
	"95":   CodeCodeInjection,
	"1336": CodeCodeInjection,
	"79":   CodeXSS,
	"352":  CodeCSRF,
	"611":  CodeXXE,
	"918":  CodeSSRF,
	"22":   CodePathTraversal,
	"23":   CodePathTraversal,
	"36":   CodePathTraversal,
	"73":   CodePathTraversal,
	"434":  CodeFileUpload,
	"639":  CodeIDOR,
	"269":  CodeAccessControl,
	"284":  CodeAccessControl,
	"732":  CodeAccessControl,
	"862":  CodeAccessControl,
	"863":  CodeAccessControl,
	"305":  CodeAuthentication,
	"306":  CodeAuthentication,
	"307":  CodeAuthentication,
	"287":  CodeAuthentication,
	"521":  CodeWeakCredential,
	"798":  CodeHardcodedCred,
	"384":  CodeSession,
	"614":  CodeSession,
	"757":  CodeSession,
	"1004": CodeSession,
	"203":  CodeUserEnumeration,
	"204":  CodeUserEnumeration,
	"200":  CodeInfoDisclosure,
	"209":  CodeInfoDisclosure,
	"215":  CodeInfoDisclosure,
	"532":  CodeInfoDisclosure,
	"538":  CodeInfoDisclosure,
	"310":  CodeCrypto,
	"311":  CodeCleartext,
	"319":  CodeCleartext,
	"326":  CodeCrypto,
	"327":  CodeCrypto,
	"328":  CodeCrypto,
	"916":  CodeCrypto,
	"942":  CodeCORS,
	"16":   CodeMisconfiguration,
	"693":  CodeMisconfiguration,
	"1188": CodeMisconfiguration,
	"937":  CodeOutdatedComponent,
	"1035": CodeOutdatedComponent,
	"1104": CodeOutdatedComponent,
	"840":  CodeBusinessLogic,
	"841":  CodeBusinessLogic,
	"400":  CodeResourceExhaust,
	"770":  CodeResourceExhaust,
	"1333": CodeResourceExhaust,
	"601":  CodeOpenRedirect,
	"644":  CodeHostHeader,
	"530":  CodeSourceDisclosure,
	"799":  CodeCaptchaAbuse,
	"1034": CodeSubdomainTakeover,
	"441":  CodeOpenProxy,
	"213":  CodeExcessiveData,
	// 以下是生產資料裡實際出現、但原本沒對照到的編號。
	"707":  CodeCodeInjection,     // Improper Neutralization
	"829":  CodeOutdatedComponent, // Inclusion of Functionality from Untrusted Control Sphere
	"830":  CodeOutdatedComponent, // Inclusion of Functionality from Untrusted Control Sphere
	"1321": CodeCodeInjection,     // Prototype Pollution
	"353":  CodeOutdatedComponent, // Missing Support for Integrity Check
	"359":  CodeInfoDisclosure,    // Exposure of Private Personal Information
	"295":  CodeCrypto,            // Improper Certificate Validation
	"297":  CodeCrypto,            // Improper Validation of Certificate with Host Mismatch
	"1021": CodeMisconfiguration,  // Clickjacking
}

// artifactTypes 是「看起來像型別、其實是 JSON 欄位名或通用字」的佔位值。
//
// 這些值不是漏洞類型（多半是模型回傳 JSON 時欄位名被當成類型），
// 因此不能直接當分類依據；改由標題與描述判定。
var artifactTypes = map[string]bool{
	"finding": true, "findings": true, "finding_type": true, "target": true, "targets": true,
	"note": true, "notes": true, "configuration": true, "config": true, "exploit": true,
	"exploitability": true, "test": true, "testing": true, "api": true, "infra": true,
	"infrastructure": true, "login": true, "port": true, "database": true, "db": true,
	"exposure": true, "missing_update": true, "issue": true, "issues": true, "type": true,
	"vulnerability": true, "vuln": true, "result": true, "results": true, "summary": true,
	"description": true, "title": true, "info": true, "information": true, "severity": true,
	"impact": true, "recommendation": true, "evidence": true, "category": true, "subtype": true,
	"sub_type": true, "other": true, "unknown": true, "n/a": true, "na": true, "none": true,
	"tbd": true, "todo": true, "misc": true, "general": true, "generic": true, "task": true,
	"item": true, "domain": true, "host": true, "url": true, "path": true, "endpoint": true,
	"module": true, "component": true, "service": true, "app": true, "application": true,
	"web": true, "site": true, "page": true, "parameter": true, "params": true, "payload": true,
	"poc": true, "proof of concept": true,
}

var artifactConfidencePattern = regexp.MustCompile(`^confidence[._-]?\d*$`)

// IsArtifactType 判斷型別文字是否只是佔位字（不是真正的漏洞類型）。
func IsArtifactType(value string) bool {
	normalized := strings.ToLower(strings.TrimSpace(value))
	if normalized == "" {
		return true
	}
	if artifactTypes[normalized] {
		return true
	}
	return artifactConfidencePattern.MatchString(normalized)
}

var cwePattern = regexp.MustCompile(`cwe[-_\s]?(\d{1,4})`)

// segmentSplitter 複合型別的分隔符。
//
// 「硬編碼憑證 / 敏感資訊洩漏」這種寫法裡，作者先寫的那個才是主要問題；
// 用分隔符切成段、逐段判定、第一段命中即採用，才符合這個語意。
var segmentSplitter = regexp.MustCompile(`[/、;；,，+＋]|\band\b`)

// classifyFromCWE 從文字中的 CWE 編號對照受控分類。
func classifyFromCWE(text string) (Classification, bool) {
	matches := cwePattern.FindAllStringSubmatch(text, -1)
	if len(matches) == 0 {
		return Classification{}, false
	}
	for _, match := range matches {
		if code, ok := cweCategories[match[1]]; ok {
			return newClassification(code, SourceCWE, "CWE-"+match[1]), true
		}
	}
	return Classification{}, false
}

// classifyText 用文字判定受控分類。
func classifyText(text string) (Classification, bool) {
	normalized := strings.ToLower(text)
	if strings.TrimSpace(normalized) == "" {
		return Classification{}, false
	}
	if IsArtifactType(normalized) {
		return Classification{}, false
	}

	for _, segment := range segmentSplitter.Split(normalized, -1) {
		if strings.TrimSpace(segment) == "" {
			continue
		}
		if result, ok := classifySegment(segment); ok {
			return result, true
		}
	}
	return classifyFromCWE(normalized)
}

// 分類優先層級。
//
// 同一段文字可能同時命中多個分類，這時怎麼選決定了分類準不準。
// 單純比「命中字數長度」會出錯：「配置錯誤」四個字會蓋過「跨域」「郵件」
// 這類具體指標（後者只有兩個字），於是 "CORS 跨域策略配置錯誤" 會被歸成
// 泛用的「安全設定缺陷」。因此比較順序是：層級 → 命中長度 → 出現位置。
//
// 第一層是具體的攻擊機制或特定領域的弱點；第二層是泛用描述
// （資訊洩漏、安全設定缺陷、加密弱點），只在沒有更具體的分類時才採用。
const (
	tierSpecific = 1
	tierGeneric  = 2
)

// codeTier 分類代碼所屬的層級。沒列到的分類一律視為第一層（具體）。
var codeTier = map[string]int{
	CodeInfoDisclosure:   tierGeneric,
	CodeMisconfiguration: tierGeneric,
	CodeCrypto:           tierGeneric,
}

func tierOf(code string) int {
	if tier, ok := codeTier[code]; ok {
		return tier
	}
	return tierSpecific
}

// classifySegment 判定單一段落。
//
// 挑選方式：先比層級（具體優先於泛用），再比命中長度最長者優先
// （概念寫得最完整的），長度相同時取位置最前者，再相同才依規則表順序。
// 取「最長」而不是「最前」是為了分辨「任意檔案上傳」是上傳類問題、
// 「任意檔案讀取」是路徑穿越類問題。
func classifySegment(segment string) (Classification, bool) {
	bestTier := 0
	bestLength := 0
	bestIndex := len(segment) + 1
	bestRule := rule{}
	found := false
	for _, candidate := range rules {
		loc := candidate.pattern.FindStringIndex(segment)
		if loc == nil {
			continue
		}
		tier := tierOf(candidate.code)
		length := loc[1] - loc[0]
		better := !found
		if found {
			switch {
			case tier < bestTier:
				better = true
			case tier == bestTier && length > bestLength:
				better = true
			case tier == bestTier && length == bestLength && loc[0] < bestIndex:
				better = true
			}
		}
		if better {
			found = true
			bestTier = tier
			bestLength = length
			bestIndex = loc[0]
			bestRule = candidate
		}
	}
	if found {
		return newClassification(bestRule.code, SourceRule, bestRule.evidence), true
	}
	return classifyFromCWE(segment)
}

func newClassification(code, source, evidence string) Classification {
	return Classification{
		Code:     code,
		LabelZh:  LabelZh(code),
		LabelEn:  LabelEn(code),
		Source:   source,
		Evidence: evidence,
	}
}

// Classify 判定一筆漏洞的受控分類。
//
// 判定順序：
//  1. 型別文字本身（命中關鍵字規則 → CWE 對照）；
//  2. 型別是佔位字（finding/target/note…）時，改用標題與描述；
//  3. 都不行 → 待人工歸類。
//
// 分類結果不含任何推斷出的嚴重度：未判定就是未判定，這裡只負責把「型別」講清楚。
func Classify(typeText, title, description string) Classification {
	if result, ok := classifyText(typeText); ok {
		return result
	}
	if result, ok := classifyText(title + " " + description); ok {
		result.Source = SourceContext
		return result
	}
	return newClassification(CodeUnclassified, SourceDefault, "")
}
