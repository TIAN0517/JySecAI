# 設計：projects.scope_json 接入 toolguard 攔截層

- 日期：2026-11-01
- 狀態：已核准（使用者確認「照此設計實作」）
- 相關既有文件：`docs/zh-CN/tool-call-guard.md`、`docs/en-US/tool-call-guard.md`

## 問題

`projects.scope_json` 目前只進提示層（`internal/project/scope_block.go` → Agent system prompt），
完全不進攔截層。`internal/toolguard` 的攔截只認 `config.yaml` 的全域 `tool_guard.scope`。

後果：

1. 專案已授權的目標（例如 `portal.agency.gov.tw`）仍會被內建 `government-domains` 規則攔下，
   因為全域 scope 沒有它。提示層寫了「這是授權範圍」沒有用，攔截層不看專案。
2. 專案的 `exclude`（明確排除的目標）同樣只靠提示層自律，沒有任何強制力。

## 已確認的決策（使用者）

| 決策 | 結論 |
| --- | --- |
| 開關 | 新增設定，**預設關閉**，僅 admin 經 `config.yaml` 可開啟；開啟後專案 scope 才影響攔截 |
| 攔截語意 | **豁免 + 排除**：`targets` 讓主機豁免內建 `government-domains` 規則；`exclude` 一律硬攔；`targets` 之外的主機不因 scope 被攔 |
| 優先序 | `exclude` 優先否決（即使同時列在 `targets`） |
| 作用範圍 | 僅作用於綁定該專案的對話，不影響其他對話 |
| 字串對應 | **兩者並存**：`scope_json` 新增結構化欄位優先，缺省才自動解析既有 `targets`/`exclude` 自由字串 |
| 失效模式 | **獨立於 `tool_guard.enabled`**：專案 exclude 仍會攔截（fail-closed），只有 `targets` 的規則豁免失效 |

## 設計

### 1. `internal/toolguard` — per-call 專案範圍

維持「零內部 import」的性質（只用 stdlib），避免 import cycle。

```go
// TargetScope 描述一次呼叫所屬對話的專案授權範圍。
type TargetScope struct {
    Allow *Scope // 已授權目標：命中者豁免內建的 government-domains 規則
    Deny  *Scope // 明確排除目標：命中者一律攔截，優先於 Allow
}
```

新增 API（既有 `Check` 簽名不變）：

```go
func (p *Policy) CheckScoped(toolName string, args map[string]interface{}, scope *TargetScope) *Match
func (m *Manager) CheckScoped(toolName string, args map[string]interface{}, scope *TargetScope) *Match
```

`Check(toolName, args)` 等同 `CheckScoped(toolName, args, nil)`。

`CheckScoped` 流程：

1. `scope` 非 nil 且有效 → 先掃 **Deny**：任一候選文字展開出的主機命中 Deny → 回傳
   `Match{RuleID: "project-scope-exclude", RuleName: "專案排除目標", ...}`。
   這一步**獨立於 `p.config.Enabled`**（fail-closed），且先於規則檢查。
2. 走既有規則迴圈。`government-domains` 規則的豁免條件由「只在全域 scope」擴為
   「全域 scope **或** 專案 Allow」。自訂規則不受 Allow 豁免（與全域 scope 語意一致）。
3. 其餘行為與現況完全相同。

### 2. 主機比對的兩條路徑

- **Allow**：不掃全文。只在規則實際命中的那個主機上比對，沿用既有 `hostAroundMatch` 展開。
  避免把參數裡的無關主機誤判成「已授權」而豁免規則。
- **Deny**：需獨立於規則生效，故新增候選主機掃描器 `candidateHosts()`，從候選文字
  （工具名稱、參數 JSON、鍵名、百分號解碼後文字）抽出所有 host token（網域 / IPv4 / IPv6）逐一比對。

### 3. `internal/mcp` — 帶入 ctx 與注入點

比照既有 `SetToolAuthorizer` 的 injection 模式（`internal/mcp` 不得 import `internal/database`，
否則 cycle）：

```go
type ScopeResolver func(ctx context.Context) *toolguard.TargetScope

func (s *Server) SetProjectScopeResolver(resolver ScopeResolver)
func (m *ExternalMCPManager) SetProjectScopeResolver(resolver ScopeResolver)
```

- `checkToolGuard` 增加 `ctx` 參數，涵蓋內部 MCP（`server.go` 的 HTTP 入口與 Agent 入口）
  與外部 MCP（`external_manager.go` 的兩處檢查）。
- 未注入 resolver → 行為與現況完全相同（零開銷、零風險）。

### 4. `internal/app` — 解析與接線

`internal/app/mcp_project_scope.go` 新增 resolver：

1. 開關關閉 → 不注入 resolver（零開銷）。
2. 由 ctx 取 projectID：`mcp.MCPProjectIDFromContext(ctx)`；若空 → 以
   `mcpAuthorizationConversationID(ctx)` 查 `db.GetConversationProjectID`。
3. 對話未綁專案、查不到專案、scope_json 為空 → 回傳 nil（不放寬、不攔截）。
4. `db.GetProject(projectID)` → `project.ParseScopeTargets(proj.ScopeJSON)`。

快取：以 projectID 為 key 記住 `(原始 scope_json 字串, 解析結果)`；原始字串相同則重用解析結果。
每次呼叫仍查一次 DB，因此 scope 變更立即生效，只省掉重複解析。

### 5. 設定開關

`internal/config/config.go` `ProjectConfig` 新增：

```go
// ScopeGuardEnabled 開啟後，專案 scope_json 會進入 toolguard 攔截層。
ScopeGuardEnabled bool `yaml:"scope_guard_enabled,omitempty" json:"scope_guard_enabled,omitempty"`
```

零值即 false（預設關閉）。位於 `project:` 區段，而 config handler 沒有
`updateProjectConfig`、只以 yaml.Node 局部改寫特定區段，因此此欄位**無法經 API 改寫**，
僅能改 `config.yaml`（admin 決策途徑）—— 符合「擴大豁免＝admin 決定」的既有控制。

### 6. `scope_json` schema

```json
{
  "targets": ["https://app.example.com", "*.cdn.example.com"],
  "exclude": ["legacy.gov.tw"],
  "notes": "…",
  "scope": {
    "allow": { "domains": [], "domain_suffixes": [], "wildcards": [], "cidrs": [] },
    "deny":  { "domains": [], "domain_suffixes": [], "wildcards": [], "cidrs": [] }
  }
}
```

- `scope.allow` / `scope.deny` 存在 → **結構化優先**，直接使用。
- 否則自動解析 `targets` → allow、`exclude` → deny：
  - 含 `/` 且 `net.ParseCIDR` 合法 → `cidrs`
  - 含 `*` 或 `?` → `wildcards`
  - 開頭為 `.` → `domain_suffixes`
  - 其餘剝掉 scheme / userinfo / path / port 後 → `domains`（含 IP）

### 7. 攔截回執

沿用 `internal/toolguard/refusal.go` 的單一來源。新增規則常數
`ProjectScopeExcludeRuleID = "project-scope-exclude"`、`ProjectScopeExcludeRuleName = "專案排除目標"`，
回執仍由 `toolguard.RefusalMessage` 組裝，既有 `toolguard.ParseRefusal` 可直接辨識 →
blocked 狀態、監控統計、舊紀錄升級全部不受影響。

## 測試計畫

| 套件 | 測試重點 |
| --- | --- |
| `internal/toolguard` | Deny 硬攔（含 Allow 同時命中、`tool_guard.enabled=false` 仍攔）；Allow 僅豁免內建政府規則；自訂規則不豁免；無 scope 行為不變；`ParseScopeEntries` 分類正確 |
| `internal/project` | 結構化欄位優先；自動解析 fallback；exclude 優先於 targets；非法 JSON 不 panic |
| `internal/mcp` | resolver 注入後 per-call scope 生效；未注入時行為不變；外部 MCP 路徑同樣生效 |
| `internal/app` | ctx → projectID → scope 解析；未綁專案回傳 nil |

## 文件

`docs/zh-CN/tool-call-guard.md` 與 `docs/en-US/tool-call-guard.md` 同步新增：
開關 `project.scope_guard_enabled`、`scope_json` schema、語意與邊界說明。
