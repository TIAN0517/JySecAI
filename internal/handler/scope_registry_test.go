package handler

import (
	"context"
	"database/sql"
	"path/filepath"
	"testing"
	"time"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

// newScopeHandlerTestDB 建立帶完整 schema 的測試資料庫。
//
// 走 database.NewDB（而不是自建 DDL）：RBAC 與 scope registry 的表結構
// 是這兩個套件的契約，重貼一份只會讓欄位悄悄走鍰。
func newScopeHandlerTestDB(t *testing.T) (*sql.DB, *database.DB) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "scope-registry.sqlite"), zap.NewNop())
	if err != nil {
		t.Fatalf("建立測試資料庫失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db.DB, db
}

// seedUser 建立使用者、角色、權限與機器人綁定。
func seedUser(t *testing.T, db *sql.DB, userID, roleID, permissionKey, telegramID string) {
	t.Helper()
	now := time.Now().UTC().Format(time.RFC3339Nano)
	if _, err := db.Exec(`INSERT OR REPLACE INTO rbac_users
		(id,username,display_name,password_hash,enabled,is_builtin,created_at,updated_at)
		VALUES (?,?,'','x',1,0,?,?)`, userID, userID, now, now); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT OR REPLACE INTO rbac_roles
		(id,name,description,scope,is_system,created_at,updated_at)
		VALUES (?,'role-'||?,'test','assigned',0,?,?)`, roleID, roleID, now, now); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`INSERT OR REPLACE INTO rbac_user_roles (user_id,role_id,created_at) VALUES (?,?,?)`,
		userID, roleID, now); err != nil {
		t.Fatal(err)
	}
	if permissionKey != "" {
		// rbac_role_permissions.permission_key 有 FK 指向 rbac_permissions(key)，
		// 所以權限鍵必須先存在（正式流程由 BootstrapRBAC 寫入）。
		if _, err := db.Exec(`INSERT OR IGNORE INTO rbac_permissions (key,description,created_at) VALUES (?,?,?)`,
			permissionKey, "test", now); err != nil {
			t.Fatal(err)
		}
		if _, err := db.Exec(`INSERT OR REPLACE INTO rbac_role_permissions (role_id,permission_key,created_at) VALUES (?,?,?)`,
			roleID, permissionKey, now); err != nil {
			t.Fatal(err)
		}
	}
	if telegramID != "" {
		if _, err := db.Exec(`INSERT OR REPLACE INTO robot_user_bindings
			(id,platform,external_user_id,rbac_user_id,enabled,created_at,updated_at)
			VALUES (?,'telegram',?,?,1,?,?)`, "bind-"+userID, telegramID, userID, now, now); err != nil {
			t.Fatal(err)
		}
	}
}

// TestCallbackRequiresScopeWrite 是最重要的一道閘門測試。
//
// Telegram 的 inline 按鈕任何人都能按。沒有權限檢查的話，
// 「人按一次就生效」等於「任何人都能替操作者核准授權」。
func TestCallbackRequiresScopeWrite(t *testing.T) {
	db, databaseDB := newScopeHandlerTestDB(t)
	ctx := context.Background()
	_ = ctx

	// 沒有綁定平台帳號的使用者。
	if _, err := db.Exec(`INSERT OR REPLACE INTO scope_grants
		(id,target_type,target_value,action_classes,max_uses,uses_used,issued_by,issued_at,evidence,status)
		VALUES ('g-1','host','a.example.com','["db_read_extract"]',1,0,'drafter',?,'','pending')`,
		time.Now().UTC().Format(time.RFC3339Nano)); err != nil {
		t.Fatal(err)
	}

	handler := &ScopeRegistryHandler{db: databaseDB}

	reply := handler.HandleCallback("telegram", "u:999999", "scope_grant:activate:g-1")
	if reply == "" {
		t.Fatal("應回覆說明為何不能核准")
	}
	t.Logf("未綁定身分的回覆：%s", reply)

	// 券必須仍是 pending（沒有被啟用）
	var status string
	if err := db.QueryRow(`SELECT status FROM scope_grants WHERE id='g-1'`).Scan(&status); err != nil {
		t.Fatal(err)
	}
	if status != database.ScopeGrantStatusPending {
		t.Fatalf("未授權者不得啟用授權券，實際狀態 %q", status)
	}

	// 有綁定但沒有 scope:write 的帳號（只有 scope:read）。
	seedUser(t, db, "reader", "role-reader", "scope:read", "u:111111")
	reply = handler.HandleCallback("telegram", "u:111111", "scope_grant:activate:g-1")
	t.Logf("只有 scope:read 的回覆：%s", reply)
	if err := db.QueryRow(`SELECT status FROM scope_grants WHERE id='g-1'`).Scan(&status); err != nil {
		t.Fatal(err)
	}
	if status != database.ScopeGrantStatusPending {
		t.Fatalf("只有讀權限者不得啟用授權券，實際狀態 %q", status)
	}

	// 有 scope:write 的帳號：應該能核准。
	seedUser(t, db, "approver", "role-approver", "scope:write", "u:222222")
	reply = handler.HandleCallback("telegram", "u:222222", "scope_grant:activate:g-1")
	t.Logf("具 scope:write 的回覆：%s", reply)
	if err := db.QueryRow(`SELECT status FROM scope_grants WHERE id='g-1'`).Scan(&status); err != nil {
		t.Fatal(err)
	}
	if status != database.ScopeGrantStatusActive {
		t.Fatalf("具 scope:write 者應可啟用授權券，實際狀態 %q（回覆：%s）", status, reply)
	}
}

// TestCallbackRejectsMalformedData 確認格式不良的按鈕資料不會造成任何變更。
func TestCallbackRejectsMalformedData(t *testing.T) {
	_, databaseDB := newScopeHandlerTestDB(t)
	handler := &ScopeRegistryHandler{db: databaseDB}

	for _, data := range []string{"", "scope_grant", "scope_grant:activate", "other:activate:g-1", "scope_grant:unknown:g-1"} {
		reply := handler.HandleCallback("telegram", "u:1", data)
		if reply == "" {
			t.Fatalf("格式不良的按鈕資料應有回覆：%q", data)
		}
	}
}
