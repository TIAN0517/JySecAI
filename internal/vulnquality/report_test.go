package vulnquality

import (
	"database/sql"
	"net/url"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestNormalizeTarget(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{name: "root trailing slash", in: "https://WWW.Example.com/", want: "https://www.example.com/"},
		{name: "root without slash", in: "https://WWW.Example.com", want: "https://www.example.com/"},
		{name: "path trailing slash", in: "https://WWW.Example.com/api/", want: "https://www.example.com/api"},
		{name: "query preserved", in: "https://WWW.Example.com/api/?a=1", want: "https://www.example.com/api?a=1"},
		{name: "port 4001 preserved", in: "https://EXAMPLE.com:4001/events/", want: "https://example.com:4001/events"},
		{name: "port 4004 distinct", in: "https://EXAMPLE.com:4004/events/", want: "https://example.com:4004/events"},
		{name: "empty remains empty", in: "  ", want: "  "},
		{name: "fragment preserved", in: "https://EXAMPLE.com/a/#Frag", want: "https://example.com/a#Frag"},
		{name: "repeated slash unchanged", in: "https://example.com/a//", want: "https://example.com/a//"},
		{name: "userinfo unchanged", in: "https://CaseSensitive:Test@example.com/a/", want: "https://CaseSensitive:Test@example.com/a/"},
		{name: "descriptive target remains opaque", in: "https://example.com/api + another endpoint", want: "https://example.com/api + another endpoint"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := NormalizeTarget(test.in); got != test.want {
				t.Fatalf("NormalizeTarget(%q) = %q, want %q", test.in, got, test.want)
			}
			if got := NormalizeTarget(test.want); got != test.want {
				t.Fatalf("normalization is not idempotent: %q -> %q", test.want, got)
			}
		})
	}
	if NormalizeTarget("https://example.com:4001/events") == NormalizeTarget("https://example.com:4004/events") {
		t.Fatal("different ports must remain distinct")
	}
}

func TestOpenReadOnlyRejectsWritesAndSymlinkOutsideTmp(t *testing.T) {
	// 產品端 ValidateCopyPath 直接以 /tmp 為允許根目錄，屬 POSIX-only 路徑。
	// Windows 上沒有對應的 /tmp 語意，模擬只會測到無關的行為。
	if runtime.GOOS == "windows" {
		t.Skip("ValidateCopyPath 以 /tmp 為根目錄，Windows 上不適用")
	}
	if _, err := ValidateCopyPath("/outside-tmp/nonexistent.db"); err == nil || !strings.Contains(err.Error(), "under /tmp") {
		t.Fatalf("outside path must be rejected before filesystem lookup: %v", err)
	}
	dir, err := os.MkdirTemp("/tmp", "jysec-quality-test-")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	path := filepath.Join(dir, "copy?test.db")
	db, err := sql.Open("sqlite3", (&url.URL{Scheme: "file", Path: path}).String())
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec("CREATE TABLE marker (value TEXT)"); err != nil {
		t.Fatal(err)
	}
	_ = db.Close()
	ro, err := OpenReadOnly(path)
	if err != nil {
		t.Fatal(err)
	}
	defer ro.Close()
	if _, err := ro.Exec("INSERT INTO marker VALUES ('changed')"); err == nil {
		t.Fatal("read-only database accepted a write")
	}
	link := filepath.Join(dir, "outside.db")
	if err := os.Symlink("/etc/hosts", link); err != nil {
		t.Fatal(err)
	}
	if _, err := OpenReadOnly(link); err == nil {
		t.Fatal("outside-/tmp symlink accepted")
	}
	for _, output := range []string{path, filepath.Join(dir, "same-db-link")} {
		if output != path {
			if err := os.Link(path, output); err != nil {
				t.Fatal(err)
			}
		}
		if err := ValidateOutputPath(output, path); err == nil {
			t.Fatal("output accepted database alias")
		}
	}
}

func TestMarkdownRedactsSecretShapedTargetContent(t *testing.T) {
	report := Report{TargetChanges: []TargetChange{{From: "https://example.test/ AIzaSyB12345678901234567890", To: "x", IDs: []string{"id"}}}}
	output := Markdown(report)
	if strings.Contains(output, "AIzaSyB12345678901234567890") || !strings.Contains(output, "[REDACTED]") {
		t.Fatalf("secret-shaped content was not redacted: %s", output)
	}
}

func TestCanonicalTypeUsesOnlyReviewedAliases(t *testing.T) {
	aliases := AliasFile{Version: 1, Aliases: map[string]string{
		"信息泄露":                   "CWE-200",
		"敏感信息泄露":                 "CWE-200",
		"Information Disclosure": "CWE-200",
	}}
	for _, value := range []string{"信息泄露", "敏感信息泄露", "information disclosure"} {
		if got, ok := CanonicalType(value, aliases); !ok || got != "CWE-200" {
			t.Fatalf("CanonicalType(%q) = %q, %v", value, got, ok)
		}
	}
	if got, ok := CanonicalType("CWE-937", aliases); ok || got != "CWE-937" {
		t.Fatalf("unreviewed type changed: %q, %v", got, ok)
	}
}

func TestBuildReportKeepsFilterOptionsAndListsAffectedIDs(t *testing.T) {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec(`CREATE TABLE vulnerabilities (id TEXT PRIMARY KEY, target TEXT, vulnerability_type TEXT, severity TEXT, status TEXT)`); err != nil {
		t.Fatal(err)
	}
	rows := []struct{ id, target, typ, severity, status string }{
		{"empty", "", "finding", "medium", "open"},
		{"slash", "https://EXAMPLE.test/", "Information Disclosure", "high", "open"},
		{"port1", "https://example.test:4001/events", "CWE-937", "critical", "confirmed"},
		{"port2", "https://example.test:4004/events", "CWE-937", "critical", "open"},
	}
	for _, row := range rows {
		if _, err := db.Exec(`INSERT INTO vulnerabilities VALUES (?,?,?,?,?)`, row.id, row.target, row.typ, row.severity, row.status); err != nil {
			t.Fatal(err)
		}
	}
	report, err := BuildReport(db, AliasFile{Version: 1, Aliases: map[string]string{"Information Disclosure": "CWE-200"}})
	if err != nil {
		t.Fatal(err)
	}
	if report.EmptyTargets.Count != 1 || report.EmptyTargets.IDs[0] != "empty" {
		t.Fatalf("empty targets = %#v", report.EmptyTargets)
	}
	if report.DirtyTypes["finding"].Count != 1 || report.DirtyTypes["finding"].IDs[0] != "empty" {
		t.Fatalf("dirty types = %#v", report.DirtyTypes)
	}
	if report.FilterOptionsAfterCount != 2 {
		t.Fatalf("filter options after cleanup = %d, want 2", report.FilterOptionsAfterCount)
	}
	if report.OpenBySeverity["critical"] != 1 || report.OpenBySeverity["high"] != 1 {
		t.Fatalf("open severity = %#v", report.OpenBySeverity)
	}
}
