package app

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"testing"
)

// updateBaseline 讓 TestWebI18nNoNewHardcodedText 改為重新產生基準檔。
var updateBaseline = flag.Bool("update", false,
	"重新產生 "+baselineFile+"（僅供 TestWebI18nNoNewHardcodedText 使用）")

// 前端 i18n 守門測試。
//
// 背景：web/ 下的介面文案有 en-US 與 zh-CN 兩份語言包，靠 data-i18n 屬性與
// t()/assetT() 輔助函式對應。這些對應關係原本完全沒有測試把關——缺一個鍵、
// 兩份語言包鍵集不同步、或新頁面忘了加 data-i18n，都不會有任何測試失敗，
// 只會在使用者切換語言時才發現畫面出現半中半英或內部鍵名。
//
// 三個測試分��守不同的失效模式：
//   - TestWebI18nDictionariesKeySetsMatch：兩份語言包必須有完全相同的鍵集。
//   - TestWebI18nReferencedKeysExist：模板與 JS 裡引用的每個鍵都必須真的存在。
//   - TestWebI18nNoNewHardcodedText：不允許新增沒走 i18n 的硬編中文（以基準檔記錄既有欠債）。

const (
	webRoot      = "../../web"
	templatesDir = webRoot + "/templates"
	staticJSDir  = webRoot + "/static/js"
	i18nDir      = webRoot + "/static/i18n"
	baselineFile = "testdata/i18n_hardcoded_baseline.json"
)

// cjkPattern 匹配 CJK 統一表意文字。用字元類別而非列舉，避免漏掉罕用字。
var cjkPattern = regexp.MustCompile(`[\x{4e00}-\x{9fff}]`)

// 一個 JS 字串字面值（雙引號、單引號或反引號）。Go 的 regexp 不支援反向參考，
// 所以三種引號各自列舉，不用「引號 + \1」。
const jsStringLiteral = `(?:"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|` + "`(?:\\\\.|[^`\\\\])*`" + `)`

// loadDictionaries 讀入兩份語言包，展開成以點號路徑為鍵的扁平 map。
func loadDictionaries(t *testing.T) map[string]map[string]string {
	t.Helper()
	out := map[string]map[string]string{}
	for _, lang := range []string{"en-US", "zh-CN"} {
		path := filepath.Join(i18nDir, lang+".json")
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("讀取語言包 %s: %v", lang, err)
		}
		var tree map[string]any
		if err := json.Unmarshal(raw, &tree); err != nil {
			t.Fatalf("解析語言包 %s: %v", lang, err)
		}
		flat := map[string]string{}
		flatten("", tree, flat)
		out[lang] = flat
	}
	return out
}

func flatten(prefix string, node any, into map[string]string) {
	switch v := node.(type) {
	case map[string]any:
		for key, child := range v {
			flatten(joinKey(prefix, key), child, into)
		}
	case string:
		into[prefix] = v
	}
}

func joinKey(prefix, key string) string {
	if prefix == "" {
		return key
	}
	return prefix + "." + key
}

// pluralSuffixes 是 i18next 的複數形式後綴。
//
// en-US 有 12 個 dashboard 鍵以 _one/_other 形式定義，zh-CN 則是不帶後綴的單純鍵。
// 這是 i18next 的正確慣例而非缺陷——中文沒有名詞複數，不需要區分。所以比對鍵集
// 與解析鍵時都必須先把後綴剝掉，直接要求兩份檔案鍵集完全相同會產生 24 個誤報。
var pluralSuffixes = []string{"_zero", "_one", "_two", "_few", "_many", "_other"}

// baseKey 剝除 i18next 複數後綴，取得基礎鍵名。
func baseKey(key string) string {
	for _, suffix := range pluralSuffixes {
		if strings.HasSuffix(key, suffix) {
			return strings.TrimSuffix(key, suffix)
		}
	}
	return key
}

// hasKey 判斷某語言是否定義了該鍵：接受精確匹配，也接受任一複數形式。
func hasKey(dict map[string]string, key string) bool {
	if _, ok := dict[key]; ok {
		return true
	}
	for _, suffix := range pluralSuffixes {
		if _, ok := dict[key+suffix]; ok {
			return true
		}
	}
	return false
}

// TestWebI18nDictionariesKeySetsMatch 保證兩個語言包涵蓋相同的基礎鍵。
// 少了任何一邊，使用者切換到該語言時就會退回內部鍵名或空白。
func TestWebI18nDictionariesKeySetsMatch(t *testing.T) {
	dicts := loadDictionaries(t)

	bases := map[string]map[string]bool{}
	for lang, dict := range dicts {
		set := map[string]bool{}
		for key := range dict {
			set[baseKey(key)] = true
		}
		bases[lang] = set
	}

	var missingInEN, missingInZH []string
	for key := range bases["zh-CN"] {
		if !bases["en-US"][key] {
			missingInEN = append(missingInEN, key)
		}
	}
	for key := range bases["en-US"] {
		if !bases["zh-CN"][key] {
			missingInZH = append(missingInZH, key)
		}
	}
	sort.Strings(missingInEN)
	sort.Strings(missingInZH)

	if len(missingInEN) > 0 {
		t.Errorf("en-US.json 缺少 %d 個鍵：%s", len(missingInEN), previewKeys(missingInEN))
	}
	if len(missingInZH) > 0 {
		t.Errorf("zh-CN.json 缺少 %d 個鍵：%s", len(missingInZH), previewKeys(missingInZH))
	}
	if len(dicts["en-US"]) == 0 || len(dicts["zh-CN"]) == 0 {
		t.Fatalf("語言包內容異常：en-US %d 鍵、zh-CN %d 鍵", len(dicts["en-US"]), len(dicts["zh-CN"]))
	}
	t.Logf("語言包鍵數：en-US %d、zh-CN %d（複數形式已合併後比較基礎鍵）",
		len(dicts["en-US"]), len(dicts["zh-CN"]))
}

func previewKeys(keys []string) string {
	const limit = 12
	if len(keys) <= limit {
		return strings.Join(keys, ", ")
	}
	return strings.Join(keys[:limit], ", ") + fmt.Sprintf(" …（另有 %d 個）", len(keys)-limit)
}

// TestWebI18nReferencedKeysExist 檢查模板與 JS 引用的每個 i18n 鍵都存在於兩份語言包。
// 這是三個測試裡價值最高的一個：它同時擋下「加了 data-i18n 卻忘了翻譯」和
// 「改了字典鍵名卻沒改引用處」兩種最常見的錯誤。
func TestWebI18nReferencedKeysExist(t *testing.T) {
	dicts := loadDictionaries(t)

	files, err := collectSourceFiles()
	if err != nil {
		t.Fatalf("收集前端檔案: %v", err)
	}

	attrPattern := regexp.MustCompile(`data-i18n(?:-title)?="([^"]+)"`)
	// 三種引號都要認：t('key', '後備值') 在專案裡很常見，只認雙引號會讓
	// 單引號的引用完全不經檢查——那正是最容易被改掉而沒人發現的情況。
	//
	// 這裡不認 t/assetT 兩個名字，專案裡的翻譯包裝有二十幾個 varied 名稱；
	// 動態組鍵另外用程式碼排除（見 concatenatedKey），因為 RE2 不支援
	// lookahead，沒辦法寫成「後面不是 +」。
	callPattern := regexp.MustCompile(`\b[A-Za-z_$][A-Za-z0-9_$]*\(\s*(?:"([^"]+)"|'([^']+)'|` +
		"`([^`]+)`" + `)`)

	total := 0
	for _, file := range files {
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatalf("讀取 %s: %v", file, err)
		}
		content := string(raw)

		seen := map[string]bool{}
		for _, m := range attrPattern.FindAllStringSubmatchIndex(content, -1) {
			seen[content[m[2]:m[3]]] = true
		}
		for _, m := range callPattern.FindAllStringSubmatchIndex(content, -1) {
			key := ""
			for g := 2; g+1 < len(m); g += 2 {
				if m[g] >= 0 { // 三個群組對應三種引號，只會有一個非空
					key = content[m[g]:m[g+1]]
					break
				}
			}
			if key == "" || !i18nKeyPattern.MatchString(key) {
				continue // 不是 i18n 鍵
			}
			if isConcatenated(content, m[1]) {
				continue // window.t('mcpMonitor.' + k)：鍵在執行期才決定
			}
			seen[key] = true
		}
		keys := make([]string, 0, len(seen))
		for key := range seen {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		total += len(keys)

		for _, key := range keys {
			for _, lang := range []string{"en-US", "zh-CN"} {
				if !hasKey(dicts[lang], key) {
					t.Errorf("%s: 語言包 %s 缺少鍵 %q", displayPath(file), lang, key)
				}
			}
		}
	}
	t.Logf("掃描 %d 個前端檔案，共引用 %d 個 i18n 鍵", len(files), total)
}

// TestWebI18nNoNewHardcodedText 擋下「新增沒走 i18n 的硬編中文」。
//
// 目前前端有 300 多行文案尚未翻譯（散落於 sentinel、rbac、settings 等頁面），
// 一次全補不現實。因此這裡不要求歸零，而是把現有欠債記錄在基準檔裡，
// 往後只擋「新增」——修好一頁就從基準移除一條，讓數字可見、可逐步下降。
func TestWebI18nNoNewHardcodedText(t *testing.T) {
	files, err := collectSourceFiles()
	if err != nil {
		t.Fatalf("收集前端檔案: %v", err)
	}

	found := map[string][]string{}
	for _, file := range files {
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatalf("讀取 %s: %v", file, err)
		}
		offenders := hardcodedTextIn(displayPath(file), string(raw))
		if len(offenders) > 0 {
			found[displayPath(file)] = offenders
		}
	}

	if *updateBaseline {
		writeBaseline(t, found)
		return
	}

	baseline := loadBaseline(t)

	// 基準檔由本測試自己產生，不要手寫：
	//
	//	go test ./internal/app/ -run TestWebI18nNoNewHardcodedText -update
	//
	// 手寫會與掃描規則脫節：規則一改（例如多認一種引號），手寫的基準會立刻失效。
	var newOffenders []string
	totalKnown, totalNow := 0, 0
	allFiles := map[string]bool{}
	for name := range baseline {
		allFiles[name] = true
	}
	for name := range found {
		allFiles[name] = true
	}
	names := make([]string, 0, len(allFiles))
	for name := range allFiles {
		names = append(names, name)
	}
	sort.Strings(names)

	for _, name := range names {
		known := map[string]bool{}
		for _, s := range baseline[name] {
			known[s] = true
			totalKnown++
		}
		for _, s := range found[name] {
			totalNow++
			if !known[s] {
				newOffenders = append(newOffenders, name+": "+s)
			}
		}
	}

	if len(newOffenders) > 0 {
		sort.Strings(newOffenders)
		const limit = 20
		shown := newOffenders
		suffix := ""
		if len(shown) > limit {
			shown = shown[:limit]
			suffix = fmt.Sprintf("（另有 %d 個）", len(newOffenders)-limit)
		}
		t.Errorf("新增 %d 處未走 i18n 的硬編中文%s：\n  %s\n  請改用 data-i18n 屬性或 t()/assetT()，\n"+
			"  若確實不需翻譯（例如品牌名），把它加進 %s 基準檔並註明理由。",
			len(newOffenders), suffix, strings.Join(shown, "\n  "), baselineFile)
	}
	t.Logf("硬編中文：基準記錄 %d 處、目前 %d 處，修好一頁可從 %s 移除對應條目",
		totalKnown, totalNow, baselineFile)
}

// hardcodedTextIn 找出檔案中未走 i18n 的中文字串。
// hardcodedTextIn 找出檔案中未走 i18n 的中文字串。
//
// 刻意不算欠債的兩種情形：
//   - 帶 data-i18n（或 data-i18n-attr）元素的文字與屬性值：那是語言包沒載入前的
//     後備值，與 JS 端 t(key, fallback) 的後備值同一個道理。
//   - t()/assetT() 呼叫裡的字串：鍵與中文後備值都是刻意的。
func hardcodedTextIn(path, content string) []string {
	var candidates []string
	if strings.HasSuffix(path, ".html") {
		candidates = htmlVisibleText(content)
	} else if strings.HasSuffix(path, ".js") {
		candidates = jsUserFacingStrings(content)
	} else {
		return nil
	}

	out := make([]string, 0, len(candidates))
	for _, s := range candidates {
		if cjkPattern.MatchString(s) {
			out = append(out, s)
		}
	}
	// 去重：同一個檔案裡重複出現的同一句文案算一處。否則複製貼上同一段程式碼
	// 會灌出成百上千筆，而實際上只有一種新文案。
	seen := map[string]bool{}
	unique := make([]string, 0, len(out))
	for _, s := range out {
		if !seen[s] {
			seen[s] = true
			unique = append(unique, s)
		}
	}
	sort.Strings(unique)
	return unique
}

// ---------------------------------------------------------------- JS 掃描

// jsUserFacingStrings 走訪 JavaScript 原始碼，回傳所有字串字面值（保留引號），
// 但跳過 t()/assetT() 呼叫範圍內的字串。
//
// 這裡用手寫狀態機而不是正規表達式，理由是實測過的：註解裡的一個撇號
// （例如 // don't do this）會讓 `"..."` 樣式從那裡一路配對到數萬字元之後，
// 產出一筆 6 萬字元的假字串。regex/ 除錯運算子的歧義不在此處理——含中文的
// 正規表達式字面值極少見，漏掉只會少報，不會誤報。
func jsUserFacingStrings(src string) []string {
	var out []string
	skipUntil := -1 // t()/assetT() 呼叫結束位置；此位置之前的字串都是翻譯參數
	// prev 與 prevWord 記錄上一個有意義的 token，用來區分 '/' 是正規表達式的
	// 開頭還是除法運算子。
	prev, prevWord := byte(0), ""
	i, n := 0, len(src)
	for i < n {
		c := src[i]
		switch {
		case c == '/' && i+1 < n && src[i+1] == '/':
			for i < n && src[i] != '\n' {
				i++
			}
		case c == '/' && i+1 < n && src[i+1] == '*':
			i += 2
			for i+1 < n && !(src[i] == '*' && src[i+1] == '/') {
				i++
			}
			i += 2
		case c == '/' && regexAllowedAfter(prev, prevWord):
			// 正規表達式字面值。必須處理它，否則 /'/g 裡的引號會被當成字串
			// 開頭，之後整個檔案都錯位——實測會產出一筆八萬多字元的假字串。
			i++
			inClass := false
		regexScan:
			for i < n {
				switch {
				case src[i] == '\\':
					i += 2
					continue
				case src[i] == '\n':
					// 沒閉合就不是正規表達式，停在這裡，別把整個檔案吃掉
					break regexScan
				case src[i] == '[':
					inClass = true
				case src[i] == ']':
					inClass = false
				case src[i] == '/' && !inClass:
					i++
					for i < n && isIdentPart(src[i]) { // 修飾旗標 g/i/m
						i++
					}
					break regexScan
				}
				i++
			}
			prev, prevWord = '/', ""
		case c == '`':
			// 模板字面值只取「靜態文字片段」，${ } 裡的運算式交回主迴圈處理。
			// 整包當成一個字串會把巢狀的 t('key', '中文') 一併算進來——實測在
			// c2.js 產生過 4 千多字元的假字串。
			i = scanTemplateChunks(src, i, skipUntil, &out)
			prev, prevWord = '`', ""
		case c == '\'' || c == '"':
			start := i
			i = scanJSString(src, i)
			if i > skipUntil {
				out = append(out, src[start:i])
			}
			prev, prevWord = c, ""
		case isIdentStart(c):
			start := i
			for i < n && isIdentPart(src[i]) {
				i++
			}
			word := src[start:i]
			if i < n && src[i] == '(' && isTranslationCall(src, word, i) {
				skipUntil = matchingParen(src, i)
			}
			prev, prevWord = word[len(word)-1], word
		default:
			if c != ' ' && c != '\t' && c != '\r' && c != '\n' {
				prev, prevWord = c, ""
			}
			i++
		}
	}
	return out
}

// regexAllowedAfter 判斷 '/' 這個位置該當成正規表達式的開頭還是除法。
// 判斷依據是它前面有意義的 token：運算子或關鍵字之後必為正規表達式，
// 識別字或右括號之後則是除法。
func regexAllowedAfter(prev byte, prevWord string) bool {
	if prev == 0 {
		return true
	}
	switch prev {
	case '(', ',', '=', ':', '[', '!', '&', '|', '?', ';', '{', '}', '+', '-', '*', '%', '<', '>', '~', '^':
		return true
	}
	switch prevWord {
	case "return", "typeof", "instanceof", "in", "of", "new", "delete", "void",
		"case", "do", "else", "yield", "await", "throw":
		return true
	}
	return false
}

// scanTemplateChunks 掃過模板字面值，把其中的靜態文字片段（${ } 之間的部分）
// 收進 out，${ } 內的運算式則略過——裡面的字串由主迴圈另行處理，這樣
// t('key', '中文') 的後備值才不會被算成欠債。回傳模板結束後的索引。
func scanTemplateChunks(src string, i int, skipUntil int, out *[]string) int {
	n := len(src)
	i++ // 跳過開頭的反引號
	chunkStart := i
	for i < n {
		switch src[i] {
		case '\\':
			i += 2
			continue
		case '`':
			if chunkStart < i && i > skipUntil {
				*out = append(*out, src[chunkStart:i])
			}
			return i + 1
		case '$':
			if i+1 < n && src[i+1] == '{' {
				if chunkStart < i && i > skipUntil {
					*out = append(*out, src[chunkStart:i])
				}
				i = scanTemplateExpr(src, i+1)
				chunkStart = i
				continue
			}
		}
		i++
	}
	return n
}

// i18nKeyPattern 認得本專案的 i18n 鍵格式：命名空間.鍵名。
var i18nKeyPattern = regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$`)

// isConcatenated 判斷字面值之後（略過空白）是否接著 '+'，也就是這是
// window.t('mcpMonitor.' + statusKey) 這種執行期才決定鍵的動態組鍵。
// 用程式碼判斷而不用 regex lookahead：Go 的 RE2 不支援 (?!)。
func isConcatenated(content string, after int) bool {
	for i := after; i < len(content); i++ {
		switch content[i] {
		case ' ', '\t', '\r', '\n':
			continue
		case '+':
			return true
		}
		return false
	}
	return false
}

// isTranslationCall 判斷 open（指向 '('）處的呼叫是不是翻譯包裝。
//
// 不列舉函式名，而是看第一個參數：專案裡的翻譯包裝有 t/_t/c2t/wsT/tp/assetT/
// rbacT/vulnT/dt/settingsT/auditT/statusT 等二十幾個列舉不完的名稱，其中還混著
// tr（DOM 的 <tr> 工廠）這種同形字，改用「第一個參數是帶點號的字串」來認
// 遠比維護名單可靠——i18n 鍵一律是 ns.key，非翻譯函式不會被這樣呼叫。
//
// 唯一例外是 applyHintMarkup：它的鍵是第二個參數（第一個是元素 id），
// 所以另外列名。
func isTranslationCall(src string, name string, open int) bool {
	if name == "applyHintMarkup" {
		return true
	}
	j := open + 1
	for j < len(src) && (src[j] == ' ' || src[j] == '\t' || src[j] == '\n' || src[j] == '\r') {
		j++
	}
	if j >= len(src) || !isJSQuote(src[j]) {
		return false
	}
	end := scanJSString(src, j)
	return i18nKeyPattern.MatchString(unquoteJS(src[j:end]))
}

// unquoteJS 去掉字面值的外層引號。
func unquoteJS(literal string) string {
	if len(literal) >= 2 {
		return literal[1 : len(literal)-1]
	}
	return literal
}

func isJSQuote(c byte) bool { return c == '\'' || c == '"' || c == '`' }

// scanJSString 從 src[i]（一個引號字元）掃到該字面值結束之後，回傳新的索引。
//
// 模板字面值要特別處理 ${ }：裡面可以再巢狀字串與模板，而外層的反引號不會
// 因為巢狀模板而出現。不處理的話，一行巢狀模板就會讓後面幾千個字元全部被
// 併進同一筆「字串」——實測在 monitor.js 產生過 2 萬多字元的假字串。
func scanJSString(src string, i int) int {
	quote, n := src[i], len(src)
	i++
	for i < n {
		switch src[i] {
		case '\\':
			i += 2
			continue
		case quote:
			return i + 1
		case '\n':
			if quote != '`' {
				// 單引號與雙引號字串不能跨行；遇到換行表示前面已經解析錯位，
				// 停在這裡，不要把整個檔案吞成一個字串。
				return i
			}
		case '$':
			if quote == '`' && i+1 < n && src[i+1] == '{' {
				i = scanTemplateExpr(src, i+1)
				continue
			}
		}
		i++
	}
	return n
}

// scanTemplateExpr 掃過模板字面值 ${ ... } 內的表達式；src[i] 指向 '{'。
// 回傳對應 '}' 之後的索引。裡面的字串同樣交給 scanJSString，避免引號或
// 反引號影響大括號的配對。
func scanTemplateExpr(src string, i int) int {
	depth, n := 0, len(src)
	for i < n {
		switch c := src[i]; {
		case c == '/' && i+1 < n && src[i+1] == '/':
			for i < n && src[i] != '\n' {
				i++
			}
			continue
		case c == '/' && i+1 < n && src[i+1] == '*':
			i += 2
			for i+1 < n && !(src[i] == '*' && src[i+1] == '/') {
				i++
			}
			i += 2
			continue
		case isJSQuote(c):
			i = scanJSString(src, i)
			continue
		case c == '{':
			depth++
		case c == '}':
			depth--
			if depth == 0 {
				return i + 1
			}
		}
		i++
	}
	return n
}

func isIdentStart(c byte) bool {
	return c == '_' || c == '$' || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
}

func isIdentPart(c byte) bool { return isIdentStart(c) || (c >= '0' && c <= '9') }

// matchingParen 回傳 open 處 '(' 對應的 ')' 位置之後的偏移。
// 掃描時跳過字串字面值與註解，避免括號出現在字串裡時配對錯誤。
func matchingParen(src string, open int) int {
	depth := 0
	for i := open; i < len(src); i++ {
		switch c := src[i]; {
		case c == '/' && i+1 < len(src) && src[i+1] == '/':
			for i < len(src) && src[i] != '\n' {
				i++
			}
		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			i += 2
			for i+1 < len(src) && !(src[i] == '*' && src[i+1] == '/') {
				i++
			}
		case isJSQuote(c):
			// 用同一套掃描，巢狀模板裡的括號才不會算錯
			i = scanJSString(src, i) - 1
		case c == '(':
			depth++
		case c == ')':
			depth--
			if depth == 0 {
				return i + 1
			}
		}
	}
	return len(src)
}

// ---------------------------------------------------------------- HTML 掃描

// htmlVisibleText 回傳 HTML 中會顯示給使用者的文字，以及沒有走 i18n 的屬性值。
//
// 用標籤堆疊而不是正規表達式：元素文字在 HTML 裡不是引號包著的，用 `"..."`
// 樣式只會抓到屬性值，而且會跨標籤邊界亂配對。
// 帶 data-i18n 的元素整棵跳過——它的文字由語言包提供，硬編內容只是後備值。
func htmlVisibleText(src string) []string {
	var out []string
	type frame struct {
		translated bool // 這個元素（或其祖先）帶 data-i18n
		skipText   bool
	}
	var stack []frame
	i, n := 0, len(src)

	for i < n {
		if src[i] != '<' {
			j := i
			for j < n && src[j] != '<' {
				j++
			}
			if len(stack) > 0 {
				top := stack[len(stack)-1]
				if !top.translated && !top.skipText {
					if text := strings.TrimSpace(htmlUnescape(src[i:j])); text != "" {
						out = append(out, text)
					}
				}
			}
			i = j
			continue
		}

		// 註解
		if strings.HasPrefix(src[i:], "<!--") {
			end := strings.Index(src[i+4:], "-->")
			if end < 0 {
				break
			}
			i += 4 + end + 3
			continue
		}
		// <script> / <style> 的內容不是文案
		if name, ok := tagNameAt(src, i); ok && (name == "script" || name == "style") {
			closing := "</" + name
			end := indexFoldFrom(src, i, closing)
			if end < 0 {
				break
			}
			i = end
			continue
		}

		end := strings.IndexByte(src[i:], '>')
		if end < 0 {
			break
		}
		tag := src[i : i+end+1]
		i += end + 1

		closing := strings.HasPrefix(strings.TrimSpace(tag), "</")
		body := strings.TrimSpace(strings.TrimSuffix(strings.TrimSpace(tag), ">"))
		body = strings.TrimSuffix(body, "/")
		if closing {
			if len(stack) > 0 {
				stack = stack[:len(stack)-1]
			}
			continue
		}
		if voidHTMLElements[tagNameOf(body)] || strings.HasSuffix(strings.TrimSpace(tag), "/>") {
			continue
		}

		translated := hasAttr(body, "data-i18n")
		if !translated {
			for _, attr := range []string{"data-i18n-attr", "data-i18n-title"} {
				if hasAttr(body, attr) {
					translated = true
				}
			}
		}
		// 沒有 data-i18n 的屬性值若是中文，就是沒有翻譯的 placeholder/title
		if !translated {
			for _, value := range attrValues(body) {
				if cjkPattern.MatchString(value) {
					out = append(out, value)
				}
			}
		}
		stack = append(stack, frame{translated: translated, skipText: translated})
	}
	return out
}

var voidHTMLElements = map[string]bool{
	"area": true, "base": true, "br": true, "col": true, "embed": true,
	"hr": true, "img": true, "input": true, "link": true, "meta": true,
	"param": true, "source": true, "track": true, "wbr": true,
}

func tagNameOf(body string) string {
	body = strings.TrimPrefix(body, "/")
	for i := 0; i < len(body); i++ {
		c := body[i]
		if isIdentPart(c) || c == '-' {
			continue
		}
		return strings.ToLower(body[:i])
	}
	return strings.ToLower(body)
}

// tagNameAt 讀取 src[pos] 處標籤的 名稱（若 src[pos] 確實是標籤開頭）。
func tagNameAt(src string, pos int) (string, bool) {
	if pos+1 >= len(src) || src[pos+1] == '/' {
		return "", false
	}
	j := pos + 1
	for j < len(src) && (isIdentPart(src[j]) || src[j] == '-') {
		j++
	}
	if j == pos+1 {
		return "", false
	}
	return strings.ToLower(src[pos+1 : j]), true
}

func indexFoldFrom(src string, from int, lowerNeedle string) int {
	if from >= len(src) {
		return -1
	}
	idx := strings.Index(strings.ToLower(src[from:]), lowerNeedle)
	if idx < 0 {
		return -1
	}
	return from + idx
}

func hasAttr(tag, name string) bool {
	lower := strings.ToLower(tag)
	needle := " " + strings.ToLower(name) + "="
	if strings.HasPrefix(lower, strings.ToLower(name)+"=") {
		return true
	}
	return strings.Contains(lower, needle)
}

// attrValues 取出標籤內所有屬性值（含單引號、雙引號與無引號三種寫法）。
func attrValues(tag string) []string {
	var out []string
	i, n := 0, len(tag)
	for i < n {
		if tag[i] != '=' {
			i++
			continue
		}
		i++
		for i < n && (tag[i] == ' ' || tag[i] == '\t' || tag[i] == '\n' || tag[i] == '\r') {
			i++
		}
		if i >= n {
			break
		}
		switch tag[i] {
		case '"', '\'':
			quote := tag[i]
			i++
			start := i
			for i < n && tag[i] != quote {
				i++
			}
			out = append(out, htmlUnescape(tag[start:i]))
			i++
		default:
			start := i
			for i < n && tag[i] != ' ' && tag[i] != '\t' && tag[i] != '\n' && tag[i] != '>' {
				i++
			}
			out = append(out, tag[start:i])
		}
	}
	return out
}

var htmlEntityPattern = regexp.MustCompile(`&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);`)

func htmlUnescape(s string) string {
	return htmlEntityPattern.ReplaceAllStringFunc(s, func(e string) string {
		switch e {
		case "&amp;":
			return "&"
		case "&lt;":
			return "<"
		case "&gt;":
			return ">"
		case "&quot;":
			return "\""
		case "&nbsp;":
			return " "
		}
		return e
	})
}

func collectSourceFiles() ([]string, error) {
	var files []string
	html, err := filepath.Glob(filepath.Join(templatesDir, "*.html"))
	if err != nil {
		return nil, err
	}
	files = append(files, html...)
	js, err := filepath.Glob(filepath.Join(staticJSDir, "*.js"))
	if err != nil {
		return nil, err
	}
	files = append(files, js...)
	sort.Strings(files)
	return files, nil
}

// writeBaseline 重新產生基準檔。
func writeBaseline(t *testing.T, found map[string][]string) {
	t.Helper()
	total := 0
	for _, offenders := range found {
		total += len(offenders) // hardcodedTextIn 已經去重並排序
	}
	data, err := json.MarshalIndent(found, "", "  ")
	if err != nil {
		t.Fatalf("序列化基準: %v", err)
	}
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(baselineFile), 0o755); err != nil {
		t.Fatalf("建立基準檔目錄: %v", err)
	}
	if err := os.WriteFile(baselineFile, data, 0o644); err != nil {
		t.Fatalf("寫入基準檔: %v", err)
	}
	t.Logf("已重新產生 %s：%d 個檔案、%d 處未走 i18n 的硬編中文",
		baselineFile, len(found), total)
}

func loadBaseline(t *testing.T) map[string][]string {
	t.Helper()
	raw, err := os.ReadFile(baselineFile)
	if os.IsNotExist(err) {
		t.Fatalf("缺少基準檔 %s：它記錄目前已知、暫時接受的未翻譯文案。\n"+
			"產生方式：go test ./internal/app/ -run TestWebI18nNoNewHardcodedText -update",
			baselineFile)
	}
	if err != nil {
		t.Fatalf("讀取基準檔: %v", err)
	}
	var baseline map[string][]string
	if err := json.Unmarshal(raw, &baseline); err != nil {
		t.Fatalf("解析基準檔: %v", err)
	}
	return baseline
}

// displayPath 讓失敗訊息顯示相對於 web/ 的路徑，與基準檔的鍵一致。
func displayPath(absolute string) string {
	rel, err := filepath.Rel(filepath.Join("..", ".."), absolute)
	if err != nil {
		return filepath.ToSlash(absolute)
	}
	return filepath.ToSlash(rel)
}

// ---------------------------------------------------------------- 掃描器自我測試
//
// 下面三個案例都是實測中真的發生過的錯位。掃描器一旦又錯位，產出的是
// 「看起來合理」的假資料——不會讓任何測試失敗，只會讓 baseline 裡混滿垃圾，
// 所以必須用案例把住。

func TestJSUserFacingStringsSkipsTranslationFallbacks(t *testing.T) {
	src := `var a = t("xss.colName", "名称");` + "\n" +
		`var b = t('chat.retry', '重试');` + "\n" +
		`var c = assetT("assets.selectAsset", '选择资产');` + "\n" +
		`var d = c2t('c2.listing', '任务列表');` + "\n" +
		`var e = "真正的硬编中文";`
	got := jsUserFacingStrings(src)
	if len(got) != 1 || got[0] != `"真正的硬编中文"` {
		t.Errorf("只應留下非翻譯字串，得到 %q", got)
	}
}

func TestJSUserFacingStringsSurvivesQuoteInComment(t *testing.T) {
	// 註解裡的一個撇號曾讓掃描器一路配對到檔案結尾，產出一筆數萬字元的假字串。
	src := "// don't panic here\nvar x = '短';"
	got := jsUserFacingStrings(src)
	if len(got) != 1 || got[0] != `'短'` {
		t.Errorf("註解中的撇號不應影響後續解析，得到 %q", got)
	}
}

func TestJSUserFacingStringsSurvivesRegexLiteral(t *testing.T) {
	// /'/g 裡的引號同樣會讓掃描器錯位。
	src := "var s = a.replace(/'/g, '&#39;');\nvar y = '中文';"
	got := jsUserFacingStrings(src)
	if len(got) != 2 {
		t.Fatalf("應取得 2 個字串，得到 %q", got)
	}
	if got[1] != `'中文'` {
		t.Errorf("第二個字串應為 '中文'，得到 %q", got[1])
	}
}

func TestJSUserFacingStringsSurvivesNestedTemplate(t *testing.T) {
	// 巢狀模板的反引號曾讓外層模板一路吃到檔案結尾。
	src := "var h = `<div>${ok ? `<span>${v}</span>` : ''}加载中</div>`;\nvar z = '中文';"
	got := jsUserFacingStrings(src)
	for _, s := range got {
		if len(s) > 200 {
			t.Fatalf("出現不合理的長字串（%d 字元），掃描器又錯位了：%.80q", len(s), s)
		}
	}
	var sawLoad, sawCN bool
	for _, s := range got {
		if strings.Contains(s, "加载中") {
			sawLoad = true
		}
		if s == `'中文'` {
			sawCN = true
		}
	}
	if !sawLoad || !sawCN {
		t.Errorf("應同時取得模板靜態片段「加载中」與字串 '中文'，得到 %q", got)
	}
}

func TestHTMLVisibleTextSkipsTranslatedElements(t *testing.T) {
	src := `<h2 data-i18n="xss.pageTitle">收割验证</h2>` + "\n" +
		`<button data-i18n="common.refresh">刷新</button>` + "\n" +
		`<input placeholder="例：目标站登录页" data-i18n-attr="placeholder" data-i18n="xss.phName">` + "\n" +
		`<!-- 註解裡的中文不算 -->` + "\n" +
		`<p>没有 data-i18n 的中文</p>` + "\n" +
		`<p>未翻譯的 placeholder</p>` + "\n" +
		`<input placeholder="未翻译的提示">` + "\n" +
		`<script>var s = '脚本里的中文';</script>`
	got := htmlVisibleText(src)
	want := map[string]bool{
		"没有 data-i18n 的中文": true,
		"未翻譯的 placeholder": true,
		"未翻译的提示":           true,
	}
	if len(got) != len(want) {
		t.Fatalf("應只留下 %d 項，得到 %d 項：%q", len(want), len(got), got)
	}
	for _, s := range got {
		if !want[s] {
			t.Errorf("不該出現的項目：%q", s)
		}
	}
}

func TestIsConcatenated(t *testing.T) {
	// after 一律是「字面值結束之後」的偏移，也就是 regex 比對的結束位置。
	cases := []struct {
		literal string // 比對到的字面值
		rest    string // 它後面的原始碼
		want    bool
	}{
		{`'mcpMonitor.'`, ` + statusKey)`, true},
		{`'mcpMonitor.'`, `   +k)`, true},
		{`'theme.'`, `
 + key)`, true},
		{`'common.retry'`, `)`, false},
		{`'common.retry'`, `, '重试')`, false},
	}
	for _, c := range cases {
		src := c.literal + c.rest
		if got := isConcatenated(src, len(c.literal)); got != c.want {
			t.Errorf("isConcatenated(%q, %d) = %v，期望 %v", src, len(c.literal), got, c.want)
		}
	}
}
