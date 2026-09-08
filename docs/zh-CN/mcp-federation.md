# MCP 聯邦

JySecAI 同時支援內建 MCP 工具、獨立 HTTP MCP 服務和外部 MCP 聯邦。MCP 是 Agent 呼叫工具的主要協議層。

## 內建 MCP

Web 服務內部會建立 MCP Server，並註冊：

- YAML 命令工具。
- 內建安全執行工具。
- 知識庫工具。
- 專案事實工具。
- C2 工具。
- WebShell 工具。
- 批次任務工具。
- 視覺分析工具。

前端和 Agent 通常透過應用內部呼叫，不需要額外配置。

## HTTP MCP 服務

配置：

```yaml
mcp:
  enabled: true
  host: 0.0.0.0
  port: 8081
  auth_header: "X-MCP-Token"
  auth_header_value: "random-secret"
```

生產環境必須設定 `auth_header_value`，並限制網路訪問。

## Web 內 MCP 端點

登入後可透過：

```text
POST /api/mcp
```

該端點複用 Web 認證，適合內部頁面或受控整合。

## 外部 MCP

外部 MCP 配置在：

```yaml
external_mcp:
  servers: {}
```

也可以透過 Web 的 MCP 管理頁面新增、啟動、停止和刪除。

介面：

- `GET /api/external-mcp`
- `GET /api/external-mcp/stats`
- `GET /api/external-mcp/:name`
- `PUT /api/external-mcp/:name`
- `POST /api/external-mcp/:name/start`
- `POST /api/external-mcp/:name/stop`
- `DELETE /api/external-mcp/:name`

## stdio

stdio MCP 適合本機命令啟動的工具服務。

關注點：

- 命令路徑必須存在。
- 工作目錄正確。
- 環境變數完整。
- 程序退出會導致工具不可用。
- 日誌中檢視啟動失敗原因。

## HTTP / SSE

HTTP 或 SSE MCP 適合遠端或長期執行服務。

關注點：

- URL 可達。
- 認證頭正確。
- TLS 證書可信。
- 代理和防火牆放行。
- 服務端協議版本相容。

## 工具暴露策略

工具過多會增加上下文成本和誤選機率。多代理中可透過：

```yaml
multi_agent:
  eino_middleware:
    tool_search_enable: true
    tool_search_min_tools: 20
    tool_search_always_visible: 12
    tool_search_always_visible_tools:
      - read_file
      - glob
      - grep
      - tool_search
```

讓常用工具常駐，其餘工具由 `tool_search` 動態解鎖。

## 安全建議

- 外部 MCP 只接入可信服務。
- 遠端 MCP 必須認證。
- 高風險工具不要常駐上下文。
- 外部 MCP 的檔案系統和命令執行能力要單獨評估。
- 變更外部 MCP 後檢視審計日誌。

## 除錯

排查順序：

1. `/api/external-mcp/stats` 檢視狀態。
2. 檢查服務日誌。
3. 單獨執行 stdio 命令。
4. 用 curl 測試 HTTP/SSE 地址。
5. 檢查工具是否被角色或 tool_search 策略隱藏。

## MCP 生命週期

外部 MCP 的生命週期不是簡單的“新增 URL”：

1. 註冊配置：名稱、型別、命令或 URL、環境變數。
2. 啟動連線：stdio 拉起程序，HTTP/SSE 建立客戶端。
3. 拉取工具列表：工具名、描述、schema 進入平臺。
4. 暴露給 Agent：受角色、tool_search、HITL 影響。
5. 執行工具：引數校驗、呼叫、記錄監控。
6. 連線恢復：程序退出或網路失敗後嘗試恢復。
7. 停止/刪除：從執行時和配置中移除。

排錯時要確認卡在哪一步。

## 工具命名規範

工具名應：

- 穩定。
- 小寫或 snake_case。
- 表達動作和物件。
- 避免和內建工具重名。

不建議：

```text
run
execute
scan
tool1
```

建議：

```text
burp_send_to_repeater
asset_lookup_domain
cloud_list_public_buckets
```

好的工具名會提升 tool_search 命中率，也降低誤呼叫。

## 外部 MCP 安全審查清單

接入前問：

- 它能讀寫本機檔案嗎？
- 它能執行命令嗎？
- 它會訪問哪些網路？
- 它是否把請求發給第三方？
- 它的工具描述是否可信？
- 它的輸出是否可能包含 prompt injection？
- 它是否需要獨立執行使用者或容器隔離？

只要答案不清楚，就不要放進生產環境常駐工具池。

## 原始碼錨點

- 外部 MCP Manager：`internal/mcp/external_manager.go`
- 連線恢復：`internal/mcp/connection_recovery.go`
- MCP 工具適配：`internal/einomcp/mcp_tools.go`
- 外部 MCP Handler：`internal/handler/external_mcp.go`
- 工具呼叫通知：`internal/einomcp/tool_invoke_notify.go`
