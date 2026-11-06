package handler

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/security"
)

func TestTargetInScope(t *testing.T) {
	patterns := []string{"app.example.com", "*.example.com", "10.20.0.0/24"}
	allowed := []string{"https://app.example.com/login", "a.example.com", "https://10.20.0.8/"}
	rejected := []string{"https://example.com", "evil.com", "https://10.20.1.8/", "not a host"}
	for _, target := range allowed {
		if !targetInScope(target, patterns) {
			t.Fatalf("%s should be in scope", target)
		}
	}
	for _, target := range rejected {
		if targetInScope(target, patterns) {
			t.Fatalf("%s should be out of scope", target)
		}
	}
}

func TestSecurityOpsApproveStaysInsideAuthorization(t *testing.T) {
	gin.SetMode(gin.TestMode)
	var requests int
	var scanBody map[string]any
	remote := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests++
		if strings.Contains(r.Header.Get("Authorization"), "remote-token") && r.URL.Path == "/api/scan" {
			raw, _ := io.ReadAll(r.Body)
			_ = json.Unmarshal(raw, &scanBody)
			if bytes.Contains(raw, []byte("remote-token")) {
				t.Errorf("token leaked: %s", raw)
			}
		}
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.URL.Path == "/api/status":
			_, _ = w.Write([]byte(`{"running":false}`))
		case r.URL.Path == "/api/scan":
			_, _ = w.Write([]byte(`{"status":"started","instance_id":"inst_9"}`))
		case strings.HasSuffix(r.URL.Path, "/events"):
			_, _ = w.Write([]byte(`[{"type":"tool_call","content":"httpx","timestamp":"2026-10-20T00:00:00Z","current_phase":1}]`))
		case strings.Contains(r.URL.Path, "/api/report/"):
			w.Header().Set("Content-Type", "application/pdf")
			_, _ = w.Write([]byte("%PDF-test"))
		default:
			_, _ = w.Write([]byte(`{"status":"running","current_phase":1,"vuln_count":0}`))
		}
	}))
	defer remote.Close()

	db, err := database.NewDB(filepath.Join(t.TempDir(), "security-ops.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	handler := NewSecurityOpsHandler(db, &config.Config{Xalgorix: config.XalgorixConfig{
		Enabled: true, BaseURL: remote.URL, APIToken: "remote-token",
	}}, zap.NewNop())
	handler.now = func() time.Time { return time.Date(2026, 10, 20, 0, 0, 0, 0, time.UTC) }

	router := gin.New()
	mountSecurityOps(router, "owner-a", database.RBACScopeOwn)
	other := gin.New()
	mountSecurityOps(other, "owner-b", database.RBACScopeOwn)
	registerSecurityOps(router, handler)
	registerSecurityOps(other, handler)

	outOfScope := securityOpsPayload("https://evil.example")
	if code, _ := doJSON(router, http.MethodPost, "/api/security-ops/runs", outOfScope); code != http.StatusBadRequest || requests != 0 {
		t.Fatalf("out of scope code=%d remoteRequests=%d", code, requests)
	}

	code, created := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/login"))
	if code != http.StatusCreated {
		t.Fatalf("create code=%d body=%s", code, created)
	}
	var createdBody struct {
		Run struct {
			ID     string `json:"id"`
			Status string `json:"status"`
		} `json:"run"`
	}
	if err := json.Unmarshal(created, &createdBody); err != nil {
		t.Fatal(err)
	}
	if createdBody.Run.Status != "awaiting_approval" || requests != 0 {
		t.Fatalf("created before approval: %#v requests=%d", createdBody.Run, requests)
	}

	code, approved := doJSON(router, http.MethodPost, "/api/security-ops/runs/"+createdBody.Run.ID+"/approve", nil)
	if code != http.StatusOK {
		t.Fatalf("approve code=%d body=%s", code, approved)
	}
	if scanBody["scan_mode"] != "single" {
		t.Fatalf("scan body %#v", scanBody)
	}
	phases, _ := scanBody["phases"].([]any)
	if len(phases) != 1 || phases[0] != float64(1) {
		t.Fatalf("phases %#v", scanBody["phases"])
	}

	if code, _ := doJSON(other, http.MethodGet, "/api/security-ops/runs/"+createdBody.Run.ID+"/events", nil); code != http.StatusNotFound {
		t.Fatalf("other owner events code=%d", code)
	}
	code, events := doJSON(router, http.MethodGet, "/api/security-ops/runs/"+createdBody.Run.ID+"/events", nil)
	if code != http.StatusOK || !bytes.Contains(events, []byte("httpx")) {
		t.Fatalf("events code=%d body=%s", code, events)
	}
	code, report := doJSON(router, http.MethodGet, "/api/security-ops/runs/"+createdBody.Run.ID+"/report", nil)
	if code != http.StatusOK || !bytes.Contains(report, []byte("%PDF-test")) {
		t.Fatalf("report code=%d body=%s", code, report)
	}

	catalogCode, catalog := doJSON(router, http.MethodGet, "/api/security-ops/catalog", nil)
	if catalogCode != http.StatusOK || bytes.Contains(catalog, []byte("remote-token")) {
		t.Fatalf("catalog leaked or failed: %d %s", catalogCode, catalog)
	}
}

func securityOpsPayload(target string) []byte {
	body := map[string]any{
		"projectId": "web-audit-2026",
		"engine":    "xalgorix",
		"profile":   "audit",
		"targets":   []string{target},
		"objective": "检查授权范围内的暴露面",
		"authorization": map[string]any{
			"id":             "AUTH-2026-001",
			"projectId":      "web-audit-2026",
			"targetPatterns": []string{"app.example.com"},
			"operations":     []string{"passive_discovery"},
			"validFrom":      "2026-10-19T00:00:00Z",
			"validUntil":     "2026-10-26T00:00:00Z",
			"approvedBy":     "audit-lead",
			"attested":       true,
		},
		"idempotencyKey": "run-" + target,
	}
	encoded, _ := json.Marshal(body)
	return encoded
}

func mountSecurityOps(router *gin.Engine, userID, scope string) {
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: userID, Scope: scope})
		c.Next()
	})
}

func registerSecurityOps(router *gin.Engine, handler *SecurityOpsHandler) {
	api := router.Group("/api")
	api.GET("/security-ops/catalog", handler.Catalog)
	api.POST("/security-ops/runs", handler.CreateRun)
	api.POST("/security-ops/runs/:id/approve", handler.ApproveRun)
	api.GET("/security-ops/runs/:id/events", handler.ListEvents)
	api.GET("/security-ops/runs/:id/report", handler.DownloadReport)
}

func doJSON(router *gin.Engine, method, path string, body []byte) (int, []byte) {
	var reader io.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	}
	req := httptest.NewRequest(method, path, reader)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)
	return recorder.Code, recorder.Body.Bytes()
}

func TestCompletedScanStoresFindingOnce(t *testing.T) {
	gin.SetMode(gin.TestMode)
	remote := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/findings" {
			_, _ = w.Write([]byte(`[{"title":"Missing header","severity":"medium","endpoint":"https://app.example.com/login","verified":false}]`))
			return
		}
		_, _ = w.Write([]byte(`{"status":"finished","current_phase":22,"vuln_count":1}`))
	}))
	defer remote.Close()

	db, err := database.NewDB(filepath.Join(t.TempDir(), "ingest.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	h := NewSecurityOpsHandler(db, &config.Config{Xalgorix: config.XalgorixConfig{
		Enabled: true, BaseURL: remote.URL, APIToken: "remote-token",
	}}, zap.NewNop())
	targets, _ := json.Marshal([]string{"https://app.example.com/login"})
	run := &database.SecurityOpsRun{
		ID: "run-ingest", ProjectID: "web-audit", OwnerID: "owner-a", Engine: "xalgorix",
		Profile: "audit", Operation: "passive_discovery", Objective: "检查授权范围",
		TargetsJSON: string(targets), PatternsJSON: `["app.example.com"]`, AuthorizationJSON: `{}`,
		Status: "running", RemoteID: "inst_1",
	}
	if err := db.InsertSecurityOpsRun(run); err != nil {
		t.Fatal(err)
	}
	h.refreshRemote(run)
	if run.Status != "completed" {
		t.Fatalf("status=%s", run.Status)
	}
	rows, err := db.ListVulnerabilities(20, 0, database.VulnerabilityListFilter{ProjectID: "web-audit"})
	if err != nil {
		t.Fatal(err)
	}
	if len(rows) != 1 || rows[0].Title != "Missing header" || rows[0].Status != database.VulnerabilityStatusOpen {
		t.Fatalf("stored=%#v", rows)
	}
	if again := h.storeRunFindings(run); again != 0 {
		t.Fatalf("second ingest stored %d", again)
	}
	rows, err = db.ListVulnerabilities(20, 0, database.VulnerabilityListFilter{ProjectID: "web-audit"})
	if err != nil {
		t.Fatal(err)
	}
	if len(rows) != 1 {
		t.Fatalf("duplicate rows=%d", len(rows))
	}
}
