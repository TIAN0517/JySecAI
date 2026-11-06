package database

import (
	"path/filepath"
	"testing"

	"go.uber.org/zap"
)

func newRedirectVerifyTestDB(t *testing.T) *DB {
	t.Helper()
	dbPath := filepath.Join(t.TempDir(), "redirect-verify.db")
	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}

func TestRedirectVerifyRunLifecycle(t *testing.T) {
	db := newRedirectVerifyTestDB(t)

	run := &RedirectVerifyRun{
		Status:         RedirectVerifyStatusPending,
		Endpoints:      []string{"https://cb.example.com/a", "https://cb.example.com/b"},
		Method:         "GET",
		Concurrency:    4,
		Total:          2,
		ProjectID:      "proj-1",
		ConversationID: "conv-1",
		OwnerUserID:    "user-1",
		AutoRecord:     true,
	}
	if err := db.CreateRedirectVerifyRun(run); err != nil {
		t.Fatal(err)
	}
	if run.ID == "" {
		t.Fatal("run id must be assigned")
	}

	loaded, err := db.GetRedirectVerifyRun(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(loaded.Endpoints) != 2 || loaded.Endpoints[1] != "https://cb.example.com/b" {
		t.Fatalf("unexpected endpoints: %#v", loaded.Endpoints)
	}
	if !loaded.AutoRecord {
		t.Fatal("auto_record must round-trip")
	}
	if loaded.Total != 2 || loaded.Completed != 0 || loaded.Confirmed != 0 {
		t.Fatalf("unexpected counters: %#v", loaded)
	}

	if err := db.StartRedirectVerifyRun(run.ID); err != nil {
		t.Fatal(err)
	}
	if err := db.UpdateRedirectVerifyRunProgress(run.ID, 1, 1, RedirectVerifyStatusRunning); err != nil {
		t.Fatal(err)
	}
	loaded, err = db.GetRedirectVerifyRun(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Status != RedirectVerifyStatusRunning || loaded.Completed != 1 || loaded.Confirmed != 1 {
		t.Fatalf("unexpected progress: %#v", loaded)
	}
	if loaded.StartedAt.IsZero() {
		t.Fatal("started_at must be set")
	}

	if err := db.FinishRedirectVerifyRun(run.ID, RedirectVerifyStatusCompleted, ""); err != nil {
		t.Fatal(err)
	}
	loaded, err = db.GetRedirectVerifyRun(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Status != RedirectVerifyStatusCompleted || loaded.CompletedAt.IsZero() {
		t.Fatalf("unexpected final state: %#v", loaded)
	}
}

func TestRedirectVerifyRunCancelRequest(t *testing.T) {
	db := newRedirectVerifyTestDB(t)
	run := &RedirectVerifyRun{Status: RedirectVerifyStatusRunning, Endpoints: []string{"https://cb.example.com/a"}}
	if err := db.CreateRedirectVerifyRun(run); err != nil {
		t.Fatal(err)
	}

	asked, err := db.RequestRedirectVerifyRunCancel(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if !asked {
		t.Fatal("expected cancel request to be accepted")
	}
	flagged, err := db.IsRedirectVerifyRunCancelAsked(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if !flagged {
		t.Fatal("cancel flag must be persisted")
	}

	// 同一個批次重複取消不應再被視為有效請求。
	again, err := db.RequestRedirectVerifyRunCancel(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if again {
		t.Fatal("duplicate cancel request must be rejected")
	}
}

func TestRedirectVerifyResultsPersist(t *testing.T) {
	db := newRedirectVerifyTestDB(t)
	run := &RedirectVerifyRun{Status: RedirectVerifyStatusRunning, Endpoints: []string{"https://cb.example.com/a"}}
	if err := db.CreateRedirectVerifyRun(run); err != nil {
		t.Fatal(err)
	}

	first := &RedirectVerifyResult{
		RunID:      run.ID,
		URL:        "https://victim.example/go",
		Confirmed:  true,
		Param:      "url",
		RequestURL: "https://victim.example/go?url=https://cb.example.com/a",
		Status:     302,
		Location:   "https://cb.example.com/a",
	}
	if err := db.AppendRedirectVerifyResult(first); err != nil {
		t.Fatal(err)
	}
	second := &RedirectVerifyResult{
		RunID:  run.ID,
		URL:    "https://other.example/go",
		Status: 200,
		Error:  "timeout",
	}
	if err := db.AppendRedirectVerifyResult(second); err != nil {
		t.Fatal(err)
	}

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	if !results[0].Confirmed || results[0].Param != "url" || results[0].Status != 302 {
		t.Fatalf("unexpected first result: %#v", results[0])
	}
	if results[1].Confirmed {
		t.Fatalf("unexpected second result: %#v", results[1])
	}

	if err := db.SetRedirectVerifyResultVulnerability(first.ID, "vuln-1"); err != nil {
		t.Fatal(err)
	}
	results, err = db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if results[0].VulnerabilityID != "vuln-1" {
		t.Fatalf("vulnerability link not persisted: %#v", results[0])
	}
}

func TestListRedirectVerifyRunsForAccessIsFailClosed(t *testing.T) {
	db := newRedirectVerifyTestDB(t)
	if err := db.CreateRedirectVerifyRun(&RedirectVerifyRun{
		Status:      RedirectVerifyStatusCompleted,
		OwnerUserID: "user-1",
	}); err != nil {
		t.Fatal(err)
	}

	// 解析不出呼叫者時看不到任何資料。
	runs, err := db.ListRedirectVerifyRunsForAccess(50, "", "assigned")
	if err != nil {
		t.Fatal(err)
	}
	if len(runs) != 0 {
		t.Fatalf("expected no visible runs, got %d", len(runs))
	}

	runs, err = db.ListRedirectVerifyRunsForAccess(50, "user-1", "assigned")
	if err != nil {
		t.Fatal(err)
	}
	if len(runs) != 1 {
		t.Fatalf("expected 1 visible run, got %d", len(runs))
	}

	runs, err = db.ListRedirectVerifyRunsForAccess(50, "other-user", "assigned")
	if err != nil {
		t.Fatal(err)
	}
	if len(runs) != 0 {
		t.Fatalf("expected 0 visible runs for other user, got %d", len(runs))
	}
}
