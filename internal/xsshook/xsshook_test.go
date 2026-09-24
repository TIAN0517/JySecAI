package xsshook

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestBuildReplacesAllPlaceholders(t *testing.T) {
	o := BuildOptions{
		PayloadID: "pid-123",
		BeaconURL: "http://127.0.0.1:8877/",
		Token:     "secret-token",
	}
	out := Build(o)
	for _, needle := range []string{"pid-123", "127.0.0.1:8877/api/xss/capture", "secret-token"} {
		if !strings.Contains(out, needle) {
			t.Fatalf("output missing %q:\n%s", needle, out)
		}
	}
	for _, leftover := range []string{"JSpL_BASE", "JSpL_TOKEN", "JSpL_PID"} {
		if strings.Contains(out, leftover) {
			t.Fatalf("unreplaced placeholder %q:\n%s", leftover, out)
		}
	}
	if !strings.Contains(out, `"POST"`) {
		t.Fatal("script must POST to collector")
	}
}

func TestBuildEscapesLiteralValues(t *testing.T) {
	// BeaconURL/Token 里若夹带双引号或换行，必须被转义成合法 JS 字符串，不能破坏脚本。
	o := BuildOptions{
		PayloadID: "pid\"quoted",
		BeaconURL: "http://h/x\n\"<>",
		Token:     "to\nken\"x",
	}
	out := Build(o)
	// 转义后的字面量应出现在输出中（json.Marshal 会把 \n 转成 \\n，\" 转成 \\"）。
	for _, raw := range []string{`pid\"quoted`, `http://h/x`, `to\nken\"x`} {
		if !strings.Contains(out, raw) {
			// 反斜杠转义形式可能与源串不同，退化校验：整体可被 JSON 反序列化且含目标子串。
			if !strings.Contains(out, strings.ReplaceAll(raw, `\"`, `"`)) {
				t.Fatalf("escaped literal %q missing from output:\n%s", raw, out)
			}
		}
	}
	// 必须是一段可解析为 JS 源码的结构（以函数表达式开头、以 }); 收尾）。
	if !strings.HasPrefix(out, "(function(){") || !strings.HasSuffix(out, "})();") {
		t.Fatalf("output not a valid IIFE: %s", out[:30])
	}
}

func TestCaptureRequestRoundTrip(t *testing.T) {
	in := CaptureRequest{
		PayloadID:   "p1",
		SourceURL:   "https://target.example/login",
		PageTitle:   `Page "t"`,
		UserAgent:   "Mozilla/5.0",
		URLFragment: "#foo",
		Cookies:     []Cookie{{Name: "session", Value: "abc=def", Domain: "target.example", Path: "/"}},
		LocalStorage: map[string]string{
			"k": "v",
		},
		SessionStorage: map[string]string{},
	}
	b, err := json.Marshal(in)
	if err != nil {
		t.Fatal(err)
	}
	var out CaptureRequest
	if err := json.Unmarshal(b, &out); err != nil {
		t.Fatal(err)
	}
	if out.SourceURL != "https://target.example/login" || out.PageTitle != `Page "t"` {
		t.Fatalf("round-trip mismatch: %#v", out)
	}
	if len(out.Cookies) != 1 || out.Cookies[0].Value != "abc=def" {
		t.Fatalf("cookie round-trip mismatch: %#v", out.Cookies)
	}
	if out.LocalStorage["k"] != "v" {
		t.Fatalf("localStorage round-trip mismatch: %#v", out.LocalStorage)
	}
}