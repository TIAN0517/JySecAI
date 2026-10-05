package handler

import (
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/database"
	"jysecai/internal/knowledge"
	"jysecai/internal/security"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// Retrieval logs carry the user's raw prompt and the knowledge items it hit.
// GetRetrievalLogs used to pass the conversationId query param straight through
// to SQL and, with no param at all, returned every tenant's rows — knowledge:read
// is granted to the viewer role.

func newKnowledgeRBACHandler(t *testing.T) (*KnowledgeHandler, *knowledge.Manager, *database.DB) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "knowledge-rbac.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	mgr := knowledge.NewManager(db.DB, filepath.Join(t.TempDir(), "kb"), zap.NewNop())
	return NewKnowledgeHandler(mgr, nil, nil, db, zap.NewNop()), mgr, db
}

func callKnowledgeAs(t *testing.T, userID, scope, method, target, id string, fn gin.HandlerFunc) *httptest.ResponseRecorder {
	t.Helper()
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, target, nil)
	c.Params = gin.Params{{Key: "id", Value: id}}
	c.Set(security.ContextSessionKey, security.Session{UserID: userID, Scope: scope})
	fn(c)
	return w
}

// The no-parameter case is the worst one: it returned the whole table.
func TestGetRetrievalLogsWithoutParamsReturnsNothingToScopedUser(t *testing.T) {
	h, mgr, db := newKnowledgeRBACHandler(t)
	other, err := db.CreateConversation("victim thread", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	// message_id has a FK to messages(id), so a real message is required.
	msg, err := db.AddMessage(other.ID, "user", "victim's confidential prompt", nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := mgr.LogRetrieval(other.ID, msg.ID, "victim's confidential prompt", "", []string{"k1"}); err != nil {
		t.Fatal(err)
	}

	me, err := db.CreateRBACUser("kb-viewer", "KB Viewer", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}

	w := callKnowledgeAs(t, me.ID, database.RBACScopeAssigned, http.MethodGet, "/retrieval-logs", "", h.GetRetrievalLogs)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
	if strings.Contains(w.Body.String(), "confidential") {
		t.Fatalf("scoped user received another tenant's prompt: %s", w.Body.String())
	}
}

// Knowing a conversation id must not be enough.
func TestGetRetrievalLogsRejectsForeignConversationID(t *testing.T) {
	h, mgr, db := newKnowledgeRBACHandler(t)
	other, err := db.CreateConversation("victim thread", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	// message_id has a FK to messages(id), so a real message is required.
	msg, err := db.AddMessage(other.ID, "user", "victim's confidential prompt", nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := mgr.LogRetrieval(other.ID, msg.ID, "victim's confidential prompt", "", []string{"k1"}); err != nil {
		t.Fatal(err)
	}

	me, err := db.CreateRBACUser("kb-viewer-2", "KB Viewer", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}

	target := "/retrieval-logs?conversationId=" + other.ID
	w := callKnowledgeAs(t, me.ID, database.RBACScopeAssigned, http.MethodGet, target, "", h.GetRetrievalLogs)
	if w.Code != http.StatusForbidden {
		t.Fatalf("status=%d, want 403; body=%s", w.Code, w.Body.String())
	}
	if strings.Contains(w.Body.String(), "confidential") {
		t.Fatalf("targeted IDOR leaked the prompt: %s", w.Body.String())
	}
}

// The legitimate owner must still see their own logs.
func TestGetRetrievalLogsAllowsOwnConversation(t *testing.T) {
	h, mgr, db := newKnowledgeRBACHandler(t)
	mine, err := db.CreateConversation("my thread", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	msg, err := db.AddMessage(mine.ID, "user", "my own prompt", nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := mgr.LogRetrieval(mine.ID, msg.ID, "my own prompt", "", []string{"k1"}); err != nil {
		t.Fatal(err)
	}
	me, err := db.CreateRBACUser("kb-owner", "KB Owner", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := db.SetResourceOwner("conversation", mine.ID, me.ID); err != nil {
		t.Fatal(err)
	}

	w := callKnowledgeAs(t, me.ID, database.RBACScopeOwn, http.MethodGet, "/retrieval-logs", "", h.GetRetrievalLogs)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
	if !strings.Contains(w.Body.String(), "my own prompt") {
		t.Fatalf("owner lost access to their own logs: %s", w.Body.String())
	}
}

// DeleteRetrievalLog had no ownership check at all — knowledge:delete is
// admin-only, but the boundary should not rest on that alone, and the same
// handler shape is what the read path leaked through.
func TestDeleteRetrievalLogRejectsForeignLog(t *testing.T) {
	h, mgr, db := newKnowledgeRBACHandler(t)
	other, err := db.CreateConversation("victim thread", database.ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	// message_id has a FK to messages(id), so a real message is required.
	msg, err := db.AddMessage(other.ID, "user", "victim's confidential prompt", nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := mgr.LogRetrieval(other.ID, msg.ID, "victim's confidential prompt", "", []string{"k1"}); err != nil {
		t.Fatal(err)
	}
	logs, err := mgr.GetRetrievalLogs(other.ID, "", 10)
	if err != nil || len(logs) == 0 {
		t.Fatalf("could not read back the seeded log: %v", err)
	}
	victimLogID := logs[0].ID

	me, err := db.CreateRBACUser("kb-deleter", "KB Deleter", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}

	w := callKnowledgeAs(t, me.ID, database.RBACScopeAssigned, http.MethodDelete, "/retrieval-logs/"+victimLogID, victimLogID, h.DeleteRetrievalLog)
	if w.Code != http.StatusForbidden {
		t.Fatalf("status=%d, want 403; body=%s", w.Code, w.Body.String())
	}
	if _, err := mgr.GetRetrievalLogConversationID(victimLogID); err != nil {
		t.Fatalf("the victim's log was deleted anyway: %v", err)
	}
}
