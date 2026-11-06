package database

import (
	"encoding/json"

	"jysecai/internal/mcp"
	"jysecai/internal/toolguard"
)

// legacyToolGuardPrefix 是舊版攔截回執的前綴。定義在 toolguard 套件，
// 與實際產生回執的 mcp 層共用同一份來源，避免兩邊各寫一份字面值而漂移。
const legacyToolGuardPrefix = toolguard.BlockedPrefix

// Only the exact envelope emitted by the old local guard is recognized here.
// New executions use the structured marker and never infer policy from text.
func isLegacyToolGuardRefusal(text string) bool {
	_, _, _, ok := toolguard.ParseRefusal(text)
	return ok
}

// migrateLegacyToolGuardBlocks is idempotent because only failed records qualify.
// Keeping status and accumulated failure counts in one transaction makes monitor
// filters, badges and statistics agree immediately after upgrading.
func (db *DB) migrateLegacyToolGuardBlocks() error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	rows, err := tx.Query(`SELECT id, tool_name, error, COALESCE(result, '') FROM tool_executions WHERE status = 'failed' AND error LIKE ?`, legacyToolGuardPrefix+"%")
	if err != nil {
		return err
	}
	type record struct{ id, tool, reason, result string }
	var records []record
	for rows.Next() {
		var r record
		if err := rows.Scan(&r.id, &r.tool, &r.reason, &r.result); err != nil {
			rows.Close()
			return err
		}
		if isLegacyToolGuardRefusal(r.reason) {
			records = append(records, r)
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, r := range records {
		var result mcp.ToolResult
		_ = json.Unmarshal([]byte(r.result), &result)
		if len(result.Content) == 0 {
			result.Content = []mcp.Content{{Type: "text", Text: r.reason}}
		}
		result.Blocked, result.IsError = true, true
		encoded, err := json.Marshal(result)
		if err != nil {
			return err
		}
		if _, err := tx.Exec(`UPDATE tool_executions SET status = 'blocked', result = ? WHERE id = ?`, string(encoded), r.id); err != nil {
			return err
		}
		if _, err := tx.Exec(`UPDATE tool_stats SET failed_calls = MAX(0, failed_calls - 1) WHERE tool_name = ?`, r.tool); err != nil {
			return err
		}
	}
	return tx.Commit()
}
