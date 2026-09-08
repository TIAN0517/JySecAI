# 外掛開發

JySecAI 當前倉庫中的外掛主要位於 `plugins/`，已有 **Burp Suite 擴充套件**與 **Chromium 瀏覽器擴充套件** 兩個參考實現。外掛通常透過 HTTP API、MCP 或本地檔案與主應用整合。

## 目錄

```text
plugins/
  README.md
  burp-suite/
    jysecai-burp-extension/
      src/main/java/burp/
      README.md
      README.zh-CN.md
      build.gradle
      pom.xml
  browser-extension/
    jysecai-browser-extension/
      manifest.json
      devtools.js
      background/service-worker.js
      panel/
      popup/
      lib/
      README.md
      README.zh-CN.md
      package.sh
```

## 外掛型別

常見整合方式：

- 瀏覽器或安全工具擴充套件：呼叫 JySecAI API。
- MCP Server：向 JySecAI 暴露新工具。
- 檔案型擴充套件：提供 tools、roles、skills、agents。
- Webhook/機器人：透過平臺回撥與 JySecAI 對話。

## Burp Suite 擴充套件

Burp 外掛目錄包含 Java 原始碼和構建指令碼。典型能力：

- 讀取 Burp 中的 HTTP 請求/響應。
- 格式化訊息。
- 呼叫 JySecAI API。
- 在 Burp 標籤頁展示 AI 分析結果。

構建前確認：

- JDK 可用。
- Gradle 或 Maven 可用。
- JySecAI 服務地址和認證配置正確。

## 瀏覽器擴充套件（Chromium DevTools）

瀏覽器擴充套件目錄為 MV3 DevTools 擴充套件，與 Burp 外掛能力對齊：捕獲 HTTP 流量 → 格式化 Prompt → SSE 流式輸出 AI 結果。完整安裝與 UI 說明見 `plugins/browser-extension/jysecai-browser-extension/README.zh-CN.md`。

典型能力：

- 在 DevTools **Network** 中捕獲 XHR/Fetch（可暫停）。
- 原始 HAR 存記憶體；展示與 AI Prompt 歸一化為 **HTTP/1.1**（與 Burp 一致）。
- 呼叫 JySecAI 登入、Validate、Agent Stream API。
- DevTools 面板展示 Progress / Final；Popup 只讀連線狀態。

構建與載入：

- 無需編譯：`chrome://extensions/` → 載入已解壓 → 選擇 `jysecai-browser-extension/`。
- 打包：`bash package.sh` → `dist/jysecai-browser-extension.zip`。

### 瀏覽器外掛認證最佳實踐

服務端 `POST /api/auth/login` 返回 `{ token, expires_at }`，**無 refresh token**，外掛不應假設 Token 會自動續期。參考實現見 `lib/auth-session.js`、`lib/api.js`、`panel/panel.js`：

| 實踐 | 說明 |
| --- | --- |
| Session 儲存 | Token 與 `expires_at` 存 `chrome.storage.session`（關瀏覽器失效），Password 不落盤 |
| 剩餘時間 | 狀態列顯示 `OK · 剩餘 11h 30m`；剩餘 <30min 警告 |
| 本地檢測 | 每 30s 檢查 `expires_at` 並呼叫 `GET /api/auth/validate` |
| 服務端探測 | 切回 DevTools 面板 / 視窗聚焦時立即探測 |
| 服務不可達 | 顯示「無法連線服務」，不清 Token（便於服務重啟中） |
| 401/403 | 清空 Token、展開連線欄（服務重啟後 session 記憶體清空） |
| Send 前校驗 | 呼叫 `ensureAuthReady()`，避免過期 Token 發起 SSE |
| 按需授權 | `optional_host_permissions`，Validate 時請求目標 origin |

擴充套件過載後 DevTools 面板上下文可能失效：需 **關閉 DevTools → 過載擴充套件 → 再開 F12**。

### 瀏覽器外掛資料與效能邊界

外掛側應設記憶體上限，避免 DevTools 長時間開啟拖垮瀏覽器：

- 捕獲：200 條 / Tab，20 個 Tab 槽；Progress 512KB / run。
- 預設 **XHR/Fetch only** + 靜態資源預過濾；不需要捕獲時用 **已暫停**。
- 大響應走截斷或摘要後再進 Prompt，不要整包塞進訊息。

## API 對接建議

外掛呼叫主應用時：

- 先 `POST /api/auth/login`，再 `GET /api/auth/validate` 確認會話。
- 儲存 `expires_at`，過期後重新登入（無 silent refresh）。
- 優先呼叫 `/api/eino-agent/stream` 或 `/api/multi-agent/stream`（SSE）。
- 大檔案透過 `/api/chat-uploads` 上傳，再在訊息中引用。
- 查詢結果或漏洞可寫入 `/api/vulnerabilities`。
- 專案資訊可寫入 `/api/projects/:id/facts`。

完整介面以 `/api-docs` 為準。

## MCP 外掛

如果外掛的目標是給 Agent 增加工具，優先實現 MCP Server。然後在外部 MCP 管理中接入：

- stdio：本機啟動。
- HTTP/SSE：長期服務。

MCP 工具設計建議：

- schema 明確。
- 引數最小化。
- 輸出結構穩定。
- 錯誤資訊可讀。
- 高風險動作拆成獨立工具，方便 HITL 審批。

## 檔案型擴充套件

外掛也可以交付：

- `tools/*.yaml`
- `roles/*.yaml`
- `skills/<name>/SKILL.md`
- `agents/*.md`

這種方式簡單可靠，適合內部方法論或工具鏈沉澱。

## 釋出檢查

釋出外掛前確認：

- 不包含 API Key、Cookie、目標資訊。
- README 有安裝、配置、解除安裝說明。
- 錯誤提示清晰。
- 與當前 JySecAI API 版本相容。
- 高風險能力有明顯說明。

## 版本相容

外掛應避免依賴未公開的前端內部實現。優先依賴：

- `/api/openapi/spec`
- 穩定 HTTP API。
- MCP 協議。
- 檔案目錄規範。

如果必須依賴內部介面，外掛 README 中應標註相容版本。

## 外掛設計的三個層次

| 層次 | 例子 | 優點 | 代價 |
| --- | --- | --- | --- |
| API 外掛 | Burp / 瀏覽器擴充套件呼叫 Agent Stream | 易實現，適合 UI 整合 | 依賴認證和 API 穩定性 |
| MCP 外掛 | 提供新工具給 Agent | Agent 可主動呼叫 | 需要 schema 和安全設計 |
| 資源包外掛 | 交付 tools/roles/skills/agents | 最簡單，可版本化 | 互動能力弱 |

外掛一開始不必做成 MCP。如果只是“把 Burp / 瀏覽器裡的 HTTP 請求交給 AI 分析”，API 外掛更直接；如果要讓 Agent 主動呼叫 Burp 掃描或查詢結果，再做 MCP。

## API 外掛請求設計

傳送給 Agent 的內容應包含：

- 來源工具和上下文。
- 目標 URL、方法、關鍵 header。
- 請求體和響應體的截斷策略。
- 使用者希望 AI 做什麼。
- 授權邊界。

不要把完整大響應直接塞進訊息。大檔案應走上傳介面或做摘要。

## MCP 外掛 schema 設計

壞 schema：

```json
{"cmd":{"type":"string"}}
```

好 schema：

```json
{
  "target_url": {"type":"string","description":"授權目標 URL"},
  "scan_profile": {"type":"string","enum":["passive","active-safe"]},
  "max_requests": {"type":"integer","description":"最大請求數"}
}
```

schema 越具體，HITL 越容易判斷風險，Agent 也越不容易發散。

## 外掛安全邊界

外掛不要繞過平臺安全控制：

- 不要直接執行本機高風險命令而不暴露給 HITL。
- 不要在外掛內儲存明文長期憑證（Password 僅用於登入，Token 用 session 儲存）。
- 不要預設把目標資料發給第三方服務。
- 不要依賴瀏覽器本地狀態繞過登入。
- 收到 401/403 應清空會話並提示重新認證，不要靜默重試或忽略。

## 原始碼錨點

- Burp 外掛 Java 程式碼：`plugins/burp-suite/jysecai-burp-extension/src/main/java/burp/`
- 瀏覽器擴充套件：`plugins/browser-extension/jysecai-browser-extension/`
  - 認證：`lib/auth-session.js`、`lib/api.js`、`lib/storage.js`
  - 主 UI：`panel/panel.js`
  - 捕獲：`devtools.js`、`background/service-worker.js`
- OpenAPI：`internal/handler/openapi.go`
- 外部 MCP：`internal/handler/external_mcp.go`
- Web 端認證參考：`web/static/js/auth.js`
