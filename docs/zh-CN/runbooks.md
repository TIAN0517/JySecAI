# 運維 Runbooks

[English](../en-US/runbooks.md)

Runbook 是“遇到一個真實任務時照著做”的步驟清單。本文覆蓋 JySecAI 最常見的運維和安全測試操作。

## Runbook 1：生產例項從 0 到可用

適用：內網團隊或生產紅隊平臺首次部署。

如果只是本地或臨時驗證，優先用倉庫自帶指令碼啟動：

```bash
chmod +x run.sh && ./run.sh
```

確認可用後，再決定是否升級為 systemd + 反向代理的長期部署。

### 前置確認

- 執行主機已納入資產管理。
- 訪問路徑確定：內網、VPN、堡壘機或反向代理。
- 有模型 API Key 和允許使用的模型。
- 已決定是否啟用 C2、WebShell、外部 MCP。

### 步驟

1. 準備目錄：

```bash
mkdir -p /opt/JySecAI
```

2. 放置二進位制和資源目錄：

```text
jysecai
web/
tools/
roles/
skills/
agents/
docs/
config.yaml
```

3. 修改關鍵配置：

```yaml
auth:
  session_duration_hours: 12
server:
  host: 127.0.0.1
  port: 8080
  tls_enabled: false
audit:
  enabled: true
c2:
  enabled: false
```

4. 配置反向代理 HTTPS，並限制來源 IP。
5. 使用 systemd 託管程序。
6. 登入 Web，測試模型。
7. 檢查工具列表和審計日誌。
8. 建立備份策略。

### 驗收

- `/api/auth/validate` 登入後返回成功。
- 模型測試成功。
- `tools/` 能正常載入。
- 審計頁面能看到登入事件。
- C2 在不需要時訪問返回禁用狀態。

### 回滾

恢復：

- 上一版二進位制。
- 上一版 `config.yaml`。
- 升級前 `data/`。

## Runbook 2：接入外部 MCP

適用：接入本地工具服務、Burp 輔助服務、資產查詢服務等。

### 前置確認

- MCP 服務可信。
- 明確它是否能讀檔案、寫檔案、執行命令或訪問第三方網路。
- 確定接入方式：stdio、HTTP、SSE。

### 步驟

1. 在外部 MCP 頁面新增服務。
2. 如果是 stdio，填寫命令、引數、工作目錄和環境變數。
3. 如果是 HTTP/SSE，填寫 URL 和認證資訊。
4. 啟動服務。
5. 檢視 `/api/external-mcp/stats`。
6. 檢查工具列表是否出現。
7. 用低風險引數執行一次工具。
8. 把高風險工具排除在全域性免審批白名單之外。

### 驗收

- MCP 狀態為 running。
- 工具 schema 可見。
- Agent 能透過 `tool_search` 找到工具。
- 工具執行記錄出現在監控頁。
- 配置變更出現在審計頁。

### 回滾

- 停止 MCP。
- 刪除外部 MCP 配置。
- 從角色/白名單中移除相關工具。
- 檢查 Agent 當前任務是否仍持有舊上下文。

## Runbook 3：啟用知識庫並調優召回

適用：把內部安全知識、漏洞手冊或測試方法接入 Agent。

### 步驟

1. 修改配置：

```yaml
knowledge:
  enabled: true
  base_path: knowledge_base
  embedding:
    model: text-embedding-v4
  retrieval:
    top_k: 5
    similarity_threshold: 0.4
```

2. 把 Markdown 放入 `knowledge_base/`。
3. 在 Web 知識庫頁面執行掃描。
4. 重建索引。
5. 準備 5 到 10 個固定測試問題。
6. 搜尋並記錄命中情況。
7. 根據結果調 `threshold`、`top_k`、chunk 引數和文件標題。

### 驗收

- `index-status` 顯示索引完成。
- 常見問題能命中正確文件。
- Agent 在不確定時會先查知識庫。
- 檢索日誌能顯示查詢和命中文件。

### 常見回滾

- 關閉 `knowledge.enabled`。
- 恢復舊的 `data/knowledge.db`。
- 降低 `batch_size` 後重新索引。

## Runbook 4：一次授權 Web 測試標準流程

適用：對授權目標做 Web 安全測試。

### 步驟

1. 建立專案，記錄授權範圍。
2. 新建對話，繫結專案。
3. 選擇最小角色，例如“資訊收集”或“Web 應用掃描”。
4. 明確目標、時間視窗、禁止動作。
5. 先執行只讀資訊收集。
6. 發現線索後寫入專案事實。
7. 對高風險驗證請求使用 HITL。
8. 確認漏洞後寫入漏洞管理。
9. 生成攻擊鏈或報告材料。
10. 清理上傳檔案、臨時 workspace 和無用執行記錄。

### 驗收

- 每個漏洞都有證據、影響、復現和修復建議。
- 高風險操作有 HITL 記錄。
- 專案事實能復現測試路徑。
- 報告不包含無關敏感資料。

## Runbook 5：C2 演練結束清理

適用：授權演練中啟用了 C2。

### 步驟

1. 停止所有 listener。
2. 列出 sessions，確認沒有仍線上的授權會話。
3. 匯出必要 task 結果。
4. 刪除 payload 或移動到受控歸檔。
5. 刪除無用 task、event、file。
6. 審計 C2 操作記錄。
7. 將關鍵結果寫入專案事實或報告。
8. 將 `c2.enabled` 改回 false，除非平臺持續需要。

### 驗收

- 無執行中 listener。
- 無待處理 task。
- payload 不再公開可下載。
- 審計與報告能解釋整個生命週期。

## Runbook 6：Agent 不呼叫工具

排查順序：

1. 當前角色是否繫結了該工具。
2. 工具是否在 `/api/config/tools` 中出現。
3. `tool_search` 是否隱藏了該工具。
4. 工具描述是否過短或命名不清。
5. HITL 是否掛起。
6. Agent 是否處於總結/結束階段。
7. 多代理子 Agent 是否有自己的工具限制。

修復方式：

- 把工具加入角色。
- 最佳化 `short_description`。
- 加入 `tool_search_always_visible_tools`。
- 在提示詞中明確什麼時候使用。
- 檢查過程詳情和監控記錄。
