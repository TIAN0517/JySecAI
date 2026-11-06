package app

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"go.uber.org/zap"

	"jysecai/internal/config"
	"jysecai/internal/database"
	"jysecai/internal/receiver"

	_ "github.com/go-sql-driver/mysql"
)

// TestEndToEndHarvestedDataLandsInMySQL 端到端驗收：走真實的寫入路徑 ——
// 平台資料庫寫入 → hook → 本地寄件箱 → 主力機 MySQL → 真的查得到資料。
//
// 這是唯一能證明「收割成果真的進到主力機」的驗收。中間任何一段被剪掉
// （hook 沒掛上、寄件箱沒寫、排程器沒跑、冪等壞了、schema 對不上），
// 這裡就會紅。
//
// 需要真的 MySQL：沒設環境變數就跳過。
func TestEndToEndHarvestedDataLandsInMySQL(t *testing.T) {
	host := os.Getenv("JY_SEC_TEST_MYSQL_HOST")
	if host == "" {
		t.Skip("未設定 JY_SEC_TEST_MYSQL_HOST，略過端到端驗收")
	}
	port, _ := strconv.Atoi(os.Getenv("JY_SEC_TEST_MYSQL_PORT"))
	if port == 0 {
		port = 3306
	}
	dbName := os.Getenv("JY_SEC_TEST_MYSQL_DATABASE")
	if dbName == "" {
		dbName = "jy_vuln_receiver"
	}
	user := os.Getenv("JY_SEC_TEST_MYSQL_USER")
	password := os.Getenv("JY_SEC_TEST_MYSQL_PASSWORD")

	logger := zap.NewNop()

	// 1. 用真實的接收端（正式表名，不用測試前綴）把 schema 建起來。
	sinkCfg := receiver.MySQLConfig{
		Host: host, Port: port, User: user, Password: password, Database: dbName,
		Timeout: 15 * time.Second, MaxOpenConns: 4, MaxIdleConns: 2,
		ConnMaxLifetime: 30 * time.Minute,
	}
	sink, err := receiver.NewMySQLSink(sinkCfg, logger)
	if err != nil {
		t.Fatalf("連線主力機 MySQL 失敗: %v", err)
	}
	defer sink.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := sink.EnsureSchema(ctx); err != nil {
		t.Fatalf("建立接收端 schema 失敗: %v", err)
	}

	// 2. 起一個真正的平台資料庫（SQLite），走真實的寫入路徑。
	dir := t.TempDir()
	db, err := database.NewDB(filepath.Join(dir, "e2e.db"), logger)
	if err != nil {
		t.Fatalf("建立測試用平台資料庫失敗: %v", err)
	}
	defer db.Close()

	cfg := &config.Config{}
	cfg.ExternalMySQL = config.ExternalMySQLConfig{
		Enabled: true, Host: host, Port: port, User: user, Password: password,
		Database: dbName, TimeoutSeconds: 15, BatchSize: 50, PollIntervalSeconds: 1,
	}
	bridge := setupExternalReceiver(cfg, db, logger)
	if bridge == nil {
		t.Fatal("接收端沒有啟動")
	}
	defer bridge.Stop()

	// 3. 寫一筆漏洞（含收割到的資料）與一筆專案事實。
	//    漏洞有 conversation 外鍵、專案事實有 project 外鍵，都要先建真的。
	conv, err := db.CreateConversation("端到端驗收對話", database.ConversationCreateMeta{Source: "e2e"})
	if err != nil {
		t.Fatalf("建立對話失敗: %v", err)
	}
	proj, err := db.CreateProject(&database.Project{
		Name:        "端到端驗收專案",
		Description: "receiver e2e",
		Status:      "active",
	})
	if err != nil {
		t.Fatalf("建立專案失敗: %v", err)
	}
	marker := fmt.Sprintf("e2e-%d", time.Now().UnixNano())
	vuln := &database.Vulnerability{
		ConversationID: conv.ID,
		ProjectID:      proj.ID,
		Title:          "端到端驗收漏洞 " + marker,
		Description:    "透過接收端送出的收割成果",
		Severity:       "critical",
		Status:         "confirmed",
		Confidence:     97,
		Type:           "SQL Injection",
		Target:         "https://api.example.com/login",
		Evidence:       "dumped users table\npassword: hunter2",
		Impact:         "full db read",
		Recommendation: "parameterized queries",
	}
	created, err := db.CreateVulnerability(vuln)
	if err != nil {
		t.Fatalf("寫入漏洞失敗: %v", err)
	}

	fact := &database.ProjectFact{
		ProjectID:  proj.ID,
		FactKey:    "finding/api.example.com-" + marker,
		Category:   "finding",
		Summary:    "收割到的使用者資料 " + marker,
		Body:       "row1\nrow2\nrow3",
		Confidence: "confirmed",
	}
	createdFact, err := db.UpsertProjectFact(fact)
	if err != nil {
		t.Fatalf("寫入專案事實失敗: %v", err)
	}
	fact.ID = createdFact.ID

	// 4. 等落地（送出是非同步的）。
	raw, err := sql.Open("mysql", sinkCfg.DSN())
	if err != nil {
		t.Fatalf("開啟查詢連線失敗: %v", err)
	}
	defer raw.Close()

	// 這個驗收寫的是正式接收庫，所以驗完要把自己的測試資料清掉 ——
	// 測試資料留在正式倉儲裡，之後就沒人分得清哪一筆是真的收割成果。
	//
	// 清理時要自己開連線：t.Cleanup 是在測試函式 return 之後才跑的，
	// 那時 defer raw.Close() 已經把 raw 關掉了。
	t.Cleanup(func() {
		cleanupConn, cleanupErr := sql.Open("mysql", sinkCfg.DSN())
		if cleanupErr != nil {
			t.Errorf("開啟清理用連線失敗: %v", cleanupErr)
			return
		}
		defer cleanupConn.Close()
		cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cleanupCancel()
		for _, sourceID := range []string{created.ID, fact.ID} {
			if _, err := cleanupConn.ExecContext(cleanupCtx,
				"DELETE FROM harvested_datasets WHERE source_id=?", sourceID); err != nil {
				t.Errorf("清理 harvested_datasets 失敗: %v", err)
			}
			if _, err := cleanupConn.ExecContext(cleanupCtx,
				"DELETE FROM receiver_ledger WHERE source_id=?", sourceID); err != nil {
				t.Errorf("清理 receiver_ledger 失敗: %v", err)
			}
		}
	})

	var vulnRows, factRows int
	deadline := time.Now().Add(30 * time.Second)
	for time.Now().Before(deadline) {
		if err := raw.QueryRowContext(ctx,
			"SELECT COUNT(*) FROM harvested_datasets WHERE source_kind='vulnerability' AND source_id=?",
			created.ID).Scan(&vulnRows); err != nil {
			t.Fatalf("查詢漏洞資料集失敗: %v", err)
		}
		if err := raw.QueryRowContext(ctx,
			"SELECT COUNT(*) FROM harvested_datasets WHERE source_kind='project_fact' AND project_id=? AND fact_key=?",
			proj.ID, fact.FactKey).Scan(&factRows); err != nil {
			t.Fatalf("查詢專案事實資料集失敗: %v", err)
		}
		if vulnRows == 1 && factRows == 1 {
			break
		}
		time.Sleep(200 * time.Millisecond)
	}
	if vulnRows != 1 {
		t.Fatalf("漏洞資料集應落地 1 筆，got %d", vulnRows)
	}
	if factRows != 1 {
		t.Fatalf("專案事實資料集應落地 1 筆，got %d", factRows)
	}

	// 5. 驗證落地內容：溯源、敏感度、收割資料本體都在。
	var (
		gotProject, gotConv, gotVulnID, gotFactKey, gotTarget string
		gotSensitivity, gotDataType                           string
		gotConfidence, gotRowCount                            int
		gotEvidence, gotBody                                  string
	)
	if err := raw.QueryRowContext(ctx,
		`SELECT project_id, conversation_id, vulnerability_id, fact_key, target,
		        sensitivity, data_type, confidence, row_count, evidence, body
		 FROM harvested_datasets WHERE source_kind='vulnerability' AND source_id=?`,
		created.ID).Scan(&gotProject, &gotConv, &gotVulnID, &gotFactKey, &gotTarget,
		&gotSensitivity, &gotDataType, &gotConfidence, &gotRowCount, &gotEvidence, &gotBody); err != nil {
		t.Fatalf("讀取落地資料失敗: %v", err)
	}
	if gotProject != proj.ID || gotConv != conv.ID || gotVulnID != created.ID {
		t.Fatalf("溯源欄位不完整：project=%q conv=%q vuln=%q", gotProject, gotConv, gotVulnID)
	}
	if gotTarget != "https://api.example.com/login" {
		t.Fatalf("目標應原樣落地，got %q", gotTarget)
	}
	if gotConfidence != 97 {
		t.Fatalf("confidence 應為 97，got %d", gotConfidence)
	}
	if gotSensitivity != receiver.SensitivityCredential {
		t.Fatalf("含 password 的證據敏感度應為 credential，got %s", gotSensitivity)
	}
	if gotEvidence == "" {
		t.Fatal("收割到的證據原文必須落地")
	}
	if gotRowCount != 2 {
		t.Fatalf("收割資料筆數應為 2，got %d", gotRowCount)
	}

	// 專案事實那筆：目標 DNS 與收割資料本體。
	var factTarget, factBody string
	if err := raw.QueryRowContext(ctx,
		`SELECT target, body FROM harvested_datasets
		 WHERE source_kind='project_fact' AND fact_key=?`, fact.FactKey).
		Scan(&factTarget, &factBody); err != nil {
		t.Fatalf("讀取專案事實落地資料失敗: %v", err)
	}
	if factTarget != "api.example.com" {
		t.Fatalf("專案事實的目標 DNS 應為 api.example.com，got %q", factTarget)
	}
	if factBody != "row1\nrow2\nrow3" {
		t.Fatalf("專案事實的收割資料本體應原樣落地，got %q", factBody)
	}

	// 6. 冪等：同一筆再寫一次不該產生第二筆資料集。
	updated := *created
	if err := db.UpdateVulnerability(created.ID, &updated); err != nil {
		t.Fatalf("更新漏洞失敗: %v", err)
	}

	time.Sleep(3 * time.Second)
	var dupRows int
	if err := raw.QueryRowContext(ctx,
		"SELECT COUNT(*) FROM harvested_datasets WHERE source_kind='vulnerability' AND source_id=?",
		created.ID).Scan(&dupRows); err != nil {
		t.Fatalf("統計重複資料集失敗: %v", err)
	}
	if dupRows != 1 {
		t.Fatalf("同一來源識別應只有一筆資料集，got %d", dupRows)
	}

	// 7. 送完之後本地寄件箱必須是空的 —— 成果不該在兩邊各留一份。
	if pending := bridge.Pending(context.Background()); pending != 0 {
		t.Fatalf("送出完成後本地寄件箱應清空，got %d", pending)
	}
}

// TestHarvestedDataSurvivesUnreachableMySQL 驗證「本地寄件箱」的存在理由：
// 外部 MySQL 連不上時，收割成果必須安全留在平台自己的 SQLite 裡，
// 而不是消失。
//
// 沒有這條，外部資料庫一故障，收割成果就會靜默流失 —— 而且是那種
// 「看起來一切正常、只是少了資料」的流失。
func TestHarvestedDataSurvivesUnreachableMySQL(t *testing.T) {
	logger := zap.NewNop()

	dir := t.TempDir()
	db, err := database.NewDB(filepath.Join(dir, "offline.db"), logger)
	if err != nil {
		t.Fatalf("建立測試用平台資料庫失敗: %v", err)
	}
	defer db.Close()

	cfg := &config.Config{}
	cfg.ExternalMySQL = config.ExternalMySQLConfig{
		Enabled: true,
		// 保留測試位址：一個不會有人監聽的連接埠。
		Host: "127.0.0.1", Port: 1, User: "jy_receiver", Password: "x",
		Database: "jy_vuln_receiver",
		// 逾時調短，讓「連不上」很快發生，不用等 10 秒。
		TimeoutSeconds:      1,
		BatchSize:           50,
		PollIntervalSeconds: 1,
	}
	bridge := setupExternalReceiver(cfg, db, logger)
	if bridge == nil {
		t.Fatal("接收端應該照常啟動 —— 外部 MySQL 連不上不代表接收端不能用")
	}
	defer bridge.Stop()

	conv, err := db.CreateConversation("離線驗收對話", database.ConversationCreateMeta{Source: "e2e"})
	if err != nil {
		t.Fatalf("建立對話失敗: %v", err)
	}
	marker := fmt.Sprintf("offline-%d", time.Now().UnixNano())
	if _, err := db.CreateVulnerability(&database.Vulnerability{
		ConversationID: conv.ID,
		Title:          "離線驗收漏洞 " + marker,
		Severity:       "critical",
		Status:         "confirmed",
		Confidence:     95,
		Type:           "SQL Injection",
		Target:         "https://api.example.com/login",
		Evidence:       "password: hunter2\nuser@example.com",
	}); err != nil {
		t.Fatalf("寫入漏洞失敗: %v", err)
	}

	// 成果必須出現在本地寄件箱裡。
	deadline := time.Now().Add(10 * time.Second)
	var pending int
	for time.Now().Before(deadline) {
		pending = bridge.Pending(context.Background())
		if pending > 0 {
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
	if pending == 0 {
		t.Fatal("外部 MySQL 連不上時，收割成果必須留在本地寄件箱 —— 不能消失")
	}

	// 而且必須真的存得住：直接查平台的 SQLite。
	var evidence string
	if err := db.QueryRow(
		`SELECT payload_json FROM receiver_outbox WHERE source_kind='vulnerability' AND payload_json LIKE ?`,
		"%"+marker+"%").Scan(&evidence); err != nil {
		t.Fatalf("查詢本地寄件箱失敗: %v", err)
	}
	if evidence == "" {
		t.Fatal("寄件箱內容不可為空")
	}
	// 收割到的資料本體必須完整留在本地寄件箱 —— 但「完整」是指資料沒有遺失，
	// 不是指憑證要以明文留在磁碟上：寄件箱的內容最終就是要送到外部 MySQL，
	// 所以遮蔽必須在進寄件箱之前就做完，否則未遮蔽的密碼會先躺在本地等待外送。
	if strings.Contains(evidence, "hunter2") {
		t.Fatalf("寄件箱裡不應留有明文憑證: %s", evidence)
	}
	if !strings.Contains(evidence, "***") {
		t.Fatal("憑證應已被遮蔽成 ***")
	}
	if !strings.Contains(evidence, marker) {
		t.Fatal("收割到的資料本體必須完整留在本地寄件箱")
	}
}
