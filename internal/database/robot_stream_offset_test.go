package database_test

import (
	"testing"

	"jysecai/internal/database"

	"go.uber.org/zap"
)

func TestRobotStreamOffsetPersistsAndNeverRegresses(t *testing.T) {
	db, err := database.NewDB(t.TempDir()+"/robot-offset.db", zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })

	offset, err := db.GetRobotStreamOffset("telegram")
	if err != nil {
		t.Fatalf("load offset: %v", err)
	}
	if offset != 0 {
		t.Fatalf("expected empty offset for unknown platform, got %d", offset)
	}

	if err := db.SaveRobotStreamOffset("telegram", 42); err != nil {
		t.Fatal(err)
	}
	offset, err = db.GetRobotStreamOffset("telegram")
	if err != nil {
		t.Fatal(err)
	}
	if offset != 42 {
		t.Fatalf("expected persisted offset 42, got %d", offset)
	}

	// 旧实例写入更小的游标不得让游标倒退（否则重启会重放已消费的消息）。
	if err := db.SaveRobotStreamOffset("telegram", 7); err != nil {
		t.Fatal(err)
	}
	offset, _ = db.GetRobotStreamOffset("telegram")
	if offset != 42 {
		t.Fatalf("offset regressed to %d", offset)
	}

	// 更大的游标必须能前进。
	if err := db.SaveRobotStreamOffset("telegram", 99); err != nil {
		t.Fatal(err)
	}
	offset, _ = db.GetRobotStreamOffset("telegram")
	if offset != 99 {
		t.Fatalf("expected offset 99, got %d", offset)
	}

	// 非正数与空平台不写入。
	if err := db.SaveRobotStreamOffset("telegram", 0); err != nil {
		t.Fatal(err)
	}
	if err := db.SaveRobotStreamOffset("", 5); err != nil {
		t.Fatal(err)
	}
	offset, _ = db.GetRobotStreamOffset("telegram")
	if offset != 99 {
		t.Fatalf("unexpected offset change to %d", offset)
	}

	// 平台之间互相独立。
	if err := db.SaveRobotStreamOffset("wecom", 5); err != nil {
		t.Fatal(err)
	}
	offset, _ = db.GetRobotStreamOffset("wecom")
	if offset != 5 {
		t.Fatalf("expected wecom offset 5, got %d", offset)
	}
	offset, _ = db.GetRobotStreamOffset("telegram")
	if offset != 99 {
		t.Fatalf("telegram offset changed by wecom write: %d", offset)
	}
}
