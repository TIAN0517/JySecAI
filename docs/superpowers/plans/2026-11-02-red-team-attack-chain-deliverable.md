# 對話攻擊鏈 → 純紅隊交付物 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把對話裡賺到的攻擊鏈（前置條件、逐步復現、利用關係）完整送進滲透測試交付物，並移除交付鏈上的藍隊框架（修復建議必填、修復優先順序章節、防禦性敘事）。

**Architecture:** 三層改造。(1) 對話層：`record_vulnerability` 的 MCP 工具契約與黑板提示，把「修復建議」必填改成「攻擊前置條件」必填。(2) 交付層：`internal/pentestreport` 新增「攻擊鏈」章（渲染 `project_facts` + `project_fact_edges`）、拿掉「修復建議」輸出與「修復優先順序」章、合格判定與去重計分改以攻擊側欄位計分。(3) 前端層：i18n 與建檔表單的必填集合同步。

**Tech Stack:** Go 1.25+ / Gin / SQLite（`mattn/go-sqlite3`，CGO）/ 靜態 SPA 前端（原生 JS + `data-i18n`）/ `node --test` 前端測試。

**Spec:** `docs/superpowers/specs/2026-11-02-red-team-attack-chain-deliverable-design.md`

## Global Constraints

以下約束在每個 task 都隱含適用，不得違反：

- **不動 `/api/eino-agent/stream` 的 POST 路徑與整條串流路徑。**
- **不動授權與審批層**：報告第 2 章「授權與範圍」、`authorizationSection`、`qualificationGaps` 裡的授權缺口那行文字、`internal/handler/security_ops.go` 的審批流程、CI 的 `authorization-boundaries` 阻擋項 —— 全部原樣保留。
- **不做 DB migration**：`vulnerabilities` / `project_facts` / `project_fact_edges` 的 schema 一律不動。`recommendation` 欄位保留，既有 300 筆資料不動。
- **不做 i18n hardcode 基準重產生**：掃描器只看 `web/templates/*.html` 與 `web/static/js/*.js`，`data-i18n` 元素內的文字被跳過。任何新增的中文字串都會讓 `TestWebI18nNoNewHardcodedText` 失敗。
- **`zh-CN.json` 與 `en-US.json` 的 key 集合必須完全一致**（`TestWebI18nDictionariesKeySetsMatch`）。改一個就要改另一個。
- **文件雙語對齊是硬規則**：`docs/zh-CN/` 與 `docs/en-US/` 必須成對更新。
- **程式碼註解用中文**，比照周邊風格。
- **本工作區有 198 個其他人的未提交變更**：每個 task 的 `git add` 只加自己碰過的檔案，禁止 `git add -A` / `git add .`。
- **分支**：`backup/scanner-wsl-20261022`（目前分支，不新建）。

---

## File Structure

| 檔案 | 動作 | 職責 |
| --- | --- | --- |
| `internal/pentestreport/report.go` | 修改 | 報告骨架：Finding 契約、章節編排、合格判定、去重計分、敘事文案 |
| `internal/pentestreport/attackchain.go` | **新增** | 攻擊鏈章：型別、納入判定、渲染。單一職責，不碰其他章節 |
| `internal/pentestreport/report_test.go` | 修改 | 報告既有斷言（藍隊契約改寫） |
| `internal/pentestreport/attackchain_test.go` | **新增** | 攻擊鏈章單元測試 |
| `internal/handler/pentest_report.go` | 修改 | DB → 報告輸入的映射，含 project_facts / edges 讀取 |
| `internal/handler/pentest_report_test.go` | 修改 | 端到端：事實圖進入報告 |
| `internal/app/vulnerability_tools.go` | 修改 | `record_vulnerability` 工具契約（schema + 必填清單） |
| `internal/app/vulnerability_tools_test.go` | **新增** | 工具必填行為測試 |
| `internal/projectprompt/blackboard.go` | 修改 | 黑板提示層的可交付漏洞說明 |
| `internal/projectprompt/blackboard_test.go` | **新增** | 提示層無藍隊殘留的斷言 |
| `web/static/i18n/zh-CN.json` / `en-US.json` | 修改 | 使用者可見文案 |
| `web/static/js/vulnerability.js` | 修改 | 建檔表單必填校驗 |
| `web/templates/index.html` | 修改 | 表單欄位必填標記與 fallback 文案 |
| `docs/zh-CN/pentest-report.md` / `docs/en-US/pentest-report.md` | 修改 | 文件同步 |

---

### Task 1: 報告欄位契約 —— Finding 加欄位、發現詳述重排

**Files:**
- Modify: `internal/pentestreport/report.go:12-26`（Finding 結構）、`internal/pentestreport/report.go:368-403`（`findingDetails`）
- Test: `internal/pentestreport/report_test.go`

**Interfaces:**
- Consumes: 無（第一個 task）
- Produces: `pentestreport.Finding` 新增兩個欄位 `Preconditions string`、`ReproSteps string`。後續 Task 2、5、6 都依賴這兩個欄位名。

- [ ] **Step 1: 寫失敗的測試**

在 `internal/pentestreport/report_test.go` 末尾新增：

```go
func TestBuildRendersPreconditionsAndReproStepsWithoutBlueTeamLabels(t *testing.T) {
	result := Build(sampleInput(Finding{
		Title: "登入參數可注入", Severity: "high", Status: "confirmed", Target: "https://app.example.com/login",
		Description: "登入參數 username 可注入。", Preconditions: "已取得一般用戶 Session。",
		ReproSteps: "1. 帶入 ' OR 1=1--\n2. 觀察回應",
		Evidence: "原始請求與回應", Impact: "可繞過登入取得他人資料。",
	}))
	html := result.HTML
	for _, want := range []string{"前置條件", "復現步驟", "登入參數可注入"} {
		if !strings.Contains(html, want) {
			t.Errorf("報告缺少 %q", want)
		}
	}
	for _, unwanted := range []string{"已歸檔驗證筆記", "修復建議"} {
		if strings.Contains(html, unwanted) {
			t.Errorf("報告仍含藍隊名稱 %q", unwanted)
		}
	}
}
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/pentestreport/ -run TestBuildRendersPreconditionsAndReproStepsWithoutBlueTeamLabels -v`

Expected: FAIL —— 編譯錯誤 `unknown field Preconditions in struct literal`。

- [ ] **Step 3: 改 Finding 結構**

把 `internal/pentestreport/report.go:12-26` 的 Finding 結構改成：

```go
// Finding 是已經入庫的漏洞，報告只轉錄這些欄位，不另寫攻擊步驟。
type Finding struct {
	ID             string
	Title          string
	Severity       string
	Status         string
	Type           string
	Target         string
	Description    string
	Preconditions  string
	ReproSteps     string
	Impact         string
	Recommendation string
	Evidence       string
	RecordedNotes  string
	RetestNotes    string
	Confidence     int
}
```

- [ ] **Step 4: 重排發現詳述的欄位輸出**

把 `internal/pentestreport/report.go` 的 `findingDetails` 裡那段欄位輸出改成：

```go
		writeField(&b, "說明", finding.Description)
		writeField(&b, "前置條件", finding.Preconditions)
		writeField(&b, "復現步驟", finding.ReproSteps)
		writeField(&b, "證據摘要", finding.Evidence)
		writeField(&b, "影響", finding.Impact)
		writeField(&b, "複測", finding.RetestNotes)
```

（原本是「說明 / 影響 / 證據摘要 / 已歸檔驗證筆記 / 修復建議 / 複測」。）

- [ ] **Step 5: 跑測試確認通過**

Run: `go test ./internal/pentestreport/ -v`

Expected: PASS（既有測試此時應該也還過；`TestBuildDraftWhenRecommendationMissing` 依賴的缺口文字還沒改，Task 2 才處理）。

- [ ] **Step 6: Commit**

```bash
git add internal/pentestreport/report.go internal/pentestreport/report_test.go
git commit -m "feat(pentestreport): Finding 補上前置條件與復現步驟，詳述輸出改攻擊導向

報告的 Finding 契約原本沒有 Preconditions / ReproSteps，復現步驟被塞進
RecordedNotes 以「已歸檔驗證筆記」的名義輸出，藍隊名稱留在交付物裡。
這裡補齊欄位並把輸出順序改成：說明 → 前置條件 → 復現步驟 → 證據 → 影響 → 複測。"
```

---

### Task 2: 合格判定與去重計分改以攻擊側欄位

**Files:**
- Modify: `internal/pentestreport/report.go:129-166`（`qualificationGaps`）、`internal/pentestreport/report.go:204-237`（`findingScore`、`isFactStub`）
- Test: `internal/pentestreport/report_test.go`

**Interfaces:**
- Consumes: Task 1 的 `Finding.Preconditions`、`Finding.ReproSteps`
- Produces: 新缺口字串「發現「X」缺少攻擊前置條件或復現步驟」；去重計分改由攻擊側欄位決定。

- [ ] **Step 1: 寫失敗的測試**

改寫 `internal/pentestreport/report_test.go` 裡既有的 `TestBuildDraftWhenRecommendationMissing`（它把藍隊契約寫成了斷言），並新增兩條：

```go
func TestBuildQualifiedWithoutRecommendationWhenAttackFieldsPresent(t *testing.T) {
	result := Build(sampleInput(Finding{
		Title: "登入參數可注入", Severity: "high", Status: "confirmed", Target: "https://app.example.com/login",
		Description: "登入參數 username 可注入。", Preconditions: "已取得一般用戶 Session。",
		ReproSteps: "1. 帶入 ' OR 1=1--", Evidence: "原始請求與回應", Impact: "可繞過登入。",
	}))
	if !result.Qualified {
		t.Fatalf("沒有修復建議不該影響合格判定, gaps=%v", result.Gaps)
	}
	if strings.Contains(result.HTML, "修復建議") {
		t.Fatal("報告不該輸出修復建議")
	}
}

func TestBuildGapWhenNeitherPreconditionsNorReproSteps(t *testing.T) {
	result := Build(sampleInput(Finding{
		Title: "標題", Severity: "medium", Status: "open", Target: "https://app.example.com",
		Description: "有描述", Impact: "有影響", Evidence: "有證據",
	}))
	if result.Qualified {
		t.Fatal("缺攻擊前置條件與復現步驟必須是草稿")
	}
	if !strings.Contains(result.HTML, "缺少攻擊前置條件或復現步驟") {
		t.Fatalf("gaps=%v", result.Gaps)
	}
}

func TestSplitFindingsPrefersExploitRicherDuplicate(t *testing.T) {
	delivery, stubs := splitFindings([]Finding{
		{Title: "同一標題", Severity: "medium", Status: "open", Target: "https://app.example.com",
			Description: "描述", Impact: "影響", Recommendation: "有修復建議但沒有復現步驟"},
		{Title: "同一標題", Severity: "high", Status: "open", Target: "https://app.example.com",
			Description: "描述", Impact: "影響", Preconditions: "前置條件", ReproSteps: "1. 步驟", Evidence: "證據"},
	})
	if len(stubs) != 0 {
		t.Fatalf("不該有 stub: %+v", stubs)
	}
	if len(delivery) != 1 {
		t.Fatalf("應保留一筆, got=%d", len(delivery))
	}
	if delivery[0].ReproSteps == "" {
		t.Fatal("攻擊鏈更完整的那筆應該勝出")
	}
}
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/pentestreport/ -run 'TestBuildQualifiedWithoutRecommendationWhenAttackFieldsPresent|TestBuildGapWhenNeitherPreconditionsNorReproSteps|TestSplitFindingsPrefersExploitRicherDuplicate' -v`

Expected: FAIL —— 缺「缺少攻擊前置條件或復現步驟」缺口，且去重仍由修復建議決定。

- [ ] **Step 3: 改合格判定**

把 `internal/pentestreport/report.go` 的 `qualificationGaps` 中發現完整性那一段改成：

```go
		if strings.TrimSpace(finding.Description) == "" && strings.TrimSpace(finding.Evidence) == "" {
			gaps = append(gaps, "發現「"+label+"」缺少描述或證據")
		}
		if strings.TrimSpace(finding.Impact) == "" {
			gaps = append(gaps, "發現「"+label+"」缺少業務影響")
		}
		if strings.TrimSpace(finding.Preconditions) == "" && strings.TrimSpace(finding.ReproSteps) == "" {
			gaps = append(gaps, "發現「"+label+"」缺少攻擊前置條件或復現步驟")
		}
```

**注意**：授權缺口那一段（在 `for _, auth := range in.Authorizations` 裡）**一個字都不能改**。

- [ ] **Step 4: 改去重計分**

把 `internal/pentestreport/report.go` 的 `findingScore` 整個換成：

```go
// findingScore 決定同一標題的多筆記錄要保留哪一筆。
//
// 計分只看攻擊側欄位：前置條件、復現步驟、原始證據、實際影響。
// 原本修復建議佔 +4，會讓「防禦性內容比較多」的那筆贏 —— 攻擊鏈更完整
// 但沒寫修復建議的新紀錄反而被蓋掉。這裡把權重挪到復現步驟與前置條件。
func findingScore(finding Finding) int {
	score := 0
	if strings.TrimSpace(finding.Target) != "" {
		score += 4
	}
	if strings.TrimSpace(finding.Preconditions) != "" {
		score += 2
	}
	if strings.TrimSpace(finding.ReproSteps) != "" {
		score += 3
	}
	if strings.TrimSpace(finding.Impact) != "" {
		score += 4
	}
	if strings.TrimSpace(finding.Evidence) != "" {
		score += 2
	}
	if strings.TrimSpace(finding.Description) != "" {
		score += 1
	}
	if !isFactStub(finding) {
		score += 3
	}
	return score
}
```

- [ ] **Step 5: 改事實降級判定**

把 `internal/pentestreport/report.go` 的 `isFactStub` 改成：

```go
// isFactStub 判斷這筆紀錄是不是「專案事實」而不是可交付發現。
//
// 事實來源的紀錄一律不進發現總表：完整攻擊鏈由「攻擊鏈」章以
// project_facts 的原始內容呈現，同一份內容再出現在發現總表只會重複。
//
// 原本用「有沒有修復建議」判定，等於讓一個藍隊欄位決定報告結構 ——
// 必須換掉。
func isFactStub(finding Finding) bool {
	switch strings.ToLower(strings.TrimSpace(finding.Type)) {
	case "note", "target":
		return true
	}
	desc := strings.TrimSpace(finding.Description)
	if strings.HasPrefix(desc, "由项目事实") || strings.HasPrefix(desc, "由專案事實") {
		return true
	}
	return false
}
```

- [ ] **Step 6: 跑測試確認通過**

Run: `go test ./internal/pentestreport/ -v`

Expected: PASS —— 包含 `TestBuildKeepsCompleteDuplicateAndOmitsFactStubs`（事實 stub 仍不進缺口清單）。

- [ ] **Step 7: Commit**

```bash
git add internal/pentestreport/report.go internal/pentestreport/report_test.go
git commit -m "fix(pentestreport): 合格判定與去重計分改以攻擊側欄位

三個缺陷一起修：
- 缺修復建議就不合格 → 改成缺「攻擊前置條件或復現步驟」才不合格
- findingScore 給修復建議 +4，防禦性內容多的那筆贏 → 權重挪到復現步驟與前置條件
- isFactStub 靠修復建議判定降級 → 事實來源紀錄一律降級，攻擊鏈改由新章呈現

授權缺口判定一個字沒動。"
```

---

### Task 3: 章節重編與藍隊敘事清除

**Files:**
- Modify: `internal/pentestreport/report.go:112-126`（`Build` 的章節編排）、`internal/pentestreport/report.go:239-257`（`stubSection`）、`internal/pentestreport/report.go:336-338`（`methodologySection`）、`internal/pentestreport/report.go:405-428`（`remediationSection` → `exploitationPrioritySection`）、`internal/pentestreport/report.go:453-459`（`writeSection`）
- Test: `internal/pentestreport/report_test.go`

**Interfaces:**
- Consumes: Task 1、Task 2
- Produces: 章節編號 1–10；`exploitationPrioritySection(findings []Finding) string`；`severityRank(severity string) int`；`writeSection` 對空 body 會跳過（Task 4 的攻擊鏈章靠這個機制缺席）。

- [ ] **Step 1: 寫失敗的測試**

在 `internal/pentestreport/report_test.go` 末尾新增：

```go
func TestBuildHasNoBlueTeamNarrative(t *testing.T) {
	result := Build(sampleInput(Finding{
		Title: "登入參數可注入", Severity: "high", Status: "confirmed", Target: "https://app.example.com/login",
		Description: "描述", Preconditions: "前置條件", ReproSteps: "復現步驟",
		Evidence: "證據", Impact: "影響", Recommendation: "請改用參數化查詢。",
	}))
	for _, unwanted := range []string{
		"修復優先順序",
		"報告不生成攻擊載荷或操作手冊",
		"不包含新的攻擊操作步驟",
		"僅供委託範圍內的修復與複測使用",
		"修復建議",
	} {
		if strings.Contains(result.HTML, unwanted) {
			t.Errorf("報告仍含藍隊敘事 %q", unwanted)
		}
	}
	for _, want := range []string{"利用優先順序", "1. 執行摘要", "2. 授權與範圍", "10. 限制"} {
		if !strings.Contains(result.HTML, want) {
			t.Errorf("報告缺少章節 %q", want)
		}
	}
}

func TestExploitationPrioritySectionOrdersBySeverityThenConfidence(t *testing.T) {
	html := exploitationPrioritySection([]Finding{
		{Title: "低", Severity: "low", Status: "open", Target: "https://a.example.com", Confidence: 90},
		{Title: "高", Severity: "high", Status: "open", Target: "https://b.example.com", Confidence: 95},
		{Title: "嚴重", Severity: "critical", Status: "open", Target: "https://c.example.com", Confidence: 95},
		{Title: "已修", Severity: "critical", Status: "fixed", Target: "https://d.example.com", Confidence: 100},
	})
	critical := strings.Index(html, "嚴重")
	high := strings.Index(html, "高")
	low := strings.Index(html, "低")
	if critical < 0 || high < 0 || low < 0 {
		t.Fatalf("項目缺漏: %s", html)
	}
	if !(critical < high && high < low) {
		t.Fatalf("排序不是嚴重度遞減: %s", html)
	}
	if strings.Contains(html, "已修") {
		t.Fatal("已修復的項目不該出現在利用優先順序")
	}
}
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/pentestreport/ -run 'TestBuildHasNoBlueTeamNarrative|TestExploitationPrioritySectionOrdersBySeverityThenConfidence' -v`

Expected: FAIL —— `exploitationPrioritySection` 未定義；報告仍含「修復優先順序」等藍隊敘事。

- [ ] **Step 3: 章節重排並讓空章節可缺席**

把 `internal/pentestreport/report.go` 的 `Build` 裡的章節編排改成：

```go
	writeSection(&b, "1. 執行摘要", executiveSummary(in))
	writeSection(&b, "2. 授權與範圍", authorizationSection(in))
	writeSection(&b, "3. 方法", methodologySection())
	writeSection(&b, "4. 攻擊鏈", "")
	writeSection(&b, "5. 發現總表", findingsTable(in.Findings))
	writeSection(&b, "6. 發現詳述", findingDetails(in.Findings))
	writeSection(&b, "7. 利用優先順序", exploitationPrioritySection(in.Findings))
	writeSection(&b, "8. 未成形紀錄", stubSection(stubs))
	writeSection(&b, "9. 任務紀錄", runsSection(in.Runs))
	writeSection(&b, "10. 限制", "<p>本報告只涵蓋系統中已歸檔、且屬於此專案的漏洞、授權掃描任務與專案事實圖中的攻擊鏈。同一標題只保留欄位較完整的一筆。由專案筆記或目標清單生成、且缺少目標與復現步驟的紀錄列在未成形紀錄，不計入合格缺口。它不替代書面授權原件。證據欄位過長時會截斷，完整內容以漏洞管理中的原始紀錄為準。</p>")
	b.WriteString("<footer>文件編號 ")
	b.WriteString(esc(reportID))
	b.WriteString(" · 僅供委託範圍內的滲透測試交付使用</footer></article></body></html>")
```

> 這裡第 4 章先傳空字串，讓本 task 獨立可編譯、可測試。
> `writeSection` 對空 body 會跳過，所以攻擊鏈章在此刻整章缺席。
> **Task 4 的 Step 4 會把它改成 `writeSection(&b, "4. 攻擊鏈", attackChainSection(in.AttackChain))`。**

同時把 `writeSection` 改成空 body 時跳過：

```go
func writeSection(b *strings.Builder, title, body string) {
	if strings.TrimSpace(body) == "" {
		return
	}
	b.WriteString("<section><h2>")
	b.WriteString(esc(title))
	b.WriteString("</h2>")
	b.WriteString(body)
	b.WriteString("</section>")
}
```

- [ ] **Step 4: 改方法論與未成形紀錄文案**

把 `methodologySection` 改成：

```go
func methodologySection() string {
	return "<ol><li>核對授權編號、範圍與有效期間，超出範圍的目標不進入任務。</li><li>整理專案內已歸檔資產與暴露面。</li><li>只透過已配置且經審批的掃描引擎，在授權範圍內收集結果。</li><li>將結果去重後寫入漏洞庫，保留攻擊前置條件、復現步驟、原始證據與實際影響。</li><li>依狀態區分待處理、已確認、已修復、誤報與忽略，並在複測備註中記錄關閉依據。</li></ol><p>報告照錄已驗證的利用步驟、原始請求與回應，不另合成新的攻擊操作步驟。</p>"
}
```

把 `stubSection` 的說明句改成：

```go
	b.WriteString("<p>以下來自專案筆記或目標清單，尚未具備目標與復現步驟，因此不列入發現總表。</p><ul>")
```

- [ ] **Step 5: 用利用優先順序取代修復優先順序**

把 `internal/pentestreport/report.go` 的 `remediationSection` 整個刪掉，換成：

```go
// exploitationPrioritySection 依可利用性排序，取代原本的「修復優先順序」。
//
// 排序鍵：嚴重度 → 信心。已修復與不列入交付的項目不出現。
// 復現步驟直接帶出來，讓排序清單本身就能當成攻擊路徑看。
func exploitationPrioritySection(findings []Finding) string {
	type entry struct {
		finding Finding
		rank    int
	}
	entries := make([]entry, 0, len(findings))
	for _, finding := range findings {
		if !countsTowardDelivery(finding.Status) || strings.EqualFold(finding.Status, "fixed") {
			continue
		}
		entries = append(entries, entry{finding: finding, rank: severityRank(finding.Severity)})
	}
	sort.SliceStable(entries, func(i, j int) bool {
		if entries[i].rank != entries[j].rank {
			return entries[i].rank > entries[j].rank
		}
		return entries[i].finding.Confidence > entries[j].finding.Confidence
	})
	if len(entries) == 0 {
		return "<p>目前沒有仍待利用的項目。</p>"
	}
	var b strings.Builder
	b.WriteString("<ol>")
	for _, item := range entries {
		b.WriteString("<li><strong>")
		b.WriteString(esc(item.finding.Title))
		b.WriteString("</strong>：")
		b.WriteString(esc(clip(item.finding.Target, 160)))
		b.WriteString("（")
		b.WriteString(esc(item.finding.Severity))
		b.WriteString(" · 信心 ")
		b.WriteString(fmt.Sprintf("%d", item.finding.Confidence))
		b.WriteString("）")
		if steps := strings.TrimSpace(item.finding.ReproSteps); steps != "" {
			b.WriteString("<pre>")
			b.WriteString(esc(clip(steps, 500)))
			b.WriteString("</pre>")
		}
		b.WriteString("</li>")
	}
	b.WriteString("</ol>")
	return b.String()
}

// severityRank 把嚴重度換算成排序權重。
func severityRank(severity string) int {
	switch strings.ToLower(strings.TrimSpace(severity)) {
	case "critical":
		return 4
	case "high":
		return 3
	case "medium":
		return 2
	case "low":
		return 1
	default:
		return 0
	}
}
```

- [ ] **Step 6: 補上 sort import**

把 `internal/pentestreport/report.go` 的 import 區塊改成：

```go
import (
	"fmt"
	"html"
	"sort"
	"strings"
	"time"
	"unicode/utf8"
)
```

- [ ] **Step 7: 跑測試確認通過**

Run: `go test ./internal/pentestreport/ -v`

Expected: PASS —— 既有 `TestBuildQualifiedWhenScopeAndFindingAreComplete` 會因為 `recommendation` 不再是缺口而仍然合格；`TestBuildDraftWhenRecommendationMissing` 在 Task 2 已改寫。

- [ ] **Step 8: Commit**

```bash
git add internal/pentestreport/report.go internal/pentestreport/report_test.go
git commit -m "feat(pentestreport): 章節重編為純紅隊交付物

- 第 6 章「修復優先順序」換成「利用優先順序」，依嚴重度與信心排序並帶出復現步驟
- 方法論刪掉「報告不生成攻擊載荷或操作手冊」，改為照錄已驗證的利用步驟
- 限制章節與頁尾去掉防禦性語氣
- writeSection 對空 body 跳過，讓攻擊鏈章在沒有事實時能整章缺席"
```

---

### Task 4: 攻擊鏈章 —— pentestreport 側型別與渲染

**Files:**
- Create: `internal/pentestreport/attackchain.go`
- Create: `internal/pentestreport/attackchain_test.go`
- Modify: `internal/pentestreport/report.go`（`Input` 加 `AttackChain` 欄位）

**Interfaces:**
- Consumes: Task 3 的 `writeSection` 空 body 跳過機制
- Produces:
  - `type AttackChainNode struct { Key, Category, Summary, Body, Confidence, RelatedVulnerabilityID string }`
  - `type AttackChainEdge struct { FromKey, ToKey, Type, Confidence string }`
  - `type AttackChain struct { Nodes []AttackChainNode; Edges []AttackChainEdge }`
  - `func InAttackChain(category, factKey string) bool`
  - `func attackChainSection(chain AttackChain) string`（package-private，Task 5 只用 `AttackChain` 型別）

- [ ] **Step 1: 寫失敗的測試**

建立 `internal/pentestreport/attackchain_test.go`：

```go
package pentestreport

import (
	"strings"
	"testing"
)

func TestInAttackChainAcceptsCategoryOrFactKeyPrefix(t *testing.T) {
	cases := []struct {
		category string
		factKey  string
		want     bool
	}{
		{"finding", "finding/sqli-login", true},
		{"chain", "chain/anything", true},
		{"exploit", "exploit/upload-rce", true},
		{"poc", "poc/x", true},
		{"note", "finding/sqli-login", true},
		{"note", "exploit/upload-rce", true},
		{"target", "target/primary_domain", false},
		{"auth", "auth/session", false},
		{"infra", "infra/docker", false},
		{"business", "business/flow", false},
	}
	for _, item := range cases {
		if got := InAttackChain(item.category, item.factKey); got != item.want {
			t.Errorf("InAttackChain(%q,%q)=%v want %v", item.category, item.factKey, got, item.want)
		}
	}
}

func TestAttackChainSectionRendersNodesAndEdges(t *testing.T) {
	html := attackChainSection(AttackChain{
		Nodes: []AttackChainNode{
			{Key: "chain/login-bypass", Category: "chain", Summary: "登入繞過鏈",
				Body: "入口 /login → 步驟 1 → 原始請求", Confidence: "confirmed"},
			{Key: "exploit/admin-takeover", Category: "exploit", Summary: "接管後台",
				Body: "利用檔案上傳", Confidence: "confirmed", RelatedVulnerabilityID: "v-001"},
		},
		Edges: []AttackChainEdge{
			{FromKey: "chain/login-bypass", ToKey: "exploit/admin-takeover", Type: "exploits", Confidence: "confirmed"},
		},
	})
	for _, want := range []string{
		"chain/login-bypass",
		"登入繞過鏈",
		"入口 /login",
		"exploit/admin-takeover",
		"v-001",
		"exploits",
	} {
		if !strings.Contains(html, want) {
			t.Errorf("攻擊鏈章缺少 %q", want)
		}
	}
}

func TestAttackChainSectionEmptyReturnsEmptyString(t *testing.T) {
	if got := attackChainSection(AttackChain{}); got != "" {
		t.Fatalf("空鏈應回空字串, got %q", got)
	}
}
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/pentestreport/ -run 'TestInAttackChain|TestAttackChainSection' -v`

Expected: FAIL —— `undefined: InAttackChain`、`undefined: attackChainSection`。

- [ ] **Step 3: 寫攻擊鏈章**

建立 `internal/pentestreport/attackchain.go`：

```go
package pentestreport

import (
	"sort"
	"strings"
)

// AttackChainNode 是專案事實圖中的一個節點。
//
// Body 依黑板規範填寫完整攻擊鏈（入口 → 逐步利用 → 原始請求/響應或命令 → 現象），
// 見 internal/projectprompt/blackboard.go 的事實寫入規範。
type AttackChainNode struct {
	Key                    string
	Category               string
	Summary                string
	Body                   string
	Confidence             string
	RelatedVulnerabilityID string
}

// AttackChainEdge 是事實之間的關係邊。
//
// EdgeType 取值對應黑板的關係邊規範：discovered_on、depends_on、leads_to、
// enables、exploits、contains、part_of、supports。
type AttackChainEdge struct {
	FromKey    string
	ToKey      string
	Type       string
	Confidence string
}

// AttackChain 是報告「攻擊鏈」章的輸入。
type AttackChain struct {
	Nodes []AttackChainNode
	Edges []AttackChainEdge
}

// attackChainCategories 是納入攻擊鏈章的事實類別，以及它們在章節內的排序權重。
var attackChainCategories = map[string]int{
	"chain":   0,
	"exploit": 1,
	"poc":     2,
	"finding": 3,
}

// attackChainKeyPrefixes 是對應的 fact_key 前綴。
var attackChainKeyPrefixes = []string{"finding/", "chain/", "exploit/", "poc/"}

// InAttackChain 回傳這條事實是否屬於攻擊鏈章。
//
// 判定同時看 category 與 fact_key 前綴，兩者取聯集：
// 代理常常只寫了 fact_key（例如 finding/sqli-login）卻沒填 category，
// 只看 category 會把這種事實靜默丟掉。
func InAttackChain(category, factKey string) bool {
	if _, ok := attackChainCategories[strings.ToLower(strings.TrimSpace(category))]; ok {
		return true
	}
	key := strings.ToLower(strings.TrimSpace(factKey))
	for _, prefix := range attackChainKeyPrefixes {
		if strings.HasPrefix(key, prefix) {
			return true
		}
	}
	return false
}

// attackChainSection 渲染攻擊鏈章；沒有節點時回空字串，讓整章缺席。
func attackChainSection(chain AttackChain) string {
	if len(chain.Nodes) == 0 {
		return ""
	}
	nodes := make([]AttackChainNode, len(chain.Nodes))
	copy(nodes, chain.Nodes)
	sort.SliceStable(nodes, func(i, j int) bool {
		return chainCategoryRank(nodes[i]) < chainCategoryRank(nodes[j])
	})

	var b strings.Builder
	b.WriteString("<p>以下攻擊鏈取自本專案的事實圖，記錄對話中確認的利用路徑。</p>")
	for _, node := range nodes {
		b.WriteString("<article class=\"chain-node\">")
		b.WriteString("<h3>")
		b.WriteString(esc(node.Key))
		b.WriteString("</h3>")
		b.WriteString("<p><strong>")
		b.WriteString(esc(node.Category))
		b.WriteString("</strong> · 信心 ")
		b.WriteString(esc(node.Confidence))
		if id := strings.TrimSpace(node.RelatedVulnerabilityID); id != "" {
			b.WriteString(" · 關聯漏洞 ")
			b.WriteString(esc(id))
		}
		b.WriteString("</p>")
		if summary := strings.TrimSpace(node.Summary); summary != "" {
			b.WriteString("<p>")
			b.WriteString(esc(summary))
			b.WriteString("</p>")
		}
		if body := strings.TrimSpace(node.Body); body != "" {
			b.WriteString("<pre>")
			b.WriteString(esc(body))
			b.WriteString("</pre>")
		}
		b.WriteString("</article>")
	}

	if len(chain.Edges) > 0 {
		b.WriteString("<h4>關係</h4><ul>")
		for _, edge := range chain.Edges {
			b.WriteString("<li>")
			b.WriteString(esc(edge.FromKey))
			b.WriteString(" ──")
			b.WriteString(esc(edge.Type))
			b.WriteString("──▶ ")
			b.WriteString(esc(edge.ToKey))
			b.WriteString("</li>")
		}
		b.WriteString("</ul>")
	}
	return b.String()
}

// chainCategoryRank 回傳節點的排序權重；未知類別排最後。
func chainCategoryRank(node AttackChainNode) int {
	if rank, ok := attackChainCategories[strings.ToLower(strings.TrimSpace(node.Category))]; ok {
		return rank
	}
	return len(attackChainCategories)
}
```

> 這個檔案用不到 `fmt`，所以 import 只有 `sort` 與 `strings`。

- [ ] **Step 4: 把 AttackChain 接進 Input 與 Build**

在 `internal/pentestreport/report.go` 的 `Input` 結構加上欄位：

```go
type Input struct {
	ProjectID          string
	ProjectName        string
	ProjectDescription string
	GeneratedAt        time.Time
	Authorizations     []Authorization
	Runs               []Run
	Findings           []Finding
	AttackChain        AttackChain
}
```

把 `Build` 裡的 `writeSection(&b, "4. 攻擊鏈", "")` 改成：

```go
	writeSection(&b, "4. 攻擊鏈", attackChainSection(in.AttackChain))
```

- [ ] **Step 5: 跑測試確認通過**

Run: `go test ./internal/pentestreport/ -v`

Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add internal/pentestreport/attackchain.go internal/pentestreport/attackchain_test.go internal/pentestreport/report.go
git commit -m "feat(pentestreport): 新增攻擊鏈章

把專案事實圖（project_facts + project_fact_edges）渲染成一章紅隊攻擊鏈。
節點的 body 依黑板規範本來就是完整利用路徑；關係邊用來呈現
exploits / discovered_on / enables 之類的利用關係。

沒有節點時整章缺席，不留空章。"
```

---

### Task 5: handler 端把事實圖接進報告

**Files:**
- Modify: `internal/handler/pentest_report.go:18-65`（`ProjectPentestReport`）、`internal/handler/pentest_report.go:67-106`（`pentestReportInput`）
- Test: `internal/handler/pentest_report_test.go`

**Interfaces:**
- Consumes: Task 4 的 `pentestreport.AttackChain`、`pentestreport.AttackChainNode`、`pentestreport.AttackChainEdge`、`pentestreport.InAttackChain`
- Produces: `func (h *SecurityOpsHandler) pentestReportAttackChain(projectID string) (pentestreport.AttackChain, error)`；`pentestReportInput(project, runs, findings, chain, now)` 的新簽章。

- [ ] **Step 1: 寫失敗的測試**

在 `internal/handler/pentest_report_test.go` 末尾新增：

```go
func TestProjectPentestReportIncludesAttackChainFromProjectFacts(t *testing.T) {
	gin.SetMode(gin.TestMode)
	db, err := database.NewDB(filepath.Join(t.TempDir(), "report.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err := db.CreateProject(&database.Project{ID: "chain-proj", Name: "鏈測試", Status: "active"}); err != nil {
		t.Fatal(err)
	}
	for _, fact := range []*database.ProjectFact{
		{ProjectID: "chain-proj", FactKey: "chain/login-bypass", Category: "chain",
			Summary: "登入繞過鏈", Body: "入口 /login → 帶入 ' OR 1=1-- → 回應 302", Confidence: "confirmed"},
		{ProjectID: "chain-proj", FactKey: "exploit/admin-takeover", Category: "exploit",
			Summary: "接管後台", Body: "利用檔案上傳取得後台權限", Confidence: "confirmed"},
		{ProjectID: "chain-proj", FactKey: "target/primary_domain", Category: "target",
			Summary: "主網域", Body: "app.example.com", Confidence: "confirmed"},
	} {
		if _, err := db.UpsertProjectFact(fact); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := db.AddProjectFactEdge("chain-proj", database.ProjectFactEdgeInput{
		To:         "exploit/admin-takeover",
		Type:       "exploits",
		Confidence: "confirmed",
	}, "chain/login-bypass", ""); err != nil {
		t.Fatal(err)
	}

	h := NewSecurityOpsHandler(db, &config.Config{}, zap.NewNop())
	h.now = func() time.Time { return time.Date(2026, 10, 20, 0, 0, 0, 0, time.UTC) }
	router := gin.New()
	router.Use(func(c *gin.Context) {
		c.Set(security.ContextSessionKey, security.Session{UserID: "owner-a", Scope: database.RBACScopeAll})
		c.Next()
	})
	api := router.Group("/api")
	api.GET("/projects/:id/pentest-report", h.ProjectPentestReport)

	status, body := doJSON(router, http.MethodGet, "/api/projects/chain-proj/pentest-report", nil)
	if status != http.StatusOK {
		t.Fatalf("report status %d body %s", status, body)
	}
	html := string(body)
	if !strings.Contains(html, "4. 攻擊鏈") {
		t.Fatalf("報告缺少攻擊鏈章: %s", html[:min(400, len(html))])
	}
	if !strings.Contains(html, "chain/login-bypass") || !strings.Contains(html, "入口 /login") {
		t.Fatalf("攻擊鏈節點未渲染: %s", html[:min(600, len(html))])
	}
	if !strings.Contains(html, "exploits") {
		t.Fatalf("攻擊鏈關係邊未渲染: %s", html[:min(600, len(html))])
	}
	if strings.Contains(html, "target/primary_domain") {
		t.Fatal("target 類別不該進攻擊鏈章")
	}
}
```

> 已核實的簽章：`db.UpsertProjectFact(f *ProjectFact) (*ProjectFact, error)`（`internal/database/project.go:458`）、
> `db.AddProjectFactEdge(projectID string, in ProjectFactEdgeInput, sourceFactKey, sourceConversationID string) (*ProjectFactEdge, error)`（`internal/database/project_fact_edges.go:262`）、
> `db.ListProjectFacts(projectID string, filter ProjectFactListFilter, limit, offset int) ([]*ProjectFact, error)`（`internal/database/project.go:362`）、
> `db.ListProjectFactEdgesByProject(projectID string) ([]*ProjectFactEdge, error)`（`internal/database/project_fact_edges.go:101`）。
> 關係邊的 `sourceFactKey` 與 `in.To` 分別是邊的兩端；兩個端點都必須留在鏈上才會被輸出。

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/handler/ -run TestProjectPentestReportIncludesAttackChainFromProjectFacts -v`

Expected: FAIL —— 報告不含「4. 攻擊鏈」。

- [ ] **Step 3: 改 handler 的映射**

把 `internal/handler/pentest_report.go` 的 `pentestReportInput` 簽章改成：

```go
func pentestReportInput(project *database.Project, runs []database.SecurityOpsRun, findings []*database.Vulnerability, chain pentestreport.AttackChain, now time.Time) pentestreport.Input {
```

並在函式開頭把 `chain` 放進 `Input`：

```go
	in := pentestreport.Input{
		ProjectID:          project.ID,
		ProjectName:        project.Name,
		ProjectDescription: project.Description,
		GeneratedAt:        now,
		AttackChain:        chain,
	}
```

- [ ] **Step 4: 讀取事實圖**

在 `internal/handler/pentest_report.go` 新增：

```go
// pentestReportAttackChain 把專案事實圖讀成報告的攻擊鏈章輸入。
//
// 事實圖是對話攻擊鏈的沉澱處（promote-attack-chain），節點的 body 依黑板規範
// 已是完整利用路徑；關係邊只在兩個端點都留在鏈上時才輸出。
func (h *SecurityOpsHandler) pentestReportAttackChain(projectID string) (pentestreport.AttackChain, error) {
	chain := pentestreport.AttackChain{}
	facts, err := h.db.ListProjectFacts(projectID, database.ProjectFactListFilter{ExcludeDeprecated: true}, 500, 0)
	if err != nil {
		return chain, err
	}
	kept := map[string]bool{}
	for _, fact := range facts {
		if fact == nil {
			continue
		}
		if !pentestreport.InAttackChain(fact.Category, fact.FactKey) {
			continue
		}
		kept[fact.FactKey] = true
		chain.Nodes = append(chain.Nodes, pentestreport.AttackChainNode{
			Key:                    fact.FactKey,
			Category:               fact.Category,
			Summary:                fact.Summary,
			Body:                   fact.Body,
			Confidence:             fact.Confidence,
			RelatedVulnerabilityID: fact.RelatedVulnerabilityID,
		})
	}
	edges, err := h.db.ListProjectFactEdgesByProject(projectID)
	if err != nil {
		return chain, err
	}
	for _, edge := range edges {
		if edge == nil {
			continue
		}
		if !kept[edge.SourceFactKey] || !kept[edge.TargetFactKey] {
			continue
		}
		chain.Edges = append(chain.Edges, pentestreport.AttackChainEdge{
			FromKey:    edge.SourceFactKey,
			ToKey:      edge.TargetFactKey,
			Type:       edge.EdgeType,
			Confidence: edge.Confidence,
		})
	}
	return chain, nil
}
```

在 `ProjectPentestReport` 裡，`result := pentestreport.Build(...)` 之前插入：

```go
	chain, err := h.pentestReportAttackChain(projectID)
	if err != nil {
		writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取攻击链")
		return
	}
	result := pentestreport.Build(pentestReportInput(project, runs, findings, chain, h.now()))
```

- [ ] **Step 5: 跑測試確認通過**

Run: `go test ./internal/handler/ -run 'TestProjectPentestReport' -v`

Expected: PASS —— 既有 `TestProjectPentestReportIsQualifiedForAuthorizedCleanProject` 也要過（該專案沒有事實 → 攻擊鏈章缺席 → 仍合格）。

- [ ] **Step 6: Commit**

```bash
git add internal/handler/pentest_report.go internal/handler/pentest_report_test.go
git commit -m "feat(handler): 報告接上專案事實圖的攻擊鏈

報告輸入過去只讀漏洞表，project_facts 裡的攻擊鏈永遠進不了交付物。
現在把 category 或 fact_key 屬於 finding/chain/exploit/poc 的事實讀成
攻擊鏈章，關係邊只在兩個端點都留在鏈上時輸出。"
```

---

### Task 6: 工具契約 —— recommendation 降選填、preconditions 升必填

**Files:**
- Modify: `internal/app/vulnerability_tools.go:179-197`（`missingVulnerabilityReproFields`）、`internal/app/vulnerability_tools.go:267-292`（schema）
- Test: `internal/app/vulnerability_tools_test.go`（新增）

**Interfaces:**
- Consumes: 無
- Produces: `record_vulnerability` 工具的必填集合變為 `{target, vulnerability_type, description, reproduction_steps, evidence, impact, preconditions}`。

- [ ] **Step 1: 寫失敗的測試**

建立 `internal/app/vulnerability_tools_test.go`：

```go
package app

import (
	"context"
	"path/filepath"
	"strings"
	"testing"

	"jysecai/internal/database"
	"jysecai/internal/mcp"
	"jysecai/internal/mcp/builtin"

	"go.uber.org/zap"
)

func TestRecordVulnerabilityAcceptsMissingRecommendation(t *testing.T) {
	_, server, cleanup := newVulnerabilityToolTestServer(t)
	defer cleanup()

	args := map[string]interface{}{
		"title":              "登入參數可注入",
		"description":        "登入參數 username 可注入。",
		"severity":           "high",
		"vulnerability_type": "SQL注入",
		"target":             "https://app.example.com/login",
		"preconditions":      "已取得一般用戶 Session。",
		"reproduction_steps": "1. 帶入 ' OR 1=1--",
		"evidence":           "原始請求與回應",
		"impact":             "可繞過登入。",
	}
	ctx := mcp.WithMCPConversationID(context.Background(), "conv-1")
	result, _, err := server.CallTool(ctx, builtin.ToolRecordVulnerability, args)
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result == nil || result.IsError {
		t.Fatalf("不帶 recommendation 應該能成功, got %s", resultText(result))
	}
}

func TestRecordVulnerabilityRequiresPreconditions(t *testing.T) {
	_, server, cleanup := newVulnerabilityToolTestServer(t)
	defer cleanup()

	args := map[string]interface{}{
		"title":              "登入參數可注入",
		"description":        "登入參數 username 可注入。",
		"severity":           "high",
		"vulnerability_type": "SQL注入",
		"target":             "https://app.example.com/login",
		"reproduction_steps": "1. 帶入 ' OR 1=1--",
		"evidence":           "原始請求與回應",
		"impact":             "可繞過登入。",
	}
	ctx := mcp.WithMCPConversationID(context.Background(), "conv-1")
	result, _, err := server.CallTool(ctx, builtin.ToolRecordVulnerability, args)
	if err != nil {
		t.Fatalf("CallTool: %v", err)
	}
	if result == nil || !result.IsError {
		t.Fatal("缺 preconditions 應該報錯")
	}
	if !strings.Contains(resultText(result), "preconditions") {
		t.Fatalf("錯誤訊息應指出 preconditions: %s", resultText(result))
	}
}

// newVulnerabilityToolTestServer 建立只註冊漏洞工具的 MCP server。
// registerVulnerabilityTools 是 package-private，所以測試必須留在 package app。
func newVulnerabilityToolTestServer(t *testing.T) (*database.DB, *mcp.Server, func()) {
	t.Helper()
	db, err := database.NewDB(filepath.Join(t.TempDir(), "vuln.db"), zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	server := mcp.NewServer(zap.NewNop())
	registerVulnerabilityTools(server, db, zap.NewNop())
	return db, server, func() { _ = db.Close() }
}

// resultText 把工具回應的內文串成純文字，方便斷言。
func resultText(result *mcp.ToolResult) string {
	if result == nil {
		return ""
	}
	var b strings.Builder
	for _, content := range result.Content {
		if content.Type == "text" {
			b.WriteString(content.Text)
		}
	}
	return b.String()
}
```

> 已核實的簽章：`registerVulnerabilityTools(mcpServer *mcp.Server, db *database.DB, logger *zap.Logger)`（package-private，見 `internal/app/vulnerability_tools.go:210`）、
> `mcp.NewServer(logger *zap.Logger) *Server`（`internal/mcp/server.go:132`）、
> `server.CallTool(ctx, toolName, args) (*mcp.ToolResult, string, error)`（`internal/mcp/server.go:962`，**回三個值**）、
> `builtin.ToolRecordVulnerability = "record_vulnerability"`（`internal/mcp/builtin/constants.go:7`）。
> 工具不要求對話存在（`conversationID` 只從 ctx 取值），所以測試可以用 `conv-1`。

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/app/ -run 'TestRecordVulnerability' -v`

Expected: FAIL —— 目前缺 `recommendation` 會報錯、缺 `preconditions` 不會報錯，與斷言相反。

- [ ] **Step 3: 改必填清單**

把 `internal/app/vulnerability_tools.go` 的 `missingVulnerabilityReproFields` 裡的必填清單改成：

```go
	required := []struct {
		key   string
		label string
	}{
		{"target", "target（受影响的 URL/IP/服务/接口）"},
		{"vulnerability_type", "vulnerability_type（漏洞类型）"},
		{"description", "description（漏洞摘要与触发点）"},
		{"preconditions", "preconditions（攻击前置条件）"},
		{"reproduction_steps", "reproduction_steps（可逐步执行的复现步骤）"},
		{"evidence", "evidence（POC、原始请求/响应、命令输出或截图/日志证据）"},
		{"impact", "impact（确认后的实际影响）"},
	}
```

- [ ] **Step 4: 改 schema 說明與 required**

把 `internal/app/vulnerability_tools.go` 的 schema 兩個欄位改成：

```go
				"preconditions": map[string]interface{}{
					"type":        "string",
					"description": "攻击前置条件（必需）：复现该漏洞所需的登录状态、权限、账号、Header/Cookie、特定数据、网络位置、环境/版本等；无前置条件可写“无”。",
				},
```

```go
				"recommendation": map[string]interface{}{
					"type":        "string",
					"description": "利用建议（选填）：后续可接续的利用向量、扩大路径，或此漏洞在攻击链中的位置。不要写修复方案。",
				},
```

把 `"required"` 改成：

```go
			"required": []string{"title", "description", "severity", "vulnerability_type", "target", "preconditions", "reproduction_steps", "evidence", "impact"},
```

- [ ] **Step 5: 改必填錯誤訊息**

`internal/app/vulnerability_tools.go:322` 的訊息結尾寫著「前置条件和复测方式为推荐填写项」——
前置條件現在是必填，這句會誤導代理。改成：

```go
			return textResult("错误: 漏洞记录缺少必填信息，请补充后再记录：\n- "+strings.Join(missing, "\n- ")+"\n\n必填项用于确保单条记录可独立复现；复测方式为推荐填写项。", true), nil
```

- [ ] **Step 6: 跑測試確認通過**

Run: `go test ./internal/app/ -run 'TestRecordVulnerability' -v`

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add internal/app/vulnerability_tools.go internal/app/vulnerability_tools_test.go
git commit -m "feat(app): record_vulnerability 契約改成紅隊導向

- recommendation 從必填改成選填，說明改為「利用建议」並明講不要寫修復方案
- preconditions 升為必填，說明改為攻擊語意（登入態/權限/帳號/Cookie/特定資料）
- 必填錯誤訊息同步：前置條件不再是「推荐填写项」

原本每個對話回合都靠這段 schema 說明逼掃描代理寫防禦建議，白白偷 token。"
```

---

### Task 7: 黑板提示層同步

**Files:**
- Modify: `internal/projectprompt/blackboard.go:82-88`
- Test: `internal/projectprompt/blackboard_test.go`（新增）

**Interfaces:**
- Consumes: Task 6 的工具必填集合
- Produces: `FactRecordingBlackboardSection(coordinatorDelegate bool) string` 的輸出不再含「修复建议」。

- [ ] **Step 1: 寫失敗的測試**

建立 `internal/projectprompt/blackboard_test.go`：

```go
package projectprompt

import (
	"strings"
	"testing"
)

func TestBlackboardSectionHasNoRemediationInstruction(t *testing.T) {
	section := FactRecordingBlackboardSection(false)
	for _, unwanted := range []string{"修复建议", "修復建議"} {
		if strings.Contains(section, unwanted) {
			t.Errorf("黑板提示仍要求寫修復建議: %q", unwanted)
		}
	}
	for _, want := range []string{"攻击前置条件", "复现步骤"} {
		if !strings.Contains(section, want) {
			t.Errorf("黑板提示缺少 %q", want)
		}
	}
}
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/projectprompt/ -run TestBlackboardSectionHasNoRemediationInstruction -v`

Expected: FAIL —— 目前含「修复建议」。

- [ ] **Step 3: 改黑板提示**

把 `internal/projectprompt/blackboard.go:82-88` 那一段改成：

```go
	b.WriteString("- **可交付漏洞**：使用 ")
	b.WriteString(builtin.ToolRecordVulnerability)
	b.WriteString("，含标题、严重程度、类型、目标、攻击前置条件、证明（POC）、复现步骤、影响。记前可先 ")
	b.WriteString(builtin.ToolListVulnerabilities)
	b.WriteString(" 查重，详情用 ")
	b.WriteString(builtin.ToolGetVulnerability)
	b.WriteString("(id)（默认仅当前项目/会话）。\n")
```

- [ ] **Step 4: 跑測試確認通過**

Run: `go test ./internal/projectprompt/ -v`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add internal/projectprompt/blackboard.go internal/projectprompt/blackboard_test.go
git commit -m "fix(projectprompt): 黑板提示的可交付漏洞說明改為紅隊欄位

這是藍隊課稅的第三個注入點：工具 schema、required 清單、黑板提示。
只改前兩處，黑板仍會叫代理補寫修復建議。"
```

---

### Task 8: 前端 i18n 與建檔表單

**Files:**
- Modify: `web/static/i18n/zh-CN.json`、`web/static/i18n/en-US.json`
- Modify: `web/static/js/vulnerability.js:1718-1745`
- Modify: `web/templates/index.html:7273,7289-7290`
- Test: `internal/app/web_i18n_test.go`（既有測試會驗證 key 集合一致）

**Interfaces:**
- Consumes: Task 6 的必填集合
- Produces: 使用者可見文案改為紅隊語意；前端表單必填集合與後端一致。

- [ ] **Step 1: 寫失敗的測試**

在 `web/static/js/` 沒有既有的 vulnerability 表單測試，因此先加一個 cjs 測試檔
`web/static/js/vulnerability-form-required.test.cjs`，用 `node --test` 跑：

```javascript
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..', '..');
const source = fs.readFileSync(path.join(repoRoot, 'web/static/js/vulnerability.js'), 'utf8');

test('建檔必填集合含前置條件、不含修復建議', () => {
  const required = source.match(/if \(!conversationId[\s\S]*?\) \{/);
  assert.ok(required, '找不到建檔必填判斷');
  assert.ok(required[0].includes('preconditions'), '必填判斷應含 preconditions');
  assert.ok(!required[0].includes('recommendation'), '必填判斷不該含 recommendation');
});

test('表單把前置條件標為必填、修復建議標為選填', () => {
  const html = fs.readFileSync(path.join(repoRoot, 'web/templates/index.html'), 'utf8');
  const preconditions = html.match(/<label for="vulnerability-preconditions"[\s\S]*?<\/label>/);
  const recommendation = html.match(/<label for="vulnerability-recommendation"[\s\S]*?<\/label>/);
  assert.ok(preconditions && preconditions[0].includes('color: red'), '前置條件應標必填');
  assert.ok(recommendation && !recommendation[0].includes('color: red'), '修復建議不該標必填');
});
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `node --test web/static/js/vulnerability-form-required.test.cjs`

Expected: FAIL —— 必填判斷仍含 `recommendation`，前置條件未標必填。

- [ ] **Step 3: 改前端必填判斷**

把 `web/static/js/vulnerability.js:1718-1721` 那段改成：

```javascript
    const recommendation = document.getElementById('vulnerability-recommendation').value.trim();
    const preconditions = document.getElementById('vulnerability-preconditions').value.trim();
    if (!conversationId || !title || !description || !severity || !type || !target || !preconditions || !reproductionSteps || !evidence || !impact) {
        alert(vulnT('vulnerabilityPage.saveRequiredFields'));
```

並把後面送出的 payload 補上 `preconditions`（若原本沒有的話）：

```javascript
        preconditions: preconditions,
```

- [ ] **Step 4: 改 index.html 的標記與 fallback 文案**

把 `web/templates/index.html:7273` 改成：

```html
                    <label for="vulnerability-preconditions"><span data-i18n="vulnerabilityModal.preconditions">前置条件</span> <span style="color: red;">*</span></label>
```

把 `web/templates/index.html:7289` 改成：

```html
                    <label for="vulnerability-recommendation"><span data-i18n="vulnerabilityModal.recommendation">利用建议</span></label>
```

> `data-i18n` 元素內的中文不會被 `TestWebI18nNoNewHardcodedText` 當成硬編碼，所以可以放心改。

- [ ] **Step 5: 改 i18n（兩個語系都要改）**

`web/static/i18n/zh-CN.json`：

| key | 新值 |
| --- | --- |
| `vulnerabilityPage.saveRequiredFields` | `请填写必填字段：会话ID、标题、描述、严重程度、漏洞类型、目标、前置条件、复现步骤、证据/POC和影响` |
| `vulnerabilityPage.detailRecommendation` | `利用建议` |
| `vulnerabilityMd.headingRecommendation` | `利用建议` |
| `vulnerabilityModal.recommendation` | `利用建议` |
| `vulnerabilityModal.recommendationPlaceholder` | `写后续可接续的利用向量、扩大路径，或此漏洞在攻击链中的位置。不要写修复方案。` |

`web/static/i18n/en-US.json`：

| key | 新值 |
| --- | --- |
| `vulnerabilityPage.saveRequiredFields` | `Please fill in conversation ID, title, description, severity, type, target, preconditions, reproduction steps, evidence/POC, and impact` |
| `vulnerabilityPage.detailRecommendation` | `Exploitation guidance` |
| `vulnerabilityMd.headingRecommendation` | `Exploitation guidance` |
| `vulnerabilityModal.recommendation` | `Exploitation guidance` |
| `vulnerabilityModal.recommendationPlaceholder` | `Write the follow-on exploitation vectors, the expansion path, or where this sits in the attack chain. Do not write remediation.` |

> **兩個 JSON 的 key 集合必須一致** —— 只改值、不新增或刪除 key。

- [ ] **Step 6: 跑測試確認通過**

Run: `node --test web/static/js/vulnerability-form-required.test.cjs` && `go test ./internal/app/ -run 'TestWebI18n' -v`

Expected: PASS —— `TestWebI18nDictionariesKeySetsMatch` 與 `TestWebI18nNoNewHardcodedText` 都通過（沒有新增基準外的硬編中文）。

- [ ] **Step 7: Commit**

```bash
git add web/static/i18n/zh-CN.json web/static/i18n/en-US.json web/static/js/vulnerability.js web/templates/index.html web/static/js/vulnerability-form-required.test.cjs
git commit -m "feat(web): 建檔表單與文案改為紅隊語意

- 前置條件改為必填，修復建議改為選填的「利用建議」
- 兩個語系的 key 集合維持一致，沒有新增基準外的硬編中文"
```

---

### Task 9: 文件雙語同步

**Files:**
- Modify: `docs/zh-CN/pentest-report.md`
- Modify: `docs/en-US/pentest-report.md`

**Interfaces:**
- Consumes: Task 1–8 的最終行為
- Produces: 無程式碼介面。

- [ ] **Step 1: 改 `docs/zh-CN/pentest-report.md`**

改成：

```markdown
# 滲透測試報告

專案頁、Web 安全掃描與資產偵察都可以下載同一份報告：`GET /api/projects/{id}/pentest-report`。

報告在請求當下，用該專案已入庫的漏洞、授權掃描任務與專案事實圖組出來。任務狀態變成已完成時，掃描頁會提示可以下載，不需要再手寫文件。

`?format=meta` 只返回是否合格與缺口。以下都齊才標成合格交付：

- 專案名稱
- 授權編號、授權人、範圍、有效期間，以及已勾選的授權確認
- 每筆待處理、已確認或待判定的漏洞都有標題、嚴重度、目標、描述或證據、影響，以及攻擊前置條件或復現步驟
- 沒有仍標成待判定的項目

沒有漏洞但授權完整時，報告會寫明未發現需列管漏洞，這也算合格。缺欄位時仍可下載，文首標成草稿並列出缺口。

## 章節結構

1. 執行摘要
2. 授權與範圍
3. 方法
4. 攻擊鏈 —— 取自專案事實圖，記錄對話中確認的利用路徑與關係邊
5. 發現總表
6. 發現詳述 —— 說明、前置條件、復現步驟、證據、影響、複測
7. 利用優先順序 —— 依嚴重度與信心排序，帶出復現步驟
8. 未成形紀錄
9. 任務紀錄
10. 限制

報告照錄漏洞庫裡已經寫下的證據、復現步驟與事實圖中的攻擊鏈，不另合成新的攻擊操作步驟。
```

- [ ] **Step 2: 改 `docs/en-US/pentest-report.md`**

先讀現有內容，再改寫成與中文版逐段對應的英文版，章節結構一致：

```markdown
# Penetration Test Report

The project page, the Web security scan page, and asset reconnaissance all download the same report: `GET /api/projects/{id}/pentest-report`.

The report is assembled at request time from the project's stored vulnerabilities, authorized scan runs, and the project fact graph. When a run reaches the completed state the scan page reports that the report is ready to download, so no manual document is needed.

`?format=meta` returns only the qualification verdict and the gaps. The report is marked as a qualified deliverable when all of the following hold:

- Project name is present
- An authorization record with id, approver, scope, validity window, and the attestation checkbox
- Every open, confirmed, or undetermined finding has a title, severity, target, a description or evidence, an impact, and either attack preconditions or reproduction steps
- Nothing is still marked as undetermined

A project with no vulnerabilities but a complete authorization still produces a report stating that no findings require tracking, and that counts as qualified. When fields are missing the report can still be downloaded; the cover marks it as a draft and lists the gaps.

## Section structure

1. Executive summary
2. Authorization and scope
3. Methodology
4. Attack chain — taken from the project fact graph: the confirmed exploitation paths and their relation edges
5. Findings table
6. Finding details — description, preconditions, reproduction steps, evidence, impact, retest
7. Exploitation priority — ordered by severity and confidence, with reproduction steps inline
8. Unformed records
9. Task log
10. Limitations

The report transcribes the evidence, reproduction steps, and attack chain already stored in the vulnerability database and the fact graph. It does not synthesize new attack procedures.
```

- [ ] **Step 3: Commit**

```bash
git add docs/zh-CN/pentest-report.md docs/en-US/pentest-report.md
git commit -m "docs: 滲透測試報告文件同步紅隊章節結構（bilingual）"
```

---

### Task 10: 全域回歸驗證

**Files:** 無新檔案；本 task 只驗證。

**Interfaces:**
- Consumes: Task 1–9 的全部改動
- Produces: 通過的驗證證據。

- [ ] **Step 1: vet 全樹**

Run: `go vet ./...`

Expected: 無輸出（成功）。

- [ ] **Step 2: 跑受影響的三個套件**

Run: `go test ./internal/pentestreport/... ./internal/app/... ./internal/handler/... ./internal/projectprompt/...`

Expected: 全部 PASS。

- [ ] **Step 3: 跑完整測試樹**

Run: `go test ./...`

Expected: 全部 PASS。若有與本次改動無關的既有失敗，**記錄下來，不要順手修**。

- [ ] **Step 4: 跑 race 測試（僅本次碰過的套件）**

Run: `go test -race ./internal/handler/... ./internal/app/... ./internal/pentestreport/...`

Expected: PASS。

- [ ] **Step 5: 跑授權邊界的阻擋測試**

Run:
```bash
go test -run 'TestResolveWithinPromptBase|TestMaskProviderSecrets|TestMergeProviderSecrets|TestGetConfigResponseCarries|TestBeaconTemplate|TestQuoteTemplateData|TestValidateBeaconHost|TestResolveBeaconDialHost|TestRedactMCP|TestMergeExternalMCP|TestExternalMCPConfigForResponse|TestEscapeCSVCell|TestMaskTerminalCommand|TestIsBlockedIP|TestValidateOutboundURL|TestWebshell.*|TestOperator|TestRBAC' ./internal/...
```

Expected: PASS —— 授權與審批層沒有被這次改動影響。

- [ ] **Step 6: 跑前端測試**

Run: `node --test web/static/js/*.test.cjs`

Expected: 全部 PASS。

- [ ] **Step 7: 確認 diff 沒有碰 POST 路徑與授權層**

Run:
```bash
git diff --stat main...HEAD -- internal/handler/agent.go internal/multiagent/ internal/handler/security_ops.go internal/security/
```

Expected: 除了 `internal/handler/security_ops.go` 之外都不該有變更；`security_ops.go` 若有變更必須是零變更 —— 出現變更就是違規。

Run:
```bash
git diff main...HEAD -- internal/handler/security_ops.go internal/security/ | head -20
```

Expected: 無輸出。

- [ ] **Step 8: 最終 commit（若 Step 1–7 有任何修正）**

```bash
git status --short
git add <本次改動的檔案>
git commit -m "chore: 紅隊交付物改造的回歸修正"
```

若沒有修正，略過這一步。

---

## 完成定義

- `go vet ./...` 與 `go test ./...` 全綠
- 授權邊界測試全綠，且 `internal/handler/security_ops.go` 與 `internal/security/` 的 diff 為空
- 一份含前置條件、復現步驟、證據、影響與事實圖攻擊鏈的專案，產生的報告：
  - 含「4. 攻擊鏈」章，節點與關係邊都出現
  - 發現詳述含「前置條件」「復現步驟」
  - 全文不含「修復建議」「已歸檔驗證筆記」「修復優先順序」
  - 判定為「合格交付」
- `record_vulnerability` 不帶 `recommendation` 也能成功；不帶 `preconditions` 會得到明確的必填錯誤
- 工具 schema、必填清單、黑板提示三處都不再出現「修复建议」
