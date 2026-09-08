# API Recipes

[English](../en-US/api-recipes.md)

本文給出外部指令碼或外掛常用的 API 呼叫配方。完整欄位以 `/api-docs` 和 `/api/openapi/spec` 為準。

## Recipe 1：登入並驗證

```bash
curl -k https://127.0.0.1:6688/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"<password>"}'
```

後續請求推薦使用：

```bash
Authorization: Bearer <token>
```

驗證：

```bash
curl -k https://127.0.0.1:6688/api/auth/validate \
  -H "Authorization: Bearer <token>"
```

## Recipe 2：建立對話併傳送訊息

最簡單方式是不先建立空對話，直接呼叫 Agent：

```bash
curl -k https://127.0.0.1:6688/api/eino-agent \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"對 127.0.0.1 做授權的基礎資訊收集，只做只讀操作"}'
```

如果需要先建立對話：

```bash
curl -k https://127.0.0.1:6688/api/conversations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Web 測試"}'
```

然後把返回的 `conversationId` 放入 Agent 請求。

## Recipe 3：流式呼叫 Agent

```bash
curl -k -N https://127.0.0.1:6688/api/eino-agent/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"總結當前專案事實並列出下一步，只讀"}'
```

注意：

- `-N` 禁用 curl 緩衝。
- 反向代理也要關閉 buffering。
- 收到 `done` 才算本輪結束。

## Recipe 4：呼叫多代理

```bash
curl -k -N https://127.0.0.1:6688/api/multi-agent/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"對授權目標做分階段 Web 安全測試，先規劃再執行只讀步驟",
    "orchestration":"plan_execute"
  }'
```

可選 `orchestration`：

- `deep`
- `plan_execute`
- `supervisor`

## Recipe 5：上傳附件

```bash
curl -k https://127.0.0.1:6688/api/chat-uploads \
  -H "Authorization: Bearer <token>" \
  -F "file=@./request.txt"
```

大檔案建議上傳後在訊息中引用，不要直接塞進 prompt。

## Recipe 6：寫入漏洞

```bash
curl -k https://127.0.0.1:6688/api/vulnerabilities \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"示例 SQL 注入",
    "severity":"high",
    "target":"https://example.com/item?id=1",
    "description":"引數 id 存在可驗證 SQL 注入",
    "evidence":"只讀驗證輸出...",
    "remediation":"使用引數化查詢"
  }'
```

欄位以 OpenAPI 為準。

## Recipe 7：查詢知識庫

```bash
curl -k https://127.0.0.1:6688/api/knowledge/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query":"SQL 注入如何判斷欄位數",
    "riskType":"SQL Injection",
    "topK":5,
    "threshold":0.4
  }'
```

如果結果為空，先呼叫 categories 看風險型別名稱是否匹配。

## Recipe 8：檢查外部 MCP 狀態

```bash
curl -k https://127.0.0.1:6688/api/external-mcp/stats \
  -H "Authorization: Bearer <token>"
```

如果服務 running 但 Agent 找不到工具，檢查角色工具限制和 `tool_search`。

## Recipe 9：獲取工具 schema

```bash
curl -k https://127.0.0.1:6688/api/config/tools/nmap/schema \
  -H "Authorization: Bearer <token>"
```

外掛或自動化指令碼應根據 schema 構造引數，不要猜欄位名。

## Recipe 10：匯出審計日誌

```bash
curl -k "https://127.0.0.1:6688/api/audit/logs/export" \
  -H "Authorization: Bearer <token>" \
  -o audit.csv
```

匯出檔案可能包含敏感操作資訊，應加密儲存。

## Recipe 11：批次匯入資產

先準備 `assets.json`：

```json
{
  "source": "api-import",
  "source_query": "cmdb-export-2026-07",
  "assets": [
    {
      "domain": "app.example.com",
      "port": 443,
      "protocol": "https",
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

提交：

```bash
curl -k https://127.0.0.1:6688/api/assets/import \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  --data-binary @assets.json
```

返回示例：

```json
{"created":2,"updated":0,"skipped":0}
```

注意：

- 呼叫者需要 `asset:write` 許可權。
- 每條資產至少填寫 `host`、`ip` 或 `domain`。
- 單次最多 100000 條；大批次請求建議使用檔案配合 `--data-binary`，不要把 JSON 直接寫進命令列。
- 已存在的“目標 + 埠 + 協議”會合並更新並計入 `updated`。
- 如需從 XLSX/CSV 操作，使用 Web 端 **資產庫 → 批次匯入**；介面本身接收 JSON，不接收 multipart 檔案。
