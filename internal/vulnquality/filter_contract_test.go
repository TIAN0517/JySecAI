package vulnquality

import (
	"database/sql"
	"testing"

	"jysecai/internal/database"
)

func TestProposedCleanupPreservesDatabaseFilterContract(t *testing.T) {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	for _, statement := range []string{
		`CREATE TABLE vulnerabilities (id TEXT PRIMARY KEY, target TEXT, vulnerability_type TEXT, severity TEXT, status TEXT, conversation_id TEXT, project_id TEXT, conversation_tag TEXT, task_tag TEXT, created_at TEXT, updated_at TEXT)`,
		`CREATE TABLE batch_tasks (id TEXT, conversation_id TEXT, queue_id TEXT)`,
	} {
		if _, err := db.Exec(statement); err != nil {
			t.Fatal(err)
		}
	}
	fixtures := []struct {
		id     string
		target any
		typ    string
	}{
		{"root-slash", "https://EXAMPLE.test/", "信息泄露"},
		{"root-empty-path", "https://example.test", "Information Disclosure"},
		{"port1", "https://example.test:4001/events/", "CWE-937"},
		{"port4", "https://example.test:4004/events/", "CWE-937"},
		{"null-target", nil, "finding"},
		{"empty-target", "", "note"},
	}
	for _, row := range fixtures {
		if _, err := db.Exec(`INSERT INTO vulnerabilities (id,target,vulnerability_type,severity,status) VALUES (?,?,?,'medium','open')`, row.id, row.target, row.typ); err != nil {
			t.Fatal(err)
		}
	}
	aliases := AliasFile{Version: 1, Aliases: map[string]string{"信息泄露": "CWE-200", "Information Disclosure": "CWE-200"}}
	before, err := BuildReport(db, aliases)
	if err != nil {
		t.Fatal(err)
	}
	// Simulate only the reviewed proposal in synthetic test rows. The command
	// has no --fix mode and never writes to an operator's database copy.
	for _, change := range before.TargetChanges {
		for _, id := range change.IDs {
			if _, err := db.Exec(`UPDATE vulnerabilities SET target=? WHERE id=?`, change.To, id); err != nil {
				t.Fatal(err)
			}
		}
	}
	for _, mapping := range before.TypeMappings {
		for _, id := range mapping.IDs {
			if _, err := db.Exec(`UPDATE vulnerabilities SET vulnerability_type=? WHERE id=?`, mapping.To, id); err != nil {
				t.Fatal(err)
			}
		}
	}
	for _, issue := range before.DirtyTypes {
		for _, id := range issue.IDs {
			if _, err := db.Exec(`UPDATE vulnerabilities SET vulnerability_type=NULL WHERE id=?`, id); err != nil {
				t.Fatal(err)
			}
		}
	}
	api := &database.DB{DB: db}
	for _, test := range []struct {
		target string
		count  int
	}{
		{"https://example.test/", 2},
		{"https://example.test:4001/events", 1},
		{"https://example.test:4004/events", 1},
	} {
		count, err := api.CountVulnerabilities(database.VulnerabilityListFilter{Target: test.target})
		if err != nil || count != test.count {
			t.Fatalf("target %q: count=%d err=%v", test.target, count, err)
		}
	}
	options, err := api.GetVulnerabilityFilterOptionsForAccess(database.RBACListAccess{Scope: database.RBACScopeAll})
	if err != nil {
		t.Fatal(err)
	}
	if len(options["vulnerability_types"]) != 2 || len(options["targets"]) != 3 {
		t.Fatalf("filter options: %#v", options)
	}
	for _, option := range options["vulnerability_types"] {
		if option == "" {
			t.Fatal("empty dropdown option")
		}
	}
	after, err := BuildReport(db, aliases)
	if err != nil {
		t.Fatal(err)
	}
	if after.EmptyTargets.Count != before.EmptyTargets.Count || len(after.TargetChanges) != 0 {
		t.Fatalf("empty targets or idempotency changed: %#v", after)
	}
	var nullType sql.NullString
	if err := db.QueryRow(`SELECT vulnerability_type FROM vulnerabilities WHERE id='null-target'`).Scan(&nullType); err != nil {
		t.Fatal(err)
	}
	if nullType.Valid {
		t.Fatal("dirty type was not SQL NULL")
	}
	if after.Severity["medium"] != before.Severity["medium"] {
		t.Fatal("severity changed")
	}
}
