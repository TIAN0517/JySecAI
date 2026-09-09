package handler

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"sync"
	"testing"

	"jysecai/internal/database"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func setupTestAWVSHandler(t *testing.T, mockAWVSURL string) (*AWVSHandler, *database.DB) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	tmp := t.TempDir()
	db, err := database.NewDB(filepath.Join(tmp, "awvs-test.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	handler := NewAWVSHandler(db, zap.NewNop(), mockAWVSURL, "test-api-key")
	return handler, db
}

func TestAWVSConcurrencySafety(t *testing.T) {
	// 模擬 AWVS API 伺服器
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/me" {
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"email": "admin@example.com",
				"role":  "admin",
			})
			return
		}
		if r.URL.Path == "/api/v1/targets" {
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"pagination": map[string]interface{}{"count": 5},
			})
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer mockServer.Close()

	handler, _ := setupTestAWVSHandler(t, mockServer.URL)

	// 並發測試 GetStatus 和 UpdateConfig，驗證是否存在 Data Race
	var wg sync.WaitGroup
	for i := 0; i < 25; i++ {
		wg.Add(2)
		go func(idx int) {
			defer wg.Done()
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			handler.GetStatus(c)
		}(i)
		go func(idx int) {
			defer wg.Done()
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			reqBody := fmt.Sprintf(`{"url": "%s", "api_key": "key-%d"}`, mockServer.URL, idx)
			c.Request, _ = http.NewRequest(http.MethodPost, "/api/awvs/config", bytes.NewBufferString(reqBody))
			c.Request.Header.Set("Content-Type", "application/json")
			handler.UpdateConfig(c)
		}(i)
	}
	wg.Wait()
}

func TestAWVSSyncPaginationAndDeduplication(t *testing.T) {
	// 模擬多頁漏洞的 AWVS 伺服器
	mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		if r.URL.Path == "/api/v1/vulnerabilities" {
			cursor := r.URL.Query().Get("c")
			if cursor == "" {
				// 第 1 頁，返回 2 個漏洞，下一頁 cursor 為 "page2"
				_ = json.NewEncoder(w).Encode(map[string]interface{}{
					"vulnerabilities": []map[string]interface{}{
						{
							"vuln_id":     "vuln-1",
							"vt_name":     "SQL Injection",
							"affects_url": "https://example.com/login",
							"severity":    3,
							"tags":        []string{"SQLi"},
						},
						{
							"vuln_id":     "vuln-2",
							"vt_name":     "XSS Vulnerability",
							"affects_url": "https://example.com/search",
							"severity":    2,
							"tags":        []string{"XSS"},
						},
					},
					"pagination": map[string]interface{}{
						"count":   3,
						"cursors": []interface{}{nil, "page2"},
					},
				})
				return
			} else if cursor == "page2" {
				// 第 2 頁，返回最後 1 個漏洞，無下一頁
				_ = json.NewEncoder(w).Encode(map[string]interface{}{
					"vulnerabilities": []map[string]interface{}{
						{
							"vuln_id":     "vuln-3",
							"vt_name":     "CSRF Vulnerability",
							"affects_url": "https://example.com/profile",
							"severity":    1,
							"tags":        []string{"CSRF"},
						},
					},
					"pagination": map[string]interface{}{
						"count":   3,
						"cursors": []interface{}{"0", nil},
					},
				})
				return
			}
		}

		if r.URL.Path == "/api/v1/vulnerabilities/vuln-1" {
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"description": "SQL Injection found",
				"request":     "POST /login HTTP/1.1",
			})
			return
		}
		if r.URL.Path == "/api/v1/vulnerabilities/vuln-2" {
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"description": "Reflected XSS",
				"details":     "q=<script>alert(1)</script>",
			})
			return
		}
		if r.URL.Path == "/api/v1/vulnerabilities/vuln-3" {
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"description": "Missing CSRF token",
			})
			return
		}

		w.WriteHeader(http.StatusNotFound)
	}))
	defer mockServer.Close()

	handler, db := setupTestAWVSHandler(t, mockServer.URL)
	project, err := db.CreateProject(&database.Project{Name: "Target Project"})
	if err != nil {
		t.Fatal(err)
	}

	// 第一次同步：應跨 2 頁同步全部 3 條漏洞
	{
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		reqBody := fmt.Sprintf(`{"project_id": "%s"}`, project.ID)
		c.Request, _ = http.NewRequest(http.MethodPost, "/api/awvs/sync", bytes.NewBufferString(reqBody))
		c.Request.Header.Set("Content-Type", "application/json")
		handler.SyncVulnerabilities(c)

		if w.Code != http.StatusOK {
			t.Fatalf("first sync failed: %d, body: %s", w.Code, w.Body.String())
		}

		var resp map[string]interface{}
		_ = json.Unmarshal(w.Body.Bytes(), &resp)
		if synced, ok := resp["synced"].(float64); !ok || int(synced) != 3 {
			t.Fatalf("expected 3 synced, got %v", resp["synced"])
		}
		if skipped, ok := resp["skipped"].(float64); !ok || int(skipped) != 0 {
			t.Fatalf("expected 0 skipped, got %v", resp["skipped"])
		}

		// 驗證 project_id 確實綁定
		vulns, err := db.ListVulnerabilities(10, 0, database.VulnerabilityListFilter{ProjectID: project.ID})
		if err != nil || len(vulns) != 3 {
			t.Fatalf("expected 3 vulns bound to project, got %d, err: %v", len(vulns), err)
		}
	}

	// 第二次同步：目標重複，應全部被去重跳過（skipped=3, synced=0）
	{
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		reqBody := fmt.Sprintf(`{"project_id": "%s"}`, project.ID)
		c.Request, _ = http.NewRequest(http.MethodPost, "/api/awvs/sync", bytes.NewBufferString(reqBody))
		c.Request.Header.Set("Content-Type", "application/json")
		handler.SyncVulnerabilities(c)

		if w.Code != http.StatusOK {
			t.Fatalf("second sync failed: %d, body: %s", w.Code, w.Body.String())
		}

		var resp map[string]interface{}
		_ = json.Unmarshal(w.Body.Bytes(), &resp)
		if synced, ok := resp["synced"].(float64); !ok || int(synced) != 0 {
			t.Fatalf("expected 0 synced on second run, got %v", resp["synced"])
		}
		if skipped, ok := resp["skipped"].(float64); !ok || int(skipped) != 3 {
			t.Fatalf("expected 3 skipped on second run, got %v", resp["skipped"])
		}

		// 資料庫總量依然為 3，未膨脹
		count, err := db.CountVulnerabilities(database.VulnerabilityListFilter{})
		if err != nil || count != 3 {
			t.Fatalf("database expanded unexpectedly, count = %d, want 3", count)
		}
	}
}
