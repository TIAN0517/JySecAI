# 配置畫像

[English](../en-US/configuration-profiles.md)

本文給出幾套常用配置畫像。它們不是完整 `config.yaml`，而是部署時最容易影響安全和可用性的關鍵段落。

## 本地開發畫像

目標：方便除錯，允許較多本地能力。

常用啟動：

```bash
chmod +x run.sh && ./run.sh
```

```yaml
server:
  host: 127.0.0.1
  port: 8080
  tls_enabled: true
  tls_auto_self_sign: true
auth:
  session_duration_hours: 12
audit:
  enabled: true
  retention_days: 7
c2:
  enabled: false
multi_agent:
  enabled: true
  eino_skills:
    filesystem_tools: true
```

適用：

- 本地功能開發。
- 除錯前端和 Handler。
- 除錯 Skills、本地檔案工具。

不適用：

- 多人共享。
- 公網訪問。

## 內網團隊畫像

目標：團隊共享，保留審計，限制高風險能力。

```yaml
server:
  host: 127.0.0.1
  port: 8080
  tls_enabled: false
auth:
  session_duration_hours: 12
audit:
  enabled: true
  retention_days: 30
monitor:
  retention_days: 90
c2:
  enabled: false
mcp:
  enabled: false
hitl:
  default_reviewer: human
  tool_whitelist: [read_file, glob, grep, tool_search]
```

配合：

- Nginx/Traefik 終止 HTTPS。
- 反向代理 IP 白名單。
- 定期備份 `data/`。

## 只啟用知識庫畫像

目標：把 JySecAI 作為知識增強助手，儘量關閉攻擊面。

```yaml
c2:
  enabled: false
mcp:
  enabled: false
knowledge:
  enabled: true
  base_path: knowledge_base
  retrieval:
    top_k: 5
    similarity_threshold: 0.4
multi_agent:
  eino_skills:
    filesystem_tools: false
```

建議：

- 角色只繫結知識庫和只讀工具。
- 禁用外部 MCP。
- 不儲存真實客戶敏感材料。

## 高審計生產畫像

目標：生產紅隊或長期安全平臺。

```yaml
auth:
  session_duration_hours: 8
audit:
  enabled: true
  retention_days: 90
  max_detail_bytes: 8192
monitor:
  retention_days: 180
hitl:
  default_reviewer: human
  retention_days: 180
  tool_whitelist: [read_file, glob, grep, tool_search]
c2:
  enabled: false
multi_agent:
  eino_callbacks:
    enabled: true
    mode: log_only
    sse_trace_to_client: false
```

配合：

- 反向代理認證。
- 獨立執行使用者。
- 日誌採集。
- 備份加密。
- 明確專案結束清理流程。

## C2 演練畫像

目標：只在授權演練視窗臨時啟用 C2。

```yaml
c2:
  enabled: true
hitl:
  default_reviewer: human
  tool_whitelist: [read_file, glob, grep, tool_search]
audit:
  enabled: true
monitor:
  retention_days: 180
```

操作要求：

- 演練前確認授權範圍。
- Listener 埠和 Web 管理埠分離。
- 演練結束執行 C2 清理 Runbook。
- 結束後恢復 `c2.enabled: false`。

## 外部 MCP 自動化畫像

目標：接入可信的內部工具服務。

```yaml
external_mcp:
  servers: {}
multi_agent:
  eino_middleware:
    tool_search_enable: true
    tool_search_min_tools: 20
hitl:
  default_reviewer: audit_agent
  tool_whitelist: [read_file, glob, grep, tool_search]
```

建議：

- 每個 MCP 工具都寫清楚 schema。
- 高風險 MCP 工具不進白名單。
- stdio MCP 用獨立工作目錄。
- HTTP MCP 必須有認證。

## 畫像選擇決策

| 需求 | 選擇 |
| --- | --- |
| 單人開發 | 本地開發畫像 |
| 多人內網使用 | 內網團隊畫像 |
| 文件/知識問答 | 只啟用知識庫畫像 |
| 長期生產平臺 | 高審計生產畫像 |
| 授權 C2 演練 | C2 演練畫像 |
| 接內部工具平臺 | 外部 MCP 自動化畫像 |
