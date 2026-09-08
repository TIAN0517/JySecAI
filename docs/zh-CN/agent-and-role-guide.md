# Agent 與角色指南

JySecAI 的 Agent 行為由三類資源共同決定：角色、子代理和 Skills。角色決定當前任務身份和可用工具；子代理決定多代理分工；Skills 提供可按需載入的專題知識與流程。

## 角色

角色檔案位於 `roles/`，格式為 YAML。角色通常包含：

- 名稱。
- 描述。
- 系統提示詞。
- 可用工具列表。

設計原則：

- 專用角色只繫結必要工具。
- 提示詞明確授權邊界。
- 對高風險操作要求先說明影響並等待審批。
- 輸出格式儘量穩定，便於報告和覆盤。

示例方向：

- 資訊收集。
- Web 應用掃描。
- API 安全測試。
- 雲安全審計。
- 數字取證。
- 二進位制分析。
- CTF。

## 單代理

單代理介面：

- `POST /api/eino-agent`
- `POST /api/eino-agent/stream`

適合：

- 快速問答。
- 單目標測試。
- 工具鏈較短的任務。
- 需要穩定上下文的互動式分析。

## 多代理模式

多代理介面：

- `POST /api/multi-agent`
- `POST /api/multi-agent/stream`

編排模式：

- `deep`：主代理拆解任務，按需呼叫子代理。
- `plan_execute`：先規劃，再執行，必要時重規劃。
- `supervisor`：主管代理根據進展轉交不同子代理。

適合：

- 多階段滲透測試。
- 大範圍資訊收集。
- 需要並行角色分工的分析。
- 長任務和批次任務。

## 子代理 Markdown

子代理位於 `agents/*.md`。Front matter 示例：

```yaml
---
name: Attack Surface Enumeration
id: attack-surface-enumeration
description: 列舉目標暴露面並整理可驗證線索
tools:
  - subfinder
  - nmap
  - http-framework-test
bind_role: 資訊收集
max_iterations: 300
---
```

正文寫系統提示詞。建議包含：

- 職責邊界。
- 輸入期望。
- 使用工具順序。
- 輸出格式。
- 禁止事項。

## 主代理

主代理可用：

- `agents/orchestrator.md`
- `agents/orchestrator-plan-execute.md`
- `agents/orchestrator-supervisor.md`

或在 front matter 中設定 `kind: orchestrator`。每種編排只應有一個主代理定義。

## 工具選擇

工具選擇順序建議：

1. 角色繫結最小工具集。
2. 子代理按任務補充專用工具。
3. `tool_search` 動態解鎖大量工具。
4. 高風險工具由 HITL 審批。

不要給所有角色預設繫結全部工具，否則上下文成本和誤呼叫風險都會上升。

## 提示詞建議

好的角色提示詞應說明：

- 只在授權範圍內行動。
- 先確認目標和約束。
- 對寫入、刪除、爆破、持久化、C2、WebShell 等操作請求審批。
- 輸出可複核證據。
- 不確定時標註假設，不編造結果。

## 除錯

如果 Agent 選錯工具：

- 縮小角色工具列表。
- 增強工具 `short_description`。
- 開啟或調整 `tool_search_always_visible_tools`。
- 在角色提示詞中明確工具使用順序。

如果多代理跑偏：

- 檢查子代理描述是否過寬。
- 降低 `sub_agent_user_context_max_runes` 或明確任務輸入。
- 最佳化 orchestrator 提示詞。
- 檢視過程詳情和工具執行監控。

## 角色、子代理、Skill 的職責邊界

三者經常混用，建議這樣分工：

| 資源 | 解決的問題 | 不適合承載 |
| --- | --- | --- |
| Role | 當前對話的身份、語氣、工具邊界和授權規則 | 大量參考資料 |
| Agent Markdown | 多代理中的專業分工、交接格式和區域性策略 | 一次性任務事實 |
| Skill | 可複用方法論、檢查清單、模板和長參考資料 | 許可權控制 |

如果把授權邊界寫進 Skill，而角色沒有限制工具，Agent 仍可能在未載入 Skill 前選錯工具。許可權邊界應優先放在 Role 和 HITL 中。

## 編排模式選擇

| 模式 | 適合 | 不適合 |
| --- | --- | --- |
| `eino_single` | 短任務、互動式分析、需要穩定上下文 | 多階段大任務 |
| `deep` | 主代理動態拆分任務，子代理按需深入 | 需要嚴格步驟順序的流程 |
| `plan_execute` | 有明確階段、需要執行後覆盤和重規劃 | 使用者頻繁打斷的即興對話 |
| `supervisor` | 專家分工明確，需要主管路由 | 子代理定義含糊或過多 |

經驗上，普通安全測試先用 `eino_single`；複雜專案用 `plan_execute`；需要多個專業角色時用 `deep` 或 `supervisor`。

## 工具可見性如何影響行為

多代理裡 `tool_search` 會讓模型一開始只看見部分常駐工具。結果是：

- 工具頁面顯示可用，不代表模型當前上下文可見。
- `tool_search_always_visible_tools` 裡的工具更容易被模型呼叫。
- 工具描述越清晰，越容易被搜尋命中。
- 子代理自己的 `tools` 限制仍然很重要。

除錯“Agent 為什麼不用某工具”時，要同時檢查角色工具、子代理工具、tool_search 配置和工具描述。

## 好的子代理輸出格式

子代理不要只返回“已完成”。建議固定格式：

```markdown
## 結論

## 證據
- 命令/工具：
- 關鍵輸出：
- 置信度：

## 風險

## 建議下一步
```

這樣主代理才能繼續編排，也方便攻擊鏈和專案事實沉澱。

## 原始碼錨點

- Markdown Agent 解析：`internal/agents/markdown.go`
- 多代理準備：`internal/handler/multi_agent_prepare.go`
- 編排實現：`internal/multiagent/eino_orchestration.go`
- 工具搜尋中介軟體：`internal/multiagent/eino_middleware.go`
- 子代理上下文：`internal/multiagent/sub_agent_context_test.go`
