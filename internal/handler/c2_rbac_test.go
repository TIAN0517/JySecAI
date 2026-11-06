package handler

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/c2"
	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func newC2RBACHandler(t *testing.T) (*C2Handler, *database.RBACUser) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2-handler-rbac.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	user, err := db.CreateRBACUser("assigned-user", "Assigned User", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now()
	for _, listener := range []*database.C2Listener{
		{ID: "l_allowed", Name: "allowed", Type: string(c2.ListenerTypeHTTPBeacon), BindHost: "127.0.0.1", BindPort: 9011, Status: "stopped", CreatedAt: now},
		{ID: "l_hidden", Name: "hidden", Type: string(c2.ListenerTypeHTTPBeacon), BindHost: "127.0.0.1", BindPort: 9012, Status: "stopped", CreatedAt: now},
	} {
		if err := db.CreateC2Listener(listener); err != nil {
			t.Fatal(err)
		}
	}
	if err := db.AssignResourceToUser(user.ID, "c2_listener", "l_allowed"); err != nil {
		t.Fatal(err)
	}
	for _, session := range []*database.C2Session{
		{ID: "s_allowed", ListenerID: "l_allowed", ImplantUUID: "implant-allowed", Status: string(c2.SessionActive), FirstSeenAt: now, LastCheckIn: now},
		{ID: "s_hidden", ListenerID: "l_hidden", ImplantUUID: "implant-hidden", Status: string(c2.SessionActive), FirstSeenAt: now, LastCheckIn: now},
	} {
		if err := db.UpsertC2Session(session); err != nil {
			t.Fatal(err)
		}
	}
	for _, task := range []*database.C2Task{
		{ID: "t_allowed", SessionID: "s_allowed", TaskType: string(c2.TaskTypeExec), Status: string(c2.TaskQueued), CreatedAt: now},
		{ID: "t_hidden", SessionID: "s_hidden", TaskType: string(c2.TaskTypeExec), Status: string(c2.TaskQueued), CreatedAt: now},
	} {
		if err := db.CreateC2Task(task); err != nil {
			t.Fatal(err)
		}
	}
	mgr := c2.NewManager(db, zap.NewNop(), filepath.Join(t.TempDir(), "storage"))
	return NewC2Handler(mgr, zap.NewNop()), user
}

func callC2Handler(t *testing.T, user *database.RBACUser, method, path, id, body string, fn gin.HandlerFunc) *httptest.ResponseRecorder {
	t.Helper()
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, path, bytes.NewBufferString(body))
	c.Request.Header.Set("Content-Type", "application/json")
	c.Params = gin.Params{{Key: "id", Value: id}}
	c.Set(security.ContextSessionKey, security.Session{UserID: user.ID, Scope: database.RBACScopeAssigned})
	fn(c)
	return w
}

func TestC2SingleResourceEndpointsRejectForeignIDs(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h, user := newC2RBACHandler(t)
	tests := []struct {
		name   string
		method string
		path   string
		id     string
		body   string
		fn     gin.HandlerFunc
	}{
		{"get listener", http.MethodGet, "/listeners/l_hidden", "l_hidden", "", h.GetListener},
		{"update listener", http.MethodPut, "/listeners/l_hidden", "l_hidden", `{}`, h.UpdateListener},
		{"delete listener", http.MethodDelete, "/listeners/l_hidden", "l_hidden", "", h.DeleteListener},
		{"start listener", http.MethodPost, "/listeners/l_hidden/start", "l_hidden", "", h.StartListener},
		{"stop listener", http.MethodPost, "/listeners/l_hidden/stop", "l_hidden", "", h.StopListener},
		{"get session", http.MethodGet, "/sessions/s_hidden", "s_hidden", "", h.GetSession},
		{"delete session", http.MethodDelete, "/sessions/s_hidden", "s_hidden", "", h.DeleteSession},
		{"set session sleep", http.MethodPut, "/sessions/s_hidden/sleep", "s_hidden", `{"sleep_seconds":5}`, h.SetSessionSleep},
		{"set session note", http.MethodPut, "/sessions/s_hidden/note", "s_hidden", `{"note":"secret"}`, h.SetSessionNote},
		{"get task", http.MethodGet, "/tasks/t_hidden", "t_hidden", "", h.GetTask},
		{"cancel task", http.MethodPost, "/tasks/t_hidden/cancel", "t_hidden", "", h.CancelTask},
		{"wait task", http.MethodGet, "/tasks/t_hidden/wait", "t_hidden", "", h.WaitTask},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			w := callC2Handler(t, user, tc.method, tc.path, tc.id, tc.body, tc.fn)
			if w.Code != http.StatusForbidden {
				t.Fatalf("status = %d, want 403: %s", w.Code, w.Body.String())
			}
		})
	}
}

func TestC2SingleResourceEndpointsAllowAssignedHierarchy(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h, user := newC2RBACHandler(t)
	for _, tc := range []struct {
		name string
		id   string
		fn   gin.HandlerFunc
	}{
		{"listener", "l_allowed", h.GetListener},
		{"session", "s_allowed", h.GetSession},
		{"task", "t_allowed", h.GetTask},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := callC2Handler(t, user, http.MethodGet, "/"+tc.id, tc.id, "", tc.fn)
			if w.Code != http.StatusOK {
				t.Fatalf("status = %d, want 200: %s", w.Code, w.Body.String())
			}
		})
	}
}
