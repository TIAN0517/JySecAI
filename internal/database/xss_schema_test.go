package database

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"fmt"
	"path/filepath"
	"strings"
	"testing"

	"go.uber.org/zap"
)

func legacyXSSFixture(t *testing.T) *sql.DB {
	t.Helper()
	raw, err := sql.Open("sqlite3", filepath.Join(t.TempDir(), "legacy.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { raw.Close() })
	// The pre-v2 rich DDL is deliberately independent from the migration code.
	for _, ddl := range []string{
		`CREATE TABLE xss_payloads (id TEXT PRIMARY KEY, project_id TEXT, conversation_id TEXT, name TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', script TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'armed', created_by TEXT, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)`,
		`CREATE TABLE xss_captures (id TEXT PRIMARY KEY, payload_id TEXT, project_id TEXT, conversation_id TEXT, status TEXT NOT NULL DEFAULT 'new', source_url TEXT NOT NULL DEFAULT '', page_title TEXT NOT NULL DEFAULT '', user_agent TEXT NOT NULL DEFAULT '', client_ip TEXT NOT NULL DEFAULT '', url_fragment TEXT NOT NULL DEFAULT '', cookies_json TEXT NOT NULL DEFAULT '{}', local_storage_json TEXT NOT NULL DEFAULT '{}', session_storage_json TEXT NOT NULL DEFAULT '{}', api_keys_json TEXT NOT NULL DEFAULT '{}', seized_at DATETIME, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)`,
	} {
		if _, err = raw.Exec(ddl); err != nil {
			t.Fatal(err)
		}
	}
	return raw
}
func TestXSSLegacyAdditiveMigrationPreservesUUIDScriptAndAllValues(t *testing.T) {
	raw := legacyXSSFixture(t)
	id := "bc619186-ba4d-4613-9a71-7d0ea2a258cc"
	script := "/* synthetic only: 舊內容 */ const fixture = 'jysec_test=1';"
	_, err := raw.Exec(`INSERT INTO xss_payloads(id,project_id,conversation_id,name,source_url,script,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)`, id, "p", "c", "legacy", "http://127.0.0.1/test", script, "fired", "owner", "2026-09-08 10:00:00", "2026-09-08 11:00:00")
	if err != nil {
		t.Fatal(err)
	}
	snapshot := func() string {
		var values [10]interface{}
		dest := make([]interface{}, 10)
		for i := range values {
			dest[i] = &values[i]
		}
		if err := raw.QueryRow(`SELECT id,project_id,conversation_id,name,source_url,script,status,created_by,created_at,updated_at FROM xss_payloads`).Scan(dest...); err != nil {
			t.Fatal(err)
		}
		return fmt.Sprint(values)
	}
	before := snapshot()
	hash := sha256.Sum256([]byte(script))
	for i := 0; i < 2; i++ {
		if err = MigrateXSSV2(context.Background(), raw); err != nil {
			t.Fatal(err)
		}
	}
	if snapshot() != before {
		t.Fatal("legacy values changed")
	}
	var after string
	var token sql.NullString
	var enabled int
	if err = raw.QueryRow(`SELECT script,callback_token,enabled FROM xss_payloads WHERE id=?`, id).Scan(&after, &token, &enabled); err != nil {
		t.Fatal(err)
	}
	if sha256.Sum256([]byte(after)) != hash || len(script) != len(after) || token.Valid || enabled != 1 {
		t.Fatal("preservation/default failure")
	}
	for table, want := range map[string]int{"xss_payloads": 1, "xss_captures": 0} {
		var n int
		if err = raw.QueryRow("SELECT count(*) FROM " + table).Scan(&n); err != nil || n != want {
			t.Fatalf("%s count %d %v", table, n, err)
		}
	}
}
func TestXSSFreshDatabaseRichSchemaAndPartialUniqueToken(t *testing.T) {
	db := newRBACTestDB(t)
	ctx := context.Background()
	for _, table := range []string{"xss_payloads", "xss_captures"} {
		cols, err := xssColumns(ctx, db.DB, table)
		if err != nil || cols["id"] != "TEXT" {
			t.Fatal(table, cols, err)
		}
	}
	for i, token := range []interface{}{nil, nil, "", "", "one"} {
		if _, err := db.Exec(`INSERT INTO xss_payloads(id,script,callback_token) VALUES(?,?,?)`, fmt.Sprint(i), "synthetic", token); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := db.Exec(`INSERT INTO xss_payloads(id,script,callback_token) VALUES('duplicate','synthetic','one')`); err == nil {
		t.Fatal("nonempty duplicate accepted")
	}
	if err := MigrateXSSV2(ctx, db.DB); err != nil {
		t.Fatal(err)
	}
}
func TestXSSIncompatibleSchemaRejectedBeforeNewDBWrites(t *testing.T) {
	for _, captureType := range []string{"INTEGER", "TEXT"} {
		t.Run(captureType, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "mixed.db")
			raw, _ := sql.Open("sqlite3", path)
			raw.Exec(`CREATE TABLE xss_payloads(id INTEGER PRIMARY KEY,token TEXT)`)
			raw.Exec("CREATE TABLE xss_captures(id " + captureType + " PRIMARY KEY)")
			var before int
			raw.QueryRow(`SELECT count(*) FROM sqlite_master`).Scan(&before)
			raw.Close()
			db, err := NewDB(path, zap.NewNop())
			if err == nil {
				db.Close()
				t.Fatal("incompatible DB accepted")
			}
			raw, _ = sql.Open("sqlite3", path)
			defer raw.Close()
			var after int
			raw.QueryRow(`SELECT count(*) FROM sqlite_master`).Scan(&after)
			if before != after {
				t.Fatal("failed preflight wrote schema")
			}
		})
	}
}
func TestXSSMigrationTransactionRollsBackOnIndexFailure(t *testing.T) {
	raw := legacyXSSFixture(t)
	raw.Exec(`CREATE TABLE collision(x TEXT)`)
	raw.Exec(`CREATE TABLE idx_xss_payloads_callback_token(x TEXT)`)
	if err := MigrateXSSV2(context.Background(), raw); err == nil {
		t.Fatal("expected collision error")
	}
	cols, _ := xssColumns(context.Background(), raw, "xss_payloads")
	if _, ok := cols["enabled"]; ok {
		t.Fatal("partial migration not rolled back")
	}
}
func TestXSSScopesAndInheritedCaptureAccess(t *testing.T) {
	db := newRBACTestDB(t)
	user, err := db.CreateRBACUser("member", "Member", "hash", true, nil)
	if err != nil {
		t.Fatal(err)
	}
	project, err := db.CreateProject(&Project{Name: "project"})
	if err != nil {
		t.Fatal(err)
	}
	conv, err := db.CreateConversation("conversation", ConversationCreateMeta{})
	if err != nil {
		t.Fatal(err)
	}
	db.SetResourceOwner("project", project.ID, user.ID)
	db.SetResourceOwner("conversation", conv.ID, user.ID)
	cases := []struct {
		name          string
		p             XSSPayload
		own, assigned bool
	}{
		{"owner", XSSPayload{OwnerUserID: user.ID}, true, false},
		{"project", XSSPayload{ProjectID: project.ID}, true, false},
		{"conversation", XSSPayload{ConversationID: conv.ID}, true, false},
		{"explicit", XSSPayload{}, true, true},
		{"other", XSSPayload{OwnerUserID: "other"}, false, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			p, err := db.CreateXSSPayload(&tc.p)
			if err != nil {
				t.Fatal(err)
			}
			cap, err := db.CreateXSSCapture(&XSSCapture{PayloadID: p.ID})
			if err != nil {
				t.Fatal(err)
			}
			if tc.name == "explicit" {
				if err = db.AssignResourceToUser(user.ID, "xss_payload", p.ID); err != nil {
					t.Fatal(err)
				}
			}
			for _, check := range []struct {
				scope string
				want  bool
			}{{RBACScopeOwn, tc.own}, {RBACScopeAssigned, tc.assigned}, {RBACScopeAll, true}, {"invalid", false}} {
				a := RBACListAccess{UserID: user.ID, Scope: check.scope}
				for table, id := range map[string]string{"xss_payloads": p.ID, "xss_captures": cap.ID} {
					typ := strings.TrimSuffix(table, "s")
					if got := db.UserCanAccessXSS(a, table, typ, id); got != check.want {
						t.Fatalf("%s %s got %v", table, check.scope, got)
					}
				}
			}
		})
	}
	items, total, err := db.ListXSSPayloads(XSSListFilter{}, RBACListAccess{UserID: user.ID, Scope: RBACScopeOwn}, 0, 50)
	if err != nil || total != 4 || len(items) != 4 {
		t.Fatal(total, err)
	}
	if db.UserCanAccessXSS(RBACListAccess{UserID: "foreign", Scope: RBACScopeOwn}, "xss_payloads", "xss_payload", cases[0].p.ID) {
		t.Fatal("cross-user access")
	}
	if err = db.AssignResourceToUser(user.ID, "project", project.ID); err != nil {
		t.Fatal(err)
	}
	assigned, _, err := db.ListXSSPayloads(XSSListFilter{}, RBACListAccess{UserID: user.ID, Scope: RBACScopeAssigned}, 0, 50)
	if err != nil || len(assigned) != 2 {
		t.Fatal("project assignment inheritance", len(assigned), err)
	}
}
func TestXSSCaptureStatusAndMalformedStoredJSON(t *testing.T) {
	db := newRBACTestDB(t)
	c, err := db.CreateXSSCapture(&XSSCapture{})
	if err != nil {
		t.Fatal(err)
	}
	for _, status := range []string{"seized", "analyzed", "ignored", "new"} {
		if err = db.UpdateXSSCaptureStatus(c.ID, status); err != nil {
			t.Fatal(err)
		}
		got, err := db.GetXSSCapture(c.ID)
		if err != nil || got.Status != status {
			t.Fatal(err)
		}
	}
	if err = db.UpdateXSSCaptureStatus(c.ID, "arbitrary"); err == nil {
		t.Fatal("invalid status")
	}
	db.Exec(`UPDATE xss_captures SET cookies_json='invalid' WHERE id=?`, c.ID)
	if _, err = db.GetXSSCapture(c.ID); err == nil {
		t.Fatal("malformed stored JSON silently accepted")
	}
}
