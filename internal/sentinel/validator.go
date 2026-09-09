package sentinel

import (
	"net"
	"regexp"
	"strconv"
	"strings"
)

var (
	ErrEmptyTarget   = "请输入二级域名或 IP"
	ErrPrivateTarget = "不支持内网或回环地址，请输入公网 IP 或二级域名"
	ErrInvalidTarget = "输入不正确，请重新输入二级域名或 IP"

	labelRegex = regexp.MustCompile(`^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$`)
	tldRegex   = regexp.MustCompile(`^(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})$`)

	// multiPartTLDs 常見複合後綴（二級頂級域）集合
	multiPartTLDs = map[string]struct{}{
		"com.cn": {}, "net.cn": {}, "org.cn": {}, "gov.cn": {}, "edu.cn": {}, "ac.cn": {}, "mil.cn": {},
		"co.uk": {}, "org.uk": {}, "ac.uk": {}, "gov.uk": {}, "me.uk": {}, "net.uk": {},
		"com.hk": {}, "org.hk": {}, "edu.hk": {}, "gov.hk": {}, "net.hk": {}, "idv.hk": {},
		"com.tw": {}, "org.tw": {}, "edu.tw": {}, "gov.tw": {}, "net.tw": {}, "idv.tw": {},
		"co.jp": {}, "or.jp": {}, "ne.jp": {}, "ac.jp": {}, "go.jp": {}, "gr.jp": {},
		"com.au": {}, "net.au": {}, "org.au": {}, "edu.au": {}, "gov.au": {},
		"co.kr": {}, "or.kr": {}, "ac.kr": {}, "go.kr": {}, "ne.kr": {},
		"com.sg": {}, "net.sg": {}, "org.sg": {}, "edu.sg": {}, "gov.sg": {},
		"com.my": {}, "net.my": {}, "org.my": {}, "edu.my": {}, "gov.my": {},
		"co.nz": {}, "net.nz": {}, "org.nz": {}, "ac.nz": {}, "govt.nz": {},
		"co.id": {}, "or.id": {}, "ac.id": {}, "go.id": {},
		"com.br": {}, "net.br": {}, "org.br": {},
		"co.in": {}, "net.in": {}, "org.in": {},
		"com.mx": {}, "co.za": {}, "org.za": {}, "com.ar": {},
		"co.il": {}, "org.il": {}, "ac.il": {}, "gov.il": {},
		"com.ph": {}, "com.pk": {}, "com.tr": {}, "com.vn": {},
		"co.th": {}, "ac.th": {}, "com.sa": {}, "com.ua": {},
	}
)

type ValidationResult struct {
	OK     bool
	Target string
	Kind   string // "ipv4" | "domain"
	Error  string
}

// ValidateTarget 驗證用戶輸入目標是否為合法的二級域名或公網 IPv4
func ValidateTarget(input string) ValidationResult {
	t := strings.TrimSpace(input)
	if t == "" {
		return ValidationResult{OK: false, Error: ErrEmptyTarget}
	}

	// 檢查是否為 IPv4
	if isIPv4(t) {
		if isPrivateOrReservedIPv4(t) {
			return ValidationResult{OK: false, Error: ErrPrivateTarget}
		}
		return ValidationResult{OK: true, Target: t, Kind: "ipv4"}
	}

	// 檢查是否為 IPv6 或帶括號等非法格式
	if strings.Contains(t, ":") || strings.Contains(t, "%") || strings.Contains(t, "/") || strings.Contains(t, " ") {
		return ValidationResult{OK: false, Error: ErrInvalidTarget}
	}

	lower := strings.ToLower(t)
	if strings.HasPrefix(lower, ".") || strings.HasSuffix(lower, ".") || strings.Contains(lower, "..") {
		return ValidationResult{OK: false, Error: ErrInvalidTarget}
	}
	if isAllNumericLabels(lower) {
		return ValidationResult{OK: false, Error: ErrInvalidTarget}
	}
	if isBlockedDomain(lower) {
		return ValidationResult{OK: false, Error: ErrPrivateTarget}
	}

	if !isValidSecondLevelDomain(lower) {
		return ValidationResult{OK: false, Error: ErrInvalidTarget}
	}

	return ValidationResult{OK: true, Target: lower, Kind: "domain"}
}

func isIPv4(s string) bool {
	parts := strings.Split(s, ".")
	if len(parts) != 4 {
		return false
	}
	for _, p := range parts {
		if len(p) == 0 || len(p) > 3 {
			return false
		}
		if len(p) > 1 && p[0] == '0' {
			return false
		}
		n, err := strconv.Atoi(p)
		if err != nil || n < 0 || n > 255 {
			return false
		}
	}
	return true
}

func isPrivateOrReservedIPv4(ipStr string) bool {
	ip := net.ParseIP(ipStr)
	if ip == nil {
		return true
	}
	v4 := ip.To4()
	if v4 == nil {
		return true
	}

	b0, b1 := v4[0], v4[1]
	// 0.0.0.0/8
	if b0 == 0 {
		return true
	}
	// 10.0.0.0/8
	if b0 == 10 {
		return true
	}
	// 127.0.0.0/8
	if b0 == 127 {
		return true
	}
	// 169.254.0.0/16
	if b0 == 169 && b1 == 254 {
		return true
	}
	// 192.168.0.0/16
	if b0 == 192 && b1 == 168 {
		return true
	}
	// 172.16.0.0/12
	if b0 == 172 && b1 >= 16 && b1 <= 31 {
		return true
	}
	// 100.64.0.0/10 (CGNAT)
	if b0 == 100 && b1 >= 64 && b1 <= 127 {
		return true
	}
	// 224.0.0.0+ (Multicast & Broadcast)
	if b0 >= 224 {
		return true
	}
	return false
}

func isBlockedDomain(domain string) bool {
	return domain == "localhost" ||
		strings.HasSuffix(domain, ".localhost") ||
		strings.HasSuffix(domain, ".local") ||
		strings.HasSuffix(domain, ".internal") ||
		strings.HasSuffix(domain, ".lan") ||
		strings.HasSuffix(domain, ".invalid")
}

func isAllNumericLabels(domain string) bool {
	parts := strings.Split(domain, ".")
	for _, p := range parts {
		if _, err := strconv.Atoi(p); err != nil {
			return false
		}
	}
	return true
}

func isValidSecondLevelDomain(domain string) bool {
	if len(domain) > 253 {
		return false
	}
	parts := strings.Split(domain, ".")
	for _, p := range parts {
		if !labelRegex.MatchString(p) {
			return false
		}
	}

	// 情況一：如 example.com (2 段)
	if len(parts) == 2 {
		if _, isMulti := multiPartTLDs[domain]; isMulti {
			return false
		}
		return tldRegex.MatchString(parts[1])
	}

	// 情況二：如 example.com.cn (3 段，後兩段為複合 TLD)
	if len(parts) == 3 {
		suffix := parts[1] + "." + parts[2]
		_, isMulti := multiPartTLDs[suffix]
		return isMulti
	}

	return false
}
