package scope

import (
	"context"
	"testing"
	"time"
)

// 拒絕記憶（設計 §7）：被拒過的目標之後直接拒，不再打擾操作者。
//
// 這條規則同時是安全特性與體驗特性：安全上避免「一直問一直問」繞過掉，
// 體驗上讓操作者只需要裁決一次。

func TestPreviouslyDeniedTargetIsNotUncovered(t *testing.T) {
	db := newScopeTestDB(t)
	_, err := db.Exec(`
		INSERT INTO scope_denials (target, owner, reason, decided_by, decided_at)
		VALUES ('example.com', 'client', 'rejected', 'operator', ?)`,
		testNow.Format(time.RFC3339Nano))
	if err != nil {
		t.Fatal(err)
	}
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Uncovered) != 0 {
		t.Fatalf("被拒過的目標不該再出現在未覆蓋清單（避免重複打擾）：%v", uncoveredTargets(result))
	}
	if len(result.Denied) != 1 {
		t.Fatalf("應回報一次拒絕：%v", result.Denied)
	}
	if result.Denied[0].Reason != ReasonPreviouslyDenied {
		t.Fatalf("應回報 previously_denied，實際 %q", result.Denied[0].Reason)
	}
	if result.Denied[0].Detail == "" {
		t.Fatal("拒絕記憶應帶上原因說明")
	}
}

func TestPreviouslyDeniedUsesNormalizedKey(t *testing.T) {
	db := newScopeTestDB(t)
	_, err := db.Exec(`
		INSERT INTO scope_denials (target, owner, reason, decided_by, decided_at)
		VALUES ('example.com', 'client', 'rejected', 'operator', ?)`,
		testNow.Format(time.RFC3339Nano))
	if err != nil {
		t.Fatal(err)
	}
	service := NewService(db)

	// 同一個目標的大小寫／結尾變體不該繞過拒絕記憶。
	for _, raw := range []string{"example.com", "EXAMPLE.com", "example.com."} {
		result, err := service.Resolve(context.Background(),
			[]string{raw}, ActionHarmlessRequest, testNow)
		if err != nil {
			t.Fatal(err)
		}
		if reason := denialFor(result, "example.com"); reason != ReasonPreviouslyDenied {
			t.Fatalf("%q 應命中拒絕記憶，實際 %q", raw, reason)
		}
	}
}

func TestDenialOnlyAffectsItsOwnTarget(t *testing.T) {
	db := newScopeTestDB(t)
	_, err := db.Exec(`
		INSERT INTO scope_denials (target, owner, reason, decided_by, decided_at)
		VALUES ('example.com', 'client', 'rejected', 'operator', ?)`,
		testNow.Format(time.RFC3339Nano))
	if err != nil {
		t.Fatal(err)
	}
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"other.example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Denied) != 0 {
		t.Fatalf("其他目標不該被連坐：%v", result.Denied)
	}
	if got := uncoveredTargets(result); len(got) != 1 || got[0] != "other.example.com" {
		t.Fatalf("其他目標應為未覆蓋：%v", got)
	}
}

func TestDeniedTargetCanStillBeAuthorizedLater(t *testing.T) {
	db := newScopeTestDB(t)
	_, err := db.Exec(`
		INSERT INTO scope_denials (target, owner, reason, decided_by, decided_at)
		VALUES ('example.com', 'client', 'rejected', 'operator', ?)`,
		testNow.Format(time.RFC3339Nano))
	if err != nil {
		t.Fatal(err)
	}
	// 操作者改變心意：把目標放進常駐集。
	insertTarget(t, db, "t-reopened", "client", "host", "example.com", nil, nil, nil)
	service := NewService(db)

	result, err := service.Resolve(context.Background(),
		[]string{"example.com"}, ActionHarmlessRequest, testNow)
	if err != nil {
		t.Fatal(err)
	}
	// 拒絕記憶優先於常駐集：要不要重開是操作者的動作（刪掉拒絕記錄），
	// 這裡的行為必須是「拒絕仍然有效」，不能被常駐集默默蓋掉。
	if len(result.Covered) != 0 {
		t.Fatalf("拒絕記憶不該被常駐集蓋掉：%v", coveredTargets(result))
	}
	if reason := denialFor(result, "example.com"); reason != ReasonPreviouslyDenied {
		t.Fatalf("應回報 previously_denied，實際 %q", reason)
	}
}
