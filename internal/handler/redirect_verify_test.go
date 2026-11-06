package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// 批次受控跳轉驗證的 API 測試。

func newRedirectVerifyTestRouter(t *testing.T, h *RedirectVerifyHandler) *gin.Engine {
	t.Helper()
	gin.SetMode(gin.TestMode)
	router := gin.New()
	middleware := func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{
			UserID:   "user-1",
			Scope:    database.RBACScopeAll,
			Roles:    []string{"admin"},
			Username: "tester",
		})
		c.Next()
	}
	router.POST("/api/redirect-verify/runs", middleware, h.CreateRun)
	router.GET("/api/redirect-verify/runs/:id", middleware, h.GetRun)
	router.GET("/api/redirect-verify/runs/:id/report", middleware, h.RunReport)
	router.POST("/api/redirect-verify/runs/:id/cancel", middleware, h.CancelRun)
	router.POST("/api/redirect-verify/crawl", middleware, h.Crawl)
	router.POST("/api/redirect-verify/injections", middleware, h.ScanInjections)
	router.GET("/api/redirect-verify/implant", middleware, h.ImplantCapabilities)
	router.POST("/api/redirect-verify/implant", middleware, h.BuildImplant)
	router.GET("/api/redirect-verify/endpoints", middleware, h.ListEndpoints)
	return router
}

func newRedirectVerifyTestHandler(t *testing.T) (*RedirectVerifyHandler, *database.DB) {
	t.Helper()
	return newRedirectVerifyTestHandlerWithEndpoint(t, "https://cb.example.com/land")
}

// newRedirectVerifyTestHandlerWithEndpoint 建立指定受控端點的 handler。
//
// 需要不同的端點是為了釘死「確認可跳轉就一定上鍊」：目標與受控端點都在
// 本機迴環時也必須建立漏洞紀錄，不因位址是 127.0.0.1 而被跳過。
func newRedirectVerifyTestHandlerWithEndpoint(t *testing.T, endpoint string) (*RedirectVerifyHandler, *database.DB) {
	t.Helper()
	dbPath := filepath.Join(t.TempDir(), "redirect-verify-handler.db")
	db, err := database.NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	cfg := &config.Config{}
	cfg.Redirect.URLs = []string{endpoint}
	return NewRedirectVerifyHandler(cfg, db, zap.NewNop()), db
}

func TestRedirectVerifyCreateRunConfirmsAndRecordsVulnerability(t *testing.T) {
	// 目標站只有 /go 且帶著 url 參數時才會跳向受控端點；/plain 永遠不跳。
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/go" && r.URL.Query().Get("url") == "https://cb.example.com/land" {
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	body := map[string]interface{}{
		"targets":     []string{server.URL + "/go", server.URL + "/plain"},
		"auto_record": true,
	}
	payload, _ := json.Marshal(body)
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/runs", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusAccepted {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}

	var created struct {
		Run database.RedirectVerifyRun `json:"run"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	if created.Run.ID == "" {
		t.Fatal("run id missing")
	}
	if created.Run.Total != 2 {
		t.Fatalf("unexpected total %d", created.Run.Total)
	}
	if created.Run.Proxy != "" {
		t.Fatalf("unexpected proxy %q", created.Run.Proxy)
	}

	// 等背景批次跑完。
	run := waitForRedirectVerifyRun(t, db, created.Run.ID)

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	confirmed := 0
	for _, result := range results {
		if result.Confirmed {
			confirmed++
			if result.VulnerabilityID == "" {
				t.Fatal("confirmed result must link to a vulnerability record")
			}
			vuln, err := db.GetVulnerability(result.VulnerabilityID)
			if err != nil {
				t.Fatalf("vulnerability not found: %v", err)
			}
			if !strings.Contains(vuln.Title, "重定向") {
				t.Fatalf("unexpected vulnerability title: %q", vuln.Title)
			}
			if vuln.TypeCode != "open-redirect" {
				t.Fatalf("unexpected vulnerability type code: %q", vuln.TypeCode)
			}
			if vuln.Status != database.VulnerabilityStatusConfirmed {
				t.Fatalf("unexpected vulnerability status: %q", vuln.Status)
			}
			if !strings.Contains(vuln.Evidence, "Location") && !strings.Contains(vuln.Evidence, "location") {
				t.Fatalf("evidence should carry the probe details: %q", vuln.Evidence)
			}
		}
	}
	if confirmed != 1 {
		t.Fatalf("expected exactly 1 confirmed target, got %d", confirmed)
	}
	if run.Confirmed != 1 || run.Completed != 2 {
		t.Fatalf("unexpected run counters: confirmed=%d completed=%d", run.Confirmed, run.Completed)
	}
}

func TestRedirectVerifyCreateRunRequiresTargets(t *testing.T) {
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	payload, _ := json.Marshal(map[string]interface{}{"targets": []string{}})
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/runs", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", recorder.Code)
	}
}

func TestRedirectVerifyCreateRunRejectsUnknownProxyScheme(t *testing.T) {
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	payload, _ := json.Marshal(map[string]interface{}{
		"targets": []string{"https://victim.example/go"},
		"proxy":   "ftp://127.0.0.1:1080",
	})
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/runs", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for unsupported proxy scheme, got %d: %s", recorder.Code, recorder.Body.String())
	}
}

func TestRedirectVerifyReportContainsConfirmedTargets(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("url") == "https://cb.example.com/land" {
			w.Header().Set("Location", "https://cb.example.com/land")
			w.WriteHeader(http.StatusFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	h, db := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	payload, _ := json.Marshal(map[string]interface{}{"targets": []string{server.URL + "/go"}})
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/runs", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)

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
	if reportRecorder.Code != http.StatusOK {
		t.Fatalf("unexpected report status %d", reportRecorder.Code)
	}
	body := reportRecorder.Body.String()
	if !strings.Contains(body, "批次受控跳轉驗證報告") {
		t.Fatalf("report header missing:\n%s", body)
	}
	if !strings.Contains(body, server.URL+"/go") {
		t.Fatalf("report should list the target:\n%s", body)
	}
}

func TestRedirectVerifyCrawlFindsCandidates(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		_, _ = w.Write([]byte(`<html><body><a href="/go?url=/next">go</a></body></html>`))
	}))
	defer server.Close()

	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	payload, _ := json.Marshal(map[string]interface{}{"seeds": []string{server.URL + "/"}})
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/crawl", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	var response struct {
		Candidates []string `json:"candidates"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &response); err != nil {
		t.Fatal(err)
	}
	if len(response.Candidates) == 0 {
		t.Fatalf("expected candidates, got %+v", response)
	}
	if !strings.Contains(response.Candidates[0], "url=") {
		t.Fatalf("unexpected candidate: %+v", response.Candidates)
	}
}

func TestRedirectVerifyCrawlRejectsProxyGroupWithoutPool(t *testing.T) {
	// 代理池沒啟用時指定 proxy_group 必須明確報錯，不能靜默直連。
	h, _ := newRedirectVerifyTestHandler(t)
	router := newRedirectVerifyTestRouter(t, h)

	payload, _ := json.Marshal(map[string]interface{}{
		"seeds":       []string{"https://example.com"},
		"proxy_group": "residential",
	})
	request := httptest.NewRequest(http.MethodPost, "/api/redirect-verify/crawl", bytes.NewReader(payload))
	request.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, request)

	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("unexpected status %d: %s", recorder.Code, recorder.Body.String())
	}
	if !strings.Contains(recorder.Body.String(), "proxy_group") {
		t.Fatalf("error should mention proxy_group: %s", recorder.Body.String())
	}
}

// waitForRedirectVerifyRun 等背景批次結束。
func waitForRedirectVerifyRun(t *testing.T, db *database.DB, runID string) *database.RedirectVerifyRun {
	t.Helper()
	deadline := time.Now().Add(10 * time.Second)
	for time.Now().Before(deadline) {
		run, err := db.GetRedirectVerifyRun(runID)
		if err != nil {
			t.Fatal(err)
		}
		if run.Status == database.RedirectVerifyStatusCompleted ||
			run.Status == database.RedirectVerifyStatusCancelled ||
			run.Status == database.RedirectVerifyStatusFailed {
			return run
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatalf("run %s did not finish in time", runID)
	return nil
}
