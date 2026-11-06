# 設計：Scope Registry 與授權 Handoff（把平台變成真正的紅隊武器）

- 日期：2026-11-02
- 狀態：待使用者審閱（§3.1「永久封鎖類別處置」待拍板）
- 相關既有程式：`internal/security/executor.go`（命令執行）、`internal/handler/hitl.go`（HITL 中斷／批准／續跑）、`internal/forbidden/scope.go`（禁區）、`internal/database/hitl_logs.go`（HITL 表）、`internal/config/config.go`（`ToolConfig` / `ParameterConfig`）、`all/工具/guard.py`（console 端守門）、`all/漏洞庫/_授權.json`（既有授權）
- 規格來源：本次 brainstorming（兩段設計皆已核准）

## 目標

把「授權」從一份靜態 JSON 變成平台資料庫裡的**可擴張授權狀態機**，並讓平台既有的 HITL 機制多一種中斷類型。於是「拓界」的成本從「手改 JSON、兩邊對齊」變成「按一下」。

```
工具呼叫 (httpx -u https://new.api.chailease.com.tw)
  → 解析目標 → scope.Resolve：未覆蓋
  → scope_extension 中斷 → SSE 推一張卡片到操作者眼前
  → 操作者按〔批准為常駐〕/〔只准這次〕/〔附條件〕/〔拒絕〕
  → registry 寫入 + 簽發授權券
  → approvedExec 續跑 → 工具照常執行
  → audit_logs 記錄：誰批的、批了什麼、證據雜湊、結果
```

## 為什麼現在「不夠牛逼」：瓶頸不在工具，在授權的覆蓋率與位置

實測盤點的結果：

| 事實 | 影響 |
| --- | --- |
| 平台已備妥 97 支 YAML 工具（amass/dnsx/httpx/bloodhound/certipy/coercer/hashcat/hydra/ffuf/dalfox/angr…） | **工具深度不是瓶頸**，不需要再加工具 |
| 平台端（Go）**完全沒有目標白名單**：MCP 工具對任何主機都照打，只有 RBAC（誰能用）、HITL（這次要不要批）、SSRF guard、禁區（只接在 redirect 驗證一條功能上） | 真正的保護只覆蓋一半執行面 |
| 授權只存在一份、而且在錯的位置：`all/工具/guard.py` + `all/漏洞庫/_授權.json`（Python） | 走 console 會被 guard 擋；直接走平台 MCP 工具就繞過了 |
| `guard.py` 的判定是**靜態 host 清單比對**（`authorized` / `allowed_hosts` / `allowed_action_classes` / `authorized_until`） | 實務上發現新子網域就必須停手改 JSON，鏈路中斷、稽核斷裂 |

也就是說：現在不是「授權太緊」，是**授權只有一份、錯位、半覆蓋**，操作體感自然不猛。

要讓它「比授權更牛逼」，正解不是把授權拿掉，而是**讓授權變成單一、權威、可稽核、且能被工具鏈自動擴張的那一份**。

## 已確認的決策（使用者）

| 決策 | 結論 |
| --- | --- |
| 授權權威歸屬 | **平台為唯一權威**：建 Go scope registry，MCP 工具執行前必查；`guard.py` 改讀平台簽發的授權，不再自己維護 `_授權.json` |
| 授權取得方式 | **兩層**：常駐集（自有資產，隨時可打）＋ 逐次 handoff（客戶案，發現即提案、操作者一鍵批准後納入） |
| 執行面強制方式 | **A′**：命令層判定 + handoff；任意執行類工具強制逐次聲明目標才能批（不做網路出口層，出口層留二期） |
| handoff 互動 | 沿用既有 HITL 卡片／SSE 流程，不另造佇列機制 |
| 助手組織 | 不叫停其他助手，改分三層：T0 唯讀偵察（並行）／T1 單一寫者／T2 戰術決策（操作者） |
| 永久封鎖類別 | **部分解除**（見 §3.1）：`credential_enum`／`bulk_scan` 改為需 scope 明確授權該類別；`destructive`／`real_transaction` 維持永久封鎖。由我在使用者授權「決策權交給你」後拍板 |

## 既有能力盤點（實作基礎）

- `internal/handler/hitl.go`：`HITLManager` 已有 `pending map[string]*pendingInterrupt`、
  `CreatePendingInterrupt(conversationID, assistantMessageID, mode, toolName, toolCallID, payloadJSON, reviewer)`、
  `ResolveInterrupt(interruptID, decision, comment, editedArguments)`、
  `waitDecision(runCtx, p, cfg.Timeout)`、以及批准後回寫 `tool_result` 的 `approvedExec` FIFO 佇列。
  兩種既有 mode：`approval`、`review_edit`（批准前可改參數）。
- `internal/database`：`hitl_interrupts` 表欄位為
  `id / conversation_id / message_id / mode / tool_name / tool_call_id / payload / status / decision / decision_comment / created_at / decided_at`。
  **擴充既有欄位即可，不新增表。**
- `internal/security/executor.go`：`buildCommandArgs(toolName, toolConfig, args)` 是最終 argv 組裝點；
  `ToolConfig` 欄位 `Name/Command/Args/ShortDescription/Description/Enabled/Parameters/ArgMapping/AllowedExitCodes`；
  `ParameterConfig` 已有 `Name/Type/Required/Position/Flag/Template/Format/Default`。
- `tools/httpx.yaml`：目標是經 **stdin** 餵進 `httpx`；`additional_args` 支援 `-l <file>`。
  → **目標解析必須涵蓋三個來源**（見 §4）。
- `internal/forbidden/scope.go`：禁區（119／EPCR／消防）既有實作，Go 端為權威。
- `all/工具/guard.py`：`evaluate(spec, mode, scope, confirm_token)`；network 分支依序檢查
  scope 存在 → `authorized` → `authorized_until` 未過期 → `action_class` 在允許清單 → `host` 在 `allowed_hosts` → 速率限制；`execute` 另需 `confirm_token`。
- `all/漏洞庫/_授權.json`：10 個 scope，含 `authorized / authorized_until / authorized_by / allowed_hosts / allowed_action_classes / rate_limit_per_min / max_requests_per_run`。

## 設計

### 1. Scope Registry（新增 `internal/scope`）

```go
package scope

type TargetType string
const (
    TargetHost       TargetType = "host"        // 精確主機
    TargetWildcard   TargetType = "wildcard"    // *.example.com（只匹對一層）
    TargetCIDR       TargetType = "cidr"        // 10.0.0.0/8
    TargetURLPrefix  TargetType = "url_prefix"  // https://example.com/admin/
)

// Resolve 判斷一組目標是否被授權涵蓋。
// 回傳已覆蓋的匹配結果，與未被覆蓋的目標。
func (s *Service) Resolve(targets []string, actionClass string, at time.Time) (Result, error)

type Result struct {
    Covered   []Match  // 每個命中：Target、GrantID、Conditions
    Uncovered []string // 未被任何 scope 涵蓋的目標
    Denied    []string // 命中 scope 但被條件／到期擋下
}
```

- **匹配順序**：`host` 精確 → `wildcard` → `cidr` → `url_prefix`。
  `wildcard` 只匹對一層子網域（`*.a.com` 命中 `x.a.com`，不命中 `x.y.a.com`）。
- **port** 為選配限定條件（存在於 `conditions.port` 時才比對）。
- **action class 解析**（見 §3.1）：
  - `scope_targets.action_classes` 為空陣列 → 僅代表「一般類別全部允許」
    （`local_analysis` / `offline_replay` / `harmless_request` / `db_read_extract`）。
  - `credential_enum` / `bulk_scan` → 必須在 `action_classes` 中**明確列出**才允許。
  - `destructive` / `real_transaction` → **任何 scope 都無法授權**，永遠拒絕。
  - `arbitrary`（工具未宣告 `action_class`）→ 一律需批准，且需明確授權。
- **禁區優先**：`Resolve` 內部先跑 `internal/forbidden`；命中禁區的目標**直接判 Denied，不列入 Uncovered**——
  即使操作者批准也擋（§6）。

### 2. 資料模型（`internal/database/scope.go`）

```sql
CREATE TABLE IF NOT EXISTS scope_targets (
    id             TEXT PRIMARY KEY,
    owner          TEXT NOT NULL,          -- 'self' | 客戶名
    target_type    TEXT NOT NULL,          -- host | wildcard | cidr | url_prefix
    target_value   TEXT NOT NULL,
    action_classes TEXT NOT NULL DEFAULT '[]',  -- JSON array；空 = 全部
    conditions     TEXT NOT NULL DEFAULT '{}',  -- JSON: {port, max_uses, valid_until}
    valid_from     DATETIME,
    valid_until    DATETIME,
    provenance     TEXT NOT NULL DEFAULT '{}',  -- JSON: {source, decided_by, decided_at, evidence_hash, note}
    status         TEXT NOT NULL DEFAULT 'active', -- active | revoked
    created_at     DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS scope_grants (
    id             TEXT PRIMARY KEY,
    target_type    TEXT NOT NULL,          -- host | wildcard | cidr | url_prefix（自帶目標描述）
    target_value   TEXT NOT NULL,
    action_classes TEXT NOT NULL DEFAULT '[]',
    max_uses       INTEGER NOT NULL DEFAULT 1,
    uses_used      INTEGER NOT NULL DEFAULT 0,
    valid_until    DATETIME,
    issued_by      TEXT NOT NULL,
    issued_at      DATETIME NOT NULL,
    evidence       TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'active'   -- active | exhausted | expired | revoked
);

CREATE TABLE IF NOT EXISTS scope_denials (
    target      TEXT PRIMARY KEY,          -- 正規化後的目標
    owner       TEXT NOT NULL,
    reason      TEXT NOT NULL,
    decided_by  TEXT NOT NULL,
    decided_at  DATETIME NOT NULL
);
```

- 遷移必須**向後相容**（既有 DB 檔案要能直接開）。`internal/database` 既有 migration 慣例沿用。
- `scope_denials` 負責「拒絕也會被記住」：被拒的目標之後直接拒，不再打擾操作者。
- **`scope_targets` = 常駐集**（永久授權：自有資產與已批准的客戶 scope）。
  **`scope_grants` = 授權券**（有條件／一次性），**自帶目標描述**，
  因此對全新目標可以直接簽發，不必先在 `scope_targets` 建一列。

### 3. 工具宣告目標與動作類別（YAML 最小侵入）

`ParameterConfig` 新增兩個欄位：

```go
Target     bool   `yaml:"target,omitempty"`      // 這是目標參數
TargetKind string `yaml:"target_kind,omitempty"` // host | url | cidr | mixed
```

`ToolConfig` 新增一個欄位：

```go
ActionClass string `yaml:"action_class,omitempty"` // 動作類別；未宣告 = arbitrary（最嚴格）
```

```yaml
name: "httpx"
action_class: "harmless_request"
parameters:
  - name: "targets"
    type: "string"
    target: true
    target_kind: "mixed"
```

**動作類別詞彙沿用 `all/工具/guard.py` 既有的 8 類**（避免兩邊對不上、遷移失真）：

| 類別 | 說明 | 既有語意 |
| --- | --- | --- |
| `local_analysis` | 本機檔案分析 | 免授權 |
| `offline_replay` | 離線重放／本機證據比對 | 免授權 |
| `harmless_request` | 無害請求（GET／HEAD 類） | 需授權 ＋ 主機白名單 |
| `db_read_extract` | 唯讀資料庫提取 | 需授權 |
| `destructive` | 破壞性操作（寫入／刪除／竄改） | **永久封鎖** |
| `credential_enum` | 憑證枚舉 | **永久封鎖** |
| `bulk_scan` | 大量掃描 | **永久封鎖** |
| `real_transaction` | 真實交易（下單／付款／轉帳） | **永久封鎖** |

**未宣告 `action_class` 的工具＝`arbitrary`**（最嚴格，一律需批准），沿用 guard.py
「未分類動作一律不執行」的既有原則。

**「永久封鎖」語意的變更（需使用者拍板，見 §3.1）。**

### 3.1 永久封鎖類別的處置（已決）

**決策：部分解除。**（2026-11-02；使用者授權「決策權交給你」後由我拍板。）

| 類別 | 決策 | 理由 |
| --- | --- | --- |
| `credential_enum` | **解除永久封鎖**，改為需 scope **明確列出**該類別 | 憑證枚舉是紅隊常規武器；`hydra`／`hashcat` 若一律封鎖，平台在這條線上等於繳械。風險改由「目標授權＋動作類別授權＋速率上限」承擔 |
| `bulk_scan` | **解除永久封鎖**，改為需 scope **明確列出**該類別 | 同上；既有 scope 已有 `rate_limit_per_min` / `max_requests_per_run` 可控 |
| `destructive` | **維持永久封鎖** | 不可逆傷害（寫入／刪除／竄改目標資料）。平台不該有這種能力，授權也不該能解鎖它 |
| `real_transaction` | **維持永久封鎖** | 同上；平台不該有下單／付款／轉帳能力 |

**配套的動作類別解析規則（避免「空值＝全部」把封鎖解掉）：**

```
scope_targets.action_classes 為空陣列時，僅代表「一般類別全部允許」：
    local_analysis / offline_replay / harmless_request / db_read_extract

credential_enum / bulk_scan   → 必須在 scope_targets.action_classes 裡「明確列出」才允許
destructive / real_transaction → 任何 scope 都無法授權，永遠拒絕
```

- 工具 YAML 需補 `action_class`：`hydra`／`hashcat` → `credential_enum`；
  `ffuf`／`dirsearch`／`gau` 等大範圍枚舉 → `bulk_scan`；其餘依語意歸類。
- 未宣告 `action_class` 的工具 = `arbitrary` → 一律需批准，且需 scope 明確授權 `arbitrary`。
- `arbitrary` 另需在 §7 卡片上強制聲明「本次將接觸的目標清單」。

**未宣告 `target: true` 的工具＝任意執行類**（`exec.yaml`、`execute-python-script.yaml` 等），
永遠需要批准，且批准前必須聲明「本次將接觸的目標清單」。

### 4. 目標解析（`internal/scope/resolve_targets.go`）

三個來源，缺一不可：

1. **目標參數本身**：`positional` / `flag` / `template` 三種 format 都要能取到值。
2. **`additional_args` 裡的檔案清單**：`-l <file>` / `--list <file>` → **讀檔展開**（一檔可能上千筆）。
3. **工具的 stdin 輸入**：`httpx.yaml` 的目標就是走 stdin；需從工具呼叫 payload 取。

解析後正規化成 `host:port` / `url` / `cidr` 三種形式，再交給 `Resolve`。

### 5. 兩個強制點

**攔截點 A（主）** — `internal/handler` 的工具執行閘，與 HITL 判定**同一個位置**：
- 目標全覆蓋 → 照常執行。
- 有未覆蓋目標 → **不直接拒絕**，改為建立 `scope_extension` HITL 中斷，
  payload 含：未覆蓋目標、來源工具、動作類別、觸發原因、相鄰已授權目標（供操作者判斷是否同組織）。
  **「相鄰」定義**：同一 `owner` 下、與未覆蓋目標**共享最長後綴**的已授權目標
  （例：`api.chailease.com.tw` 已授權、`new.api.chailease.com.tw` 未授權 → 相鄰＝`api.chailease.com.tw`）。
  純字串後綴比對，不引入 public-suffix 依賴。
- 操作者決定後：寫入 registry → **原工具呼叫原地續跑**（既有 `approvedExec` 機制）。

**攔截點 B（兜底）** — `internal/security/executor.go` 在 `buildCommandArgs` 之後、spawn 之前再驗一次；
不符直接失敗（fail closed）。防的是繞過 handler 的內部呼叫路徑。

**任意執行類工具**走 A，且卡片**強制要求填「本次將接觸的目標清單」**；
批准後簽 `scope_grants(max_uses=1, action_classes=[該次宣告的類別])`，
該次呼叫自動視為對那些目標有授權。

### 6. 禁區優先（不可退讓）

**禁區永遠優先於任何授權**：即使操作者在卡片上按了批准，119／EPCR／消防的目標仍然擋掉。
- 平台端 `internal/forbidden/scope.go` 是唯一權威。
- `all/tools/forbidden_scope.py`（Python 端）改為向平台查詢，**收掉雙軌守門**。
- 測試必須覆蓋「即使 `scope_targets` 涵蓋了禁區目標，仍然擋」。

### 7. Handoff（跳轉給操作者）

- 沿用 `hitl_interrupts` 表，**不新增表**：
  - `mode` 新增 `scope_extension`。
  - `decision` 新增 `approve_permanent` / `approve_once` / `approve_conditional` / `reject`。
  - 條件（動作類別、次數、時段）以 JSON 存 `decision_comment`。
- 卡片內容：

```
未覆蓋目標：new.api.chailease.com.tw
來源工具  ：httpx            動作類別：recon_http
觸發原因  ：不在任何 scope 的允許清單內
相鄰已授權：api.chailease.com.tw（chailease scope，已授權至 2026-12-01）
選擇 ：〔批准為常駐〕〔只准這次〕〔附條件：類別／次數／時段〕〔拒絕〕
```

- **批准可帶條件**——這是「像武器」跟「像開關」的差別。
- **拒絕會被記住**（寫 `scope_denials`），避免同一目標反覆回來騷擾。

### 8. 稽核

- 每次判定都寫 `audit_logs`：`action=scope_resolve`，`detail_json` 含
  目標、命中的 scope、未覆蓋清單、denied 清單、decision、決策者、關聯的 HITL interrupt id。
- 授權狀態變更寫進 `scope_targets.provenance`（誰、何時、依據什麼證據、來源）。
- 與既有 `hitl_logs` retention 對齊（`internal/hitl/retention.go`）。

### 9. Console 收斂（`all/工具/guard.py`）

- 不再自己當權威。改為啟動時向平台拉**簽章授權快照**（本機快取，離線可用）。
- 執行前仍用本地快照判定（離線可用）；**平台不可用時降級為「拒絕網路動作」，不是放行**。
- `all/漏洞庫/_授權.json` 保留但降為**唯讀匯入來源**。

### 10. 遷移（不讓任何案子中斷）

1. 匯入 `all/漏洞庫/_授權.json` 的 10 個 scope → `scope_targets`
   （`owner`＝客戶名、`target_type` 逐條 host/wildcard、`action_classes`、
   `valid_until`＝`authorized_until`、`provenance.source`＝`_授權.json`）。
2. 平台提供匯入 CLI（`cmd/scopeimport`），可重複執行且冪等。
3. `guard.py` 切換到快照模式前，先跑一次比對：匯入前後同一組 scope 的判定結果必須一致。
4. 既有稽核與 `verify_all.py` 守門不得轉紅。

## 測試

| # | 測試 | 位置 |
| --- | --- | --- |
| 1 | 匹配語意：host / wildcard（只一層）/ cidr / url_prefix / port 限定 / 到期 | `internal/scope/*_test.go` |
| 2 | 目標解析：positional、flag、`-l <file>`、stdin 四種來源 | `internal/scope/resolve_targets_test.go` |
| 3 | 強制點：宣告式工具 vs 任意執行類的行為差異 | `internal/handler/scope_gate_test.go` |
| 4 | handoff 全流程：未覆蓋→中斷→批准→原地續跑→稽核 | `internal/handler/scope_handoff_test.go` |
| 5 | 拒絕記憶：拒絕後同目標不再中斷 | `internal/scope/denial_test.go` |
| 6 | 禁區優先：`scope_targets` 涵蓋禁區目標時仍然擋 | `internal/scope/forbidden_precedence_test.go` |
| 7 | 遷移回歸：匯入 10 scope 後 `02_验证工具/verify_all.py` 仍綠 | `all/02_验证工具/verify_all.py` |
| 8 | 兜底強制：繞過 handler 直呼 executor 時不符即失敗 | `internal/security/executor_scope_test.go` |

測試不得對外送出任何真實請求（沿用既有做法：攔截式 Transport 斷言零對外請求）。

## 分期

| 階段 | 內容 | 產出 |
| --- | --- | --- |
| **P0** | schema + `internal/scope`（Resolve／目標解析／禁區優先）＋ 攔截點 B ＋ 匯入 CLI | 授權狀態有了唯一權威，尚未影響既有執行路徑 |
| **P1** | 攔截點 A ＋ `scope_extension` HITL ＋ 卡片 ＋ 原地續跑 | **拓界成本從「手改 JSON」降到「按一下」** |
| **P2** | `guard.py` 收斂 ＋ 任意執行類的目標聲明流程 | 兩端單一權威，執行面完整覆蓋 |
| **P3** | registry 管理頁（常駐集／已批准／拒絕清單／稽核） | 操作者可自行維護，不必每次找我 |
| **P4**（二期選配） | 網路出口層兜底 | 對「命令層被繞過」的終極防線 |

P0/P1 完成即達成主要目標；P2/P3 是體驗與治理補完；P4 等真的出現繞過案例再上。

> **本 spec 的實作計畫只涵蓋 P0 + P1。** P2／P3／P4 各自另開 spec 與計畫，
> 避免一份計畫同時鋪四個階段、無法逐段驗收。

## 風險與取捨

| 風險 | 緩解 |
| --- | --- |
| 目標抽取有盲區（目標藏在檔案、工具自行解析網域、SSRF 二次跳轉） | 宣告式工具涵蓋三個來源；任意執行類改為**逐次批准**，用制度關盲區；P4 出口層作終極防線 |
| 批准流轉太細碎，操作者疲於點擊 | 常駐集承載自有資產；客戶案只在**拓界**時才打擾；批准可帶條件（一次／N 次／時段） |
| 執行面收斂可能影響既有自動化（`verify_all.py` 等打本機 8899） | 本機 8899 路徑不在 scope 管轄內；遷移前後比對 + 守門回歸 |
| 多助手並行寫壞共享狀態 | T1 單一寫者 + lock 檔；交接紀錄寫進 spec／docs |
| 平台停機時 console 無法判定授權 | 快照 + 離線可用；平台不可用時**拒絕網路動作**（不放行） |

## 明確不做（YAGNI）

- 不做網路出口層（A 之外的方案 C）——留 P4。
- 不做多使用者、分級授權、授權券的自動續期。
- 不做雲端 IAM／AD 身分層級的授權對象（先做主機層）。
- 不做自動信任同組織的自動納入（使用者已選定兩層制，自動納入會誤傷 CDN／託管／共用 IP）。
- 不改既有 HITL 的 `approval` / `review_edit` 兩種 mode 的行為。
