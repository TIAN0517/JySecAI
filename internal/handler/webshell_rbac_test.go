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

func TestWebshellExecRequiresConnectionAccessWhenConnectionIDProvided(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, user, allowed, hidden := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellJSON(user, http.MethodPost, "/api/webshell/exec", map[string]interface{}{
		"url":           hidden.URL,
		"connection_id": hidden.ID,
		"command":       "id",
	}, handler.Exec)
	if w.Code != http.StatusForbidden {
		t.Fatalf("hidden connection status = %d, want %d: %s", w.Code, http.StatusForbidden, w.Body.String())
	}

	w = performWebshellJSON(user, http.MethodPost, "/api/webshell/exec", map[string]interface{}{
		"url":           hidden.URL,
		"connection_id": allowed.ID,
		"command":       "id",
	}, handler.Exec)
	if w.Code != http.StatusForbidden {
		t.Fatalf("mismatched URL status = %d, want %d: %s", w.Code, http.StatusForbidden, w.Body.String())
	}
}

func TestWebshellExecAllowsAdHocURLWithoutConnectionID(t *testing.T) {
	gin.SetMode(gin.TestMode)
	_, user, _, _ := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), nil)
	// Ad-hoc probe (connectivity test before save) must not be rejected as "无权访问"
	// for a session that holds webshell:connect-unsaved. The target URL will fail
	// to connect; we only assert auth allows the request through.
	w := performWebshellJSONWithPerms(user, http.MethodPost, "/api/webshell/exec", map[string]interface{}{
		"url": "http://127.0.0.1:1/admin", "command": "id",
	}, handler.Exec, map[string]bool{"webshell:write": true, "webshell:connect-unsaved": true})
	if w.Code == http.StatusForbidden {
		t.Fatalf("ad-hoc URL status = %d, want non-403: %s", w.Code, w.Body.String())
	}
	var resp ExecResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v body=%s", err, w.Body.String())
	}
	if resp.OK {
		t.Fatalf("expected connection failure for closed port, got ok=true")
	}
}

func TestWebshellExecRejectsAdHocWithoutConnectUnsavedPermission(t *testing.T) {
	gin.SetMode(gin.TestMode)
	_, user, _, _ := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), nil)
	// Omitting connection_id bypasses the per-connection ownership ACL and
	// uses the caller's own url/password, reaching any host the server can
	// reach. webshell:write is granted to Operator by default, so that alone
	// must not be sufficient.
	w := performWebshellJSON(user, http.MethodPost, "/api/webshell/exec", map[string]interface{}{
		"url": "http://169.254.169.254/latest/meta-data/", "command": "id",
	}, handler.Exec)
	if w.Code != http.StatusForbidden {
		t.Fatalf("ad-hoc URL with only webshell:write status = %d, want %d: %s",
			w.Code, http.StatusForbidden, w.Body.String())
	}
}

func TestWebshellExecRejectsAdHocWithoutWritePermission(t *testing.T) {
	gin.SetMode(gin.TestMode)
	user := &database.RBACUser{ID: "u_ro", Username: "readonly"}
	handler := NewWebShellHandler(zap.NewNop(), nil)
	payload, _ := json.Marshal(map[string]interface{}{
		"url": "http://127.0.0.1/admin", "command": "id",
	})
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/api/webshell/exec", bytes.NewReader(payload))
	c.Request.Header.Set("Content-Type", "application/json")
	c.Set(security.ContextSessionKey, security.Session{
		UserID:      user.ID,
		Username:    user.Username,
		Permissions: map[string]bool{"webshell:read": true},
		Scope:       database.RBACScopeAssigned,
	})
	handler.Exec(c)
	if w.Code != http.StatusForbidden {
		t.Fatalf("status = %d, want %d: %s", w.Code, http.StatusForbidden, w.Body.String())
	}
}

func TestWebshellFileOpRequiresConnectionAccessWhenConnectionIDProvided(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, user, _, hidden := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellJSON(user, http.MethodPost, "/api/webshell/file", map[string]interface{}{
		"url":           hidden.URL,
		"connection_id": hidden.ID,
		"action":        "list",
		"path":          ".",
	}, handler.FileOp)
	if w.Code != http.StatusForbidden {
		t.Fatalf("status = %d, want %d: %s", w.Code, http.StatusForbidden, w.Body.String())
	}
}

func TestWebshellConnectionEndpointsRejectForeignIDs(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, user, _, hidden := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), db)

	tests := []struct {
		name   string
		method string
		path   string
		body   map[string]interface{}
		fn     gin.HandlerFunc
	}{
		{"update", http.MethodPut, "/api/webshell/connections/" + hidden.ID, map[string]interface{}{"url": hidden.URL}, handler.UpdateConnection},
		{"delete", http.MethodDelete, "/api/webshell/connections/" + hidden.ID, nil, handler.DeleteConnection},
		{"get state", http.MethodGet, "/api/webshell/connections/" + hidden.ID + "/state", nil, handler.GetConnectionState},
		{"save state", http.MethodPut, "/api/webshell/connections/" + hidden.ID + "/state", map[string]interface{}{"state": map[string]interface{}{}}, handler.SaveConnectionState},
		{"ai history", http.MethodGet, "/api/webshell/connections/" + hidden.ID + "/ai-history", nil, handler.GetAIHistory},
		{"ai conversations", http.MethodGet, "/api/webshell/connections/" + hidden.ID + "/ai-conversations", nil, handler.ListAIConversations},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			w := performWebshellIDJSON(user, tc.method, tc.path, hidden.ID, tc.body, tc.fn)
			if w.Code != http.StatusForbidden {
				t.Fatalf("status = %d, want %d: %s", w.Code, http.StatusForbidden, w.Body.String())
			}
		})
	}
}

func TestWebshellAPIRedactsPasswordAndBlankUpdatePreservesIt(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, user, allowed, _ := setupWebshellRBACTest(t)
	handler := NewWebShellHandler(zap.NewNop(), db)

	w := performWebshellJSON(user, http.MethodGet, "/api/webshell/connections", nil, handler.ListConnections)
	if w.Code != http.StatusOK {
		t.Fatalf("list status = %d: %s", w.Code, w.Body.String())
	}
	var list []database.WebShellConnection
	if err := json.Unmarshal(w.Body.Bytes(), &list); err != nil {
		t.Fatal(err)
	}
	if len(list) != 1 || list[0].ID != allowed.ID || list[0].Password != "" {
		t.Fatalf("list leaked or omitted connection: %#v", list)
	}

	w = performWebshellIDJSON(user, http.MethodPut, "/api/webshell/connections/"+allowed.ID, allowed.ID, map[string]interface{}{
		"url": allowed.URL, "type": allowed.Type, "method": allowed.Method, "cmd_param": allowed.CmdParam,
	}, handler.UpdateConnection)
	if w.Code != http.StatusOK {
		t.Fatalf("update status = %d: %s", w.Code, w.Body.String())
	}
	var response database.WebShellConnection
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatal(err)
	}
	if response.Password != "" {
		t.Fatalf("update response leaked password: %#v", response)
	}
	stored, err := db.GetWebshellConnection(allowed.ID)
	if err != nil || stored == nil || stored.Password != "allowed-secret" {
		t.Fatalf("blank password did not preserve stored credential: conn=%#v err=%v", stored, err)
	}
}

func setupWebshellRBACTest(t *testing.T) (*database.DB, *database.RBACUser, *database.WebShellConnection, *database.WebShellConnection) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "webshell-rbac.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	user, err := db.CreateRBACUser("operator1", "Operator One", "hash", true, nil)
	if err != nil {
		t.Fatalf("CreateRBACUser: %v", err)
	}
	allowed := &database.WebShellConnection{
		ID:        "ws_allowed",
		URL:       "http://127.0.0.1/allowed.php",
		Password:  "allowed-secret",
		Type:      "php",
		Method:    "post",
		CmdParam:  "cmd",
		CreatedAt: time.Now(),
	}
	hidden := &database.WebShellConnection{
		ID:        "ws_hidden",
		URL:       "http://127.0.0.1/hidden.php",
		Password:  "hidden-secret",
		Type:      "php",
		Method:    "post",
		CmdParam:  "cmd",
		CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(allowed); err != nil {
		t.Fatalf("CreateWebshellConnection allowed: %v", err)
	}
	if err := db.CreateWebshellConnection(hidden); err != nil {
		t.Fatalf("CreateWebshellConnection hidden: %v", err)
	}
	if err := db.AssignResourceToUser(user.ID, "webshell", allowed.ID); err != nil {
		t.Fatalf("AssignResourceToUser: %v", err)
	}
	return db, user, allowed, hidden
}

func performWebshellJSON(user *database.RBACUser, method, path string, body map[string]interface{}, handler gin.HandlerFunc) *httptest.ResponseRecorder {
	return performWebshellJSONWithPerms(user, method, path, body, handler, nil)
}

// performWebshellJSONWithPerms runs the handler with webshell:write already
// granted and any extra permission layered on top, so a test can model a
// session that also holds an admin-only capability.
func performWebshellJSONWithPerms(user *database.RBACUser, method, path string, body map[string]interface{}, handler gin.HandlerFunc, extra map[string]bool) *httptest.ResponseRecorder {
	payload, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, path, bytes.NewReader(payload))
	c.Request.Header.Set("Content-Type", "application/json")
	perms := map[string]bool{"webshell:write": true}
	for k, v := range extra {
		perms[k] = v
	}
	c.Set(security.ContextSessionKey, security.Session{
		UserID:      user.ID,
		Username:    user.Username,
		Permissions: perms,
		Scope:       database.RBACScopeAssigned,
	})
	handler(c)
	return w
}

func performWebshellIDJSON(user *database.RBACUser, method, path, id string, body map[string]interface{}, handler gin.HandlerFunc) *httptest.ResponseRecorder {
	payload, _ := json.Marshal(body)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, path, bytes.NewReader(payload))
	c.Request.Header.Set("Content-Type", "application/json")
	c.Params = gin.Params{{Key: "id", Value: id}}
	c.Set(security.ContextSessionKey, security.Session{
		UserID:      user.ID,
		Username:    user.Username,
		Permissions: map[string]bool{"webshell:read": true, "webshell:write": true, "webshell:delete": true},
		Scope:       database.RBACScopeAssigned,
	})
	handler(c)
	return w
}
