# 部署指南

本文說明 JySecAI 的常見部署方式。生產環境部署前，請先閱讀 [安全模型](security-model.md)，確認授權範圍、認證、HITL、審計和高風險功能開關。

## 部署前準備

基礎依賴：

- Go：用於原始碼執行或構建二進位制。
- Python：部分 MCP 服務或工具指令碼需要 Python 執行環境。
- SQLite：預設使用檔案型資料庫，無需單獨服務。
- 安全工具：`tools/` 中的 YAML 只是工具定義，實際命令如 `nmap`、`sqlmap`、`nuclei` 仍需安裝到系統 PATH。
- 模型服務：至少配置一個 `ai.channels` 通道；`provider: openai_compatible` 適用於 OpenAI 相容 API，`provider: claude` 使用 Eino 原生 Claude 元件。

建議目錄：

```text
JySecAI-main/
  config.yaml
  data/
  tools/
  roles/
  skills/
  agents/
  knowledge_base/
```

`data/`、`config.yaml`、自定義 `tools/roles/skills/agents/knowledge_base` 是最重要的持久化內容，升級前應備份。

## 快速啟動

倉庫提供 `run.sh`，適合本地體驗和小規模部署：

```bash
chmod +x run.sh && ./run.sh
```

預設配置中 `server.tls_enabled: true` 且 `tls_auto_self_sign: true`，訪問地址通常是：

```text
https://127.0.0.1:6688/
```

自簽證書會觸發瀏覽器安全提示，這是本地測試的正常現象。生產環境建議配置真實證書。

`run.sh` 是最常用的啟動入口，適合：

- 本機體驗。
- 開發除錯。
- 小團隊臨時內網使用。
- 升級後快速驗證新版是否能啟動。

如果需要長期執行、開機自啟、日誌託管或程序崩潰自動恢復，建議改用 systemd 託管二進位制。

## 原始碼執行

適合開發除錯：

```bash
go run ./cmd/server --config config.yaml
```

如果依賴下載較慢，可以先配置 Go 代理：

```bash
go env -w GOPROXY=https://goproxy.cn,direct
```

## 構建二進位制

```bash
go build -o jysecai ./cmd/server
./jysecai --config config.yaml
```

交付二進位制時仍需要攜帶：

- `web/templates/`
- `web/static/`
- `tools/`
- `roles/`
- `skills/`
- `agents/`
- `config.yaml`

## HTTPS

本地測試可以使用自籤：

```yaml
server:
  tls_enabled: true
  tls_auto_self_sign: true
```

生產環境建議使用證書檔案：

```yaml
server:
  host: 0.0.0.0
  port: 8080
  tls_enabled: true
  tls_cert_path: /etc/letsencrypt/live/example.com/fullchain.pem
  tls_key_path: /etc/letsencrypt/live/example.com/privkey.pem
```

啟用 TLS 後，同埠 HTTP 請求預設會 308 跳轉到 HTTPS。若前面有反向代理負責 TLS，可以關閉應用內 TLS，在代理層處理 HTTPS。

## 反向代理

Nginx 示例：

```nginx
server {
    listen 443 ssl http2;
    server_name jysecai.example.com;

    ssl_certificate /etc/letsencrypt/live/jysecai.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jysecai.example.com/privkey.pem;

    client_max_body_size 200m;

    location / {
        proxy_pass http://127.0.0.1:6688;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
    }
}
```

`proxy_buffering off` 對 SSE 流式輸出和 WebSocket 終端更友好。

## systemd

示例服務：

```ini
[Unit]
Description=JySecAI
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/JySecAI
ExecStart=/opt/JySecAI/jysecai --config /opt/JySecAI/config.yaml
Restart=on-failure
RestartSec=5
Environment=GIN_MODE=release

[Install]
WantedBy=multi-user.target
```

啟用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now jysecai
sudo journalctl -u jysecai -f
```

## 資料與備份

重點備份：

- `config.yaml`
- `data/conversations.db`
- `data/knowledge.db`
- `data/eino-checkpoints/`
- 自定義 `tools/roles/skills/agents/knowledge_base`
- 上傳檔案目錄 `chat_uploads/`

SQLite 熱備份時最好先停止服務，或至少複製 `*.db`、`*.db-wal`、`*.db-shm` 三類檔案。

## 升級

推薦流程：

1. 停止服務。
2. 備份 `config.yaml`、`data/` 和自定義目錄。
3. 拉取或替換新版程式碼/二進位制。
4. 保留原配置，按新版 `config.yaml` 示例補新增欄位。
5. 啟動服務，檢查登入、模型測試、工具列表、知識庫狀態。

倉庫提供 `upgrade.sh`，適合無相容性問題的快速升級；生產環境仍建議先備份再執行。

## 回滾

回滾時同時恢復：

- 上一版本二進位制或程式碼。
- 升級前的 `config.yaml`。
- 升級前的 `data/`。

如果新版已經寫入資料庫結構變更，單獨回滾二進位制可能不夠，建議整體恢復備份。

## 生產部署決策表

| 場景 | 推薦部署 | 關鍵配置 | 不建議 |
| --- | --- | --- | --- |
| 單人本機測試 | `./run.sh` + 自籤 HTTPS | `tls_auto_self_sign: true` | 暴露公網 |
| 小團隊內網 | 二進位制 + systemd + 內網 HTTPS | 強密碼、審計、備份、限制來源 IP | 所有人共用弱密碼 |
| 生產紅隊平臺 | 反向代理 + 獨立執行使用者 + 日誌採集 | 真實證書、反向代理認證、C2 按需啟用 | Web 管理面直連公網 |
| 只做知識庫/對話 | 關閉 C2，禁用不需要的外部 MCP | `c2.enabled: false` | 預設開啟所有高風險模組 |
| 多工具自動化 | 獨立工作目錄 + HITL + 工具白名單 | `workspace_root_dir`、`hitl`、`monitor` | 讓 Agent 擁有全域性 Shell 許可權且免審批 |

## 執行時檔案分層

部署時最容易出問題的是“程式碼、配置、執行資料混在一起”。建議按下面方式理解：

- 可替換：二進位制、`web/`、預設 `tools/roles/skills/agents/docs`。
- 必須保留：`config.yaml`、`data/`、自定義工具/角色/技能/子代理、`knowledge_base/`、`chat_uploads/`。
- 可清理但要謹慎：`data/eino-checkpoints/`、臨時 workspace、舊 payload、舊工具執行記錄。

升級時如果覆蓋整個目錄，應先把自定義目錄和 `data/` 移出或備份。很多“升級後配置丟了”的問題，本質是把執行態檔案當成釋出包的一部分覆蓋掉。

## 啟動後驗收清單

啟動成功不代表可用，至少做下面檢查：

1. 開啟 `/`，確認 HTTPS/反向代理沒有跳轉迴圈。
2. 登入後訪問 `/api/auth/validate`，確認會話可用。
3. 系統設定中執行模型測試。
4. 開啟工具列表，確認 `tools/` 被載入，核心工具 schema 正常。
5. 若啟用知識庫，訪問知識庫頁，確認 `index-status` 正常。
6. 若啟用外部 MCP，檢視外部 MCP 狀態和工具是否出現在對話側。
7. 若啟用 C2，只在授權網路啟動一個測試 listener，並確認停止/刪除正常。
8. 檢視審計頁面，確認登入和配置讀取有記錄。

## 反向代理容易踩的坑

- SSE 被緩衝：表現為 Agent 一直不輸出，結束時一次性吐出。關閉 `proxy_buffering`。
- WebSocket 失敗：終端或事件流異常。檢查 `Upgrade` 和 `Connection` 頭。
- HTTPS 混用：應用內 TLS 和 Nginx TLS 同時啟用時，`proxy_pass` 協議必須匹配。
- 上傳失敗：調大 `client_max_body_size`，並檢查應用側上傳限制。
- 308 迴圈：如果應用啟用同埠 HTTPS 跳轉，而代理又用 HTTP 回源，需要關閉應用 TLS 或改代理回源 HTTPS。

## 原始碼錨點

- 服務組裝和路由：`internal/app/app.go`
- HTTPS 和自簽證書：`internal/app/main_server_tls.go`
- HTTP 到 HTTPS 跳轉：`internal/app/main_server_http_redirect.go`
- 配置結構和預設值：`internal/config/config.go`
- 配置應用邏輯：`internal/handler/config.go`
