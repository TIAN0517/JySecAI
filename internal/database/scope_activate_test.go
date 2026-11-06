package database

import (
	"context"
	"testing"
)

// TestActivateScopeGrantOnlyFromPending 驗證「按一次核准」的唯一入口語意。
//
// 規則：只認 pending → active 的單向轉換。
// 已生效的券再呼叫一次不能重置使用次數（不可重放）。
func TestActivateScopeGrantOnlyFromPending(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	if err := CreateScopeGrant(ctx, db, ScopeGrant{
		ID:            "g-pending",
		TargetType:    ScopeTargetTypeHost,
		TargetValue:   "pending.example.com",
		ActionClasses: []string{"db_read_extract"},
		MaxUses:       1,
		IssuedBy:      "scope-drafter",
		Status:        ScopeGrantStatusPending,
	}); err != nil {
		t.Fatal(err)
	}

	// pending 的券不能被消耗（ConsumeScopeGrant 只認 active）。
	if err := ConsumeScopeGrant(ctx, db, "g-pending"); err == nil {
		t.Fatal("pending 的授權券不該能被消耗")
	}

	activated, err := ActivateScopeGrant(ctx, db, "g-pending", "admin")
	if err != nil {
		t.Fatal(err)
	}
	if !activated {
		t.Fatal("pending 的券應該可以啟用")
	}

	loaded, err := GetScopeGrant(ctx, db, "g-pending")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Status != ScopeGrantStatusActive {
		t.Fatalf("啟用後狀態應為 active，實際 %q", loaded.Status)
	}
	if loaded.DecidedBy != "admin" {
		t.Fatalf("應記錄核准者，實際 %q", loaded.DecidedBy)
	}
	if loaded.DecidedAt == nil {
		t.Fatal("應記錄核准時間")
	}

	// 第二次啟用：冪等，回傳 false，且不重置 uses_used。
	if err := ConsumeScopeGrant(ctx, db, "g-pending"); err != nil {
		t.Fatal(err)
	}
	activated, err = ActivateScopeGrant(ctx, db, "g-pending", "someone-else")
	if err != nil {
		t.Fatal(err)
	}
	if activated {
		t.Fatal("已生效的券不該再次啟用")
	}
	loaded, err = GetScopeGrant(ctx, db, "g-pending")
	if err != nil {
		t.Fatal(err)
	}
	if loaded.UsesUsed != 1 {
		t.Fatalf("重複啟用不該重置使用次數，實際 %d", loaded.UsesUsed)
	}
}

// TestActivateScopeGrantRejectsUnknownAndExpired 確認不存在的券與已過期的券
// 都不會被啟用（而且不會回傳錯誤——那只是「沒有可啟用的東西」）。
func TestActivateScopeGrantRejectsUnknownAndExpired(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	activated, err := ActivateScopeGrant(ctx, db, "g-missing", "admin")
	if err != nil {
		t.Fatalf("不存在的券不該是錯誤：%v", err)
	}
	if activated {
		t.Fatal("不存在的券不該被啟用")
	}

	if err := CreateScopeGrant(ctx, db, ScopeGrant{
		ID:            "g-expired",
		TargetType:    ScopeTargetTypeHost,
		TargetValue:   "expired.example.com",
		ActionClasses: []string{"db_read_extract"},
		MaxUses:       1,
		IssuedBy:      "scope-drafter",
		Status:        ScopeGrantStatusPending,
	}); err != nil {
		t.Fatal(err)
	}
	// 直接把 valid_until 設成過去，模擬已過期的待裁決券。
	if _, err := db.Exec(`UPDATE scope_grants SET valid_until = ? WHERE id = 'g-expired'`,
		"2000-01-01T00:00:00Z"); err != nil {
		t.Fatal(err)
	}
	activated, err = ActivateScopeGrant(ctx, db, "g-expired", "admin")
	if err != nil {
		t.Fatal(err)
	}
	if activated {
		t.Fatal("已過期的券不該被啟用")
	}
}

// TestRevokeScopeGrant 確認撤銷可以把 pending 與 active 券都收掉。
func TestRevokeScopeGrant(t *testing.T) {
	db := newScopeTestDB(t)
	ctx := context.Background()

	for _, id := range []string{"g-rev-pending", "g-rev-active"} {
		status := ScopeGrantStatusPending
		if id == "g-rev-active" {
			status = ScopeGrantStatusActive
		}
		if err := CreateScopeGrant(ctx, db, ScopeGrant{
			ID:          id,
			TargetType:  ScopeTargetTypeHost,
			TargetValue: id + ".example.com",
			MaxUses:     1,
			IssuedBy:    "scope-drafter",
			Status:      status,
		}); err != nil {
			t.Fatal(err)
		}
		revoked, err := RevokeScopeGrant(ctx, db, id, "admin")
		if err != nil {
			t.Fatal(err)
		}
		if !revoked {
			t.Fatalf("%s 應該可以撤銷", id)
		}
		loaded, err := GetScopeGrant(ctx, db, id)
		if err != nil {
			t.Fatal(err)
		}
		if loaded.Status != ScopeGrantStatusRevoked {
			t.Fatalf("%s 撤銷後狀態應為 revoked，實際 %q", id, loaded.Status)
		}
	}

	// 已撤銷的券再撤銷一次 → 冪等，回傳 false。
	revoked, err := RevokeScopeGrant(ctx, db, "g-rev-pending", "admin")
	if err != nil {
		t.Fatal(err)
	}
	if revoked {
		t.Fatal("已撤銷的券不該再次撤銷")
	}
}
