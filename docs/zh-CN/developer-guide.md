# 開發者指南

本文面向二次開發者，說明專案結構、啟動方式、主要擴充套件點和開發習慣。

## 專案結構

```text
cmd/server/              Web 服務入口
internal/app/            應用組裝、路由註冊、MCP 工具註冊
internal/handler/        HTTP Handler
internal/database/       SQLite 資料訪問
internal/security/       認證、限流、Shell 執行
internal/mcp/            MCP Server、外部 MCP 管理
internal/multiagent/     Eino 單代理、多代理、中介軟體
internal/workflow/       工作流執行時
internal/knowledge/      知識庫索引與檢索
internal/c2/             內建 C2
internal/project/        專案事實黑板
web/static/              前端 JS/CSS/資源
web/templates/           HTML 模板
tools/                   命令工具 YAML
roles/                   角色 YAML
agents/                  多代理 Markdown 定義
skills/                  Agent Skills
docs/                    專案文件
```

## 啟動開發環境

```bash
go run ./cmd/server --config config.yaml
```

前端是靜態頁面，模板在 `web/templates/`，JS/CSS 在 `web/static/`。修改後重新整理瀏覽器即可驗證，多數場景不需要單獨前端構建。

## 路由

路由集中在 `internal/app/app.go` 的 `registerRoutes` 中。新增業務介面通常需要：

1. 在 `internal/handler/` 增加 Handler。
2. 在 `internal/database/` 增加必要的資料訪問。
3. 在 `internal/app/app.go` 構造並註冊路由。
4. 如需對外文件，更新 `internal/handler/openapi.go`。
5. 如需前端呼叫，更新 `web/static/js/`。

## 資料庫

預設 SQLite。新增表或欄位時：

- 將遷移邏輯放到資料庫初始化或對應模組遷移函式。
- 保持向後相容，避免破壞已有 `data/conversations.db`。
- 新增針對遷移和核心查詢的單測。

## 新增工具

命令工具優先透過 `tools/*.yaml` 增加，不必改 Go 程式碼。需要 Go 內建工具時：

- 在合適模組註冊 MCP Tool。
- 定義清晰 `InputSchema`。
- 處理超時、錯誤、審計和 HITL 上下文。
- 避免把高風險操作預設免審批。

工具 YAML 規則見 `tools/README.md`。

## 新增角色

角色透過 `roles/*.yaml` 管理。常見欄位包括名稱、描述、系統提示詞和工具列表。角色應遵循最小工具集原則，不要把所有工具預設交給專用角色。

## 新增子代理

多代理子 Agent 放在 `agents/*.md`。Front matter 示例：

```yaml
---
name: Vulnerability Triage
id: vulnerability-triage
description: 對漏洞線索進行驗證、定級和修復建議整理
tools:
  - nmap
  - nuclei
bind_role: 綜合漏洞掃描
max_iterations: 200
---
```

正文是系統提示詞。主代理可使用固定檔名或 `kind: orchestrator`。

## 新增 Skill

Skill 放在 `skills/<name>/SKILL.md`。用於提供專題能力、流程說明或附屬資料。詳見 [Skills 指南](skills-guide.md)。

## 前端開發

前端程式碼按功能拆分在 `web/static/js/`。新增頁面或模組時：

- 複用現有 `apiFetch`、modal、通知、i18n 工具。
- 同步更新 `web/static/i18n/zh-CN.json` 和 `en-US.json`。
- 避免把敏感 Key 放到前端。
- 高風險按鈕要有確認和清晰狀態反饋。

i18n 規範見 [前端國際化方案](frontend-i18n.md)。

## OpenAPI

`internal/handler/openapi.go` 維護內建 OpenAPI 輸出。新增公開介面後建議同步補：

- path
- method
- summary/description
- requestBody
- responses
- security

這樣 `/api-docs` 才能反映最新介面。

## 開發習慣

- 優先保持現有模組邊界。
- 大模型、外部 API、檔案系統、Shell 相關改動必須考慮超時和錯誤路徑。
- 高風險能力要接入 HITL 或至少有清晰審計。
- 程式碼變更後執行相關包單測。

## 新增業務模組的完整配方

不要只加一個 Handler。完整模組通常要考慮：

1. 資料模型：是否需要 SQLite 表和遷移。
2. Handler：HTTP 引數、錯誤碼、分頁、過濾。
3. Audit：管理動作是否要審計。
4. Monitor：如果會執行長任務，是否要記錄執行狀態。
5. MCP：是否要暴露給 Agent。
6. HITL：MCP 工具是否有審批邊界。
7. OpenAPI：是否更新 `/api/openapi/spec`。
8. Frontend：是否需要 i18n、狀態、空態、錯誤提示。
9. Tests：資料庫、handler、邊界條件。
10. Docs：配置、使用、排錯和安全影響。

少做其中一項，後面通常會以“使用者看不懂”“Agent 調錯”“介面沒人會用”的形式返工。

## Handler 錯誤設計

建議錯誤響應保持：

```json
{
  "error": "machine_readable_code",
  "message": "給使用者看的說明"
}
```

不要只返回 Go error 字串。前端需要穩定欄位，使用者需要可操作建議，日誌需要詳細錯誤。

## 長任務設計

掃描、索引、批次任務、C2 等都可能長時間執行。設計時要回答：

- 是否能取消？
- 是否能查詢進度？
- 失敗後能否重試？
- 結果寫在哪裡？
- 頁面重新整理後狀態是否還在？
- 是否會阻塞 HTTP 請求？

如果答案是否定的，應考慮接入任務表、事件流或監控模組。

## 測試優先順序

最值得補測試的地方：

- 配置熱應用。
- HITL 審批分支。
- Shell 超時和無輸出。
- 外部 MCP 失敗恢復。
- 知識庫索引和檢索後處理。
- WebShell 編碼和系統識別。
- SQLite 遷移相容。

這些地方比普通 getter/setter 更容易出現真實使用者故障。
