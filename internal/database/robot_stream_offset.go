package database

import (
	"database/sql"
	"fmt"
	"strings"
	"time"
)

// GetRobotStreamOffset 读取机器人长轮询游标（下一条待处理消息的 update_id）。
// 返回 0 表示该平台尚未持久化过游标，调用方需自行决定是否跳过历史积压。
func (db *DB) GetRobotStreamOffset(platform string) (int64, error) {
	platform = strings.TrimSpace(platform)
	if platform == "" {
		return 0, nil
	}
	var offset int64
	err := db.QueryRow(
		"SELECT update_offset FROM robot_stream_offsets WHERE platform = ?",
		platform,
	).Scan(&offset)
	if err != nil {
		if err == sql.ErrNoRows {
			return 0, nil
		}
		return 0, fmt.Errorf("查询机器人轮询游标失败: %w", err)
	}
	if offset < 0 {
		return 0, nil
	}
	return offset, nil
}

// SaveRobotStreamOffset 持久化机器人长轮询游标。
// 只允许前进不回退：旧实例或并发写入的更小游标不会覆盖更大的值，
// 避免游标倒退导致 Telegram 重放历史消息。
func (db *DB) SaveRobotStreamOffset(platform string, offset int64) error {
	platform = strings.TrimSpace(platform)
	if platform == "" || offset <= 0 {
		return nil
	}
	_, err := db.Exec(`
		INSERT INTO robot_stream_offsets (platform, update_offset, updated_at)
		VALUES (?, ?, ?)
		ON CONFLICT(platform) DO UPDATE SET
			update_offset = MAX(robot_stream_offsets.update_offset, excluded.update_offset),
			updated_at = excluded.updated_at
	`, platform, offset, time.Now())
	if err != nil {
		return fmt.Errorf("写入机器人轮询游标失败: %w", err)
	}
	return nil
}
