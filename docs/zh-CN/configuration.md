# 配置參考

JySecAI 的主配置檔案是 `config.yaml`。大多數配置也可以在 Web 的“系統設定”中修改，儲存後再應用。生產環境中，建議把敏感值放在受控配置系統中，並限制 `config.yaml` 的檔案許可權。

## 基礎配置

```yaml
version: "vX.Y.Z" # 佔位符；請使用 config.example.yaml 中當前釋出版本的值
server:
  host: 0.0.0.0
  port: 8080
  tls_enabled: true
  tls_auto_self_sign: true
  # 可選：其他可信 Web 整合；Chromium 瀏覽器外掛無需配置
  # cors_allowed_origins:
  #   - https://trusted-integration.example
auth:
  session_duration_hours: 12
log:
  level: info
  output: stdout
```

- `version`：前端展示版本。
- `server.host/port`：Web 服務監聽地址和埠。
- `server.tls_*`：HTTPS 配置。生產環境建議使用 `tls_cert_path` 和 `tls_key_path`。
- Chromium 瀏覽器外掛的合法 `chrome-extension://<32位外掛ID>` Origin 會被自動識別，無需配置。外掛仍需按域授權，並使用密碼登入與 Bearer Token 呼叫 API。
- `server.cors_allowed_origins`：僅供其他可信 Web 整合使用的額外 Origin 精確白名單；不支援 `*`，修改後需重啟服務。
- `auth.session_duration_hours`：登入會話有效期（小時）。登入密碼由 RBAC 使用者管理，首次啟動時在控制檯輸出 `admin` 初始密碼。
- `log.output`：可以是 `stdout`、`stderr` 或檔案路徑。

## AI 通道與模型配置

```yaml
ai:
  default_channel: openai-main
  channels:
    openai-main:
      name: OpenAI Main
      provider: openai_compatible
      base_url: https://api.openai.com/v1
      api_key: sk-...
      model: gpt-4.1
      max_total_tokens: 120000
      max_completion_tokens: 16384
      reasoning:
        mode: on
        effort: high
        allow_client_reasoning: true
        profile: openai_compat
    claude-main:
      name: Claude Main
      provider: claude
      base_url: https://api.anthropic.com/v1
      api_key: sk-ant-...
      model: claude-sonnet-4-5
```

`ai` 是推薦的模型配置入口。系統設定頁對應路徑是 **系統設定 → 基本設定 → AI 通道配置**，儲存後寫入 `ai.default_channel` 和 `ai.channels`。舊版 `openai` 欄位仍保留為相容執行時欄位；載入配置時會確保至少有一個預設通道，並把 `ai.default_channel` 解析後的配置同步到執行時 `openai`。

通道欄位：

| 欄位 | 說明 |
| --- | --- |
| `ai.default_channel` | 預設通道 ID。新對話、機器人、批次任務和未顯式選擇通道的請求使用它。 |
| `ai.channels.<id>` | 通道配置。ID 會歸一化為小寫、數字和短橫線，例如 `Qwen_Max` 會變成 `qwen-max`。 |
| `name` | Web UI 展示名。留空時使用通道 ID。 |
| `provider` | `openai_compatible` 或 `claude`。`openai_compatible` 會在執行時對映為 `openai`；`claude` 使用 Eino 原生 Anthropic Messages API。 |
| `base_url/api_key/model` | 必填。Base URL 通常需要包含版本路徑，如 OpenAI/相容閘道器的 `/v1`。 |
| `max_total_tokens` | 上下文壓縮、攻擊鏈構建、多代理摘要等共用的總預算。 |
| `max_completion_tokens` | 單次模型輸出上限；未填時使用預設值。 |
| `reasoning` | 該通道的預設推理擴充套件欄位。不同閘道器支援差異較大，異常時先嚐試 `mode: off`。 |

對話頁的“AI 通道”下拉框會讀取已儲存通道。請求體中的 `aiChannelId` 非空時僅對本次/本會話執行配置生效，不會把 API Key 傳送給模型；為空時跟隨 `ai.default_channel`。

常用操作：

- 新增：點選左側 `+`，填寫必填欄位後儲存。
- 設預設：選中通道後點選“設為預設”，儲存並應用後新請求生效。
- 複製：以當前表單內容建立副本，適合為同一服務商配置不同模型。
- 刪除：預設通道不能作為批次刪除目標；刪除後需保留至少一個通道。
- 探活：單通道“測試連線”或左側“批次探活”會呼叫模型測試介面，適合驗證 Key、Base URL 和模型名。

## Agent

```yaml
agent:
  max_iterations: 12000
  tool_timeout_minutes: 60
  shell_no_output_timeout_seconds: 1200
  workspace_root_dir: ""
  system_prompt_path: ""
```

- `max_iterations`：單代理、多代理主執行器和子代理的預設迭代上限。
- `tool_timeout_minutes`：單次工具最長執行時間。
- `shell_no_output_timeout_seconds`：Shell 長時間無輸出時終止。
- `workspace_root_dir`：會話工作區根目錄，建議不要設定到系統 `/tmp`。
- `system_prompt_path`：單代理系統提示詞覆蓋檔案。

## HITL

```yaml
hitl:
  default_reviewer: audit_agent
  retention_days: 90
  tool_whitelist: [read_file, list_dir, glob, grep, tool_search]
  audit_model:
    provider: ""
    base_url: ""
    api_key: ""
    model: ""
```

- `default_reviewer`：`human` 或 `audit_agent`。
- `tool_whitelist`：全域性免審批工具列表，會與會話白名單合併。
- `audit_model`：審計 Agent 獨立模型；留空複用主模型。
- `audit_agent_prompt` / `audit_agent_prompt_review_edit`：可覆蓋預設審批策略。

更多策略見 [人機協同最佳實踐](hitl-best-practices.md)。

## 多代理

```yaml
multi_agent:
  enabled: true
  robot_default_agent_mode: eino_single
  batch_use_multi_agent: false
  eino_skills:
    disable: false
    filesystem_tools: true
    skill_tool_name: skill
```

支援模式：

- `eino_single`：Eino 單代理。
- `deep`：DeepAgent 風格多代理。
- `plan_execute`：規劃、執行、重規劃。
- `supervisor`：主管代理轉交子代理。

`agents_dir` 指向 Markdown 子代理目錄。單個代理可在 front matter 中設定 `tools`、`bind_role`、`max_iterations`。

## 工具與 MCP

```yaml
security:
  tools_dir: tools
  tool_description_mode: full
mcp:
  enabled: false
  host: 0.0.0.0
  port: 8081
  auth_header: "X-MCP-Token"
  auth_header_value: ""
external_mcp:
  servers: {}
```

- `security.tools_dir`：內建工具 YAML 目錄。
- `tool_description_mode`：`short` 更省 token，`full` 更完整。
- `mcp.enabled`：是否啟動獨立 HTTP MCP 服務。
- `mcp.auth_header_value`：外部呼叫 MCP 時的共享金鑰，生產環境必須設定。
- `external_mcp.servers`：外部 MCP 聯邦配置。

工具 YAML 規則見 `tools/README.md`。

## 知識庫

```yaml
knowledge:
  enabled: false
  base_path: knowledge_base
  embedding:
    provider: openai
    model: text-embedding-v4
    base_url: ""
    api_key: ""
  retrieval:
    top_k: 5
    similarity_threshold: 0.4
  indexing:
    chunk_size: 512
    chunk_overlap: 50
    batch_size: 10
```

啟用後會註冊知識庫檢索工具，並開放管理介面。詳細說明見 [知識庫](knowledge-base.md)。

## 資料庫

```yaml
database:
  path: data/conversations.db
  knowledge_db_path: data/knowledge.db
```

預設使用 SQLite。`knowledge_db_path` 為空時可複用會話資料庫；獨立檔案更便於遷移知識庫。

## 審計與監控

```yaml
audit:
  enabled: true
  retention_days: 15
  max_detail_bytes: 8192
monitor:
  retention_days: 90
```

- `audit` 記錄平臺操作，不記錄對話正文和每次工具呼叫正文。
- `monitor` 管理工具執行記錄保留時間。

## C2、WebShell、專案

```yaml
c2:
  enabled: true
project:
  enabled: true
  fact_index_max_runes: 65000
```

- `c2.enabled`：關閉後不啟動 C2 監聽器，也不註冊 C2 MCP 工具。
- WebShell 連線配置存 SQLite，沒有單獨的主配置開關。
- `project` 控制跨對話事實黑板注入預算。

## 機器人

`robots` 支援個人微信 iLink、企業微信、釘釘、飛書、Telegram、Slack、Discord、QQ。詳細配置步驟見 [機器人使用說明](robot.md)。

## 配置修改建議

- 先在測試環境驗證模型、MCP、知識庫和高風險工具。
- 改動 `tools_dir`、`roles_dir`、`skills_dir`、`agents_dir` 後，檢查 Web 頁面是否能列出對應資源。
- 生產環境避免開啟不需要的 C2、WebShell、終端和外部 MCP。
- 修改敏感配置後，檢查審計頁面是否有異常登入或配置變更記錄。

## 配置應用機制

配置不是所有欄位都同等“熱更新”。`/api/config/apply` 會做一組協調動作：更新模型配置、工具描述模式、重新註冊部分 MCP 工具、初始化或更新知識庫、重啟機器人連線、按配置啟停 C2。這個邏輯在 `internal/handler/config.go` 中由 `ConfigHandler` 協調。

實務判斷：

| 配置段 | 應用後通常立即生效 | 需要額外動作 |
| --- | --- | --- |
| `ai.default_channel` / `ai.channels` | 新請求使用解析後的預設或選定通道 | 舊的流式請求不會被強制切換；前端通道列表需要重新讀取配置 |
| `openai` | 相容欄位；通常由預設 AI 通道同步 | 新配置優先維護 `ai.channels` |
| `agent.max_iterations` | 新 Agent 任務生效 | 已執行任務按啟動時狀態繼續 |
| `security.tool_description_mode` | 工具重新暴露時生效 | 模型已有上下文不會回滾 |
| `hitl.tool_whitelist` | 新工具呼叫審批判斷生效 | 已掛起審批不自動重判 |
| `knowledge.enabled` | 會嘗試初始化/更新元件 | 啟用後仍需掃描和索引 |
| `knowledge.embedding` | 檢索器/索引器配置更新 | 已有向量通常需要重建索引 |
| `robots` | 會觸發連線重啟 | 平臺回撥配置仍需在平臺側正確 |
| `c2.enabled` | 會協調 C2 runtime | 已暴露埠和會話要人工確認 |
| `server.port/tls` | 通常需要重啟程序 | 監聽地址不是普通熱更新 |

## 配置優先順序和派生關係

幾個欄位有“留空複用”的關係：

- `vision.api_key/base_url/provider` 留空時複用 `openai`。
- `hitl.audit_model` 留空時複用預設 AI 通道解析後的 `openai`。
- `knowledge.embedding.base_url/api_key` 留空時複用主模型或 embedding 預設配置。
- `knowledge.retrieval.rerank.base_url/api_key` 留空時複用 embedding/openai。
- `database.knowledge_db_path` 留空時可以複用主會話資料庫，但獨立檔案更利於備份。

這類配置排障時不要只看子配置段，也要看它會回落到哪個上級配置。

## 引數取值建議

| 引數 | 保守值 | 激進值 | 判斷依據 |
| --- | --- | --- | --- |
| `agent.tool_timeout_minutes` | 10-30 | 60+ | 掃描工具是否常跑長任務 |
| `shell_no_output_timeout_seconds` | 300-600 | 1200+ | 工具是否長時間靜默 |
| `knowledge.indexing.batch_size` | 5-10 | 20+ | embedding 服務批次限制 |
| `knowledge.indexing.rate_limit_delay_ms` | 300-800 | 0-100 | 服務商 RPM 和 429 情況 |
| `retrieval.top_k` | 3-5 | 8-12 | 內容質量和上下文預算 |
| `similarity_threshold` | 0.35-0.45 | 0.5+ | 召回優先還是精度優先 |
| `audit.retention_days` | 15-30 | 90+ | 合規要求和磁碟空間 |
| `monitor.retention_days` | 30-90 | 180+ | 是否需要長週期覆盤 |

## 變更前後驗證模板

修改配置前記錄：

```text
變更目的：
涉及配置段：
預期影響：
回滾方式：
驗證介面：
```

修改後驗證：

```bash
curl -k https://127.0.0.1:6688/api/auth/validate \
  -H "Authorization: Bearer <token>"
```

再按配置型別驗證模型、工具、知識庫、C2 或機器人。不要只看 Web 儲存成功提示。

## 原始碼錨點

- 配置結構：`internal/config/config.go`
- 環境變數展開：`internal/config/envexpand.go`
- Web 配置介面：`internal/handler/config.go`
- 路由註冊：`internal/app/app.go`
- C2 配置協調：`internal/app/c2_lifecycle.go`
