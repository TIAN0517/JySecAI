# 設定憑證加密遷移評估

產生日期：2026-10-02

## 結論

技術上可行，但不應直接讓 `internal/config` 呼叫 `internal/database/secret_crypto.go`。資料庫的 `credentialCipher` 是未匯出的 DB 內部實作，金鑰預設綁定 `dbPath + ".key"`，而設定檔有不同的生命週期、備份與啟動順序。

目前程式其實已有更接近需求的 `internal/config/secret_protection.go`：使用 AES-256-GCM、支援 `JYSECAI_CONFIG_KEY`（並相容回退到 `JYSECAI_CREDENTIAL_KEY`），且在 `Load` 時解密。不過它目前只涵蓋 robots 與 external MCP 的 secrets，尚未涵蓋本次 P0 欄位。因此建議擴充既有設定保護層，共用同一個經審閱的底層 AEAD/key-store 元件，而不是把設定內容搬進應用資料庫。

## 建議範圍

後續實作應明確納入：

- `ai.channels.*.api_key`，以及相容欄位 `openai.api_key`
- `mcp.auth_header_value`；`mcp.auth_header` 通常是 header 名稱，不是秘密
- `xss.token`
- `knowledge.embedding.api_key`

對 `${VAR}` / `${VAR:-default}` 參照應維持不加密，讓部署系統以環境變數或 secret manager 注入。空字串也保持空字串。

## 建議設計

1. 把 AES-GCM、key decode、原子建立與父目錄 fsync 抽成不依賴 database/config 的內部套件，讓 DB 與 config 兩邊共用；兩種 ciphertext prefix 與 key domain 仍分開，避免交叉誤解密。
2. 擴充設定保護的 transform，覆蓋上述四類欄位；runtime struct 維持解密後值，持久化副本才轉成 ciphertext。
3. 提供獨立的 `--report`／`--protect-config` 管理命令。預覽只列欄位路徑與狀態，不列值；寫入前建立權限 `0600` 的備份，以同目錄 temporary file、`fsync`、atomic rename、父目錄 `fsync` 寫回。
4. `persistMCPAuth` 必須改走同一持久化路徑；目前它會直接把 `auth_header_value` 寫回 YAML，且使用 `0644`，若先擴充讀取端卻漏掉這條寫入路徑，秘密仍會回到明文。
5. 加密前先完成供應商輪替。加密只能降低靜態檔案再次外洩的風險，不能讓已進入 Git 歷史的 key 恢復安全。

## 相容與回滾

- 讀取端需同時接受明文、環境變數參照與帶版本 prefix 的 ciphertext；明文只為遷移相容，不應再由管理介面寫出。
- 寫入必須冪等：已加密且可驗證的值不得再次包裝。
- 回滾前必須保留相同金鑰；遺失 key 等同永久失去 ciphertext。備份不得含新明文。
- 金鑰輪替應採「舊 key 解密、新 key 重加密、原子替換」；失敗時保留原檔與舊 key，不做部分更新。

## 主要風險

| 風險 | 影響 | 緩解 |
|---|---|---|
| key 與 config 一起備份或一起進版控 | 加密失去意義 | key 放 secret manager／systemd credential；本機 key 檔保持 `0600` 並加入 ignore／pre-commit 阻擋。 |
| key 遺失或部署節點拿到不同 key | 服務無法啟動 | 啟動前驗證、受控備份、明確 key ID、雙 key 輪替流程。 |
| 非原子寫入或斷電 | YAML 損壞或部分欄位更新 | same-directory temp、file fsync、rename、parent fsync。 |
| 只保護部分寫入路徑 | 明文重新出現 | 盤點 `persistMCPAuth`、設定 API、bootstrap 與匯出路徑；集中到單一 persistence API。 |
| runtime／API／日誌洩漏解密值 | 靜態加密仍被繞過 | 敏感 DTO 不輸出 JSON、日誌 redaction、設定 API 只回傳 `configured` 狀態。 |
| 重用同一 key/domain | 一處 compromise 擴大爆炸半徑 | DB 與 config 使用不同 HKDF context 或獨立 key；ciphertext 帶用途與版本。 |

## 上線前驗收

- 明文、ciphertext、環境變數參照三種設定均有 round-trip 測試。
- 四類 P0 欄位都被保護，且 API／日誌／匯出不含值。
- `persistMCPAuth` 不再產生明文或放寬檔案權限。
- 缺 key、錯 key、損壞 ciphertext 都 fail closed，錯誤訊息不含秘密。
- Linux 與 Windows/WSL 的 atomic write、權限降級與父目錄 sync 行為均測試。

本文件是設計與風險評估；依交接約束，本次沒有實作或遷移任何設定值。
