# 設計：對話攻擊鏈 → 純紅隊交付物

- 日期：2026-11-02
- 狀態：待使用者覆核
- 相關既有文件：`docs/zh-CN/pentest-report.md`、`docs/en-US/pentest-report.md`、`docs/zh-CN/security-ops.md`、`docs/en-US/security-ops.md`

## 問題

平台已經有兩套並行的記錄機制，但它們的分工在**交付時被做反了**。

對話裡的掃描代理有兩個落庫工具（`internal/projectprompt/blackboard.go:12,65`）：

| 工具 | 承載內容 | 黑板對它的定位 |
| --- | --- | --- |
| `upsert_project_fact` | 完整攻擊鏈：入口 → 逐步利用 → 原始請求/響應或命令 → 現象 → 關聯漏洞 ID | 「事實記**復現所需的全部上下文**（含失敗嘗試、繞過、依賴會話）」 |
| `record_vulnerability` | 可交付發現的摘要 | 「記可交付 findings」 |

但漏洞紀錄的契約（`internal/app/vulnerability_tools.go:292`）要求每一筆都必填 `recommendation`（修復建議），
且 schema 說明寫的是「修复建议（必需）：给出针对该触发点/参数/组件的具体修复和复测建议」。
**這段指令每個對話回合都注入掃描代理的上下文**，逼它為每筆漏洞寫一段防禦建議 —— 這是「藍隊」進入對話層、
並且偷走 agent token 的真正入口。

而交付物端（`internal/pentestreport/report.go`）只讀漏洞表，**從不讀 `project_facts`**：

- `internal/handler/pentest_report.go:49,95-104` — 報告輸入只有 `ListVulnerabilitiesForAccess(...)` 的漏洞列。
- 對話的攻擊鏈雖然可以經 `POST /api/projects/{id}/promote-attack-chain/{conversationId}`
  （`internal/handler/openapi.go:2819`）沉澱到 `project_facts` 與 `project_fact_edges`，
  但沒有任何一條路徑把它送進交付物。

結果是：對話裡賺到的攻擊鏈在落地成交付物前被整段丟掉，交付物只剩一份防禦性備忘錄。

### 已核實的四個具體缺陷

| # | 缺陷 | 證據 |
| --- | --- | --- |
| 1 | 對話層被藍隊課稅：`recommendation` 是 MCP 工具的必填欄位，代理必須為每筆漏洞寫防禦建議 | `internal/app/vulnerability_tools.go:185-196,292` |
| 2 | 交付層被藍隊把關：缺 `Recommendation` → 報告降級為「草稿」，UI 徽章顯示「報告草稿」 | `internal/pentestreport/report.go:158-160`；`web/static/js/security-ops.js:328-330` |
| 3 | 去重被偏誤：`findingScore` 給 `Recommendation` +4，同一漏洞記兩次時，有修復建議的那筆贏 —— 攻擊鏈更完整但沒寫修復建議的新紀錄會被比較弱的那筆蓋掉 | `internal/pentestreport/report.go:204-225` |
| 4 | 事實來源的紀錄被結構性排除：`isFactStub` 用「有沒有修復建議」判定降級，導致事實生出的紀錄被踢進「未成形紀錄」，完全不出現在發現總表 | `internal/pentestreport/report.go:227-237` |

### 欄位在轉換時被丟

- `pentestreport.Finding` 沒有 `Preconditions`、沒有 `ReproSteps` 欄位（`internal/pentestreport/report.go:12-26`）
- `internal/handler/pentest_report.go:99-103`：`Preconditions` 直接消失；`vuln.ReproSteps` 被塞進 `RecordedNotes`，
  在報告裡以「已歸檔驗證筆記」這個藍隊名稱出現（`internal/pentestreport/report.go:394`）
- 前端手動建檔表單也要求修復建議（`web/static/i18n/zh-CN.json:2856,3769`）

### `recommendation` 沒有任何功能消費者

| 消費者 | 是否讀 `recommendation` |
| --- | --- |
| 自動複測 `internal/handler/vulnerability_verify_auto.go:239-246` | 否（只讀 `Description` / `ReproSteps` / `Evidence`） |
| CSV 匯出 `internal/handler/vulnerability_export_records.go:138-143` | 讀，但只是原樣帶出；資料不丟 |
| 資料庫 `internal/database/vulnerability.go:509-512` | 只是空值互補 |

也就是說，`recommendation` 唯一的實際效果就是**塑造交付物形狀**。

### 平台內已有的正確認證

`internal/redirectverify/record.go:64-81` 已經是一份紅隊紀錄的正確樣態：
`Preconditions`（攻擊前置條件）、`ReproSteps`（含受控端點與觀察點的逐步復現）、
`Evidence`（原始請求/狀態/Location）、`Impact`（攻擊者能造成什麼後果）、
`RetestNotes`（攻擊者再次確認的結果）—— 唯一不屬於攻擊面的是 `Recommendation` 那一行。

## 已確認的決策（使用者）

| 決策 | 結論 |
| --- | --- |
| 「這掃描器」指哪一條資料流 | **對話中的掃描代理 → 漏洞庫 → 滲透報告**。不是 Xalgorix 外部掃描引擎（security-ops 任務流程不動） |
| 攻擊鏈要不要進交付物 | **要**。報告新增「攻擊鏈」章，讀 `project_facts` + `project_fact_edges` |
| 授權與審批這層 | **全部保留，一字不改**。授權章節、審批閘門、ROE 資料、CI `authorization-boundaries` 皆不動 |
| 「修復建議」欄位 | 報告端**拿掉輸出**；工具端保留欄位但降為選填、說明改寫為紅隊語意（「利用建議」）；DB schema 不動 |
| 第 6 章 | 排序清單（依 severity + confidence）。「可接續利用方向」由新的攻擊鏈章的關係邊承載，不臆造文字 |
| 動工範圍 | 後端契約 + 報告 + 前端 i18n/表單 + 文件。**不動 POST 串流路徑** |

## 設計

### 0. 明確不動的部分

- `/api/eino-agent/stream` 的 POST 與整條串流路徑 —— 一字不碰
- 授權與審批層：報告第 2 章「授權與範圍」、`authorizationSection`、`qualificationGaps` 裡的授權缺口那行、
  security-ops 的人工審批流程、CI 的 `authorization-boundaries` 阻擋項 —— 全部原樣保留
- DB schema：`vulnerabilities` / `project_facts` / `project_fact_edges` 皆無 migration
- `internal/redirectverify/record.go` 等其他漏洞寫入來源 —— 不動

### 1. 對話層：把必填注意力從藍隊移到紅隊

`internal/app/vulnerability_tools.go`

| 欄位 | 變更 |
| --- | --- |
| `recommendation` | 從 `required` 移除；schema 說明改寫為「利用建議（選填）：後續可接續的利用向量與擴大路徑，或此漏洞在攻擊鏈中的位置」 |
| `preconditions` | **升為 `required`**；說明改為攻擊語意：登入狀態、權限、帳號、Header/Cookie、特定資料、網段位置、環境/版本 |
| `reproduction_steps` | 維持 `required`，說明不動（既有說明已是「未參與對話的人照做即可復現」） |
| `retest_notes` | 不動（平台內部生命週期欄位，與交付物無關） |

`missingVulnerabilityReproFields`（`:179-197`）的必填清單同步：`recommendation` 移除、`preconditions` 加入，
欄位標籤一併改寫。

**1.2 黑板提示層也要同步**

`internal/projectprompt/blackboard.go:84` 的可交付漏洞說明寫的是
「含标题、严重程度、类型、目标、证明（POC）、影响、**修复建议**」—— 這是藍隊課稅的第三個注入點
（工具 schema 說明、工具 required 清單、黑板提示）。只改前兩處，黑板仍會叫代理補寫修復建議。

改為「含标题、严重程度、类型、目标、攻击前置条件、证明（POC）、复现步骤、影响」。

**效果**：掃描代理每記一筆漏洞，少寫一段防禦建議、多寫一段攻擊前置條件。
這是「把對話的部分優化」的本體 —— 紅隊化從提示層開始，不只是報告層。

### 2. 交付層：報告本體

`internal/pentestreport/report.go`

**2.1 `Finding` 結構**

新增 `Preconditions string`、`ReproSteps string`。`RecordedNotes` 保留（相容既有呼叫端），
但 mapper 不再把 `ReproSteps` 塞進它。

**2.2 發現詳述的欄位順序**（`findingDetails`）

```
說明 → 前置條件 → 復現步驟 → 證據摘要 → 影響 → 複測
```

- 「已歸檔驗證筆記」這個名稱消失，改為「復現步驟」
- 「修復建議」欄位不再輸出

**2.3 章節重編**

| 新 | 舊 | 內容 | 動作 |
| --- | --- | --- | --- |
| 1 | 1 | 執行摘要 | 不動 |
| 2 | 2 | 授權與範圍 | **一字不動** |
| 3 | 3 | 方法 | 改寫：刪掉「報告不生成攻擊載荷或操作手冊」，改為照錄已驗證的利用步驟與原始請求/響應 |
| 4 | — | **攻擊鏈**（新） | 見 §3 |
| 5 | 4 | 發現總表 | 不動 |
| 6 | 5 | 發現詳述 | 見 §2.2 |
| 7 | 6 | **利用優先順序** | 取代「修復優先順序」：依 severity + confidence 排序，每筆列標題、目標、關聯漏洞編號 |
| 8 | 7 | 未成形紀錄 | 文字改寫（不再提「修復建議」） |
| 9 | 8 | 任務紀錄 | 不動 |
| 10 | 9 | 限制 | 改寫為紅隊語氣（不再寫「不包含新的攻擊操作步驟」） |
| 頁尾 | 頁尾 | — | 改寫：不再寫「僅供委託範圍內的修復與複測使用」 |

**2.4 合格判定**（`qualificationGaps`）

授權缺口那行**逐字保留**。發現完整性判定改為：

- 缺 `Title` / `Severity` / `Target` → 沿用現有缺口文字
- 缺 `Description` 或 `Evidence` → 沿用現有缺口文字
- 缺 `Impact` → 缺口文字改為「缺少業務影響」
- `Preconditions` 與 `ReproSteps` **至少一項非空** → 否則新增缺口「缺少攻擊前置條件或復現步驟」
- **移除**「缺少業務影響或修復建議」中的修復建議那一半

「至少一項」而非兩項都必填的理由：`reproduction_steps` 自第一個 commit 起就是 `record_vulnerability` 的必填欄位
（`git log -S'reproduction_steps'` 確認），所以既有 agent 記錄的漏洞都有復現步驟；
而 `preconditions` 一直是選填，實務上大量為 NULL。若把 `Preconditions` 設成獨立的合格條件，
會讓全部既有報告集體從「合格」降級為「草稿」。

**2.5 去重計分**（`findingScore`）

| 欄位 | 舊 | 新 |
| --- | --- | --- |
| `Target` | +4 | +4 |
| `Impact` | +4 | +4 |
| `Recommendation` | **+4** | **0（移除）** |
| `Evidence` | +2 | +2 |
| `Description` | +1 | +1 |
| 非 stub | +3 | +3 |
| `Preconditions` | — | **+2** |
| `ReproSteps` | — | **+3** |

修掉缺陷 3：代表紀錄改由「攻擊鏈完整度」決定，而不是「防禦性內容多寡」。

**2.6 事實降級判定**（`isFactStub`）

- `Type` 為 `note` / `target` → 仍是 stub（不動）
- 描述以「由项目事实」/「由專案事實」開頭 → **一律**是 stub。

理由：`upsert_project_fact` 不會建立漏洞紀錄（`internal/app/project_fact_tools.go` 只寫 `project_facts`），
這個前綴已是無產生器的舊慣例；而且新的「攻擊鏈」章本來就會呈現這些事實，
讓它們同時出現在發現總表只會重複。原本靠「有沒有修復建議」判定，屬於用藍隊欄位決定結構，必須換掉。

### 3. 新章：攻擊鏈

新檔 `internal/pentestreport/attackchain.go`，單一職責 —— 把專案事實圖渲染成攻擊鏈章。

**輸入**（新增到 `pentestreport.Input`）：

```go
type AttackChainInput struct {
    Nodes []AttackChainNode
    Edges []AttackChainEdge
}
type AttackChainNode struct {
    Key, Category, Summary, Body, Confidence string
    RelatedVulnerabilityID string
}
type AttackChainEdge struct {
    FromKey, ToKey, Type, Confidence string
}
```

**組裝**（`internal/handler/pentest_report.go`）

- `h.db.ListProjectFacts(projectID, database.ProjectFactListFilter{ExcludeDeprecated: true}, 500, 0)`
- `h.db.ListProjectFactEdgesByProject(projectID)`
- **節點納入規則**：`category ∈ {finding, chain, exploit, poc}` **或** `fact_key` 前綴 ∈ `{finding/, chain/, exploit/, poc/}`
  （兩者取聯集，避免代理只寫了 fact_key 沒寫 category 時被靜默丟棄）
- 其他類別（`target/` `auth/` `infra/` `business/` 等環境認知）不進攻擊鏈章
- 事實為空 → 整章不出現（不留空章）
- `pentestReportInput` 簽章改為 `pentestReportInput(project, runs, findings, chain, now)`

**渲染**

- 節點：每個事實一節，列出 fact_key、category、summary、body（body 依 `blackboard.go:64` 已是完整攻擊鏈）、
  confidence；有 `related_vulnerability_id` 時標出關聯的漏洞編號
- 邊：`exploits` / `discovered_on` / `enables` / `leads_to` / `depends_on` / `contains` / `part_of` / `supports`
  渲染成「來源 key ──type──▶ 目標 key」的關係清單
- 節點依 category 排序：chain → exploit → poc → finding
- 所有字串經既有 `esc()` 轉義

### 4. mapper

`internal/handler/pentest_report.go`

- `Preconditions: vuln.Preconditions`、`ReproSteps: vuln.ReproSteps` 補上
- `RecordedNotes` 不再塞 `vuln.ReproSteps`（改留空或保留相容值，但報告不再以該名稱輸出）

### 5. 前端

`web/static/i18n/zh-CN.json` + `web/static/i18n/en-US.json`

| key | 變更 |
| --- | --- |
| `vulnerabilities.saveRequiredFields` | 必填清單拿掉「修复建议」、加入「前置条件」 |
| `vulnerabilities.headingRecommendation` | 「修复建议」→「利用建议」 |
| `vulnerabilities.headingPreconditions` | 保持「前置条件」 |
| `vulnerabilities.detailRecommendation` | 「修复建议」→「利用建议」 |

`web/static/js/vulnerability.js`：建檔表單的必填校驗與欄位標題同步。
（此檔工作區已有未提交變更，只在現有結構上加減，不整檔覆寫。）

### 6. 文件

- `docs/zh-CN/pentest-report.md` + `docs/en-US/pentest-report.md`：章節結構同步（bilingual 對齊是 CLAUDE.md 硬規則）

### 7. 測試

**必須改寫的既有測試**

`internal/pentestreport/report_test.go:23-34` 的 `TestBuildDraftWhenRecommendationMissing`
把藍隊契約寫成了斷言（沒有修復建議 = 不合格，且報告要出現「修復建議」）。
改寫為新契約：沒有修復建議、但有前置條件 + 復現步驟 + 影響 → **合格**。

`internal/pentestreport/report_test.go:9-21` 的 `TestBuildQualifiedWhenScopeAndFindingAreComplete` 補上新的必填欄位。

**新增測試**

| 測試 | 斷言 |
| --- | --- |
| 前置條件 / 復現步驟不再被丟 | 報告 HTML 含「前置條件」「復現步驟」，且不含「已歸檔驗證筆記」 |
| 報告不含修復建議 | HTML 不含「修復建議」 |
| 攻擊鏈章渲染 | 給定 facts + edges，HTML 含節點 key、body、關係邊 |
| 攻擊鏈章缺席 | 無 facts 時 HTML 不含「攻擊鏈」章 |
| 事實降級判定 | 「由專案事實」開頭的紀錄一定落在未成形紀錄，不進發現總表 |
| 去重計分 | 攻擊鏈更完整（無修復建議）的紀錄勝出 |
| 工具必填清單 | `preconditions` 缺 → 報錯；`recommendation` 缺 → 不報錯 |
| 提示層無藍隊殘留 | 工具 schema 說明、`missingVulnerabilityReproFields` 標籤、`blackboard.go` 可交付漏洞說明，皆不含「修复建议」/「修復建議」 |

**執行**

```
go vet ./...
go test ./internal/pentestreport/... ./internal/app/... ./internal/handler/...
go test -run 'TestResolveWithinPromptBase|TestMaskProviderSecrets|TestMergeProviderSecrets|TestGetConfigResponseCarries|TestBeaconTemplate|TestQuoteTemplateData|TestValidateBeaconHost|TestResolveBeaconDialHost|TestRedactMCP|TestMergeExternalMCP|TestExternalMCPConfigForResponse|TestEscapeCSVCell|TestMaskTerminalCommand|TestIsBlockedIP|TestValidateOutboundURL|TestWebshell.*|TestOperator|TestRBAC' ./internal/...
```

### 8. 明確不做（YAGNI）

- 不改 DB schema、不做 migration
- 不動 security-ops 任務建立與人工審批流程
- 不動 Xalgorix 客戶端（`internal/xalgorix/`）
- 不改 `chat.js` 的對話渲染與攻擊鏈視覺化（已經是紅隊呈現）
- 不新增匯出格式（CSV 維持原樣帶出所有欄位）
- 不移除 `recommendation` 的 DB 欄位（300 筆既有資料 + 遷移相容要求）
- 不改 `internal/vulnmask/` 的匯出遮蔽

## 風險與影響

| 風險 | 處理 |
| --- | --- |
| 既有 300 筆漏洞的 `recommendation` 不再出現在報告 | 這正是本次需求。資料仍在 DB 與漏洞管理 UI，CSV 匯出也仍帶 |
| 既有漏洞若 `Preconditions` 與 `ReproSteps` 都為空 → 報告降級為「草稿」 | `reproduction_steps` 自第一個 commit 起就是必填，既有 agent 紀錄都有；實務上只有非 agent 來源的舊列可能受影響 |
| `preconditions` 升為必填後，舊的 agent 對話可能送出缺 `preconditions` 的呼叫 | 工具回傳明確錯誤並列出缺哪一欄，代理可補齊；黑板 prompt 也要同步說明 |
| 報告章節重新編號 | 章節是每次重新產生的靜態 HTML，無外部錨點依賴；文件同步更新 |
| `isFactStub` 判定變寬 | 影響面僅限報告呈現（事實紀錄從發現總表移到未成形紀錄 + 攻擊鏈章），資料不刪 |
| CI `authorization-boundaries` | 該 job 的測試清單不涵蓋 pentestreport 與本次改動；仍會照跑一次確認綠 |

## 驗收標準

1. 一份含前置條件、復現步驟、證據、影響、攻擊鏈事實與關係邊的專案，產生的報告：
   - 含「攻擊鏈」章，節點與關係邊都出現
   - 發現詳述含「前置條件」「復現步驟」
   - 全文不含「修復建議」「已歸檔驗證筆記」「修復優先順序」
   - 判定為「合格交付」
2. `record_vulnerability` 不帶 `recommendation` 也能成功；不帶 `preconditions` 會得到明確的必填錯誤
3. 工具 schema、必填清單、黑板提示三處都不再出現「修复建议」
4. `go vet ./...` 與上述測試全綠
5. `/api/eino-agent/stream` 的 POST 路徑與授權/審批流程未被修改（diff 檢視確認）
