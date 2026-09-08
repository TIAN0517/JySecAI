package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"cyberstrike-ai/internal/security"

	"github.com/gin-gonic/gin"
)

func TestSecurityOpsCreateRunBindsServerIdentity(t *testing.T) {
	gin.SetMode(gin.TestMode)
	var gotTenant, gotUser, gotRoles string
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotTenant = r.Header.Get("X-Jysec-Tenant")
		gotUser = r.Header.Get("X-Jysec-User")
		gotRoles = r.Header.Get("X-Jysec-Roles")
		var body map[string]interface{}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatal(err)
		}
		auth := body["authorization"].(map[string]interface{})
		if auth["tenantId"] != "test-tenant" {
			t.Fatalf("tenantId = %v", auth["tenantId"])
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte(`{"run":{"id":"run_1"}}`))
	}))
	defer upstream.Close()

	base, _ := url.Parse(upstream.URL)
	h := NewSecurityOpsHandler(nil)
	h.baseURL = base
	h.tenantID = "test-tenant"
	router := gin.New()
	router.POST("/api/security-ops/runs", withSecurityOpsSession(map[string]bool{"tasks:write": true, "hitl:write": true}), h.CreateRun)

	body := `{"projectId":"p1","authorization":{"tenantId":"spoofed"}}`
	req := httptest.NewRequest(http.MethodPost, "/api/security-ops/runs", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusAccepted {
		t.Fatalf("status = %d, body = %s", w.Code, w.Body.String())
	}
	if gotTenant != "test-tenant" || gotUser != "user-7" {
		t.Fatalf("identity headers tenant=%q user=%q", gotTenant, gotUser)
	}
	if gotRoles != "security_operator,security_approver" {
		t.Fatalf("roles = %q", gotRoles)
	}
}

func TestSecurityOpsListRunsForwardsOnlyExpectedQuery(t *testing.T) {
	gin.SetMode(gin.TestMode)
	var gotPath, gotQuery string
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath, gotQuery = r.URL.Path, r.URL.RawQuery
		_, _ = w.Write([]byte(`{"items":[]}`))
	}))
	defer upstream.Close()
	base, _ := url.Parse(upstream.URL)
	h := NewSecurityOpsHandler(nil)
	h.baseURL = base
	router := gin.New()
	router.GET("/api/security-ops/runs", withSecurityOpsSession(map[string]bool{"tasks:read": true}), h.ListRuns)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/api/security-ops/runs?limit=50&projectId=p1", nil))
	if w.Code != http.StatusOK || gotPath != "/v1/runs" || gotQuery != "limit=50&projectId=p1" {
		t.Fatalf("status=%d path=%q query=%q", w.Code, gotPath, gotQuery)
	}
}

func withSecurityOpsSession(permissions map[string]bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: "user-7", Username: "operator", Permissions: permissions})
		c.Next()
	}
}
