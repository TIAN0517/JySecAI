package handler

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"jysecai/internal/database"
)

func TestStartAttachedFromScanSkipsWithoutHTTPTarget(t *testing.T) {
	h, _ := newRedirectVerifyTestHandlerWithEndpoint(t, "https://97y.me/tjneJ")
	run, err := h.StartAttachedFromScan(ScanAttachedRedirectRequest{Text: "没有网址的扫描说明"})
	if err != nil {
		t.Fatalf("StartAttachedFromScan: %v", err)
	}
	if run != nil {
		t.Fatalf("run = %#v, want nil", run)
	}
}

func TestStartAttachedFromScanSkipsOwnShortlink(t *testing.T) {
	h, _ := newRedirectVerifyTestHandlerWithEndpoint(t, "https://97y.me/tjneJ")
	run, err := h.StartAttachedFromScan(ScanAttachedRedirectRequest{Text: "请打开 https://97y.me/tjneJ"})
	if err != nil {
		t.Fatalf("StartAttachedFromScan: %v", err)
	}
	if run != nil {
		t.Fatalf("own shortlink should not be a scan seed, run=%#v", run)
	}
}

func TestStartAttachedFromScanCreatesCrawlAutoRecordRun(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`<a href="/go?url=/home">next</a>`))
	}))
	t.Cleanup(server.Close)
	h, db := newRedirectVerifyTestHandlerWithEndpoint(t, "https://97y.me/tjneJ")
	run, err := h.StartAttachedFromScan(ScanAttachedRedirectRequest{
		Text:           "扫 " + server.URL + "/login?next=/home",
		ConversationID: "conv-1",
		OwnerUserID:    "user-1",
	})
	if err != nil {
		t.Fatalf("StartAttachedFromScan: %v", err)
	}
	if run == nil {
		t.Fatal("run is nil")
	}
	if !run.CrawlEnabled || !run.AutoRecord {
		t.Fatalf("crawl=%v auto_record=%v, want both true", run.CrawlEnabled, run.AutoRecord)
	}
	if len(run.Endpoints) != 1 || run.Endpoints[0] != "https://97y.me/tjneJ" {
		t.Fatalf("endpoints = %#v", run.Endpoints)
	}
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		loaded, loadErr := db.GetRedirectVerifyRun(run.ID)
		if loadErr == nil && loaded != nil && loaded.Status != database.RedirectVerifyStatusPending {
			return
		}
		time.Sleep(50 * time.Millisecond)
	}
}
