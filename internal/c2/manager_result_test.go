package c2

import (
	"errors"
	"path/filepath"
	"testing"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestIngestTaskResultValidatesOwnershipAndState(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if err := db.CreateC2Listener(&database.C2Listener{
		ID: "l_owned", Name: "owned", Type: string(ListenerTypeHTTPBeacon),
	}); err != nil {
		t.Fatal(err)
	}
	if err := db.UpsertC2Session(&database.C2Session{
		ID: "s_owned", ListenerID: "l_owned", ImplantUUID: "implant_owned", Status: "active",
	}); err != nil {
		t.Fatal(err)
	}
	for _, task := range []*database.C2Task{
		{ID: "t_sent", SessionID: "s_owned", TaskType: "exec", Status: string(TaskSent)},
		{ID: "t_queued", SessionID: "s_owned", TaskType: "exec", Status: string(TaskQueued)},
	} {
		if err := db.CreateC2Task(task); err != nil {
			t.Fatal(err)
		}
	}

	mgr := NewManager(db, zap.NewNop(), filepath.Join(t.TempDir(), "c2store"))
	if err := mgr.IngestTaskResultForSession(TaskResultReport{TaskID: "t_sent", Success: true}, "s_other"); !errors.Is(err, ErrTaskNotFound) {
		t.Fatalf("expected session ownership rejection, got %v", err)
	}
	if err := mgr.IngestTaskResultForListener(TaskResultReport{TaskID: "t_sent", Success: true}, "l_other"); !errors.Is(err, ErrTaskNotFound) {
		t.Fatalf("expected listener ownership rejection, got %v", err)
	}
	err = mgr.IngestTaskResultForSession(TaskResultReport{TaskID: "t_queued", Success: true}, "s_owned")
	var commonErr *CommonError
	if !errors.As(err, &commonErr) || commonErr.HTTP != 409 {
		t.Fatalf("expected queued task state rejection, got %v", err)
	}
}
