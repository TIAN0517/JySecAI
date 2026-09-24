package database

import (
	"database/sql"
	"path/filepath"
	"strings"
	"testing"

	_ "github.com/mattn/go-sqlite3"
	"go.uber.org/zap"
)

func TestLegacyXssSchemaFailsBeforeImplicitConversion(t *testing.T) {
	path := filepath.Join(t.TempDir(), "legacy-xss.db")
	raw, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatal(err)
	}
	_, err = raw.Exec(`
		CREATE TABLE xss_payloads (
			id TEXT PRIMARY KEY,
			project_id TEXT,
			conversation_id TEXT,
			name TEXT NOT NULL DEFAULT '',
			source_url TEXT NOT NULL DEFAULT '',
			script TEXT NOT NULL,
			status TEXT NOT NULL DEFAULT 'armed',
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
		);
		CREATE TABLE xss_captures (
			id TEXT PRIMARY KEY,
			payload_id TEXT,
			status TEXT NOT NULL DEFAULT 'new',
			source_url TEXT NOT NULL DEFAULT '',
			cookies_json TEXT NOT NULL DEFAULT '{}',
			created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
		);
	`)
	if err != nil {
		_ = raw.Close()
		t.Fatal(err)
	}
	_ = raw.Close()

	if _, err := NewDB(path, zap.NewNop()); err == nil || !strings.Contains(err.Error(), "legacy XSS schema detected") {
		t.Fatalf("NewDB error = %v, want explicit legacy XSS schema error", err)
	}

	check, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatal(err)
	}
	defer check.Close()

	var tokenColumnCount int
	if err := check.QueryRow("SELECT COUNT(*) FROM pragma_table_info('xss_payloads') WHERE name='token'").Scan(&tokenColumnCount); err != nil {
		t.Fatal(err)
	}
	if tokenColumnCount != 0 {
		t.Fatalf("legacy table was partially converted; token column count = %d", tokenColumnCount)
	}
}
