package redirect

import (
	"net/url"
	"regexp"
	"strings"
)

// scanHTTPURLRe 從掃描訊息裡抽出 http(s) 目標。
var scanHTTPURLRe = regexp.MustCompile(`https?://[^\s<>"'\\]+`)

const maxScanAttachedSeeds = 32

// ExtractHTTPURLs 從一段掃描訊息抽出 http/https 目標，去掉尾隨標點並去重。
func ExtractHTTPURLs(text string) []string {
	raw := scanHTTPURLRe.FindAllString(text, -1)
	if len(raw) == 0 {
		return nil
	}
	seen := make(map[string]struct{}, len(raw))
	out := make([]string, 0, len(raw))
	for _, item := range raw {
		cleaned := strings.TrimRight(item, ".,;:!?)]}'\"")
		if cut := strings.IndexAny(cleaned, "。，、；：！？）】」』》"); cut >= 0 {
			cleaned = cleaned[:cut]
		}
		cleaned = strings.TrimRight(cleaned, ".,;:!?)]}'\"")
		parsed, err := url.Parse(cleaned)
		if err != nil {
			continue
		}
		scheme := strings.ToLower(parsed.Scheme)
		if scheme != "http" && scheme != "https" {
			continue
		}
		if strings.TrimSpace(parsed.Host) == "" {
			continue
		}
		if _, ok := seen[cleaned]; ok {
			continue
		}
		seen[cleaned] = struct{}{}
		out = append(out, cleaned)
		if len(out) >= maxScanAttachedSeeds {
			break
		}
	}
	return out
}

// FilterOwnCallbackURLs 丟掉指向受控回連主機的 URL，避免拿短鏈自己當掃描目標。
func FilterOwnCallbackURLs(seeds []string, endpointHosts []string) []string {
	if len(seeds) == 0 {
		return nil
	}
	own := make(map[string]struct{}, len(endpointHosts))
	for _, host := range endpointHosts {
		h := strings.ToLower(strings.TrimSpace(host))
		if h != "" {
			own[h] = struct{}{}
		}
	}
	out := make([]string, 0, len(seeds))
	for _, seed := range seeds {
		host := strings.ToLower(strings.TrimSpace(EndpointHost(seed)))
		if host != "" {
			if _, skip := own[host]; skip {
				continue
			}
		}
		out = append(out, seed)
	}
	return out
}
