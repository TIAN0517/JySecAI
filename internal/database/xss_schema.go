package database

import (
	"context"
	"database/sql"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
)

const xssPayloadsDDL = `CREATE TABLE IF NOT EXISTS xss_payloads (
 id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
 conversation_id TEXT REFERENCES conversations(id) ON DELETE SET NULL,
 name TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', script TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'armed', created_by TEXT,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 callback_token TEXT, enabled INTEGER NOT NULL DEFAULT 1, domain TEXT NOT NULL DEFAULT '',
 domain_only INTEGER NOT NULL DEFAULT 0, owner_user_id TEXT
)`
const xssCapturesDDL = `CREATE TABLE IF NOT EXISTS xss_captures (
 id TEXT PRIMARY KEY, payload_id TEXT REFERENCES xss_payloads(id) ON DELETE SET NULL,
 project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
 conversation_id TEXT REFERENCES conversations(id) ON DELETE SET NULL,
 status TEXT NOT NULL DEFAULT 'new', source_url TEXT NOT NULL DEFAULT '', page_title TEXT NOT NULL DEFAULT '',
 user_agent TEXT NOT NULL DEFAULT '', client_ip TEXT NOT NULL DEFAULT '', url_fragment TEXT NOT NULL DEFAULT '',
 cookies_json TEXT NOT NULL DEFAULT '{}', local_storage_json TEXT NOT NULL DEFAULT '{}',
 session_storage_json TEXT NOT NULL DEFAULT '{}', api_keys_json TEXT NOT NULL DEFAULT '{}',
 seized_at DATETIME, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)`

type xssQuery interface {
	QueryContext(context.Context, string, ...interface{}) (*sql.Rows, error)
}

func xssColumns(ctx context.Context, q xssQuery, table string) (map[string]string, error) {
	rows, err := q.QueryContext(ctx, "PRAGMA table_info("+table+")")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	cols := map[string]string{}
	for rows.Next() {
		var cid, nn, pk int
		var name, typ string
		var def interface{}
		if err = rows.Scan(&cid, &name, &typ, &nn, &def, &pk); err != nil {
			return nil, err
		}
		cols[name] = strings.ToUpper(strings.TrimSpace(typ))
	}
	return cols, rows.Err()
}

var richXSSColumns = map[string][]string{
	"xss_payloads": {"id", "project_id", "conversation_id", "name", "source_url", "script", "status", "created_by", "created_at", "updated_at"},
	"xss_captures": {"id", "payload_id", "project_id", "conversation_id", "status", "source_url", "page_title", "user_agent", "client_ip", "url_fragment", "cookies_json", "local_storage_json", "session_storage_json", "api_keys_json", "seized_at", "created_at", "updated_at"},
}

// CheckXSSSchema fails before ANY write for INTEGER, mixed or partial schemas.
func CheckXSSSchema(ctx context.Context, q xssQuery) error {
	present := 0
	for table, required := range richXSSColumns {
		cols, err := xssColumns(ctx, q, table)
		if err != nil {
			return err
		}
		if len(cols) == 0 {
			continue
		}
		present++
		if cols["id"] != "TEXT" || (table == "xss_captures" && cols["payload_id"] != "TEXT") {
			return fmt.Errorf("incompatible XSS schema in %s: rich TEXT IDs required; no implicit conversion", table)
		}
		for _, c := range required {
			if _, ok := cols[c]; !ok {
				return fmt.Errorf("incomplete rich XSS schema in %s: missing %s", table, c)
			}
		}
		if table == "xss_payloads" {
			for _, col := range xssV2Columns {
				if typ, ok := cols[col.name]; ok && typ != col.typ {
					return fmt.Errorf("incompatible XSS column %s", col.name)
				}
			}
		}
	}
	if present == 1 {
		return fmt.Errorf("partial XSS schema: both rich tables required")
	}
	return nil
}
func preflightXSSFile(path string) error {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil
	} else if err != nil {
		return err
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	u := url.URL{Scheme: "file", Path: filepath.ToSlash(abs), RawQuery: "mode=ro"}
	raw, err := sql.Open("sqlite3", u.String())
	if err != nil {
		return err
	}
	defer raw.Close()
	return CheckXSSSchema(context.Background(), raw)
}

var xssV2Columns = []struct{ name, typ, ddl string }{
	{"callback_token", "TEXT", "ALTER TABLE xss_payloads ADD COLUMN callback_token TEXT"},
	{"enabled", "INTEGER", "ALTER TABLE xss_payloads ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1"},
	{"domain", "TEXT", "ALTER TABLE xss_payloads ADD COLUMN domain TEXT NOT NULL DEFAULT ''"},
	{"domain_only", "INTEGER", "ALTER TABLE xss_payloads ADD COLUMN domain_only INTEGER NOT NULL DEFAULT 0"},
	{"owner_user_id", "TEXT", "ALTER TABLE xss_payloads ADD COLUMN owner_user_id TEXT"},
}

// MigrateXSSV2 modifies only XSS columns/indexes in one transaction. Existing
// IDs, script, JSON, timestamps and all other legacy values are never updated.
func MigrateXSSV2(ctx context.Context, raw *sql.DB) error {
	tx, err := raw.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = CheckXSSSchema(ctx, tx); err != nil {
		return err
	}
	cols, err := xssColumns(ctx, tx, "xss_payloads")
	if err != nil {
		return err
	}
	if len(cols) == 0 {
		for _, ddl := range []string{xssPayloadsDDL, xssCapturesDDL} {
			if _, err = tx.ExecContext(ctx, ddl); err != nil {
				return err
			}
		}
	} else {
		for _, c := range xssV2Columns {
			if _, ok := cols[c.name]; !ok {
				if _, err = tx.ExecContext(ctx, c.ddl); err != nil {
					return err
				}
			}
		}
	}
	for _, ddl := range []string{
		"CREATE UNIQUE INDEX IF NOT EXISTS idx_xss_payloads_callback_token ON xss_payloads(callback_token) WHERE callback_token IS NOT NULL AND callback_token <> ''",
		"CREATE INDEX IF NOT EXISTS idx_xss_payloads_created_at ON xss_payloads(created_at)",
		"CREATE INDEX IF NOT EXISTS idx_xss_captures_created_at ON xss_captures(created_at)",
		"CREATE INDEX IF NOT EXISTS idx_xss_captures_payload_id ON xss_captures(payload_id)",
	} {
		if _, err = tx.ExecContext(ctx, ddl); err != nil {
			return err
		}
	}
	return tx.Commit()
}
