package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"jysecai/internal/database"
	"jysecai/internal/security"
)

type recordingVerifyQueue struct {
	title string
	owner string
	tasks []string
}

func (r *recordingVerifyQueue) RunVerificationQueue(title, ownerUserID, aiChannelID string, tasks []string) (string, error) {
	r.title = title
	r.owner = ownerUserID
	r.tasks = append([]string(nil), tasks...)
	return "queue-pending", nil
}

func TestDispatchPendingVerificationSkipsCritical(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "pending-verify.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	for _, item := range []database.Vulnerability{
		{Title: "open-medium", Type: "xss", Target: "https://app.example/a", Severity: "medium", Status: database.VulnerabilityStatusOpen},
		{Title: "open-critical", Type: "rce", Target: "https://app.example/b", Severity: "critical", Status: database.VulnerabilityStatusOpen},
	} {
		if _, err := db.CreateVulnerability(&item); err != nil {
			t.Fatal(err)
		}
	}
	queue := &recordingVerifyQueue{}
	h := NewVulnerabilityHandler(db, zap.NewNop())
	h.SetAutoVerifyQueueRunner(queue)

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = httptest.NewRequest(http.MethodPost, "/api/vulnerability-pending/approve", strings.NewReader(`{}`))
	ctx.Request.Header.Set("Content-Type", "application/json")
	ctx.Set(security.ContextSessionKey, security.Session{UserID: "operator", Scope: database.RBACScopeAll})
	h.DispatchPendingVerification(ctx)

	if recorder.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", recorder.Code, recorder.Body.String())
	}
	var body struct {
		Dispatched int      `json:"dispatched"`
		QueueID    string   `json:"queueId"`
		IDs        []string `json:"ids"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if body.Dispatched != 1 || body.QueueID != "queue-pending" || len(queue.tasks) != 1 {
		t.Fatalf("body=%s tasks=%d", recorder.Body.String(), len(queue.tasks))
	}
	if strings.Contains(queue.tasks[0], "open-critical") || !strings.Contains(queue.tasks[0], "open-medium") {
		t.Fatalf("queued prompt=%s", queue.tasks[0])
	}
}
