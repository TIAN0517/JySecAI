package handler

import (
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/database"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// auditFilterForAccess used to be `if session, ok := ...; ok && ...`, which
// left filter.Actor empty when the session could not be resolved. Since
// buildAuditLogsWhere only emits `actor = ?` for a non-empty actor, the query
// degraded to WHERE 1=1 and returned every tenant's audit rows. GetLog in the
// same file already used the correct `!ok ||` rejection.

func newAuditRBACHandler(t *testing.T) (*AuditHandler, *database.DB) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "audit-rbac.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	for _, actor := range []string{"alice", "bob"} {
		if err := db.AppendAuditLog(&database.AuditLog{
			ID: "log-" + actor, Actor: actor, Action: "test", Level: "info", CreatedAt: time.Now(),
		}); err != nil {
			t.Fatalf("AppendAuditLog(%s): %v", actor, err)
		}
	}
	return NewAuditHandler(db, nil, zap.NewNop()), db
}

func callAuditWithoutSession(t *testing.T, fn gin.HandlerFunc) *httptest.ResponseRecorder {
	t.Helper()
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/audit/logs", nil)
	fn(c)
	return w
}

func TestAuditListLogsRejectsMissingSession(t *testing.T) {
	h, _ := newAuditRBACHandler(t)
	for name, fn := range map[string]gin.HandlerFunc{
		"ListLogs":   h.ListLogs,
		"Summary":    h.Summary,
		"ExportLogs": h.ExportLogs,
	} {
		w := callAuditWithoutSession(t, fn)
		if w.Code != http.StatusUnauthorized {
			t.Errorf("%s: status=%d, want 401; body=%s", name, w.Code, w.Body.String())
		}
	}
}

// A scoped caller must see only their own rows; the all-scope caller sees all.
func TestAuditListLogsScopesByActor(t *testing.T) {
	h, _ := newAuditRBACHandler(t)

	asCaller := func(userID, scope, target string) *httptest.ResponseRecorder {
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, target, nil)
		c.Set(security.ContextSessionKey, security.Session{UserID: userID, Username: userID, Scope: scope})
		h.ListLogs(c)
		return w
	}

	mine := asCaller("alice", database.RBACScopeAssigned, "/audit/logs")
	if mine.Code != http.StatusOK {
		t.Fatalf("alice status=%d body=%s", mine.Code, mine.Body.String())
	}
	if strings.Contains(mine.Body.String(), "bob") {
		t.Errorf("scoped caller received another actor's audit rows: %s", mine.Body.String())
	}
	if !strings.Contains(mine.Body.String(), "alice") {
		t.Errorf("scoped caller lost their own rows: %s", mine.Body.String())
	}

	all := asCaller("admin", database.RBACScopeAll, "/audit/logs")
	if all.Code != http.StatusOK {
		t.Fatalf("admin status=%d body=%s", all.Code, all.Body.String())
	}
	if !strings.Contains(all.Body.String(), "bob") {
		t.Errorf("all-scope caller could not see other rows: %s", all.Body.String())
	}
}
