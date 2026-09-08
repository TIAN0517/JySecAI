# API 參考

JySecAI 內建 OpenAPI 規格和 API 文件頁面。啟動服務後訪問：

```text
/api-docs
```

OpenAPI JSON：

```text
GET /api/openapi/spec
```

`/api/openapi/spec` 需要登入認證，避免未授權使用者直接列舉介面結構。

## 認證

登入：

```http
POST /api/auth/login
Content-Type: application/json

{"password":"your-password"}
```

認證成功後，前端通常使用 Cookie 會話。外部客戶端也可參考 OpenAPI 中的 Bearer Token 描述，按實際返回欄位接入。

常用認證介面：

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/change-password`
- `GET /api/auth/validate`

## 對話與 Agent

單代理：

- `POST /api/eino-agent`
- `POST /api/eino-agent/stream`

多代理：

- `POST /api/multi-agent`
- `POST /api/multi-agent/stream`

多代理請求體透過 `orchestration` 指定：

- `deep`
- `plan_execute`
- `supervisor`

常用請求體欄位：

| 欄位 | 說明 |
| --- | --- |
| `message` | 使用者訊息，必填。 |
| `conversationId` | 繼續已有對話；為空時建立新對話。 |
| `projectId` | 新對話繫結專案；為空時可跟隨 `config.project.default_project_id`。 |
| `role` | 使用指定角色。 |
| `aiChannelId` | 選擇 `ai.channels` 中的通道 ID；為空時使用 `ai.default_channel`。 |
| `reasoning` | 會話級推理覆蓋，受通道 `reasoning.allow_client_reasoning` 控制。 |
| `hitl` | 會話級人機協同配置。 |

對話管理：

- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/:id`
- `PUT /api/conversations/:id`
- `DELETE /api/conversations/:id`
- `POST /api/conversations/:id/delete-turn`
- `GET /api/messages/:id/process-details`

## 檔案管理來源

檔案管理頁面和 `/api/chat-uploads` 列表介面會把對話相關檔案按來源歸類。底層目錄仍使用專案 ID 或會話 ID 保持穩定，介面會優先顯示專案名或對話標題，完整 ID 可在提示或路徑中檢視。

| 來源 | `source` | 典型目錄 | 說明 | 可變更性 |
| --- | --- | --- | --- | --- |
| 工作目錄 | `workspace` | `tmp/workspace/projects/<projectId>/...`、`tmp/workspace/conversations/<conversationId>/...` | Agent 執行任務時儲存下載檔案、分析指令碼、中間結果和生成的 CSV/XLSX/Markdown 等。使用者反饋“AI 生成的檔案找不到”時，通常先看這裡。 | 只讀展示；支援複製路徑、下載、匯出。 |
| 會話產物 | `conversation_artifact` | `data/conversation_artifacts/<conversationId>/...` | 系統按會話歸檔的交付物或會話級產物，例如總結、報告、模型中介軟體生成的歸檔內容。 | 只讀展示；支援複製路徑、下載、匯出。 |
| 工具輸出 | `reduction` | `tmp/reduction/projects/<projectId>/...`、`tmp/reduction/conversations/<conversationId>/...` | 超長工具輸出、掃描原文或被截斷前落盤的結果快取。適合回看完整工具輸出。 | 只讀展示；支援複製路徑、下載、匯出。 |
| 對話附件 | `upload` | `chat_uploads/<date>/<conversationId>/...` | 使用者在對話或檔案管理頁手動上傳的附件。需要讓 AI 引用某檔案時，可複製伺服器絕對路徑貼上到對話中。 | 可上傳、新建目錄、編輯文字檔案、重新命名、刪除、複製路徑、下載、匯出。 |

相關介面：

- `GET /api/chat-uploads`：按來源、專案、會話、檔名篩選檔案。
- `GET /api/chat-uploads/path`：把檔案管理中的相對路徑或內部虛擬路徑解析為伺服器絕對路徑，用於複製檔案或目錄路徑。
- `GET /api/chat-uploads/download`：下載指定檔案。
- `GET /api/chat-uploads/export`：匯出當前篩選結果為 ZIP。
- `POST /api/chat-uploads`：上傳到對話附件目錄。

## 專案、漏洞、攻擊鏈

專案：

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/:id`
- `PUT /api/projects/:id`
- `DELETE /api/projects/:id`
- `GET /api/projects/:id/facts`
- `POST /api/projects/:id/facts`
- `GET /api/projects/:id/fact-graph`

漏洞：

- `GET /api/vulnerabilities`
- `POST /api/vulnerabilities`
- `GET /api/vulnerabilities/:id`
- `PUT /api/vulnerabilities/:id`
- `DELETE /api/vulnerabilities/:id`
- `GET /api/vulnerabilities/export`

攻擊鏈：

- `GET /api/attack-chain/:conversationId`
- `POST /api/attack-chain/:conversationId/regenerate`

## 資產管理與批次匯入

資產介面：

- `GET /api/assets`：分頁查詢資產；
- `GET /api/assets/selection`：按當前篩選條件解析跨頁選擇，最多返回 10000 條；
- `GET /api/assets/stats`：獲取資產統計，`days` 僅支援 `7`、`30` 或 `90`；
- `POST /api/assets/import`：新增或去重更新資產，單次最多 100000 條；
- `POST /api/assets/scan-links`：批次記錄掃描關聯，單次最多 10000 條；
- `PUT /api/assets/bulk`：原子批次更新最多 10000 個資產；
- `PUT /api/assets/project-binding`：批次繫結專案，單次最多 10000 個資產 ID；
- `POST /api/assets/batch-delete`：原子批次刪除最多 10000 個資產；
- `POST /api/assets/merge`：合併 2-100 個具有共同身份的重複資產；
- `PUT /api/assets/:id`：更新資產；
- `DELETE /api/assets/:id`：刪除資產。

`GET /api/assets` 和 `GET /api/assets/selection` 使用相同的篩選與排序引數；`selection` 會忽略分頁引數並返回全部匹配項（最多 10000 條）：

| 類別 | 引數 |
| --- | --- |
| 分頁（僅列表） | `page`、`page_size`（最大 100） |
| 常用 | `q`、`status`、`project_id`、`risk_level`、`min_vulnerabilities`、`max_vulnerabilities` |
| 目標與來源 | `host`、`ip`、`domain`、`port`、`protocol`、`source`、`tag` |
| 責任與業務 | `responsible_person`、`department`、`business_system`、`environment`、`criticality` |
| 地理 | `country`、`province`、`city` |
| 掃描 | `scan_state=never|scanned`、`scan_overdue_days`、`last_scan_before`、`last_scan_after` |
| 發現時間 | `first_seen_before`、`first_seen_after`、`last_seen_before`、`last_seen_after` |
| 排序 | `sort_by`、`sort_order=asc|desc` |

時間引數接受 RFC3339 或 `YYYY-MM-DD`。`sort_by` 支援 `last_seen_at`、`last_scan_at`、`first_seen_at`、`created_at`、`updated_at`、`host`、`port`、`risk_level` 和 `vulnerability_count`。

`POST /api/assets/import` 接收 JSON，而不是 XLSX/CSV 檔案。Web 端會在瀏覽器中解析模板、預覽並轉換為該請求格式：

```http
POST /api/assets/import
Authorization: Bearer <token>
Content-Type: application/json

{
  "source": "manual-import",
  "source_query": "asset-import-2026-07.xlsx",
  "assets": [
    {
      "host": "https://app.example.com:443",
      "domain": "app.example.com",
      "port": 443,
      "protocol": "https",
      "title": "Example App",
      "server": "nginx",
      "project_id": "<project-id>",
      "responsible_person": "Alice",
      "department": "Security",
      "business_system": "Customer Portal",
      "environment": "production",
      "criticality": "critical",
      "tags": ["production", "internet"],
      "status": "active"
    },
    {
      "ip": "192.0.2.10",
      "port": 22,
      "protocol": "ssh",
      "status": "active"
    }
  ]
}
```

請求規則：

- `assets` 必須包含 `1-100000` 條；
- 每條資產的 `host`、`ip`、`domain` 至少一項非空；
- `port` 範圍為 `0-65535`；
- `status` 僅支援 `active` 或 `inactive`；
- `environment` 支援空值或 `production`、`staging`、`testing`、`development`、`other`；
- `criticality` 支援空值或 `critical`、`high`、`medium`、`low`；
- 標籤最多 30 個，單個最多 64 個字元；
- `project_id` 非空時，呼叫者必須有權訪問該專案；
- 需要 `asset:write` 許可權；
- 服務端按“目標 + 埠 + 協議”去重，並在同一事務中處理本次請求。

成功響應：

```json
{
  "created": 120,
  "updated": 8,
  "skipped": 2
}
```

- `created`：新建數量；
- `updated`：命中去重鍵併合並更新的數量；
- `skipped`：空記錄或因資源歸屬不可更新而跳過的數量。

欄位校驗失敗返回 `400`，且響應 `error` 會包含出錯資產的順序。專案無權訪問返回 `403`。批次匯入的模板欄位和 UI 操作見[資產管理指南](asset-management.md#從表格批次匯入)。

批次編輯示例：

```http
PUT /api/assets/bulk
Content-Type: application/json

{
  "asset_ids": ["<asset-id-1>", "<asset-id-2>"],
  "responsible_person": "Alice",
  "department": "Security",
  "environment": "production",
  "criticality": "high",
  "add_tags": ["internet-facing"],
  "remove_tags": ["untriaged"]
}
```

批次欄位均為可選；未提供的欄位保持原值。`add_tags` 和 `remove_tags` 會在事務內去重處理。批次編輯、專案繫結和批次刪除會先驗證全部資產的可訪問性，任一 ID 不存在或無權訪問時整批失敗。

重複資產合併示例：

```http
POST /api/assets/merge
Content-Type: application/json

{
  "asset_ids": ["<primary-id>", "<duplicate-id>"],
  "primary_id": "<primary-id>"
}
```

每個待刪除記錄必須與主資產共享域名、IP 或 Host。主資產已有欄位優先，空欄位從其他記錄補齊，標籤取並集；呼叫者需要更新主資產和刪除其餘資產的許可權。

## 工具、MCP、配置

配置：

- `GET /api/config`
- `PUT /api/config`
- `POST /api/config/apply`
- `GET /api/config/tools`
- `GET /api/config/tools/:name/schema`
- `POST /api/config/test-openai`
- `POST /api/config/test-vision`
- `POST /api/config/list-models`

MCP：

- `POST /api/mcp`
- `GET /api/external-mcp`
- `PUT /api/external-mcp/:name`
- `POST /api/external-mcp/:name/start`
- `POST /api/external-mcp/:name/stop`
- `DELETE /api/external-mcp/:name`

## 知識庫、Skills、角色、Agent

知識庫：

- `GET /api/knowledge/categories`
- `GET /api/knowledge/items`
- `POST /api/knowledge/scan`
- `POST /api/knowledge/index`
- `POST /api/knowledge/search`

角色：

- `GET /api/roles`
- `POST /api/roles`
- `GET /api/roles/:name`
- `PUT /api/roles/:name`
- `DELETE /api/roles/:name`

Skills：

- `GET /api/skills`
- `POST /api/skills`
- `GET /api/skills/:name`
- `PUT /api/skills/:name`
- `DELETE /api/skills/:name`
- `GET /api/skills/:name/files`
- `GET /api/skills/:name/file`
- `PUT /api/skills/:name/file`

Markdown 子代理：

- `GET /api/multi-agent/markdown-agents`
- `POST /api/multi-agent/markdown-agents`
- `GET /api/multi-agent/markdown-agents/:filename`
- `PUT /api/multi-agent/markdown-agents/:filename`
- `DELETE /api/multi-agent/markdown-agents/:filename`

## 高風險能力

WebShell：

- `GET /api/webshell/connections`
- `POST /api/webshell/connections`
- `POST /api/webshell/exec`
- `POST /api/webshell/file`

C2：

- `GET /api/c2/listeners`
- `POST /api/c2/listeners`
- `GET /api/c2/sessions`
- `POST /api/c2/tasks`
- `POST /api/c2/payloads/build`

終端：

- `POST /api/terminal/run`
- `POST /api/terminal/run/stream`
- `GET /api/terminal/ws`

這些介面應只開放給可信管理員，並配合 HTTPS、強密碼、網路隔離和審計。

## 呼叫建議

- 優先使用 `/api-docs` 檢視完整引數和響應結構。
- 流式介面使用 SSE，反向代理需關閉緩衝。
- 所有修改類介面都應處理 401、403、404、409、500。
- 外部整合建議建立最小許可權網路路徑，不要把 Web 管理面直接暴露到公網。

## 認證細節

認證中介軟體會按順序提取 token：

1. `Authorization: Bearer <token>`
2. `Authorization: <token>`
3. 查詢引數 `?token=<token>`
4. Cookie `auth_token`

這意味著外部指令碼最穩妥的方式是使用 `Authorization: Bearer`。查詢引數雖然支援，但容易進入代理日誌，不建議生產使用。

## SSE 客戶端注意事項

`/api/eino-agent/stream` 和 `/api/multi-agent/stream` 是長連線。客戶端應處理：

- 網路中斷後不要盲目重放破壞性請求。
- 收到 `error` 事件後讀取錯誤正文。
- 收到 `done` 才視為本輪結束。
- 代理層不能緩衝。
- 請求體中的 `conversationId` 決定是否接續已有對話。

## API 穩定性分層

| API 型別 | 穩定性 | 整合建議 |
| --- | --- | --- |
| `/api/auth/*` | 高 | 可直接整合 |
| `/api/eino-agent*` | 高 | 推薦外部對話入口 |
| `/api/openapi/spec` | 高 | 用於生成客戶端 |
| `/api/assets/*` | 高 | 資產管理與批次匯入 |
| `/api/config*` | 中 | 管理工具使用，謹慎自動化 |
| `/api/c2/*`、`/api/webshell/*` | 中 | 高風險，必須加許可權邊界 |
| 前端私有呼叫細節 | 低 | 不建議外掛依賴 |

## Curl 示例

登入並提取 token 的返回欄位可能隨實現調整，建議先看 `/api-docs`。如果已有 token：

```bash
curl -k https://127.0.0.1:6688/api/conversations \
  -H "Authorization: Bearer <token>"
```

傳送非流式單代理請求：

```bash
curl -k https://127.0.0.1:6688/api/eino-agent \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"對 127.0.0.1 做授權的基礎資訊收集，先不要執行高風險操作"}'
```

## 原始碼錨點

- 路由：`internal/app/app.go`
- 認證：`internal/security/auth_middleware.go`
- OpenAPI：`internal/handler/openapi.go`
- 單代理：`internal/handler/eino_single_agent.go`
- 多代理：`internal/handler/multi_agent.go`
- 資產介面：`internal/handler/asset.go`
- 資產儲存與去重：`internal/database/asset.go`
