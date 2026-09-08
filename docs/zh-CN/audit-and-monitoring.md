# 審計與監控

JySecAI 有兩類常用可觀測資料：平臺操作審計和工具執行監控。二者用途不同，建議同時開啟。

## 平臺審計

配置：

```yaml
audit:
  enabled: true
  retention_days: 15
  max_detail_bytes: 8192
  auth_failure_cooldown_seconds: 60
```

審計記錄覆蓋登入、配置、資源管理等平臺操作。它不會完整記錄對話正文，也不逐條記錄所有工具呼叫正文。

介面：

- `GET /api/audit/meta`
- `GET /api/audit/summary`
- `GET /api/audit/logs`
- `GET /api/audit/logs/:id`
- `GET /api/audit/logs/export`

建議關注：

- 登入失敗和異常來源 IP。
- 密碼修改。
- 配置修改。
- 外部 MCP 增刪改。
- C2/WebShell/知識庫等高風險資源操作。

## 工具執行監控

配置：

```yaml
monitor:
  retention_days: 90
```

工具執行監控用於檢視 MCP 工具呼叫、命令狀態、耗時、取消和結果摘要。

介面：

- `GET /api/monitor`
- `GET /api/monitor/execution/:id`
- `POST /api/monitor/execution/:id/cancel`
- `DELETE /api/monitor/execution/:id`
- `DELETE /api/monitor/executions`
- `GET /api/monitor/stats`
- `GET /api/monitor/calls-timeline`
- `POST /api/monitor/executions/names`

## 通知摘要

介面：

- `GET /api/notifications/summary`
- `POST /api/notifications/read`

通知用於提示待處理事項、未讀狀態或執行中任務概況。具體展示取決於前端頁面。

## HITL 日誌

HITL 決策日誌獨立管理：

- `GET /api/hitl/pending`
- `GET /api/hitl/logs`
- `GET /api/hitl/logs/:id`
- `DELETE /api/hitl/logs`
- `POST /api/hitl/decision`
- `POST /api/hitl/dismiss`

建議將 HITL 日誌與平臺審計結合，用於覆盤 Agent 為什麼執行或沒有執行某個工具。

## 保留策略

建議：

- 審計日誌保留 15 到 90 天，按組織要求調整。
- 工具執行記錄保留 30 到 180 天。
- C2、WebShell、上傳附件和任務結果按專案週期單獨清理。
- 匯出日誌時注意脫敏和訪問許可權。

## 運維巡檢

每週檢查：

- 是否有異常登入失敗。
- 是否有未授權配置變更。
- 長時間執行或失敗率高的工具。
- 外部 MCP 連線狀態。
- 資料庫檔案大小和磁碟空間。

每次演練結束：

- 匯出必要審計證據。
- 刪除無用 WebShell/C2 會話和 payload。
- 清理上傳附件和臨時工作區。
- 歸檔報告、漏洞和專案事實。

## 審計和監控的邊界

兩者經常被混用，但語義不同：

- 審計回答“誰在平臺上做了什麼管理動作”。
- 監控回答“工具呼叫執行得怎麼樣”。
- HITL 日誌回答“某個工具呼叫為什麼被放行、修改或拒絕”。
- 對話過程詳情回答“Agent 當時如何推理和串聯步驟”。

一次安全覆盤通常要把四類資訊合在一起看。只看審計，會漏掉具體工具輸出；只看監控，會漏掉誰修改了配置。

## 關鍵事件解釋

建議重點關注這些事件型別：

| 事件 | 為什麼重要 |
| --- | --- |
| 登入失敗 | 暴力嘗試、密碼洩露或誤配置 |
| 修改密碼 | 所有舊 session 會被撤銷，可能影響正在使用的人 |
| 更新配置 | 可能改變模型、工具、C2、知識庫、審計策略 |
| 外部 MCP 變更 | 新工具可能擁有本機或遠端執行能力 |
| C2 listener/task | 直接影響授權目標和網路暴露面 |
| WebShell 連線變更 | 可能引入真實業務系統執行通道 |
| HITL 拒絕 | 說明 Agent 或使用者請求觸達風險邊界 |

## 日誌保留不是越久越好

安全工具日誌往往包含目標、漏洞、路徑、命令輸出和組織內部資訊。保留時間應平衡覆盤價值與洩露風險：

- 短期演練：15-30 天。
- 持續紅隊平臺：90-180 天。
- 合規要求：按組織規範歸檔，但匯出後應加密。

如果沒有專門日誌平臺，不要無限期保留 SQLite 中的所有明細。

## 原始碼錨點

- 審計服務：`internal/audit/service.go`
- 審計脫敏：`internal/audit/sanitize.go`
- 審計保留：`internal/audit/retention.go`
- 審計介面：`internal/handler/audit.go`
- 監控 reconcile：`internal/monitor/reconcile.go`
- 監控介面：`internal/handler/monitor.go`
- HITL 日誌：`internal/handler/hitl_logs.go`
