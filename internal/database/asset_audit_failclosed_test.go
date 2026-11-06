package database

import (
	"fmt"
	"testing"
	"time"
)

// appendAssetAccess gates both reads AND writes: DELETE FROM assets and
// UPDATE assets go through the same helper. When it treated an empty user ID
// as "no predicate", a caller without a session could delete or modify every
// tenant's assets — not merely read them.

func seedAccessScopeAssets(t *testing.T, db *DB) {
	t.Helper()
	if _, err := db.UpsertAssets([]*Asset{
		{IP: "198.51.100.1", Port: 443, Protocol: "https", Host: "a.example.test"},
		{IP: "198.51.100.2", Port: 443, Protocol: "https", Host: "b.example.test"},
		{IP: "198.51.100.3", Port: 443, Protocol: "https", Host: "c.example.test"},
	}, "", true); err != nil {
		t.Fatalf("UpsertAssets: %v", err)
	}
}

func TestAssetAccessFilterFailsClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	seedAccessScopeAssets(t, db)

	zero := RBACListAccess{}

	all, _, err := db.ListAssets(50, 0, AssetListFilter{}, RBACListAccess{Scope: RBACScopeAll})
	if err != nil || len(all) != 3 {
		t.Fatalf("all-scope list: n=%d err=%v (seed sanity)", len(all), err)
	}

	list, _, err := db.ListAssets(50, 0, AssetListFilter{}, zero)
	if err != nil {
		t.Fatalf("ListAssets: %v", err)
	}
	if len(list) != 0 {
		t.Fatalf("zero-value access listed %d assets; the filter failed open", len(list))
	}
}

func TestAssetWriteOperationsFailClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	seedAccessScopeAssets(t, db)

	all, _, err := db.ListAssets(50, 0, AssetListFilter{}, RBACListAccess{Scope: RBACScopeAll})
	if err != nil || len(all) == 0 {
		t.Fatalf("all-scope list: n=%d err=%v (seed sanity)", len(all), err)
	}
	victimID := all[0].ID

	zero := RBACListAccess{}

	// Delete must refuse rather than remove the row.
	if err := db.DeleteAsset(victimID, zero); err == nil {
		t.Error("DeleteAsset with an empty user id reported success")
	}
	if _, err := db.GetAsset(victimID, RBACListAccess{Scope: RBACScopeAll}); err != nil {
		t.Fatalf("the asset was deleted anyway: %v", err)
	}

	// Bulk delete must refuse too.
	if _, err := db.DeleteAssets([]string{victimID}, zero); err == nil {
		t.Error("DeleteAssets with an empty user id reported success")
	}
	if _, err := db.GetAsset(victimID, RBACListAccess{Scope: RBACScopeAll}); err != nil {
		t.Fatalf("the asset was bulk-deleted anyway: %v", err)
	}

	// Bulk update must not touch rows outside the caller's scope.
	inactive := "inactive"
	// Either outcome is acceptable as long as no row outside the caller's
	// scope is touched: a refusal, or a zero-row update. What must never
	// happen is a successful update.
	patched, _ := db.UpdateAssetsBulk([]string{victimID}, AssetBulkPatch{Status: &inactive}, zero)
	if patched != 0 {
		t.Errorf("UpdateAssetsBulk with an empty user id updated %d rows", patched)
	}
	got, err := db.GetAsset(victimID, RBACListAccess{Scope: RBACScopeAll})
	if err != nil {
		t.Fatal(err)
	}
	if got.Status == "inactive" {
		t.Error("UpdateAssetsBulk modified an asset outside the caller's scope")
	}
}

func TestGetAssetStatsFailsClosedOnEmptyUser(t *testing.T) {
	db := newTriageTestDB(t)
	seedAccessScopeAssets(t, db)

	all, err := db.GetAssetStats(RBACListAccess{Scope: RBACScopeAll}, 30)
	if err != nil {
		t.Fatalf("GetAssetStats all-scope: %v", err)
	}
	zero, err := db.GetAssetStats(RBACListAccess{}, 30)
	if err != nil {
		t.Fatalf("GetAssetStats: %v", err)
	}
	if fmt.Sprint(zero) == fmt.Sprint(all) {
		t.Errorf("zero-value access produced the same aggregate as all-scope: %#v", zero)
	}
}

// buildAuditLogsWhere only emits `actor = ?` when filter.Actor is non-empty,
// so a filter that never had an actor set degrades to WHERE 1=1 — every
// tenant's audit rows.
func TestAuditLogsRequireAnActorForScopedCallers(t *testing.T) {
	db := newTriageTestDB(t)
	for _, actor := range []string{"alice", "bob"} {
		if err := db.AppendAuditLog(&AuditLog{
			ID: "log-" + actor, Actor: actor, Action: "test", Level: "info", CreatedAt: time.Now(),
		}); err != nil {
			t.Fatalf("AppendAuditLog(%s): %v", actor, err)
		}
	}

	// Sanity: all rows exist.
	all, err := db.ListAuditLogs(ListAuditLogsFilter{})
	if err != nil {
		t.Fatalf("ListAuditLogs: %v", err)
	}
	if len(all) != 2 {
		t.Fatalf("seed sanity: got %d rows, want 2", len(all))
	}

	// A scoped caller's filter is narrowed by actor, not left empty.
	mine, err := db.ListAuditLogs(ListAuditLogsFilter{Actor: "alice"})
	if err != nil {
		t.Fatalf("ListAuditLogs(alice): %v", err)
	}
	if len(mine) != 1 || mine[0].Actor != "alice" {
		t.Errorf("actor filter returned %d rows: %#v", len(mine), mine)
	}
}
