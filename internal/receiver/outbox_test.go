package receiver

import (
	"context"
	"database/sql"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

func newTestOutbox(t *testing.T) *SQLiteOutbox {
	t.Helper()
	dir := t.TempDir()
	db, err := sql.Open("sqlite3", filepath.Join(dir, "outbox.db"))
	if err != nil {
		t.Fatalf("開啟測試用 SQLite 失敗: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	outbox, err := NewSQLiteOutbox(db, nil)
	if err != nil {
		t.Fatalf("建立測試用寄件箱失敗: %v", err)
	}
	return outbox
}

func TestOutboxEnqueueAndClaim(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()

	p := Payload{
		SourceKind: SourceKindVulnerability,
		SourceID:   "vuln-1",
		Title:      "SQL injection",
		Evidence:   "dumped users",
		Body:       "row1\nrow2",
	}
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("寫入寄件箱失敗: %v", err)
	}

	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("應有 1 筆，got %d", len(items))
	}
	if items[0].Payload.Evidence != p.Evidence {
		t.Fatalf("收割資料本體必須完整保留，got %q", items[0].Payload.Evidence)
	}
	if items[0].Payload.Title != p.Title {
		t.Fatalf("標題必須完整保留，got %q", items[0].Payload.Title)
	}
}

func TestOutboxSameSourceOverwritesInsteadOfDuplicating(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()

	base := Payload{SourceKind: SourceKindVulnerability, SourceID: "vuln-1", Evidence: "first"}
	if err := outbox.Enqueue(ctx, base); err != nil {
		t.Fatalf("第一次寫入失敗: %v", err)
	}
	updated := base
	updated.Evidence = "second, stronger evidence"
	if err := outbox.Enqueue(ctx, updated); err != nil {
		t.Fatalf("第二次寫入失敗: %v", err)
	}

	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("同一來源識別應只有一筆待送資料，got %d", len(items))
	}
	if items[0].Payload.Evidence != updated.Evidence {
		t.Fatalf("應保留最新內容，got %q", items[0].Payload.Evidence)
	}
}

func TestOutboxAckRemovesItem(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()

	p := Payload{SourceKind: SourceKindVulnerability, SourceID: "vuln-1"}
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("寫入寄件箱失敗: %v", err)
	}
	if err := outbox.Ack(ctx, p.SourceKind, p.SourceID); err != nil {
		t.Fatalf("清除寄件箱紀錄失敗: %v", err)
	}
	n, err := outbox.Pending(ctx)
	if err != nil {
		t.Fatalf("統計寄件箱失敗: %v", err)
	}
	if n != 0 {
		t.Fatalf("清除後應為 0 筆，got %d", n)
	}
}

func TestOutboxNackKeepsItemAndRecordsFailure(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()

	p := Payload{SourceKind: SourceKindVulnerability, SourceID: "vuln-1", Evidence: "keep"}
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("寫入寄件箱失敗: %v", err)
	}
	if err := outbox.Nack(ctx, p.SourceKind, p.SourceID, context.DeadlineExceeded); err != nil {
		t.Fatalf("更新失敗狀態失敗: %v", err)
	}

	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("失敗後成果必須留在寄件箱，got %d", len(items))
	}
	if items[0].Attempts != 1 {
		t.Fatalf("失敗次數應為 1，got %d", items[0].Attempts)
	}
	if items[0].Payload.Evidence != "keep" {
		t.Fatal("失敗後內容必須原封不動")
	}
}

func TestOutboxRejectsPayloadWithoutProvenance(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()
	if err := outbox.Enqueue(ctx, Payload{SourceID: "no-kind"}); err == nil {
		t.Fatal("缺少 source_kind 的成果不該被接受 —— 無法溯源的資料等於廢紙")
	}
	if err := outbox.Enqueue(ctx, Payload{SourceKind: SourceKindVulnerability}); err == nil {
		t.Fatal("缺少 source_id 的成果不該被接受")
	}
}

func TestOutboxPendingCountsWaitingItems(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()
	for i := 0; i < 3; i++ {
		p := Payload{SourceKind: SourceKindProjectFact, SourceID: string(rune('a' + i))}
		if err := outbox.Enqueue(ctx, p); err != nil {
			t.Fatalf("寫入寄件箱失敗: %v", err)
		}
	}
	n, err := outbox.Pending(ctx)
	if err != nil {
		t.Fatalf("統計寄件箱失敗: %v", err)
	}
	if n != 3 {
		t.Fatalf("應有 3 筆待送，got %d", n)
	}
}

func TestOutboxPayloadRoundTripPreservesFields(t *testing.T) {
	// 寄件箱把成果序列化成 JSON 再讀出來。任何欄位遺失都會讓下游
	// 拿到缺胳膊少腿的資料，而且很難發現。
	outbox := newTestOutbox(t)
	ctx := context.Background()

	p := Payload{
		SourceKind:      SourceKindVulnerability,
		SourceID:        "vuln-rt",
		ProjectID:       "proj",
		ConversationID:  "conv",
		VulnerabilityID: "vuln-rt",
		FactKey:         "finding/api.example.com-x",
		Category:        "SQL Injection",
		Title:           "標題",
		Target:          "https://api.example.com",
		Severity:        "critical",
		Status:          "confirmed",
		Confidence:      97,
		DataType:        DataTypeCredential,
		Evidence:        "證據原文",
		Body:            "主體",
		Meta:            `{"impact":"full db read"}`,
		OccurredAt:      time.Now().UTC().Truncate(time.Millisecond),
	}
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("寫入寄件箱失敗: %v", err)
	}
	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("應有 1 筆，got %d", len(items))
	}
	got := items[0].Payload
	if !reflect.DeepEqual(got, p) {
		t.Fatalf("來回序列化後欄位不一致：\n got = %+v\nwant = %+v", got, p)
	}
}

func TestOutboxEnqueueResetsAttemptsOnNewContent(t *testing.T) {
	outbox := newTestOutbox(t)
	ctx := context.Background()

	p := Payload{SourceKind: SourceKindVulnerability, SourceID: "vuln-1", Evidence: "v1"}
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("寫入寄件箱失敗: %v", err)
	}
	if err := outbox.Nack(ctx, p.SourceKind, p.SourceID, context.DeadlineExceeded); err != nil {
		t.Fatalf("更新失敗狀態失敗: %v", err)
	}
	p.Evidence = "v2"
	if err := outbox.Enqueue(ctx, p); err != nil {
		t.Fatalf("第二次寫入失敗: %v", err)
	}
	items, err := outbox.Claim(ctx, 10)
	if err != nil {
		t.Fatalf("讀取寄件箱失敗: %v", err)
	}
	if len(items) != 1 || items[0].Attempts != 0 {
		t.Fatalf("新內容應重置失敗次數，got attempts=%d", items[0].Attempts)
	}
}
