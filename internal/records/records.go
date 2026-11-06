// Package records 提供「通用提取記錄」的儲存與查詢層。
//
// 為什麼需要這一層：平台原本只有單一資料型別的專屬檢視（貸款案件主檔）。
// 但掃描器 / 代理從靶站抽到的東西並不只一種形态——貸款案件、快遞訂單、
// 帳號密碼、資產指紋、風險漏洞各有各的欄位。把這些東西硬塞進同一張表會
// 讓欄位變成萬用的 key/value，最後前端只能顯示一欄 JSON。
//
// 這裡的做法是：記錄本身是通用的（type_id + fields），但「型別 → 欄位定義」
// 是宣告式的（TypeDef.Columns）。前端拿到欄位定義就照著排欄，不需要為
// 每一種資料型別寫一份前端程式。
//
// 幾條不打折的原則：
//   - 去重是資料庫層的 UNIQUE 約束，不是「先查出來再比對」：唯一鍵是
//     (type_id, dataset, dedupe_key)，寫入走 upsert，重複資料不會產生第二列。
//   - 沒有資料就是沒有資料：型別沒有種子資料時回空集合，不塞示範列。
//   - 欄位值一律存文字：不同來源同一欄位的型別本來就不一致，轉型應該發生在
//     匯出或呈現端，而不是寫入端。
package records

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// Column 宣告一個欄位。Kind 給前端決定呈現方式，Norm 給去重鍵正規化用。
type Column struct {
	Key   string `json:"key"`
	Label string `json:"label"`
	Kind  string `json:"kind"`  // text | money | int | date | bool
	Norm  string `json:"norm"`  // text | digits | phone | alnum
	Facet bool   `json:"facet"` // 是否作為分類（facet）維度
	Width int    `json:"width,omitempty"`
}

// TypeDef 定義一種資料型別的欄位與去重規則。
type TypeDef struct {
	ID           string   `json:"id"`
	Label        string   `json:"label"`
	Description  string   `json:"description"`
	Icon         string   `json:"icon"`
	Columns      []Column `json:"columns"`
	DedupeFields []string `json:"dedupe_fields"`
	FacetColumn  string   `json:"facet_column"`
}

// Record 一筆提取記錄。
type Record struct {
	ID          int64             `json:"id"`
	TypeID      string            `json:"type_id"`
	Dataset     string            `json:"dataset"`
	Source      string            `json:"source"`
	DedupeKey   string            `json:"dedupe_key"`
	Title       string            `json:"title"`
	Fields      map[string]string `json:"fields"`
	Evidence    map[string]any    `json:"evidence"`
	ExtractedAt string            `json:"extracted_at"`
	IngestedAt  string            `json:"ingested_at"`
	HitCount    int               `json:"hit_count"`
}

// IngestInput 是一次入庫的請求。
type IngestInput struct {
	TypeID  string        `json:"type_id"`
	Dataset string        `json:"dataset"`
	Source  string        `json:"source"`
	Records []IncomingRec `json:"records"`
}

// IncomingRec 是一筆待入庫的記錄。Fields 的鍵必須是型別定義裡的欄位 key。
type IncomingRec struct {
	Key         string            `json:"key"`
	Title       string            `json:"title"`
	Fields      map[string]string `json:"fields"`
	Evidence    map[string]any    `json:"evidence"`
	ExtractedAt string            `json:"extracted_at"`
}

// IngestResult 回報入庫結果，讓呼叫端知道哪些是新資料、哪些是重複。
type IngestResult struct {
	Inserted  int `json:"inserted"`
	Updated   int `json:"updated"`
	Duplicate int `json:"duplicate"`
	Total     int `json:"total"`
}

// Page 是分頁結果。
type Page struct {
	Items    []Record `json:"items"`
	Total    int      `json:"total"`
	Page     int      `json:"page"`
	PageSize int      `json:"page_size"`
	Type     *TypeDef `json:"type,omitempty"`
}

const schemaSQL = `
CREATE TABLE IF NOT EXISTS record_types (
    type_id              TEXT PRIMARY KEY,
    label                TEXT NOT NULL,
    description          TEXT NOT NULL DEFAULT '',
    icon                 TEXT NOT NULL DEFAULT '',
    columns_json         TEXT NOT NULL DEFAULT '[]',
    dedupe_fields_json   TEXT NOT NULL DEFAULT '[]',
    facet_column         TEXT NOT NULL DEFAULT '',
    created_at           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id         TEXT NOT NULL,
    dataset         TEXT NOT NULL DEFAULT '',
    source          TEXT NOT NULL DEFAULT '',
    dedupe_key      TEXT NOT NULL,
    title           TEXT NOT NULL DEFAULT '',
    fields_json     TEXT NOT NULL DEFAULT '{}',
    evidence_json   TEXT NOT NULL DEFAULT '{}',
    extracted_at    TEXT NOT NULL DEFAULT '',
    ingested_at     TEXT NOT NULL DEFAULT '',
    hit_count       INTEGER NOT NULL DEFAULT 1,
    UNIQUE (type_id, dataset, dedupe_key)
);
CREATE INDEX IF NOT EXISTS idx_records_type ON records(type_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_records_dataset ON records(dataset);
CREATE INDEX IF NOT EXISTS idx_records_title ON records(title);
`

// Store 是提取記錄的儲存層。
type Store struct {
	dbPath string
	db     *sql.DB
}

// Open 開啟（或建立）提取記錄庫。
func Open(path string) (*Store, error) {
	if strings.TrimSpace(path) == "" {
		return nil, fmt.Errorf("records: db path is empty")
	}
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, fmt.Errorf("records: mkdir %s: %w", dir, err)
		}
	}
	dsn := "file:" + path + "?_busy_timeout=8000&_journal_mode=WAL&_foreign_keys=on"
	db, err := sql.Open("sqlite3", dsn)
	if err != nil {
		return nil, fmt.Errorf("records: open %s: %w", path, err)
	}
	db.SetMaxOpenConns(4)
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("records: ping %s: %w", path, err)
	}
	s := &Store{dbPath: path, db: db}
	if err := s.ensureSchema(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return s, nil
}

// Close 關閉底層連線。
func (s *Store) Close() error {
	if s == nil || s.db == nil {
		return nil
	}
	return s.db.Close()
}

// DBPath 回傳儲存路徑。
func (s *Store) DBPath() string {
	if s == nil {
		return ""
	}
	return s.dbPath
}

func (s *Store) ensureSchema() error {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	if _, err := s.db.ExecContext(ctx, schemaSQL); err != nil {
		return fmt.Errorf("records: schema: %w", err)
	}
	return s.SeedTypes(ctx, BuiltinTypes())
}

// SeedTypes 寫入／更新型別定義。已存在的型別會覆寫欄位定義，但不會動到資料。
func (s *Store) SeedTypes(ctx context.Context, defs []TypeDef) error {
	now := time.Now().UTC().Format(time.RFC3339)
	for _, def := range defs {
		cols, err := json.Marshal(def.Columns)
		if err != nil {
			return err
		}
		dedupe, err := json.Marshal(def.DedupeFields)
		if err != nil {
			return err
		}
		_, err = s.db.ExecContext(ctx, `
			INSERT INTO record_types (type_id, label, description, icon, columns_json, dedupe_fields_json, facet_column, created_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(type_id) DO UPDATE SET
				label = excluded.label,
				description = excluded.description,
				icon = excluded.icon,
				columns_json = excluded.columns_json,
				dedupe_fields_json = excluded.dedupe_fields_json,
				facet_column = excluded.facet_column`,
			def.ID, def.Label, def.Description, def.Icon, string(cols), string(dedupe), def.FacetColumn, now)
		if err != nil {
			return fmt.Errorf("records: seed type %s: %w", def.ID, err)
		}
	}
	return nil
}

// Types 回傳所有型別定義（含每型筆數）。
func (s *Store) Types(ctx context.Context) ([]TypeDef, map[string]int64, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT type_id, label, description, icon, columns_json, dedupe_fields_json, facet_column
		FROM record_types ORDER BY type_id`)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()
	defs := []TypeDef{}
	for rows.Next() {
		var def TypeDef
		var colsJSON, dedupeJSON string
		if err := rows.Scan(&def.ID, &def.Label, &def.Description, &def.Icon, &colsJSON, &dedupeJSON, &def.FacetColumn); err != nil {
			return nil, nil, err
		}
		_ = json.Unmarshal([]byte(colsJSON), &def.Columns)
		_ = json.Unmarshal([]byte(dedupeJSON), &def.DedupeFields)
		defs = append(defs, def)
	}
	if err := rows.Err(); err != nil {
		return nil, nil, err
	}
	counts, err := s.typeCounts(ctx)
	if err != nil {
		return nil, nil, err
	}
	return defs, counts, nil
}

func (s *Store) typeCounts(ctx context.Context) (map[string]int64, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT type_id, COUNT(*) FROM records GROUP BY type_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string]int64{}
	for rows.Next() {
		var id string
		var n int64
		if err := rows.Scan(&id, &n); err != nil {
			return nil, err
		}
		out[id] = n
	}
	return out, rows.Err()
}

// TypeDefOf 取單一型別定義。
func (s *Store) TypeDefOf(ctx context.Context, typeID string) (*TypeDef, error) {
	var def TypeDef
	var colsJSON, dedupeJSON string
	err := s.db.QueryRowContext(ctx, `
		SELECT type_id, label, description, icon, columns_json, dedupe_fields_json, facet_column
		FROM record_types WHERE type_id = ?`, typeID).
		Scan(&def.ID, &def.Label, &def.Description, &def.Icon, &colsJSON, &dedupeJSON, &def.FacetColumn)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	_ = json.Unmarshal([]byte(colsJSON), &def.Columns)
	_ = json.Unmarshal([]byte(dedupeJSON), &def.DedupeFields)
	return &def, nil
}

// DedupeKey 依型別定義算出去重鍵。
//
// 優先用型別宣告的 dedupe_fields（依序串接）；沒宣告時退而求其次，
// 用整個 fields 的正規化雜湊。兩種情況下結果都只跟內容有關，跟寫入順序、
// 來源時間或來源主機無關 —— 這是「不同掃描器掃到同一筆資料不會重複」的前提。
func DedupeKey(def *TypeDef, fields map[string]string) string {
	if def == nil {
		return ""
	}
	norm := map[string]string{}
	for _, col := range def.Columns {
		norm[col.Key] = normalizeValue(fields[col.Key], col.Norm)
	}
	if len(def.DedupeFields) > 0 {
		parts := make([]string, 0, len(def.DedupeFields))
		for _, key := range def.DedupeFields {
			parts = append(parts, norm[key])
		}
		joined := strings.Join(parts, "|")
		if strings.Trim(joined, "|") != "" {
			return joined
		}
	}
	keys := make([]string, 0, len(norm))
	for k := range norm {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, k+"="+norm[k])
	}
	return strings.Join(parts, ";")
}

// 字元類一定要含大寫（0-9a-zA-ZÀ-ỹ）。
// 原本寫成 [^0-9a-zÀ-ỹ]+ 會把大寫英文字母當成「非字母」刪掉，
// 導致 PM2306020VCA → 2306020、P122721001 → 122721001，
// 於是不同的人 / 不同的案件被誤判成同一筆而合併
// （實測讓中租 28,678 案塌成 15,772 筆，新鑫不同申請人也被併）。
var nonAlnum = regexp.MustCompile(`[^0-9a-zA-ZÀ-ỹ]+`)

// normalizeValue 正規化欄位值，讓同一筆資料的不同寫法對應到同一個去重鍵。
func normalizeValue(v, norm string) string {
	s := strings.TrimSpace(v)
	switch norm {
	case "digits":
		var b strings.Builder
		for _, r := range s {
			if r >= '0' && r <= '9' {
				b.WriteRune(r)
			}
		}
		return b.String()
	case "phone":
		var b strings.Builder
		for _, r := range s {
			if r >= '0' && r <= '9' {
				b.WriteRune(r)
			}
		}
		out := b.String()
		// 越南／台灣號碼常寫成 0xx xxx xxx，去掉前導 0 讓 0912345678 與
		// 912345678 視為同一筆。但要保留短號這類非電話字串的原樣。
		if len(out) > 9 && out[0] == '0' {
			out = strings.TrimLeft(out, "0")
		}
		return out
	case "alnum":
		return strings.ToLower(nonAlnum.ReplaceAllString(s, ""))
	default:
		return strings.ToLower(strings.Join(strings.Fields(s), " "))
	}
}

// Ingest 寫入一批記錄並去重。
//
// 去重是 upsert：同 (type_id, dataset, dedupe_key) 再來一次時更新欄位與
// 擷取時間，並把 hit_count 加一，而不是產生第二列。呼叫端因此可以安全地
// 對同一份來源重複匯入。
func (s *Store) Ingest(ctx context.Context, in IngestInput) (*IngestResult, error) {
	if strings.TrimSpace(in.TypeID) == "" {
		return nil, fmt.Errorf("records: type_id is required")
	}
	def, err := s.TypeDefOf(ctx, in.TypeID)
	if err != nil {
		return nil, err
	}
	if def == nil {
		return nil, fmt.Errorf("records: unknown type %q", in.TypeID)
	}
	dataset := strings.TrimSpace(in.Dataset)
	source := strings.TrimSpace(in.Source)
	now := time.Now().UTC().Format(time.RFC3339)

	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer func() { _ = tx.Rollback() }()

	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO records (type_id, dataset, source, dedupe_key, title, fields_json,
		                     evidence_json, extracted_at, ingested_at, hit_count)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
		ON CONFLICT(type_id, dataset, dedupe_key) DO UPDATE SET
			source = excluded.source,
			title = excluded.title,
			fields_json = excluded.fields_json,
			evidence_json = excluded.evidence_json,
			extracted_at = excluded.extracted_at,
			ingested_at = excluded.ingested_at,
			hit_count = records.hit_count + 1`)
	if err != nil {
		return nil, err
	}
	defer stmt.Close()

	res := &IngestResult{}
	for _, rec := range in.Records {
		fields := map[string]string{}
		for k, v := range rec.Fields {
			fields[k] = v
		}
		key := strings.TrimSpace(rec.Key)
		if key == "" {
			key = DedupeKey(def, fields)
		}
		if key == "" {
			continue
		}
		fieldsJSON, err := json.Marshal(fields)
		if err != nil {
			return nil, err
		}
		evidenceJSON := []byte("{}")
		if len(rec.Evidence) > 0 {
			b, err := json.Marshal(rec.Evidence)
			if err != nil {
				return nil, err
			}
			evidenceJSON = b
		}
		title := strings.TrimSpace(rec.Title)
		if title == "" {
			title = deriveTitle(def, fields)
		}
		extractedAt := strings.TrimSpace(rec.ExtractedAt)
		if extractedAt == "" {
			extractedAt = now
		}
		// 先確認這把去重鍵是否已經存在，才能分辨「新增」與「重複命中」。
		// SQLite 的 upsert 不論新增或更新都回 RowsAffected=1，事後查已經分不出來。
		exists, err := s.rowExists(ctx, tx, in.TypeID, dataset, key)
		if err != nil {
			return nil, err
		}
		if _, err := stmt.ExecContext(ctx, in.TypeID, dataset, source, key, title,
			string(fieldsJSON), string(evidenceJSON), extractedAt, now); err != nil {
			return nil, fmt.Errorf("records: upsert %s: %w", key, err)
		}
		res.Total++
		if exists {
			res.Updated++
		} else {
			res.Inserted++
		}
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	return res, nil
}

func (s *Store) rowExists(ctx context.Context, tx *sql.Tx, typeID, dataset, key string) (bool, error) {
	var n int
	err := tx.QueryRowContext(ctx,
		`SELECT COUNT(*) FROM records WHERE type_id = ? AND dataset = ? AND dedupe_key = ?`,
		typeID, dataset, key).Scan(&n)
	if err != nil {
		return false, err
	}
	return n > 0, nil
}

func deriveTitle(def *TypeDef, fields map[string]string) string {
	if def == nil {
		return ""
	}
	for _, col := range def.Columns {
		if v := strings.TrimSpace(fields[col.Key]); v != "" {
			return v
		}
	}
	return ""
}

// ListQuery 是列表查詢條件。
type ListQuery struct {
	TypeID   string
	Dataset  string
	Query    string
	Page     int
	PageSize int
	// SortBy 是要排序的欄位 key（必須是該型別定義裡宣告過的欄位，
	// 否則忽略）。SortDir 為 "asc" 或 "desc"（預設 desc）。
	// 為什麼需要：記錄是依匯入順序寫入的，若固定用 id DESC，
	// 第一頁會落在「最早匯入的那批」，常常正好是資料最稀疏的舊資料，
	// 看起來像沒資料。讓前端可指定日期欄位做「最新優先」。
	SortBy  string
	SortDir string
}

// List 依條件分頁查詢記錄。
func (s *Store) List(ctx context.Context, q ListQuery) (*Page, error) {
	if q.Page <= 0 {
		q.Page = 1
	}
	if q.PageSize <= 0 {
		q.PageSize = 50
	}
	if q.PageSize > 500 {
		q.PageSize = 500
	}
	where := []string{"1=1"}
	args := []any{}
	if strings.TrimSpace(q.TypeID) != "" {
		where = append(where, "type_id = ?")
		args = append(args, q.TypeID)
	}
	if strings.TrimSpace(q.Dataset) != "" {
		where = append(where, "dataset = ?")
		args = append(args, q.Dataset)
	}
	if strings.TrimSpace(q.Query) != "" {
		where = append(where, "(title LIKE ? OR fields_json LIKE ?)")
		like := "%" + q.Query + "%"
		args = append(args, like, like)
	}
	cond := strings.Join(where, " AND ")
	countArgs := args

	// 排序：欄位必須是該型別宣告過的欄位，否則退回 id DESC。
	orderBy := "id DESC"
	sortArg := ""
	if col, ok := s.sortableColumn(ctx, q.TypeID, q.SortBy); ok {
		dir := "DESC"
		if strings.EqualFold(strings.TrimSpace(q.SortDir), "asc") {
			dir = "ASC"
		}
		orderBy = "json_extract(fields_json, '$.' || ?) " + dir + ", id DESC"
		sortArg = col
	}

	var total int
	if err := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM records WHERE "+cond, countArgs...).Scan(&total); err != nil {
		return nil, err
	}
	offset := (q.Page - 1) * q.PageSize
	listArgs := append([]any{}, countArgs...)
	if sortArg != "" {
		listArgs = append(listArgs, sortArg)
	}
	listArgs = append(listArgs, q.PageSize, offset)
	rows, err := s.db.QueryContext(ctx,
		"SELECT id, type_id, dataset, source, dedupe_key, title, fields_json, evidence_json, extracted_at, ingested_at, hit_count "+
			"FROM records WHERE "+cond+" ORDER BY "+orderBy+" LIMIT ? OFFSET ?",
		listArgs...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []Record{}
	for rows.Next() {
		var rec Record
		var fieldsJSON, evidenceJSON string
		if err := rows.Scan(&rec.ID, &rec.TypeID, &rec.Dataset, &rec.Source, &rec.DedupeKey,
			&rec.Title, &fieldsJSON, &evidenceJSON, &rec.ExtractedAt, &rec.IngestedAt, &rec.HitCount); err != nil {
			return nil, err
		}
		rec.Fields = map[string]string{}
		rec.Evidence = map[string]any{}
		_ = json.Unmarshal([]byte(fieldsJSON), &rec.Fields)
		_ = json.Unmarshal([]byte(evidenceJSON), &rec.Evidence)
		items = append(items, rec)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	page := &Page{Items: items, Total: total, Page: q.Page, PageSize: q.PageSize}
	if q.TypeID != "" {
		if def, err := s.TypeDefOf(ctx, q.TypeID); err == nil {
			page.Type = def
		}
	}
	return page, nil
}

// AllRows 取符合條件的全部記錄（匯出用）。
func (s *Store) AllRows(ctx context.Context, q ListQuery) ([]Record, error) {
	q.Page = 1
	q.PageSize = 0
	where := []string{"1=1"}
	args := []any{}
	if strings.TrimSpace(q.TypeID) != "" {
		where = append(where, "type_id = ?")
		args = append(args, q.TypeID)
	}
	if strings.TrimSpace(q.Dataset) != "" {
		where = append(where, "dataset = ?")
		args = append(args, q.Dataset)
	}
	if strings.TrimSpace(q.Query) != "" {
		where = append(where, "(title LIKE ? OR fields_json LIKE ?)")
		like := "%" + q.Query + "%"
		args = append(args, like, like)
	}
	rows, err := s.db.QueryContext(ctx,
		"SELECT id, type_id, dataset, source, dedupe_key, title, fields_json, evidence_json, extracted_at, ingested_at, hit_count "+
			"FROM records WHERE "+strings.Join(where, " AND ")+" ORDER BY id DESC", args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []Record{}
	for rows.Next() {
		var rec Record
		var fieldsJSON, evidenceJSON string
		if err := rows.Scan(&rec.ID, &rec.TypeID, &rec.Dataset, &rec.Source, &rec.DedupeKey,
			&rec.Title, &fieldsJSON, &evidenceJSON, &rec.ExtractedAt, &rec.IngestedAt, &rec.HitCount); err != nil {
			return nil, err
		}
		rec.Fields = map[string]string{}
		rec.Evidence = map[string]any{}
		_ = json.Unmarshal([]byte(fieldsJSON), &rec.Fields)
		_ = json.Unmarshal([]byte(evidenceJSON), &rec.Evidence)
		out = append(out, rec)
	}
	return out, rows.Err()
}

// Facet 回傳某個分類維度的統計。
func (s *Store) Facet(ctx context.Context, typeID, column string) ([]FacetBucket, error) {
	if strings.TrimSpace(typeID) == "" || strings.TrimSpace(column) == "" {
		return nil, nil
	}
	rows, err := s.db.QueryContext(ctx,
		`SELECT json_extract(fields_json, '$.' || ?) AS value, COUNT(*) FROM records WHERE type_id = ? GROUP BY value ORDER BY COUNT(*) DESC, value`,
		column, typeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []FacetBucket{}
	for rows.Next() {
		var value sql.NullString
		var n int64
		if err := rows.Scan(&value, &n); err != nil {
			return nil, err
		}
		label := strings.TrimSpace(value.String)
		if label == "" {
			label = "(空)"
		}
		out = append(out, FacetBucket{Value: label, Count: n})
	}
	return out, rows.Err()
}

// FacetBucket 是一個分類桶。
type FacetBucket struct {
	Value string `json:"value"`
	Count int64  `json:"count"`
}

// sortableColumn 確認要排序的欄位確實是該型別宣告過的欄位。
// 只認型別定義裡的欄位 → 不會讓呼叫端把任意字串送進 SQL。
func (s *Store) sortableColumn(ctx context.Context, typeID, key string) (string, bool) {
	key = strings.TrimSpace(key)
	if key == "" || strings.TrimSpace(typeID) == "" {
		return "", false
	}
	def, err := s.TypeDefOf(ctx, typeID)
	if err != nil || def == nil {
		return "", false
	}
	for _, col := range def.Columns {
		if col.Key == key {
			return key, true
		}
	}
	return "", false
}

// ColumnFill 統計某型別每個欄位「有多少筆有值」。
//
// 為什麼需要：主控台若把型別定義裡所有欄位都秀出來，遇到資料本來就稀疏的
// 型別（例如只有案件編號、日期、金額來源欄有值的案件主檔），畫面會半屏空白，
// 看起來像沒抓到資料。有了這個數字，前端可以把有值率直接標在欄位名上，
// 並預設只顯示真的有資料的欄位。
func (s *Store) ColumnFill(ctx context.Context, typeID string) (map[string]int64, error) {
	out := map[string]int64{}
	if strings.TrimSpace(typeID) == "" {
		return out, nil
	}
	rows, err := s.db.QueryContext(ctx,
		"SELECT fields_json FROM records WHERE type_id = ?", typeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		var m map[string]any
		if err := json.Unmarshal([]byte(raw), &m); err != nil {
			continue
		}
		for k, v := range m {
			if strings.TrimSpace(fmt.Sprint(v)) == "" {
				continue
			}
			out[k]++
		}
	}
	return out, rows.Err()
}

// Datasets 回傳所有資料集名稱與筆數。
func (s *Store) Datasets(ctx context.Context) ([]FacetBucket, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT dataset, COUNT(*) FROM records GROUP BY dataset ORDER BY COUNT(*) DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []FacetBucket{}
	for rows.Next() {
		var ds string
		var n int64
		if err := rows.Scan(&ds, &n); err != nil {
			return nil, err
		}
		if strings.TrimSpace(ds) == "" {
			ds = "(未指定)"
		}
		out = append(out, FacetBucket{Value: ds, Count: n})
	}
	return out, rows.Err()
}

// exportColumn 是匯出時實際輸出的欄位（資料欄位 key + 顯示標籤）。
type exportColumn struct {
	key   string
	label string
}

// exportColumns 決定 CSV 匯出要包含哪些欄位。
//
// 這條規則必須跟前端 web/static/js/records.js 的 renderTable 一致，
// 否則會出現「網頁看得到、匯出看不到」的不一致：
//  1. 宣告了、但整個型別都沒有值的欄位 → 拿掉
//     （否則匯出檔會出現整欄空白，看起來像沒抓到資料）
//  2. 資料裡有值、但型別定義沒宣告的欄位 → 補上
//     （否則真正的資料會整個從匯出檔消失）
//
// 2026-11-06 實測：member_profile 匯出 11 欄中 7 欄全空，而真正有內容的
// channel／business 一個都沒被匯出 —— 這是本函式只照 def.Columns 硬列造成的。
//
// 順序：先照型別宣告順序，再把額外欄位以 key 字母序補在後面。
// 字母序是必要的：Go 的 map 迭代順序不保穩定，不排序匯出檔就無法 diff。
func exportColumns(def *TypeDef, rows []Record) []exportColumn {
	if def == nil {
		return nil
	}
	declared := map[string]bool{}
	for _, c := range def.Columns {
		declared[c.Key] = true
	}
	hasValue := map[string]bool{}
	extra := map[string]bool{}
	for _, rec := range rows {
		for k, v := range rec.Fields {
			if strings.TrimSpace(v) == "" {
				continue
			}
			hasValue[k] = true
			if !declared[k] {
				extra[k] = true
			}
		}
	}
	cols := make([]exportColumn, 0, len(def.Columns)+len(extra))
	for _, c := range def.Columns {
		if !hasValue[c.Key] {
			continue
		}
		cols = append(cols, exportColumn{key: c.Key, label: c.Label})
	}
	extras := make([]string, 0, len(extra))
	for k := range extra {
		extras = append(extras, k)
	}
	sort.Strings(extras)
	for _, k := range extras {
		cols = append(cols, exportColumn{key: k, label: k})
	}
	return cols
}

// FormatCSV 把記錄轉成 CSV 內容。欄位選取規則見 exportColumns。
func FormatCSV(def *TypeDef, rows []Record) ([]string, [][]string) {
	cols := exportColumns(def, rows)
	if len(cols) == 0 {
		// 沒有型別定義，或該型別所有欄位都沒有值 → 退回通用欄位，
		// 避免產生只有空白標題列的 CSV。
		header := []string{"類型", "資料集", "標題", "擷取時間"}
		out := make([][]string, 0, len(rows))
		for _, rec := range rows {
			out = append(out, []string{rec.TypeID, rec.Dataset, rec.Title, rec.ExtractedAt})
		}
		return header, out
	}
	header := make([]string, 0, len(cols))
	for _, c := range cols {
		header = append(header, c.label)
	}
	out := make([][]string, 0, len(rows))
	for _, rec := range rows {
		line := make([]string, 0, len(cols))
		for _, c := range cols {
			line = append(line, rec.Fields[c.key])
		}
		out = append(out, line)
	}
	return header, out
}

// FormatNumber 讓前端顯示金額／數量時不靠前端自己處理千分位。
func FormatNumber(v string) string {
	s := strings.TrimSpace(v)
	if s == "" {
		return ""
	}
	if _, err := strconv.ParseFloat(s, 64); err != nil {
		return s
	}
	return s
}
