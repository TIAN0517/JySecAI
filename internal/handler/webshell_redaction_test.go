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
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

const webshellTestPassword = "REAL-WEBSHELL-PASSWORD"

// setupWebshellRedactionTest 建立一個帶密碼的 WebShell 連線，回傳可供
// UpdateConnection / ListConnections 使用的環境。
func setupWebshellRedactionTest(t *testing.T) (*database.DB, *database.RBACUser, *database.WebShellConnection) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "webshell-redact.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	user, err := db.CreateRBACUser("owner1", "Owner One", "hash", true, nil)
	if err != nil {
		t.Fatalf("CreateRBACUser: %v", err)
	}
	conn := &database.WebShellConnection{
		ID:        "ws_redact",
		URL:       "http://127.0.0.1/shell.php",
		Password:  webshellTestPassword,
		Type:      "php",
		Method:    "post",
		CmdParam:  "cmd",
		Remark:    "test",
		CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(conn); err != nil {
		t.Fatalf("CreateWebshellConnection: %v", err)
	}
	if err := db.SetResourceOwner("webshell", conn.ID, user.ID); err != nil {
		t.Fatalf("SetResourceOwner: %v", err)
	}
	if err := db.AssignResourceToUser(user.ID, "webshell", conn.ID); err != nil {
		t.Fatalf("AssignResourceToUser: %v", err)
	}
	return db, user, conn
}

func performWebshellUpdate(user *database.RBACUser, id string, body map[string]interface{}, h gin.HandlerFunc) *httptest.ResponseRecorder {
	payload, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPut, "/api/webshell/connections/"+id, bytes.NewReader(payload))
	c.Request.Header.Set("Content-Type", "application/json")
	c.Params = gin.Params{{Key: "id", Value: id}}
	c.Set(security.ContextSessionKey, security.Session{
		UserID:      user.ID,
		Username:    user.Username,
		Permissions: map[string]bool{"webshell:read": true, "webshell:write": true},
		Scope:       database.RBACScopeAssigned,
	})
	h(c)
	return w
}

func performWebshellList(user *database.RBACUser, h gin.HandlerFunc) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/api/webshell/connections", nil)
	c.Set(security.ContextSessionKey, security.Session{
		UserID:      user.ID,
		Username:    user.Username,
		Permissions: map[string]bool{"webshell:read": true},
		Scope:       database.RBACScopeAssigned,
	})
	h(c)
	return w
}

// 列表回應不得包含明文密碼。
func TestWebshellListDoesNotLeakPassword(t *testing.T) {
	db, user, _ := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellList(user, h.ListConnections)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	if bytes.Contains(w.Body.Bytes(), []byte(webshellTestPassword)) {
		t.Fatalf("列表回應洩漏明文密碼：%s", w.Body.String())
	}
	var list []database.WebShellConnection
	if err := json.Unmarshal(w.Body.Bytes(), &list); err != nil {
		t.Fatalf("decode list: %v", err)
	}
	if len(list) != 1 {
		t.Fatalf("list len = %d, want 1", len(list))
	}
	if list[0].Password != database.RedactedSecretPlaceholder {
		t.Errorf("列表中密碼 = %q, want %q", list[0].Password, database.RedactedSecretPlaceholder)
	}
	if list[0].URL == "" {
		t.Error("列表回應遺漏 URL，遮罩過度")
	}
}

// 建立連線的回應同樣不得回傳明文密碼。
func TestWebshellCreateResponseDoesNotLeakPassword(t *testing.T) {
	db, user, _ := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellJSON(user, http.MethodPost, "/api/webshell/connections", map[string]interface{}{
		"url":      "http://127.0.0.1/new.php",
		"password": "another-secret",
		"type":     "php",
		"method":   "post",
	}, h.CreateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	if bytes.Contains(w.Body.Bytes(), []byte("another-secret")) {
		t.Fatalf("建立回應洩漏明文密碼：%s", w.Body.String())
	}
}

// 讀-改-寫：使用者只改 URL，密碼欄位送空字串，後端必須沿用既有密碼。
func TestWebshellUpdateKeepsPasswordWhenFieldLeftBlank(t *testing.T) {
	db, user, conn := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellUpdate(user, conn.ID, map[string]interface{}{
		"url":      "http://127.0.0.1/renamed.php",
		"password": "",
		"type":     "php",
		"method":   "post",
		"remark":   "renamed",
	}, h.UpdateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	stored, err := db.GetWebshellConnection(conn.ID)
	if err != nil || stored == nil {
		t.Fatalf("GetWebshellConnection: %v", err)
	}
	if stored.Password != webshellTestPassword {
		t.Errorf("修改 URL 後密碼被清空：%q", stored.Password)
	}
	if stored.URL != "http://127.0.0.1/renamed.php" {
		t.Errorf("URL 未更新：%q", stored.URL)
	}
	if stored.Remark != "renamed" {
		t.Errorf("備註未更新：%q", stored.Remark)
	}
}

// 前端若仍送遮罩佔位符，後端也必須視為「不變更」。
func TestWebshellUpdateKeepsPasswordWhenPlaceholderSentBack(t *testing.T) {
	db, user, conn := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellUpdate(user, conn.ID, map[string]interface{}{
		"url":      "http://127.0.0.1/shell.php",
		"password": database.RedactedSecretPlaceholder,
		"type":     "php",
		"method":   "post",
	}, h.UpdateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	stored, _ := db.GetWebshellConnection(conn.ID)
	if stored == nil || stored.Password != webshellTestPassword {
		t.Errorf("遮罩佔位符覆蓋了既有密碼：%+v", stored)
	}
}

// 使用者仍可設定新密碼。
func TestWebshellUpdateAcceptsNewPassword(t *testing.T) {
	db, user, conn := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellUpdate(user, conn.ID, map[string]interface{}{
		"url":      conn.URL,
		"password": "rotated-password",
		"type":     "php",
		"method":   "post",
	}, h.UpdateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	stored, _ := db.GetWebshellConnection(conn.ID)
	if stored == nil || stored.Password != "rotated-password" {
		t.Errorf("新密碼未寫入：%+v", stored)
	}
}

// 明確勾選清除時才真的清空密碼 —— 遮罩機制不得吃掉既有功能。
func TestWebshellUpdateClearPasswordWhenExplicitlyRequested(t *testing.T) {
	db, user, conn := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellUpdate(user, conn.ID, map[string]interface{}{
		"url":            conn.URL,
		"password":       "",
		"clear_password": true,
		"type":           "php",
		"method":         "post",
	}, h.UpdateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
	}
	stored, _ := db.GetWebshellConnection(conn.ID)
	if stored == nil || stored.Password != "" {
		t.Errorf("clear_password 未生效，密碼仍為 %+v", stored)
	}
}

// 更新回應本身也不得回傳明文密碼。
func TestWebshellUpdateResponseDoesNotLeakPassword(t *testing.T) {
	db, user, conn := setupWebshellRedactionTest(t)
	h := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellUpdate(user, conn.ID, map[string]interface{}{
		"url":      conn.URL,
		"password": "fresh-secret-value",
		"type":     "php",
		"method":   "post",
	}, h.UpdateConnection)
	if bytes.Contains(w.Body.Bytes(), []byte("fresh-secret-value")) {
		t.Fatalf("更新回應洩漏明文密碼：%s", w.Body.String())
	}
}
