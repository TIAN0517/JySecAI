# WebShell 管理

WebShell 管理用於儲存授權目標的 WebShell 連線，並透過 Web 頁面或 Agent 工具執行命令、檔案操作和上下文分析。

## 基本流程

1. 在 WebShell 頁面新增連線。
2. 填寫名稱、URL、密碼或請求引數。
3. 測試連線。
4. 執行命令或檔案操作。
5. 在對話中選擇 WebShell 連線，讓 AI 基於該連線輔助排查。

連線資料儲存在 SQLite 中。

## 介面

主要 API：

- `GET /api/webshell/connections`
- `POST /api/webshell/connections`
- `PUT /api/webshell/connections/:id`
- `DELETE /api/webshell/connections/:id`
- `GET /api/webshell/connections/:id/state`
- `PUT /api/webshell/connections/:id/state`
- `POST /api/webshell/exec`
- `POST /api/webshell/file`
- `GET /api/webshell/connections/:id/ai-history`
- `GET /api/webshell/connections/:id/ai-conversations`

## MCP 工具

系統會註冊 WebShell MCP 工具，例如：

- `webshell_exec`：在連線上執行命令。
- `webshell_file_list`：列目錄。
- `webshell_file_read`：讀取檔案。
- `webshell_file_write`：寫檔案。
- WebShell 連線管理工具。

Agent 使用這些工具時需要 `connection_id`。前端通常會把當前選中的連線注入上下文。

## 命令執行

執行命令前確認：

- 當前連線屬於授權目標。
- 命令不會破壞業務。
- 輸出中可能包含敏感資訊。
- 長命令和互動式命令不適合 WebShell 通道。

建議先執行只讀命令確認環境：

```bash
whoami
pwd
uname -a
id
```

Windows 目標可用：

```cmd
whoami
cd
ver
ipconfig
```

## 檔案操作

檔案操作包括列目錄、讀取、寫入。建議：

- 寫入前先備份原檔案。
- 不在生產目標寫入未經確認的指令碼或二進位制。
- 大檔案優先透過專用下載/上傳通道處理。
- 注意目標編碼和換行符。

## AI 輔助

AI 可以幫助：

- 識別作業系統和當前許可權。
- 規劃只讀列舉步驟。
- 分析命令輸出。
- 彙總風險和修復建議。

不建議讓 AI 自動執行：

- 刪除檔案。
- 修改業務配置。
- 持久化。
- 憑證抓取。
- 大範圍掃描內網。

這些操作應由人工確認，並配合 HITL。

## 安全建議

- 僅儲存授權目標連線。
- 給連線命名時包含專案、環境、目標。
- 演練結束後刪除連線。
- 不把 WebShell 寫入工具加入全域性免審批白名單。
- 重要輸出及時納入專案事實或報告，隨後清理敏感原始資料。

## 排錯

連線失敗：

- URL 不可達。
- 引數名或密碼錯誤。
- 目標 WAF 攔截。
- 代理或 TLS 配置異常。

命令亂碼：

- 檢查目標系統編碼。
- 嘗試切換命令輸出編碼或使用 base64 包裝。

AI 找不到連線：

- 確認前端已選中 WebShell 連線。
- 確認連線未被刪除。
- 檢查 `connection_id` 是否正確。

## 操作分層

WebShell 操作建議分成四層，不同層級使用不同審批策略：

| 層級 | 操作 | 風險 | 建議 |
| --- | --- | --- | --- |
| 識別 | `whoami`、`pwd`、系統版本 | 低 | 可自動 |
| 列舉 | 目錄、程序、環境變數 | 中 | 限定路徑和命令 |
| 讀取 | 配置、日誌、原始碼 | 中高 | 人工確認敏感性 |
| 寫入/執行 | 寫檔案、執行指令碼、刪除 | 高 | 人工審批，說明回滾 |

不要把“WebShell 已經拿到了”理解成“後續操作都低風險”。WebShell 通常位於業務系統內部，誤操作成本很高。

## 連線命名規範

建議命名：

```text
<專案>-<環境>-<目標>-<許可權>-<日期>
```

示例：

```text
acme-staging-web01-www-20260707
```

糟糕命名：

```text
test
shell1
客戶機器
```

AI 和人類審批都依賴上下文，連線名稱含糊會直接放大誤操作機率。

## AI 使用約束模板

給 WebShell 相關角色加一段約束：

```text
使用 WebShell 前先確認 connection_id、目標名稱、當前目錄和許可權。預設只執行只讀命令。任何寫入、刪除、上傳、許可權修改、持久化、憑證讀取、內網探測都必須先給出目的、影響和回滾方式，並等待審批。
```

## 原始碼錨點

- Handler：`internal/handler/webshell.go`
- 連線上下文：`internal/handler/webshell_context.go`
- 探測邏輯：`internal/handler/webshell_probe.go`
- OS/編碼處理測試：`internal/handler/webshell_os_test.go`、`internal/handler/webshell_encoding_test.go`
- MCP 工具註冊：`internal/app/app.go` 中 `registerWebshellTools`
