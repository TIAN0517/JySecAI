package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"jysecai/internal/redirect"
)

// 批次受控跳轉驗證的持久化。
//
// 這是長跑工作：一次可能跑上千個目標，必須能中途查進度、可以取消、結果要能落地
// （頁面重新整理不會消失），所以批次本身與每筆結果都存進資料庫。

const (
	// RedirectVerifyStatusPending 表示批次已建立但尚未開始。
	RedirectVerifyStatusPending = "pending"
	// RedirectVerifyStatusRunning 表示批次執行中。
	RedirectVerifyStatusRunning = "running"
	// RedirectVerifyStatusCompleted 表示批次正常跑完。
	RedirectVerifyStatusCompleted = "completed"
	// RedirectVerifyStatusCancelled 表示批次被取消。
	RedirectVerifyStatusCancelled = "cancelled"
	// RedirectVerifyStatusFailed 表示批次因錯誤中止。
	RedirectVerifyStatusFailed = "failed"
)

// RedirectVerifyRun 是一批次受控跳轉驗證。
type RedirectVerifyRun struct {
	ID             string   `json:"id"`
	Status         string   `json:"status"`
	Endpoints      []string `json:"endpoints"`
	Param          string   `json:"param,omitempty"`
	Method         string   `json:"method"`
	Concurrency    int      `json:"concurrency"`
	Total          int      `json:"total"`
	Completed      int      `json:"completed"`
	Confirmed      int      `json:"confirmed"`
	ProjectID      string   `json:"project_id,omitempty"`
	ConversationID string   `json:"conversation_id,omitempty"`
	OwnerUserID    string   `json:"owner_user_id,omitempty"`
	AutoRecord     bool     `json:"auto_record"`
	// Proxy 是本次使用的代理出口（已遮蔽帳密）；空字串代表直連。
	Proxy string `json:"proxy,omitempty"`
	// ProxyGroup 是使用的代理池群組名稱（例如 residential）；空字串代表未使用代理池。
	ProxyGroup  string    `json:"proxy_group,omitempty"`
	Error       string    `json:"error,omitempty"`
	CancelAsked bool      `json:"cancel_asked"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	StartedAt   time.Time `json:"started_at,omitempty"`
	CompletedAt time.Time `json:"completed_at,omitempty"`

	// CrawlEnabled 表示這批要先自動巡站、找出站上本來就有的跳轉入口，再驗證。
	//
	// 這是「自動植入」的開關：開啟後，站點本來的跳轉參數（不是猜的參數名）
	// 會被拿來代入操作者指定的受控端點。
	CrawlEnabled bool `json:"crawl_enabled"`
	// CrawlMaxPages / CrawlMaxDepth 是巡站的上限。
	CrawlMaxPages int `json:"crawl_max_pages"`
	CrawlMaxDepth int `json:"crawl_max_depth"`
	// SeedSource 是種子來源：manual（請求內附的目標）、assets（資產庫）、
	// vulns（漏洞紀錄）。
	SeedSource string `json:"seed_source,omitempty"`
	// SeedKeyword 是從資產庫／漏洞紀錄挑站點時用的分類關鍵字（例如 娛樂城、SEO）。
	SeedKeyword string `json:"seed_keyword,omitempty"`
	// SeedCount 是實際採用的種子站點數。
	SeedCount int `json:"seed_count"`
	// CrawlCandidates 是巡站找到的跳轉入口候選數。
	CrawlCandidates int `json:"crawl_candidates"`
	// Phase 是目前進度階段：crawl（巡站中）、verify（驗證中）、done。
	Phase string `json:"phase,omitempty"`
	// Encoding 是受控端點寫進 payload 時的編碼方式（none／percent／base64…）。
	Encoding string `json:"encoding,omitempty"`
	// Repeat 是同一個目標重複探測幾次（1 = 不重複）。
	//
	// 用來量「穩不穩」：命中一次可能是巧合，重複複測都一致才算可信。
	Repeat int `json:"repeat"`
	// InjectionCount 是巡站時在頁面裡找到的注入點總數。
	InjectionCount int `json:"injection_count"`
	// ThirdPartyInjections 是其中指向外部主機的（真正的第三方注入）。
	ThirdPartyInjections int `json:"third_party_injections"`
	// Injections 是巡站時實際找到的注入點（JSON 序列化後落地）。
	//
	// 這是「把他們注入的換成我們的」的定位結果：前端可以直接挑一個點，
	// 呼叫植入 API 產生替換片段。
	Injections []redirect.InjectionPoint `json:"injections,omitempty"`
}

// RedirectVerifyResult 是批次裡單一目標的驗證結果。
type RedirectVerifyResult struct {
	ID        string `json:"id"`
	RunID     string `json:"run_id"`
	URL       string `json:"url"`
	Confirmed bool   `json:"confirmed"`
	Param     string `json:"param,omitempty"`
	// OwnParam 是目標網址本來就帶著的跳轉參數名（空字串代表沒有）。
	OwnParam string `json:"own_param,omitempty"`
	// ParamsTried 是實際送出過的參數名（逗號分隔儲存）。
	//
	// 沒有這欄時報表只顯示「最後一次試的參數」，會讓人以為只試過一個參數。
	ParamsTried     []string `json:"params_tried,omitempty"`
	RequestURL      string   `json:"request_url,omitempty"`
	Status          int      `json:"status"`
	Location        string   `json:"location,omitempty"`
	Error           string   `json:"error,omitempty"`
	VulnerabilityID string   `json:"vulnerability_id,omitempty"`
	// Evidence 是證據等級：location（真的 3xx 跳轉）、body_echo（本文回顯，
	// 不是跳轉）、none（沒證據）。
	Evidence string `json:"evidence,omitempty"`
	// BodyEcho 為 true 表示只是回應本文回顯了受控端點 —— 偽陽性來源，
	// 不計入 confirmed。
	BodyEcho bool `json:"body_echo,omitempty"`
	// OwnParamHit 為 true 表示命中的參數就是站上本來就有的那一個。
	OwnParamHit bool `json:"own_param_hit,omitempty"`
	// Attempts 是這個目標實際送出的探測次數。
	Attempts int `json:"attempts,omitempty"`
	// Stable 為 true 表示重複探測的結果一致。
	Stable    bool      `json:"stable"`
	CreatedAt time.Time `json:"created_at"`
}

const createRedirectVerifyRunsTable = `
	CREATE TABLE IF NOT EXISTS redirect_verify_runs (
		id TEXT PRIMARY KEY,
		status TEXT NOT NULL DEFAULT 'pending',
		endpoints TEXT NOT NULL DEFAULT '',
		param TEXT NOT NULL DEFAULT '',
		method TEXT NOT NULL DEFAULT 'GET',
		concurrency INTEGER NOT NULL DEFAULT 4,
		total INTEGER NOT NULL DEFAULT 0,
		completed INTEGER NOT NULL DEFAULT 0,
		confirmed INTEGER NOT NULL DEFAULT 0,
		project_id TEXT,
		conversation_id TEXT,
		owner_user_id TEXT,
		auto_record INTEGER NOT NULL DEFAULT 0,
		proxy TEXT NOT NULL DEFAULT '',
		proxy_group TEXT NOT NULL DEFAULT '',
		crawl_enabled INTEGER NOT NULL DEFAULT 0,
		crawl_max_pages INTEGER NOT NULL DEFAULT 10,
		crawl_max_depth INTEGER NOT NULL DEFAULT 1,
		seed_source TEXT NOT NULL DEFAULT 'manual',
		seed_keyword TEXT NOT NULL DEFAULT '',
		seed_count INTEGER NOT NULL DEFAULT 0,
		crawl_candidates INTEGER NOT NULL DEFAULT 0,
		phase TEXT NOT NULL DEFAULT '',
		encoding TEXT NOT NULL DEFAULT 'none',
		repeat INTEGER NOT NULL DEFAULT 1,
		injection_count INTEGER NOT NULL DEFAULT 0,
		third_party_injections INTEGER NOT NULL DEFAULT 0,
		injections TEXT NOT NULL DEFAULT '',
		error TEXT NOT NULL DEFAULT '',
		cancel_asked INTEGER NOT NULL DEFAULT 0,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		started_at DATETIME,
		completed_at DATETIME
	);`

const createRedirectVerifyResultsTable = `
	CREATE TABLE IF NOT EXISTS redirect_verify_results (
		id TEXT PRIMARY KEY,
		run_id TEXT NOT NULL,
		url TEXT NOT NULL,
		confirmed INTEGER NOT NULL DEFAULT 0,
		param TEXT NOT NULL DEFAULT '',
		own_param TEXT NOT NULL DEFAULT '',
		params_tried TEXT NOT NULL DEFAULT '',
		request_url TEXT NOT NULL DEFAULT '',
		status INTEGER NOT NULL DEFAULT 0,
		location TEXT NOT NULL DEFAULT '',
		error TEXT NOT NULL DEFAULT '',
		evidence TEXT NOT NULL DEFAULT '',
		body_echo INTEGER NOT NULL DEFAULT 0,
		own_param_hit INTEGER NOT NULL DEFAULT 0,
		attempts INTEGER NOT NULL DEFAULT 0,
		stable INTEGER NOT NULL DEFAULT 1,
		vulnerability_id TEXT,
		created_at DATETIME NOT NULL,
		FOREIGN KEY (run_id) REFERENCES redirect_verify_runs(id) ON DELETE CASCADE
	);`

// initRedirectVerifyTables 建立批次驗證相關的資料表。
func (db *DB) initRedirectVerifyTables() error {
	if _, err := db.Exec(createRedirectVerifyRunsTable); err != nil {
		return fmt.Errorf("创建redirect_verify_runs表失败: %w", err)
	}
	if _, err := db.Exec(createRedirectVerifyResultsTable); err != nil {
		return fmt.Errorf("创建redirect_verify_results表失败: %w", err)
	}
	// 舊資料檔可能已經有這張表：欄位用 ALTER 補齊，已存在時忽略錯誤。
	if _, err := db.Exec(`ALTER TABLE redirect_verify_runs ADD COLUMN proxy TEXT NOT NULL DEFAULT ''`); err != nil {
		if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
			return fmt.Errorf("迁移redirect_verify_runs.proxy失败: %w", err)
		}
	}
	if _, err := db.Exec(`ALTER TABLE redirect_verify_runs ADD COLUMN proxy_group TEXT NOT NULL DEFAULT ''`); err != nil {
		if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
			return fmt.Errorf("迁移redirect_verify_runs.proxy_group失败: %w", err)
		}
	}
	// 結果表補欄位：own_param / params_tried。
	// 舊資料檔沒有這兩欄，用 ALTER 補齊（已有時忽略錯誤）。
	if _, err := db.Exec(`ALTER TABLE redirect_verify_results ADD COLUMN own_param TEXT NOT NULL DEFAULT ''`); err != nil {
		if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
			return fmt.Errorf("迁移redirect_verify_results.own_param失败: %w", err)
		}
	}
	if _, err := db.Exec(`ALTER TABLE redirect_verify_results ADD COLUMN params_tried TEXT NOT NULL DEFAULT ''`); err != nil {
		if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
			return fmt.Errorf("迁移redirect_verify_results.params_tried失败: %w", err)
		}
	}
	// 批次表補欄位：自動巡站與種子來源。
	// 舊資料檔沒有這些欄位，用 ALTER 補齊（已有時忽略錯誤）。
	for _, migration := range []struct {
		column string
		decl   string
	}{
		{"crawl_enabled", "INTEGER NOT NULL DEFAULT 0"},
		{"crawl_max_pages", "INTEGER NOT NULL DEFAULT 10"},
		{"crawl_max_depth", "INTEGER NOT NULL DEFAULT 1"},
		{"seed_source", "TEXT NOT NULL DEFAULT 'manual'"},
		{"seed_keyword", "TEXT NOT NULL DEFAULT ''"},
		{"seed_count", "INTEGER NOT NULL DEFAULT 0"},
		{"encoding", "TEXT NOT NULL DEFAULT 'none'"},
		{"crawl_candidates", "INTEGER NOT NULL DEFAULT 0"},
		{"phase", "TEXT NOT NULL DEFAULT ''"},
		{"repeat", "INTEGER NOT NULL DEFAULT 1"},
		{"injection_count", "INTEGER NOT NULL DEFAULT 0"},
		{"third_party_injections", "INTEGER NOT NULL DEFAULT 0"},
		{"injections", "TEXT NOT NULL DEFAULT ''"},
	} {
		if _, err := db.Exec(fmt.Sprintf("ALTER TABLE redirect_verify_runs ADD COLUMN %s %s", migration.column, migration.decl)); err != nil {
			if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
				return fmt.Errorf("迁移redirect_verify_runs.%s失败: %w", migration.column, err)
			}
		}
	}
	// 結果表補欄位：證據等級與精準度指標。
	for _, migration := range []struct {
		column string
		decl   string
	}{
		{"evidence", "TEXT NOT NULL DEFAULT ''"},
		{"body_echo", "INTEGER NOT NULL DEFAULT 0"},
		{"own_param_hit", "INTEGER NOT NULL DEFAULT 0"},
		{"attempts", "INTEGER NOT NULL DEFAULT 0"},
		{"stable", "INTEGER NOT NULL DEFAULT 1"},
	} {
		if _, err := db.Exec(fmt.Sprintf("ALTER TABLE redirect_verify_results ADD COLUMN %s %s", migration.column, migration.decl)); err != nil {
			if !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
				return fmt.Errorf("迁移redirect_verify_results.%s失败: %w", migration.column, err)
			}
		}
	}
	return nil
}

// CreateRedirectVerifyRun 建立批次。
func (db *DB) CreateRedirectVerifyRun(run *RedirectVerifyRun) error {
	if run == nil {
		return fmt.Errorf("批次內容不能為空")
	}
	if run.ID == "" {
		run.ID = uuid.New().String()
	}
	if strings.TrimSpace(run.Status) == "" {
		run.Status = RedirectVerifyStatusPending
	}
	if strings.TrimSpace(run.Method) == "" {
		run.Method = "GET"
	}
	now := time.Now()
	if run.CreatedAt.IsZero() {
		run.CreatedAt = now
	}
	run.UpdatedAt = now

	_, err := db.Exec(
		`INSERT INTO redirect_verify_runs (
			id, status, endpoints, param, method, concurrency, total, completed, confirmed,
			project_id, conversation_id, owner_user_id, auto_record, proxy, proxy_group,
			crawl_enabled, crawl_max_pages, crawl_max_depth, seed_source, seed_keyword,
			seed_count, crawl_candidates, phase, encoding, repeat, injection_count,
			third_party_injections, injections, error, cancel_asked,
			created_at, updated_at, started_at, completed_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		run.ID, run.Status, strings.Join(run.Endpoints, "\n"), run.Param, run.Method,
		run.Concurrency, run.Total, run.Completed, run.Confirmed,
		nullIfEmpty(run.ProjectID), nullIfEmpty(run.ConversationID), nullIfEmpty(run.OwnerUserID),
		boolToInt(run.AutoRecord), run.Proxy, run.ProxyGroup,
		boolToInt(run.CrawlEnabled), run.CrawlMaxPages, run.CrawlMaxDepth,
		run.SeedSource, run.SeedKeyword, run.SeedCount, run.CrawlCandidates, run.Phase,
		run.Encoding, run.Repeat, run.InjectionCount, run.ThirdPartyInjections,
		marshalInjections(run.Injections),
		run.Error, boolToInt(run.CancelAsked),
		run.CreatedAt, run.UpdatedAt, nullTimePtr(run.StartedAt), nullTimePtr(run.CompletedAt),
	)
	if err != nil {
		return fmt.Errorf("建立跳轉驗證批次失敗: %w", err)
	}
	return nil
}

// GetRedirectVerifyRun 取得單一批次。
func (db *DB) GetRedirectVerifyRun(id string) (*RedirectVerifyRun, error) {
	id = strings.TrimSpace(id)
	if id == "" {
		return nil, fmt.Errorf("批次 ID 為空")
	}
	row := db.QueryRow(redirectVerifyRunSelect+" WHERE id = ?", id)
	run, err := scanRedirectVerifyRun(row)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("批次不存在")
		}
		return nil, fmt.Errorf("取得跳轉驗證批次失敗: %w", err)
	}
	return run, nil
}

const redirectVerifyRunSelect = `SELECT id, status, endpoints, param, method, concurrency, total, completed, confirmed,
	COALESCE(project_id,''), COALESCE(conversation_id,''), COALESCE(owner_user_id,''), auto_record,
	COALESCE(proxy,''), COALESCE(proxy_group,''), COALESCE(error,''), cancel_asked,
	crawl_enabled, crawl_max_pages, crawl_max_depth,
	COALESCE(seed_source,'manual'), COALESCE(seed_keyword,''), seed_count, crawl_candidates, COALESCE(phase,''), COALESCE(encoding,'none'),
	COALESCE(repeat,1), COALESCE(injection_count,0), COALESCE(third_party_injections,0), COALESCE(injections,''),
	created_at, updated_at, started_at, completed_at FROM redirect_verify_runs`

type redirectVerifyRowScanner interface {
	Scan(dest ...interface{}) error
}

func scanRedirectVerifyRun(row redirectVerifyRowScanner) (*RedirectVerifyRun, error) {
	var run RedirectVerifyRun
	var endpoints string
	var autoRecord, cancelAsked int
	var crawlEnabled int
	var injections string
	var createdAt, updatedAt string
	var startedAt, completedAt sql.NullString
	err := row.Scan(
		&run.ID, &run.Status, &endpoints, &run.Param, &run.Method, &run.Concurrency,
		&run.Total, &run.Completed, &run.Confirmed,
		&run.ProjectID, &run.ConversationID, &run.OwnerUserID, &autoRecord,
		&run.Proxy, &run.ProxyGroup, &run.Error, &cancelAsked,
		&crawlEnabled, &run.CrawlMaxPages, &run.CrawlMaxDepth,
		&run.SeedSource, &run.SeedKeyword, &run.SeedCount, &run.CrawlCandidates, &run.Phase, &run.Encoding,
		&run.Repeat, &run.InjectionCount, &run.ThirdPartyInjections, &injections,
		&createdAt, &updatedAt, &startedAt, &completedAt,
	)
	if err != nil {
		return nil, err
	}
	run.Endpoints = splitNonEmptyLines(endpoints)
	run.Injections = unmarshalInjections(injections)
	run.AutoRecord = autoRecord != 0
	run.CancelAsked = cancelAsked != 0
	run.CrawlEnabled = crawlEnabled != 0
	// 舊資料列的 repeat 可能是 0；統一視為 1（不重複），避免前端顯示「0 次」。
	if run.Repeat <= 0 {
		run.Repeat = 1
	}
	run.CreatedAt = parseDBTime(createdAt)
	run.UpdatedAt = parseDBTime(updatedAt)
	run.StartedAt = parseNullableDBTime(startedAt)
	run.CompletedAt = parseNullableDBTime(completedAt)
	return &run, nil
}

// UpdateRedirectVerifyRunTotal 更新批次的目標總數。
//
// 巡站之後才知道真正要驗的筆數（候選數），這時才把 total 改成候選數，
// 進度條才不會停在一半。
func (db *DB) UpdateRedirectVerifyRunTotal(id string, total int) error {
	if strings.TrimSpace(id) == "" {
		return fmt.Errorf("批次 ID 為空")
	}
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET total = ?, updated_at = ? WHERE id = ?`,
		total, now, id,
	)
	if err != nil {
		return fmt.Errorf("更新跳轉驗證批次目標總數失敗: %w", err)
	}
	return nil
}

// UpdateRedirectVerifyRunCrawl 更新巡站階段的進度（候選數、種子數、目前階段）。
func (db *DB) UpdateRedirectVerifyRunCrawl(id string, seedCount int, candidates int, phase string) error {
	if strings.TrimSpace(id) == "" {
		return fmt.Errorf("批次 ID 為空")
	}
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET seed_count = ?, crawl_candidates = ?, phase = ?, updated_at = ? WHERE id = ?`,
		seedCount, candidates, phase, now, id,
	)
	if err != nil {
		return fmt.Errorf("更新跳轉驗證批次巡站進度失敗: %w", err)
	}
	return nil
}

// UpdateRedirectVerifyRunInjections 更新巡站階段找到的注入點統計與清單。
//
// 注入點是「站上別人塞進來的外部 URL」——那是替換成我們受控端點的目標位置，
// 數量要落在批次上，前端才看得到「可自動植入幾個」。
func (db *DB) UpdateRedirectVerifyRunInjections(id string, injectionCount int, thirdParty int, points []redirect.InjectionPoint) error {
	if strings.TrimSpace(id) == "" {
		return fmt.Errorf("批次 ID 為空")
	}
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET injection_count = ?, third_party_injections = ?, injections = ?, updated_at = ? WHERE id = ?`,
		injectionCount, thirdParty, marshalInjections(points), now, id,
	)
	if err != nil {
		return fmt.Errorf("更新跳轉驗證批次注入點統計失敗: %w", err)
	}
	return nil
}

// marshalInjections 把注入點清單序列化；空清單回空字串（資料庫存 JSON 文字）。
func marshalInjections(points []redirect.InjectionPoint) string {
	if len(points) == 0 {
		return ""
	}
	encoded, err := json.Marshal(points)
	if err != nil {
		return ""
	}
	return string(encoded)
}

// unmarshalInjections 還原注入點清單；壞掉的 JSON 不讓整筆批次讀取失敗。
func unmarshalInjections(raw string) []redirect.InjectionPoint {
	value := strings.TrimSpace(raw)
	if value == "" {
		return nil
	}
	var points []redirect.InjectionPoint
	if err := json.Unmarshal([]byte(value), &points); err != nil {
		return nil
	}
	return points
}

// UpdateRedirectVerifyRunProgress 更新批次進度。
func (db *DB) UpdateRedirectVerifyRunProgress(id string, completed int, confirmed int, status string) error {
	if strings.TrimSpace(id) == "" {
		return fmt.Errorf("批次 ID 為空")
	}
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET completed = ?, confirmed = ?, status = ?, updated_at = ? WHERE id = ?`,
		completed, confirmed, status, now, id,
	)
	if err != nil {
		return fmt.Errorf("更新跳轉驗證批次進度失敗: %w", err)
	}
	return nil
}

// StartRedirectVerifyRun 標記批次開始執行。
func (db *DB) StartRedirectVerifyRun(id string) error {
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET status = ?, started_at = ?, updated_at = ? WHERE id = ?`,
		RedirectVerifyStatusRunning, now, now, id,
	)
	if err != nil {
		return fmt.Errorf("標記跳轉驗證批次開始失敗: %w", err)
	}
	return nil
}

// FinishRedirectVerifyRun 標記批次結束。
func (db *DB) FinishRedirectVerifyRun(id string, status string, errorMessage string) error {
	now := time.Now()
	_, err := db.Exec(
		`UPDATE redirect_verify_runs SET status = ?, error = ?, completed_at = ?, updated_at = ? WHERE id = ?`,
		status, errorMessage, now, now, id,
	)
	if err != nil {
		return fmt.Errorf("標記跳轉驗證批次結束失敗: %w", err)
	}
	return nil
}

// RequestRedirectVerifyRunCancel 請求取消批次；回傳 false 表示批次已結束，取消無效。
func (db *DB) RequestRedirectVerifyRunCancel(id string) (bool, error) {
	if strings.TrimSpace(id) == "" {
		return false, fmt.Errorf("批次 ID 為空")
	}
	now := time.Now()
	result, err := db.Exec(
		`UPDATE redirect_verify_runs SET cancel_asked = 1, updated_at = ?
		 WHERE id = ? AND cancel_asked = 0 AND status IN (?, ?)`,
		now, id, RedirectVerifyStatusPending, RedirectVerifyStatusRunning,
	)
	if err != nil {
		return false, fmt.Errorf("請求取消跳轉驗證批次失敗: %w", err)
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return false, fmt.Errorf("請求取消跳轉驗證批次失敗: %w", err)
	}
	return affected > 0, nil
}

// IsRedirectVerifyRunCancelAsked 查詢批次是否已被請求取消。
func (db *DB) IsRedirectVerifyRunCancelAsked(id string) (bool, error) {
	var cancelAsked int
	err := db.QueryRow(`SELECT cancel_asked FROM redirect_verify_runs WHERE id = ?`, id).Scan(&cancelAsked)
	if err != nil {
		if err == sql.ErrNoRows {
			return false, nil
		}
		return false, fmt.Errorf("查詢跳轉驗證批次取消狀態失敗: %w", err)
	}
	return cancelAsked != 0, nil
}

// AppendRedirectVerifyResult 寫入單筆結果。
func (db *DB) AppendRedirectVerifyResult(result *RedirectVerifyResult) error {
	if result == nil {
		return fmt.Errorf("結果內容不能為空")
	}
	if result.ID == "" {
		result.ID = uuid.New().String()
	}
	if result.CreatedAt.IsZero() {
		result.CreatedAt = time.Now()
	}
	_, err := db.Exec(
		`INSERT INTO redirect_verify_results (
			id, run_id, url, confirmed, param, own_param, params_tried,
			request_url, status, location, error,
			evidence, body_echo, own_param_hit, attempts, stable,
			vulnerability_id, created_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		result.ID, result.RunID, result.URL, boolToInt(result.Confirmed), result.Param,
		result.OwnParam, strings.Join(result.ParamsTried, ","),
		result.RequestURL, result.Status, result.Location, result.Error,
		result.Evidence, boolToInt(result.BodyEcho), boolToInt(result.OwnParamHit),
		result.Attempts, boolToInt(result.Stable),
		nullIfEmpty(result.VulnerabilityID), result.CreatedAt,
	)
	if err != nil {
		return fmt.Errorf("寫入跳轉驗證結果失敗: %w", err)
	}
	return nil
}

// SetRedirectVerifyResultVulnerability 把驗證成功的結果連結到建立的漏洞紀錄。
func (db *DB) SetRedirectVerifyResultVulnerability(resultID string, vulnerabilityID string) error {
	if strings.TrimSpace(resultID) == "" {
		return fmt.Errorf("結果 ID 為空")
	}
	_, err := db.Exec(
		`UPDATE redirect_verify_results SET vulnerability_id = ? WHERE id = ?`,
		nullIfEmpty(vulnerabilityID), resultID,
	)
	if err != nil {
		return fmt.Errorf("連結跳轉驗證結果失敗: %w", err)
	}
	return nil
}

// ListRedirectVerifyResults 取得批次的所有結果（依建立順序）。
func (db *DB) ListRedirectVerifyResults(runID string) ([]RedirectVerifyResult, error) {
	runID = strings.TrimSpace(runID)
	if runID == "" {
		return nil, fmt.Errorf("批次 ID 為空")
	}
	rows, err := db.Query(
		`SELECT id, run_id, url, confirmed, param,
			COALESCE(own_param,''), COALESCE(params_tried,''),
			request_url, status, location, error,
			COALESCE(evidence,''), COALESCE(body_echo,0), COALESCE(own_param_hit,0),
			COALESCE(attempts,0), COALESCE(stable,1),
			COALESCE(vulnerability_id,''), created_at
		 FROM redirect_verify_results WHERE run_id = ? ORDER BY created_at ASC, rowid ASC`,
		runID,
	)
	if err != nil {
		return nil, fmt.Errorf("查詢跳轉驗證結果失敗: %w", err)
	}
	defer rows.Close()

	var out []RedirectVerifyResult
	for rows.Next() {
		var result RedirectVerifyResult
		var confirmed int
		var paramsTried string
		var bodyEcho, ownParamHit, stable int
		var createdAt string
		if err := rows.Scan(
			&result.ID, &result.RunID, &result.URL, &confirmed, &result.Param,
			&result.OwnParam, &paramsTried,
			&result.RequestURL, &result.Status, &result.Location, &result.Error,
			&result.Evidence, &bodyEcho, &ownParamHit,
			&result.Attempts, &stable,
			&result.VulnerabilityID, &createdAt,
		); err != nil {
			return nil, fmt.Errorf("掃描跳轉驗證結果失敗: %w", err)
		}
		result.Confirmed = confirmed != 0
		result.ParamsTried = splitCommaList(paramsTried)
		result.BodyEcho = bodyEcho != 0
		result.OwnParamHit = ownParamHit != 0
		result.Stable = stable != 0
		result.CreatedAt = parseDBTime(createdAt)
		out = append(out, result)
	}
	return out, rows.Err()
}

// splitCommaList 依逗號切開並去掉空白項目。
func splitCommaList(value string) []string {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		if trimmed := strings.TrimSpace(part); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}

// ListRedirectVerifyRuns 列出批次（依建立時間倒序）。
func (db *DB) ListRedirectVerifyRuns(limit int) ([]RedirectVerifyRun, error) {
	return db.ListRedirectVerifyRunsForAccess(limit, "", "")
}

// ListRedirectVerifyRunsForAccess 依 RBAC 範圍列出批次。
//
// 與其他資源一致：解析不出呼叫者時（scope 非全部且 userID 為空）看不到任何資料，
// 避免把別人的批次結果洩漏出去。
func (db *DB) ListRedirectVerifyRunsForAccess(limit int, userID string, scope string) ([]RedirectVerifyRun, error) {
	if limit <= 0 {
		limit = 50
	}
	query := redirectVerifyRunSelect + " WHERE 1=1"
	args := []interface{}{}

	userID = strings.TrimSpace(userID)
	if scope != RBACScopeAll && userID == "" {
		query += " AND 1=0"
	} else if scope != RBACScopeAll {
		query += ` AND (
			owner_user_id = ?
			OR EXISTS (
				SELECT 1 FROM rbac_resource_assignments ra
				WHERE ra.user_id = ? AND ra.resource_type = 'redirect_verify_run' AND ra.resource_id = redirect_verify_runs.id
			)
			OR (
				project_id IS NOT NULL AND project_id <> '' AND (
					EXISTS (SELECT 1 FROM projects p WHERE p.id = redirect_verify_runs.project_id AND p.owner_user_id = ?)
					OR EXISTS (
						SELECT 1 FROM rbac_resource_assignments pra
						WHERE pra.user_id = ? AND pra.resource_type = 'project' AND pra.resource_id = redirect_verify_runs.project_id
					)
				)
			)
		)`
		args = append(args, userID, userID, userID, userID)
	}

	query += " ORDER BY created_at DESC LIMIT ?"
	args = append(args, limit)

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("查詢跳轉驗證批次列表失敗: %w", err)
	}
	defer rows.Close()

	var out []RedirectVerifyRun
	for rows.Next() {
		run, err := scanRedirectVerifyRun(rows)
		if err != nil {
			return nil, fmt.Errorf("掃描跳轉驗證批次失敗: %w", err)
		}
		out = append(out, *run)
	}
	return out, rows.Err()
}

// splitNonEmptyLines 依行切開並去掉空白行。
func splitNonEmptyLines(value string) []string {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	parts := strings.Split(value, "\n")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		if trimmed := strings.TrimSpace(part); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}

// nullTimePtr 把零值時間轉成可寫入資料表的 nil。
func nullTimePtr(value time.Time) interface{} {
	if value.IsZero() {
		return nil
	}
	return value
}

// parseNullableDBTime 解析可為空的时间欄位。
func parseNullableDBTime(value sql.NullString) time.Time {
	if !value.Valid {
		return time.Time{}
	}
	return parseDBTime(value.String)
}
