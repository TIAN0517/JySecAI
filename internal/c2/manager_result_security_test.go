package c2

import (
	"errors"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func newResultSecurityManager(t *testing.T) (*Manager, *database.DB) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	for _, listenerID := range []string{"l_owner", "l_other"} {
		if err := db.CreateC2Listener(&database.C2Listener{
			ID: listenerID, Name: listenerID, Type: string(ListenerTypeHTTPBeacon),
			BindHost: "127.0.0.1", BindPort: 8080, Status: "stopped", CreatedAt: time.Now(),
		}); err != nil {
			t.Fatal(err)
		}
	}
	now := time.Now()
	for _, session := range []*database.C2Session{
		{ID: "s_owner", ListenerID: "l_owner", ImplantUUID: "implant-owner", Status: string(SessionActive), FirstSeenAt: now, LastCheckIn: now},
		{ID: "s_other", ListenerID: "l_other", ImplantUUID: "implant-other", Status: string(SessionActive), FirstSeenAt: now, LastCheckIn: now},
	} {
		if err := db.UpsertC2Session(session); err != nil {
			t.Fatal(err)
		}
	}
	return NewManager(db, zap.NewNop(), filepath.Join(t.TempDir(), "store")), db
}

func createResultTask(t *testing.T, db *database.DB, id, sessionID string, status TaskStatus) {
	t.Helper()
	if err := db.CreateC2Task(&database.C2Task{
		ID: id, SessionID: sessionID, TaskType: string(TaskTypeExec), Status: string(status), CreatedAt: time.Now(),
	}); err != nil {
		t.Fatal(err)
	}
}

func TestIngestTaskResultRequiresActiveStateAndExactSession(t *testing.T) {
	mgr, db := newResultSecurityManager(t)
	createResultTask(t, db, "t_session_ok", "s_owner", TaskSent)

	if err := mgr.IngestTaskResultForSession("s_other", TaskResultReport{TaskID: "t_session_ok", Success: true}); err == nil {
		t.Fatal("wrong session unexpectedly accepted task result")
	}
	if err := mgr.IngestTaskResultForSession("s_owner", TaskResultReport{TaskID: "t_session_ok", Success: true, Output: "ok"}); err != nil {
		t.Fatalf("owner result rejected: %v", err)
	}
	task, err := db.GetC2Task("t_session_ok")
	if err != nil || task == nil || task.Status != string(TaskSuccess) || task.ResultText != "ok" {
		t.Fatalf("result not persisted correctly: task=%+v err=%v", task, err)
	}
	if err := mgr.IngestTaskResultForSession("s_owner", TaskResultReport{TaskID: "t_session_ok", Success: true}); err == nil {
		t.Fatal("completed task replay unexpectedly accepted")
	}

	for _, status := range []TaskStatus{TaskQueued, TaskSuccess, TaskFailed, TaskCancelled} {
		id := "t_state_" + string(status)
		createResultTask(t, db, id, "s_owner", status)
		err := mgr.IngestTaskResultForSession("s_owner", TaskResultReport{TaskID: id, Success: true})
		var common *CommonError
		if !errors.As(err, &common) || common.Code != "invalid_task_state" || common.HTTP != 409 {
			t.Fatalf("status %s: got %v, want invalid_task_state", status, err)
		}
	}
}

func TestIngestTaskResultRequiresExactListenerOwnership(t *testing.T) {
	mgr, db := newResultSecurityManager(t)
	createResultTask(t, db, "t_listener_ok", "s_owner", TaskRunning)

	if err := mgr.IngestTaskResultForListener("l_other", TaskResultReport{TaskID: "t_listener_ok", Success: true}); err == nil {
		t.Fatal("wrong listener unexpectedly accepted task result")
	}
	if err := mgr.IngestTaskResultForListener("l_owner", TaskResultReport{TaskID: "t_listener_ok", Success: true}); err != nil {
		t.Fatalf("owner listener result rejected: %v", err)
	}
}
