package handler

import (
	"encoding/json"
	"net/http"
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

// mountAuthorizationLetter 掛上授權書端點與掃描任務端點。
func mountAuthorizationLetter(router *gin.Engine, h *SecurityOpsHandler) {
	api := router.Group("/api")
	api.POST("/security-ops/runs", h.CreateRun)
	api.GET("/projects/:id/authorization-letter", h.ProjectAuthorizationLetter)
	api.POST("/projects/:id/authorization-letter", h.ProjectAuthorizationLetter)
}

// TestAuthorizationLetterUsesStoredAuthorization：GET 應從既有的授權掃描任務取事實。
func TestAuthorizationLetterUsesStoredAuthorization(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "letter.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err := db.CreateProject(&database.Project{ID: "web-audit-2026", Name: "網站授權測試", Status: "active"}); err != nil {
		t.Fatal(err)
	}
	h := NewSecurityOpsHandler(db, &config.Config{}, zap.NewNop())
	h.now = func() time.Time { return time.Date(2026, 10, 20, 0, 0, 0, 0, time.UTC) }
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: "owner-a", Scope: database.RBACScopeAll})
		c.Next()
	})
	mountAuthorizationLetter(router, h)

	status, body := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/"))
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("create status %d body %s", status, body)
	}

	status, body = doJSON(router, http.MethodGet, "/api/projects/web-audit-2026/authorization-letter?format=md", nil)
	if status != http.StatusOK {
		t.Fatalf("letter status %d body %s", status, body)
	}
	letter := string(body)
	for _, needle := range []string{"資訊安全測試授權書", "AUTH-2026-001", "app.example.com", "被動偵察", "audit-lead"} {
		if !strings.Contains(letter, needle) {
			t.Fatalf("授權書缺少內容 %q:\n%s", needle, letter)
		}
	}
}

// TestAuthorizationLetterNeverInventsApprover：授權事實缺授權人時，文件上不該出現一個。
//
// 這是這支端點最重要的行為：它排版，但不發明法律事實。
func TestAuthorizationLetterNeverInventsApprover(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "letter2.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err := db.CreateProject(&database.Project{ID: "p1", Name: "案件", Status: "active"}); err != nil {
		t.Fatal(err)
	}
	h := NewSecurityOpsHandler(db, &config.Config{}, zap.NewNop())
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: "owner-a", Scope: database.RBACScopeAll})
		c.Next()
	})
	mountAuthorizationLetter(router, h)

	// 直接帶一份沒有授權人的授權事實進資料庫（跳過建立任務的驗證路徑）。
	auth := securityOpsAuthorization{
		ID:             "AUTH-2026-777",
		ProjectID:      "p1",
		TargetPatterns: []string{"app.example.com"},
		Operations:     []string{"active_scan"},
		ValidFrom:      time.Date(2026, 10, 19, 0, 0, 0, 0, time.UTC),
		ValidUntil:     time.Date(2026, 10, 26, 0, 0, 0, 0, time.UTC),
		Attested:       false,
	}
	raw, _ := json.Marshal(auth)
	if err := db.InsertSecurityOpsRun(&database.SecurityOpsRun{
		ID:                "run-1",
		ProjectID:         "p1",
		OwnerID:           "owner-a",
		Engine:            "xalgorix",
		Profile:           "audit",
		Operation:         "active_scan",
		Objective:         "檢查暴露面",
		TargetsJSON:       `["app.example.com"]`,
		PatternsJSON:      `["app.example.com"]`,
		AuthorizationJSON: string(raw),
		Status:            "pending",
	}); err != nil {
		t.Fatal(err)
	}

	status, body := doJSON(router, http.MethodGet, "/api/projects/p1/authorization-letter?format=json", nil)
	if status != http.StatusOK {
		t.Fatalf("letter status %d body %s", status, body)
	}
	var payload struct {
		Qualified bool     `json:"qualified"`
		Attested  bool     `json:"attested"`
		Gaps      []string `json:"gaps"`
		Markdown  string   `json:"markdown"`
		Record    struct {
			ApprovedBy string `json:"approvedBy"`
			Attested   bool   `json:"attested"`
		} `json:"record"`
	}
	if err := json.Unmarshal(body, &payload); err != nil {
		t.Fatal(err)
	}
	if payload.Qualified {
		t.Fatal("未確認的授權事實不應是合格文件")
	}
	if payload.Attested || payload.Record.Attested {
		t.Fatal("未確認的授權事實不應被標示為 attested")
	}
	if payload.Record.ApprovedBy != "" {
		t.Fatalf("不應代填授權人: %q", payload.Record.ApprovedBy)
	}
	if !strings.Contains(strings.Join(payload.Gaps, " "), "授權人") {
		t.Fatalf("缺口應指出缺授權人: %v", payload.Gaps)
	}
}

// TestAuthorizationLetterAcceptsClientFactsFromPOST：POST 帶入委託方事實後應產生可簽署文件。
func TestAuthorizationLetterAcceptsClientFactsFromPOST(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "letter3.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err := db.CreateProject(&database.Project{ID: "p1", Name: "案件", Status: "active"}); err != nil {
		t.Fatal(err)
	}
	cfg := &config.Config{}
	cfg.Engagement.VendorName = "示例資安有限公司"
	cfg.Engagement.VendorLead = "李專案"
	h := NewSecurityOpsHandler(db, cfg, zap.NewNop())
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: "owner-a", Scope: database.RBACScopeAll})
		c.Next()
	})
	mountAuthorizationLetter(router, h)

	body := []byte(`{
		"document_id": "AUTH-2026-888",
		"client_name": "示例股份有限公司",
		"client_approver": "王小明",
		"client_approver_role": "資安長",
		"patterns": ["app.example.com"],
		"operations": ["passive_discovery","active_scan"],
		"valid_from": "2026-11-01T00:00:00Z",
		"valid_until": "2026-11-30T00:00:00Z",
		"source_attested": true
	}`)
	status, resp := doJSON(router, http.MethodPost, "/api/projects/p1/authorization-letter?format=md", body)
	if status != http.StatusOK {
		t.Fatalf("letter status %d body %s", status, resp)
	}
	letter := string(resp)
	for _, needle := range []string{"AUTH-2026-888", "示例股份有限公司", "王小明", "示例資安有限公司", "app.example.com"} {
		if !strings.Contains(letter, needle) {
			t.Fatalf("授權書缺少內容 %q:\n%s", needle, letter)
		}
	}
	if strings.Contains(letter, "草稿") {
		t.Fatalf("事實齊全時不應是草稿:\n%s", letter)
	}
}
