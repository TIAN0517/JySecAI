# 第二輪審計發現 — 2026-10-07

> 本檔記錄第二輪盤點的發現。分兩部分：
> **A. 主審計者（Claude）親自查證** — 已完整驗證證據鏈
> **B. 專項審計助手回報** — 待交叉驗證後併入
>
> 分支：`fix/audit-20261002` · 基準：`main` @ `bf7eaa8`

---

## A. 主審計者查證（§3 第 4 項：資源耗盡 / 網路層）

### [嚴重度 高] F1 — 速率限制可被 `X-Forwarded-For` 偽造完全繞過

**位置**：`internal/app/app.go:90`

```go
router := gin.Default()
```

全專案**沒有任何 `SetTrustedProxies` 呼叫**（已 grep 確認）。

gin v1.9.1 的預設值（`gin@v1.9.1/gin.go:205`）：

```go
trustedProxies: []string{"0.0.0.0/0", "::/0"},
```

即**信任所有 proxy**。`Context.ClientIP()`（`gin@v1.9.1/context.go`）在
`isTrustedProxy(remoteIP)` 為真時直接回傳 `X-Forwarded-For` 的值 ——
而因為 CIDR 是 `0.0.0.0/0`，任何來源 IP 都被視為 trusted。

**可利用性**：攻擊者對每個請求設定不同的 `X-Forwarded-For`，即可讓
`RateLimitMiddleware` 認為每次都是新 IP。**不需要任何前置條件。**

**影響範圍**（`grep RateLimitMiddleware` 全專案僅兩處）：

| 位置 | 限制 | 繞過後的後果 |
|---|---|---|
| `app.go:925` `POST /api/auth/login` | 10 次/分 | **密碼暴力破解完全不受限** |
| `app.go:938` `robotGroup.Use(...)` | 60 次/分 | 見 F2，無上限 body 讀取變得完全可利用 |

**連帶影響**：`internal/audit/service.go:165` 與
`internal/audit/conversation_create.go:50` 都以 `c.ClientIP()` 記錄來源 IP。
該值可被攻擊者任意偽造 → **稽核紀錄的 IP 欄位不可用於取證**。

**建議修法**：明確設定 `router.SetTrustedProxies(...)`。
若實際部署確實在反向代理後，應設為**該代理的實際 IP/CIDR**，
而不是預設的 `0.0.0.0/0`；純直連部署應設為 `nil`（完全信任 `RemoteAddr`）。

> ⚠️ 注意：這一項會讓稽核紀錄的來源 IP 從「可偽造」變成「真實」，
> 屬於修護而非行為改變。但它需要新增 `ServerConfig.trusted_proxies` 設定欄位，
> 且**部署在反向代理後的既有環境必須填對**，否則所有 IP 都會變成 proxy 的 IP。
> 不能猜預設值 —— 要先確認 `docs/en-US/security-hardening.md` 描述的部署形态。

---

### [嚴重度 高（條件式）] F2 — 免認證端點無上限緩衝請求 body

**位置**：`internal/handler/robot.go:1562`

```go
func (h *RobotHandler) HandleWecomPOST(c *gin.Context) {
	if !h.config.Robots.Wecom.Enabled { ... }
	...
	// 先读取请求体，后续解析/签名验证都会用到
	bodyRaw, err := io.ReadAll(c.Request.Body)   // ← 無上限
	...
	h.logger.Debug("企业微信 POST 收到请求", zap.String("body", string(bodyRaw)))  // ← 認證前寫日誌
	// 驗證簽章在 ~1571 之後才發生
```

**端點認證狀態**：`app.go:934` 的註解明寫「机器人回调（**无需登录**）」。
`robotGroup` 掛在 `api` 上，**不是**掛在有 `AuthMiddleware` 的 `protected` 上。
唯一防線是 `RateLimitMiddleware`（60/分）—— 而 F1 使該防線失效。

**攻擊鏈**：F1 繞過限流 → 任意大的 POST body 被完整緩存在記憶體 → OOM。

**次要問題**：第 1567 行在**簽章驗證之前**把整個攻擊者控制的 body 寫進
Debug 日誌。若啟用 Debug 記錄，等於讓未認證的攻擊者往日誌檔寫入任意內容
（日誌注入 / 磁碟耗盡）。

**前提條件**：`robots.wecom.enabled: true`。
`config.example.yaml:486` 預設為 `false`，且 `ValidateWecomConfig`
（`config.go:702`）要求啟用時必須設定 token。**故預設安裝不可利用**，
但任何啟用企業微信整合的部署都完全暴露。

**同型但需認證**：`internal/mcp/server.go:272` 與 `:299` 的
`io.ReadAll(r.Body)` 無上限，但在 `mcpHandlerWithAuth` 之後。

**已排除**：其餘 `io.ReadAll` 皆非接收端——
`fofa.go` / `webshell.go` / `knowledge/rerank_http.go` / `openai/openai.go` /
`robot/ilink` 讀的是**對外請求的回應**；`llm/deepseek_anthropic_compat.go` 與
`openai/reasoning_tool_choice_compat.go` 是 **RoundTripper**，
讀的是 app 自己組裝、要送出的請求。

---

### [嚴重度 中] F3 — 主 HTTP server 與 MCP server 完全沒有逾時設定

**位置**：`internal/app/app.go:676`（主 server）、`:661`（MCP server）

```go
srv := &http.Server{Addr: addr, Handler: a.router}
mcpServer = &http.Server{Addr: mcpAddr, Handler: mux}
```

`ReadTimeout` / `ReadHeaderTimeout` / `WriteTimeout` / `IdleTimeout` /
`MaxHeaderBytes` **全部未設定**。Go 的零值代表不設限。

**對照**：同一個專案的 C2 listener 已經設了完整逾時
（`internal/c2/listener_http.go:103-106`：15s / 60s / 120s / 300s）。
**模式在這個 codebase 是已知的，但最大的攻擊面反而漏了。**

**可利用性**：Slowloris — 攻擊者慢慢送標頭，每個連線佔住一個 goroutine 與 fd
且永不釋放；`IdleTimeout` 未設使 keep-alive 連線也不會被回收。

**緩解因素**：`docs/en-US/security-hardening.md` 建議部署在反向代理之後，
代理可能會設逾時。但這不能取代應用層防禦。

**修復時的取捨（尚未實施，需注意）**：
- `ReadHeaderTimeout`（15s）— 安全的 Slowloris 完整緩解
- `IdleTimeout`（300s）— 安全
- `MaxHeaderBytes`（1MB）— 安全，Go 預設即為 1MB
- ⚠️ `WriteTimeout` — **不可直接套用**：主伺服器提供 AI SSE 長串流，
  會被硬生生砍斷
- ⚠️ `ReadTimeout` — **不可直接套用**：知識庫上傳有大型 body 的正當需求

---

### [嚴重度 低] F4 — 簽章驗證失敗時把「期望簽章」寫入日誌

**位置**：`internal/handler/robot.go:1431`

```go
h.logger.Warn("企业微信 URL 验证签名失败",
    zap.String("expected", msgSignature), zap.String("got", signature))
```

`expected` 是由 token 推導出的**有效簽章值**，以 Warn 等級寫入日誌。
若日誌被轉送到存取控制較鬆散的位置，等於洩漏簽章推導中間值。
建議只記錄「驗證失敗」與來源，不記錄期望值。

> 已於 PR #8 的稽核脫敏修正中一併強化：`signature` 現在列入
> `internal/audit/sanitize.go` 的敏感詞，`signature_algorithm` 這類
> 描述性欄位則保留（見 §D）。

---

### [嚴重度 高（自我審計）] F5 — 稽核脫敏過度遮蔽，把紀錄的核心價值毀掉

**位置**：`internal/audit/sanitize.go`（PR #8 commit `c05716a8` 引入）

第一輪修復把敏感詞從「寬泛詞」收斂成一份子字串清單：

```go
var sensitiveKeySubstrings = []string{
    "password", "secret", "token", "credential", ...
}
```

收斂的方向是對的，但**子字串比對本身有致命副作用**，而且方向完全相反。

實測（`tools/redact_probe`，本輪新增）顯示，這份清單會把下列欄位全部遮成 `***`：

```
max_tokens   prompt_tokens   completion_tokens   total_tokens
token_count  tokens_used     token_usage         tokenizer
token_type   token_id        secret_count        credential_type
```

**對一個 LLM 平台，token 用量就是成本稽核與計費對帳的第一手資料。**
把 `max_tokens` 遮掉，等於把稽核紀錄最核心的內容連同稽核本身一起摧毀 ——
紀錄還在，但已經沒有價值。這正是該函式自己註解宣稱要避免的事。

**修法**：改成「**完整 segment 比對 + 明確的計量豁免**」：

| 層 | 規則 | 效果 |
|---|---|---|
| 1 | 單詞敏感詞以完整 segment 比對 | `tokenizer` ≠ `token`；`sort_key` ≠ 機密 |
| 2 | 複合詞（`api_key`、`master_key`…）以右側詞邊界比對 | `api_keyword` ≠ `api_key` |
| 3 | 欄位名含計量詞時不遮 | `token_count` 保留、`access_token` 仍遮 |

**關鍵設計取向**：未列入豁免的未知欄位一律遮罩。判斷錯誤時的預設方向是
「多遮」而不是「漏遮」，這是脫敏函數唯一合理的失敗模式。

**豁免條款為什麼不會變成繞過點**：已逐處確認稽核 `Detail` 的鍵全部是程式碼裡
的字面值（`internal/audit`、`internal/handler` 全部 10 處 `Detail:` 欄位），
**沒有任何由請求內容反序列化而來的鍵**。攻擊者無法藉由命名欄位來騙過豁免。

**突變測試 M17–M27（11 個，全攔下）**證明每一層都有測試釘住。其中
**M21 找出一段真正的冗餘**：原本「詞邊界也檢查左側」的寫法，
拿掉後整組測試沒有任何一條會紅，而且它會讓 `myapi_key` 這類真憑證漏遮 ——
所以刪掉它反而是**增強**。

---

## B. 專項審計助手回報

> 待 5 個助手（RBAC / SQL / 檔案 I/O / 工具授權 / 認證與洩漏）回報後併入。
> 所有回報都必須經過交叉驗證才採信 —— 第一輪曾有審計發現是錯的
> （`/vulnerabilities/:id` IDOR 已在 PR #8 撤回）。

---

## C. 額外觀察（非漏洞，但影響面值得記錄）

### C1 — `internal/handler` 被排除在 CI 外 = 43,195 LOC 零 CI 覆蓋

`internal/handler` 有 103 個原始檔、43,195 LOC、38 個測試檔，
卻因 6 個既有失敗被排除在 CI 的 `go-test` job 之外。

其中 4 個失敗（`TestCreateProgressCallback_*` × 3、`TestEnrichHitlApprovalPayload`）
是 **Windows 專屬的測試衛生問題**：建立 SQLite 後沒有 `defer db.Close()`，
Windows 上 `t.TempDir()` 的 RemoveAll 會因檔案句柄未釋放而失敗。
Linux 上不會發生。補上 `defer db.Close()` 即可。

剩下 2 個是**真實缺陷**：
- `TestEnsureSchemaFinalizesOnlyHistoricalPlaceholdersWithTerminalEvidence`
- `TestToolGuardSavePersistsAndAppliesWithoutChangingHITL`
  （tool guard YAML 往返遺失權限與註解，已在 PR #8 記錄）

修好這 6 項即可讓 43k LOC 重新獲得 CI 保護。建議列為高優先工作。

### C2 — `NewRateLimiter` 每個實例洩漏一個永不結束的 goroutine

`internal/security/ratelimit.go:33` 的 `go rl.cleanup()` 內是
`for range ticker.C`，沒有停止機制。目前只在啟動時建立有限幾個，
影響有限，但若日後改為動態建立會累積。

### C3 — WebSocket 面已確認無問題

全 repo 僅兩個升級點，兩者都有 `SetReadLimit`
（C2 `listener_websocket.go:151` 為 64MB、terminal `terminal_ws_unix.go:78`
為 64KB）。Windows 變數 `terminal_ws_windows.go` 直接回 501，不做升級。
**已查證，非遺漏。**

### C4 — CI 排除清單已實測：`internal/logger` 可以拿回來

以 `ci/exclusion-check` 分支實跑 GitHub Actions（run `37567963574`）確認：

| 套件 | Linux runner 結果 | 結論 |
|---|---|---|
| `internal/logger` | `ok jysecai/internal/logger 0.010s` | **排除是過度保守，應移出清單**（+290 LOC 獲得 CI 覆蓋） |
| `internal/security` | 僅 `TestEinoStreamingShell_SudoFailsFast` 失敗 | runner 以 root 執行，`sudo` 成功而非失敗 → **環境造成，非產品缺陷** |

`internal/security` 那項**不可用 skip 掩蓋**（紅線明令禁止）。
正解是讓測試在非 root 環境下斷言、或改用不依賴 `sudo` 的注入點，
讓它在任何權限下都有明確意義 —— 屬於「修」不是「藏」。

---

## D. 五個專項審計助手的回報 — 已由主審計者逐項複驗

> 交叉驗證是硬規則：第一輪曾有「發現」是錯的（`/vulnerabilities/:id` IDOR 已撤回）。
> 下列 **D1–D7 全部由主審計者重新讀原始碼確認為真**，每項都附複驗過的證據。
> §E 之後是「回報但尚未複驗」，**不可直接動工**。

### [嚴重度 高] D1 — `GET /api/config` 明文回傳 API 金鑰給**任何登入者**

**位置**：`internal/app/app.go:1080`、`internal/handler/config.go:374-390`、
`internal/config/config.go:881-890`

```go
// app.go:1080 —— protected 群組有 AuthMiddleware，但這個端點沒有 RequirePermission
protected.GET("/config", configHandler.GetConfig)
```

```go
// config.go:376-384 —— 直接回傳原始設定物件
AI:         h.config.AI,
OpenAI:     h.config.OpenAI,     // ← 含 APIKey
FOFA:       h.config.FOFA,
Shodan:     h.config.Shodan,
```

```go
// config.go:883 —— json tag 沒有任何遮罩處理
APIKey string `yaml:"api_key" json:"api_key"`
```

**複驗結果**：確認。`protected` 群組掛了 `AuthMiddleware` +
`RBACMiddlewareWithDenyHook`，但 `/config` 本身**沒有 `RequirePermission`**，
因此**任何角色、任何登入者**都能取得明文 `api_key`。

**這是 PR #8 的漏網**。該輪已為 C2 與 Robots 做了 `C2.Public()` / `Robots.Public()`
清洗（見 `internal/config/robots_public.go`），但同樣的處理沒有套用到
`OpenAI` / `AI` / `FOFA` / `Shodan` / `ZoomEye` / `Quake` / `MCP`。
修法模式**已經在 repo 裡**，照著做即可。

---

### [嚴重度 高] D2 — 人機協同（HITL）可由發起者自己在請求內關閉

**位置**：`internal/handler/hitl.go:304-308`、`:618-631`、
`internal/handler/eino_single_agent.go:109` / `:440`、`multi_agent.go:126` / `:459`

```go
// hitl.go:304
func (m *HITLManager) ActivateConversation(conversationID string, req *HITLRequest) {
	if req == nil || !req.Enabled {
		m.DeactivateConversation(conversationID)   // ← 客戶端送 enabled:false 走這裡
		return
	}
```

```go
// hitl.go:620-627 —— 只有 req 為 nil 才會去撈資料庫設定
if req == nil {
	cfg, err := h.loadHITLConversationConfig(conversationID)
	if err == nil { req = cfg }
}
```

**複驗結果**：確認。`ChatRequest.Hitl` 是客戶端 JSON（`json:"hitl,omitempty"`），
而 `hitlRequestWithMergedConfigWhitelist`（`hitl.go:361-386`）**只合併工具白名單，
不會把 `Enabled` 翻回 true**。因此送 `{"hitl":{"enabled":false}}` 會讓
`shouldInterrupt`（`hitl.go:388-395`）在 runtime map 找不到 key 而直接回傳 `false`
→ 不審批直接執行工具。

**修法方向**：啟用狀態改由伺服器端決定；請求內的 `hitl` 欄位只允許「收緊」
（提高敏感度），不允許「放寬」。這是**產品政策決定**，需先確認預設語意。

---

### [嚴重度 高] D3 — `DELETE /api/skills/:name` 可遞迴刪除任意目錄

**位置**：`internal/handler/skills.go:448-463`

```go
skillName := c.Param("name")
if skillName == "" { ... }              // ← 唯一的檢查
skillDir := filepath.Join(h.skillsRootAbs(), skillName)
if err := os.RemoveAll(skillDir); ...   // ← 無路徑約束
```

**複驗結果**：確認，且**同一個 handler 裡已有正確的驗證函式** ——
`isValidSkillName`（`skills.go:700`，只允許 `[a-z0-9-]`）只被 `CreateSkill`
（`skills.go:337`）呼叫，`DeleteSkill` 是唯一沒用的破壞性端點。

`:name=..` 可刪掉整個 config 目錄（`config.yaml`、`roles/`、`skills/`）；
Windows 上 `..%5c..%5c` 可留在單一 URL segment 內，被 `filepath.Join` 清理成
多層穿越。

**修法**：`DeleteSkill` 開頭加 `isValidSkillName`，`os.RemoveAll` 前再以
路徑約束二次確認。**零歧義，可直接修。**

---

### [嚴重度 高] D4 — 知識庫 `category` / `title` 未驗證 → 知識庫根外任意檔案寫入

**位置**：`internal/knowledge/manager.go:603`（Create）、`:644`/`:654`（Update）、
`:703`/`:718`（Delete）

```go
filePath := filepath.Join(m.basePath, category, title+".md")  // ← 無任何驗證
os.MkdirAll(filepath.Dir(filePath), 0755)
os.WriteFile(filePath, []byte(content), 0644)
```

**複驗結果**：確認。兩個欄位只經過 `binding:"required"`（僅檢查非空），
沒有 `filepath.Clean` / `IsAbs` / `Rel` / 前綴比對 / `Lstat`。
對照組：`internal/c2/manager.go:804` 的 `ensurePathInDir` 明確擋掉絕對路徑與
`..` 前綴 —— 知識庫這條路徑**沒有等價防線**。

`UpdateItem` 還會 `os.Rename` 把既有檔案搬走，`DeleteItem` 對 DB 記錄的路徑做
`os.Remove` 並刪空目錄。

**修法**：沿用既有的單段名稱白名單（`isValidSkillName` 的模式），或一律以
路徑約束解析後才寫入。

---

### [嚴重度 高] D5 — 工作流的 `tool` 節點完全沒有 HITL

**位置**：`internal/workflow/nodes.go:77`、`internal/handler/workflow_integration.go`

```go
// nodes.go:77 —— 直接呼叫，繞過所有 ToolMiddleware
result, err := args.Agent.ExecuteMCPToolForConversation(ctx, args.ConversationID, toolName, toolArgs)
```

**複驗結果**：確認。`WithHITLToolInterceptor` 在 `workflow_integration.go`
**零命中**。HITL 是以 Eino `ToolMiddleware` 形式掛載的，而 workflow 的 tool
節點直接呼叫 Agent，**不經過 middleware 鏈**。`nodes.go` 裡的 `case "hitl"`
只是讓圖作者**手動放置**的審批節點；`validation.go` 從不要求 `tool` 節點前
必須有 `hitl` 節點。

**已確認仍有的防線**：這條路徑的 RBAC 與 toolguard 都在（`CallTool` 內的
authorizer 與 `checkToolGuard`），所以**缺的只有人工這一關**，不是全面繞過。

---

### [嚴重度 高] D6 — 子代理工具清單覆寫父代理的角色限制

**位置**：`internal/multiagent/runner.go:197`（參數定義於 `runner.go:76`）、
`internal/agent/agent.go:324`

```go
// runner.go:76  —— 函式參數
roleTools []string,

// runner.go:197 —— 遮蔽了上面的參數
roleTools := sub.RoleTools
subDefs := ag.ToolsForRole(roleTools)   // ← 只用子代理自己的清單
```

**複驗結果**：確認。子代理**完全沒有**把父代理的 `roleTools` 拿進來做交集。
`agent.go:324` 的 `if len(roleToolSet) > 0` 表示**空清單 = 全部工具**。
因此 `role_tools` 留空且未綁角色的子代理會拿到完整工具目錄，
父代理被剝奪的工具它都能叫。

**修法**：子代理可用工具 = 父代理允許集合 ∩ 子代理宣告集合。**零歧義。**

---

### [嚴重度 高] D7 — 速率限制可被 `X-Forwarded-For` 偽造繞過（= §A F1）

已於 §A F1 完整記錄，此處不重複。**複驗確認**：全專案零 `SetTrustedProxies` 呼叫。

---

## E. 回報但尚未複驗 —— 動工前必須先自己確認

| 項目 | 回報者 | 備註 |
|---|---|---|
| skills 檔案讀取 `:name` 未驗證 → 設定外洩 | fileio-audit | 走 `internal/skillpackage/layout.go` + `io.go:88-107`，與 D3 同型，很可能是真的 |
| 保留單輪 SHA-256 舊密碼驗證分支 | authleak-audit | 回報者自己標為**條件式**：已確認全樹沒有任何寫入 `sha256$` 格式的程式碼 |
| 登入回應時間差可列舉帳號 | authleak-audit | 需精準計時，實務影響被 D7 淹沒 |
| 初始管理員密碼明文寫 stdout、無強制變更旗標 | authleak-audit | 無硬編碼預設密碼（這點是好的） |
| `NewRateLimiter` goroutine 洩漏 | 主審計者 | 見 §C C2 |

> 複驗發現回報有誤時**必須明確撤回**並在本檔記錄，不要默默不寫。
> 第一輪的 `/vulnerabilities/:id` IDOR 就是這樣被擋下來的。

---

## F. 基礎設施事件（非專案缺陷，但影響所有人）

2026-10-07 約 11:52，`D:\AI` 子樹被**整批刪除**（`security`、`deploy`、`portal`、
`dealers`、`gateway`、`tin888`、`Ollama`、`worktrees`、`Workspaces` 全部消失），
12:00 起有程序開始還原。

`fileio-audit` 的鑑識結果：

- **非磁碟故障** — `chkdsk D:` 唯讀掃描 754,136 檔案記錄，**0 bad file records**
- **非回收筒** — D 槽無 `$Recycle.Bin`
- **無備份可還原** — `wbadmin` 無備份；**D 槽無 VSS 陰影副本**（僅 C 槽有 10/3、10/6 兩份）

即這是一次**不可從快照復原的直接刪除**。`D:\AI\deploy` 的營運紀錄
（`deploy/*/REPORT.md`）至今仍未回來。

**教訓**：D 槽目前**沒有任何備份**。所有工作只推上 GitHub 才算安全。

---

---

**維護規則：本檔記載的發現、證據或未修理由有變更時，須在同一變更中更新本檔。**