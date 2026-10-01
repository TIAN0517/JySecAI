package database

import (
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jysecai/internal/secretstore"

	"go.uber.org/zap"
)

const (
	migrationTestKey = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
	// 另一把格式合法但內容不同的金鑰，用來模擬「換錯金鑰」。
	otherTestMasterKey = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

	legacyWebshellID   = "ws_legacy"
	legacyWebshellPass = "LEGACY-WEBSHELL-PASSWORD"
	legacyListenerID   = "listener_legacy"
	legacyListenerKey  = "LEGACY-BEACON-ENCRYPTION-KEY"
	legacyImplantToken = "LEGACY-IMPLANT-BEARER-TOKEN"
)

// useTestMasterKey 設一把確定性的主金鑰。測試走的是與正式環境完全相同的加密路徑，
// 這裡只是換掉金鑰值本身，不繞過任何加密邏輯。
func useTestMasterKey(t *testing.T) {
	t.Helper()
	t.Setenv(secretstore.MasterKeyEnvVar, migrationTestKey)
	secretstore.ResetForTesting()
	// t.Cleanup 以 LIFO 執行：先清快取，再由 t.Setenv 還原環境變數。
	t.Cleanup(secretstore.ResetForTesting)
}

// useNoMasterKey 模擬未提供主金鑰。LoadMasterKey 以 TrimSpace 判斷空值，
// 因此設成 "" 與完全未設定的行為一致。
func useNoMasterKey(t *testing.T) {
	t.Helper()
	t.Setenv(secretstore.MasterKeyEnvVar, "")
	secretstore.ResetForTesting()
	t.Cleanup(secretstore.ResetForTesting)
}

// seedLegacyPlaintextSecrets 直接以 SQL 寫入明文，模擬尚未遷移的舊資料庫。
// 刻意繞過 CreateWebshellConnection / CreateC2Listener 的加密鉤子 —— 那正是
// 遷移要處理的狀態。
func seedLegacyPlaintextSecrets(t *testing.T, db *DB) {
	t.Helper()
	if _, err := db.Exec(`
		INSERT INTO webshell_connections (id, project_id, url, password, type, method, cmd_param, remark, encoding, os, created_at)
		VALUES (?, '', 'http://127.0.0.1/shell.php', ?, 'php', 'post', 'cmd', '', '', '', ?)`,
		legacyWebshellID, legacyWebshellPass, time.Now()); err != nil {
		t.Fatalf("寫入舊版 WebShell 明文密碼: %v", err)
	}
	if _, err := db.Exec(`
		INSERT INTO c2_listeners (id, project_id, name, type, bind_host, bind_port, profile_id,
			encryption_key, implant_token, status, config_json, remark, owner_user_id, created_at)
		VALUES (?, '', 'legacy listener', 'http', '127.0.0.1', 18080, '', ?, ?, 'stopped', '{}', '', '', ?)`,
		legacyListenerID, legacyListenerKey, legacyImplantToken, time.Now()); err != nil {
		t.Fatalf("寫入舊版 C2 listener 明文機密: %v", err)
	}
}

// rawColumn 直接讀取落盤值，略過所有解密鉤子 —— 用來驗證「磁碟上」確實是密文。
func rawColumn(t *testing.T, db *DB, table, column, id string) string {
	t.Helper()
	var raw string
	// table / column 皆為本檔的測試常數，非使用者輸入。
	if err := db.QueryRow("SELECT "+column+" FROM "+table+" WHERE id = ?", id).Scan(&raw); err != nil {
		t.Fatalf("讀取 %s.%s: %v", table, column, err)
	}
	return raw
}

func assertSealedOnDisk(t *testing.T, db *DB, table, column, id, plaintext string) {
	t.Helper()
	raw := rawColumn(t, db, table, column, id)
	if raw == plaintext {
		t.Fatalf("%s.%s 仍以明文落盤：%q", table, column, raw)
	}
	if !secretstore.IsEncrypted(raw) {
		t.Fatalf("%s.%s 缺少 %s 前綴：%q", table, column, secretstore.CipherPrefix, raw)
	}
	// 遷移可重跑：不得疊成多層密文。
	if strings.HasPrefix(raw, secretstore.CipherPrefix+secretstore.CipherPrefix) {
		t.Fatalf("%s.%s 被重複加密成多層密文", table, column)
	}
}

// 舊版明文資料在重啟後必須被原地升級為密文，且讀出時仍是原文。
func TestMigrateSecretColumnsEncryptsLegacyPlaintext(t *testing.T) {
	useTestMasterKey(t)
	dbPath := filepath.Join(t.TempDir(), "legacy.db")

	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("建立舊版資料庫: %v", err)
	}
	seedLegacyPlaintextSecrets(t, db)
	if err := db.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}

	// 重啟即觸發遷移。
	migrated, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("重啟觸發遷移失敗: %v", err)
	}
	defer migrated.Close()

	assertSealedOnDisk(t, migrated, "webshell_connections", "password", legacyWebshellID, legacyWebshellPass)
	assertSealedOnDisk(t, migrated, "c2_listeners", "encryption_key", legacyListenerID, legacyListenerKey)
	assertSealedOnDisk(t, migrated, "c2_listeners", "implant_token", legacyListenerID, legacyImplantToken)

	// 應用層讀出必須仍是原文 —— 遷移不得改變資料語意。
	conn, err := migrated.GetWebshellConnection(legacyWebshellID)
	if err != nil || conn == nil {
		t.Fatalf("GetWebshellConnection: %v (%v)", err, conn)
	}
	if conn.Password != legacyWebshellPass {
		t.Errorf("遷移後 WebShell 密碼 = %q, want %q", conn.Password, legacyWebshellPass)
	}
	if conn.URL != "http://127.0.0.1/shell.php" {
		t.Errorf("遷移後 URL 被更動：%q", conn.URL)
	}

	listener, err := migrated.GetC2Listener(legacyListenerID)
	if err != nil || listener == nil {
		t.Fatalf("GetC2Listener: %v (%v)", err, listener)
	}
	if listener.EncryptionKey != legacyListenerKey {
		t.Errorf("遷移後 encryption_key = %q, want %q", listener.EncryptionKey, legacyListenerKey)
	}
	if listener.ImplantToken != legacyImplantToken {
		t.Errorf("遷移後 implant_token = %q, want %q", listener.ImplantToken, legacyImplantToken)
	}
}

// 核心安全契約：資料庫有明文機密卻沒有主金鑰時，必須啟動失敗，
// 絕不能默默留著明文繼續運作。
func TestMigrateSecretColumnsFailsClosedWithoutMasterKey(t *testing.T) {
	useTestMasterKey(t)
	dbPath := filepath.Join(t.TempDir(), "legacy.db")

	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("建立舊版資料庫: %v", err)
	}
	seedLegacyPlaintextSecrets(t, db)
	if err := db.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}

	useNoMasterKey(t)
	opened, err := NewDB(dbPath, zap.NewNop())
	if err == nil {
		_ = opened.Close()
		t.Fatal("資料庫仍有明文機密卻缺少主金鑰時，NewDB 竟成功 —— 會讓明文繼續留在磁碟上")
	}
	if !strings.Contains(err.Error(), secretstore.MasterKeyEnvVar) {
		t.Errorf("錯誤訊息未指明應設定的環境變數 %s：%v", secretstore.MasterKeyEnvVar, err)
	}
	// 外層檢查的價值在診斷：應報出待遷移的筆數，讓維運知道要遷移多少資料。
	// 少了這個檢查，錯誤仍會從底層 Encrypt 冒出（安全上仍是 fail closed），
	// 但使用者只會看到一句籠統的解密失敗，看不出規模。
	if !strings.Contains(err.Error(), "3 筆") {
		t.Errorf("錯誤訊息未報出待遷移筆數：%v", err)
	}

	// 補上金鑰後必須能正常啟動，且資料完好 —— 這是 fail closed 的操作指引。
	useTestMasterKey(t)
	recovered, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("補上主金鑰後仍無法啟動: %v", err)
	}
	defer recovered.Close()
	conn, err := recovered.GetWebshellConnection(legacyWebshellID)
	if err != nil || conn == nil || conn.Password != legacyWebshellPass {
		t.Fatalf("補上金鑰後資料未正確還原：%+v (%v)", conn, err)
	}
}

// 全新安裝沒有任何受保護的值，因此不該要求主金鑰 —— 否則會擋住所有首次部署。
func TestMigrateSecretColumnsSkippedWhenNoSecretsExist(t *testing.T) {
	useNoMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "fresh.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("全新安裝不應要求主金鑰: %v", err)
	}
	if err := db.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}
}

// 遷移必須可重跑：重複開啟資料庫不會產生多層密文，資料也不會劣化。
func TestMigrateSecretColumnsIsIdempotent(t *testing.T) {
	useTestMasterKey(t)
	dbPath := filepath.Join(t.TempDir(), "legacy.db")

	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("建立舊版資料庫: %v", err)
	}
	seedLegacyPlaintextSecrets(t, db)
	if err := db.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}

	for round := 1; round <= 3; round++ {
		reopened, err := NewDB(dbPath, zap.NewNop())
		if err != nil {
			t.Fatalf("第 %d 次重啟失敗: %v", round, err)
		}
		assertSealedOnDisk(t, reopened, "webshell_connections", "password", legacyWebshellID, legacyWebshellPass)
		conn, err := reopened.GetWebshellConnection(legacyWebshellID)
		if err != nil || conn == nil || conn.Password != legacyWebshellPass {
			t.Fatalf("第 %d 次重啟後密碼劣化：%+v (%v)", round, conn, err)
		}
		if err := reopened.Close(); err != nil {
			t.Fatalf("第 %d 次 Close: %v", round, err)
		}
	}
}

// 走正常 API 寫入的資料也必須在磁碟上就是密文。
func TestWebshellPasswordEncryptedAtRest(t *testing.T) {
	useTestMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "ws.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	defer db.Close()

	const plaintext = "AT-REST-WEBSHELL-SECRET"
	conn := &WebShellConnection{
		ID: "ws_atrest", URL: "http://127.0.0.1/x.php", Password: plaintext,
		Type: "php", Method: "post", CmdParam: "cmd", CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(conn); err != nil {
		t.Fatalf("CreateWebshellConnection: %v", err)
	}
	assertSealedOnDisk(t, db, "webshell_connections", "password", conn.ID, plaintext)

	// 呼叫端持有的結構仍是明文（加密不應外溢到呼叫端）。
	if conn.Password != plaintext {
		t.Errorf("CreateWebshellConnection 改動了呼叫端的密碼欄位：%q", conn.Password)
	}

	got, err := db.GetWebshellConnection(conn.ID)
	if err != nil || got == nil {
		t.Fatalf("GetWebshellConnection: %v", err)
	}
	if got.Password != plaintext {
		t.Errorf("讀回密碼 = %q, want %q", got.Password, plaintext)
	}
}

func TestC2ListenerSecretsEncryptedAtRest(t *testing.T) {
	useTestMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "c2.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	defer db.Close()

	listener := &C2Listener{
		ID: "listener_atrest", Name: "test", Type: "http", BindHost: "127.0.0.1", BindPort: 18081,
		EncryptionKey: "AT-REST-BEACON-KEY", ImplantToken: "AT-REST-IMPLANT-TOKEN",
	}
	if err := db.CreateC2Listener(listener); err != nil {
		t.Fatalf("CreateC2Listener: %v", err)
	}
	assertSealedOnDisk(t, db, "c2_listeners", "encryption_key", listener.ID, "AT-REST-BEACON-KEY")
	assertSealedOnDisk(t, db, "c2_listeners", "implant_token", listener.ID, "AT-REST-IMPLANT-TOKEN")

	if listener.EncryptionKey != "AT-REST-BEACON-KEY" || listener.ImplantToken != "AT-REST-IMPLANT-TOKEN" {
		t.Error("CreateC2Listener 改動了呼叫端持有的機密欄位")
	}

	got, err := db.GetC2Listener(listener.ID)
	if err != nil || got == nil {
		t.Fatalf("GetC2Listener: %v", err)
	}
	if got.EncryptionKey != "AT-REST-BEACON-KEY" || got.ImplantToken != "AT-REST-IMPLANT-TOKEN" {
		t.Errorf("讀回的機密欄位不符：%q / %q", got.EncryptionKey, got.ImplantToken)
	}

	// 列表路徑也必須解密，否則 UI 會拿到 "v1:..." 這種密文。
	listed, err := db.ListC2Listeners()
	if err != nil {
		t.Fatalf("ListC2Listeners: %v", err)
	}
	if len(listed) != 1 {
		t.Fatalf("ListC2Listeners len = %d, want 1", len(listed))
	}
	if listed[0].EncryptionKey != "AT-REST-BEACON-KEY" || listed[0].ImplantToken != "AT-REST-IMPLANT-TOKEN" {
		t.Errorf("列表回傳未解密的機密：%q / %q", listed[0].EncryptionKey, listed[0].ImplantToken)
	}
}

// 更新既有連線時，若呼叫端帶的是明文，重新加密後不得疊成多層密文。
func TestC2ListenerUpdateReencryptsPlaintextNotDoublesSeal(t *testing.T) {
	useTestMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "c2upd.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	defer db.Close()

	listener := &C2Listener{
		ID: "listener_upd", Name: "test", Type: "http", BindHost: "127.0.0.1", BindPort: 18082,
		EncryptionKey: "KEY-V1", ImplantToken: "TOKEN-V1",
	}
	if err := db.CreateC2Listener(listener); err != nil {
		t.Fatalf("CreateC2Listener: %v", err)
	}

	listener.Name = "renamed"
	listener.EncryptionKey = "KEY-V2"
	if err := db.UpdateC2Listener(listener); err != nil {
		t.Fatalf("UpdateC2Listener: %v", err)
	}
	raw := rawColumn(t, db, "c2_listeners", "encryption_key", listener.ID)
	if strings.HasPrefix(raw, secretstore.CipherPrefix+secretstore.CipherPrefix) {
		t.Fatal("更新後被加密成多層密文")
	}
	got, _ := db.GetC2Listener(listener.ID)
	if got == nil || got.EncryptionKey != "KEY-V2" {
		t.Fatalf("更新後讀回 = %+v, want KEY-V2", got)
	}
	if got.Name != "renamed" {
		t.Errorf("名稱未更新：%q", got.Name)
	}
}

// 空值代表「此欄位未設定」，不該被加密成密文 —— 否則每次解密都只是拿回空字串，
// 卻讓資料庫裡多出看似有值、實際不存在的密文。
func TestEmptySecretColumnsStayEmpty(t *testing.T) {
	useTestMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "empty.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("NewDB: %v", err)
	}
	defer db.Close()

	listener := &C2Listener{ID: "listener_empty", Name: "test", Type: "http", BindHost: "127.0.0.1", BindPort: 18083}
	if err := db.CreateC2Listener(listener); err != nil {
		t.Fatalf("CreateC2Listener: %v", err)
	}
	if raw := rawColumn(t, db, "c2_listeners", "encryption_key", listener.ID); raw != "" {
		t.Errorf("空 encryption_key 被寫成 %q", raw)
	}
	if raw := rawColumn(t, db, "c2_listeners", "implant_token", listener.ID); raw != "" {
		t.Errorf("空 implant_token 被寫成 %q", raw)
	}
	conn := &WebShellConnection{ID: "ws_empty", URL: "http://127.0.0.1/y.php", Type: "php", Method: "post", CreatedAt: time.Now()}
	if err := db.CreateWebshellConnection(conn); err != nil {
		t.Fatalf("CreateWebshellConnection: %v", err)
	}
	if raw := rawColumn(t, db, "webshell_connections", "password", conn.ID); raw != "" {
		t.Errorf("空密碼被寫成 %q", raw)
	}
}

// 換錯主金鑰時必須在啟動期就被擋下，而不是等到使用者第一次讀取才看到無法解密。
//
// 這個情境特別容易漏掉：資料已全部遷移完畢時待遷移數為 0，遷移整段會被略過，
// 服務看似正常啟動，問題要到讀取才浮現 —— 使用者只會看到一句「解密失敗」。
func TestStartupFailsWhenMasterKeyDoesNotMatchExistingCiphertext(t *testing.T) {
	const secret = "ROTATE-ME-PASSWORD"
	useTestMasterKey(t)
	dbPath := filepath.Join(t.TempDir(), "rotated.db")

	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("建立資料庫: %v", err)
	}
	conn := &WebShellConnection{
		ID: "ws_rotated", URL: "http://127.0.0.1/rot.php", Password: secret,
		Type: "php", Method: "post", CmdParam: "cmd", CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(conn); err != nil {
		t.Fatalf("CreateWebshellConnection: %v", err)
	}
	if err := db.Close(); err != nil {
		t.Fatalf("Close: %v", err)
	}
	// 確認種子資料確實已是密文（否則本測試會因走不到驗證分支而虛綠）。
	assertSealedOnDisk(t, mustReopen(t, dbPath), "webshell_connections", "password", conn.ID, secret)

	// 換一把格式合法、內容錯誤的金鑰。
	t.Setenv(secretstore.MasterKeyEnvVar, otherTestMasterKey)
	secretstore.ResetForTesting()
	t.Cleanup(secretstore.ResetForTesting)

	opened, err := NewDB(dbPath, zap.NewNop())
	if err == nil {
		_ = opened.Close()
		t.Fatal("金鑰與既有密文不符時 NewDB 竟成功 —— 問題會延後到讀取才爆")
	}
	if !strings.Contains(err.Error(), secretstore.MasterKeyEnvVar) {
		t.Errorf("錯誤訊息未指明環境變數 %s：%v", secretstore.MasterKeyEnvVar, err)
	}

	// 換回原本的金鑰即可正常啟動，且資料未被毀損 —— 這是 fail closed 的操作指引。
	useTestMasterKey(t)
	recovered, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("換回正確金鑰後仍無法啟動: %v", err)
	}
	defer recovered.Close()
	got, err := recovered.GetWebshellConnection(conn.ID)
	if err != nil || got == nil || got.Password != secret {
		t.Fatalf("換回正確金鑰後資料未正確還原：%+v (%v)", got, err)
	}
}

func mustReopen(t *testing.T, dbPath string) *DB {
	t.Helper()
	db, err := NewDB(dbPath, zap.NewNop())
	if err != nil {
		t.Fatalf("重新開啟資料庫: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

// 缺少主金鑰時，寫入有值的新連線必須失敗 —— 不得寫下明文。
func TestWriteFailsClosedWithoutMasterKey(t *testing.T) {
	useNoMasterKey(t)
	db, err := NewDB(filepath.Join(t.TempDir(), "nokey.db"), zap.NewNop())
	if err != nil {
		t.Fatalf("全新安裝不應要求主金鑰: %v", err)
	}
	defer db.Close()

	conn := &WebShellConnection{
		ID: "ws_nokey", URL: "http://127.0.0.1/z.php", Password: "MUST-NOT-BE-PLAINTEXT",
		Type: "php", Method: "post", CreatedAt: time.Now(),
	}
	if err := db.CreateWebshellConnection(conn); err == nil {
		t.Fatal("缺少主金鑰時寫入帶密碼的連線竟成功")
	}
	// 預期是整筆寫入被拒絕、列不存在 —— 比「寫成空值」更安全。
	var count int
	if err := db.QueryRow(`SELECT COUNT(*) FROM webshell_connections WHERE id = ?`, conn.ID).Scan(&count); err != nil {
		t.Fatalf("統計 webshell_connections: %v", err)
	}
	if count != 0 {
		t.Errorf("寫入失敗後仍留下 %d 筆列，磁碟上可能已有明文", count)
	}
}
