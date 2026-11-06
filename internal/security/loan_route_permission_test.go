package security

import (
	"net/http"
	"testing"
)

// TestLoanRoutesMapToCatalogPermission 迴歸測試：貸款路由必須有權限映射。
//
// 未映射的路由在 permissionForRequest 會回空字串，RBAC 中介層因此 fail-closed
// 擋成 403 —— 整個貸款模組會對所有人（含 admin）失效，而且每次請求還會寫一筆
// unmapped_route 稽核。這個模組掛的是真實案件主檔，失效時不會有人第一時間發現。
func TestLoanRoutesMapToCatalogPermission(t *testing.T) {
	paths := []string{
		"/api/loan/summary",
		"/api/loan/cases",
		"/api/loan/applications",
		"/api/loan/case/123",
		"/api/loan/tables",
		"/api/loan/verify",
	}
	for _, p := range paths {
		permission := permissionForRequest(http.MethodGet, p)
		if permission == "" {
			t.Fatalf("permissionForRequest(GET, %s) = \"\" — 該路由會被 fail-closed 擋成 403", p)
		}
		if _, ok := PermissionCatalog[permission]; !ok {
			t.Fatalf("permissionForRequest(GET, %s) = %q，但 %q 不在 PermissionCatalog 裡", p, permission, permission)
		}
	}
}

// TestLoanWriteRoutesRequireWritePermission 貸款資料的寫入權限必須與讀取分開。
func TestDatabasesCatalogMapsToConfigRead(t *testing.T) {
	got := permissionForRequest(http.MethodGet, "/api/databases")
	if got != "config:read" {
		t.Fatalf("permissionForRequest(GET, /api/databases) = %q", got)
	}
	if _, ok := PermissionCatalog[got]; !ok {
		t.Fatalf("permission %q 不在 PermissionCatalog 裡", got)
	}
}

func TestLoanWriteRoutesRequireWritePermission(t *testing.T) {
	read := permissionForRequest(http.MethodGet, "/api/loan/cases")
	write := permissionForRequest(http.MethodPost, "/api/loan/cases")
	if read == write {
		t.Fatalf("讀寫對應到同一個權限 %q，資料寫入必須能單獨撤銷", read)
	}
	if _, ok := PermissionCatalog[write]; !ok {
		t.Fatalf("permission %q 不在 PermissionCatalog 裡", write)
	}
}
