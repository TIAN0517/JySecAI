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
)

// newAuthorizationInheritHandler 建立授權繼承測試用的 handler 與資料庫。
func newAuthorizationInheritHandler(t *testing.T) (*SecurityOpsHandler, *database.DB, *gin.Engine) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "auth-inherit.db"), zap.NewNop())
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
	mountSecurityOps(router, "owner-a", database.RBACScopeAll)
	registerSecurityOps(router, h)
	return h, db, router
}

// TestAuthorizationInheritedFromPriorAttestedRecord：第二次任務沿用前一次的授權。
//
// 這是授權繼承的主路徑：同一份書面授權只確認一次，後續任務不需要重打。
func TestAuthorizationInheritedFromPriorAttestedRecord(t *testing.T) {
	_, _, router := newAuthorizationInheritHandler(t)

	// 第一筆：人工填寫完整授權。
	status, body := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/"))
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("create status %d body %s", status, body)
	}
	firstRunID := runIDFromResponse(t, body)

	// 第二筆：完全不帶授權 —— 應該沿用。
	payload := map[string]any{
		"projectId":      "web-audit-2026",
		"engine":         "xalgorix",
		"profile":        "audit",
		"targets":        []string{"https://app.example.com/api"},
		"objective":      "檢查授權範圍內的暴露面",
		"idempotencyKey": "run-inherited",
	}
	encoded, _ := json.Marshal(payload)
	status, body = doJSON(router, http.MethodPost, "/api/security-ops/runs", encoded)
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("繼承後應可建立任務，得到 status %d body %s", status, body)
	}
	inherited := authorizationFromResponse(t, body)
	if inherited.ID != "AUTH-2026-001" {
		t.Fatalf("應沿用授權編號，得到 %q", inherited.ID)
	}
	if inherited.ApprovedBy != "audit-lead" {
		t.Fatalf("應沿用授權人，得到 %q", inherited.ApprovedBy)
	}
	if !inherited.Attested {
		t.Fatal("應沿用已確認的授權事實")
	}
	if !inherited.Inherited {
		t.Fatal("沿用來的授權應標記 inherited")
	}
	if inherited.SourceRunID != firstRunID {
		t.Fatalf("應記下來源記錄 %q，得到 %q", firstRunID, inherited.SourceRunID)
	}
	if len(inherited.TargetPatterns) == 0 {
		t.Fatal("應沿用授權範圍")
	}
}

// TestAuthorizationNotInheritedForOtherProject：別的專案沒有授權就不得繼承。
//
// 繼承只在同一專案內進行 —— 別的專案可能有完全不同的書面授權與範圍。
func TestAuthorizationNotInheritedForOtherProject(t *testing.T) {
	_, db, router := newAuthorizationInheritHandler(t)
	if _, err := db.CreateProject(&database.Project{ID: "other-project", Name: "另一個案件", Status: "active"}); err != nil {
		t.Fatal(err)
	}
	status, body := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/"))
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("create status %d body %s", status, body)
	}

	payload := map[string]any{
		"projectId":      "other-project",
		"engine":         "xalgorix",
		"profile":        "audit",
		"targets":        []string{"https://app.example.com/api"},
		"objective":      "檢查暴露面",
		"idempotencyKey": "run-other-project",
	}
	encoded, _ := json.Marshal(payload)
	status, body = doJSON(router, http.MethodPost, "/api/security-ops/runs", encoded)
	if status != http.StatusBadRequest {
		t.Fatalf("沒有授權的專案應被拒絕，得到 status %d body %s", status, body)
	}
	if !strings.Contains(string(body), "授权") {
		t.Fatalf("錯誤訊息應說明缺少授權: %s", body)
	}
}

// TestAuthorizationNotInheritedOutsideScope：目標不在原授權範圍內時不得繼承。
//
// 繼承是把既有書面授權沿用到新任務，不是擴大授權範圍。
func TestAuthorizationNotInheritedOutsideScope(t *testing.T) {
	_, _, router := newAuthorizationInheritHandler(t)
	status, body := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/"))
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("create status %d body %s", status, body)
	}

	payload := map[string]any{
		"projectId":      "web-audit-2026",
		"engine":         "xalgorix",
		"profile":        "audit",
		"targets":        []string{"https://other-site.example.net/"},
		"objective":      "檢查暴露面",
		"idempotencyKey": "run-outside-scope",
	}
	encoded, _ := json.Marshal(payload)
	status, body = doJSON(router, http.MethodPost, "/api/security-ops/runs", encoded)
	if status != http.StatusBadRequest {
		t.Fatalf("範圍外的目標不該繼承授權，得到 status %d body %s", status, body)
	}
}

// TestHalfFilledAuthorizationIsNotCompleted：半填的授權不會被補成全填。
//
// 有編號但缺授權人，代表有人填了一半 —— 補完之後看不出是哪一次確認的，
// 證據鏈會斷掉。寧可拒絕。
func TestHalfFilledAuthorizationIsNotCompleted(t *testing.T) {
	_, _, router := newAuthorizationInheritHandler(t)
	status, body := doJSON(router, http.MethodPost, "/api/security-ops/runs", securityOpsPayload("https://app.example.com/"))
	if status != http.StatusCreated && status != http.StatusOK {
		t.Fatalf("create status %d body %s", status, body)
	}

	payload := map[string]any{
		"projectId":      "web-audit-2026",
		"engine":         "xalgorix",
		"profile":        "audit",
		"targets":        []string{"https://app.example.com/api"},
		"objective":      "檢查暴露面",
		"idempotencyKey": "run-half-filled",
		"authorization": map[string]any{
			"id":             "AUTH-2026-999",
			"projectId":      "web-audit-2026",
			"targetPatterns": []string{"app.example.com"},
			"operations":     []string{"passive_discovery"},
			"validFrom":      "2026-10-19T00:00:00Z",
			"validUntil":     "2026-10-26T00:00:00Z",
		},
	}
	encoded, _ := json.Marshal(payload)
	status, body = doJSON(router, http.MethodPost, "/api/security-ops/runs", encoded)
	if status != http.StatusBadRequest {
		t.Fatalf("半填的授權應被拒絕，得到 status %d body %s", status, body)
	}
	if !strings.Contains(string(body), "授权人") {
		t.Fatalf("錯誤訊息應指出缺授權人: %s", body)
	}
}

// runIDFromResponse 從建立任務的回應取出任務 ID。
func runIDFromResponse(t *testing.T, body []byte) string {
	t.Helper()
	var payload struct {
		Run struct {
			ID string `json:"id"`
		} `json:"run"`
	}
	if err := json.Unmarshal(body, &payload); err != nil {
		t.Fatalf("解析建立任務回應失敗: %v", err)
	}
	return payload.Run.ID
}

// authorizationFromResponse 從建立任務的回應取出授權記錄。
func authorizationFromResponse(t *testing.T, body []byte) securityOpsAuthorization {
	t.Helper()
	var payload struct {
		Run struct {
			Authorization securityOpsAuthorization `json:"authorization"`
		} `json:"run"`
	}
	if err := json.Unmarshal(body, &payload); err != nil {
		t.Fatalf("解析建立任務回應失敗: %v", err)
	}
	return payload.Run.Authorization
}
