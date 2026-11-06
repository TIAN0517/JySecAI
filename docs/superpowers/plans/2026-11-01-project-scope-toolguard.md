# 專案 scope 接入 toolguard 攔截層 — 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓 `projects.scope_json` 真正進入 toolguard 攔截層：`targets` 豁免內建 `government-domains` 規則、`exclude` 一律硬攔，且僅作用於綁定該專案的對話。

**Architecture:** 在 `internal/toolguard` 新增 per-call 的 `TargetScope`（編譯後的 Allow/Deny），以 `CheckScoped` 帶入；`internal/mcp` 以 `ScopeResolver` 回呼注入點取得「這次呼叫屬於哪個專案」的範圍（避免 mcp → database 的 import cycle）；`internal/app` 負責從 ctx 解析專案 ID、讀 `scope_json`、解析成範圍；`internal/config` 新增預設關閉的開關。

**Tech Stack:** Go 1.25+、標準庫 `regexp`/`net`/`encoding/json`、既有 `internal/toolguard` 規則引擎。

## Global Constraints

- 模組路徑 `jysecai`；`go.mod` 宣告 `go 1.25.0`，本機 go1.26.7。
- `internal/toolguard` 必須維持「零內部 import」（只用 stdlib），避免 import cycle。
- `internal/mcp` 不得 import `internal/database`（database 已 import mcp）→ 範圍取得必須走回呼注入。
- 既有 `Policy.Check(toolName, args)` / `Manager.Check(...)` 簽名不得變更（`internal/handler/tool_guard.go:120` 直接呼叫 `Policy.Check`）。
- `compileScope` 的既有錯誤字串（含前綴 `tool guard: `）不得改變 → 以 label 參數化，既有呼叫傳 `"tool guard"`。
- 錯誤回應格式 `{"error": "machine_readable_code", "message": "..."}`。
- 文件雙語：`docs/zh-CN/` 與 `docs/en-US/` 必須同步。
- 觸及安全敏感程式碼後需跑 CI `authorization-boundaries` job 對應測試（`go test -run '...'`）。
- 不啟動第二份服務；`jysec-core` 為線上實例。
- **不 commit**：使用者未要求提交，且工作樹極髒。所有變更留在工作樹，由使用者自行審閱。
- 程式碼註解用中文，風格比照周遭檔案。

---

### Task 1: toolguard — TargetScope / CheckScoped / 字串解析

**Files:**
- Create: `internal/toolguard/target_scope.go`
- Modify: `internal/toolguard/toolguard.go`（`compileScope` label 參數化、`Check` → `CheckScoped`）
- Test: `internal/toolguard/target_scope_test.go`

**Interfaces:**
- Produces:
  - `type TargetScope struct { allow, deny compiledScope; active bool }`
  - `func NewTargetScope(allow, deny *Scope) (*TargetScope, error)`
  - `func (p *Policy) CheckScoped(toolName string, args map[string]interface{}, scope *TargetScope) *Match`
  - `func (m *Manager) CheckScoped(toolName string, args map[string]interface{}, scope *TargetScope) *Match`
  - `func ParseScopeEntries(entries []string) (*Scope, error)`
  - `func candidateHosts(text string) []string`
  - `const ProjectScopeExcludeRuleID = "project-scope-exclude"`、`ProjectScopeExcludeRuleName = "專案排除目標"`

- [ ] **Step 1: 寫失敗的測試** `internal/toolguard/target_scope_test.go`

```go
func TestTargetScopeDenyBlocksEvenWhenAllowed(t *testing.T) {
	scope, err := NewTargetScope(
		&Scope{Domains: []string{"legacy.gov.tw"}},
		&Scope{Domains: []string{"legacy.gov.tw"}},
	)
	if err != nil { t.Fatal(err) }
	policy, err := Compile(Config{Enabled: true, Rules: []Rule{{ID: "government-domains", Name: "gov", Enabled: true, Pattern: governmentDomainPattern}}})
	if err != nil { t.Fatal(err) }
	match := policy.CheckScoped("curl", map[string]interface{}{"url": "https://legacy.gov.tw/x"}, scope)
	if match == nil || match.RuleID != ProjectScopeExcludeRuleID {
		t.Fatalf("expected project-scope-exclude, got %#v", match)
	}
}

func TestTargetScopeAllowExemptsGovernmentRuleOnly(t *testing.T) { /* 自訂規則不豁免 */ }
func TestTargetScopeDenyBlocksWhenGlobalGuardDisabled(t *testing.T) { /* tool_guard.enabled=false 仍擋 */ }
func TestCheckScopedWithoutScopeMatchesCheck(t *testing.T) { /* nil scope 行為與 Check 完全相同 */ }
func TestParseScopeEntriesClassifiesEntries(t *testing.T) { /* URL/wildcard/suffix/CIDR/IP */ }
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/toolguard/ -run 'TargetScope|ParseScopeEntries' -v`
Expected: FAIL — `undefined: NewTargetScope` 等編譯錯誤。

- [ ] **Step 3: 實作 `internal/toolguard/target_scope.go`**

核心內容：

```go
// TargetScope 是編譯後的專案授權範圍，可安全並行使用。
type TargetScope struct {
	allow  compiledScope
	deny   compiledScope
	active bool
}

// NewTargetScope 編譯專案授權範圍。allow/deny 皆 nil 或空時回傳 nil（表示不套用）。
func NewTargetScope(allow, deny *Scope) (*TargetScope, error) {
	if allow == nil && deny == nil {
		return nil, nil
	}
	compiledAllow, err := compileScopeWithLabel("project scope allow", allow)
	if err != nil { return nil, err }
	compiledDeny, err := compileScopeWithLabel("project scope deny", deny)
	if err != nil { return nil, err }
	scope := &TargetScope{allow: compiledAllow, deny: compiledDeny}
	scope.active = compiledAllow.active || compiledDeny.active
	if !scope.active { return nil, nil }
	return scope, nil
}
```

`candidateHosts` 以 regex 抽出 host token：

```go
var (
	ipv6BracketPattern = regexp.MustCompile(`\[[0-9A-Fa-f:.]+\]`)
	hostTokenPattern   = regexp.MustCompile(`[A-Za-z0-9_*][A-Za-z0-9_*.-]*`)
)

func candidateHosts(text string) []string {
	var out []string
	seen := map[string]struct{}{}
	add := func(value string) {
		host := normalizeHost(value)
		if host == "" { return }
		if _, ok := seen[host]; ok { return }
		seen[host] = struct{}{}
		out = append(out, host)
	}
	for _, m := range ipv6BracketPattern.FindAllString(text, -1) { add(m) }
	for _, token := range hostTokenPattern.FindAllString(text, -1) {
		if strings.Contains(token, ".") { add(token) }
	}
	return out
}
```

`ParseScopeEntries` 分類規則（順序固定）：合法 CIDR → `CIDRs`；含 `*`/`?` → `Wildcards`；開頭 `.` → `DomainSuffixes`；其餘且含 `.` 或為 IP → `Domains`；無法解讀者忽略。

- [ ] **Step 4: 改 `internal/toolguard/toolguard.go`**

1. `compileScope` 改為呼叫 `compileScopeWithLabel("tool guard", scope)`；既有錯誤字串不變。
2. `Policy.Check` 改為 `return p.CheckScoped(toolName, args, nil)`；`CheckScoped` 為真正實作：
   - 先掃 Deny（獨立於 `p.config.Enabled`），命中回傳 `Match{RuleID: ProjectScopeExcludeRuleID, ...}`。
   - 規則迴圈中，`government-domains` 改走 `allMatches` 路徑（原本僅在 `p.scope.active` 時才走；未啟用 scope 時 `allMatches` 與 `FindStringSubmatchIndex` 結果相同，故行為等價）。
   - 豁免條件：全域 scope 命中 **或** 專案 Allow 命中。
3. `Manager.CheckScoped` 轉呼叫 `m.policy.Load().CheckScoped(...)`。

- [ ] **Step 5: 跑測試確認通過**

Run: `go test ./internal/toolguard/... -v -run 'TargetScope|ParseScopeEntries|Scope|Check'`
Expected: PASS（含既有 toolguard 測試全部維持綠燈）

---

### Task 2: project — scope_json 解析

**Files:**
- Create: `internal/project/scope_guard.go`
- Modify: `internal/project/scope_block.go`（移除重複的 `projectScopePayload` 定義，改用共用版本；`BuildScopeBlock` 增加結構化欄位分支）
- Test: `internal/project/scope_guard_test.go`

**Interfaces:**
- Consumes: `toolguard.NewTargetScope`、`toolguard.ParseScopeEntries`、`toolguard.Scope`
- Produces: `func ParseScopeTargets(raw string) (*toolguard.TargetScope, error)`

- [ ] **Step 1: 寫失敗的測試**

```go
func TestParseScopeTargetsPrefersStructuredFields(t *testing.T)
func TestParseScopeTargetsFallsBackToFreeText(t *testing.T)
func TestParseScopeTargetsInvalidJSON(t *testing.T)
func TestBuildScopeBlockRendersStructuredScope(t *testing.T)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/project/ -run 'ScopeTargets|ScopeBlock' -v`
Expected: FAIL — `undefined: ParseScopeTargets`。

- [ ] **Step 3: 實作 `internal/project/scope_guard.go`**

```go
// projectScopePayload 解析 projects.scope_json（约定字段，可扩展）。
type projectScopePayload struct {
	Targets []string `json:"targets"`
	Exclude []string `json:"exclude"`
	Notes   string   `json:"notes"`
	// Scope 是結構化授權範圍；存在時優先於 Targets / Exclude 的自由字串解析。
	Scope *projectScopeStructured `json:"scope,omitempty"`
}

type projectScopeStructured struct {
	Allow *toolguard.Scope `json:"allow,omitempty"`
	Deny  *toolguard.Scope `json:"deny,omitempty"`
}

// ParseScopeTargets 解析 projects.scope_json 為攔截層用的專案授權範圍。
//
// 結構化欄位（scope.allow / scope.deny）優先；缺省時才自動解析 targets / exclude。
// 自由字串中無法解讀的項目會被忽略（不讓整份 scope 失效）。
func ParseScopeTargets(raw string) (*toolguard.TargetScope, error) { /* … */ }
```

`scope_block.go` 刪掉自己的 `projectScopePayload` 定義，改用同一套；`BuildScopeBlock` 在 `payload.Scope != nil` 時改以結構化欄位渲染允許/排除清單（避免提示層顯示「未識別欄位」而攔截層卻在生效的落差）。

- [ ] **Step 4: 跑測試確認通過**

Run: `go test ./internal/project/... -v`
Expected: PASS

---

### Task 3: mcp — ScopeResolver 注入與 ctx 傳遞

**Files:**
- Modify: `internal/mcp/tool_call_guard.go`（新增 `ScopeResolver`、`toolGuardBlockedResult` 改收 scope）
- Modify: `internal/mcp/server.go`（`Server.projectScopeResolver` 欄位、`SetProjectScopeResolver`、`checkToolGuard(ctx, …)`、兩處呼叫點）
- Modify: `internal/mcp/external_manager.go`（同上）
- Test: `internal/mcp/tool_call_guard_test.go`

**Interfaces:**
- Produces:
  - `type ScopeResolver func(ctx context.Context) *toolguard.TargetScope`
  - `func (s *Server) SetProjectScopeResolver(resolver ScopeResolver)`
  - `func (m *ExternalMCPManager) SetProjectScopeResolver(resolver ScopeResolver)`

- [ ] **Step 1: 寫失敗的測試**

```go
func TestToolGuardAppliesInjectedProjectScope(t *testing.T)      // resolver 回傳 deny scope → 被攔
func TestToolGuardWithoutResolverKeepsBehaviour(t *testing.T)     // 未注入 → 不被專案 scope 影響
func TestExternalToolGuardAppliesInjectedProjectScope(t *testing.T)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/mcp/ -run 'ProjectScope' -v`
Expected: FAIL — `undefined: SetProjectScopeResolver`。

- [ ] **Step 3: 實作**

```go
// ScopeResolver 回傳目前這次呼叫所屬對話的專案授權範圍。
// 回傳 nil 代表不套用專案範圍（預設行為）。
type ScopeResolver func(ctx context.Context) *toolguard.TargetScope
```

`Server` / `ExternalMCPManager` 各加一個欄位與 setter；`checkToolGuard` 改為吃 ctx：

```go
func (s *Server) checkToolGuard(ctx context.Context, toolName string, args map[string]interface{}) *ToolResult {
	s.mu.RLock()
	guard := s.toolGuard
	resolver := s.projectScopeResolver
	s.mu.RUnlock()
	if guard == nil { return nil }
	var scope *toolguard.TargetScope
	if resolver != nil { scope = resolver(ctx) }
	return toolGuardBlockedResult(guard, toolName, args, scope)
}
```

呼叫點更新：`server.go:629` 用 `execCtx`；`server.go:971` 用 `runCtx`；`external_manager.go:725` 用 `ctx`；`external_manager.go:769` 用 `runCtx`。

- [ ] **Step 4: 跑測試確認通過**

Run: `go test ./internal/mcp/...`
Expected: PASS

---

### Task 4: app + config — 開關與接線

**Files:**
- Modify: `internal/config/config.go`（`ProjectConfig.ScopeGuardEnabled`）
- Create: `internal/app/mcp_scope_guard.go`（resolver）
- Modify: `internal/app/app.go`（開關為 true 時注入 resolver）
- Test: `internal/app/mcp_scope_guard_test.go`

**Interfaces:**
- Consumes: `project.ParseScopeTargets`、`mcp.ScopeResolver`、`mcp.MCPProjectIDFromContext`、`db.GetProject`、`db.GetConversationProjectID`
- Produces: `func newProjectScopeResolver(db *database.DB) *projectScopeResolver` 與其 `Resolve(ctx) *toolguard.TargetScope`

- [ ] **Step 1: 寫失敗的測試**

```go
func TestProjectScopeResolverResolvesConversationProject(t *testing.T)  // ctx 帶 conversationID → scope
func TestProjectScopeResolverReturnsNilForUnboundConversation(t *testing.T)
func TestProjectScopeResolverCachesParsedScope(t *testing.T)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `go test ./internal/app/ -run 'ProjectScopeResolver' -v`
Expected: FAIL — `undefined: newProjectScopeResolver`。

- [ ] **Step 3: 實作**

`internal/config/config.go`：

```go
	// ScopeGuardEnabled 開啟後，專案 scope_json 的 targets/exclude 會進入 toolguard 攔截層：
	// targets 豁免內建政府規則，exclude 一律攔截。預設關閉；此欄位位於 project: 區段，
	// 只能經 config.yaml 修改（config handler 不改寫該區段）。
	ScopeGuardEnabled bool `yaml:"scope_guard_enabled,omitempty" json:"scope_guard_enabled,omitempty"`
```

`internal/app/mcp_scope_guard.go`：resolver（ctx → projectID → `db.GetProject` → `project.ParseScopeTargets`），以 projectID 為 key 快取 `(原始 scope_json, 解析結果)`；原始字串相同則重用解析結果，變更立即生效。

`internal/app/app.go`：在 `mcpServer` / `externalMCPMgr` 建立後，

```go
	if cfg.Project.ScopeGuardEnabled {
		resolver := newProjectScopeResolver(db)
		mcpServer.SetProjectScopeResolver(resolver.Resolve)
		externalMCPMgr.SetProjectScopeResolver(resolver.Resolve)
	}
```

- [ ] **Step 4: 跑測試確認通過**

Run: `go test ./internal/app/... ./internal/config/...`
Expected: PASS

---

### Task 5: 雙語文件

**Files:**
- Modify: `docs/zh-CN/tool-call-guard.md`
- Modify: `docs/en-US/tool-call-guard.md`

- [ ] **Step 1: 新增章節**（兩份同步）

說明：`project.scope_guard_enabled` 開關（預設關、僅 config.yaml）、`scope_json` 的
`scope.allow` / `scope.deny` 結構化欄位與 `targets` / `exclude` 自由字串 fallback、
語意（targets 僅豁免內建政府規則；exclude 一律攔截且優先）、作用範圍（僅綁定該專案的對話）、
以及邊界（僅主服務生效，`cmd/mcp-stdio` 無 DB 故不套用；文字比對非網路層授權檢查）。

- [ ] **Step 2: 檢查雙語一致性**

Run: `diff <(grep -c '' docs/zh-CN/tool-call-guard.md) <(grep -c '' docs/en-US/tool-call-guard.md)`
（僅檢查篇幅相近；內容以人工比對為準）

---

### Task 6: 完整驗證

- [ ] **Step 1: 建置**

```bash
go build ./internal/toolguard/... ./internal/project/... ./internal/mcp/... ./internal/app/... ./internal/config/...
```
Expected: exit 0

- [ ] **Step 2: 相關套件測試**

```bash
go test ./internal/toolguard/... ./internal/project/... ./internal/mcp/... ./internal/app/... ./internal/config/... ./internal/database/... ./internal/handler/...
```

- [ ] **Step 3: authorization-boundaries 對應測試**

從 `.github/workflows/linux-build.yml` 取出該 job 的 `go test -run` 表達式並原樣執行。

- [ ] **Step 4: 全樹**

```bash
go vet ./... && go test ./...
```
（`/mnt/c` I/O 慢，放背景任務跑）
