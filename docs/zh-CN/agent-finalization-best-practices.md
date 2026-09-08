# Agent 最終回覆治理最佳實踐

[返回中文文件](README.md)

調研日期：2026-07-28

本文聚焦一個具體問題：Agent 在工具呼叫、推理、計劃或子代理協作尚未真正完成時，輸出了一段“像結論”的自然語言，前端或編排層把它當作最終回覆展示。結論先說清楚：成熟 Agent 系統不會用“最近一段 assistant 文字”判斷任務完成，而是用執行時狀態、工具狀態、驗證結果和顯式終態事件共同決定是否 final。

## 一、核心結論

1. **最終回覆是執行時事件，不是自然語言內容。**
   “已拿到”“下一步”“Huge breakthrough”這類文字只能作為候選觀察或進展，不能作為完成訊號。

2. **過程面和交付面必須隔離。**
   `thinking`、`reasoning_chain`、`planning`、`response_delta`、子代理回覆、工具輸出都屬於過程面；只有透過 final gate 的 `response` / `final` 事件才能寫入主訊息氣泡和 `messages.content`。

3. **複雜任務需要 verifier，而不是更長 prompt。**
   Prompt 可以提醒模型謹慎，但最終完成必須由程式碼層判斷：是否仍有待執行工具、後臺 execution、未完成計劃步驟、未驗證證據、未記錄事實/漏洞、未清理或未說明不可清理。

4. **不同 agent 模式不同，但 final 治理原則一致。**
   單代理、Deep、Plan-Execute、Supervisor 都需要 final gate。區別只是 gate 的證據來源不同：單代理看工具軌跡，Deep 還要看子代理結果，Plan-Execute 要看 Replanner 的終止判斷，Supervisor 要看 `exit` 與 supervisor 彙總。

## 二、成熟 Agent 的公開做法

| 系統 | 公開做法 | 對 final 治理的啟發 |
|---|---|---|
| Codex | OpenAI 的 Codex prompting guide 建議不要在 prompt 中強行要求 upfront plan、preamble 或 status updates，因為這可能導致 rollout 未完成就停止。 | 不要把“模型自己說的階段性計劃/狀態”當完成依據；agent harness 應負責執行迴圈和收尾。 |
| Claude Code | Claude Code 提供 `PreToolUse`、`PostToolUse`、`Stop` 等 hooks；`PostToolUse` 明確發生在工具成功執行之後。 | 生命週期事件比自然語言可靠。驗證、審計、阻斷應掛在確定的階段邊界上。 |
| Claude Code Subagents | 子代理有獨立上下文、自定義系統提示、特定工具許可權和獨立許可權；子代理適合隔離大量檢索/日誌/檔案讀取。 | 子代理輸出是證據材料，不是主任務最終結論；主代理必須彙總、驗收、再 final。 |
| Claude Code Plan Mode | Plan mode 先讀檔案併產出計劃，獲得批准前不編輯。 | 計劃與執行是不同狀態；計劃完成不等於任務完成。 |
| Cursor Plan Mode | Cursor Plan Mode 會研究程式碼庫、詢問澄清問題、生成可審查計劃，並等待使用者確認後再構建。 | UI 層把 plan/review/build 拆開，使用者不會把計劃誤認為最終交付。 |
| OpenCode | OpenCode 把 Build、Plan、Review、Debug、Docs 等 agent 分成不同工具許可權與用途，Plan agent 只分析規劃不做修改。 | 用 agent 能力邊界降低誤觸發：能規劃的 agent 不等於能執行完成。 |
| Eino ADK | Eino ADK 提供事件驅動輸出、Runner 回撥、中斷、checkpoint，以及 Supervisor、Plan-Execute 等協作原語。Plan-Execute 由 Planner、Executor、Replanner 協作。 | 當前專案選型方向正確；需要把事件驅動能力進一步固化為 finalization contract。 |

主要參考：

- OpenAI Codex Prompting Guide: https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide
- Claude Code Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Claude Code Common Workflows: https://docs.anthropic.com/en/docs/claude-code/common-workflows
- Cursor Agent Best Practices: https://cursor.com/blog/agent-best-practices
- OpenCode Agents: https://opencode.ai/docs/agents/
- CloudWeGo Eino ADK: https://www.cloudwego.io/docs/eino/core_modules/eino_adk/
- CloudWeGo Eino ADK Patterns: https://www.cloudwego.io/docs/eino/overview/eino_adk0_1/

## 三、通用最佳實踐

### 1. 建立 Finalization Contract

所有執行入口統一產出一個結構化收尾物件，只有它允許觸發最終回覆。

```go
type FinalizationDecision struct {
    Status             string   // in_progress | completed | blocked | failed | cancelled
    Finalizable        bool
    CompletionReason   string   // verified | user_cancelled | timeout | blocked | failed
    FinalText          string
    EvidenceVerified   bool
    EvidenceRefs       []string
    PendingToolRuns    []string
    PendingPlanSteps   []string
    PendingApprovals   []string
    MissingChecks      []string
}
```

硬規則：

- `Finalizable=false` 時禁止傳送 `response` 終態事件。
- `Status=in_progress` 時只能發 `progress`、`planning`、`tool_*`、`reasoning_chain` 等過程事件。
- `FinalText` 不能為空，但非空不代表可以 final。
- `PendingToolRuns`、`PendingPlanSteps`、`PendingApprovals` 任一非空時不能 `completed`。
- `EvidenceVerified=false` 時不能把候選輸出寫成已驗證結論。

### 2. 固定 SSE 事件語義

推薦事件分層：

| 事件 | 展示位置 | 可否寫 `messages.content` | 說明 |
|---|---|---:|---|
| `progress` | 任務狀態/時間線 | 否 | 簡短進度 |
| `planning` | 執行詳情 | 否 | 主代理計劃、階段性判斷 |
| `reasoning_chain` / `thinking` | 執行詳情 | 否 | 推理/思考摘要 |
| `tool_call` / `tool_result` | 執行詳情 | 否 | 工具事件 |
| `eino_agent_reply` | 執行詳情 | 否 | 子代理返回材料 |
| `finalization_check` | 執行詳情 | 否 | verifier 結果 |
| `finalization_auto_continue` | 執行詳情 | 否 | verifier 觸發的工程續跑，`contextInjection=false` |
| `response` | 主訊息氣泡 | 是 | 只能在 `data.finalized=true` 時使用 |
| `done` | 關閉流 | 否 | 僅表示流結束，不表示任務成功 |
| `error` / `cancelled` | 主訊息氣泡或系統提示 | 是，終態失敗類 | 必須帶原因 |

### 3. 把“最終候選”與“最終回覆”分開

模型可以輸出候選結論，但候選結論必須先進入 `final_candidate` 或 `planning`，再由 verifier 決定是否提升：

```text
assistant text
  -> candidate
  -> finalization gate
  -> response(finalized=true)
```

不要這樣做：

```text
assistant text
  -> response
```

### 4. Stop-time Verification

借鑑 Claude Code hook 思路，在 agent run 停止時做一次確定性檢查：

- 所有工具呼叫都有對應 tool result。
- 後臺 execution 都處於 terminal 狀態，或被明確登記為仍在執行且任務狀態為 `in_progress` / `blocked`。
- Plan-Execute 沒有未執行的 required step。
- Supervisor 沒有未彙總的子代理結果。
- 在 evidence-required 策略下，至少存在可查詢到的 completed 工具執行證據。

### 5. 子代理輸出只作證據

子代理返回不能直接成為使用者最終回覆。主代理必須完成：

- 去重和衝突合併。
- 證據強度排序。
- 不確定性標註。
- 範圍邊界確認。
- 使用者可讀交付。

### 6. Prompt 只做軟約束，程式碼做硬約束

Prompt 中可以寫：

```text
Interim observations must be marked as progress, not final.
Do not produce a final answer until verification is complete.
```

但真正決定 final 的必須是後端欄位和狀態機。否則模型只要生成一段像最終結論的自然語言，UI 仍可能誤判。

## 四、JySecAI 當前落地狀態

當前專案已經具備一套顯式 final gate：

- [internal/agentfinalizer/decision.go](../../internal/agentfinalizer/decision.go) 是唯一的最終回覆決策契約。
- [internal/handler/finalization_helpers.go](../../internal/handler/finalization_helpers.go) 負責把決策結果寫入 `process_details`，並且只有 `Finalizable=true` 時才呼叫 `UpdateAssistantMessageFinalize`。
- [internal/handler/eino_single_agent.go](../../internal/handler/eino_single_agent.go)、[internal/handler/multi_agent.go](../../internal/handler/multi_agent.go)、[internal/handler/workflow_integration.go](../../internal/handler/workflow_integration.go)、[internal/handler/batch_queue_executor.go](../../internal/handler/batch_queue_executor.go) 均已在收尾處接入 finalizer。
- [web/static/js/monitor.js](../../web/static/js/monitor.js) 只把 `data.finalized === true` 的 `response` 當最終回覆；未最終化文字會顯示為最終回覆檢查未透過。
- [web/static/js/webshell.js](../../web/static/js/webshell.js) 將流式正文標記為候選輸出，只有 `response(finalized=true)` 才切換為完成態。
- [internal/agentfinalizer/decision_test.go](../../internal/agentfinalizer/decision_test.go) 覆蓋 pending tool、HITL、空輸出、證據策略要求但缺執行證據、失敗證據不能支撐最終化、完成態證據可 final 等迴歸場景。
- [internal/handler/finalization_auto_continue.go](../../internal/handler/finalization_auto_continue.go) 在缺 completed 執行證據時最多自動續跑 2 段；續跑只恢復已有模型軌跡，不向 agent 注入新的 user/system 文案。

當前契約的核心規則：

1. **模型自然語言只是 candidate。**
   `RunResult.Response` 不能直接升級為最終回覆，必須經過 `agentfinalizer.Decide`。

2. **所有 `response` 事件必須攜帶終態欄位。**
   至少包含 `finalized`、`finalizable`、`status`、`completionReason`、`evidenceVerified`、`evidenceRefs`、`pendingExecutionIds`、`missingChecks`。

3. **未完成工具會阻斷 final。**
   `queued/running` 工具執行仍存在時，決策結果為 `in_progress/pending_tool_executions`。

4. **執行證據必須由結構化策略宣告。**
   後端不從使用者自然語言、助手回覆或 agent mode 名稱中推斷執行意圖。聊天請求透過 `finalization.requireExecutionEvidence` 顯式宣告；WebShell、Workflow、批次、機器人等執行入口由呼叫點顯式傳入 policy。policy 要求證據時，至少需要一個可查詢到的 `completed` 工具執行記錄；只有 failed/cancelled 記錄不能支撐最終化。

5. **缺執行證據先工程續跑，再阻斷。**
   Eino 單代理和 Eino 多代理主鏈路在 `missing_execution_evidence` 時會先透過已有 trace 自動續跑，不注入額外上下文；達到續跑上限後仍缺證據才寫入 blocked。

6. **HITL 和空輸出不會 final。**
   workflow 等待人工確認、空 assistant 文字、Eino 空輸出佔位均會寫入阻斷文案，而不是成功總結。

## 五、貼合當前專案的推薦架構

當前採用的鏈路是：

```text
Agent / Eino ADK events
  -> event normalizer
  -> process_details
  -> finalization verifier
  -> response(finalized=true)
  -> messages.content
```

### 1. 後端統一 Finalizer

職責：

- 接收 `RunResult` / 候選文字、`mcpExecutionIds`、會話與助手訊息 ID、HITL 狀態、編排模式。
- 透過資料庫查詢工具執行狀態，識別 pending、completed、failed、cancelled 等證據狀態。
- 返回 `FinalizationDecision`。
- 不呼叫高風險工具，只做狀態和證據檢查。

### 2. RunResult 終態欄位

[internal/multiagent/runner.go](../../internal/multiagent/runner.go) 已擴充套件終態欄位：

```go
type RunResult struct {
    Response             string
    MCPExecutionIDs      []string
    LastAgentTraceInput  string
    LastAgentTraceOutput string

    Finalized           bool
    Status              string
    CompletionReason    string
    EvidenceVerified    bool
    EvidenceRefs        []string
    PendingExecutionIDs []string
    MissingChecks       []string
}
```

### 3. 傳送 `response` 的條件

在單代理、多代理、工作流、批處理收尾處統一執行：

```go
decision := h.finalizeAgentRunForDelivery(...)
if !decision.Finalizable {
    sendEvent("finalization_check", "任務尚未達到最終回覆條件", decision)
    sendEvent("response", finalizationBlockedMessage(decision), finalizationResponsePayload(decision, extra))
    return
}

sendEvent("response", decision.FinalText, finalizationResponsePayload(decision, extra))
```

### 4. 前端只信 `finalized=true`

在 [web/static/js/monitor.js](../../web/static/js/monitor.js) 的 `case 'response'` 中執行硬判斷：

```js
const responseFinalized = isFinalizedResponseData(responseData);
const bubbleText = responseFinalized
  ? resolvedResponseText
  : (event.message || '任務尚未達到最終回覆條件，暫不生成成功結論。');
markAssistantFinalizationState(assistantIdFinal, responseData);
```

WebShell 側同理：`response_delta` 可以用於實時預覽，但 UI 文案應標記為“執行中輸出”，只有最終 `response(finalized=true)` 才顯示為完成態。

### 5. 各模式 final gate

| 模式 | 誰可以產出最終候選 | 誰決定 final | 必須檢查 |
|---|---|---|---|
| Eino 單代理 | 單代理最後助手文字 | Finalizer | 無 pending tool、證據引用完整、任務狀態 terminal |
| Deep | 主代理彙總文字 | Finalizer | 子代理結果已彙總；子代理文字不能直接 final；工具狀態 terminal |
| Plan-Execute | Replanner 結束後的彙總文字 | Replanner + Finalizer | Executor 單步輸出不能 final；計劃步驟完成或明確 blocked |
| Supervisor | Supervisor 的 `exit` / 彙總文字 | Supervisor + Finalizer | transfer 已返回；無未處理專家結果；最終由 supervisor 統一口徑 |

### 6. 安全測試場景的證據 gate

安全測試、WebShell、批次驗證、Workflow 和多代理執行等 evidence-required 場景，最終回覆必須至少滿足：

- 有明確目標和授權範圍標識。
- 有可複核證據引用，例如工具 execution id、請求/響應摘要、截圖路徑、命令輸出摘要、事實/漏洞記錄 ID。
- 有身份或影響驗證結果，而不是隻憑 marker 文字判斷。
- 已記錄到專案黑板或漏洞庫，或明確說明未繫結專案導致無法記錄。
- 高風險動作已清理、回滾、取消，或明確說明未執行清理的原因。
- 仍在執行的掃描/命令/WebShell/C2 任務不能被隱式當作完成。

注意：這裡的 gate 是治理規則，不要求最終報告暴露敏感利用細節；可以只給證據摘要和內部引用。

## 六、落地狀態與後續增強

### P0：先修“誤 final”（已落地）

1. 已引入 `FinalizationDecision`。
2. 主要 agent SSE `response` 事件已攜帶 `data.finalized/finalizable/status/completionReason` 等欄位。
3. 前端 `monitor.js` 和 `webshell.js` 已按 `finalized=true` 區分候選輸出和最終回覆。
4. `RunResult.Response` 仍保留相容欄位名，但語義已由 finalizer 統一提升；後續可再拆成 `CandidateResponse` / `FinalResponse`，減少誤用空間。
5. Plan-Execute / Deep / Supervisor / Eino Single 等模式均透過統一 handler 收尾 gate。

### P1：補證據鏈（部分落地）

1. 已用 `mcp_execution:<id>` 作為基礎 evidence refs。
2. `finalization_check` 事件已展示 pending execution 與 missing checks。
3. 執行入口已啟用顯式 execution evidence policy；Eino 主鏈路在 policy 要求證據且缺少 completed 工具證據時先無注入續跑，達到上限後才阻斷 final。
4. 後續建議：為 `record_vulnerability`、`upsert_project_fact`、專案黑板記錄建立更細粒度 evidence refs。
5. 後續建議：最終報告模板固定包含“結論、證據、風險/不確定性、後續動作”。

### P2：體驗和觀測（後續增強）

1. 在任務卡片展示 `in_progress / verifying / finalizing / completed / blocked`。
2. 為 finalizer 加日誌和指標：誤攔截率、缺失證據型別、pending tool 數量。
3. 支援“繼續驗證”按鈕，從 `FinalizationDecision.MissingChecks` 自動生成下一輪輸入。

## 七、驗收測試建議

至少加入這些迴歸測試：

1. **推理文字不 final**
   模擬 `reasoning_chain` 裡出現看似完成的候選結論，但本輪沒有 completed 工具執行證據；預期主訊息氣泡不顯示成功結論，只顯示執行中或阻斷態。

2. **主代理階段性輸出不 final**
   模擬 `response_start/delta` 輸出“下一步繼續驗證”；預期只進入 timeline `planning`。

3. **未完成後臺工具不 final**
   工具返回 `execution_id` 且狀態 `running`；即使模型給出總結，也只能 `in_progress`。

4. **Plan-Execute Executor 輸出不 final**
   Executor 輸出“突破成功”，但 Replanner 未結束；預期不觸發 `messages.content` finalize。

5. **Supervisor 子代理輸出不 final**
   子代理返回確定結論，Supervisor 未 `exit`；預期只進入 `eino_agent_reply`。

6. **最終事件必須帶 finalized**
   前端收到舊格式 `response` 無 `finalized=true`；預期候選內容只進入詳情/警告，主訊息顯示阻斷態，不建立成功最終氣泡。

7. **失敗和取消可終態**
   `error` / `cancelled` 仍可更新助手訊息，但 `completionReason` 必須是 `failed` / `user_cancelled`，不能偽裝為成功完成。

## 八、推薦預設策略

對 JySecAI，建議預設策略是：

```text
eino_single：輕量任務可用，但 final gate 必須開啟
deep：複雜安全測試預設推薦
plan_execute：目標明確、需要嚴格“規劃-執行-重規劃”的任務推薦
supervisor：多專家路由任務使用，不作為預設泛化模式
```

最終治理一句話：

```text
messages.content 只能來自 FinalizationDecision.FinalText；
process_details 可以展示所有過程；
前端只能把 response(finalized=true) 當最終回覆。
```
