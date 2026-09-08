# 人機協同（HITL）最佳實踐

[English](../en-US/hitl-best-practices.md)

人機協同用於在 Agent 執行工具前做審批攔截。它適合控制高風險操作、保留審計痕跡，並在人工審計壓力過大時讓審計 Agent 接管常規審批。

## 配置入口

Web 端進入 **系統設定 → 人機協同**，可配置：

- 全域性預設審批方：`human` 或 `audit_agent`
- 審計 Agent 專用模型：`hitl.audit_model`
- 已決策審計日誌保留天數
- 免審批工具白名單：`hitl.tool_whitelist`
- 審批模式與審查編輯模式的審計提示詞

對應的 `config.yaml` 示例：

```yaml
hitl:
  default_reviewer: human
  audit_model:
    provider: ""
    base_url: ""
    api_key: ""
    model: "" # 可填小模型；留空複用預設 AI 通道的模型
  retention_days: 90
  tool_whitelist: [read_file, ls, glob, grep, tool_search, get_project_fact, list_project_facts, search_project_facts, list_vulnerabilities, get_vulnerability, get_asset, query_assets, list_knowledge_risk_types, get_tool_execution, wait_tool_execution, batch_task_list, batch_task_get, manage_webshell_list, c2_event, c2_file]
```

`audit_model` 的欄位可以只填一部分。空欄位會自動繼承預設 AI 通道解析後的模型配置，因此常見做法是隻填 `model`，讓審計 Agent 使用更便宜的小模型。

## 推薦審批策略

### 1. 預設人工，逐步放權

剛開始建議：

- `default_reviewer: human`
- 僅把明顯只讀工具加入 `tool_whitelist`
- 對寫檔案、執行命令、C2 任務、WebShell 操作保持人工審批

執行一段時間後，觀察審計日誌，把重複、低風險、誤報少的工具加入白名單。

### 2. 人工審不過來時，用小模型接管常規審批

當待審批積壓明顯時，可以切換為：

```yaml
hitl:
  default_reviewer: audit_agent
  audit_model:
    model: "your-small-reviewer-model"
```

建議讓小模型處理：

- 只讀查詢
- 資訊收集
- 埠與服務掃描
- 目錄列舉
- 無破壞性的驗證命令

仍建議人工處理：

- 刪除、覆蓋、清空資料
- 修改許可權、密碼、賬號
- 持久化、橫向移動、C2 高風險任務
- 對生產目標的寫入操作

### 3. 用提示詞定義組織策略

審計 Agent 的提示詞應該寫成策略，而不是泛泛地說“謹慎審批”。建議明確：

- 預設放行哪些低風險操作
- 必須拒絕哪些破壞性操作
- 哪些情況需要人工升級
- 審查編輯模式下允許怎樣收窄引數

示例策略片段：

```text
常規資訊收集、只讀查詢、埠掃描預設 approve。
涉及刪除檔案、清空資料庫、修改賬號許可權、寫入持久化後門、停止關鍵服務時必須 reject。
若目標範圍超出使用者授權範圍，應 reject。
審查編輯模式下，可將路徑、目標、命令引數收窄後 approve，但不得擴大攻擊面。
```

### 4. 白名單隻放穩定低風險工具

白名單工具會跳過審批，因此要保守維護。推薦放：

- `read_file`
- `ls`
- `glob`
- `grep`
- `tool_search`
- 專案與漏洞查詢：`get_project_fact`、`list_project_facts`、`search_project_facts`、`list_vulnerabilities`、`get_vulnerability`
- 資產與知識後設資料查詢：`get_asset`、`query_assets`、`list_knowledge_risk_types`
- 執行與任務狀態查詢：`get_tool_execution`、`wait_tool_execution`、`batch_task_list`、`batch_task_get`
- 本地管理後設資料查詢：`manage_webshell_list`、`c2_event`、`c2_file`

上述內建 MCP 查詢仍受 RBAC 和資源範圍約束；白名單隻跳過 HITL 審批，不擴大訪問許可權。`list_dir` 僅在實際工具名為該值時有效；Eino 檔案系統的目錄列表工具名是 `ls`。

不建議直接全域性白名單：

- 任意 shell 執行工具
- 檔案寫入/刪除工具
- C2 任務工具
- WebShell 命令執行工具
- 會向目標或外部服務發起請求的“只讀”工具，例如 `webshell_file_read`、`webshell_file_list` 和 `search_knowledge_base`
- 同一工具名同時包含讀寫 action 的複合工具，例如 `c2_session`、`c2_listener`、`c2_profile`、`c2_task_manage`

## 模式選擇

| 模式 | 適用場景 |
|------|----------|
| 關閉 | 本地實驗、完全信任工具鏈 |
| 審批模式 | 只需要透過/拒絕 |
| 審查編輯 | 希望審計 Agent 收窄引數後放行 |

如果你已經配置了小模型審計，推薦從 **審批模式** 開始。只有當你希望 AI 自動收窄路徑、目標範圍或命令引數時，再開啟 **審查編輯**。

## 運維建議

- 定期檢視 **人機協同 → 審計日誌**，調整白名單和提示詞。
- 高風險環境下保持 `default_reviewer: human`，只讓審計 Agent 輔助給出建議。
- 小模型審批失敗時預設保守拒絕，這是預期行為。
- 修改 `hitl.audit_model` 後先在頁面點選 **測試審計模型**。
- 對生產、客戶、真實業務系統操作前，應保留人工最終確認。
