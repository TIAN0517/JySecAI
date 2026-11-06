package receiver

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"
)

// 整合測試需要真的 MySQL。沒有環境變數就跳過 —— CI 沒有這台機器，
// 但本機跑得起來，而且這是唯一能證明「冪等真的有冪等」的地方。
//
// 用獨立的 table prefix 跑，測完把測試表刪掉，不碰正式接收表。
//
// 建議跑在專門的測試庫（JY_SEC_TEST_MYSQL_DATABASE 指過去）而不是正式接收庫：
// 測試需要 DROP 權限才能清掉自己的測試表，而正式接收帳號刻意不給 DROP。
// 跑在正式庫也能運（清理會退成清空資料），但會留下三張空的 jytest_* 表。
func integrationSink(t *testing.T) *MySQLSink {
	t.Helper()
	host := os.Getenv("JY_SEC_TEST_MYSQL_HOST")
	if host == "" {
		t.Skip("未設定 JY_SEC_TEST_MYSQL_HOST，略過 MySQL 整合測試")
	}
	port, _ := strconv.Atoi(os.Getenv("JY_SEC_TEST_MYSQL_PORT"))
	if port == 0 {
		port = 3306
	}
	dbName := os.Getenv("JY_SEC_TEST_MYSQL_DATABASE")
	if dbName == "" {
		dbName = "jy_vuln_receiver"
	}
	prefix := "jytest_"

	cfg := MySQLConfig{
		Host:     host,
		Port:     port,
		User:     os.Getenv("JY_SEC_TEST_MYSQL_USER"),
		Password: os.Getenv("JY_SEC_TEST_MYSQL_PASSWORD"),
		Database: dbName,
		// 每個測試檔用不同前綴，避免平行測試互相踩。
		TablePrefix:     prefix,
		Timeout:         10 * time.Second,
		MaxOpenConns:    2,
		MaxIdleConns:    1,
		ConnMaxLifetime: time.Minute,
	}
	sink, err := NewMySQLSink(cfg, nil)
	if err != nil {
		t.Fatalf("建立測試用 MySQL 連線失敗: %v", err)
	}
	t.Cleanup(func() {
		dropTestTables(t, sink)
		_ = sink.Close()
	})
	return sink
}

// 接收端帳號刻意沒有 DROP 權限（平台不該能刪接收端的表），
// 所以清理要先試 DROP、失敗就退成清空資料。
// 測試資料本身用每次執行唯一的 source id，所以就算上一輪沒清乾淨也不會互相干擾。
func dropTestTables(t *testing.T, sink *MySQLSink) {
	t.Helper()
	for _, name := range []string{"receiver_ledger", "harvested_datasets", "receiver_runs"} {
		if _, err := sink.db.Exec("DROP TABLE IF EXISTS " + sink.table(name)); err == nil {
			continue
		}
		_, _ = sink.db.Exec("DELETE FROM " + sink.table(name))
	}
}

// uniqueSourceID 產生本次執行專屬的來源識別，避免跨執行殘留互相影響。
func uniqueSourceID(prefix string) string {
	return fmt.Sprintf("%s-%d", prefix, time.Now().UnixNano())
}

func TestMySQLSinkEnsureSchemaCreatesTables(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立 schema 失敗: %v", err)
	}
	for _, name := range []string{"receiver_ledger", "harvested_datasets", "receiver_runs"} {
		var count int
		if err := sink.db.QueryRowContext(ctx,
			"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?",
			sink.table(name)).Scan(&count); err != nil {
			t.Fatalf("查詢表 %s 失敗: %v", name, err)
		}
		if count != 1 {
			t.Fatalf("表 %s 應該存在", sink.table(name))
		}
	}
}

func TestMySQLSinkDeliverWritesDatasetAndLedger(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立 schema 失敗: %v", err)
	}

	p := Payload{
		SourceKind:      SourceKindVulnerability,
		SourceID:        uniqueSourceID("test-vuln"),
		ProjectID:       "proj-1",
		ConversationID:  "conv-1",
		VulnerabilityID: "test-vuln-1",
		FactKey:         "finding/api.example.com-sql",
		Category:        "SQL Injection",
		Title:           "SQL injection in /api/login",
		Target:          "https://api.example.com/login",
		Severity:        "critical",
		Status:          "confirmed",
		Confidence:      98,
		Evidence:        "payload: ' OR 1=1 --\nadmin password: hunter2",
		Body:            "reproduction steps...",
		Meta:            `{"impact":"full db read"}`,
		OccurredAt:      time.Now().UTC(),
	}

	res, err := sink.Deliver(ctx, p)
	if err != nil {
		t.Fatalf("第一次送出失敗: %v", err)
	}
	if !res.Delivered || res.DatasetID == "" {
		t.Fatalf("第一次送出應該落地並回傳 dataset id，got %+v", res)
	}

	var checksum, status, datasetID string
	if err := sink.db.QueryRowContext(ctx,
		"SELECT checksum, status, dataset_id FROM "+sink.table("receiver_ledger")+
			" WHERE source_kind=? AND source_id=?", p.SourceKind, p.SourceID).
		Scan(&checksum, &status, &datasetID); err != nil {
		t.Fatalf("讀取帳本失敗: %v", err)
	}
	if checksum != p.Checksum() {
		t.Fatal("帳本 checksum 與送出內容不符")
	}
	if status != "delivered" {
		t.Fatalf("帳本狀態應為 delivered，got %s", status)
	}
	if datasetID != res.DatasetID {
		t.Fatal("帳本 dataset id 與回傳值不符")
	}

	var rowCount, confidence int
	var sensitivity, dataType string
	if err := sink.db.QueryRowContext(ctx,
		"SELECT row_count, confidence, sensitivity, data_type FROM "+sink.table("harvested_datasets")+
			" WHERE id=?", res.DatasetID).Scan(&rowCount, &confidence, &sensitivity, &dataType); err != nil {
		t.Fatalf("讀取資料集失敗: %v", err)
	}
	if rowCount != 2 {
		t.Fatalf("row_count 應等於證據的非空行數 2，got %d", rowCount)
	}
	if confidence != 98 {
		t.Fatalf("confidence 應保留 98，got %d", confidence)
	}
	if sensitivity != SensitivityCredential {
		t.Fatalf("含 password 的證據敏感度應為 credential，got %s", sensitivity)
	}
	if dataType != DataTypeCredential {
		t.Fatalf("資料形態應為 credential，got %s", dataType)
	}
}

func TestMySQLSinkDeliverSameContentIsSkipped(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立 schema 失敗: %v", err)
	}

	p := Payload{
		SourceKind: SourceKindProjectFact,
		SourceID:   uniqueSourceID("test-fact"),
		FactKey:    "chain/api.example.com-chain",
		Title:      "attack chain",
		Body:       "step1 -> step2 -> step3",
	}

	first, err := sink.Deliver(ctx, p)
	if err != nil {
		t.Fatalf("第一次送出失敗: %v", err)
	}
	second, err := sink.Deliver(ctx, p)
	if err != nil {
		t.Fatalf("第二次送出失敗: %v", err)
	}
	if !second.Skipped || second.Delivered {
		t.Fatalf("相同內容重送應該被跳過，got %+v", second)
	}
	if second.DatasetID != first.DatasetID {
		t.Fatal("跳過時應回傳原本的 dataset id")
	}

	var count int
	if err := sink.db.QueryRowContext(ctx,
		"SELECT COUNT(*) FROM "+sink.table("harvested_datasets")+
			" WHERE source_kind=? AND source_id=?", p.SourceKind, p.SourceID).Scan(&count); err != nil {
		t.Fatalf("統計資料集筆數失敗: %v", err)
	}
	if count != 1 {
		t.Fatalf("相同內容不該產生第二筆資料集，got %d", count)
	}
}

func TestMySQLSinkDeliverChangedContentOverwritesInPlace(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立 schema 失敗: %v", err)
	}

	p := Payload{
		SourceKind: SourceKindVulnerability,
		SourceID:   uniqueSourceID("test-vuln-update"),
		Title:      "leak",
		Evidence:   "first version",
	}
	first, err := sink.Deliver(ctx, p)
	if err != nil {
		t.Fatalf("第一次送出失敗: %v", err)
	}

	p.Evidence = "second version with stronger evidence"
	second, err := sink.Deliver(ctx, p)
	if err != nil {
		t.Fatalf("第二次送出失敗: %v", err)
	}
	if !second.Delivered {
		t.Fatal("內容改變後應該覆寫而不是跳過")
	}
	if second.DatasetID != first.DatasetID {
		t.Fatal("覆寫時應沿用原本的 dataset id，不該產生新資料集")
	}

	var count int
	if err := sink.db.QueryRowContext(ctx,
		"SELECT COUNT(*) FROM "+sink.table("harvested_datasets")+
			" WHERE source_kind=? AND source_id=?", p.SourceKind, p.SourceID).Scan(&count); err != nil {
		t.Fatalf("統計資料集筆數失敗: %v", err)
	}
	if count != 1 {
		t.Fatalf("覆寫後仍應只有一筆資料集，got %d", count)
	}

	var evidence string
	if err := sink.db.QueryRowContext(ctx,
		"SELECT evidence FROM "+sink.table("harvested_datasets")+" WHERE id=?", second.DatasetID).
		Scan(&evidence); err != nil {
		t.Fatalf("讀取證據失敗: %v", err)
	}
	if evidence != p.Evidence {
		t.Fatalf("證據應已被新內容覆寫，got %q", evidence)
	}
}

func TestMySQLSinkRecordFailureLeavesTrace(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立 schema 失敗: %v", err)
	}

	p := Payload{
		SourceKind: SourceKindVulnerability,
		SourceID:   uniqueSourceID("test-vuln-fail"),
		Title:      "x",
	}
	sink.RecordFailure(ctx, p, context.DeadlineExceeded)

	var status, errText string
	if err := sink.db.QueryRowContext(ctx,
		"SELECT status, COALESCE(error_text,'') FROM "+sink.table("receiver_ledger")+
			" WHERE source_kind=? AND source_id=?", p.SourceKind, p.SourceID).
		Scan(&status, &errText); err != nil {
		t.Fatalf("讀取失敗紀錄失敗: %v", err)
	}
	if status != "failed" {
		t.Fatalf("狀態應為 failed，got %s", status)
	}
	if errText == "" {
		t.Fatal("失敗紀錄應帶錯誤原因")
	}
}

func TestMySQLSinkPing(t *testing.T) {
	sink := integrationSink(t)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := sink.Ping(ctx); err != nil {
		t.Fatalf("ping 失敗: %v", err)
	}
}

func TestMySQLConfigMaskHost(t *testing.T) {
	// 日誌是最常被外帶的載體。連線錯誤裡的主機位址不該跟著跑到聊天、工單、issue。
	cfg := MySQLConfig{Host: "10.0.0.1"}
	msg := "dial tcp 10.0.0.1:3306: connect: connection refused"
	got := cfg.MaskHost(msg)
	if strings.Contains(got, "10.0.0.1") {
		t.Fatalf("主機位址必須被遮掉，got %q", got)
	}
	if !strings.Contains(got, "<mysql-host>") {
		t.Fatalf("應該保留可讀的佔位符，got %q", got)
	}
	if !strings.Contains(got, "connection refused") {
		t.Fatalf("除錯需要的部分必須保留，got %q", got)
	}
}

func TestMySQLConfigMaskHostIsNoOpWithoutHost(t *testing.T) {
	cfg := MySQLConfig{}
	msg := "some error"
	if got := cfg.MaskHost(msg); got != msg {
		t.Fatalf("沒有設定主機時不該改動訊息，got %q", got)
	}
}
