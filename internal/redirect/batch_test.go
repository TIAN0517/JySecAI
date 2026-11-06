package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// 批次受控跳轉驗證測試。

func TestVerifyTargetsConfirmsWhenLocationPointsToEndpoint(t *testing.T) {
	// 目標站在 url 參數被塞入受控端點時才會 302 過去。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("url") == "https://cb.example.com/land" {
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if !results[0].Confirmed {
		t.Fatalf("expected confirmed result, got %#v", results[0])
	}
	if results[0].Param != "url" {
		t.Fatalf("expected param url, got %q", results[0].Param)
	}
	if results[0].Status != http.StatusFound {
		t.Fatalf("expected status 302, got %d", results[0].Status)
	}
	if !strings.Contains(results[0].RequestURL, "url=") {
		t.Fatalf("request url should carry the injected param: %q", results[0].RequestURL)
	}
}

func TestVerifyTargetsDetectsNonDefaultParam(t *testing.T) {
	// 目標站用非預設參數名（例如 redirect_to），批次驗證要能自己找出來。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("redirect_to") == "https://cb.example.com/x" {
			w.Header().Set("Location", "https://cb.example.com/x")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/x"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if !results[0].Confirmed {
		t.Fatalf("expected confirmed result, got %#v", results[0])
	}
	if results[0].Param != "redirect_to" {
		t.Fatalf("expected param redirect_to, got %q", results[0].Param)
	}
}

func TestVerifyTargetsUsesSpecifiedParam(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("custom") == "https://cb.example.com/y" {
			w.Header().Set("Location", "https://cb.example.com/y")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/y"},
		Param:     "custom",
	})
	if err != nil {
		t.Fatal(err)
	}
	if !results[0].Confirmed || results[0].Param != "custom" {
		t.Fatalf("unexpected result %#v", results[0])
	}
}

func TestVerifyTargetsDeduplicatesAndKeepsOrder(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	targets := []string{
		server.URL + "/b",
		"  ",
		server.URL + "/a",
		server.URL + "/b",
	}
	results, err := VerifyTargets(context.Background(), server.Client(), targets, BatchOptions{
		Endpoints: []string{"https://cb.example.com/z"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d (%#v)", len(results), results)
	}
	if !strings.HasSuffix(results[0].URL, "/b") || !strings.HasSuffix(results[1].URL, "/a") {
		t.Fatalf("unexpected order: %#v", results)
	}
}

func TestVerifyTargetsReportsInvalidTargetWithoutStoppingBatch(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(),
		[]string{"ftp://example.com/x", server.URL + "/ok"}, BatchOptions{
			Endpoints: []string{"https://cb.example.com/z"},
		})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	if results[0].Error == "" {
		t.Fatal("invalid target must carry an error")
	}
	if results[0].Confirmed {
		t.Fatal("invalid target must not be confirmed")
	}
	if results[1].Error != "" {
		t.Fatalf("valid target must not carry an error: %q", results[1].Error)
	}
}

func TestVerifyTargetsRequiresEndpoint(t *testing.T) {
	if _, err := VerifyTargets(context.Background(), nil, []string{"https://example.com"}, BatchOptions{}); err == nil {
		t.Fatal("expected error when no endpoint is configured")
	}
}

func TestVerifyTargetsHonoursContextCancellation(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	results, err := VerifyTargets(ctx, server.Client(), []string{server.URL + "/a", server.URL + "/b"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/z"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	for _, result := range results {
		if result.Confirmed {
			t.Fatalf("cancelled run must not confirm anything: %#v", result)
		}
	}
}

func TestVerifyTargetsReportsUnreachableTarget(t *testing.T) {
	// 指向不存在的監聽埠，應該記錄錯誤而不是 panic 或中斷整批。
	results, err := VerifyTargets(context.Background(), &http.Client{Timeout: 2 * time.Second},
		[]string{"http://127.0.0.1:1/none"}, BatchOptions{
			Endpoints: []string{"https://cb.example.com/z"},
			Param:     "url",
		})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Error == "" {
		t.Fatal("unreachable target must carry an error")
	}
}

// TestVerifyTargetsThroughProxyConfirmsRedirect 驗證整條批次路徑都能走代理：
// 探測請求經代理送到目標站，目標站再 302 回受控端點才算命中。
// 批次與代理是本專案實際會一起用的組合，這裡把兩段串起來測。
func TestVerifyTargetsThroughProxyConfirmsRedirect(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("url") == "https://cb.example.com/land" {
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	proxyServer := startFakeSOCKS5(t)
	defer proxyServer.Close()

	client, err := NewProxyClient("socks5://127.0.0.1:"+proxyPort(t, proxyServer), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}

	results, err := VerifyTargets(context.Background(), client, []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/land"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if !results[0].Confirmed {
		t.Fatalf("expected confirmed result through proxy, got %#v", results[0])
	}
	if results[0].Status != http.StatusFound {
		t.Fatalf("expected status 302, got %d", results[0].Status)
	}
}

// TestVerifyTargetsReportsProxyFailurePerTarget 驗證代理失效時批次是 soft-fail：
// 壞掉的那一筆記錯誤，其餘目標照跑，不會整批中止。
func TestVerifyTargetsReportsProxyFailurePerTarget(t *testing.T) {
	// 代理指向不存在的監聽埠，連線必然失敗。
	client, err := NewProxyClient("socks5://127.0.0.1:1", 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}

	results, err := VerifyTargets(context.Background(), client, []string{"http://example.invalid/go"}, BatchOptions{
		Endpoints: []string{"https://cb.example.com/z"},
		Param:     "url",
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Confirmed {
		t.Fatalf("failed proxy must not confirm anything: %#v", results[0])
	}
	if results[0].Error == "" {
		t.Fatal("proxy failure must carry an error")
	}
}
