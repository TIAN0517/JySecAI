# 測試指南

JySecAI 的測試包括 Go 單測、配置驗證、API 手測、MCP 工具驗證和前端冒煙測試。

## Go 單測

執行全部內部測試：

```bash
go test ./internal/...
```

執行指定包：

```bash
go test ./internal/workflow
go test ./internal/multiagent
go test ./internal/handler
```

常見重點包：

- `internal/security`
- `internal/mcp`
- `internal/multiagent`
- `internal/workflow`
- `internal/knowledge`
- `internal/project`
- `internal/handler`
- `internal/c2`

## 構建測試

```bash
go build -o jysecai ./cmd/server
```

構建透過不代表功能正確，但能發現入口、依賴和靜態型別問題。

## 配置驗證

啟動前檢查：

- YAML 縮排。
- 模型配置。
- 資料庫路徑可寫。
- `tools_dir`、`roles_dir`、`skills_dir`、`agents_dir` 是否存在。
- HTTPS 證書路徑是否正確。

啟動後在 Web 設定頁測試：

- OpenAI 相容模型。
- 視覺模型。
- 工具列表。
- 外部 MCP 狀態。

## API 手測

訪問：

```text
/api-docs
```

重點驗證：

- 登入。
- `/api/eino-agent/stream`。
- `/api/config`。
- `/api/config/tools`。
- `/api/knowledge/search`。
- `/api/monitor`。

流式介面經過反向代理時要驗證輸出是否實時。

## 工具測試

新增或修改 `tools/*.yaml` 後：

- 在工具列表中確認 schema。
- 用低風險引數執行。
- 檢查錯誤輸出是否可讀。
- 檢查超時是否生效。
- 檢查 HITL 是否按預期攔截。

不要用生產目標測試新工具。

## MCP 測試

外部 MCP：

- stdio：先在終端獨立執行命令。
- HTTP/SSE：用 curl 檢查連通性。
- Web 頁面啟動後檢查 `/api/external-mcp/stats`。
- 在對話中確認工具是否可被 `tool_search` 找到。

## 知識庫測試

步驟：

1. 放入小型 Markdown 文件。
2. 掃描知識庫。
3. 重建索引。
4. 搜尋文件中的關鍵詞和同義表達。
5. 檢視檢索日誌。

如果使用真實 embedding API，注意配額和速率限制。

## 前端冒煙

修改前端後至少驗證：

- 登入和退出。
- 側邊欄對話列表。
- 新建對話和流式回覆。
- 設定頁面儲存。
- 相關業務頁面增刪改查。
- 中英文切換。
- 瀏覽器控制檯無明顯錯誤。

## 高風險模組測試

C2、WebShell、終端、批次任務只能在授權測試環境驗證。測試前確認：

- 目標是本機、靶機或演練環境。
- 命令無破壞性。
- HITL 策略符合預期。
- 測試後清理會話、payload、上傳檔案和任務結果。

## 測試金字塔

建議測試分層：

| 層級 | 目標 | 示例 |
| --- | --- | --- |
| 單元測試 | 純邏輯正確 | 表示式、chunk、脫敏、超時格式 |
| Handler 測試 | HTTP 行為 | 引數校驗、狀態碼、許可權 |
| 整合測試 | 多模組協作 | 外部 MCP、知識庫索引、HITL |
| 冒煙測試 | 使用者路徑可用 | 登入、對話、工具、設定 |
| 授權靶場測試 | 高風險能力安全 | C2、WebShell、終端 |

不要用端到端手測代替單元測試，也不要用單元測試代替高風險靶場驗證。

## 迴歸測試重點

修改這些模組時必須擴大測試範圍：

- `internal/handler/config.go`：測模型、知識庫、MCP、C2、機器人配置應用。
- `internal/multiagent/`：測流式、工具呼叫、摘要、重試、HITL。
- `internal/security/`：測認證、Shell、超時、無輸出。
- `internal/database/`：測舊資料相容。
- `web/static/js/chat.js`：測對話、過程詳情、攻擊鏈、分組。

## 測試資料管理

不要用真實客戶資料做測試。建議準備：

- 小型 Markdown 知識庫樣例。
- 本地假 MCP Server。
- 本地可控 HTTP 目標。
- 無害 WebShell 模擬端。
- 臨時 SQLite 資料庫。

測試完成後刪除臨時資料庫和上傳檔案，避免汙染開發環境。

## 失敗用例比成功用例更重要

至少覆蓋：

- 模型 API 401/429/500。
- MCP 程序啟動失敗。
- 工具超時。
- HITL 拒絕。
- 知識庫索引中斷。
- 資料庫不可寫。
- WebShell 目標返回非 200。
- C2 關閉時訪問介面。

這些才是使用者真實會遇到的問題。

## 原始碼錨點

已有測試集中在：

- `internal/handler/*_test.go`
- `internal/multiagent/*_test.go`
- `internal/workflow/*_test.go`
- `internal/knowledge/*_test.go`
- `internal/security/*_test.go`
- `internal/mcp/*_test.go`
- `internal/c2/*_test.go`
