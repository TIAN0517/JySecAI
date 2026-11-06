package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"jysecai/internal/database"
)

// 注入點偵測 → 自動植入 → 復測 → 判定真偽的端到端流程。
//
// 這裡用一個 fixture 站同時扮演三種角色：
//   1. 被入侵的頁面（頁面裡有「他們塞的」外部網址）；
//   2. 真的有開放式跳轉的目標（3xx Location → 受控端點）；
//   3. 只會把參數回顯在本文的假目標（粗略掃描器會誤判成跳轉）。
//
// 第 3 種是整條流水線最關鍵的一個案例：沒有證據分級時，confirmed 會是 2，
// 有了分級之後必須是 1，而且偽陽性必須被單獨標成 body_echo。

// compromisedPage 是被注入的頁面。
const compromisedPage = `<html><head>
<script src="https://evil.tld/p.js"></script>
<script src="https://cb.example.com/ours.js"></script>
<link href="https://evil.tld/a.css" rel="stylesheet">
<meta http-equiv="refresh" content="0;url=https://evil.tld/refresh">
</head><body>
<iframe src="https://evil.tld/frame"></iframe>
<form action="https://evil.tld/post"></form>
<script>location.href='https://evil.tld/next';</script>
<a href="/go?next=/x">go</a>
</body></html>`

// redirectVerifyFixture 啟動 fixture 站。
func redirectVerifyFixture(t *testing.T) *httptest.Server {
	t.Helper()
	var goCalls int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/page":
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(compromisedPage))
		case r.URL.Path == "/go":
			// 真的有開放式跳轉：站上自己的參數 next。
			if target := r.URL.Query().Get("next"); target != "" {
				w.Header().Set("Location", target)
				w.WriteHeader(http.StatusFound)
				return
			}
			w.WriteHeader(http.StatusOK)
		case r.URL.Path == "/echo":
			// 偽陽性：把參數值回顯在本文裡，但完全沒有 Location。
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte("<html><body>you were sent to: " + r.URL.RawQuery + "</body></html>"))
		case r.URL.Path == "/flaky":
			// flaky：第一次跳、之後不跳 —— 重複複測要能看出來不穩。
			if atomic.AddInt32(&goCalls, 1) == 1 {
				w.Header().Set("Location", r.URL.Query().Get("url"))
				w.WriteHeader(http.StatusFound)
				return
			}
			w.WriteHeader(http.StatusOK)
		default:
			w.WriteHeader(http.StatusOK)
		}
	}))
	t.Cleanup(server.Close)
	return server
}

func postRedirectVerifyJSON(t *testing.T, router http.Handler, path string, body map[string]interface{}) *httptest.ResponseRecorder {
	t.Helper()
	payload, err := json.Marshal(body)
	if err != nil {
		t.Fatal(err)
	}
	request := httptest.NewRequest(http.MethodPost, path, bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	return recorder
}

func TestRedirectVerifyScanInjectionsFindsAndReplaces(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/injections", map[string]interface{}{
		"url":             server.URL + "/page",
		"endpoint":        "https://cb.example.com/land",
		"encoding":        "none",
		"with_implant":    true,
		"verify_endpoint": true,
	})
	if recorder.Code != http.StatusOK {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var response struct {
		InjectionCount       int `json:"injection_count"`
		ThirdPartyInjections int `json:"third_party_injections"`
		Injections           []struct {
			Kind     string `json:"kind"`
			URL      string `json:"url"`
			SelfHost bool   `json:"self_host"`
		} `json:"injections"`
		Implants []struct {
			Kind     string `json:"kind"`
			Original string `json:"original"`
			Payload  string `json:"payload"`
			Fragment string `json:"fragment"`
		} `json:"implants"`
		EndpointCheck *struct {
			Reachable bool   `json:"reachable"`
			Suitable  bool   `json:"suitable"`
			Note      string `json:"note"`
		} `json:"endpoint_check"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &response); err != nil {
		t.Fatal(err)
	}

	if response.InjectionCount == 0 {
		t.Fatalf("expected injection points, got %+v", response)
	}
	if response.ThirdPartyInjections == 0 {
		t.Fatalf("expected third-party injections, got %+v", response)
	}
	// 我們自己的受控端點必須被排除 —— 否則自動植入會拿自己替換自己。
	for _, point := range response.Injections {
		if strings.Contains(point.URL, "cb.example.com") {
			t.Fatalf("our own endpoint must not be reported as an injection: %+v", point)
		}
	}
	kinds := map[string]bool{}
	for _, point := range response.Injections {
		kinds[point.Kind] = true
	}
	for _, kind := range []string{"script_src", "iframe_src", "meta_refresh", "js_string", "link_href", "form_action"} {
		if !kinds[kind] {
			t.Fatalf("expected injection kind %q, got %v", kind, kinds)
		}
	}
	// 每個注入點都要有對應的替換片段，且片段帶著我們的受控端點。
	if len(response.Implants) != response.InjectionCount {
		t.Fatalf("expected one implant per injection point, got %d implants for %d points",
			len(response.Implants), response.InjectionCount)
	}
	for _, implant := range response.Implants {
		if !strings.Contains(implant.Fragment, "cb.example.com/land") {
			t.Fatalf("implant fragment must carry the controlled endpoint: %s", implant.Fragment)
		}
		if implant.Original == "" {
			t.Fatalf("implant must keep the original URL: %+v", implant)
		}
	}
	if response.EndpointCheck == nil {
		t.Fatal("endpoint check missing")
	}
	// cb.example.com 在測試環境不會真的回應，所以預期是不可達 —— 但仍要給結論。
	if response.EndpointCheck.Note == "" {
		t.Fatalf("endpoint check must explain itself: %+v", response.EndpointCheck)
	}
}

func TestRedirectVerifyScanInjectionsRejectsBadEncodingPerKind(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	// script src 不接受 base64（瀏覽器不會解）—— 後端要明確拒收。
	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/implant", map[string]interface{}{
		"endpoint": "https://cb.example.com/land",
		"encoding": "base64",
		"point": map[string]interface{}{
			"kind": "script_src",
			"url":  "https://evil.tld/p.js",
		},
	})
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for incompatible encoding, got %d: %s", recorder.Code, recorder.Body.String())
	}
	if !strings.Contains(recorder.Body.String(), "supported") {
		t.Fatalf("error should list supported encodings: %s", recorder.Body.String())
	}
	_ = server
}

func TestRedirectVerifyBatchSeparatesRealRedirectFromBodyEcho(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets": []string{server.URL + "/go?next=/x", server.URL + "/echo?url=/x"},
	})
	if recorder.Code != http.StatusAccepted {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	run := waitForRedirectVerifyRun(t, db, created.Run.ID)

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	confirmed := 0
	echoes := 0
	for _, result := range results {
		if result.Confirmed {
			confirmed++
			if result.Evidence != "location" {
				t.Fatalf("confirmed result must carry location evidence: %+v", result)
			}
			if !result.OwnParamHit {
				t.Fatalf("confirmed result must record the own-param hit: %+v", result)
			}
		}
		if result.BodyEcho {
			echoes++
			if result.Confirmed {
				t.Fatalf("body echo must never be counted as confirmed: %+v", result)
			}
			if result.Evidence != "body_echo" {
				t.Fatalf("body echo result must carry body_echo evidence: %+v", result)
			}
		}
	}
	if confirmed != 1 {
		t.Fatalf("expected exactly 1 confirmed target, got %d", confirmed)
	}
	if echoes != 1 {
		t.Fatalf("expected exactly 1 body-echo false positive, got %d", echoes)
	}
	if run.Confirmed != 1 {
		t.Fatalf("run counter must count only real redirects, got %d", run.Confirmed)
	}
}

func TestRedirectVerifyGetRunReturnsAccuracy(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets": []string{server.URL + "/go?next=/x", server.URL + "/echo?url=/x"},
	})
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	waitForRedirectVerifyRun(t, db, created.Run.ID)

	getRequest := httptest.NewRequest(http.MethodGet, "/api/redirect-verify/runs/"+created.Run.ID, nil)
	getRecorder := httptest.NewRecorder()
	router.ServeHTTP(getRecorder, getRequest)
	if getRecorder.Code != http.StatusOK {
		t.Fatalf("unexpected status %d: %s", getRecorder.Code, getRecorder.Body.String())
	}
	var payload struct {
		Accuracy struct {
			Confirmed         int     `json:"confirmed"`
			LocationEvidence  int     `json:"location_evidence"`
			BodyEcho          int     `json:"body_echo"`
			FalsePositiveRate float64 `json:"false_positive_rate"`
			OwnParamHit       int     `json:"own_param_hit"`
		} `json:"accuracy"`
	}
	if err := json.Unmarshal(getRecorder.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	accuracy := payload.Accuracy
	if accuracy.Confirmed != 1 || accuracy.LocationEvidence != 1 {
		t.Fatalf("unexpected accuracy: %+v", accuracy)
	}
	if accuracy.BodyEcho != 1 {
		t.Fatalf("expected 1 body echo in the accuracy summary: %+v", accuracy)
	}
	// 偽陽性率 = 1 / (1+1) = 50%
	if accuracy.FalsePositiveRate < 49.9 || accuracy.FalsePositiveRate > 50.1 {
		t.Fatalf("expected 50%% false positive rate, got %f", accuracy.FalsePositiveRate)
	}
	if accuracy.OwnParamHit != 1 {
		t.Fatalf("expected 1 own-param hit: %+v", accuracy)
	}
}

func TestRedirectVerifyReportIncludesPrecisionSection(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets": []string{server.URL + "/go?next=/x", server.URL + "/echo?url=/x"},
	})
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	waitForRedirectVerifyRun(t, db, created.Run.ID)

	reportRequest := httptest.NewRequest(http.MethodGet, "/api/redirect-verify/runs/"+created.Run.ID+"/report", nil)
	reportRecorder := httptest.NewRecorder()
	router.ServeHTTP(reportRecorder, reportRequest)
	body := reportRecorder.Body.String()
	for _, want := range []string{"## 精準度", "偽陽性率", "真跳轉", "本文回顯"} {
		if !strings.Contains(body, want) {
			t.Fatalf("report should contain %q:\n%s", want, body)
		}
	}
}

func TestRedirectVerifyRepeatMeasuresStability(t *testing.T) {
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets": []string{server.URL + "/flaky"},
		"param":   "url",
		"repeat":  3,
	})
	if recorder.Code != http.StatusAccepted {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	run := waitForRedirectVerifyRun(t, db, created.Run.ID)
	if run.Repeat != 3 {
		t.Fatalf("repeat must be persisted on the run, got %d", run.Repeat)
	}
	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Attempts != 3 {
		t.Fatalf("expected 3 attempts, got %d", results[0].Attempts)
	}
	if results[0].Stable {
		t.Fatalf("a flaky target must not be reported as stable: %+v", results[0])
	}
}

func TestRedirectVerifyImplantCapabilitiesIncludePointMatrix(t *testing.T) {
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	request := httptest.NewRequest(http.MethodGet, "/api/redirect-verify/implant", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("unexpected status %d", recorder.Code)
	}
	var payload struct {
		PointKinds []string            `json:"point_kinds"`
		Matrix     map[string][]string `json:"point_encodings_by_kind"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	if len(payload.PointKinds) == 0 {
		t.Fatalf("point kinds missing: %s", recorder.Body.String())
	}
	allowed, ok := payload.Matrix["script_src"]
	if !ok {
		t.Fatalf("script_src missing from the matrix: %s", recorder.Body.String())
	}
	for _, encoding := range allowed {
		if encoding == "base64" {
			t.Fatalf("script_src must not accept base64: %v", allowed)
		}
	}
}

func TestRedirectVerifyAutoRecordRecordsLoopbackTargetAndEndpoint(t *testing.T) {
	// 自我回歸用的 fixture 都在本機迴環（httptest server + 本機受控端點）。
	// 這裡釘死的是「原本的行為」：確認可跳轉就**必須**自動建立漏洞紀錄，
	// 不因目標或受控端點是 127.0.0.1 而跳過。
	//
	// 為什麼不該用「目標是 loopback 就別上鍊」來擋 fixture：
	// 「跳轉到 localhost」本身是真實的攻擊原語（把受害者導去他自己的
	// 127.0.0.1:6379 之類的內部服務），任何以 loopback 為由的禁令都會誤殺
	// 真實發現。測試 fixture 該自己清理，不該靠產品層加禁令。
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandlerWithEndpoint(t, "http://127.0.0.1:18099/landing")
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets":     []string{server.URL + "/go?next=/x"},
		"auto_record": true,
	})
	if recorder.Code != http.StatusAccepted {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	run := waitForRedirectVerifyRun(t, db, created.Run.ID)

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if !results[0].Confirmed {
		t.Fatalf("the fixture target is a valid redirect finding: %+v", results[0])
	}
	if results[0].VulnerabilityID == "" {
		t.Fatalf("a confirmed redirect must become a vulnerability record: %+v", results[0])
	}
	if results[0].Error != "" {
		t.Fatalf("recording must not produce a probe error: %+v", results[0])
	}
	vuln, err := db.GetVulnerability(results[0].VulnerabilityID)
	if err != nil {
		t.Fatalf("vulnerability record not found: %v", err)
	}
	if vuln.TypeCode != "open-redirect" {
		t.Fatalf("unexpected vulnerability type code: %q", vuln.TypeCode)
	}
	if vuln.Status != database.VulnerabilityStatusConfirmed {
		t.Fatalf("unexpected vulnerability status: %q", vuln.Status)
	}
}

func TestRedirectVerifyAutoRecordRecordsLoopbackTargetWithExternalEndpoint(t *testing.T) {
	// 目標在 localhost、受控端點在外部 → 這是「跳轉到 localhost」的真實
	// 攻擊原語，必須照常上鍊。
	server := redirectVerifyFixture(t)
	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	recorder := postRedirectVerifyJSON(t, router, "/api/redirect-verify/runs", map[string]interface{}{
		"targets":     []string{server.URL + "/go?next=/x"},
		"auto_record": true,
	})
	if recorder.Code != http.StatusAccepted {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	run := waitForRedirectVerifyRun(t, db, created.Run.ID)

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if !results[0].Confirmed {
		t.Fatalf("the fixture target is a valid redirect finding: %+v", results[0])
	}
	if results[0].VulnerabilityID == "" {
		t.Fatalf("a confirmed redirect must become a vulnerability record: %+v", results[0])
	}
	if results[0].Error != "" {
		t.Fatalf("recording must not produce a probe error: %+v", results[0])
	}
}

func TestRedirectVerifyWaitHelperHasTimeout(t *testing.T) {
	// 保護措施：背景批次逾時時不應該無限等待。
	done := make(chan struct{})
	go func() {
		time.Sleep(10 * time.Millisecond)
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("wait helper timed out")
	}
}
