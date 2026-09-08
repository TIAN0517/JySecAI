# 安全加固指南

[English](../en-US/security-hardening.md)

本文給出 JySecAI 上線前和持續執行中的安全加固清單。

## 上線前必做

- 首次部署後立即修改 `admin` 初始密碼（Web 介面或平臺許可權 → 使用者管理）。
- 使用 HTTPS，或放在可信反向代理之後。
- 限制來源 IP、VPN 或堡壘機訪問。
- 開啟 `audit.enabled`。
- 不需要 C2 時設定 `c2.enabled: false`。
- 不暴露獨立 HTTP MCP，除非設定強認證和網路隔離。
- 外部 MCP 只接可信服務。
- 備份 `config.yaml`、`data/`、自定義資源目錄。

## 反向代理建議

Nginx 基線：

```nginx
client_max_body_size 200m;
proxy_buffering off;
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

建議額外加：

```nginx
add_header X-Content-Type-Options nosniff;
add_header Referrer-Policy no-referrer;
add_header X-Frame-Options DENY;
```

## HITL 白名單基線

推薦最小白名單：

```yaml
hitl:
  tool_whitelist:
    - read_file
    - glob
    - grep
    - tool_search
```

不要預設加入：

- `execute`
- WebShell 寫入/執行工具
- C2 任務和 payload 工具
- 外部 MCP 高風險工具
- 刪除、寫入、上傳、持久化相關工具

## 檔案許可權

建議：

```bash
chmod 600 config.yaml
chmod 700 data
```

生產環境使用獨立系統使用者執行：

```text
jysecai:jysecai
```

避免 root 執行，除非明確需要繫結低埠或訪問特殊資源。

## 外部 MCP 審查

接入前確認：

- 工具是否能執行命令。
- 是否能讀寫本機檔案。
- 是否會把資料發往第三方。
- 是否有自己的認證。
- 是否會返回不可信網頁或模型內容。
- 是否需要容器隔離。

接入後：

- 高風險工具不進白名單。
- 定期檢查工具列表變化。
- 審計配置變更。

## C2 和 WebShell

C2：

- 預設關閉。
- 演練視窗臨時開啟。
- Listener 埠與管理埠分離。
- 結束後清理 payload、session、task、event。

WebShell：

- 只儲存授權目標。
- 使用清晰命名。
- 寫入/刪除/執行必須審批。
- 專案結束刪除連線。

## 資料保留

建議：

- 審計：30-90 天。
- 工具監控：90-180 天。
- 上傳附件：專案結束清理。
- C2/WebShell 輸出：只保留報告需要的證據。
- 知識庫：不放真實憑證和客戶私密資料。

## 週期巡檢

每週：

- 登入失敗和異常 IP。
- 配置變更。
- 外部 MCP 增刪改。
- 長時間執行工具。
- C2 是否被意外開啟。
- WebShell 連線是否過期。
- 磁碟空間和資料庫大小。

每個專案結束：

- 清理臨時 workspace。
- 刪除無用附件。
- 歸檔必要證據。
- 刪除過期 WebShell/C2 資源。
- 匯出審計記錄。
