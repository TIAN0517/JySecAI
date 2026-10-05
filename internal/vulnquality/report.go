package vulnquality

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

var dirtyVulnerabilityTypes = []string{
	"finding",
	"target",
	"note",
	"configuration",
	"exploit",
	"confidence.80",
}

type AliasFile struct {
	Version int               `json:"version"`
	Aliases map[string]string `json:"aliases"`
}

type Issue struct {
	Count int      `json:"count"`
	IDs   []string `json:"ids"`
}

type TargetChange struct {
	From string   `json:"from"`
	To   string   `json:"to"`
	IDs  []string `json:"ids"`
}

type TypeMapping struct {
	From string   `json:"from"`
	To   string   `json:"to"`
	IDs  []string `json:"ids"`
}

type Report struct {
	GeneratedAt             time.Time        `json:"generated_at"`
	Total                   int              `json:"total"`
	EmptyTargets            Issue            `json:"empty_targets"`
	DirtyTypes              map[string]Issue `json:"dirty_types"`
	TargetChanges           []TargetChange   `json:"target_changes"`
	TypeMappings            []TypeMapping    `json:"type_mappings"`
	Severity                map[string]int   `json:"severity"`
	Status                  map[string]int   `json:"status"`
	OpenBySeverity          map[string]int   `json:"open_by_severity"`
	FilterOptionsBefore     []string         `json:"filter_options_before"`
	FilterOptionsAfterCount int              `json:"filter_options_after_count"`
}

func LoadAliases(path string) (AliasFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return AliasFile{}, fmt.Errorf("read alias file: %w", err)
	}
	var aliases AliasFile
	if err := json.Unmarshal(data, &aliases); err != nil {
		return AliasFile{}, fmt.Errorf("parse alias file: %w", err)
	}
	if aliases.Version != 1 {
		return AliasFile{}, fmt.Errorf("unsupported alias file version %d", aliases.Version)
	}
	if len(aliases.Aliases) == 0 {
		return AliasFile{}, fmt.Errorf("alias file is empty")
	}
	for from, to := range aliases.Aliases {
		if strings.TrimSpace(from) == "" || strings.TrimSpace(to) == "" {
			return AliasFile{}, fmt.Errorf("alias entries must not be empty")
		}
	}
	return aliases, nil
}

// NormalizeTarget conservatively canonicalizes HTTP(S) targets. Scheme and
// host are lower-cased; an absent root path becomes /, and a single non-root
// trailing slash is removed. Port, path, query and fragment remain distinct.
// Repeated trailing slashes, userinfo and opaque targets remain unchanged.
func NormalizeTarget(value string) string {
	if strings.TrimSpace(value) == "" {
		return value
	}
	// A number of legacy rows contain prose or several URLs in target. Treat
	// those as opaque text; URL parsing would percent-encode the prose and
	// silently change meaning beyond the conservative normalization contract.
	if strings.ContainsAny(value, " \t\r\n") {
		return value
	}
	parsed, err := url.Parse(value)
	if err != nil || parsed.Host == "" || parsed.User != nil || (!strings.EqualFold(parsed.Scheme, "http") && !strings.EqualFold(parsed.Scheme, "https")) {
		return value
	}
	schemeEnd := strings.Index(value, "://")
	if schemeEnd < 0 {
		return value
	}
	authorityStart := schemeEnd + 3
	authorityEnd := len(value)
	if offset := strings.IndexAny(value[authorityStart:], "/?#"); offset >= 0 {
		authorityEnd = authorityStart + offset
	}
	normalized := strings.ToLower(value[:schemeEnd]) + "://" + strings.ToLower(value[authorityStart:authorityEnd])
	rest := value[authorityEnd:]
	pathEnd := len(rest)
	if offset := strings.IndexAny(rest, "?#"); offset >= 0 {
		pathEnd = offset
	}
	path, suffix := rest[:pathEnd], rest[pathEnd:]
	if path == "" {
		path = "/"
	} else if path != "/" && strings.HasSuffix(path, "/") && !strings.HasSuffix(path, "//") {
		path = strings.TrimSuffix(path, "/")
	}
	return normalized + path + suffix
}

func CanonicalType(value string, aliases AliasFile) (string, bool) {
	wanted := strings.TrimSpace(value)
	for from, to := range aliases.Aliases {
		if strings.EqualFold(strings.TrimSpace(from), wanted) {
			return strings.TrimSpace(to), true
		}
	}
	return value, false
}

func OpenReadOnly(dbPath string) (*sql.DB, error) {
	resolved, err := ValidateCopyPath(dbPath)
	if err != nil {
		return nil, err
	}
	dsn := (&url.URL{Scheme: "file", Path: resolved, RawQuery: "mode=ro&_busy_timeout=5000"}).String()
	db, err := sql.Open("sqlite3", dsn)
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return db, nil
}

// ValidateCopyPath enforces the operator's /tmp-copy-only constraint, including
// symlink resolution. The production path is never opened by this command.
func ValidateCopyPath(dbPath string) (string, error) {
	absolute, err := filepath.Abs(dbPath)
	if err != nil {
		return "", err
	}
	if !insideTmp(absolute) {
		return "", fmt.Errorf("database must be a regular SQLite copy under /tmp")
	}
	resolved, err := filepath.EvalSymlinks(dbPath)
	if err != nil {
		return "", err
	}
	resolved, err = filepath.Abs(resolved)
	if err != nil {
		return "", err
	}
	if !insideTmp(resolved) {
		return "", fmt.Errorf("database must be a regular SQLite copy under /tmp")
	}
	info, err := os.Stat(resolved)
	if err != nil {
		return "", err
	}
	if !info.Mode().IsRegular() {
		return "", fmt.Errorf("database copy must be a regular file")
	}
	return resolved, nil
}

func insideTmp(path string) bool {
	relative, err := filepath.Rel("/tmp", path)
	return err == nil && relative != "." && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator))
}

func BuildReport(db *sql.DB, aliases AliasFile) (Report, error) {
	report := Report{
		GeneratedAt:    time.Now(),
		DirtyTypes:     make(map[string]Issue),
		Severity:       make(map[string]int),
		Status:         make(map[string]int),
		OpenBySeverity: make(map[string]int),
	}
	if err := db.QueryRow(`SELECT COUNT(*) FROM vulnerabilities`).Scan(&report.Total); err != nil {
		return Report{}, err
	}

	empty, err := queryIDs(db, `SELECT id FROM vulnerabilities WHERE target IS NULL OR TRIM(target) = '' ORDER BY id`)
	if err != nil {
		return Report{}, err
	}
	report.EmptyTargets = Issue{Count: len(empty), IDs: empty}

	for _, dirty := range dirtyVulnerabilityTypes {
		ids, err := queryIDs(db, `SELECT id FROM vulnerabilities WHERE LOWER(TRIM(COALESCE(vulnerability_type,''))) = LOWER(?) ORDER BY id`, dirty)
		if err != nil {
			return Report{}, err
		}
		report.DirtyTypes[dirty] = Issue{Count: len(ids), IDs: ids}
	}

	rows, err := db.Query(`SELECT id, COALESCE(target,'') FROM vulnerabilities WHERE target IS NOT NULL AND TRIM(target) <> '' ORDER BY id`)
	if err != nil {
		return Report{}, err
	}
	targetGroups := make(map[string]*TargetChange)
	for rows.Next() {
		var id, original string
		if err := rows.Scan(&id, &original); err != nil {
			_ = rows.Close()
			return Report{}, err
		}
		normalized := NormalizeTarget(original)
		if normalized == original {
			continue
		}
		key := original + "\x00" + normalized
		if targetGroups[key] == nil {
			targetGroups[key] = &TargetChange{From: original, To: normalized}
		}
		targetGroups[key].IDs = append(targetGroups[key].IDs, id)
	}
	if err := rows.Err(); err != nil {
		_ = rows.Close()
		return Report{}, err
	}
	if err := rows.Close(); err != nil {
		return Report{}, err
	}
	for _, item := range targetGroups {
		report.TargetChanges = append(report.TargetChanges, *item)
	}
	sort.Slice(report.TargetChanges, func(i, j int) bool { return report.TargetChanges[i].From < report.TargetChanges[j].From })

	for from, to := range aliases.Aliases {
		ids, err := queryIDs(db, `SELECT id FROM vulnerabilities WHERE LOWER(TRIM(COALESCE(vulnerability_type,''))) = LOWER(?) ORDER BY id`, from)
		if err != nil {
			return Report{}, err
		}
		report.TypeMappings = append(report.TypeMappings, TypeMapping{From: from, To: to, IDs: ids})
	}
	sort.Slice(report.TypeMappings, func(i, j int) bool { return report.TypeMappings[i].From < report.TypeMappings[j].From })

	if err := queryCounts(db, `SELECT LOWER(COALESCE(severity,'')), COUNT(*) FROM vulnerabilities GROUP BY LOWER(COALESCE(severity,''))`, report.Severity); err != nil {
		return Report{}, err
	}
	if err := queryCounts(db, `SELECT LOWER(COALESCE(status,'')), COUNT(*) FROM vulnerabilities GROUP BY LOWER(COALESCE(status,''))`, report.Status); err != nil {
		return Report{}, err
	}
	if err := queryCounts(db, `SELECT LOWER(COALESCE(severity,'')), COUNT(*) FROM vulnerabilities WHERE LOWER(COALESCE(status,'')) = 'open' GROUP BY LOWER(COALESCE(severity,''))`, report.OpenBySeverity); err != nil {
		return Report{}, err
	}

	options, err := queryStrings(db, `SELECT DISTINCT TRIM(vulnerability_type) FROM vulnerabilities WHERE vulnerability_type IS NOT NULL AND TRIM(vulnerability_type) <> '' ORDER BY TRIM(vulnerability_type)`)
	if err != nil {
		return Report{}, err
	}
	report.FilterOptionsBefore = options
	after := make(map[string]struct{})
	dirty := make(map[string]struct{}, len(dirtyVulnerabilityTypes))
	for _, value := range dirtyVulnerabilityTypes {
		dirty[strings.ToLower(value)] = struct{}{}
	}
	for _, option := range options {
		if _, remove := dirty[strings.ToLower(strings.TrimSpace(option))]; remove {
			continue
		}
		canonical, _ := CanonicalType(option, aliases)
		if strings.TrimSpace(canonical) != "" {
			after[canonical] = struct{}{}
		}
	}
	report.FilterOptionsAfterCount = len(after)
	return report, nil
}

// ValidateOutputPath prevents --report from overwriting the database through
// the same pathname, a symlink or a hard link.
func ValidateOutputPath(outputPath, dbPath string) error {
	dbInfo, err := os.Stat(dbPath)
	if err != nil {
		return err
	}
	outputInfo, err := os.Stat(outputPath)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if os.SameFile(dbInfo, outputInfo) {
		return fmt.Errorf("report output must not overwrite the database copy")
	}
	return nil
}

func queryIDs(db *sql.DB, query string, args ...any) ([]string, error) {
	return queryStrings(db, query, args...)
}

func queryStrings(db *sql.DB, query string, args ...any) ([]string, error) {
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var values []string
	for rows.Next() {
		var value string
		if err := rows.Scan(&value); err != nil {
			return nil, err
		}
		values = append(values, value)
	}
	return values, rows.Err()
}

func queryCounts(db *sql.DB, query string, output map[string]int) error {
	rows, err := db.Query(query)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var name string
		var count int
		if err := rows.Scan(&name, &count); err != nil {
			return err
		}
		output[name] = count
	}
	return rows.Err()
}
