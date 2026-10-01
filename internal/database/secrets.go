package database

import (
	"fmt"
	"strings"

	"jysecai/internal/secretstore"

	"go.uber.org/zap"
)

// 本檔負責把三個機密欄位在「寫入時加密、讀出時解密」：
//
//	c2_listeners.encryption_key   —— beacon 通用的 AES-256 金鑰
//	c2_listeners.implant_token    —— beacon check-in 用的 bearer token
//	webshell_connections.password —— 目標 WebShell 的存取密碼
//
// 這三者的共通點是：持有者即可偽造 C2 beacon 或在目標主機執行任意指令。
// 以明文落盤代表 SQLite 檔案（連同備份、快照、誤傳）一旦外洩即全數失守。

// secretColumnMigration 描述一個需要 at-rest 加密的欄位。
type secretColumnMigration struct {
	table  string
	column string
	// 僅在該欄位有實際值時才需要主金鑰。
	idColumn string
}

var secretColumnMigrations = []secretColumnMigration{
	{table: "c2_listeners", column: "encryption_key", idColumn: "id"},
	{table: "c2_listeners", column: "implant_token", idColumn: "id"},
	{table: "webshell_connections", column: "password", idColumn: "id"},
}

// migrateSecretColumns 把歷史明文原地升級為密文。
//
// 行為契約（刻意 fail closed）：
//   - 資料庫中完全沒有受保護欄位值時 → 不需要主金鑰， 直接略過。
//     這讓全新安裝與既有測試不受影響。
//   - 一旦存在任何受保護的值而缺少／不合法的主金鑰 → 啟動失敗，
//     絕不回退到明文讀寫。錯誤訊息會指出應設定的環境變數。
//   - 已全部遷移完畢但金鑰換錯 → 同樣在啟動期失敗，而不是等到第一次讀取才爆。
func (db *DB) migrateSecretColumns() error {
	pending, err := db.countPendingSecretColumns()
	if err != nil {
		return err
	}
	if pending > 0 {
		// 這裡刻意先載入金鑰：載入失敗就讓啟動失敗，而不是默默留著明文繼續跑。
		if _, err := secretstore.LoadMasterKey(); err != nil {
			return fmt.Errorf("資料庫中有 %d 筆機密欄位仍為明文，且無法載入主金鑰以完成遷移: %w", pending, err)
		}
		migrated := 0
		for _, m := range secretColumnMigrations {
			n, err := db.migrateSecretColumn(m)
			if err != nil {
				return fmt.Errorf("遷移 %s.%s 失敗: %w", m.table, m.column, err)
			}
			migrated += n
		}
		if db.logger != nil {
			db.logger.Info("已完成機密欄位 at-rest 加密遷移",
				zap.Int("fields", migrated),
				zap.String("master_key_env", secretstore.MasterKeyEnvVar))
		}
	}
	// 驗證放在遷移之後而非之前，且在 pending == 0 時也要執行：
	// 換錯金鑰時待遷移數為 0、遷整段會被略過，服務照常啟動，
	// 直到使用者第一次讀取該資料才看到「解密失敗」——那是很難自我診斷的狀態。
	return db.verifyMasterKeyMatchesData()
}

// verifyMasterKeyMatchesData 抽樣解密每個受保護欄位既有的一筆密文，確認主金鑰正確。
//
// 抽樣一筆而非全部：這是啟動期的健全性檢查，O(1) 足以抓出「金鑰根本換錯了」
// 這種全域性錯誤；個別單筆密文損毀由讀取當下回報即可。
func (db *DB) verifyMasterKeyMatchesData() error {
	for _, m := range secretColumnMigrations {
		var raw string
		err := db.QueryRow(fmt.Sprintf(
			`SELECT %s FROM %s WHERE %s LIKE ? LIMIT 1`,
			m.column, m.table, m.column), secretstore.CipherPrefix+"%").Scan(&raw)
		if err != nil {
			if isMissingTableErr(err) || strings.Contains(err.Error(), "no rows") {
				// 該表不存在，或此欄位尚無任何密文 —— 都無法用來驗證金鑰，略過。
				continue
			}
			return fmt.Errorf("驗證主金鑰時讀取 %s.%s 失敗: %w", m.table, m.column, err)
		}
		if _, err := secretstore.Decrypt(raw); err != nil {
			return fmt.Errorf("%s.%s 已有密文，但 %s 與其不符: %w。請確認環境變數設定的是這份資料庫原本使用的主金鑰",
				m.table, m.column, secretstore.MasterKeyEnvVar, err)
		}
	}
	return nil
}

// countPendingSecretColumns 統計仍為明文的欄位數。
func (db *DB) countPendingSecretColumns() (int, error) {
	total := 0
	for _, m := range secretColumnMigrations {
		var n int
		// 表格可能不存在於極舊的資料庫；這種情況視為 0，不阻擋啟動。
		err := db.QueryRow(fmt.Sprintf(
			`SELECT COUNT(*) FROM %s WHERE %s IS NOT NULL AND TRIM(%s) <> '' AND %s NOT LIKE ?`,
			m.table, m.column, m.column, m.column), secretstore.CipherPrefix+"%").Scan(&n)
		if err != nil {
			if isMissingTableErr(err) {
				continue
			}
			return 0, fmt.Errorf("統計 %s.%s 明文值失敗: %w", m.table, m.column, err)
		}
		total += n
	}
	return total, nil
}

func (db *DB) migrateSecretColumn(m secretColumnMigration) (int, error) {
	rows, err := db.Query(fmt.Sprintf(
		`SELECT %s, %s FROM %s WHERE %s IS NOT NULL AND TRIM(%s) <> '' AND %s NOT LIKE ?`,
		m.idColumn, m.column, m.table, m.column, m.column, m.column), secretstore.CipherPrefix+"%")
	if err != nil {
		if isMissingTableErr(err) {
			return 0, nil
		}
		return 0, err
	}
	defer rows.Close()

	type pending struct {
		id  string
		raw string
	}
	var batch []pending
	for rows.Next() {
		var p pending
		if err := rows.Scan(&p.id, &p.raw); err != nil {
			return 0, err
		}
		batch = append(batch, p)
	}
	if err := rows.Err(); err != nil {
		return 0, err
	}
	// rows 尚未關閉前不可在同一連線上寫入（WAL 下 SQLite 仍可能鎖）；
	// 先收集再逐筆更新，並在每筆上驗證解密後能還原原文。
	for _, p := range batch {
		sealed, err := secretstore.Encrypt(p.raw)
		if err != nil {
			return 0, err
		}
		if _, err := db.Exec(fmt.Sprintf(`UPDATE %s SET %s = ? WHERE %s = ?`, m.table, m.column, m.idColumn), sealed, p.id); err != nil {
			return 0, err
		}
		// 立刻回讀驗證：確保遷移沒有把資料改成解不開的狀態。
		var check string
		if err := db.QueryRow(fmt.Sprintf(`SELECT %s FROM %s WHERE %s = ?`, m.column, m.table, m.idColumn), p.id).Scan(&check); err != nil {
			return 0, err
		}
		plain, err := secretstore.Decrypt(check)
		if err != nil {
			return 0, fmt.Errorf("遷移後回讀驗證失敗 (%s=%s): %w", m.table, p.id, err)
		}
		if plain != p.raw {
			return 0, fmt.Errorf("遷移後回讀值不一致 (%s=%s)", m.table, p.id)
		}
	}
	return len(batch), nil
}

func isMissingTableErr(err error) bool {
	return err != nil && strings.Contains(strings.ToUpper(err.Error()), "NO SUCH TABLE")
}

// sealListenerSecrets 在寫入前加密 C2 listener 的兩個機密欄位。
func sealListenerSecrets(l *C2Listener) error {
	if l == nil {
		return nil
	}
	var err error
	if l.EncryptionKey, err = secretstore.Encrypt(l.EncryptionKey); err != nil {
		return fmt.Errorf("加密 C2 listener encryption_key 失敗: %w", err)
	}
	if l.ImplantToken, err = secretstore.Encrypt(l.ImplantToken); err != nil {
		return fmt.Errorf("加密 C2 listener implant_token 失敗: %w", err)
	}
	return nil
}

// openListenerSecrets 在讀出後解密 C2 listener 的兩個機密欄位。
func openListenerSecrets(l *C2Listener) error {
	if l == nil {
		return nil
	}
	var err error
	if l.EncryptionKey, err = secretstore.Decrypt(l.EncryptionKey); err != nil {
		return fmt.Errorf("解密 C2 listener encryption_key 失敗: %w", err)
	}
	if l.ImplantToken, err = secretstore.Decrypt(l.ImplantToken); err != nil {
		return fmt.Errorf("解密 C2 listener implant_token 失敗: %w", err)
	}
	return nil
}

// sealWebshellPassword 在寫入前加密 WebShell 密碼。
func sealWebshellPassword(c *WebShellConnection) error {
	if c == nil {
		return nil
	}
	pw, err := secretstore.Encrypt(c.Password)
	if err != nil {
		return fmt.Errorf("加密 WebShell 密碼失敗: %w", err)
	}
	c.Password = pw
	return nil
}

// openWebshellPassword 在讀出後解密 WebShell 密碼。
func openWebshellPassword(c *WebShellConnection) error {
	if c == nil {
		return nil
	}
	pw, err := secretstore.Decrypt(c.Password)
	if err != nil {
		return fmt.Errorf("解密 WebShell 密碼失敗: %w", err)
	}
	c.Password = pw
	return nil
}
