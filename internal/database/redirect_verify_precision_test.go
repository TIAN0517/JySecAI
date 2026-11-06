package database

import (
	"testing"

	"jysecai/internal/redirect"
)

// 新欄位的落地測試：批次層的 repeat／注入點統計／注入點清單，
// 結果層的證據等級與精準度指標。
//
// 這些欄位是「實不實、精不精準」的原始資料 —— 少了任何一個，
// 報告裡的精準度數字就會變成猜的。

func TestRedirectVerifyRunPersistsPrecisionFields(t *testing.T) {
	db := newRedirectVerifyTestDB(t)

	points := []redirect.InjectionPoint{
		{Kind: redirect.InjectionKindScriptSrc, Tag: "script", Attr: "src", URL: "https://evil.tld/p.js", Page: "https://site.tld/"},
		{Kind: redirect.InjectionKindJSString, Tag: "script", Attr: "text", URL: "https://evil.tld/x", Page: "https://site.tld/"},
	}
	run := &RedirectVerifyRun{
		Status:               RedirectVerifyStatusPending,
		Endpoints:            []string{"https://cb.example.com/a"},
		Encoding:             "none",
		Repeat:               3,
		InjectionCount:       2,
		ThirdPartyInjections: 2,
		Injections:           points,
	}
	if err := db.CreateRedirectVerifyRun(run); err != nil {
		t.Fatal(err)
	}
	if err := db.UpdateRedirectVerifyRunInjections(run.ID, 2, 2, points); err != nil {
		t.Fatal(err)
	}

	loaded, err := db.GetRedirectVerifyRun(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Repeat != 3 {
		t.Fatalf("repeat must round-trip, got %d", loaded.Repeat)
	}
	if loaded.InjectionCount != 2 || loaded.ThirdPartyInjections != 2 {
		t.Fatalf("injection counters must round-trip: %#v", loaded)
	}
	if len(loaded.Injections) != 2 {
		t.Fatalf("injection points must round-trip, got %d", len(loaded.Injections))
	}
	if loaded.Injections[0].Kind != redirect.InjectionKindScriptSrc {
		t.Fatalf("unexpected injection point: %#v", loaded.Injections[0])
	}
	if loaded.Injections[0].URL != "https://evil.tld/p.js" {
		t.Fatalf("injection URL must round-trip: %#v", loaded.Injections[0])
	}
}

func TestRedirectVerifyResultPersistsEvidenceFields(t *testing.T) {
	db := newRedirectVerifyTestDB(t)
	run := &RedirectVerifyRun{Status: RedirectVerifyStatusRunning, Endpoints: []string{"https://cb.example.com/a"}}
	if err := db.CreateRedirectVerifyRun(run); err != nil {
		t.Fatal(err)
	}

	confirmed := &RedirectVerifyResult{
		RunID:       run.ID,
		URL:         "https://victim.example/go?next=/x",
		Confirmed:   true,
		Param:       "next",
		OwnParam:    "next",
		ParamsTried: []string{"next", "url"},
		Evidence:    redirect.EvidenceLocation,
		OwnParamHit: true,
		Attempts:    3,
		Stable:      true,
	}
	if err := db.AppendRedirectVerifyResult(confirmed); err != nil {
		t.Fatal(err)
	}
	echo := &RedirectVerifyResult{
		RunID:    run.ID,
		URL:      "https://other.example/echo?url=/x",
		Evidence: redirect.EvidenceBodyEcho,
		BodyEcho: true,
		Attempts: 1,
		Stable:   true,
		Param:    "url",
		OwnParam: "url",
	}
	if err := db.AppendRedirectVerifyResult(echo); err != nil {
		t.Fatal(err)
	}

	results, err := db.ListRedirectVerifyResults(run.ID)
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	if results[0].Evidence != redirect.EvidenceLocation {
		t.Fatalf("evidence must round-trip: %#v", results[0])
	}
	if !results[0].OwnParamHit {
		t.Fatalf("own_param_hit must round-trip: %#v", results[0])
	}
	if results[0].Attempts != 3 || !results[0].Stable {
		t.Fatalf("attempts/stable must round-trip: %#v", results[0])
	}
	if results[1].Evidence != redirect.EvidenceBodyEcho || !results[1].BodyEcho {
		t.Fatalf("body echo must round-trip: %#v", results[1])
	}
	if results[1].Confirmed {
		t.Fatalf("body echo must never be confirmed: %#v", results[1])
	}
}

func TestRedirectVerifyRunDefaultsRepeatToOne(t *testing.T) {
	db := newRedirectVerifyTestDB(t)
	// 舊資料列沒有 repeat 欄位 → 讀出來必須是 1（不重複），不是 0。
	if _, err := db.Exec(`INSERT INTO redirect_verify_runs (id, status, endpoints, created_at, updated_at)
		VALUES ('legacy-1', 'completed', 'https://cb.example.com/a', '2026-01-01 00:00:00', '2026-01-01 00:00:00')`); err != nil {
		t.Fatal(err)
	}
	run, err := db.GetRedirectVerifyRun("legacy-1")
	if err != nil {
		t.Fatal(err)
	}
	if run.Repeat != 1 {
		t.Fatalf("legacy run must report repeat=1, got %d", run.Repeat)
	}
}
