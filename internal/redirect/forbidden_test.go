package redirect

import (
	"context"
	"errors"
	"net/http"
	"strings"
	"testing"
)

// blockingTransport 攔截所有請求。
//
// 這支測試的目標是「禁區資產一個封包都不能出去」；用攔截式 Transport 當第二道保險：
// 就算守門哪天被改壞，測試也不會真的打到消防／EPCR 系統，只會看到 calls > 0 而失敗。
type blockingTransport struct {
	calls int
}

func (t *blockingTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	t.calls++
	return nil, errors.New("blocked by test transport")
}

// TestVerifyTargetsSkipsForbiddenTargets 禁區目標不得被探測。
func TestVerifyTargetsSkipsForbiddenTargets(t *testing.T) {
	transport := &blockingTransport{}
	client := &http.Client{Transport: transport}

	// 這三個都在 all/tools/forbidden_scope.py 的禁區清單裡：
	//   epcr.tpf.gov.tw  → 網域層（EPCR）
	//   123.252.43.71    → IP 層（高雄市消防局高桂分隊）
	//   223.200.7.74     → IP 層（消防署 tyfdapp 推播目標）
	forbiddenTargets := []string{
		"https://epcr.tpf.gov.tw:4004/login?url=x",
		"http://123.252.43.71/",
		"http://223.200.7.74/",
	}

	results, err := VerifyTargets(context.Background(), client, forbiddenTargets, BatchOptions{
		Endpoints: []string{"https://97y.me/hjnej"},
		Param:     "url",
	})
	if err != nil {
		t.Fatalf("VerifyTargets() error = %v", err)
	}
	if len(results) != len(forbiddenTargets) {
		t.Fatalf("results = %d, want %d", len(results), len(forbiddenTargets))
	}
	for _, result := range results {
		if result.Confirmed {
			t.Fatalf("forbidden target %q must not be confirmed", result.URL)
		}
		if result.RequestURL != "" {
			t.Fatalf("forbidden target %q was probed: %q", result.URL, result.RequestURL)
		}
		if !strings.Contains(result.Error, "禁区") {
			t.Fatalf("forbidden target %q error = %q, want a forbidden-scope reason", result.URL, result.Error)
		}
	}
	if transport.calls != 0 {
		t.Fatalf("forbidden targets caused %d outbound requests, want 0", transport.calls)
	}
}

// TestVerifyTargetsStillProbesAllowedTargets 允許的目標照常探測（守門不能把功能打死）。
func TestVerifyTargetsStillProbesAllowedTargets(t *testing.T) {
	transport := &blockingTransport{}
	client := &http.Client{Transport: transport}

	results, err := VerifyTargets(context.Background(), client, []string{"https://www.sps-tw.com.tw/account/login/auth/"}, BatchOptions{
		Endpoints: []string{"https://97y.me/hjnej"},
		Param:     "redirect",
	})
	if err != nil {
		t.Fatalf("VerifyTargets() error = %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("results = %d, want 1", len(results))
	}
	if transport.calls != 1 {
		t.Fatalf("allowed target caused %d outbound requests, want 1", transport.calls)
	}
	if results[0].RequestURL == "" {
		t.Fatalf("allowed target was not probed: %#v", results[0])
	}
}
