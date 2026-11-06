package redirectverify

import (
	"testing"

	"jysecai/internal/database"
	"jysecai/internal/redirect"
)

// 精準度指標的計算：真跳轉與本文回顯要分開、命中品質要分開、穩定度要分開。

func TestComputeAccuracySeparatesEvidenceLevels(t *testing.T) {
	run := &database.RedirectVerifyRun{ID: "run-1", Total: 4}
	results := []database.RedirectVerifyResult{
		{URL: "a", Confirmed: true, Evidence: redirect.EvidenceLocation, OwnParam: "url", OwnParamHit: true, Attempts: 1, Stable: true},
		{URL: "b", Confirmed: true, Evidence: redirect.EvidenceLocation, OwnParam: "", OwnParamHit: false, Attempts: 1, Stable: true},
		{URL: "c", Confirmed: false, Evidence: redirect.EvidenceBodyEcho, BodyEcho: true, Attempts: 1, Stable: true},
		{URL: "d", Confirmed: false, Evidence: redirect.EvidenceNone, Attempts: 1, Stable: true},
	}

	accuracy := ComputeAccuracy(run, results)
	if accuracy.LocationEvidence != 2 {
		t.Fatalf("expected 2 location evidences, got %d", accuracy.LocationEvidence)
	}
	if accuracy.BodyEcho != 1 {
		t.Fatalf("expected 1 body echo, got %d", accuracy.BodyEcho)
	}
	if accuracy.Confirmed != 2 {
		t.Fatalf("expected 2 confirmed, got %d", accuracy.Confirmed)
	}
	// 偽陽性率 = body_echo / (location + body_echo) = 1/3
	if accuracy.FalsePositiveRate < 33.3 || accuracy.FalsePositiveRate > 33.4 {
		t.Fatalf("expected false positive rate ~33.3%%, got %f", accuracy.FalsePositiveRate)
	}
	if accuracy.OwnParamHit != 1 || accuracy.GuessParamHit != 1 {
		t.Fatalf("expected 1 own-param hit and 1 guess hit, got %d/%d",
			accuracy.OwnParamHit, accuracy.GuessParamHit)
	}
	if accuracy.OwnParamHitRate < 49.9 || accuracy.OwnParamHitRate > 50.1 {
		t.Fatalf("expected own param hit rate 50%%, got %f", accuracy.OwnParamHitRate)
	}
	if accuracy.StabilityRate != 0 {
		// 沒有重複探測（attempts 全部 = 1）→ 分母為 0 → 0%。
		t.Fatalf("expected stability rate 0 when nothing was repeated, got %f", accuracy.StabilityRate)
	}
}

func TestComputeAccuracyCountsStabilityOnlyForRepeatedTargets(t *testing.T) {
	run := &database.RedirectVerifyRun{ID: "run-2", Total: 2}
	results := []database.RedirectVerifyResult{
		{URL: "a", Confirmed: true, Evidence: redirect.EvidenceLocation, Attempts: 3, Stable: true},
		{URL: "b", Confirmed: false, Evidence: redirect.EvidenceNone, Attempts: 2, Stable: false},
	}
	accuracy := ComputeAccuracy(run, results)
	if accuracy.Repeated != 2 {
		t.Fatalf("expected 2 repeated targets, got %d", accuracy.Repeated)
	}
	if accuracy.Stable != 1 || accuracy.Unstable != 1 {
		t.Fatalf("expected 1 stable and 1 unstable, got %d/%d", accuracy.Stable, accuracy.Unstable)
	}
	if accuracy.StabilityRate != 50 {
		t.Fatalf("expected stability rate 50%%, got %f", accuracy.StabilityRate)
	}
	if accuracy.Attempts != 5 {
		t.Fatalf("expected 5 attempts in total, got %d", accuracy.Attempts)
	}
}

func TestComputeAccuracyHandlesEmptyResults(t *testing.T) {
	accuracy := ComputeAccuracy(&database.RedirectVerifyRun{ID: "empty", Total: 10}, nil)
	if accuracy.Completed != 0 || accuracy.Confirmed != 0 {
		t.Fatalf("expected an empty summary, got %+v", accuracy)
	}
	if accuracy.FalsePositiveRate != 0 || accuracy.OwnParamHitRate != 0 {
		t.Fatalf("expected zero ratios, got %+v", accuracy)
	}
}

func TestComputeAccuracyFallsBackToConfirmedForLegacyRows(t *testing.T) {
	// 舊資料列沒有 evidence 欄位 → 用 confirmed 反推，不讓歷史批次變成空白。
	results := []database.RedirectVerifyResult{
		{URL: "a", Confirmed: true},
	}
	accuracy := ComputeAccuracy(nil, results)
	if accuracy.LocationEvidence != 1 {
		t.Fatalf("expected legacy confirmed row to count as location evidence, got %d", accuracy.LocationEvidence)
	}
}
