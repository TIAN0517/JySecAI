package scope

import (
	"fmt"
	"net"
	"net/url"
	"os"
	"reflect"
	"strings"

	"jysecai/internal/config"
)

// 目標解析：把「工具呼叫」翻成「實際會碰到的主機清單」。
//
// 為什麼這一層不能簡化
// ------------------
// 授權判定要成立的前提是「我們知道這次會碰到誰」。但目標可能藏在三個地方（設計 §4）：
//  1. 工具的目標參數本身（positional / flag / template）。
//  2. additional_args 裡的檔案清單（`-l <file>`），一個檔可能上千筆。
//  3. stdin（httpx 的目標就是走 stdin）。
//
// 三個來源缺一不可，而且「找不到目標」不等於「沒有目標」——那要叫「任意執行」
// （arbitraryTargets=true），讓呼叫端去要求操作者逐次聲明，而不是默默放行。

// targetParamNames 是「看起來像目標參數」的參數名稱（fallback 啟發式）。
//
// 為什麼需要 fallback：config.ParameterConfig 目前還沒有 target 欄位
// （設計 §3 規劃由另一個改動補上），但工具 YAML 已經有近百支，
// 不能等欄位補齊才做授權。所以先用參數名稱判斷，欄位補上後會自動改用明確宣告。
var targetParamNames = map[string]struct{}{
	"target": {}, "targets": {}, "scan_target": {}, "scan_targets": {},
	"target_url": {}, "target_urls": {}, "target_host": {}, "target_hosts": {},
	"target_ip": {}, "target_ips": {}, "target_domain": {}, "target_domains": {},
	"url": {}, "urls": {}, "uri": {}, "uris": {}, "base_url": {}, "site_url": {},
	"host": {}, "hosts": {}, "hostname": {}, "hostnames": {},
	"domain": {}, "domains": {}, "dname": {}, "subdomain": {}, "subdomains": {},
	"ip": {}, "ips": {}, "ip_address": {}, "ip_addresses": {}, "address": {}, "addresses": {},
	"cidr": {}, "cidrs": {}, "network": {}, "networks": {},
	"endpoint": {}, "endpoints": {}, "server": {}, "servers": {},
	"site": {}, "sites": {}, "host_file": {}, "url_file": {}, "target_file": {},
}

// nonTargetParamNames 是「看起來像目標、其實不是」的參數名（沿用 executor 的特判名稱）。
var nonTargetParamNames = map[string]struct{}{
	"additional_args": {},
	"scan_type":       {},
	"action":          {},
}

// listFileFlags 是「後面接檔案清單」的旗標。
//
// 這些旗標後面的檔案必須讀進來展開，否則會漏掉上千個目標——
// 漏掉目標等於沒做授權檢查，是最危險的失效模式。
var listFileFlags = map[string]struct{}{
	"-l": {}, "--list": {}, "-list": {},
	"--list-file": {}, "-list-file": {},
	"--targets": {}, "-targets": {},
}

// maxListFileBytes 是清單檔的大小上限（避免讀到失控的檔案）。
const maxListFileBytes = 32 << 20 // 32 MiB

// maxListEntries 是清單檔展開後的筆數上限。
const maxListEntries = 200000

// NormalizeTarget 把原始目標字串正規化成 Target。
//
// 正規化規則：
//   - 帶 scheme 的字串 → URL 目標（Kind=url_prefix，保留正規化後的完整 URL）。
//   - 可解析的 CIDR → 網段目標（Kind=cidr）。
//   - 以 "*." 開頭 → wildcard 目標。
//   - 其餘 → 主機目標（可帶埠位）。
//
// 正規化的目的有兩個：讓比對不受大小寫／尾點／預設埠位影響，
// 以及讓拒絕記憶可以用同一把鍵（Target.Key()）。
func NormalizeTarget(raw string) Target {
	target := Target{Raw: strings.TrimSpace(raw)}
	value := target.Raw
	if value == "" {
		return target
	}

	// ① URL（含 scheme）。
	if strings.Contains(value, "://") {
		if parsed, err := url.Parse(value); err == nil && parsed.Host != "" {
			target.Kind = TargetURLPrefix
			target.Host = strings.ToLower(parsed.Hostname())
			target.Port = parsed.Port()
			target.URL = normalizeURL(parsed)
			return target
		}
	}

	// ② CIDR。
	if strings.Contains(value, "/") {
		if _, _, err := net.ParseCIDR(value); err == nil {
			target.Kind = TargetCIDR
			target.Host = strings.ToLower(value)
			return target
		}
	}

	// ③ wildcard。
	if strings.HasPrefix(value, "*.") {
		target.Kind = TargetWildcard
		target.Host = strings.ToLower(strings.TrimSuffix(value, "."))
		return target
	}

	// ④ 主機（可帶埠位）；沒有 scheme 但有路徑時取主機部分。
	hostPart := value
	if idx := strings.Index(hostPart, "/"); idx >= 0 {
		hostPart = hostPart[:idx]
	}
	host, port := splitHostPort(hostPart)
	target.Kind = TargetHost
	target.Host = host
	target.Port = port
	return target
}

// normalizeURL 正規化 URL：scheme／host 小寫、去掉預設埠位與 query/fragment。
func normalizeURL(parsed *url.URL) string {
	scheme := strings.ToLower(parsed.Scheme)
	host := strings.ToLower(parsed.Hostname())
	port := parsed.Port()
	if port != "" && !isDefaultPort(scheme, port) {
		host = net.JoinHostPort(host, port)
	}
	path := parsed.EscapedPath()
	if path == "" {
		path = "/"
	}
	return scheme + "://" + host + path
}

// isDefaultPort 判斷是否為該 scheme 的預設埠位。
func isDefaultPort(scheme, port string) bool {
	switch scheme {
	case "http":
		return port == "80"
	case "https":
		return port == "443"
	default:
		return false
	}
}

// splitHostPort 拆出主機與埠位（埠位必須是數字才當埠位）。
func splitHostPort(value string) (string, string) {
	value = strings.TrimSpace(value)
	if value == "" {
		return "", ""
	}
	if strings.HasPrefix(value, "[") {
		if host, port, err := net.SplitHostPort(value); err == nil {
			return strings.ToLower(host), port
		}
		return strings.ToLower(strings.Trim(value, "[]")), ""
	}
	if strings.Count(value, ":") == 1 {
		idx := strings.LastIndex(value, ":")
		host, port := value[:idx], value[idx+1:]
		if isNumericPort(port) {
			return strings.ToLower(strings.TrimSuffix(host, ".")), port
		}
	}
	return strings.ToLower(strings.TrimSuffix(value, ".")), ""
}

// isNumericPort 判斷字串是否為數字埠位。
func isNumericPort(value string) bool {
	if value == "" {
		return false
	}
	for _, c := range value {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

// scheme 回傳目標 URL 的 scheme（沒有 URL 就是空字串）。
func (t Target) scheme() string {
	if t.URL == "" {
		return ""
	}
	if idx := strings.Index(t.URL, "://"); idx > 0 {
		return strings.ToLower(t.URL[:idx])
	}
	return ""
}

// effectivePort 回傳目標的實際埠位。
//
// 沒有明確埠位時用 scheme 的預設埠位（http=80、https=443），
// 這樣 conditions.port=443 的授權才能涵蓋 https://example.com/ 這種寫法。
// 完全無法推斷時回傳空字串——「不知道埠位」不等於「任何埠位都對」。
func (t Target) effectivePort() string {
	if t.Port != "" {
		return t.Port
	}
	switch t.scheme() {
	case "http":
		return "80"
	case "https":
		return "443"
	default:
		return ""
	}
}

// ExtractTargets 從一次工具呼叫抽出實際會碰到的目標。
//
// toolName 是工具名稱（保留在簽名裡是為了錯誤訊息與日誌）。
// params／args 來自 internal/config 的 ToolConfig／ParameterConfig 結構。
// additionalArgs 是額外參數（已經切好的 token，或一整串空格分隔的字串都可以）。
// stdin 是工具的標準輸入內容（httpx 走這條路）。
//
// 回傳：
//   - targets：抽到的目標（去重、保持順序）。
//   - arbitrary：true 代表這是「任意執行類」工具——它沒有宣告目標參數、
//     沒有清單檔、也沒有 stdin，呼叫端必須要求操作者逐次聲明目標清單。
//     它絕對不能被當成「沒有目標」。
//   - err：檔案讀取失敗等錯誤（fail closed：寧可報錯也不要放行未檢查的目標）。
func ExtractTargets(toolName string, params []config.ParameterConfig, args map[string]any, additionalArgs []string, stdin string) ([]string, bool, error) {
	var targets []string
	seen := make(map[string]struct{})
	add := func(value string) {
		value = strings.TrimSpace(value)
		if value == "" {
			return
		}
		key := NormalizeTarget(value).Key()
		if key == "" {
			return
		}
		if _, ok := seen[key]; ok {
			return
		}
		seen[key] = struct{}{}
		targets = append(targets, value)
	}

	declaredTarget := false

	// ── 來源 1：目標參數本身 ─────────────────────────────────────────
	for _, param := range params {
		name := strings.ToLower(strings.TrimSpace(param.Name))
		if _, skip := nonTargetParamNames[name]; skip {
			continue
		}
		explicit, kind, _ := paramTargetInfo(param)
		// 明確宣告 target: true 優先；沒有宣告時用名稱啟發式補救。
		//
		// 為什麼 false 不算明確的「不是目標」：config.ParameterConfig.Target 是
		// bool 且 YAML 為 omitempty，false 同時代表「未宣告」與「宣告為 false」，
		// 兩者無法從值分辨。對安全閘來說，寧可多檢查一個目標（多問一次操作者），
		// 也不要漏檢。
		isTarget := explicit
		if !isTarget {
			_, isTarget = targetParamNames[name]
		}
		if !isTarget {
			continue
		}
		declaredTarget = true

		// 沒有進 argv 的參數（Position/Flag/Template 都沒有）不是目標來源。
		if !explicit && param.Position == nil && param.Flag == "" && param.Template == "" {
			continue
		}

		for _, value := range paramValues(args, param) {
			expanded, isFile, err := expandTargetValue(value, kind)
			if err != nil {
				return nil, false, fmt.Errorf("工具 %s 的目標參數 %s 解析失敗: %w", toolName, param.Name, err)
			}
			if isFile {
				for _, line := range expanded {
					add(line)
				}
				continue
			}
			for _, piece := range splitTargetList(value) {
				add(piece)
			}
		}
	}

	// ── 來源 2：additional_args 裡的清單檔 ────────────────────────────
	listFileFound := false
	tokens := splitArgTokens(additionalArgs)
	for i := 0; i < len(tokens); i++ {
		if _, ok := listFileFlags[tokens[i]]; !ok {
			continue
		}
		if i+1 >= len(tokens) {
			return nil, false, fmt.Errorf("工具 %s 的清單旗標 %s 缺少檔名", toolName, tokens[i])
		}
		path := tokens[i+1]
		lines, err := readTargetFile(path)
		if err != nil {
			return nil, false, fmt.Errorf("工具 %s 的清單檔 %s 讀取失敗: %w", toolName, path, err)
		}
		listFileFound = true
		for _, line := range lines {
			add(line)
		}
		i++
	}

	// ── 來源 3：stdin ────────────────────────────────────────────────
	stdinContent := stdin
	if strings.TrimSpace(stdinContent) == "" {
		stdinContent = stdinFromArgs(args)
	}
	hasStdin := strings.TrimSpace(stdinContent) != ""
	if hasStdin {
		for _, piece := range splitTargetList(stdinContent) {
			add(piece)
		}
	}

	// 沒有任何目標來源 → 任意執行類工具。
	arbitrary := !declaredTarget && !listFileFound && !hasStdin
	return targets, arbitrary, nil
}

// paramTargetInfo 讀取 ParameterConfig 上的 target 宣告。
//
// 用反射是為了在 config.ParameterConfig 還沒有 target 欄位時也能編譯；
// 欄位補上後（設計 §3）這裡會自動改用明確宣告，優先於名稱啟發式。
func paramTargetInfo(param config.ParameterConfig) (isTarget bool, kind string, hasExplicitField bool) {
	value := reflect.ValueOf(param)
	if field := value.FieldByName("Target"); field.IsValid() && field.Kind() == reflect.Bool {
		isTarget = field.Bool()
		hasExplicitField = true
	}
	if field := value.FieldByName("TargetKind"); field.IsValid() && field.Kind() == reflect.String {
		kind = strings.ToLower(strings.TrimSpace(field.String()))
	}
	return isTarget, kind, hasExplicitField
}

// paramValues 取出參數值（支援字串／字串陣列／任意型別）。
func paramValues(args map[string]any, param config.ParameterConfig) []string {
	if args == nil {
		return nil
	}
	raw, ok := args[param.Name]
	if !ok || raw == nil {
		return nil
	}
	switch value := raw.(type) {
	case string:
		if strings.TrimSpace(value) == "" {
			return nil
		}
		return []string{value}
	case []string:
		out := make([]string, 0, len(value))
		for _, item := range value {
			if strings.TrimSpace(item) != "" {
				out = append(out, item)
			}
		}
		return out
	case []any:
		out := make([]string, 0, len(value))
		for _, item := range value {
			text := fmt.Sprintf("%v", item)
			if strings.TrimSpace(text) != "" {
				out = append(out, text)
			}
		}
		return out
	case bool:
		return nil
	default:
		text := fmt.Sprintf("%v", raw)
		if strings.TrimSpace(text) == "" {
			return nil
		}
		return []string{text}
	}
}

// stdinFromArgs 從工具輸入 payload 取出 stdin 內容。
//
// 慣例的 key 是 "stdin" 或 "input"（httpx 這類把目標走 stdin 的工具）。
func stdinFromArgs(args map[string]any) string {
	if args == nil {
		return ""
	}
	for _, key := range []string{"stdin", "input", "stdin_data", "stdin_targets"} {
		raw, ok := args[key]
		if !ok || raw == nil {
			continue
		}
		switch value := raw.(type) {
		case string:
			if strings.TrimSpace(value) != "" {
				return value
			}
		case []string:
			if len(value) > 0 {
				return strings.Join(value, "\n")
			}
		case []any:
			if len(value) > 0 {
				parts := make([]string, 0, len(value))
				for _, item := range value {
					parts = append(parts, fmt.Sprintf("%v", item))
				}
				return strings.Join(parts, "\n")
			}
		}
	}
	return ""
}

// splitTargetList 把一段文字切成多個目標（逗號、空白、換行皆可分隔）。
//
// 與 tools/httpx.yaml 的包裝腳本行為一致（re.split(r"[,\s]+", ...)）。
func splitTargetList(value string) []string {
	fields := strings.FieldsFunc(value, func(r rune) bool {
		return r == ',' || r == ' ' || r == '\t' || r == '\n' || r == '\r' || r == ';' || r == '|'
	})
	out := make([]string, 0, len(fields))
	for _, field := range fields {
		if trimmed := strings.TrimSpace(field); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}

// splitArgTokens 把 additionalArgs 展開成 token 序列。
//
// 呼叫端可能已經切好（[]string{"-l", "/tmp/a.txt"}），也可能丟整串
// （[]string{"-l /tmp/a.txt -silent"}），兩種都支援；引號內的空白不會切開。
func splitArgTokens(additionalArgs []string) []string {
	var tokens []string
	for _, item := range additionalArgs {
		tokens = append(tokens, splitShellLike(item)...)
	}
	return tokens
}

// splitShellLike 以空白切分字串，但保留引號內容。
func splitShellLike(value string) []string {
	var (
		tokens  []string
		current strings.Builder
		quote   rune
		started bool
	)
	for _, r := range value {
		switch {
		case quote != 0:
			if r == quote {
				quote = 0
				continue
			}
			current.WriteRune(r)
		case r == '\'' || r == '"':
			quote = r
			started = true
		case r == ' ' || r == '\t' || r == '\n' || r == '\r':
			if started || current.Len() > 0 {
				tokens = append(tokens, current.String())
				current.Reset()
				started = false
			}
		default:
			current.WriteRune(r)
		}
	}
	if started || current.Len() > 0 {
		tokens = append(tokens, current.String())
	}
	return tokens
}

// expandTargetValue 判斷參數值是不是一個清單檔；是就讀檔展開。
//
// 為什麼連參數值也當成檔案處理：像 nuclei「目標寫在檔案裡」這類工具，
// 參數值本身就是檔名。不展開就會漏掉目標，漏掉目標＝沒做授權檢查。
func expandTargetValue(value, kind string) ([]string, bool, error) {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return nil, false, nil
	}
	if kind == "cidr" {
		return nil, false, nil
	}
	// 只有像路徑的字串才值得試著當檔案（避免把 "example.com" 拿去做 stat）。
	if !looksLikePath(trimmed) {
		return nil, false, nil
	}
	info, err := os.Stat(trimmed)
	if err != nil || info.IsDir() {
		return nil, false, nil
	}
	lines, err := readTargetFile(trimmed)
	if err != nil {
		return nil, false, err
	}
	return lines, true, nil
}

// looksLikePath 判斷字串看起來像檔案路徑。
func looksLikePath(value string) bool {
	if strings.ContainsAny(value, " \t") {
		return false
	}
	if strings.Contains(value, "/") || strings.Contains(value, "\\") {
		return true
	}
	return strings.Contains(value, ".")
}

// readTargetFile 讀清單檔並回傳非空、非註解的行。
func readTargetFile(path string) ([]string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}
	if info.IsDir() {
		return nil, fmt.Errorf("%s 是目錄，不是清單檔", path)
	}
	if info.Size() > maxListFileBytes {
		return nil, fmt.Errorf("清單檔 %s 超過大小上限（%d bytes）", path, maxListFileBytes)
	}
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(strings.ReplaceAll(string(content), "\r\n", "\n"), "\n")
	out := make([]string, 0, len(lines))
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		out = append(out, trimmed)
		if len(out) > maxListEntries {
			return nil, fmt.Errorf("清單檔 %s 的筆數超過上限（%d）", path, maxListEntries)
		}
	}
	return out, nil
}
