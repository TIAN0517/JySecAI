package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestNormalizeURLsDropsInvalidAndDeduplicates(t *testing.T) {
	raw := []string{
		"  https://97y.me/tjneJ  ",
		"",
		"https://97y.me/tjneK",
		"https://97y.me/tjneJ", // 重複
		"ftp://97y.me/tjneL",   // 非 http/https
		"97y.me/tjneM",         // 沒有 scheme
		"https://",             // 沒有主機
		"   ",
		"http://97y.me/tjneN",
	}

	got := NormalizeURLs(raw)
	want := []string{"https://97y.me/tjneJ", "https://97y.me/tjneK", "http://97y.me/tjneN"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("NormalizeURLs() = %#v, want %#v", got, want)
	}
}

func TestNormalizeURLsIsDeterministic(t *testing.T) {
	raw := []string{
		"https://a.example/1",
		"https://b.example/2",
		"https://a.example/1",
		"https://c.example/3",
		"https://b.example/2",
	}
	first := NormalizeURLs(raw)
	for i := 0; i < 20; i++ {
		got := NormalizeURLs(raw)
		if !reflect.DeepEqual(got, first) {
			t.Fatalf("NormalizeURLs() is not deterministic: %#v vs %#v", got, first)
		}
	}
	want := []string{"https://a.example/1", "https://b.example/2", "https://c.example/3"}
	if !reflect.DeepEqual(first, want) {
		t.Fatalf("NormalizeURLs() = %#v, want %#v", first, want)
	}
}

func TestNormalizeURLsEmptyInput(t *testing.T) {
	if got := NormalizeURLs(nil); got != nil {
		t.Fatalf("NormalizeURLs(nil) = %#v, want nil", got)
	}
	if got := NormalizeURLs([]string{"", "   "}); got != nil {
		t.Fatalf("NormalizeURLs(blank) = %#v, want nil", got)
	}
}

func TestDetectRedirectParamsIsFixedOrder(t *testing.T) {
	got := DetectRedirectParams("https://victim.example/login")
	if len(got) != len(defaultRedirectParams) {
		t.Fatalf("DetectRedirectParams() returned %d params, want %d", len(got), len(defaultRedirectParams))
	}
	if got[0] != "url" || got[1] != "redirect" {
		t.Fatalf("DetectRedirectParams() head = %#v, want url,redirect", got[:2])
	}
	for i := 1; i < len(got); i++ {
		if got[i] == got[i-1] {
			t.Fatalf("DetectRedirectParams() contains duplicate %q", got[i])
		}
	}
}

func TestDetectRedirectParamsPrefersExistingQueryParams(t *testing.T) {
	got := DetectRedirectParams("https://victim.example/go?next=/home&url=/x")
	if len(got) < 2 {
		t.Fatalf("DetectRedirectParams() = %#v, want at least 2 entries", got)
	}
	if got[0] != "next" && got[0] != "url" {
		t.Fatalf("DetectRedirectParams() head = %q, want an existing query param first", got[0])
	}
	// 既有參數必須排在同順序的其他參數之前。
	for _, name := range []string{"next", "url"} {
		idx := indexOf(got, name)
		if idx < 0 {
			t.Fatalf("DetectRedirectParams() lost %q: %#v", name, got)
		}
		for _, other := range []string{"redirect_uri", "goto", "u"} {
			if otherIdx := indexOf(got, other); otherIdx >= 0 && otherIdx < idx {
				t.Fatalf("DetectRedirectParams() put %q before existing param %q: %#v", other, name, got)
			}
		}
	}
}

func indexOf(list []string, want string) int {
	for i, v := range list {
		if v == want {
			return i
		}
	}
	return -1
}

func TestBuildProbeURL(t *testing.T) {
	cases := []struct {
		name    string
		target  string
		param   string
		payload string
		want    string
	}{
		{
			name:    "目标没有 query",
			target:  "https://victim.example/login",
			param:   "next",
			payload: "https://evil.example/steal",
			want:    "https://victim.example/login?next=https%3A%2F%2Fevil.example%2Fsteal",
		},
		{
			name:    "目标已有其他 query",
			target:  "https://victim.example/login?lang=zh",
			param:   "next",
			payload: "https://evil.example/steal",
			want:    "https://victim.example/login?lang=zh&next=https%3A%2F%2Fevil.example%2Fsteal",
		},
		{
			name:    "目标已有同名参数时改写",
			target:  "https://victim.example/login?next=/home&lang=zh",
			param:   "next",
			payload: "https://evil.example/steal",
			want:    "https://victim.example/login?lang=zh&next=https%3A%2F%2Fevil.example%2Fsteal",
		},
		{
			name:    "保留 fragment",
			target:  "https://victim.example/login?lang=zh#section",
			param:   "next",
			payload: "https://evil.example/steal",
			want:    "https://victim.example/login?lang=zh&next=https%3A%2F%2Fevil.example%2Fsteal#section",
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := BuildProbeURL(tc.target, tc.param, tc.payload)
			if err != nil {
				t.Fatalf("BuildProbeURL() error = %v", err)
			}
			if got != tc.want {
				t.Fatalf("BuildProbeURL() = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestBuildProbeURLRejectsMalformedTarget(t *testing.T) {
	bad := []struct {
		name   string
		target string
		param  string
	}{
		{"空目标", "   ", "next"},
		{"没有 scheme", "victim.example/login", "next"},
		{"不支援的 scheme", "ftp://victim.example/login", "next"},
		{"解析失败", "://victim.example", "next"},
		{"缺少主机名", "https://", "next"},
		{"参数名为空", "https://victim.example/", "  "},
	}
	for _, tc := range bad {
		t.Run(tc.name, func(t *testing.T) {
			got, err := BuildProbeURL(tc.target, tc.param, "https://evil.example/steal")
			if err == nil {
				t.Fatalf("BuildProbeURL(%q) = %q, want error", tc.target, got)
			}
			if got != "" {
				t.Fatalf("BuildProbeURL(%q) returned %q alongside error", tc.target, got)
			}
		})
	}
}

func TestIsReflected(t *testing.T) {
	cases := []struct {
		name     string
		location string
		payload  string
		want     bool
	}{
		{
			name:     "绝对 URL 命中",
			location: "https://evil.example/steal",
			payload:  "https://evil.example/steal",
			want:     true,
		},
		{
			name:     "payload 是 protocol-relative",
			location: "https://evil.example/steal",
			payload:  "//evil.example/steal",
			want:     true,
		},
		{
			name:     "location 是 protocol-relative",
			location: "//evil.example/steal",
			payload:  "https://evil.example/steal",
			want:     true,
		},
		{
			name:     "带 userinfo 仍算命中",
			location: "https://user@evil.example/steal",
			payload:  "https://evil.example/steal",
			want:     true,
		},
		{
			name:     "后缀相似的主机不算命中",
			location: "https://victim.com.evil.example/steal",
			payload:  "https://evil.example/steal",
			want:     false,
		},
		{
			name:     "受害者自己的主机不算命中",
			location: "https://victim.example/home",
			payload:  "https://evil.example/steal",
			want:     false,
		},
		{
			name:     "空 Location 不算命中",
			location: "",
			payload:  "https://evil.example/steal",
			want:     false,
		},
		{
			name:     "大小写差异仍算命中",
			location: "https://EVIL.example/steal",
			payload:  "https://evil.example/steal",
			want:     true,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := IsReflected(tc.location, tc.payload); got != tc.want {
				t.Fatalf("IsReflected(%q, %q) = %v, want %v", tc.location, tc.payload, got, tc.want)
			}
		})
	}
}

func TestExtractLocationIsCaseInsensitive(t *testing.T) {
	header := http.Header{}
	header.Set("Location", "https://evil.example/steal")
	if got := ExtractLocation(header); got != "https://evil.example/steal" {
		t.Fatalf("ExtractLocation() = %q", got)
	}

	raw := http.Header{"location": []string{"https://evil.example/steal"}}
	if got := ExtractLocation(raw); got != "https://evil.example/steal" {
		t.Fatalf("ExtractLocation(lowercase key) = %q", got)
	}

	if got := ExtractLocation(nil); got != "" {
		t.Fatalf("ExtractLocation(nil) = %q, want empty", got)
	}
}

func TestProbeCapturesLocationWithoutFollowingRedirect(t *testing.T) {
	var finalHits int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/final":
			atomic.AddInt32(&finalHits, 1)
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("should not be reached"))
		default:
			w.Header().Set("Location", "https://evil.example/steal")
			w.WriteHeader(http.StatusFound)
		}
	}))
	defer server.Close()

	client := &http.Client{Timeout: 5 * time.Second}
	result := Probe(context.Background(), client, server.URL+"/go", "next", "https://evil.example/steal")

	if result.Error != "" {
		t.Fatalf("Probe() error = %q", result.Error)
	}
	if result.Status != http.StatusFound {
		t.Fatalf("Probe() status = %d, want %d", result.Status, http.StatusFound)
	}
	if result.Location != "https://evil.example/steal" {
		t.Fatalf("Probe() location = %q", result.Location)
	}
	if !result.Reflected {
		t.Fatal("Probe() did not mark the payload as reflected")
	}
	if result.Param != "next" {
		t.Fatalf("Probe() param = %q", result.Param)
	}
	if !strings.Contains(result.RequestURL, "next=") {
		t.Fatalf("Probe() request url = %q, want the payload in the query", result.RequestURL)
	}
	if hits := atomic.LoadInt32(&finalHits); hits != 0 {
		t.Fatalf("Probe() followed the redirect (%d hits on /final)", hits)
	}
}

func TestProbeReportsErrorInsteadOfPanicking(t *testing.T) {
	result := Probe(context.Background(), nil, "://bad-url", "next", "https://evil.example/steal")
	if result.Error == "" {
		t.Fatal("Probe() did not report the malformed target")
	}
	if result.Status != 0 {
		t.Fatalf("Probe() status = %d, want 0", result.Status)
	}
}

func TestProbeCapturesNetworkError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	url := server.URL
	server.Close()

	result := Probe(context.Background(), &http.Client{Timeout: 2 * time.Second}, url+"/go", "next", "https://evil.example/steal")
	if result.Error == "" {
		t.Fatal("Probe() did not report the network error")
	}
	if result.Reflected {
		t.Fatal("Probe() reported a reflection for a failed request")
	}
}
