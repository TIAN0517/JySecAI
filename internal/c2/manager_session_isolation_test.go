package c2

import (
	"errors"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestIngestCheckInCannotMoveImplantAcrossListeners(t *testing.T) {
	db, err := database.NewDB(filepath.Join(t.TempDir(), "c2.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	for i, id := range []string{"l_original", "l_attacker"} {
		if err := db.CreateC2Listener(&database.C2Listener{
			ID: id, Name: id, Type: string(ListenerTypeHTTPBeacon), BindHost: "127.0.0.1",
			BindPort: 9000 + i, Status: "stopped", CreatedAt: time.Now(),
		}); err != nil {
			t.Fatal(err)
		}
	}
	mgr := NewManager(db, zap.NewNop(), filepath.Join(t.TempDir(), "store"))
	req := ImplantCheckInRequest{ImplantUUID: "shared-self-reported-id", Hostname: "original", OS: "linux"}
	created, err := mgr.IngestCheckIn("l_original", req)
	if err != nil {
		t.Fatal(err)
	}
	req.Hostname = "attacker-controlled"
	_, err = mgr.IngestCheckIn("l_attacker", req)
	var common *CommonError
	if !errors.As(err, &common) || common.Code != "implant_listener_mismatch" {
		t.Fatalf("cross-listener check-in was not rejected precisely: %v", err)
	}
	stored, err := db.GetC2Session(created.ID)
	if err != nil {
		t.Fatal(err)
	}
	if stored.ListenerID != "l_original" || stored.Hostname != "original" {
		t.Fatalf("original session was modified: %+v", stored)
	}
}
