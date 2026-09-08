# JySecAI 工作流使用說明

[English](../en-US/workflow-graph.md)

本文件說明 **工作流（Workflow）** 的完整使用方式：如何在畫布上搭建流程、配置各型別節點、在節點之間傳遞資料，以及如何將流程繫結到角色並自動執行。

---

## 一、在哪裡使用工作流

1. 登入 JySecAI Web 端  
2. 左側導航進入 **工作流**  
3. 在左側列表選擇已有流程，或新建流程  
4. 在中央畫布拖拽、連線、配置節點  
5. 填寫流程 **ID**、**名稱**、**描述** 後點選 **儲存**

儲存後的流程可在 **角色管理** 中繫結到某個角色。繫結後，使用者與該角色對話時會按流程圖自動執行（`workflow_policy: auto`）。

---

## 二、畫布基本操作

| 操作 | 說明 |
|------|------|
| 新增節點 | 點選畫布上方節點型別按鈕（開始、工具、Agent、條件、審批、輸出、結束） |
| 連線 | 點選 **連線**，依次點選源節點和目標節點；再次點選 **連線** 退出連線模式 |
| 選中元素 | 單擊節點或連線，右側顯示 **節點屬性** |
| 刪除選中 | 點選 **刪除選中** 刪除當前節點或連線 |
| 自動佈局 | 點選 **自動佈局** 整理節點位置 |
| 試執行 | 點選 **試執行** 使用安全 dry-run 驗證資料流；工具、Agent、審批不會真實執行 |
| 刪除流程 | 點選 **刪除** 刪除整個流程定義 |

**硬性規則：** 每個流程至少包含 **1 個開始節點** 和 **1 個輸出節點**；開始節點不能有入邊，輸出 / 結束節點不能有出邊。儲存時前端和後端都會執行嚴格校驗。

---

## 三、自然語言生成草稿

工作流頁面提供 **用自然語言建立** 入口。使用者描述一句安全作業目標後，平臺會生成一個可編輯草稿，並返回結構化審計結果：

- 只生成草稿，不會自動儲存、試執行或真實執行工具。
- 服務端介面為 `POST /api/workflows/generate-draft`，許可權為 `workflow:write`。
- 生成結果包含 `graph`、`meta`、`capabilities`、`audit` 和 `stats`，前端應用到畫布後仍走現有儲存校驗。
- 高風險語義（執行指令碼、隔離、封禁、刪除、利用等）會標記 `high_risk`，並預設插入 HITL 審批或 `requires_human_confirmation`。
- 工具能力按已有工具列表匹配；未匹配到時降級為 Agent 草稿，並在 `audit.missing_fields` / `audit.assumptions` 中提示需要補配置。
- 如果服務端生成不可用，前端會使用本地確定性兜底生成器，繼續給出可編輯草稿和風險提示。

示例請求：

```http
POST /api/workflows/generate-draft
Content-Type: application/json

{
  "prompt": "對目標資產做埠掃描，如果發現高危埠就建立漏洞任務並通知負責人審批，最後輸出報告",
  "options": {
    "include_objective": true,
    "allow_schedule": false,
    "allow_high_risk": false
  },
  "available_tools": [
    { "key": "nmap", "name": "nmap", "enabled": true }
  ]
}
```

---

## 四、執行模型（先理解再配置）

工作流按 **有向圖** 執行，引擎從 **開始** 節點出發，沿連線依次執行下游節點。

每次執行會維護一份內部狀態，模板變數 `{{...}}` 從這裡取值：

| 內部狀態 | 模板字首 | 含義 |
|----------|----------|------|
| `inputs` | `{{inputs.xxx}}` | 流程啟動時的輸入（使用者訊息、會話 ID 等） |
| `lastOutput` | `{{previous.xxx}}` | **上一個剛執行完** 的節點的輸出 |
| `outputs` | `{{outputs.xxx}}` | 全域性 **命名變數池**（由節點的「輸出變數名」寫入） |
| `nodeOutputs` | `{{節點ID.xxx}}` | 指定節點 ID 的完整輸出物件 |
| `metrics` | 執行詳情中檢視 | 節點耗時、工具呼叫數、可收集到的 token / cost 等指標 |

### 3.1 `previous` 是什麼？

`{{previous.output}}` 表示 **緊鄰的上一個執行節點** 的 `output` 欄位。

- 每執行完一個節點，引擎都會更新 `lastOutput`
- **不是**「畫布上畫線的上游」，而是 **實際執行順序上的上一步**

示例：

```text
開始 → Agent A → Agent B
```

Agent B 的 `{{previous.output}}` = Agent A 的輸出。

但若中間有條件節點：

```text
開始 → Agent A → 條件 → Agent B
```

Agent B 的 `{{previous.output}}` = **條件節點** 的輸出（`true` / `false`），**不是** Agent A 的結果。

如果一個節點有 **多個上游節點** 同時連入，`previous` 會先按該節點的 **匯聚策略** 生成：

| 匯聚策略 | 含義 | 適合場景 |
|----------|------|----------|
| `all_merge` | 合併所有上游輸出，`previous.output` 為陣列 | 預設推薦，綜合多路結果 |
| `last_by_canvas` | 按畫布順序取最後一個上游輸出 | 明確只採用一路結果 |
| `first_non_empty` | 取第一個非空輸出 | 多路兜底 |
| `fail_fast` | 任一上游失敗則中止當前節點 | 關鍵鏈路、審批前置、安全檢查 |

### 3.2 `outputs` 是什麼？

`outputs` 是引擎在執行過程中維護的 **命名變數登錄檔**。

當 Agent、工具、輸出 等節點配置了 **輸出變數名**（欄位 `output_key`）後，節點執行成功會把結果寫入：

```text
outputs["你填的變數名"] = 節點輸出內容
```

之後 **任意下游節點** 都可以透過 `{{outputs.變數名}}` 引用，不要求兩個節點直接相連。

示例：

- Agent A 的 **輸出變數名** 填 `agent_result1`
- Agent B 的 **輸入來源** 填 `{{outputs.agent_result1}}`

即使 A 和 B 之間隔著條件節點，B 仍能拿到 A 的輸出。

### 3.3 什麼時候用 `previous`，什麼時候用 `outputs`？

| 場景 | 推薦寫法 |
|------|----------|
| 兩個節點 **直連**，只取上一步結果 | `{{previous.output}}` |
| 中間有其他節點（條件、工具、審批等） | `{{outputs.變數名}}` |
| 需要引用 **更早** 的某個節點結果 | `{{outputs.變數名}}` 或 `{{節點ID.output}}` |
| 條件判斷要基於某 Agent 的輸出 | `{{outputs.變數名}} != ""` |
| 讀取使用者最初輸入 | `{{inputs.message}}` |

**記憶口訣：**

- `previous` = 上一步（鏈式、緊鄰）
- `outputs` = 按名字取（跨節點、可回溯）

---

## 五、模板語法

### 4.1 基本格式

```text
{{變數路徑}}
```

支援字母、數字、下劃線、點、連字元，例如：

```text
{{previous.output}}
{{outputs.agent_result1}}
{{inputs.message}}
{{inputs.conversationId}}
{{previous.matched}}
{{node-abc123.output}}
```

### 4.2 可用路徑一覽

| 路徑 | 說明 |
|------|------|
| `{{inputs.message}}` | 使用者訊息（開始節點輸入） |
| `{{inputs.conversationId}}` | 會話 ID |
| `{{inputs.projectId}}` | 專案 ID |
| `{{previous.output}}` | 上一節點主輸出 |
| `{{previous.matched}}` | 上一條件節點的匹配結果（`true` / `false`） |
| `{{outputs.變數名}}` | 某節點註冊過的命名輸出 |
| `{{節點ID.output}}` | 指定節點 ID 的 `output` 欄位 |
| `{{previous.kind}}` | 上一節點輸出型別，如 `agent` / `tool` / `condition` |
| `{{previous.status}}` | 上一節點狀態，如 `completed` / `failed` / `simulated` |

節點輸出會保留相容欄位（如 `output`、`matched`），同時帶有結構化欄位：

```json
{
  "kind": "agent",
  "node_id": "node-2",
  "node_type": "agent",
  "status": "completed",
  "output": "..."
}
```

### 4.3 條件表示式

條件節點和連線條件支援比較、文字匹配、正則、邏輯組合與安全 JSONPath/JQ 路徑讀取：

```text
{{outputs.agent_result1}} != ""
{{previous.output}} == "ok"
{{outputs.count}} >= 100
{{previous.output}} contains "success"
{{previous.output}} matches "^ok"
{{outputs.risk_score}} >= 8 && {{previous.output}} != ""
jsonpath({{previous.output}}, "$.status") == "ok"
jq({{outputs.scan}}, ".severity") == "high"
```

規則：

- 支援 `==`、`!=`、`>`、`>=`、`<`、`<=`
- 支援 `contains` 子串匹配與 `matches` 正則匹配
- 支援簡單 `&&` / `||`
- 支援 `jsonpath(value, "$.path")` 與 `jq(value, ".path")` 的**安全路徑子集**，僅做欄位讀取，不執行任意指令碼
- 比較兩側會自動去掉首尾空格和引號
- 無比較符時，非空且不為 `false` / `0` / `null` 視為真
- 儲存時會靜態校驗表示式格式、JSONPath/JQ 路徑和正則語法

### 4.4 巢狀欄位繫結

節點的欄位繫結除 `output`、`message` 等普通欄位外，也支援 JSONPath/JQ 風格路徑：

| 繫結配置 | 含義 |
|----------|------|
| `from=previous, field=$.status` | 從上一節點輸出物件讀取 `status` |
| `from=outputs, field=$.scan.severity` | 從命名輸出中讀取巢狀欄位 |
| `from=node-1, field=.output.items[0]` | 從指定節點輸出讀取陣列元素 |

---

## 六、節點型別與配置

### 5.1 開始（start）

流程入口，將使用者輸入注入 `inputs`。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 輸入變數 | 逗號分隔的輸入鍵名 | `message, conversationId, projectId` |

開始節點輸出包含：`output`、`message`、`conversationId`、`projectId`。

### 5.2 Agent（agent）

呼叫大模型 Agent 處理任務，支援多種執行模式。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| Agent 模式 | `eino_single` / `deep` / `plan_execute` / `supervisor` | `eino_single` |
| 輸入來源 | 上游資料的模板表示式 | `{{previous.output}}` |
| 節點指令 | 本節點要完成的任務描述 | 空 |
| 輸出變數名 | 寫入 `outputs` 的鍵名 | `agent_result` |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

**訊息拼裝規則：**

- 僅填 **節點指令**：直接把指令發給 Agent  
- 僅填 **輸入來源**：生成「請基於上游節點輸出繼續處理：…」  
- 兩者都填：合併為「上游輸入 + 節點指令」

Agent 節點執行後：

- `previous.output` 更新為本節點響應文字  
- 若配置了 **輸出變數名**，同時寫入 `outputs[輸出變數名]`
- Agent 子圖在 Eino 中拆為 `prepare → execute → finalize`，便於 trace 與後續區域性 checkpoint

### 5.3 工具（tool）

呼叫已啟用的 MCP 工具。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| MCP 工具 | 工具名稱（必填） | — |
| 引數模板 | JSON，支援 `{{...}}` 模板 | `{}` |
| 超時秒數 | 可選 | 空 |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

示例引數模板：

```json
{"target": "{{inputs.message}}", "port": "443"}
```

若配置了 **輸出變數名**，工具返回結果會寫入 `outputs`。

### 5.4 條件（condition）

根據表示式計算分支，輸出 `matched`（`true` / `false`）。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 條件表示式 | 支援 `{{...}}` 與 `==` / `!=` | `{{previous.output}} != ""` |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

**分支規則：**

- 從條件節點連出的 **第一條線** 預設為 **「是」** 分支（`matched == true`）
- **第二條線** 預設為 **「否」** 分支（`matched == false`）
- 連線標籤可寫 `是` / `否`（或 `yes` / `no`、`true` / `false`）輔助識別
- 第三條及以後的出邊需在 **連線條件** 中自定義表示式

連線條件示例（選中連線後在右側配置）：

```text
{{previous.matched}} == "true"
{{previous.matched}} == "false"
```

### 5.5 審批（hitl）

人工確認檢查點。流程執行到該節點前會透過 Eino interrupt/checkpoint 暫停，等待 API 或監控面板審批後恢復。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 審批提示 | 支援模板 | `請審批該步驟是否繼續執行` |
| 提示欄位繫結 | 留空審批提示時，從繫結欄位讀取說明 | `previous.output` |
| 審批方 | `human` / `audit_agent` | `human` |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

HITL 等待資訊會記錄：

- `checkpointId`
- interrupt `beforeNodes`
- resume target / address / path
- resume payload schema（`approved`、`comment`）

### 5.6 輸出（output）

將流程最終結果寫入 `outputs`，供結束摘要和對話展示使用。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 輸出變數名 | 必填，最終結果的鍵名 | `result` |
| 變數來源 | 模板表示式，決定寫入的值 | `{{previous.output}}` |
| 固定輸出值 | 可選，填寫後覆蓋變數來源 | 空 |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

**注意：** 輸出節點是流程的「出口」，不應再有出邊。

### 5.7 結束（end）

可選節點，用於生成結束摘要模板（角色繫結流程中較少單獨使用）。

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 結束摘要模板 | 支援 `{{outputs.xxx}}` | `{{outputs.result}}` |
| 匯聚策略 | 多上游進入本節點時如何生成 `previous` | `all_merge` |

---

## 七、連線配置

選中 **連線** 後，右側可配置 **連線條件**。

| 場景 | 示例 |
|------|------|
| 普通節點後的過濾 | `{{previous.output}} == "ok"` |
| 條件節點「是」分支 | `{{previous.matched}} == "true"` |
| 條件節點「否」分支 | `{{previous.matched}} == "false"` |

若不填連線條件：

- 非條件節點：連線始終放行  
- 條件節點：按出邊順序自動分配是/否分支

---

## 八、完整示例：跨條件節點傳遞 Agent 輸出

### 7.1 流程結構

```text
開始 → Agent（生成初始值）→ 條件 → Agent（加工）→ 輸出
                              ↘ 否 → 輸出
```

### 7.2 節點配置

**Agent 1（第一個 Agent）**

| 欄位 | 值 |
|------|-----|
| 節點指令 | 只輸出 `123333333` |
| 輸出變數名 | `agent_result1` |

**條件**

| 欄位 | 值 |
|------|-----|
| 條件表示式 | `{{outputs.agent_result1}} != ""` |

**Agent 2（第二個 Agent）**

| 欄位 | 值 |
|------|-----|
| 輸入來源 | `{{outputs.agent_result1}}` |
| 節點指令 | 在輸入基礎上加 100，然後輸出 |
| 輸出變數名 | `agent_result` |

**輸出**

| 欄位 | 值 |
|------|-----|
| 輸出變數名 | `result` |
| 變數來源 | `{{outputs.agent_result}}` |

### 7.3 常見錯誤

| 錯誤配置 | 原因 |
|----------|------|
| Agent 2 輸入來源寫 `{{previous.output}}` | `previous` 指向條件節點，得到的是 `true`/`false`，不是 Agent 1 的文字 |
| 未給 Agent 1 填輸出變數名 | `outputs.agent_result1` 不存在，下游取到空值 |
| 條件表示式寫 `{{previous.output}}` | 判斷的是開始節點或上一節點的輸出，而非 Agent 1 的命名變數 |

---

## 九、繫結角色並執行

### 8.1 在角色管理中繫結

1. 進入 **角色管理**，編輯或新建角色  
2. 選擇繫結的 **工作流** ID  
3. 策略設為 `auto`（預設：有 `workflow_id` 時自動執行）  
4. 儲存角色

也可在角色 YAML 中直接配置：

```yaml
name: 工作流測試
workflow_id: "1233"
workflow_version: latest
workflow_policy: auto
```

### 8.2 執行效果

使用者選擇該角色併傳送訊息後：

1. 引擎載入對應 `graph_json` 並按圖執行  
2. 對話頁可看到 `workflow_start`、`workflow_node_start`、Agent 推理等進度事件  
3. 流程結束後返回摘要，列出 `outputs` 中所有命名輸出

若未配置輸出節點或條件未命中，`outputs` 可能為空，摘要會提示檢查輸出節點與分支。

---

## 十、除錯、試執行與覆盤

### 9.1 安全試執行（dry-run）

畫布工具欄點選 **試執行**，輸入一條測試訊息即可模擬執行流程。

dry-run 的安全邊界：

- `start` / `condition` / `output` / `end` 會按真實邏輯計算
- `tool` 不會真實呼叫 MCP，只返回 `[dry-run] tool call skipped`
- `agent` 不會真實呼叫模型，只返回 `[dry-run] agent execution skipped`
- `hitl` 不會暫停，只模擬透過

相關 API：

```http
POST /api/workflows/dry-run
```

請求體：

```json
{
  "graph": { "nodes": [], "edges": [], "config": {} },
  "inputs": { "message": "ping" }
}
```

響應包含：

- `outputs`
- `nodeOutputs`
- `trace`
- `metrics`
- `replayScript`

### 9.2 執行詳情與 replay

執行後可查詢完整節點執行軌跡：

```http
GET /api/workflows/runs/{runId}
```

返回 `run` 與 `nodeRuns`，每個節點記錄包含：

- input 快照
- output 快照
- status / error
- started_at / finished_at
- `duration_ms`

覆盤介面：

```http
GET /api/workflows/runs/{runId}/replay
```

該介面只根據已儲存的 `nodeRuns` 生成步驟，不會重新執行工具或 Agent。

### 9.3 指標（metrics）

工作流會盡量累計：

- `node_count`
- `duration_ms`
- `tool_call_count`
- Agent progress 中可收集到的 `prompt_tokens` / `completion_tokens` / `total_tokens` / `cost`

token 與成本是否存在取決於底層模型/Agent 事件是否上報 usage。

---

## 十一、儲存前校驗規則

儲存時系統會自動檢查：

| 規則 | 說明 |
|------|------|
| 必須有開始節點 | 至少 1 個 `start` |
| 必須有輸出節點 | 至少 1 個 `output`，且填寫輸出變數名 |
| 連線合法 | 源/目標節點存在，不能自環 |
| 開始節點無入邊 | 開始節點不能被指向 |
| 輸出 / 結束節點無出邊 | 輸出 / 結束節點後不應再連線 |
| 非開始節點必須有入邊 | 避免孤島節點 |
| 非輸出 / 結束節點必須有出邊 | 避免執行到死路 |
| 無環路 | Workflow 編排必須是 DAG |
| 可達性 | 所有節點必須能從開始節點到達，並能最終到達 output/end |
| 工具節點 | 必須選擇 MCP 工具；引數 JSON 必須合法；超時必須為正整數 |
| Agent 節點 | 必須填寫節點指令或輸入繫結；必須填寫輸出變數名 |
| 條件節點 | 必須填寫表示式；需要 1～2 條出邊；分支必須標記是/否且不能重複 |
| 連線條件 | 表示式、正則、JSONPath/JQ 路徑必須透過靜態校驗 |
| 匯聚策略 | 必須是 `all_merge` / `last_by_canvas` / `first_non_empty` / `fail_fast` |

---

## 十二、排錯指南

| 現象 | 可能原因 | 處理建議 |
|------|----------|----------|
| 下游拿到空值 | 上游未配置輸出變數名 | 給上游 Agent/工具填 **輸出變數名**，下游用 `{{outputs.xxx}}` |
| 下游拿到 `true`/`false` | 誤用 `{{previous.output}}`，上一步是條件節點 | 改用 `{{outputs.xxx}}` |
| 條件總走「否」 | 表示式與真實輸出格式不一致 | 檢查 Agent 輸出是否帶引號、換行；用 `!= ""` 先驗證 |
| 流程無最終輸出 | 未命中輸出節點所在分支 | 檢查條件分支連線；確保至少一條路徑到達 **輸出** 節點 |
| 角色對話未跑流程 | 角色未繫結或未啟用 | 確認 `workflow_id`、`workflow_policy: auto`、流程 `enabled: true` |
| 工具節點失敗 | 引數 JSON 不合法或工具未啟用 | 檢查引數模板；在 MCP 中啟用對應工具 |
| 儲存失敗提示分支非法 | 條件節點出邊未標記是/否或重複 | 選中連線，設定條件分支為 `true` 或 `false` |
| 多上游結果不符合預期 | 匯聚策略不合適 | 根據場景改為 `all_merge` / `first_non_empty` / `last_by_canvas` / `fail_fast` |
| 巢狀欄位取不到 | JSONPath/JQ 路徑不符合安全子集 | 使用 `$.a.b[0]` 或 `.a.b[0]`，不要用萬用字元/遞迴/表示式 |

---

## 十三、最佳實踐

1. **命名規範**：為每個需要被引用的節點設定有意義的輸出變數名，如 `scan_result`、`parsed_targets`，避免都叫 `agent_result`。  
2. **跨節點傳參優先用 `outputs`**：只要中間可能插入條件、工具、審批節點，就應用命名變數。  
3. **`previous` 僅用於直連**：A → B 且無中間節點時，`{{previous.output}}` 最簡潔。  
4. **條件判斷引用源資料**：判斷 Agent 輸出時用 `{{outputs.xxx}}`，不要用 `{{previous.output}}`（除非條件緊跟在目標 Agent 之後）。  
5. **每條路徑都要有出口**：確保「是」「否」分支最終都能到達 **輸出** 節點（或你期望的終點）。  
6. **多上游節點顯式選擇匯聚策略**：綜合結果用 `all_merge`，兜底用 `first_non_empty`，關鍵鏈路用 `fail_fast`。  
7. **巢狀 JSON 用 JSONPath/JQ 安全路徑**：例如 `jsonpath({{previous.output}}, "$.status") == "ok"`。  
8. **儲存前先 dry-run**：用簡單訊息驗證資料傳遞和分支，再繫結角色真實執行。

---

## 十四、相關程式碼位置（開發者參考）

| 模組 | 路徑 |
|------|------|
| 執行引擎 | `internal/workflow/runner.go` |
| Eino 編譯 / checkpoint / HITL | `internal/workflow/eino_compile.go` |
| 圖校驗 | `internal/workflow/validation.go` |
| 表示式 / JSONPath / 匯聚 | `internal/workflow/expression.go`、`jsonpath.go`、`join.go` |
| dry-run / replay 資料 | `internal/workflow/dry_run.go`、`internal/handler/workflow_run.go` |
| 畫布前端 | `web/static/js/workflows.js` |
| 流程 API | `internal/handler/workflow.go` |
| 角色繫結 | `internal/config/config.go`（`workflow_id` 欄位） |
