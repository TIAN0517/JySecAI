package database

import (
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"
)

const createSecurityOpsRunsTable = `
CREATE TABLE IF NOT EXISTS security_ops_runs (
	id TEXT PRIMARY KEY,
	idempotency_key TEXT NOT NULL DEFAULT '',
	project_id TEXT NOT NULL,
	owner_id TEXT NOT NULL,
	engine TEXT NOT NULL,
	profile TEXT NOT NULL,
	operation TEXT NOT NULL,
	objective TEXT NOT NULL,
	targets_json TEXT NOT NULL,
	patterns_json TEXT NOT NULL,
	authorization_json TEXT NOT NULL,
	status TEXT NOT NULL,
	status_reason TEXT NOT NULL DEFAULT '',
	remote_id TEXT NOT NULL DEFAULT '',
	current_phase INTEGER NOT NULL DEFAULT 0,
	vuln_count INTEGER NOT NULL DEFAULT 0,
	created_at TEXT NOT NULL,
	updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_security_ops_idempotency
	ON security_ops_runs(idempotency_key) WHERE idempotency_key != '';
CREATE INDEX IF NOT EXISTS idx_security_ops_owner_project
	ON security_ops_runs(owner_id, project_id, created_at);
`

// SecurityOpsRun 是「Web 安全掃描」頁的一筆任務。遠端掃描器的編號只存在 remote_id。
type SecurityOpsRun struct {
	ID                string
	IdempotencyKey    string
	ProjectID         string
	OwnerID           string
	Engine            string
	Profile           string
	Operation         string
	Objective         string
	TargetsJSON       string
	PatternsJSON      string
	AuthorizationJSON string
	Status            string
	StatusReason      string
	RemoteID          string
	CurrentPhase      int
	VulnCount         int
	CreatedAt         time.Time
	UpdatedAt         time.Time
}

func (db *DB) InsertSecurityOpsRun(run *SecurityOpsRun) error {
	if run == nil || strings.TrimSpace(run.ID) == "" {
		return errors.New("security ops run id is required")
	}
	now := time.Now().UTC()
	if run.CreatedAt.IsZero() {
		run.CreatedAt = now
	}
	run.UpdatedAt = now
	_, err := db.Exec(`
		INSERT INTO security_ops_runs (
			id, idempotency_key, project_id, owner_id, engine, profile, operation, objective,
			targets_json, patterns_json, authorization_json, status, status_reason, remote_id,
			current_phase, vuln_count, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		run.ID, run.IdempotencyKey, run.ProjectID, run.OwnerID, run.Engine, run.Profile, run.Operation, run.Objective,
		run.TargetsJSON, run.PatternsJSON, run.AuthorizationJSON, run.Status, run.StatusReason, run.RemoteID,
		run.CurrentPhase, run.VulnCount, run.CreatedAt.Format(time.RFC3339Nano), run.UpdatedAt.Format(time.RFC3339Nano),
	)
	return err
}

func (db *DB) FindSecurityOpsRunByIdempotency(key, ownerID string) (*SecurityOpsRun, error) {
	key = strings.TrimSpace(key)
	if key == "" {
		return nil, nil
	}
	row := db.QueryRow(`SELECT `+securityOpsRunColumns+` FROM security_ops_runs WHERE idempotency_key = ? AND owner_id = ?`, key, ownerID)
	run, err := scanSecurityOpsRun(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	return run, err
}

func (db *DB) GetSecurityOpsRun(id string) (*SecurityOpsRun, error) {
	row := db.QueryRow(`SELECT `+securityOpsRunColumns+` FROM security_ops_runs WHERE id = ?`, id)
	run, err := scanSecurityOpsRun(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	return run, err
}

func (db *DB) ListSecurityOpsRuns(ownerID, projectID string, allOwners bool, limit int) ([]SecurityOpsRun, error) {
	if limit <= 0 || limit > 200 {
		limit = 50
	}
	query := `SELECT ` + securityOpsRunColumns + ` FROM security_ops_runs WHERE 1=1`
	args := make([]any, 0, 3)
	if !allOwners {
		query += ` AND owner_id = ?`
		args = append(args, ownerID)
	}
	if strings.TrimSpace(projectID) != "" {
		query += ` AND project_id = ?`
		args = append(args, strings.TrimSpace(projectID))
	}
	query += ` ORDER BY created_at DESC LIMIT ?`
	args = append(args, limit)
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []SecurityOpsRun
	for rows.Next() {
		run, err := scanSecurityOpsRun(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, *run)
	}
	return out, rows.Err()
}

func (db *DB) UpdateSecurityOpsRun(run *SecurityOpsRun) error {
	if run == nil || run.ID == "" {
		return errors.New("security ops run id is required")
	}
	run.UpdatedAt = time.Now().UTC()
	res, err := db.Exec(`
		UPDATE security_ops_runs
		SET status = ?, status_reason = ?, remote_id = ?, current_phase = ?, vuln_count = ?, updated_at = ?
		WHERE id = ?`,
		run.Status, run.StatusReason, run.RemoteID, run.CurrentPhase, run.VulnCount, run.UpdatedAt.Format(time.RFC3339Nano), run.ID,
	)
	if err != nil {
		return err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return fmt.Errorf("security ops run %s not found", run.ID)
	}
	return nil
}

const securityOpsRunColumns = `id, idempotency_key, project_id, owner_id, engine, profile, operation, objective,
	targets_json, patterns_json, authorization_json, status, status_reason, remote_id,
	current_phase, vuln_count, created_at, updated_at`

type securityOpsScanner interface {
	Scan(dest ...any) error
}

func scanSecurityOpsRun(scanner securityOpsScanner) (*SecurityOpsRun, error) {
	var run SecurityOpsRun
	var created, updated string
	err := scanner.Scan(
		&run.ID, &run.IdempotencyKey, &run.ProjectID, &run.OwnerID, &run.Engine, &run.Profile, &run.Operation, &run.Objective,
		&run.TargetsJSON, &run.PatternsJSON, &run.AuthorizationJSON, &run.Status, &run.StatusReason, &run.RemoteID,
		&run.CurrentPhase, &run.VulnCount, &created, &updated,
	)
	if err != nil {
		return nil, err
	}
	run.CreatedAt, err = time.Parse(time.RFC3339Nano, created)
	if err != nil {
		return nil, err
	}
	run.UpdatedAt, err = time.Parse(time.RFC3339Nano, updated)
	if err != nil {
		return nil, err
	}
	return &run, nil
}
