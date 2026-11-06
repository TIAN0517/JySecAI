package receiver

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"go.uber.org/zap"
)

// SQLiteOutbox 是接收端的本地持久化寄件箱。
//
// 存在的理由只有一句：收割成果是整個平台最不能弄丟的東西 —— 它可能是某個
// 目標僅存的一份證據。原本的設計只有一條記憶體佇列，外部 MySQL 掛久了佇列
// 滿了只能丟棄，而且行程一重啟就沒了。寄件箱把成果先寫進平台自己的 SQLite，
// 等外部 MySQL 通了再送出去；送不出去就一直留著，不會消失。
//
// 關鍵設計：主鍵是 (source_kind, source_id)，不是 checksum。
//
//   - 同一個來源識別只有一筆待送資料，內容更新了就是覆寫。
//   - 這樣就不會出現「舊內容排在新內容後面送到、把新證據蓋掉」的問題 ——
//     那是最難察覺的一種資料退化，而且只有真的送出去才看得出來。
type SQLiteOutbox struct {
	db     *sql.DB
	logger *zap.Logger
}

// OutboxItem 寄件箱裡的一筆待送成果。
type OutboxItem struct {
	Payload  Payload
	Attempts int
}

// outboxStatements 寄件箱的建表語句。
//
// DDL 放在這裡而不是平台的遷移清單：這張表屬於接收端而不是平台的業務資料，
// 而且接收端要能在沒有平台的情況下單獨測試（CREATE TABLE IF NOT EXISTS 是
// idempotent 的，兩邊都放也不會打架）。
var outboxStatements = []string{
	`CREATE TABLE IF NOT EXISTS receiver_outbox (
		checksum TEXT NOT NULL,
		source_kind TEXT NOT NULL,
		source_id TEXT NOT NULL,
		payload_json TEXT NOT NULL,
		attempts INTEGER NOT NULL DEFAULT 0,
		last_error TEXT,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		PRIMARY KEY (source_kind, source_id)
	)`,
	`CREATE INDEX IF NOT EXISTS idx_receiver_outbox_created ON receiver_outbox(created_at)`,
}

// NewSQLiteOutbox 建立寄件箱並確保 schema 存在。
func NewSQLiteOutbox(db *sql.DB, logger *zap.Logger) (*SQLiteOutbox, error) {
	if db == nil {
		return nil, fmt.Errorf("寄件箱需要資料庫連線")
	}
	if logger == nil {
		logger = zap.NewNop()
	}
	outbox := &SQLiteOutbox{db: db, logger: logger}
	if err := outbox.EnsureSchema(context.Background()); err != nil {
		return nil, err
	}
	return outbox, nil
}

// EnsureSchema 建立寄件箱需要的表。
func (o *SQLiteOutbox) EnsureSchema(ctx context.Context) error {
	if o == nil || o.db == nil {
		return ErrDisabled
	}
	for _, stmt := range outboxStatements {
		if _, err := o.db.ExecContext(ctx, stmt); err != nil {
			return fmt.Errorf("建立接收端寄件箱失敗: %w", err)
		}
	}
	return nil
}

// Enqueue 把成果寫進寄件箱。
//
// 同一個來源識別重複寫入是「覆寫」而不是「新增」：內容更新了就用新的，
// 內容沒變就是原筆更新時間 —— 冪等靠這裡，不靠呼叫端小心。
func (o *SQLiteOutbox) Enqueue(ctx context.Context, p Payload) error {
	if o == nil || o.db == nil {
		return ErrDisabled
	}
	if strings.TrimSpace(p.SourceKind) == "" || strings.TrimSpace(p.SourceID) == "" {
		return fmt.Errorf("寄件箱缺少 source_kind / source_id，無法溯源")
	}
	blob, err := json.Marshal(p)
	if err != nil {
		return fmt.Errorf("序列化收割成果失敗: %w", err)
	}
	now := time.Now().UTC()
	_, err = o.db.ExecContext(ctx,
		`INSERT INTO receiver_outbox
			(checksum, source_kind, source_id, payload_json, attempts, last_error, created_at, updated_at)
		 VALUES (?,?,?,?,0,NULL,?,?)
		 ON CONFLICT(source_kind, source_id) DO UPDATE SET
			checksum=excluded.checksum,
			payload_json=excluded.payload_json,
			attempts=0,
			last_error=NULL,
			updated_at=excluded.updated_at`,
		p.Checksum(), p.SourceKind, p.SourceID, string(blob), now, now)
	if err != nil {
		return fmt.Errorf("寫入接收端寄件箱失敗: %w", err)
	}
	return nil
}

// Claim 取出一批待送成果（依建立時間排序，先進先出）。
func (o *SQLiteOutbox) Claim(ctx context.Context, limit int) ([]OutboxItem, error) {
	if o == nil || o.db == nil {
		return nil, ErrDisabled
	}
	if limit <= 0 {
		limit = 50
	}
	rows, err := o.db.QueryContext(ctx,
		`SELECT source_kind, source_id, payload_json, attempts
		 FROM receiver_outbox ORDER BY created_at ASC LIMIT ?`, limit)
	if err != nil {
		return nil, fmt.Errorf("讀取接收端寄件箱失敗: %w", err)
	}
	defer rows.Close()

	var items []OutboxItem
	for rows.Next() {
		var kind, id, blob string
		var attempts int
		if err := rows.Scan(&kind, &id, &blob, &attempts); err != nil {
			return nil, fmt.Errorf("掃描接收端寄件箱失敗: %w", err)
		}
		var p Payload
		if err := json.Unmarshal([]byte(blob), &p); err != nil {
			// 壞掉的 payload 不能卡住整個寄件箱 —— 否則一筆壞資料會讓
			// 後面所有成果都送不出去。直接刪掉並留下錯誤紀錄。
			o.logger.Error("寄件箱中有無法解析的成果，已移除",
				zap.String("source_kind", kind), zap.String("source_id", id), zap.Error(err))
			_ = o.Ack(ctx, kind, id)
			continue
		}
		items = append(items, OutboxItem{Payload: p, Attempts: attempts})
	}
	return items, rows.Err()
}

// Ack 送出成功：把成果從寄件箱移除。
func (o *SQLiteOutbox) Ack(ctx context.Context, sourceKind, sourceID string) error {
	if o == nil || o.db == nil {
		return ErrDisabled
	}
	if _, err := o.db.ExecContext(ctx,
		`DELETE FROM receiver_outbox WHERE source_kind=? AND source_id=?`,
		sourceKind, sourceID); err != nil {
		return fmt.Errorf("清除接收端寄件箱紀錄失敗: %w", err)
	}
	return nil
}

// Nack 送出失敗：留在寄件箱等待重試，並記錄失敗原因。
//
// 失敗也要留痕：沒有失敗紀錄的接收端，看起來就像「從來沒有東西要送」。
func (o *SQLiteOutbox) Nack(ctx context.Context, sourceKind, sourceID string, cause error) error {
	if o == nil || o.db == nil {
		return ErrDisabled
	}
	msg := ""
	if cause != nil {
		msg = cause.Error()
	}
	if len(msg) > 2000 {
		msg = msg[:2000]
	}
	if _, err := o.db.ExecContext(ctx,
		`UPDATE receiver_outbox SET attempts=attempts+1, last_error=?, updated_at=?
		 WHERE source_kind=? AND source_id=?`,
		msg, time.Now().UTC(), sourceKind, sourceID); err != nil {
		return fmt.Errorf("更新接收端寄件箱失敗狀態時出錯: %w", err)
	}
	return nil
}

// Pending 寄件箱裡還有多少筆待送成果。
func (o *SQLiteOutbox) Pending(ctx context.Context) (int, error) {
	if o == nil || o.db == nil {
		return 0, ErrDisabled
	}
	var n int
	if err := o.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM receiver_outbox`).Scan(&n); err != nil {
		return 0, fmt.Errorf("統計接收端寄件箱失敗: %w", err)
	}
	return n, nil
}
