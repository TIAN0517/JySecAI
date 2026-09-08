# Eino 多代理改造說明（DeepAgent）

本文件記錄 **Eino 單代理（ADK）** 與 **多 Agent（CloudWeGo Eino `adk/prebuilt`）** 的改造範圍、進度與後續事項。原生 ReAct 執行路徑已移除。

## 總體結論

- **改造已可用於生產試驗**：流式對話、MCP 工具橋接、配置開關、前端模式切換均已落地。
- **入口策略**：**單代理** 走 `/api/eino-agent/stream`；多代理走 `/api/multi-agent/stream`，請求體 **`orchestration`** 指定編排。模式定位按 Eino ADK 最佳實踐區分：**Deep** 適合複雜安全測試與 task 子代理協作；**Plan-Execute** 適合目標明確的規劃 → 執行 → 重規劃閉環；**Supervisor** 適合多個專業子代理動態分派的專家路由場景。機器人預設 `robot_default_agent_mode: eino_single`；批次佇列預設 `eino_single`，多代理模式需 `multi_agent.enabled`。

## 已完成項

| 項 | 說明 |
|----|------|
| 依賴與代理 | `go.mod` 直接依賴 `github.com/cloudwego/eino`、`eino-ext/.../openai`；`go.mod` 註釋與 `scripts/bootstrap-go.sh` 指導 **GOPROXY**（如 `https://goproxy.cn,direct`）。 |
| 配置 | `config.yaml` → `agent.max_iterations` 為全域性 ReAct 上限（主/子代理統一）；`multi_agent`：`enabled`、`robot_use_multi_agent`、`sub_agents`（含可選 `bind_role`）、`eino_skills`、`eino_middleware` 等；結構體見 `internal/config/config.go`。 |
| Markdown 子代理 / 主代理 | 在 `agents_dir` 下放 `*.md`。**子代理**：供 Deep `task` 與 `supervisor` `transfer`。**主代理（按模式分離）**：`orchestrator.md`（或 `kind: orchestrator` 的**單個**其他 .md）→ **Deep**；固定名 `orchestrator-plan-execute.md` → **plan_execute**；固定名 `orchestrator-supervisor.md` → **supervisor**。正文優先於 YAML：`multi_agent.orchestrator_instruction`、`orchestrator_instruction_plan_execute`、`orchestrator_instruction_supervisor`；plan_execute / supervisor **不會**回退到 Deep 的 `orchestrator_instruction`。皆空時 plan_execute / supervisor 使用程式碼內建預設提示。管理：**Agents → Agent管理**；API：`/api/multi-agent/markdown-agents*`。 |
| MCP 橋 | `internal/einomcp`：`ToolsFromDefinitions` + 會話 ID 持有者，執行走 `Agent.ExecuteMCPToolForConversation`。 |
| 編排 | `internal/multiagent/runner.go`：單代理、Deep 主代理與子代理、Supervisor 主代理與子代理均使用 `TypedChatModelAgent[*schema.AgenticMessage]` / `deep.NewTyped[*schema.AgenticMessage]`，再經 adapter 接回現有 `adk.Runner` / TurnLoop / SSE 邊界；`plan_execute` 的 Executor 也使用 Agentic typed agent，經 adapter 掛入 Eino 官方 `planexecute.Config` 的經典外層契約。 |
| HTTP | `POST /api/multi-agent`（非流式）、`POST /api/multi-agent/stream`（SSE）；路由**常註冊**，是否可用由執行時 `multi_agent.enabled` 決定（流式未啟用時 SSE 內 `error` + `done`）。 |
| 會話準備 | `internal/handler/multi_agent_prepare.go`：`prepareMultiAgentSession`（含 **WebShell** `CreateConversationWithWebshell`、工具白名單與單代理一致）。 |
| 單 Agent | `internal/agent` 為 MCP/工具層（`ToolsForRole`、`ExecuteMCPToolForConversation`）；單代理編排走 `RunEinoSingleChatModelAgent`（`/api/eino-agent*`）。 |
| 前端 | 主聊天 / WebShell：**Eino 單代理**（`/api/eino-agent/stream`）與 **Deep / Plan-Execute / Supervisor**（`/api/multi-agent/stream` + `orchestration`）；`multi_agent.enabled` 控制多代理選項是否展示；設定頁已暴露 Eino 原生模型 retry/failover 引數，執行態時間線展示 `eino_model_retry` / `eino_model_failover` / `eino_usage_summary`。 |
| 流式相容 | Eino 單/多代理與 Web UI 共用 `handleStreamEvent`：`conversation`、`progress`、`response_start` / `response_delta`、`thinking` / `thinking_stream_*`、`tool_*`、`response`、`done` 等。 |
| 批次任務 | 佇列 `agentMode` 為 `deep` / `plan_execute` / `supervisor` 時子任務帶對應 `orchestration` 呼叫 `RunDeepAgent`；舊值 `multi` 與「`agentMode` 為空且 `batch_use_multi_agent: true`」均按 `deep`。 |
| 配置 API | `GET /api/config` 返回 `multi_agent` 標量與 Eino middleware 可運營欄位（含使用者輸入預算、`model_retry_*`、`model_failover_*`、常駐工具白名單）；`PUT /api/config` 可更新這些欄位且不覆蓋 `sub_agents`。 |
| OpenAPI | 多代理路徑說明已更新（流式未啟用為 SSE 錯誤事件）。 |
| 機器人 | `ProcessMessageForRobot` 按 `robot_default_agent_mode`（預設 `eino_single`）呼叫 `RunEinoSingleChatModelAgent` 或 `RunDeepAgent`。 |
| 預置編排 | 聊天 / WebShell：`POST /api/multi-agent*` 請求體 `orchestration`：`deep` \| `plan_execute` \| `supervisor`（預設 `deep`）。`deep` 使用 task 子代理協作；`plan_execute` 不構建 YAML/Markdown 子代理；`plan_execute_loop_max_iterations` 仍來自配置；`supervisor` 至少需一個子代理，只有一個子代理時會提示其專家路由空間有限。 |
| Eino 中介軟體 | `multi_agent.eino_middleware`（可選）：`patchtoolcalls`（預設開）、`toolsearch`（按閾值拆分 MCP 工具列表）、`plantask`（需 `eino_skills`）、`reduction`（大工具輸出截斷/落盤）、`checkpoint_dir`（Runner 斷點）、`model_retry_*` / `model_failover_channels`（單代理、Deep、Supervisor 與 `plan_execute` Executor 均走 Eino 原生 AgenticModel retry/failover）、`deep_output_key` / `task_tool_description_prefix`（Deep 與 supervisor 主代理共享其中模型容錯與 OutputKey）。Agentic 路徑的 patchtoolcalls / toolsearch / plantask / reduction / filesystem / skill / summarization tail 均使用 Eino v0.9.14 官方 typed middleware。**`plan_execute`**：Executor 使用 Agentic typed agent，經 adapter 保持官方 Plan/UserInput/ExecutedSteps session contract；Planner/Replanner 僅 summarization tail + prompt 預算截斷，不跑 MCP 工具鏈，因當前 Eino 官方 Planner/Replanner 構造仍是經典 ChatModel 介面。 |
| AgenticMessage 邊界 | `internal/multiagent/eino_agentic_message.go` 提供 `schema.Message` ↔ `schema.AgenticMessage` 的文字、reasoning、函式工具呼叫、函式工具結果對映；`internal/multiagent/eino_agentic_event_adapter.go` 將 `TypedAgentEvent[*schema.AgenticMessage]` 轉成現有 SSE/MCP drain 消費的 `AgentEvent[*schema.Message]`，覆蓋 assistant/tool result/stream/error，並保證 Agentic 流式 `FunctionToolResult` 的 tool name / call id 可被現有 `einoToolResultEventHandler` 回放、持久化與展示；`internal/multiagent/eino_agentic_agent_adapter.go` 將 `TypedAgent[*schema.AgenticMessage]` 包裝成現有 `adk.Agent` / `adk.ResumableAgent`，使 checkpoint resume、Runner、TurnLoop 與 SSE 邊界無需重寫；`internal/multiagent/eino_agentic_chat_model_agent.go` 組裝 `TypedChatModelAgent[*schema.AgenticMessage]`；`internal/multiagent/eino_single_runner.go`、Deep、Supervisor 生產路徑已切到 AgenticModel；`internal/multiagent/eino_model_resilience.go` 已接入 `agenticopenai.ChatModel` 工廠、Agentic 原生 ModelRetry 與 ModelFailover 配置，OpenAI/OpenAI-compatible 配置可實際構建 `model.AgenticModel`；`internal/multiagent/eino_middleware.go` 已提供 Agentic 官方泛型 patchtoolcalls / toolsearch / plantask / reduction prepender；`internal/multiagent/eino_agentic_summarize.go` 已把專案領域化摘要策略接入 Eino 原生 `summarization.NewTyped[*schema.AgenticMessage]`；`internal/multiagent/eino_agentic_chat_model_tail_middleware.go` 提供 protocol-neutral 的 Agentic typed tail（system 合併、continuation 去重、typed summarization、model-facing trace、model-output guard）。 |
| TurnLoop 接入橋 | 主聊天 Eino 單代理 / 多代理流式路徑已透過 `WithAgentTurnLoopInterruptRegistrar` 啟用 Eino 原生 `adk.TurnLoop` bridge：`internal/multiagent/eino_run_trace.go` 為每次 Eino run 生成統一 `runId`，自動注入所有 Eino progress data，並讓 `einoobserve` callbacks 複用同一 id；`internal/multiagent/eino_turn_loop_runtime.go` 封裝會話 item、`PushInterruptContinue`（`WithPreemptTimeout(AnySafePoint, ...)`）、idle stop 與 checkpoint 引數；`internal/multiagent/eino_turn_loop_iterator_starter.go` 統一 runtime 建立、舊 registrar 清理、interrupt/cancel registrar 繫結、idle stop 與 TurnLoop exit 轉發；`internal/multiagent/eino_runner_iterator_starter.go` 統一 Runner fallback 的原生 cancel option、runtime cancel registrar、fresh run checkpoint id 與 resume cancel option；`internal/multiagent/eino_checkpoint_runtime.go` 統一 checkpoint_dir 規整、store 建立、checkpoint id 與啟停日誌；`internal/multiagent/eino_checkpoint_resume_handler.go` 統一 Runner checkpoint preflight、resume 進度事件、resume 呼叫與失敗回退；`internal/multiagent/eino_initial_iterator_start_handler.go` 統一 checkpoint resume 後的 Runner / TurnLoop fresh start 選擇與 TurnLoop takeover 進度事件；`internal/multiagent/eino_turn_loop_event_bridge.go` 將 TurnLoop `OnAgentEvents` 顯式轉發給現有 SSE/MCP drain，併吞掉 preempt 產生的框架級 cancel；`internal/multiagent/eino_run_runtime_session.go` 統一 Runner/TurnLoop 啟動、checkpoint resume、fresh restart、native cancel registrar、run recovery、stream error、completion/cancellation cleanup 與 final result builder；`internal/multiagent/eino_run_error_handler.go` 統一不可重試 run error 的 pending flush、cancel fallback、timeout、iteration limit 與 error progress；`internal/multiagent/eino_run_recovery_handler.go` 統一 Eino 原生 retry、context overflow、run-level transient retry 與 fatal fallback 的恢復策略分派；`internal/multiagent/eino_stream_error_handler.go` 統一 assistant stream recv error 的 interrupt-continue、`eino_stream_error`、retry 與 partial result 分派；`internal/multiagent/eino_run_cancellation_handler.go` 統一 iter ctx cancel / interrupt-continue 時的 pending flush、進度事件與 partial result；`internal/multiagent/eino_run_completion_handler.go` 統一正常完成時 orphan pending flush 與 checkpoint cleanup；`internal/multiagent/eino_run_event_drain.go` 統一 Runner/TurnLoop 共享的 runMessages、assistantOutput、pending tool calls、stream id、tool-result / assistant-stream / materialized-message handlers 裝配；`internal/multiagent/eino_run_result_builder.go` 統一 partial/final `RunResult` 構建、model-facing trace 持久化、plan_execute executor 輸出優先順序與 exit fallback；`internal/multiagent/eino_pending_tool_calls.go` 抽出 pending tool-call drain state；`internal/multiagent/eino_tool_result_progress_emitter.go` 統一 `tool_result` 的 pending 關聯、去重、background wait 展示、execute stdout 抑制與 filesystem monitor 更新；`internal/multiagent/eino_tool_result_event_handler.go` 統一 ADK 流式/非流式 tool result 到 runMessages 與 `tool_result` 事件的適配；`internal/multiagent/eino_assistant_stream_event_handler.go` 統一 ADK 流式 assistant 輸出到主助手、子代理回覆、reasoning 與 tool-call fragments 的 drain；`internal/multiagent/eino_materialized_message_event_handler.go` 統一 ADK 非流式 message 到 runMessages、reasoning、主/子回覆、tool-call 與 tool-result drain；`internal/multiagent/eino_stream_tool_call_completion_handler.go` 統一流式 assistant tool-call fragments 的合併、pending 標記與 runMessages 持久化；`internal/multiagent/eino_execute_stdout_suppressor.go` 抽出 execute 輸出重複抑制狀態；`internal/multiagent/eino_message_stream_receiver.go` 統一 schema.Message stream 的 ctx cancel / EOF / nil chunk / recv error 處理；`internal/multiagent/eino_main_response_stream_emitter.go` 統一主助手 `response_start/response_delta` 與 SSE accumulated 欄位；`internal/multiagent/eino_main_assistant_stream_handler.go` 統一主助手流式正文緩衝、execute 複述去重、最終輸出記錄與 runMessages 追加；`internal/multiagent/eino_main_assistant_complete_handler.go` 統一主助手非流式正文的 execute 複述去重、UI 發射與最終輸出記錄；`internal/multiagent/eino_sub_agent_reply_emitter.go` 統一子代理 `eino_agent_reply(_stream_*)` 事件；`internal/multiagent/eino_reasoning_stream_emitter.go` 統一 reasoning chain 流式/非流式事件與 Claude signature 展示過濾；`internal/multiagent/eino_assistant_output_accumulator.go` 統一最後助手輸出與 plan_execute executor 展示文字記錄；`internal/multiagent/eino_run_message_accumulator.go` 統一事件流累積訊息，作為異常重試/partial result 的 Runner/TurnLoop 共享上下文來源；`internal/multiagent/eino_run_progress_tracker.go` 收斂主/子代理輪次、工具呼叫去重與 pending 標記狀態；`internal/multiagent/model_output_recovery_compat.go` 僅保留舊 recovery marker 的歷史相容攔截，預設鏈路不再預改寫模型工具呼叫；`internal/multiagent/eino_context_overflow_retry.go` 統一上下文超限後的單次激進壓縮、restart 上下文選擇、SSE 事件與結構化日誌；`internal/multiagent/eino_transient_run_retry_handler.go` 統一 run-level 臨時錯誤退避、pending flush、`eino_run_retry` 事件與重試耗盡日誌；`internal/multiagent/eino_native_model_retry_progress.go` 統一 Eino 原生 `WillRetryError` 的 `eino_model_retry` 事件與結構化日誌。“中斷並繼續”會優先 push 使用者補充進 TurnLoop，未註冊或 push 失敗時回退到 Eino 原生 cancel + trace 續跑鏈路。context overflow 壓縮、run-level transient retry 的 fresh restart 入口已統一為 TurnLoop-aware，避免異常續跑退回普通 Runner。 |

## 進行中 / 待辦（ backlog ）

| 優先順序 | 項 | 說明 |
|--------|----|------|
| P1 | **plan_execute Planner/Replanner typed 化跟進** | Executor 已切到 Agentic typed agent；當前 Eino 官方 Planner/Replanner 構造仍接收經典 ChatModel，因此規劃/重規劃側保留經典訊息契約。待官方提供 typed planner/replanner 或遷移到自研 typed plan-execute root 後再統一切換。 |
| P2 | **觀測與計費成本** | run 級 `runId` 已統一注入 Eino SSE/progress 事件並複用於 callbacks；`eino_run_usage_accumulator.go` 已從 `schema.ResponseMeta.Usage` 聚合 run 級 model calls、prompt/completion/total、cached 與 reasoning tokens，final/partial result 前透過 `eino_usage_summary` 發到前端時間線。後續可繼續補模型單價與 cost 欄位。 |
| P3 | **測試** | 增加 `internal/multiagent` 與 einomcp 的整合測試（mock model 或錄屏回放）。 |

## 關鍵檔案索引

- `internal/multiagent/runner.go` — DeepAgent / plan_execute / supervisor 組裝與事件迴圈  
- `internal/multiagent/eino_orchestration.go` — PlanExecute 根節點與 Agentic Executor 中介軟體棧（`buildPlanExecuteAgenticExecutorHandlers`）  
- `internal/handler/multi_agent.go` — SSE 與（同步）HTTP  
- `internal/handler/multi_agent_prepare.go` — 會話準備（含 WebShell）  
- `internal/einomcp/` — MCP → Eino Tool  
- `config.yaml` — `multi_agent` 示例塊  
- `web/static/js/chat.js` — 模式選擇與 stream URL  
- `web/static/js/webshell.js` — WebShell AI 流式 URL 與主聊天模式對齊  
- `web/static/js/settings.js` — 多代理標量、Eino 模型 retry/failover 設定儲存  

## 版本記錄

| 日期 | 說明 |
|------|------|
| 2026-03-22 | 首版：Eino DeepAgent + stream + 前端開關 + GOPROXY 指令碼。 |
| 2026-03-22 | 補充：進度文件、`prepareMultiAgentSession` 抽取、WebShell 後端對齊、`POST /api/multi-agent`、OpenAPI `/api/multi-agent*` 條目。 |
| 2026-03-22 | 路由常註冊、流式未啟用 SSE 錯誤、`robot_use_multi_agent`、設定頁持久化、WebShell/機器人多代理、`bind_role` 子代理 Skills/tools。 |
| 2026-03-22 | `tool_result.toolCallId`、`ReasoningContent`→思考流、`batch_use_multi_agent` 與批次佇列 Eino 執行。 |
| 2026-03-22 | 流式工具事件：按穩定簽名去重，避免每 chunk 刷屏與「未知工具」；最終回覆去重相同段落；內建排程顯示為 `task`。 |
| 2026-03-22 | `agents/*.md` 子代理定義、`agents_dir`、合併進 `RunDeepAgent`、前端 Agents 選單與 CRUD API。 |
| 2026-03-22 | `orchestrator.md` / `kind: orchestrator` 主代理、列表主/子標記、與 `orchestrator_instruction` 優先順序。 |
| 2026-04-19 | 主聊天「對話模式」：原生 ReAct 與 Deep / Plan-Execute / Supervisor；`POST /api/multi-agent*` 請求體 `orchestration` 與介面一致；`config.yaml` / 設定頁不再維護預置編排欄位（機器人/批次預設 `deep`）。 |
| 2026-04-21 | 移除角色 `skills` 與 `/api/roles/skills/list`；`bind_role` 僅繼承 tools；Skills 僅透過 Eino `skill` 工具按需載入。 |
| 2026-07-06 | **最佳實踐對齊**：Deep / Plan-Execute / Supervisor 改為中性適用場景描述；Supervisor 標為專家路由特定場景並收緊 transfer/exit 約束；plan_execute Executor 明確為遵循官方 session contract 的自定義 ChatModelAgent，保留 middleware 並補型別保護。 |
| 2026-07-02 | **plan_execute Executor 中介軟體對齊**：早期經典 `ExecPreMiddlewares` 與 Deep 主代理同源並補回歸測試；後續已由 Agentic typed Executor 裝配取代。 |
| 2026-06-02 | **移除原生 ReAct**：刪除 `/api/agent-loop*` 執行入口與 `AgentLoopWithProgress`；統一 Eino ADK（單代理 `/api/eino-agent*`，多代理 `/api/multi-agent*`）；任務 cancel/tasks API 保留。 |
| 2026-08-14 | **Eino 原生模型容錯運營化**：設定頁、`/api/config` public/update、YAML 寫回與迴歸測試補齊 `model_retry_*` / `model_failover_*` 配置鏈路。 |
| 2026-08-14 | **Agentic 原生摘要接入**：新增 `summarization.NewTyped[*schema.AgenticMessage]` builder 與 Agentic typed tail 插槽，保留專案摘要預算、transcript、使用者意圖 ledger、fact index 與 transient retry 策略。 |
| 2026-08-14 | **流式工具引數保護**：流式 tool-call fragments 合併後複用 model-output guard 閾值，危險 arguments 統一替換為 recovery marker，並同步到 UI `tool_call`、pending 跟蹤與 runMessages。 |
| 2026-08-14 | **Agentic 流式工具結果回放**：`recvSchemaMessageStream` 聚合 tool name / call id，Agentic streaming `FunctionToolResult` 經 adapter 後可被現有 tool-result drain 完整展示、持久化並用於 MCP display 更新。 |
| 2026-08-14 | **本地 MCP 審計迴歸**：新增真實 `mcp.Server` 覆蓋，驗證 Eino ADK filesystem begin/finish 複用同一 execution id，並在 `tool_result` 後把模型可見正文更新回 MCP display result。 |
| 2026-08-14 | **Agentic 上下文壓縮端到端**：新增 typed agent 測試，證明 `summarization.NewTyped[*schema.AgenticMessage]` 會先壓縮歷史，再把摘要、ledger 與 transcript 提示送入業務 AgenticModel。 |
| 2026-08-14 | **Agentic 主路徑切換**：`RunEinoSingleChatModelAgent`、Deep 主/子代理、Supervisor 主/子代理與 plan_execute Executor 切到 `TypedChatModelAgent[*schema.AgenticMessage]` / `deep.NewTyped[*schema.AgenticMessage]`；官方 typed patchtoolcalls / toolsearch / plantask / reduction / filesystem / skill / summarization 與 Agentic retry/failover 進入生產裝配；adapter 補 `adk.ResumableAgent`，保持 Runner checkpoint、TurnLoop、SSE 與 MCP drain 邊界穩定。 |
