# 工具執行治理

[返回中文文件](README.md)

本文說明 JySecAI 對長時間工具、MCP 阻塞、大輸出、取消和恢復上下文的治理策略。目標是讓 Agent 保持標準工具語義，同時避免工具卡死、上下文爆炸、資料庫膨脹或恢復時重新注入歷史大輸出。

## 設計目標

- **Agent 不被工具綁死**：工具呼叫可以很慢，但當前 runner 只等待有限時間。
- **長任務可繼續觀察**：超時返回 `execution_id`，後續可用 `wait_tool_execution` 多輪等待。
- **使用者和 Agent 都能取消**：當前會話結束或使用者停止任務時，會取消仍在執行的工具。
- **資料庫與 Agent 檢視一致**：DB 儲存的是 Agent 實際拿到的兜底後結果，不再儲存另一份原始大輸出。
- **恢復不會撐爆上下文**：續跑使用 model-facing trace；歷史異常大 tool trace 恢復時也會再次裁剪。
- **外部 MCP 有隔離保護**：按 server 限併發、按全侷限併發，並對連續失敗的 server 熔斷。

## 執行模型

普通工具呼叫仍然對 Eino/Agent 表現為一次標準 tool call，但底層執行分為兩段：

```text
Agent 呼叫工具
  -> ExecutionService 建立 execution
  -> worker 執行真實 MCP/工具呼叫
  -> Agent bounded wait
       -> 完成：返回工具結果
       -> 未完成：返回 execution_id，worker 繼續後臺執行
```

這解決了 MCP server、`exec`、`sqlmap`、`nmap`、`nuclei` 等長任務阻塞當前 runner 的問題。

## 工具狀態語義

| 狀態 | 含義 |
|---|---|
| `queued` | execution 已建立，等待 worker 或併發槽位 |
| `running` | worker 正在執行 |
| `background_running` | 前端展示狀態，表示本輪 Agent 已停止等待，但後臺仍在跑 |
| `completed` | 本次 tool call 本身已完成 |
| `failed` | 工具真實失敗 |
| `cancelled` | 使用者、Agent 或會話清理主動取消 |
| `hard_timeout` | 超過硬超時，被系統終止 |
| `orphaned` | 重啟/異常後發現 DB 中仍是 running，但執行時已無對應 worker |

注意：`wait_tool_execution` 到達 `timeout_seconds` 時，如果目標 execution 仍在執行，**這次 wait 呼叫本身是完成的觀察動作**，不是工具執行失敗。返回體會說明目標仍為 `running`，前端不應顯示為紅色失敗。

## 控制工具

| 工具 | 用途 |
|---|---|
| `get_tool_execution` | 讀取 execution 當前狀態 |
| `wait_tool_execution` | 等待指定 execution 一段時間 |
| `cancel_tool_execution` | 主動取消指定 execution |

`get_tool_execution` 與 `wait_tool_execution` 支援返回執行中輸出預覽：

- `include_partial_output`：是否返回 partial output，預設 `true`。
- `partial_output_max_bytes`：本次返回的尾部預覽上限，預設 `4096`，最大 `65536`。

partial output 是“已產生輸出的有界預覽”，不等同於最終 `result`。最終 `result` 仍只在工具結束時寫入 canonical execution 記錄；不支援流式輸出的工具不會返回 partial 欄位。

典型流程：

```text
1. 呼叫 exec/sqlmap/nmap 等長任務
2. 超過 tool_wait_timeout_seconds 後拿到 execution_id
3. Agent 可繼續推理、改用其他工具，或呼叫 wait_tool_execution
4. 仍未完成時可繼續等待，或呼叫 cancel_tool_execution
```

`tool_wait_timeout_seconds` 適用於內部 MCP、外部 MCP，以及 Eino filesystem 的流式 `execute`。Eino 的 `ls/read_file/write_file/edit_file/glob/grep` 等非流式 filesystem 工具會寫入 execution 監控記錄，但不作為後臺 worker 做軟等待續跑。

## 取消和會話清理

- 使用者點選“停止任務”時，會取消當前會話仍在執行的工具。
- 會話正常結束後，會批次取消當前會話仍 `running` 的工具。
- “中斷並繼續”類流程不會做會話級批次取消，以免誤殺後續需要等待的 worker。
- 取消只針對當前 conversation 繫結的 execution，不會誤殺其他會話的工具。

## 外部 MCP 隔離

外部 MCP 可能因為遠端 server 卡住、斷連或返回異常而拖慢 Agent。系統提供三層保護：

| 能力 | 配置 | 說明 |
|---|---|---|
| 單 server 併發限制 | `external_mcp_max_concurrent_per_server` | 同一個外部 MCP server 同時執行的工具數 |
| 全域性併發限制 | `external_mcp_max_concurrent_total` | 所有外部 MCP 工具總併發 |
| 熔斷 | `external_mcp_circuit_failure_threshold` / `external_mcp_circuit_cooldown_seconds` | 單 server 連續失敗後短期快速失敗，避免反覆打壞 server |

推薦預設：

```yaml
agent:
  external_mcp_max_concurrent_per_server: 2
  external_mcp_max_concurrent_total: 16
  external_mcp_circuit_failure_threshold: 3
  external_mcp_circuit_cooldown_seconds: 60
```

## 輸出兜底

系統使用 `multi_agent.eino_middleware.reduction_max_length_for_trunc` 作為統一工具結果上限。當前示例配置為 50000 bytes。

```yaml
multi_agent:
  eino_middleware:
    reduction_enable: true
    reduction_max_length_for_trunc: 50000
```

兜底覆蓋：

| 渠道 | 行為 |
|---|---|
| Agent 實際拿到的工具結果 | 使用兜底後的 canonical result |
| DB/監控儲存 | 儲存同一份 canonical result |
| `get_tool_execution` / `wait_tool_execution` | 讀取同一份 canonical result |
| Eino `execute` / filesystem 監控記錄 | 完成記錄前統一兜底 |
| 非流式 `exec` stdout/stderr | 源頭 bounded buffer |
| 流式 `exec` stdout/stderr | 推送給前端的累計輸出也受上限控制 |
| PTY 執行路徑 | 同樣受上限控制 |
| 前端詳情彈窗 | 額外有 UI 展示截斷保護 |

觸發上限後，完整輸出先寫入本地 trunc 檔案，Agent 側只保留計入預算的 `<persisted-output>` 預覽（含絕對路徑）。因此閾值為 50000 時，上下文文字不會超過該上限。

示例：

```text
<persisted-output>
Output too large (200000). Full output saved to: /path/to/tmp/reduction/conversations/<id>/trunc/<execution_id>
Use read_file with offset/limit to read parts of the file.
Preview (first …):
…

Preview (last …):
…

</persisted-output>
```

當前策略是「全文落盤 + 上下文預覽」：超過 `reduction_max_length_for_trunc` 時，完整輸出寫入本地檔案（預設 `tmp/reduction/conversations/<會話ID>/trunc/<execution_id>`），Agent/DB/監控拿到的是帶絕對路徑的 `<persisted-output>` 預覽；可用 `read_file` 按 offset/limit 回讀全文。

## DB 與恢復上下文

新執行結果的寫入路徑如下：

```text
工具完成
  -> NormalizeToolResultForStorage
  -> 寫入記憶體 execution
  -> 寫入 DB
  -> 返回給 Agent
```

因此正常情況下，DB 中儲存的就是 Agent 拿到的結果。

續跑恢復時，系統使用 `LastAgentTraceInput` 中的 model-facing trace，也就是實際送入 ChatModel 的訊息快照，而不是原始事件流累計。恢復入口還會對歷史 tool 內容再次應用上限，防止以下情況撐爆上下文：

- 升級前 DB 已經存過原始大輸出。
- 手工遷移或匯入的資料繞過了當前寫入路徑。
- 配置從更大閾值改成 50000。
- 未來某條旁路寫入漏掉 canonicalize。

## 關鍵配置建議

長任務場景推薦：

```yaml
agent:
  max_iterations: 800
  tool_timeout_minutes: 60
  tool_wait_timeout_seconds: 30
  external_mcp_max_concurrent_per_server: 2
  external_mcp_max_concurrent_total: 16
  external_mcp_circuit_failure_threshold: 3
  external_mcp_circuit_cooldown_seconds: 60
  shell_no_output_timeout_seconds: 1200

multi_agent:
  eino_middleware:
    reduction_enable: true
    reduction_max_length_for_trunc: 50000
```

引數說明：

| 引數 | 建議 | 說明 |
|---|---:|---|
| `max_iterations` | `300-1000` | 太大等於放棄迴圈保護 |
| `tool_timeout_minutes` | `60` | 單次工具硬超時，適合 sqlmap 等長任務 |
| `tool_wait_timeout_seconds` | `30-60` | Agent 本輪等待上限，到時返回 `execution_id` |
| `shell_no_output_timeout_seconds` | `600-1200` | 連續無輸出時終止，防止靜默掛死 |
| `reduction_max_length_for_trunc` | `50000` | 工具結果統一上限 |

不建議把 `tool_wait_timeout_seconds` 設定得很大。長任務應由 worker 後臺跑，Agent 透過 `execution_id` 繼續觀察，而不是一輪等待數分鐘。

## 測試建議

可以用以下對話測試長任務語義：

```text
呼叫 exec 執行 sleep 120；如果超過 10 秒還沒完成，不要一直等，告訴我 execution_id，然後呼叫 wait_tool_execution 等 5 秒；如果仍未完成，再呼叫 cancel_tool_execution，最後說明狀態。
```

可以用以下命令測試大輸出兜底：

```text
呼叫 exec 執行：python3 - <<'PY'
print("A" * 200000)
PY
然後展示工具結果長度和是否包含截斷提示。
```

預期：

- 初始長任務會返回 `execution_id`，狀態為 `running` 或前端展示 `background_running`。
- `wait_tool_execution` 等待到上限但目標未完成時，本次 wait 呼叫不應顯示為執行失敗。
- 大輸出結果不會超過 `reduction_max_length_for_trunc`。
- DB、監控詳情、Agent 繼續推理看到的是同一份兜底結果。

## 當前邊界

- 外部 MCP 的遠端 server 內部如何採集輸出不由 JySecAI 控制；JySecAI 會在結果進入本系統後統一兜底、限併發和熔斷。
- 超長工具輸出會在截斷前寫入本地 `tmp/reduction/.../trunc/<id>`（或 `reduction_root_dir`），bounded result 中包含可 `read_file` 的絕對路徑。
