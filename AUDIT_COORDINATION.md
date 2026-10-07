# 審計協調地圖 — JySecAI

> 這份文件的唯一目的：**讓多個並行助手在同一個 repo 上工作時不會互相踩踏。**
> 開工前先讀這裡；完成後請更新「地盤登記表」。
>
> 最後更新：2026-10-07 · 撰寫者：Claude（第一輪修復 + 第二輪盤點）

---

## 0. 目前分支狀態

| 項目 | 值 |
|---|---|
| 工作分支 | `fix/audit-20261002` |
| PR | [#8](https://github.com/TIAN0517/JySecAI/pull/8) |
| base | `main` @ `bf7eaa8` |
| CI | `go-test` / `frontend-test` / `build-linux` 全綠 |
| 工作區 | 乾淨 |
| 第二輪發現 | [`AUDIT_FINDINGS_20261007.md`](AUDIT_FINDINGS_20261007.md) |

**已完成的第一輪（5 個 commit，不要重做）：**

| Commit | 主題 |
|---|---|
| `11975ff` | 停止經 API 回傳機器人憑證與 WebShell 密碼 |
| `60b7491` | 機密欄位落盤加密（AES-256-GCM + `JY_SECMASTER_KEY`） |
| `8923d35` | C2 三項強化（XSS、符號連結、明文 beacon 需顯式開啟） |
| `c05716a` | 稽核脫敏修正 + CI 從單套件擴充到全專案 |
| `fe94771` | 不再把主金鑰交給任何子行程 |

**第二輪（2 個 commit）：**

| Commit | 主題 |
|---|---|
| `402e9e8` | 本檔（協調地圖） |
| `24ae3b7` | 稽核脫敏精準化：segment 比對 + 計量豁免（修正 `c05716a` 的過度遮蔽） |

> ⚠️ `c05716a` 的稽核脫敏**已被 `24ae3b7` 修正**。子字串比對會把
> `max_tokens`、`prompt_tokens`、`token_usage` 等 LLM 用量欄位全遮掉。
> 若你正在做稽核相關的工作，請以 `24ae3b7` 的 `internal/audit/sanitize.go`
> 為準，並用 `go run ./tools/redact_probe` 確認分類。

---

## 1. 🚫 已佔用地盤 — 不要修改這些檔案

以下是 PR #8 已改動的檔案。**若你的任務與它們無關，請避開**；若確實相關，
先在下面「地盤登記表」登記，並在 PR 說明裡註明重疊範圍。

### Go — 認證 / 機密欄位 / 稽核
```
internal/secretstore/secretstore.go          internal/secretstore/childenv.go
internal/secretstore/secretstore_test.go     internal/secretstore/childenv_test.go
internal/secretstore/subprocess_env_policy_test.go
internal/database/secrets.go                 internal/database/database.go
internal/database/c2.go                      internal/database/webshell.go
internal/audit/sanitize.go
internal/audit/sanitize_test.go
tools/redact_probe/main.go
internal/config/robots_public.go
```

### Go — C2
```
internal/c2/io.go            internal/c2/manager.go
internal/c2/types.go         internal/c2/listener_http.go
internal/c2/payload_builder.go
```

### Go — Handler / Security
```
internal/handler/config.go   internal/handler/webshell.go
internal/handler/terminal.go internal/handler/terminal_ws_unix.go
internal/security/executor.go
internal/mcp/client_sdk.go
```

### 前端 / 文件 / CI
```
web/static/js/c2.js         web/static/js/webshell.js
web/templates/index.html
web/static/i18n/en-US.json  web/static/i18n/zh-CN.json
web/static/js/c2-xss.test.cjs
config.example.yaml         SECURITY.md
AUDIT_FINDINGS_20261007.md
docs/en-US/security-hardening.md   docs/zh-CN/security-hardening.md
.github/workflows/linux-build.yml
```

### 本輪新增的測試（名字帶 `masterkey_testmain_test.go` 的是佔位套件初始化用）
```
internal/app/masterkey_testmain_test.go
internal/c2/masterkey_testmain_test.go
internal/database/secrets_migration_test.go
internal/database/webshell_redacted_test.go
internal/handler/masterkey_testmain_test.go
internal/handler/webshell_redaction_test.go
internal/c2/path_safety_test.go
internal/mcp/subprocess_env_test.go
```

---

## 2. ✅ 尚未被盤點的高風險區（可以接手）

前五份審計覆蓋的是：XSS/路徑穿越、敏感資料、C2、批次/漏洞管理、WebShell/外部工具。
**以下區域尚未被審計，且風險高、面積大：**

| 優先 | 區域 | 位置 | 規模 | 為什麼沒被看過 |
|---|---|---|---|---|
| **P0** | 授權 / 權限提升 | `internal/security/rbac.go`、`rbac_middleware.go`、`internal/handler/rbac.go`、`auth.go`、`role.go` | 約 3k LOC | 前五輪都在看資料流，沒人系統性看過「誰能做什麼」 |
| **P0** | SQL 注入 / 資料存取層 | `internal/database/`（55 檔 19k LOC） | 19k LOC | 只審過 secrets 相關，其餘 50 檔未動 |
| **P1** | 檔案 I/O 與上傳 | `internal/knowledge/`（23 檔） | 3.9k LOC | 與 C2 的路徑問題同型，但知識庫上傳是另一條路徑 |
| **P1** | 工作流執行 | `internal/workflow/`（28 檔） | 4.9k LOC | 工作流能觸發工具執行，權限傳遞可疑 |
| **P2** | 認證管理本身 | `internal/security/auth_manager.go`、`password.go`、`ratelimit.go` | — | 密碼雜湊、session、暴力破解防護 |
| **P2** | 多代理協作 | `internal/multiagent/`（194 檔 26k LOC） | 26k LOC | 面積最大，但風險取決於是否隔離 |

---

## 3. 第二輪盤點的路線（本助手負責）

**原則：只增強，不降弱。修復 + 補測試 + 突變測試證明測試有效。**

1. **授權邊界** — 從路由清單出發，反查每個 handler 的 RBAC 檢查是否可繞過
   （漏檢 / 檢查錯資源 / 只在前端藏按鈕）
2. **資料存取層** — 找動態組 SQL、字串拼接 WHERE、未參數化的排序欄位
3. **檔案 I/O** — 知識庫上傳與 C2 相同的路徑逃逸型態
4. **資源耗盡** — 無上限的 goroutine / 檔案句柄 / 連線池
5. **秘密與設定** — 確認 `JY_SECMASTER_KEY` 沒有第二條外流路徑

每項發現都會：**先寫失敗測試 → 再修 → 突變測試證明測試有牙齒**。

---

## 4. ⚠️ 必須知道的坑（每個都實際踩過）

### 行尾是本 repo 最大的地雷
`core.autocrlf=true`，但 **HEAD blob 存的是 CRLF**。直接 `git add` 會把整個檔案
視為改動（曾出現 3919 行的假 diff）。

```bash
# 編輯前先確認該檔是 CRLF 還是 LF
f=internal/handler/terminal.go
echo "CR=$(tr -cd '\r' < $f | wc -c) NL=$(tr -cd '\n' < $f | wc -c)"

# 提交時務必關閉 autocrlf，否則 CRLF 會被吃掉
git -c core.autocrlf=false add <檔案>
```

已知：`internal/secretstore/*` 是 **LF**，其餘多數為 **CRLF**。以實測為準。

### `grep -c $'\r$'` 是壞的行尾偵測器
曾誤報 `secretstore.go` 為 CRLF（實際是 LF），害我做出錯誤假設。
**請改用上一則的 `tr` 寫法。**

### `gofmt` 會把 CRLF 標記為需要格式化
本 repo 有 600+ 個檔案被 `gofmt -l` 標記，**這是既有狀態，不要順手重排檔案**。
判斷「我的改動是否格式正確」要用：

```bash
gofmt "$f" > /tmp/x.go && diff <(tr -d '\r' < "$f") /tmp/x.go
```

### CI 目前排除三個套件（既有失敗，非本輪造成）
`internal/handler`(6)、`internal/logger`(2)、`internal/security`(4)。
排除清單寫在 `.github/workflows/linux-build.yml`，附有原因註解。
**若你修好了其中一項，請把套件從排除清單移除** — 這是刻意留給後續工作的出口。

**已實測的結論**（用 `ci/exclusion-check` 分支跑真實 Actions，run `37567963574`）：

| 套件 | Linux runner | 結論 |
|---|---|---|
| `internal/logger` | `ok jysecai/internal/logger 0.010s` | **排除是過度保守，移出清單即可白拿 +290 LOC 的 CI 覆蓋**。這是最低成本、最高報酬的一步。 |
| `internal/security` | 只剩 `TestEinoStreamingShell_SudoFailsFast` | runner 以 root 跑，`sudo` 反而成功 → **環境造成，非產品缺陷**。紅線禁止用 skip 掩蓋，正解是讓該測試在非 root 下有明確意義。 |
| `internal/handler` | — | 4 個是 Windows 測試衛生問題（缺 `defer db.Close()`），2 個是真實缺陷。 |

---

## 5. 紅線（不可違反）

這些是本專案第一輪修復時訂下的約束，延續適用：

- ❌ 為了讓 CI 綠燈而刪除測試，或把 failing test 改成 skip
- ❌ 用 `continue-on-error` 掩蓋真正的錯誤
- ❌ 降低 security gate、放寬授權檢查
- ❌ 刪除既有功能、或為了單一問題大規模 refactor
- ❌ 把 Secret / API Key 寫進 repo、config 或測試 fixture
- ❌ `git reset --hard` / `git clean -fd` / force push
- ❌ 覆蓋別的工作者未提交的修改
- ❌ 針對安全掃描的測試對任何未知外部目標實際掃描（只用既有 mock / fixture / 隔離環境）
- ❌ 假裝修好；做不到就明確標記 BLOCKED

---

## 6. 地盤登記表

接手新區域前先在這裡加一行，避免重複與衝突。

| 區域 | 負責人 | 分支 | 狀態 | 備註 |
|---|---|---|---|---|
| 認證 / 機密欄位 / 稽核脫敏 | Claude | `fix/audit-20261002` | 已完成 | PR #8 |
| C2 模組 | Claude | `fix/audit-20261002` | 已完成 | PR #8 |
| 前端 XSS / i18n | Claude | `fix/audit-20261002` | 已完成 | PR #8 |
| CI 擴充 | Claude | `fix/audit-20261002` | 已完成 | PR #8 |
| 子行程環境隔離 | Claude | `fix/audit-20261002` | 已完成 | PR #8 |
| **授權 / RBAC 邊界** | **Claude** | `fix/audit-20261002` | **盤點中** | §3 第 1 項 |
| **資料存取層（SQL）** | **Claude** | `fix/audit-20261002` | **盤點中** | §3 第 2 項 |
| 知識庫檔案 I/O | *(未指派)* | — | 可接手 | §2 P1 |
| 工作流執行 | *(未指派)* | — | 可接手 | §2 P1 |
| 認證管理 / 密碼 / 限流 | *(未指派)* | — | 可接手 | §2 P2 |
| 多代理協作 | *(未指派)* | — | 可接手 | §2 P2 |

---

## 7. 已知的未修項目（先別重做，理由在 PR #8）

| 項目 | 位置 | 為什麼沒修 |
|---|---|---|
| `IngestTaskResult` 無會話綁定 / 狀態閘門 | c2 result ingest | 加狀態閘門會**直接打斷 `tcp_reverse`**（該路徑全程不更新任務狀態）。跨傳輸綁定需改 4 條 transport |
| 外部 MCP 無指令白名單 | `internal/mcp/client_sdk.go:391` | 架構層級決策，需先定義「允許執行哪些外部 MCP」 |
| 外部 MCP 未強制 TLS scheme | 同上 | 同上 |
| WeCom webhook 簽章用 `!=` 而非常數時間比較 | `internal/handler/robot.go:1430` | 已記錄，未排入本輪 |
| tool guard YAML 往返會遺失權限與註解 | `tool_guard_test.go:72` | **真實的既有缺陷**，非環境造成，本輪之後處理 |

---

**維護規則：本檔記載的分支狀態、佔用地盤或坑有任何變更時，須在同一變更中更新本檔。**