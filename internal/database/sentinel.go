package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"jysecai/internal/sentinel"
)

type SentinelScanRecord struct {
	ID          string                 `json:"id"`
	Target      string                 `json:"target"`
	TargetKind  string                 `json:"target_kind"`
	Status      string                 `json:"status"`
	Error       string                 `json:"error,omitempty"`
	DurationMs  int64                  `json:"duration_ms"`
	SummaryJSON string                 `json:"summary_json"`
	Snapshot    *sentinel.ScanSnapshot `json:"snapshot,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	FinishedAt  *time.Time             `json:"finished_at,omitempty"`
}

func (db *DB) initSentinelTable() error {
	ddl := `
	CREATE TABLE IF NOT EXISTS sentinel_scans (
		id TEXT PRIMARY KEY,
		target TEXT NOT NULL,
		target_kind TEXT NOT NULL,
		status TEXT NOT NULL,
		error TEXT,
		duration_ms INTEGER DEFAULT 0,
		summary_json TEXT NOT NULL,
		snapshot_json TEXT NOT NULL,
		created_at DATETIME NOT NULL,
		finished_at DATETIME
	);
	CREATE INDEX IF NOT EXISTS idx_sentinel_scans_created_at ON sentinel_scans(created_at DESC);
	`
	_, err := db.Exec(ddl)
	return err
}

func (db *DB) SaveSentinelScan(s *sentinel.ScanSnapshot) error {
	summaryBytes, _ := json.Marshal(s.Summary)
	snapshotBytes, err := json.Marshal(s)
	if err != nil {
		return fmt.Errorf("序列化快照失敗: %w", err)
	}

	var finishedAt sql.NullTime
	if s.FinishedAt != "" {
		if t, err := time.Parse(time.RFC3339, s.FinishedAt); err == nil {
			finishedAt = sql.NullTime{Time: t, Valid: true}
		}
	}

	query := `
	INSERT INTO sentinel_scans (id, target, target_kind, status, error, duration_ms, summary_json, snapshot_json, created_at, finished_at)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	ON CONFLICT(id) DO UPDATE SET
		status = excluded.status,
		error = excluded.error,
		duration_ms = excluded.duration_ms,
		summary_json = excluded.summary_json,
		snapshot_json = excluded.snapshot_json,
		finished_at = excluded.finished_at;
	`
	_, err = db.Exec(query, s.ID, s.Target, s.TargetKind, s.Status, s.Error, s.DurationMs, string(summaryBytes), string(snapshotBytes), s.CreatedAt, finishedAt)
	return err
}

func (db *DB) GetLatestSentinelScan() (*sentinel.ScanSnapshot, error) {
	row := db.QueryRow(`SELECT snapshot_json FROM sentinel_scans ORDER BY created_at DESC LIMIT 1`)
	var snapshotJSON string
	if err := row.Scan(&snapshotJSON); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	var s sentinel.ScanSnapshot
	if err := json.Unmarshal([]byte(snapshotJSON), &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func (db *DB) GetSentinelScanByID(id string) (*sentinel.ScanSnapshot, error) {
	row := db.QueryRow(`SELECT snapshot_json FROM sentinel_scans WHERE id = ?`, id)
	var snapshotJSON string
	if err := row.Scan(&snapshotJSON); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	var s sentinel.ScanSnapshot
	if err := json.Unmarshal([]byte(snapshotJSON), &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func (db *DB) ListSentinelScans(limit int) ([]*SentinelScanRecord, error) {
	if limit <= 0 {
		limit = 20
	}
	rows, err := db.Query(`SELECT id, target, target_kind, status, error, duration_ms, summary_json, created_at, finished_at FROM sentinel_scans ORDER BY created_at DESC LIMIT ?`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var records []*SentinelScanRecord
	for rows.Next() {
		var r SentinelScanRecord
		var finishedAt sql.NullTime
		if err := rows.Scan(&r.ID, &r.Target, &r.TargetKind, &r.Status, &r.Error, &r.DurationMs, &r.SummaryJSON, &r.CreatedAt, &finishedAt); err != nil {
			return nil, err
		}
		if finishedAt.Valid {
			r.FinishedAt = &finishedAt.Time
		}
		records = append(records, &r)
	}
	return records, nil
}
