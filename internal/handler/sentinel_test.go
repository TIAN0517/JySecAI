package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/sentinel"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func setupTestSentinelHandler(t *testing.T) (*SentinelHandler, *database.DB) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "sentinel-test.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	handler := NewSentinelHandler(db, zap.NewNop())
	return handler, db
}

func TestSentinelScanValidation(t *testing.T) {
	handler, _ := setupTestSentinelHandler(t)

	r := gin.New()
	r.POST("/api/sentinel/scan", handler.StartScan)

	// Test private IP target rejection
	body, _ := json.Marshal(map[string]string{"target": "192.168.1.1"})
	req := httptest.NewRequest("POST", "/api/sentinel/scan", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for private IP, got %d: %s", w.Code, w.Body.String())
	}

	// Test invalid subdomain rejection
	body, _ = json.Marshal(map[string]string{"target": "foo.example.com"})
	req = httptest.NewRequest("POST", "/api/sentinel/scan", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for 3rd-level domain, got %d: %s", w.Code, w.Body.String())
	}
}

func TestSentinelSyncDeduplication(t *testing.T) {
	handler, db := setupTestSentinelHandler(t)

	// Create and save a mock completed snapshot
	snap := &sentinel.ScanSnapshot{
		ID:         "test-snap-001",
		Target:     "example.com",
		TargetKind: "domain",
		Status:     "completed",
		CreatedAt:  time.Now().Add(-10 * time.Second),
		FinishedAt: time.Now().Format(time.RFC3339),
		Assets: []sentinel.AssetItem{
			{Host: "example.com", IP: "93.184.216.34", Scope: "official", Alive: true, Title: "Example Domain"},
			{Host: "api.example.com", IP: "93.184.216.35", Scope: "product", Alive: true, Title: "API Gateway"},
		},
		Ports: []sentinel.PortItem{
			{Host: "example.com", IP: "93.184.216.34", Port: 80, Service: "http"},
			{Host: "example.com", IP: "93.184.216.34", Port: 443, Service: "https"},
		},
		Databases: []sentinel.DatabaseItem{
			{EngineID: "redis", EngineName: "Redis", Host: "example.com", Port: 6379, Risk: "unauth", Evidence: "+PONG (noauth)"},
		},
		Findings: []sentinel.FindingItem{
			{ID: "f1", Category: "database", Severity: "high", Title: "Redis 未授权访问 / 暴露在公网", Detail: "Redis 端口 6379 可直连", Host: "example.com"},
		},
	}
	if err := db.SaveSentinelScan(snap); err != nil {
		t.Fatalf("failed to save test snapshot: %v", err)
	}

	r := gin.New()
	r.POST("/api/sentinel/sync/assets", handler.SyncToAssets)
	r.POST("/api/sentinel/sync/vulnerabilities", handler.SyncToVulnerabilities)

	// 1. Sync assets first time
	body, _ := json.Marshal(map[string]string{"scan_id": "test-snap-001"})
	req := httptest.NewRequest("POST", "/api/sentinel/sync/assets", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("sync assets failed with %d: %s", w.Code, w.Body.String())
	}
	var res1 map[string]interface{}
	_ = json.Unmarshal(w.Body.Bytes(), &res1)
	if res1["created"].(float64) < 2 {
		t.Fatalf("expected at least 2 assets created, got %v", res1)
	}

	// 2. Sync assets second time (upsert / deduplication check)
	req2 := httptest.NewRequest("POST", "/api/sentinel/sync/assets", bytes.NewReader(body))
	req2.Header.Set("Content-Type", "application/json")
	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, req2)
	var res2 map[string]interface{}
	_ = json.Unmarshal(w2.Body.Bytes(), &res2)
	if res2["created"].(float64) != 0 {
		t.Fatalf("expected 0 assets created on second sync (dedup), got %v", res2)
	}

	// 3. Sync vulnerabilities first time
	reqV1 := httptest.NewRequest("POST", "/api/sentinel/sync/vulnerabilities", bytes.NewReader(body))
	reqV1.Header.Set("Content-Type", "application/json")
	wV1 := httptest.NewRecorder()
	r.ServeHTTP(wV1, reqV1)

	if wV1.Code != http.StatusOK {
		t.Fatalf("sync vulns failed with %d: %s", wV1.Code, wV1.Body.String())
	}
	var resV1 map[string]interface{}
	_ = json.Unmarshal(wV1.Body.Bytes(), &resV1)
	if resV1["created"].(float64) != 1 {
		t.Fatalf("expected 1 vuln created, got %v", resV1)
	}

	// 4. Sync vulnerabilities second time (deduplication check)
	reqV2 := httptest.NewRequest("POST", "/api/sentinel/sync/vulnerabilities", bytes.NewReader(body))
	reqV2.Header.Set("Content-Type", "application/json")
	wV2 := httptest.NewRecorder()
	r.ServeHTTP(wV2, reqV2)

	var resV2 map[string]interface{}
	_ = json.Unmarshal(wV2.Body.Bytes(), &resV2)
	if resV2["created"].(float64) != 0 || resV2["skipped"].(float64) != 1 {
		t.Fatalf("expected 0 created and 1 skipped on duplicate sync, got %v", resV2)
	}
}
