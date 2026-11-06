# 授權範圍登記（Scope Registry）

> 平台端唯一的授權權威：誰可以對哪些目標做哪些動作，全部在資料庫裡，可稽核、可擴張。

## 這份文件解決什麼問題

在 Scope Registry 之前，平台端（Go）**完全沒有目標白名單**：

- MCP 工具對任何主機都照打；
- 真正的保護只有 RBAC（誰能用）、HITL（這次要不要批）、SSRF guard，以及只接在「受控跳轉驗證」一條功能上的禁區；
- 授權本身只存在一份、而且在錯的位置——`all/漏洞庫/_授權.json`（Python 端）。

也就是說：**授權只有一份、錯位、半覆蓋**。走 console 會被 `guard.py` 擋住；直接走平台 MCP 工具就繞過了。

Scope Registry 把授權變成**一份、權威、可稽核、而且能被工具鏈自動擴張**的狀態機。於是「拓界」的成本從「手改 JSON、兩邊對齊」變成「按一下」。

設計全文見 [`docs/superpowers/specs/2026-11-02-scope-registry-handoff-design.md`](../../docs/superpowers/specs/2026-11-02-scope-registry-handoff-design.md)。

## 三個詞彙先講清楚

| 詞 | 意思 | 誰在用 |
| --- | --- | --- |
| **常駐集**（`scope_targets`） | 永久授權：自有資產、已批准的客戶 scope | 操作者維護；平台上線時匯入 |
| **授權券**（`scope_grants`） | 有條件／一次性授權，自帶目標描述 | 卡片上按「只准這次」或「附條件批准」時產生 |
| **拒絕記憶**（`scope_denials`） | 被拒絕過的目標 | 按「拒絕」時產生；同一目標之後直接拒，不再打擾操作者 |

## 資料模型

三張表由 `internal/database/scope.go` 的 `EnsureScopeSchema()` 建立，**冪等且向後相容**（既有 DB 檔不需要重建就能開）。

### `scope_targets` — 常駐集

| 欄位 | 說明 |
| --- | --- |
| `id` | 主鍵（`scope_` + uuid） |
| `owner` | 擁有者：`self` 或客戶名 |
| `target_type` | `host` / `wildcard` / `cidr` / `url_prefix` |
| `target_value` | 目標值（主機、網段、正規化 URL） |
| `action_classes` | JSON 陣列；**空陣列只代表四個一般類別**，不是全部 |
| `conditions` | JSON：`{port, max_uses, valid_until}` |
| `valid_from` / `valid_until` | 授權有效期 |
| `provenance` | JSON：`{source, decided_by, decided_at, evidence_hash, note}` |
| `status` | `active` / `revoked` |

### `scope_grants` — 授權券

| 欄位 | 說明 |
| --- | --- |
| `id` | 主鍵 |
| `target_type` / `target_value` | 券自帶目標描述，所以全新目標不必先建常駐集列就能簽 |
| `action_classes` | 這一張券容許的動作類別 |
| `max_uses` / `uses_used` | 使用次數上限與已用次數 |
| `valid_until` | 券的到期時間 |
| `issued_by` / `issued_at` / `evidence` | 誰在什麼時候依據什麼核發 |
| `status` | `active` / `exhausted` / `expired` / `revoked` |

### `scope_denials` — 拒絕記憶

`target`（正規化後的目標鍵）為主鍵，另有 `owner` / `reason` / `decided_by` / `decided_at`。

## 動作類別

詞彙沿用 `all/工具/guard.py` 既有八類，避免兩邊對不上：

| 類別 | 說明 | 預設授權 |
| --- | --- | --- |
| `local_analysis` | 本機檔案分析 | 免授權 |
| `offline_replay` | 離線重放／本機證據比對 | 免授權 |
| `harmless_request` | 無害請求（GET／HEAD 類） | 空 `action_classes` 時允許 |
| `db_read_extract` | 唯讀資料庫提取 | 空 `action_classes` 時允許 |
| `credential_enum` | 憑證枚舉 | **必須明確列出** |
| `bulk_scan` | 大量掃描 | **必須明確列出** |
| `destructive` | 破壞性操作（寫入／刪除／竄改） | **永久封鎖** |
| `real_transaction` | 真實交易（下單／付款／轉帳） | **永久封鎖** |
| `arbitrary` | 工具未宣告 `action_class` | **必須明確列出**，且一律需批准 |

**最容易搞錯的一條**：`action_classes` 是空陣列時，只代表「一般類別全部允許」（`local_analysis` / `offline_replay` / `harmless_request` / `db_read_extract`），**不代表全部類別允許**。`credential_enum` / `bulk_scan` / `arbitrary` 必須被明確列出；`destructive` / `real_transaction` 任何 scope 都解鎖不了。

工具的動作類別宣告在 `tools/*.yaml`：

```yaml
name: "httpx"
action_class: "harmless_request"
parameters:
  - name: "targets"
    type: "string"
    target: true
    target_kind: "mixed"
```

未宣告 `action_class` 的工具一律視為 `arbitrary`（最嚴格）。

## 執行模式

```yaml
scope:
  enforcement: "enforce"   # off | audit | enforce
  default_owner: "self"
  timeout_seconds: 0       # 0 = 沿用該會話的 HITL 逾時設定
```

| 模式 | 行為 | 什麼時候用 |
| --- | --- | --- |
| `off`（預設） | 完全不評估，維持既有行為 | 剛升級、還沒匯入授權時 |
| `audit` | 評估並寫 `audit_logs`（`action=scope_resolve`），**不阻擋任何呼叫** | 想先看覆蓋率缺口再決定要不要強制 |
| `enforce` | 未覆蓋目標 → 產生 `scope_extension` 中斷；命中禁區／永久封鎖類別 → 直接拒絕 | 授權已匯入、想讓平台真的守範圍 |

> **預設是 `off` 是刻意的**：registry 一旦是空的，`enforce` 會讓每一次碰網路的工具呼叫都跳出授權卡片，平台等於被鎖死。先用 `audit` 看清缺口，再匯入授權，最後才切 `enforce`。

改完 `config.yaml` **要重啟核心**才會生效（設定檔只在啟動時讀一次）。

## 命中規則

比對順序固定，不可調換：

1. **禁區優先**：`internal/forbidden` 命中的目標（119／EPCR／消防救護）直接判拒絕，**不列入未覆蓋清單**——它不是「還沒被授權」，而是「永遠不該被碰到」。即使操作者按了批准也擋。
2. **永久封鎖類別**：`destructive` / `real_transaction` 整批拒絕。
3. **拒絕記憶**：之前拒過的目標直接拒。
4. **常駐集**（`scope_targets`）→ **授權券**（`scope_grants`）。

目標型別的匹配：

- `host`：精確主機；
- `wildcard`：一層子網域（`*.example.com` 命中 `x.example.com`，**不**命中 `x.y.example.com`）；
- `cidr`：網段（`192.0.2.0/24`）；
- `url_prefix`：URL 前綴。

`conditions.port` 存在時才比對埠位；沒有明確埠位時用 scheme 的預設埠位（http=80、https=443）。

## 目標從哪裡來

授權判定要成立的前提是「我們知道這次會碰到誰」。目標可能藏在三個地方，**三個來源缺一不可**：

1. **工具的目標參數本身**：`positional` / `flag` / `template` 三種 format 都取得到；
2. **`additional_args` 裡的清單檔**：`-l <file>` / `--list <file>` → 會**讀檔展開**（一檔可能上千筆）；
3. **工具的 stdin**：`httpx` 的目標就是走 stdin。

三個來源都沒有 → 判定為**任意執行類**（`arbitrary`）。這不代表「沒有目標」，而是代表「目標藏在指令裡」——此時一律要求操作者逐次宣告目標清單，**沒宣告就不准批准**。

## scope_extension 卡片

`enforce` 模式下，未覆蓋的目標不會直接被拒，而是產生一張授權裁決卡片（沿用既有 HITL 流程與 SSE 事件，**不另造佇列機制**）：

```
未覆蓋目標：new.api.example.com
來源工具  ：httpx            動作類別：harmless_request
觸發原因  ：不在任何授權範圍的允許清單內
相鄰已授權：api.example.com · 擁有者：example-client · 有效至：2026-12-01T00:00:00Z
選擇：〔批准為常駐〕〔只准這次〕〔附條件批准〕〔拒絕〕
```

| 決策 | 落地到哪裡 | 效果 |
| --- | --- | --- |
| **批准為常駐**（`approve_permanent`） | `scope_targets` | 永久納入授權，之後同類呼叫不再打擾 |
| **只准這次**（`approve_once`） | `scope_grants`（`max_uses=1`） | 這一次放行，用完即止 |
| **附條件批准**（`approve_conditional`） | `scope_grants`（帶次數／時段／類別） | 授權 N 次，或到某個時間為止 |
| **拒絕**（`reject`） | `scope_denials` | 記住此目標，之後直接拒，不再回來騷擾 |

批准會**原地續跑**：中斷結束後原工具呼叫照常執行，不改寫任何參數。

附條件批准可填：擁有者 owner、可用次數、有效期限（RFC3339）、動作類別（逗號分隔）。

### API

`POST /api/hitl/decision` 沿用既有端點，`scope_extension` 模式額外接受兩個欄位：

```json
{
  "interruptId": "hitl_xxx",
  "decision": "approve_conditional",
  "comment": "客戶已回覆同意本次測試",
  "scopeConditions": {
    "owner": "example-client",
    "actionClasses": ["harmless_request"],
    "maxUses": 3,
    "validUntil": "2026-12-01T00:00:00Z"
  },
  "scopeTargets": ["new.api.example.com"]
}
```

- `scopeConditions`：僅 `scope_extension` 模式使用；其他模式忽略。
- `scopeTargets`：操作者宣告的目標清單；**任意執行類工具必填**，缺了這次決策會被拒（不會寫入任何資料）。
- 既有 `approval` / `review_edit` 模式仍**只接受** `approve` / `reject`，行為完全沒有放寬。

## 匯入既有授權

平台提供匯入 CLI，可重複執行且冪等：

```bash
# 先看會匯入什麼（不寫資料庫）
go run ./cmd/scopeimport --config /var/lib/jysecai/core/config.yaml \
  --source /path/to/_授權.json --dry-run

# 真的匯入
go run ./cmd/scopeimport --config /var/lib/jysecai/core/config.yaml \
  --source /path/to/_授權.json
```

規則：

- `allowed_hosts` 中以 `*.` 開頭 → `target_type=wildcard`，其餘 → `host`；
- `authorized_until` → `valid_until`（解析失敗就留空並警告，**不會讓整份匯入失敗**）；
- `allowed_action_classes` → `action_classes`（空 → 空陣列＝一般類別）；
- `provenance.source` 記錄來源檔名；
- **禁區目標會被跳過並警告**——禁區永遠優先，不會因為匯入而進 registry；
- 冪等鍵是 `owner` + `target_type` + `target_value`，同一份來源重跑不會產生重複列。

## 稽核

- 每次判定寫 `audit_logs`：`action=scope_resolve`，detail 含目標、命中的 scope（`grantId` / `source` / `owner`）、未覆蓋清單、拒絕清單、決策、決策者、關聯的 HITL interrupt id、當時的執行模式。
- 授權狀態變更寫進 `scope_targets.provenance`（誰、何時、依據什麼證據、來源）。
- HITL 中斷本身沿用既有 `hitl_interrupts` 表與既有保留策略。

## 待裁決授權券：把「一直拒絕」變成可見、可批的工作佇列

### 問題

`scope.enforcement` 開著但 registry 是空的時候，agent 碰到任何需要授權的目標
只會退化成「我不做」——因為平台從來沒有問過使用者「這件事該不該做」。
上千筆已確認的 critical/high 目標不可能逐筆人工審，於是整個流程卡死在「什麼都不做」。

### 覆蓋率稽核（scope-audit）

先量化缺口，再談授權：

```bash
# 產生覆蓋率報告（唯讀，不寫任何資料）
./build/releases/scope-audit \
  --config /var/lib/jysecai/core/config.yaml \
  --status confirmed --severity critical,high \
  --action-class db_read_extract \
  --out docs/scope-audit-$(date +%Y%m%d-%H%M%S).md
```

2026-11-07 的實測：1023 筆 confirmed critical/high 漏洞記錄，去重後 803 個目標鍵，
其中 729 個是有效主機、74 個是無法解析的雜訊（漏洞記錄的 target 欄位塞了自由文字）。
覆蓋率 0%。

雜訊不會被自動起草——`scopeaudit.PlausibleHost` 會把
「dns.example.tw (61.63.14.15 與 61.218.16.228)」這種描述擋下，
因為把它變成授權券只會讓 registry 被垃圾填滿。

### 自動起草（scope-drafter）

```bash
# 先看會起草什麼（不寫資料庫、不發通知）
./build/releases/scope-drafter --config /var/lib/jysecai/core/config.yaml --limit 20 --dry-run

# 真的起草 + 推播核准通知
./build/releases/scope-drafter --config /var/lib/jysecai/core/config.yaml --limit 20
```

起草出來的券一律是 `status=pending`、`max_uses=1`、預設 24 小時有效、
`action_classes` 明列（`db_read_extract,harmless_request,local_analysis,offline_replay`）。

**待裁決的券不構成授權。** `internal/scope` 的 `matchGrantRows` 會略過
`pending` 的券，所以「起草」只是把問題搬到人面前，不會讓任何未經核准的目標變成可打。
這一點有測試釘住（`TestPendingGrantDoesNotCover`）。

### 三條核准路徑

| 路徑 | 權限 | 適用情境 |
|---|---|---|
| `POST /api/scope/grants/:id/activate` | `scope:write`（預設只有 admin） | 平台內操作 |
| Telegram inline 按鈕 | 綁定帳號且有 `scope:write` | 手機上快速核准 |
| `scripts/scope-approve.sh --activate <id>` | root | Telegram token 失效時的後備 |

CLI 與 API 走同一套資料層語意（只認 pending → active、不可重放、過期或用盡就不給動），
只是把核准者記成 `cli:<unix使用者>`。

```bash
# 列出待裁決的券
bash scripts/scope-approve.sh --list

# 核准一張
bash scripts/scope-approve.sh --activate grant_draft_a7dfc90c4c108436 --by operator

# 拒絕（會寫入拒絕記憶，同一目標之後不再打擾）
bash scripts/scope-approve.sh --reject grant_draft_a7dfc90c4c108436 --owner operator
```

### 權限模型

`scope:write` 預設只給 admin：核准授權券等於改變安全邊界本身，
若也給 operator，就變成「自己提出、自己核准」——等於沒有控制。
`scope:read` 依平台既有慣例給 operator／auditor／viewer。

### Telegram 核准按鈕

按鈕點擊走的是 Telegram 的 callback_query。平台在 `internal/robot` 加了
callback 支援（`telegram_callback.go`），並且**按下按鈕的人必須是平台上有
`scope:write` 的綁定帳號**——任何能對機器人說話的人都看得到這則訊息，
沒有權限檢查的話等於把核准權交給每一個人。

注意：若 `getMe` 回 404 Not Found，代表 bot token 已被撤銷／輪替，
`robots.telegram.enabled` 應維持 `false`，否則 poller 會每 5 秒失敗重連、
持續灌錯誤日誌卻收不到任何訊息。換上有效 token 後即可啟用。

## 疑難排解

| 症狀 | 原因 | 處理 |
| --- | --- | --- |
| 每個碰網路的工具呼叫都跳出授權卡片 | `enforcement: enforce` 但 registry 是空的 | 先匯入授權；或暫時切 `audit` / `off` |
| 改了 `config.yaml` 但行為沒變 | 設定檔只在啟動時讀一次 | `systemctl restart jysec-core` |
| 明明在授權裡卻還是被擋 | 該動作類別沒被明確列出（`credential_enum` / `bulk_scan` / `arbitrary`） | 把類別補進 `action_classes`，或改用該類別相符的授權 |
| 目標被判拒絕而且繞不掉 | 命中禁區或永久封鎖類別 | 這是設計如此：禁區與 `destructive` / `real_transaction` 不可解鎖 |
| 卡片一直重複跳出同一個目標 | 之前是「逾時自動拒絕」而不是「拒絕」 | 逾時也會寫進拒絕記憶；若要重新開放，刪掉 `scope_denials` 對應列 |
| 批准了卻還是被攔截點 B 擋下 | 授權寫入與續跑之間有競態 | 批准時是「先寫 registry、再續跑」；若仍發生，檢查 `scope_grants.uses_used` 是否已用盡 |
| 匯入後守門（`verify_all.py`）轉紅 | 匯入改變了判定結果 | 匯入前後的判定結果必須一致；比對匯入前後同一組 scope 的判定 |

## 相關文件

- [HITL Best Practices](hitl-best-practices.md) — 人工審批的操作原則
- [Tool Execution Governance](tool-execution-governance.md) — 工具執行面的治理
- [Security Model](security-model.md) — 平台的整體安全模型
- [Audit and Monitoring](audit-and-monitoring.md) — 稽核與監控
