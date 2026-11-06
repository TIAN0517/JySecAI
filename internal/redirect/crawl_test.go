package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// 自動巡站（發掘跳轉參數）測試。

func TestDiscoverRedirectCandidatesFindsRedirectLinks(t *testing.T) {
	var mux *http.ServeMux
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/":
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`<html><body>
				<a href="/go?url=/next">go</a>
				<a href="/plain">plain</a>
				<a href="https://other.example/go?redirect=https://evil.example">offsite</a>
				<a href="mailto:a@b.example">mail</a>
				<form action="/login?next=%2Fhome"><input name="q"></form>
			</body></html>`))
		case "/go":
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`<html><body><a href="/deep?goto=1">deep</a></body></html>`))
		default:
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`<html><body>ok</body></html>`))
		}
	}))
	defer server.Close()
	mux = nil
	_ = mux

	result := DiscoverRedirectCandidates(context.Background(), server.Client(), []string{server.URL + "/"}, CrawlOptions{
		SameHostOnly: true,
		MaxPages:     10,
		MaxDepth:     1,
	})
	if len(result.Candidates) == 0 {
		t.Fatal("expected redirect candidates")
	}
	joined := strings.Join(result.Candidates, "\n")
	if !strings.Contains(joined, "url=") {
		t.Fatalf("expected url param candidate, got:\n%s", joined)
	}
	if !strings.Contains(joined, "next=") {
		t.Fatalf("expected next param candidate, got:\n%s", joined)
	}
	// 同主機限制：不該把站外的連結算進來。
	if strings.Contains(joined, "other.example") {
		t.Fatalf("same-host filter leaked an offsite link:\n%s", joined)
	}
	// 非跳轉參數的連結不該被當成候選。
	if strings.Contains(joined, "/plain") {
		t.Fatalf("plain link must not be a candidate:\n%s", joined)
	}
}

func TestDiscoverRedirectCandidatesRespectsPageLimit(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		_, _ = w.Write([]byte(`<html><body>
			<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
		</body></html>`))
	}))
	defer server.Close()

	result := DiscoverRedirectCandidates(context.Background(), server.Client(), []string{server.URL + "/"}, CrawlOptions{
		SameHostOnly: true,
		MaxPages:     1,
		MaxDepth:     2,
	})
	if result.PagesVisited > 1 {
		t.Fatalf("page limit exceeded: visited %d", result.PagesVisited)
	}
}

func TestDiscoverRedirectCandidatesIgnoresInvalidSeeds(t *testing.T) {
	result := DiscoverRedirectCandidates(context.Background(), nil, []string{"", "ftp://example.com", "not a url"}, CrawlOptions{})
	if result.PagesVisited != 0 || len(result.Candidates) != 0 {
		t.Fatalf("invalid seeds must be ignored: %#v", result)
	}
}

func TestIsRedirectParam(t *testing.T) {
	for _, name := range []string{"url", "URL", "redirect", "next", "returnUrl", "goto"} {
		if !IsRedirectParam(name) {
			t.Fatalf("%q should be a redirect param", name)
		}
	}
	for _, name := range []string{"", "q", "id", "page"} {
		if IsRedirectParam(name) {
			t.Fatalf("%q should not be a redirect param", name)
		}
	}
}
