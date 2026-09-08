# 排錯指南

本文按現象列出常見問題。優先檢視服務日誌、瀏覽器控制檯和 `/api-docs` 中的介面響應。

## 無法訪問頁面

檢查：

- 服務是否啟動。
- 埠是否被佔用。
- 配置中是否啟用 HTTPS。
- 訪問協議是否正確。

預設配置常見地址：

```text
https://127.0.0.1:6688/
```

如果使用自簽證書，瀏覽器會提示不受信任，需要手動繼續訪問。

## 登入失敗

檢查：

- RBAC 使用者密碼是否正確（預設 `admin`；首次啟動密碼見控制檯輸出）。
- 是否修改密碼後舊會話已失效，需重新登入。
- 瀏覽器 Cookie 是否異常，可嘗試無痕視窗。
- 審計日誌中是否有登入失敗節流。

### 忘記 `admin` 密碼

如果仍有其他具備 `rbac:write` 許可權的管理員賬號，優先在 **平臺許可權 → 使用者管理** 中重置密碼。

如果沒有可用的管理員會話，可在伺服器上緊急重置內建 `admin` 賬號。在專案根目錄執行：

```bash
./run.sh --reset-admin-password
```

按提示輸入並確認新密碼。指令碼會隱藏輸入並寫入 bcrypt 雜湊。如果服務正在執行，完成後重新啟動服務，使原有登入會話失效。

如果無法使用 `run.sh`，也可以手動執行以下命令，按提示輸入並確認新密碼：

```bash
HASH=$(htpasswd -nBC 10 '' | cut -d: -f2 | tr -d '\n') && sqlite3 data/conversations.db "UPDATE rbac_users SET password_hash='$HASH', updated_at=CURRENT_TIMESTAMP WHERE id='admin' AND username='admin' AND is_builtin=1; SELECT changes();"
```

輸出 `1` 表示修改成功。該命令需要 `sqlite3` 和 `htpasswd`；如果 `config.yaml` 中的 `database.path` 不是預設值，請替換 `data/conversations.db`。密碼輸入不會顯示，也不會寫入 Shell 歷史。

## 模型無響應

檢查：

- 當前對話選擇的 AI 通道是否存在；為空時會使用 `ai.default_channel`。
- `ai.channels.<id>.base_url` 是否包含正確路徑，如 `/v1`。
- `ai.channels.<id>.api_key` 是否有效。
- `ai.channels.<id>.model` 是否存在。
- 服務商是否支援當前通道的 `reasoning` 欄位。

可在系統設定中使用模型測試。若閘道器報 400，先嚐試：

```yaml
ai:
  channels:
    your-channel:
      reasoning:
        mode: off
```

## 流式輸出中斷

常見原因：

- 反向代理緩衝 SSE。
- 模型閘道器超時。
- 瀏覽器網路斷開。
- 上下文過大。

Nginx 需要：

```nginx
proxy_buffering off;
proxy_http_version 1.1;
```

## 工具執行失敗

檢查：

- 工具命令是否已安裝到 PATH。
- `tools/*.yaml` 引數 schema 是否正確。
- 是否被 HITL 拒絕。
- 是否超過 `agent.tool_timeout_minutes`。
- Shell 長時間無輸出是否觸發 `shell_no_output_timeout_seconds`。

工具配置可參考 `tools/README.md`。

## MCP 連不上

內建 MCP：

- 檢查 `mcp.enabled`。
- 檢查 `mcp.port`。
- 檢查 `auth_header` 和 `auth_header_value`。

外部 MCP：

- stdio：檢查命令路徑、工作目錄、環境變數。
- HTTP/SSE：檢查 URL、認證、網路連通性。
- 檢視 `/api/external-mcp/stats`。

## 知識庫不可用

檢查：

- `knowledge.enabled: true`。
- embedding 配置是否正確。
- 是否已經掃描並重建索引。
- `data/knowledge.db` 是否可寫。
- 嵌入服務是否 429 或超時。

如果索引大量失敗，降低：

```yaml
knowledge:
  indexing:
    batch_size: 5
    rate_limit_delay_ms: 600
```

## 機器人沒有回覆

檢查：

- 對應平臺 `robots.<platform>.enabled`。
- 平臺回撥 URL 是否指向 `/api/robot/...`。
- Token、secret、verify_token 是否一致。
- 伺服器是否可被平臺訪問。
- 群聊是否需要 @ 機器人。

詳細步驟見 [機器人使用說明](robot.md)。

## C2 監聽器啟動失敗

檢查：

- `c2.enabled`。
- 埠是否被佔用。
- 防火牆或安全組。
- 是否需要管理員許可權繫結低埠。

關閉 C2 後 `/api/c2/*` 返回 503 是預期行為。

## WebShell 命令亂碼

處理：

- 確認目標系統編碼。
- 嘗試更短命令。
- 使用 base64 包裝輸出。
- Windows 目標檢查內碼表。

## 資料庫鎖或寫入失敗

檢查：

- `data/` 是否可寫。
- 是否多個例項共用同一個 SQLite 檔案。
- 磁碟是否滿。
- 是否異常複製了 WAL/SHM 檔案。

生產環境不要讓多個程序同時寫同一份 SQLite 資料庫。

## 前端頁面異常

檢查：

- 瀏覽器控制檯錯誤。
- 靜態資源是否載入成功。
- 修改前端後是否重新整理快取。
- i18n key 是否缺失。

介面異常時開啟 `/api-docs` 對照請求體。

## 診斷順序

遇到問題時不要直接改配置，先定位層級：

1. 程序：服務是否還在，日誌是否有 panic。
2. 網路：埠、HTTPS、反向代理、瀏覽器控制檯。
3. 認證：`/api/auth/validate` 是否 200。
4. 配置：`/api/config` 是否能讀，應用後是否報錯。
5. 模型：模型測試是否透過。
6. 工具：工具列表和單個 schema 是否正常。
7. 資料庫：`data/` 是否可寫，有無鎖。
8. 業務模組：知識庫、MCP、C2、WebShell 分別測最小動作。

先定位層級，再改引數。否則容易把一個代理問題誤判成模型問題。

## 最小診斷命令

```bash
# 程序和埠
lsof -i :8080

# 本機 HTTPS 是否通
curl -k -I https://127.0.0.1:6688/

# 靜態資源是否通
curl -k -I https://127.0.0.1:6688/static/logo.png

# 檢視資料庫檔案
ls -lh data/
```

如果經過 Nginx，再分別測代理地址和回源地址，確認問題在哪一層。

## 常見誤判

- “模型壞了”：實際是 HITL 掛起等待審批。
- “工具沒載入”：實際是 tool_search 隱藏了大部分工具。
- “知識庫沒效果”：實際是索引沒重建或 risk_type 過濾過窄。
- “C2 介面壞了”：實際是 `c2.enabled: false`，返回 503 是正常保護。
- “配置儲存了但沒生效”：實際是監聽埠/TLS 需要重啟。
- “機器人不回覆”：實際是平臺側沒有正確配置回撥 URL 或驗籤引數。

## 故障報告模板

提交問題時建議附：

```text
版本/提交：
啟動方式：
訪問方式：http/https/反向代理：
相關配置段：
復現步驟：
預期結果：
實際結果：
服務端日誌：
瀏覽器控制檯：
相關介面響應：
```

有了這些資訊，定位速度通常會快很多。
