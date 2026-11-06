package redirect

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

// 證據分級與精準度指標的行為測試。
//
// 核心語意：
//   - location：伺服器真的 3xx 跳轉到受控端點 → 強證據，confirmed = true。
//   - body_echo：只是把受控端點回顯在本文裡 → 弱證據，confirmed 必須是 false
//     （這是粗略掃描器最常見的偽陽性來源）。
//   - 重複複測：命中一次可能是巧合，全部一致才算穩。

func TestProbeClassifiesLocationAsStrongEvidence(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "https://97y.me/tjneJ/landing", http.StatusFound)
	}))
	defer server.Close()

	probe := Probe(context.Background(), server.Client(), server.URL+"/go", "url", "https://97y.me/tjneJ")
	if !probe.Reflected {
		t.Fatalf("expected the Location header to be reflected, got %+v", probe)
	}
	if probe.Evidence != EvidenceLocation {
		t.Fatalf("expected evidence %q, got %q", EvidenceLocation, probe.Evidence)
	}
	if probe.BodyEcho {
		t.Fatal("a real redirect must not be flagged as body echo")
	}
}

func TestProbeClassifiesBodyEchoAsWeakEvidence(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		// 只回顯參數值，沒有任何 3xx —— 這是偽陽性的典型來源。
		_, _ = w.Write([]byte(`<html><body>you were sent to: ` + r.URL.Query().Get("url") + `</body></html>`))
	}))
	defer server.Close()

	probe := Probe(context.Background(), server.Client(), server.URL+"/go", "url", "https://97y.me/tjneJ")
	if probe.Reflected {
		t.Fatalf("body echo must not count as a redirect: %+v", probe)
	}
	if probe.Evidence != EvidenceBodyEcho {
		t.Fatalf("expected evidence %q, got %q", EvidenceBodyEcho, probe.Evidence)
	}
	if !probe.BodyEcho {
		t.Fatal("expected BodyEcho to be true")
	}
}

func TestVerifyTargetsDoesNotConfirmBodyEcho(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`<html><body>` + r.URL.RawQuery + `</body></html>`))
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://97y.me/tjneJ"},
		Param:     "url",
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("expected one result, got %d", len(results))
	}
	if results[0].Confirmed {
		t.Fatalf("body echo must not be confirmed: %+v", results[0])
	}
	if results[0].Evidence != EvidenceBodyEcho {
		t.Fatalf("expected evidence %q, got %q", EvidenceBodyEcho, results[0].Evidence)
	}
}

func TestVerifyTargetsReportsOwnParamHit(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, r.URL.Query().Get("next"), http.StatusFound)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go?next=/x"}, BatchOptions{
		Endpoints: []string{"https://97y.me/tjneJ"},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("expected one result, got %d", len(results))
	}
	if !results[0].Confirmed {
		t.Fatalf("expected confirmed: %+v", results[0])
	}
	if results[0].OwnParam != "next" {
		t.Fatalf("expected own param to be next, got %q", results[0].OwnParam)
	}
	if !results[0].OwnParamHit {
		t.Fatalf("expected OwnParamHit to be true: %+v", results[0])
	}
}

func TestVerifyTargetsRepeatMeasuresStability(t *testing.T) {
	// flaky 站：第一次跳、第二次不跳 —— 重複複測要看出來不穩。
	var calls int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if atomic.AddInt32(&calls, 1) == 1 {
			http.Redirect(w, r, r.URL.Query().Get("url"), http.StatusFound)
			return
		}
		_, _ = w.Write([]byte("<html>no redirect this time</html>"))
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://97y.me/tjneJ"},
		Param:     "url",
		Repeat:    3,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("expected one result, got %d", len(results))
	}
	if results[0].Attempts != 3 {
		t.Fatalf("expected 3 attempts, got %d", results[0].Attempts)
	}
	if results[0].Stable {
		t.Fatalf("expected Stable to be false for a flaky target: %+v", results[0])
	}
}

func TestVerifyTargetsRepeatConsistentIsStable(t *testing.T) {
	var calls int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&calls, 1)
		http.Redirect(w, r, r.URL.Query().Get("url"), http.StatusFound)
	}))
	defer server.Close()

	results, err := VerifyTargets(context.Background(), server.Client(), []string{server.URL + "/go"}, BatchOptions{
		Endpoints: []string{"https://97y.me/tjneJ"},
		Param:     "url",
		Repeat:    2,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !results[0].Stable {
		t.Fatalf("expected Stable to be true: %+v", results[0])
	}
	if results[0].Attempts != 2 {
		t.Fatalf("expected 2 attempts, got %d", results[0].Attempts)
	}
}

func TestCheckEndpointFlagsScriptMismatch(t *testing.T) {
	// 端點回 HTML，卻要拿來當 <script src> —— 必須判定「不適合」。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		_, _ = w.Write([]byte("<!doctype html><html><body>hi</body></html>"))
	}))
	defer server.Close()

	check := CheckEndpoint(context.Background(), server.Client(), server.URL, InjectionKindScriptSrc)
	if !check.Reachable {
		t.Fatalf("expected the endpoint to be reachable: %+v", check)
	}
	if check.Suitable {
		t.Fatalf("an HTML endpoint must not be suitable for script_src: %+v", check)
	}
}

func TestCheckEndpointAcceptsScriptEndpoint(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/javascript")
		_, _ = w.Write([]byte("window.location='https://97y.me/tjneJ';"))
	}))
	defer server.Close()

	check := CheckEndpoint(context.Background(), server.Client(), server.URL, InjectionKindScriptSrc)
	if !check.Suitable {
		t.Fatalf("a JS endpoint must be suitable for script_src: %+v", check)
	}
	if !check.ScriptLike {
		t.Fatalf("expected ScriptLike to be true: %+v", check)
	}
}

func TestCheckEndpointReportsUnreachable(t *testing.T) {
	// 指向一個不存在的位址，必須報不可達而不是 panic。
	client := &http.Client{Timeout: 500 * time.Millisecond}
	check := CheckEndpoint(context.Background(), client, "http://127.0.0.1:1/never", "")
	if check.Reachable {
		t.Fatalf("expected unreachable: %+v", check)
	}
	if check.Suitable {
		t.Fatalf("an unreachable endpoint must not be suitable: %+v", check)
	}
}
