package receiver

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"go.uber.org/zap"

	// MySQL driver。註冊為 "mysql" driver。
	_ "github.com/go-sql-driver/mysql"
)

// MySQLConfig 外部 MySQL 接收端設定。
type MySQLConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Database string
	// TablePrefix 表名前綴。同一個 MySQL 上跑多個平台實例時用來隔離。
	TablePrefix string
	// Timeout 單次操作的逾時。逾時必須遠小於平台的請求逾時，
	// 否則網路卡住會把主流程一起拖住。
	Timeout         time.Duration
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
}

// MySQLSink 把收割成果寫進主力機 MySQL。
type MySQLSink struct {
	db     *sql.DB
	cfg    MySQLConfig
	logger *zap.Logger
}

// DSN 組出 go-sql-driver 的連線字串。
//
// parseTime=true 是必要的：接收端要讀 DATETIME(3)，沒有它就會拿到 []byte。
// loc=UTC 讓時間戳與平台其他部分一致（平台內部一律 UTC）。
func (c MySQLConfig) DSN() string {
	port := c.Port
	if port == 0 {
		port = 3306
	}
	timeout := c.Timeout
	if timeout <= 0 {
		timeout = 10 * time.Second
	}
	return fmt.Sprintf(
		"%s:%s@tcp(%s)/%s?charset=utf8mb4&parseTime=true&loc=UTC&timeout=%s&readTimeout=%s&writeTimeout=%s&multiStatements=false",
		c.User, c.Password, net.JoinHostPort(c.Host, strconv.Itoa(port)),
		c.Database,
		url.QueryEscape(timeout.String()),
		url.QueryEscape((timeout * 6).String()),
		url.QueryEscape((timeout * 6).String()),
	)
}

// MaskHost 把字串裡出現的連線主機換成佔位符。
//
// 為什麼要遮：接收端的連線錯誤會被寫進應用程式日誌，而日誌是除錯時最常被
// 貼到聊天、工單、issue 的東西。主機位址在那些地方沒有價值得著（要查設定檔
// 就有），但內網拓撲不該跟著到處跑 —— 日誌外流往往就是從「貼一段 log」開始的。
func (c MySQLConfig) MaskHost(msg string) string {
	host := strings.TrimSpace(c.Host)
	if host == "" || msg == "" {
		return msg
	}
	return strings.ReplaceAll(msg, host, "<mysql-host>")
}

// NewMySQLSink 建立接收端。
//
// 這裡只驗證「連得上」，不建立 schema —— schema 建立是明確的部署步驟，
// 混在連線裡會讓啟動路徑變得不可預期。
func NewMySQLSink(cfg MySQLConfig, logger *zap.Logger) (*MySQLSink, error) {
	if cfg.Host == "" || cfg.User == "" || cfg.Database == "" {
		return nil, fmt.Errorf("外部 MySQL 設定不完整（host/user/database 必填）")
	}
	if logger == nil {
		logger = zap.NewNop()
	}
	if cfg.MaxOpenConns <= 0 {
		cfg.MaxOpenConns = 4
	}
	if cfg.MaxIdleConns <= 0 {
		cfg.MaxIdleConns = 2
	}
	if cfg.ConnMaxLifetime <= 0 {
		cfg.ConnMaxLifetime = 30 * time.Minute
	}

	db, err := sql.Open("mysql", cfg.DSN())
	if err != nil {
		return nil, fmt.Errorf("開啟外部 MySQL 連線失敗: %w", err)
	}
	db.SetMaxOpenConns(cfg.MaxOpenConns)
	db.SetMaxIdleConns(cfg.MaxIdleConns)
	db.SetConnMaxLifetime(cfg.ConnMaxLifetime)

	pingCtx, cancel := context.WithTimeout(context.Background(), cfg.Timeout)
	defer cancel()
	if err := db.PingContext(pingCtx); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("外部 MySQL 連線測試失敗: %w", err)
	}
	return &MySQLSink{db: db, cfg: cfg, logger: logger}, nil
}

func (s *MySQLSink) table(name string) string {
	if s == nil {
		return name
	}
	return s.cfg.TablePrefix + name
}

// Close 關閉連線。
func (s *MySQLSink) Close() error {
	if s == nil || s.db == nil {
		return nil
	}
	return s.db.Close()
}

// EnsureSchema 建立接收端需要的表。
//
// 這是明確的部署動作，不在啟動路徑上自動呼叫 —— 自動建表會讓
// 「這個帳號到底有什麼權限」變得無法從程式碼看出來。
func (s *MySQLSink) EnsureSchema(ctx context.Context) error {
	if s == nil || s.db == nil {
		return ErrDisabled
	}
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS ` + s.table("receiver_ledger") + ` (
			id BIGINT AUTO_INCREMENT PRIMARY KEY,
			source_kind VARCHAR(32) NOT NULL,
			source_id VARCHAR(128) NOT NULL,
			dataset_id CHAR(36) NOT NULL,
			checksum CHAR(64) NOT NULL,
			status VARCHAR(16) NOT NULL,
			attempts INT NOT NULL DEFAULT 0,
			error_text TEXT,
			delivered_at DATETIME(3) NULL,
			created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
			updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
			UNIQUE KEY uk_source (source_kind, source_id),
			KEY idx_checksum (checksum),
			KEY idx_status (status)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

		`CREATE TABLE IF NOT EXISTS ` + s.table("harvested_datasets") + ` (
			id CHAR(36) PRIMARY KEY,
			source_kind VARCHAR(32) NOT NULL,
			source_id VARCHAR(128) NOT NULL,
			project_id VARCHAR(64) NOT NULL DEFAULT '',
			conversation_id VARCHAR(64) NOT NULL DEFAULT '',
			vulnerability_id VARCHAR(64) NOT NULL DEFAULT '',
			fact_key VARCHAR(255) NOT NULL DEFAULT '',
			category VARCHAR(64) NOT NULL DEFAULT '',
			title TEXT,
			target VARCHAR(1024) NOT NULL DEFAULT '',
			severity VARCHAR(16) NOT NULL DEFAULT '',
			status VARCHAR(32) NOT NULL DEFAULT '',
			confidence INT NOT NULL DEFAULT 0,
			data_type VARCHAR(32) NOT NULL DEFAULT 'unknown',
			row_count INT NOT NULL DEFAULT 0,
			byte_size BIGINT NOT NULL DEFAULT 0,
			sensitivity VARCHAR(16) NOT NULL DEFAULT 'none',
			checksum CHAR(64) NOT NULL,
			evidence LONGTEXT,
			body LONGTEXT,
			meta LONGTEXT,
			occurred_at DATETIME(3) NULL,
			delivered_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
			KEY idx_source (source_kind, source_id),
			KEY idx_project (project_id),
			KEY idx_vuln (vulnerability_id),
			KEY idx_sensitivity (sensitivity),
			KEY idx_type (data_type)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

		`CREATE TABLE IF NOT EXISTS ` + s.table("receiver_runs") + ` (
			id CHAR(36) PRIMARY KEY,
			started_at DATETIME(3) NOT NULL,
			finished_at DATETIME(3) NULL,
			delivered INT NOT NULL DEFAULT 0,
			failed INT NOT NULL DEFAULT 0,
			skipped INT NOT NULL DEFAULT 0,
			error_text TEXT,
			created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

		// 結構化漏洞表：完整漏洞記錄（含受控分類），供倉儲側直接查詢與統計。
		// harvested_datasets 是通用成果容器（每次收割一筆），這張表則是
		// 「平台上的漏洞」本身的投影，欄位固定、可建索引、可做維度分析。
		//
		// 注意：target 與 evidence 進這張表前已經過 vulnmask 遮蔽 ——
		// 真實目標位址不該永久留在外部資料庫裡。
		`CREATE TABLE IF NOT EXISTS ` + s.table("vulnerabilities") + ` (
			id CHAR(36) PRIMARY KEY,
			source_id VARCHAR(128) NOT NULL,
			project_id VARCHAR(64) NOT NULL DEFAULT '',
			conversation_id VARCHAR(64) NOT NULL DEFAULT '',
			title TEXT NOT NULL,
			type_label VARCHAR(64) NOT NULL DEFAULT '',
			type_code VARCHAR(64) NOT NULL DEFAULT '',
			type_raw VARCHAR(512) NOT NULL DEFAULT '',
			target VARCHAR(1024) NOT NULL DEFAULT '',
			severity VARCHAR(16) NOT NULL DEFAULT '',
			status VARCHAR(32) NOT NULL DEFAULT '',
			confidence INT NOT NULL DEFAULT 0,
			description MEDIUMTEXT,
			preconditions MEDIUMTEXT,
			reproduction_steps MEDIUMTEXT,
			evidence MEDIUMTEXT,
			impact MEDIUMTEXT,
			recommendation MEDIUMTEXT,
			retest_notes MEDIUMTEXT,
			conversation_tag VARCHAR(255) NOT NULL DEFAULT '',
			task_tag VARCHAR(255) NOT NULL DEFAULT '',
			task_id VARCHAR(64) NOT NULL DEFAULT '',
			task_queue_id VARCHAR(64) NOT NULL DEFAULT '',
			checksum CHAR(64) NOT NULL,
			imported_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
			updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
			UNIQUE KEY uk_source (source_id),
			KEY idx_type (type_code),
			KEY idx_severity (severity),
			KEY idx_status (status),
			KEY idx_project (project_id),
			KEY idx_conv (conversation_id)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
	}
	for _, stmt := range stmts {
		if _, err := s.db.ExecContext(ctx, stmt); err != nil {
			return fmt.Errorf("建立接收端 schema 失敗: %w", err)
		}
	}
	return nil
}

// Deliver 送出一筆收割成果。
//
// 冪等保證：以 (source_kind, source_id) 為帳本主鍵。
//   - 帳本沒有 → 新資料集 + 新帳本
//   - 帳本有、checksum 相同、狀態 delivered → 跳過（不重複落地）
//   - 帳本有、checksum 不同 → 覆寫資料集（證據更新了），帳本更新
//
// 整段包在交易裡：帳本與資料集必須一起成功或一起不成功，
// 否則會留下「帳本說送過、資料其實沒有」的假紀錄 —— 那正是這套東西最不能犯的錯。
func (s *MySQLSink) Deliver(ctx context.Context, p Payload) (DeliveryResult, error) {
	if s == nil || s.db == nil {
		return DeliveryResult{}, ErrDisabled
	}
	if strings.TrimSpace(p.SourceKind) == "" || strings.TrimSpace(p.SourceID) == "" {
		return DeliveryResult{}, fmt.Errorf("接收端缺少 source_kind / source_id，無法溯源")
	}

	checksum := p.Checksum()
	sensitivity := p.Sensitivity()
	// 資料形態：呼叫端指定就用指定的，沒指定才推測。
	// 這裡刻意用 DetectDataType() 而不是直接讀 p.DataType —— 直接讀的話
	// DetectDataType 永遠不會被呼叫，倉儲側就會拿到一整批 unknown 而沒有分類。
	dataType := p.DetectDataType()
	if dataType == "" {
		dataType = DataTypeUnknown
	}
	occurredAt := p.OccurredAt
	if occurredAt.IsZero() {
		occurredAt = time.Now().UTC()
	}

	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return DeliveryResult{}, fmt.Errorf("開啟接收端交易失敗: %w", err)
	}
	defer func() { _ = tx.Rollback() }()

	var prevChecksum, prevStatus, prevDatasetID string
	row := tx.QueryRowContext(ctx,
		"SELECT checksum, status, dataset_id FROM "+s.table("receiver_ledger")+" WHERE source_kind=? AND source_id=?",
		p.SourceKind, p.SourceID)
	switch err := row.Scan(&prevChecksum, &prevStatus, &prevDatasetID); {
	case errors.Is(err, sql.ErrNoRows):
		// 新成果，往下走。
	case err != nil:
		return DeliveryResult{}, fmt.Errorf("讀取接收端帳本失敗: %w", err)
	case prevChecksum == checksum && prevStatus == "delivered":
		return DeliveryResult{
			Skipped:   true,
			DatasetID: prevDatasetID,
			Reason:    "內容未變更，已送過",
		}, nil
	}

	datasetID := prevDatasetID
	if datasetID == "" {
		datasetID = uuid.New().String()
	}

	// 資料集本身用 UPSERT：同一個來源識別只有一筆，內容更新就覆寫。
	_, err = tx.ExecContext(ctx,
		`INSERT INTO `+s.table("harvested_datasets")+`
			(id, source_kind, source_id, project_id, conversation_id, vulnerability_id, fact_key,
			 category, title, target, severity, status, confidence, data_type, row_count,
			 byte_size, sensitivity, checksum, evidence, body, meta, occurred_at, delivered_at)
		 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP(3))
		 ON DUPLICATE KEY UPDATE
			 project_id=VALUES(project_id), conversation_id=VALUES(conversation_id),
			 vulnerability_id=VALUES(vulnerability_id), fact_key=VALUES(fact_key),
			 category=VALUES(category), title=VALUES(title), target=VALUES(target),
			 severity=VALUES(severity), status=VALUES(status), confidence=VALUES(confidence),
				data_type=VALUES(data_type), row_count=VALUES(row_count), byte_size=VALUES(byte_size),
				sensitivity=VALUES(sensitivity), checksum=VALUES(checksum),
			 evidence=VALUES(evidence), body=VALUES(body), meta=VALUES(meta),
			 occurred_at=VALUES(occurred_at),
			 delivered_at=CURRENT_TIMESTAMP(3)`,
		sanitizeArgs([]any{
			datasetID, p.SourceKind, p.SourceID, p.ProjectID, p.ConversationID, p.VulnerabilityID,
			p.FactKey, p.Category, p.Title, p.Target, p.Severity, p.Status, p.Confidence, dataType,
			p.RowCount(), p.ByteSize(), sensitivity, checksum, p.Evidence, p.Body, p.Meta, occurredAt,
		})...,
	)
	if err != nil {
		return DeliveryResult{}, fmt.Errorf("寫入收割資料集失敗: %w", err)
	}

	// 漏洞成果另外寫進結構化漏洞表。
	//
	// harvested_datasets 是通用容器（每次收割一筆），欄位取決於收割到什麼；
	// 但「平台上有哪些漏洞、各自是什麼嚴重度與分類」是固定形狀的查詢，
	// 需要自己的表才能建索引、做維度分析。
	if p.SourceKind == SourceKindVulnerability {
		if err := upsertVulnerabilityRow(ctx, tx, s, p, checksum, datasetID); err != nil {
			return DeliveryResult{}, err
		}
	}

	// 帳本 UPSERT。
	_, err = tx.ExecContext(ctx,
		`INSERT INTO `+s.table("receiver_ledger")+`
			(source_kind, source_id, dataset_id, checksum, status, attempts, delivered_at)
		 VALUES (?,?,?,?,'delivered',1,CURRENT_TIMESTAMP(3))
		 ON DUPLICATE KEY UPDATE
			dataset_id=VALUES(dataset_id), checksum=VALUES(checksum), status='delivered',
			attempts=attempts+1, error_text=NULL, delivered_at=CURRENT_TIMESTAMP(3)`,
		sanitizeArgs([]any{p.SourceKind, p.SourceID, datasetID, checksum})...,
	)
	if err != nil {
		return DeliveryResult{}, fmt.Errorf("寫入接收端帳本失敗: %w", err)
	}

	if err := tx.Commit(); err != nil {
		return DeliveryResult{}, fmt.Errorf("提交接收端交易失敗: %w", err)
	}
	return DeliveryResult{Delivered: true, DatasetID: datasetID}, nil
}

// LedgerSnapshot 一次把整份帳本讀回來（依 source_kind 過濾）。
//
// 這是批次匯入的關鍵：Deliver 每筆都要查一次帳本判斷內容有沒有變，
// 在跨主機的資料庫上逐筆查詢就是瓶頸（4359 筆 = 4359 次往返）。
// 先一次讀回來、當場比對 checksum，匯入時間從數十分鐘降到幾分鐘。
//
// 回傳的 map 以 SourceID 為鍵。
func (s *MySQLSink) LedgerSnapshot(ctx context.Context, sourceKind string) (map[string]LedgerEntry, error) {
	if s == nil || s.db == nil {
		return nil, ErrDisabled
	}
	query := "SELECT source_id, checksum, status, dataset_id FROM " + s.table("receiver_ledger")
	args := []any{}
	if sourceKind != "" {
		query += " WHERE source_kind=?"
		args = append(args, sourceKind)
	}
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("讀取接收端帳本快照失敗: %w", err)
	}
	defer rows.Close()

	entries := make(map[string]LedgerEntry)
	for rows.Next() {
		var entry LedgerEntry
		if err := rows.Scan(&entry.SourceID, &entry.Checksum, &entry.Status, &entry.DatasetID); err != nil {
			return nil, fmt.Errorf("讀取接收端帳本快照失敗: %w", err)
		}
		entry.SourceKind = sourceKind
		entries[entry.SourceID] = entry
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("讀取接收端帳本快照失敗: %w", err)
	}
	return entries, nil
}

// sanitizeArgs 把參數裡的非法 UTF-8 位元組換掉。
//
// 平台資料庫裡有些欄位存了截斷的多位元組字元（證據片段只寫了「\xE6\x8E」
// 這種三個位元組的前兩個）。MySQL 的 utf8mb4 會以 Error 1366
// (Incorrect string value) 整筆拒收 —— 單一筆壞資料會擋住整批匯入。
//
// 在寫入邊界統一處理，而不是靠呼叫端記得處理：這裡是資料離開平台的唯一路口。
func sanitizeArgs(args []any) []any {
	for i, arg := range args {
		if value, ok := arg.(string); ok {
			args[i] = strings.ToValidUTF8(value, "\uFFFD")
		}
	}
	return args
}

// buildVulnerabilityUpsert 產生漏洞表的 UPSERT 語句與參數。
//
// 欄位清單、占位符與參數必須同源產生：早期版本把三個分別手寫，
// 新增欄位時少寫一個 ? 卻不會編譯錯誤，只會在真正寫入時炸
// "Column count doesn't match value count" —— 而這條路徑平常根本不會被執行到。
func buildVulnerabilityUpsert(table string, p Payload, meta map[string]any, checksum, datasetID string) (string, []any) {
	get := func(key string) string {
		value, ok := meta[key]
		if !ok || value == nil {
			return ""
		}
		switch typed := value.(type) {
		case string:
			return typed
		case float64:
			return strconv.FormatFloat(typed, 'f', -1, 64)
		case bool:
			return strconv.FormatBool(typed)
		default:
			return ""
		}
	}

	// value 為 nil 表示該欄位用 CURRENT_TIMESTAMP(3)，不帶參數。
	columns := []struct {
		name  string
		value any
	}{
		{"id", datasetID},
		{"source_id", p.SourceID},
		{"project_id", p.ProjectID},
		{"conversation_id", p.ConversationID},
		{"title", p.Title},
		{"type_label", p.Category},
		{"type_code", p.TypeCode},
		{"type_raw", get("vulnerability_type_raw")},
		{"target", p.Target},
		{"severity", p.Severity},
		{"status", p.Status},
		{"confidence", p.Confidence},
		{"description", p.Body},
		{"preconditions", get("preconditions")},
		{"reproduction_steps", get("reproduction_steps")},
		{"evidence", p.Evidence},
		{"impact", get("impact")},
		{"recommendation", get("recommendation")},
		{"retest_notes", get("retest_notes")},
		{"conversation_tag", get("conversation_tag")},
		{"task_tag", get("task_tag")},
		{"task_id", get("task_id")},
		{"task_queue_id", get("task_queue_id")},
		{"checksum", checksum},
		{"imported_at", nil},
		{"updated_at", nil},
	}

	names := make([]string, 0, len(columns))
	marks := make([]string, 0, len(columns))
	args := make([]any, 0, len(columns))
	for _, column := range columns {
		names = append(names, column.name)
		if column.value == nil {
			marks = append(marks, "CURRENT_TIMESTAMP(3)")
			continue
		}
		marks = append(marks, "?")
		args = append(args, column.value)
	}

	statement := `INSERT INTO ` + table + ` (` + strings.Join(names, ", ") + `) VALUES (` + strings.Join(marks, ", ") + `)
		ON DUPLICATE KEY UPDATE
			project_id=VALUES(project_id), conversation_id=VALUES(conversation_id),
			title=VALUES(title), type_label=VALUES(type_label), type_code=VALUES(type_code),
			type_raw=VALUES(type_raw), target=VALUES(target), severity=VALUES(severity),
			status=VALUES(status), confidence=VALUES(confidence),
			description=VALUES(description), preconditions=VALUES(preconditions),
			reproduction_steps=VALUES(reproduction_steps), evidence=VALUES(evidence),
			impact=VALUES(impact), recommendation=VALUES(recommendation),
			retest_notes=VALUES(retest_notes), conversation_tag=VALUES(conversation_tag),
			task_tag=VALUES(task_tag), task_id=VALUES(task_id), task_queue_id=VALUES(task_queue_id),
			checksum=VALUES(checksum), updated_at=CURRENT_TIMESTAMP(3)`
	return statement, args
}

// upsertVulnerabilityRow 把漏洞成果寫進結構化漏洞表。
//
// 多型欄位（描述、影響、修建議、複現步驟…）由橋接層序列化在 Meta 裡，
// 這裡解析出來各自成欄 —— 倉儲側要能直接 GROUP BY severity / type_code，
// 把這些欄位塞回一個 JSON 欄位就沒辦法用了。
func upsertVulnerabilityRow(ctx context.Context, tx *sql.Tx, s *MySQLSink, p Payload, checksum, datasetID string) error {
	meta := map[string]any{}
	if strings.TrimSpace(p.Meta) != "" {
		_ = json.Unmarshal([]byte(p.Meta), &meta)
	}
	statement, args := buildVulnerabilityUpsert(s.table("vulnerabilities"), p, meta, checksum, datasetID)
	if _, err := tx.ExecContext(ctx, statement, sanitizeArgs(args)...); err != nil {
		return fmt.Errorf("寫入結構化漏洞失敗: %w", err)
	}
	return nil
}

// RecordFailure 把失敗寫進帳本。
//
// 失敗也要留痕：沒有失敗紀錄的接收端，看起來就像「從來沒有東西要送」。
func (s *MySQLSink) RecordFailure(ctx context.Context, p Payload, cause error) {
	if s == nil || s.db == nil {
		return
	}
	msg := ""
	if cause != nil {
		msg = cause.Error()
	}
	if len(msg) > 2000 {
		msg = msg[:2000]
	}
	_, err := s.db.ExecContext(ctx,
		`INSERT INTO `+s.table("receiver_ledger")+`
			(source_kind, source_id, dataset_id, checksum, status, attempts, error_text)
		 VALUES (?,?,'',?,'failed',1,?)
		 ON DUPLICATE KEY UPDATE
			status='failed', attempts=attempts+1, error_text=VALUES(error_text)`,
		p.SourceKind, p.SourceID, p.Checksum(), msg,
	)
	if err != nil && s.logger != nil {
		s.logger.Warn("記錄接收端失敗狀態時出錯", zap.Error(errors.New(s.cfg.MaskHost(err.Error()))))
	}
}

// Ping 檢查連線是否正常。
func (s *MySQLSink) Ping(ctx context.Context) error {
	if s == nil || s.db == nil {
		return ErrDisabled
	}
	return s.db.PingContext(ctx)
}
