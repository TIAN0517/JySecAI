package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

// 巡站死鎖與重複抓取的回歸測試。
//
// 背景：舊版 crawlSeed 讓每個 worker 都跑完整個 jobs 清單，並把結果塞進一個
// 容量只有 len(jobs) 的 channel，但送出總數是 workers×len(jobs)，消費者又要等
// wg.Wait() 之後才開始讀 —— workers≥2 且 jobs≥2 時必然死鎖，整個巡站永久卡住。
//
// 舊版的單元測試湊巧只有 1 個非同主機連結（jobs=1 → workers=1 → 剛好不會死鎖），
// 所以沒抓到。這裡用 2 個以上的普通連結把條件補齊。

func TestDiscoverRedirectCandidatesDoesNotDeadlockWithMultipleLinks(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		switch r.URL.Path {
		case "/":
			// 三個普通連結 → depth 1 的 jobs = 3 → workers = 2（預設併發）。
			_, _ = w.Write([]byte(`<html><body>
				<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
				<a href="/go?url=/next">go</a>
			</body></html>`))
		default:
			_, _ = w.Write([]byte(`<html><body>ok</body></html>`))
		}
	}))
	defer server.Close()

	done := make(chan CrawlResult, 1)
	go func() {
		done <- DiscoverRedirectCandidates(context.Background(), server.Client(), []string{server.URL + "/"}, CrawlOptions{
			SameHostOnly: true,
			MaxPages:     20,
			MaxDepth:     1,
			Concurrency:  2,
			Timeout:      5 * time.Second,
		})
	}()

	select {
	case result := <-done:
		if result.PagesVisited < 2 {
			t.Fatalf("expected to visit more than the seed page, got %d", result.PagesVisited)
		}
		joined := strings.Join(result.Candidates, "\n")
		if !strings.Contains(joined, "url=") {
			t.Fatalf("expected the redirect candidate to be found, got:\n%s", joined)
		}
	case <-time.After(20 * time.Second):
		t.Fatal("DiscoverRedirectCandidates deadlocked: page with multiple links must not hang")
	}
}

func TestDiscoverRedirectCandidatesFetchesEachPageOnce(t *testing.T) {
	var mu sync.Mutex
	counts := map[string]int{}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		counts[r.URL.Path]++
		mu.Unlock()
		w.Header().Set("Content-Type", "text/html")
		switch r.URL.Path {
		case "/":
			_, _ = w.Write([]byte(`<html><body>
				<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>
			</body></html>`))
		default:
			_, _ = w.Write([]byte(`<html><body>ok</body></html>`))
		}
	}))
	defer server.Close()

	result := DiscoverRedirectCandidates(context.Background(), server.Client(), []string{server.URL + "/"}, CrawlOptions{
		SameHostOnly: true,
		MaxPages:     20,
		MaxDepth:     1,
		Concurrency:  2,
		Timeout:      5 * time.Second,
	})

	mu.Lock()
	defer mu.Unlock()
	for path, count := range counts {
		if count > 1 {
			t.Fatalf("page %s fetched %d times; each page must be fetched exactly once", path, count)
		}
	}
	if len(counts) != 4 {
		t.Fatalf("expected 4 distinct pages to be fetched, got %d (%v)", len(counts), counts)
	}
	if result.PagesVisited != 4 {
		t.Fatalf("expected 4 pages visited, got %d", result.PagesVisited)
	}
}

func TestDiscoverRedirectCandidatesFindsSiteOwnRedirectMethod(t *testing.T) {
	// 站點本來的跳轉入口：/redirect?next=/home —— 巡站必須把它找出來，
	// 因為後續驗證會把 next 的值換成受控端點（這是「自動植入」的對象）。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		if r.URL.Path == "/" {
			_, _ = w.Write([]byte(`<html><body><a href="/redirect?next=/home">continue</a></body></html>`))
			return
		}
		_, _ = w.Write([]byte(`<html><body>ok</body></html>`))
	}))
	defer server.Close()

	result := DiscoverRedirectCandidates(context.Background(), server.Client(), []string{server.URL + "/"}, CrawlOptions{
		SameHostOnly: true,
		MaxPages:     5,
		MaxDepth:     0,
		Timeout:      5 * time.Second,
	})
	if len(result.Candidates) != 1 {
		t.Fatalf("expected 1 candidate, got %d (%v)", len(result.Candidates), result.Candidates)
	}
	if !strings.Contains(result.Candidates[0], "next=/home") {
		t.Fatalf("candidate should keep the site's own redirect param, got %q", result.Candidates[0])
	}
}
