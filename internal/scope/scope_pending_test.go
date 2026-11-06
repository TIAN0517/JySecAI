package scope

import (
	"context"
	"testing"
)

// TestPendingGrantDoesNotCover 是「自動起草」機制的安全前提。
//
// pending 的授權券代表「機器已起草、人還沒核准」。若它也算涵蓋，
// 等於機器先批准、人事後追認——整個授權狀態機就形同虛設。
// 所以這裡明確測試：pending 的券不涵蓋、也不產生拒絕。
func TestPendingGrantDoesNotCover(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	insertGrant(t, db, "g-pending", "host", "pending.example.com",
		[]string{ActionDBReadExtract}, 1, 0, nil, "pending")

	service := NewService(db)
	result, err := service.Resolve(ctx, []string{"pending.example.com"}, ActionDBReadExtract, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("pending 的授權券不該構成涵蓋，實際涵蓋：%v", coveredTargets(result))
	}
	if len(result.Uncovered) != 1 {
		t.Fatalf("pending 的目標應該落在未涵蓋，實際：%v", uncoveredTargets(result))
	}
	if len(result.Denied) != 0 {
		t.Fatalf("pending 不該產生拒絕記錄，實際：%v", result.Denied)
	}
}

// TestActiveGrantCovers 是對照組：同一張券轉為 active 後就涵蓋。
//
// 沒有這條對照，就無法分辨「pending 不涵蓋」是規則生效，還是比對邏輯壞掉。
func TestActiveGrantCovers(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	insertGrant(t, db, "g-active", "host", "active.example.com",
		[]string{ActionDBReadExtract}, 1, 0, nil, "active")

	service := NewService(db)
	result, err := service.Resolve(ctx, []string{"active.example.com"}, ActionDBReadExtract, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 1 {
		t.Fatalf("active 的授權券應該涵蓋，實際涵蓋：%v", coveredTargets(result))
	}
	if result.Covered[0].Source != SourceScopeGrant {
		t.Fatalf("涵蓋來源應為 scope_grant，實際 %q", result.Covered[0].Source)
	}
}

// TestPendingGrantWithExplicitClassStillBlocked 確認 pending 券連
// 「明確列出動作類別」也救不了它——pending 就是不生效。
func TestPendingGrantWithExplicitClassStillBlocked(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	insertGrant(t, db, "g-pending-cred", "host", "pending2.example.com",
		[]string{ActionCredentialEnum, ActionDBReadExtract}, 1, 0, nil, "pending")

	service := NewService(db)
	result, err := service.Resolve(ctx, []string{"pending2.example.com"}, ActionCredentialEnum, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Covered) != 0 {
		t.Fatalf("pending 的券不該涵蓋任何動作類別，實際：%v", coveredTargets(result))
	}
}

// TestAuditCoverageCountsDistinctTargets 確認覆蓋率報告不會被同一個目標灌水。
//
// 去重的單位是「正規化後的目標鍵」：大小寫與前後空白屬於同一個目標，
// 但 URL（url_prefix）與裸主機（host）是不同的授權單元——
// 授權「dup.example.com」不等於授權「https://dup.example.com/admin」。
func TestAuditCoverageCountsDistinctTargets(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	insertGrant(t, db, "g-audit", "host", "dup.example.com",
		[]string{ActionDBReadExtract}, 1, 0, nil, "active")

	report, err := AuditCoverage(ctx, db, []string{
		"dup.example.com",
		"DUP.example.com",
		"  dup.example.com  ",
		"https://dup.example.com/path",
		"other.example.com",
	}, ActionDBReadExtract, testNow)
	if err != nil {
		t.Fatal(err)
	}
	// 三個不同的目標鍵：dup 主機 / dup 的 URL / other 主機。
	if report.Total != 3 {
		t.Fatalf("去重後應該只有 3 個目標鍵，實際 %d（%v）", report.Total, report.UncoveredTargets)
	}
	// 主機授權同時涵蓋該主機與該主機底下的 URL（valueMatches 的既有語意）。
	if report.Covered != 2 {
		t.Fatalf("應該有 2 個目標被涵蓋（主機 + 其 URL），實際 %d", report.Covered)
	}
	if report.Uncovered != 1 {
		t.Fatalf("應該有 1 個目標未涵蓋，實際 %d", report.Uncovered)
	}
	if report.BySource[SourceScopeGrant] != 2 {
		t.Fatalf("涵蓋來源統計不正確：%v", report.BySource)
	}
}

// TestAuditCoverageWithoutGrantsIsAllUncovered 確認沒有任何授權時，
// 報告要誠實地呈現「全部未涵蓋」——這正是這份報告要回答的問題。
func TestAuditCoverageWithoutGrantsIsAllUncovered(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	report, err := AuditCoverage(ctx, db, []string{
		"a.example.com",
		"https://b.example.com/x",
		"c.example.com",
	}, ActionDBReadExtract, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if report.Total != 3 {
		t.Fatalf("應該有 3 個目標，實際 %d", report.Total)
	}
	if report.Covered != 0 {
		t.Fatalf("沒有授權時不該有涵蓋，實際 %d", report.Covered)
	}
	if report.Uncovered != 3 {
		t.Fatalf("應該全部未涵蓋，實際 %d", report.Uncovered)
	}
}
