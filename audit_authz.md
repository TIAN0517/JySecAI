# Authentication & Authorization Audit — JySecAI

**Scope:** every HTTP route registered in `internal/app/app.go`, the RBAC permission map
(`internal/security/rbac_middleware.go`), the ownership/ACL layer (`internal/database/rbac.go`),
and the session lifecycle (`internal/security/auth_manager.go`, `internal/handler/auth.go`,
`internal/handler/rbac.go`).

**Totals:** 286 routes registered. 275 are behind `AuthMiddleware` + `RBACMiddleware`
(`protected` 221, `c2Routes` 34, `xssRoutes` 6, `knowledgeRoutes` 13, plus `/api/conversations/:id/results`
and `/api/openapi/spec`). 7 are on `authRoutes` (session self-service, `RequirePermission`-gated inline).
4 are unauthenticated robot webhooks. 1 is the public API-docs page.

**Headline result:** the permission *mapping* layer is sound — every protected route maps to a
permission that exists in `PermissionCatalog`, and there are no unmapped routes. The gap is in the
*resource* layer: `resourceAllowed()` inspects only path prefixes, so any module whose resource
selector is a query parameter or a body field is invisible to it, and the handler is the only
remaining line of defense. Three such endpoints have no handler-level check.

Ownership column — what the **middleware** enforces. This is not the same as "is this route
authorized", because `resourceAllowed()` is only the first of two lines of defence:

- `Y` — the path matches a case in `resourceAllowed()` (`internal/security/rbac_middleware.go:216-264`),
  so `db.UserCanAccessResource` runs before the handler.
- `-` — the path does **not** match any case, so the request reaches `default: return true`
  (`:262`). The handler is then the *only* line of defence, and must do its own ownership check.

For `-` rows, §5 lists which ones actually do. The three that do not are the S0 findings in §2:
`GET /api/vulnerabilities/triage/runs`, `GET /api/vulnerabilities/triage/runs/:id` and
`GET /api/knowledge/retrieval-logs`.

---

## 1. Full route inventory

| METHOD | PATH | Permission | Ownership | Group |
|---|---|---|---|---|
| GET | /api/agent-loop/tasks | tasks:read | - | protected |
| GET | /api/agent-loop/task-events | tasks:read | - | protected |
| GET | /api/agent-loop/tasks/completed | tasks:read | - | protected |
| POST | /api/agent-loop/cancel | tasks:write | - | protected |
| GET | /api/api-docs | (none - public/n-a) | - | router |
| DELETE | /api/assets/:id | asset:delete | - | protected |
| GET | /api/assets | asset:read | - | protected |
| GET | /api/assets/selection | asset:read | - | protected |
| GET | /api/assets/stats | asset:read | - | protected |
| POST | /api/assets/import | asset:write | - | protected |
| POST | /api/assets/scan-links | asset:write | - | protected |
| POST | /api/assets/batch-delete | asset:delete | - | protected |
| POST | /api/assets/merge | asset:delete | - | protected |
| PUT | /api/assets/bulk | asset:write | - | protected |
| PUT | /api/assets/project-binding | asset:write | - | protected |
| PUT | /api/assets/:id | asset:write | - | protected |
| GET | /api/attack-chain/:conversationId | attackchain:read | - | protected |
| POST | /api/attack-chain/:conversationId/regenerate | attackchain:write | - | protected |
| GET | /api/audit/meta | audit:read | - | protected |
| GET | /api/audit/summary | audit:read | - | protected |
| GET | /api/audit/logs | audit:read | - | protected |
| GET | /api/audit/logs/export | audit:read | - | protected |
| GET | /api/audit/logs/:id | audit:read | - | protected |
| DELETE | /api/auth/robot-bindings/:id | (none - public/n-a) | - | authRoutes |
| GET | /api/auth/validate | (none - public/n-a) | - | authRoutes |
| GET | /api/auth/robot-bindings | (none - public/n-a) | - | authRoutes |
| POST | /api/auth/login | (none - public/n-a) | - | authRoutes |
| POST | /api/auth/logout | (none - public/n-a) | - | authRoutes |
| POST | /api/auth/change-password | (none - public/n-a) | - | authRoutes |
| POST | /api/auth/robot-binding-code | (none - public/n-a) | - | authRoutes |
| DELETE | /api/batch-tasks/:queueId | tasks:delete | - | protected |
| DELETE | /api/batch-tasks/:queueId/tasks/:taskId | tasks:delete | - | protected |
| GET | /api/batch-tasks | tasks:read | - | protected |
| GET | /api/batch-tasks/:queueId | tasks:read | - | protected |
| POST | /api/batch-tasks | tasks:write | - | protected |
| POST | /api/batch-tasks/:queueId/start | tasks:write | - | protected |
| POST | /api/batch-tasks/:queueId/rerun | tasks:write | - | protected |
| POST | /api/batch-tasks/:queueId/pause | tasks:write | - | protected |
| POST | /api/batch-tasks/:queueId/tasks/:taskId/run | tasks:write | - | protected |
| POST | /api/batch-tasks/:queueId/tasks | tasks:write | - | protected |
| PUT | /api/batch-tasks/:queueId/metadata | tasks:write | - | protected |
| PUT | /api/batch-tasks/:queueId/schedule | tasks:write | - | protected |
| PUT | /api/batch-tasks/:queueId/schedule-enabled | tasks:write | - | protected |
| PUT | /api/batch-tasks/:queueId/tasks/:taskId | tasks:write | - | protected |
| DELETE | /api/c2/listeners/:id | c2:delete | - | c2Routes |
| DELETE | /api/c2/sessions | c2:delete | - | c2Routes |
| DELETE | /api/c2/sessions/:id | c2:delete | - | c2Routes |
| DELETE | /api/c2/tasks | c2:delete | - | c2Routes |
| DELETE | /api/c2/events | c2:delete | - | c2Routes |
| DELETE | /api/c2/profiles/:id | c2:delete | - | c2Routes |
| GET | /api/c2/listeners | c2:read | - | c2Routes |
| GET | /api/c2/listeners/:id | c2:read | - | c2Routes |
| GET | /api/c2/sessions | c2:read | - | c2Routes |
| GET | /api/c2/sessions/:id | c2:read | - | c2Routes |
| GET | /api/c2/tasks | c2:read | - | c2Routes |
| GET | /api/c2/tasks/:id | c2:read | - | c2Routes |
| GET | /api/c2/tasks/:id/wait | c2:read | - | c2Routes |
| GET | /api/c2/payloads/:id/download | c2:read | - | c2Routes |
| GET | /api/c2/events | c2:read | - | c2Routes |
| GET | /api/c2/events/stream | c2:read | - | c2Routes |
| GET | /api/c2/files | c2:read | - | c2Routes |
| GET | /api/c2/tasks/:id/result-file | c2:read | - | c2Routes |
| GET | /api/c2/profiles | c2:read | - | c2Routes |
| GET | /api/c2/profiles/:id | c2:read | - | c2Routes |
| POST | /api/c2/listeners | c2:write | - | c2Routes |
| POST | /api/c2/listeners/:id/start | c2:write | - | c2Routes |
| POST | /api/c2/listeners/:id/stop | c2:write | - | c2Routes |
| POST | /api/c2/tasks | c2:write | - | c2Routes |
| POST | /api/c2/tasks/:id/cancel | c2:write | - | c2Routes |
| POST | /api/c2/sessions/:id/tasks | c2:write | - | c2Routes |
| POST | /api/c2/payloads/oneliner | c2:write | - | c2Routes |
| POST | /api/c2/payloads/build | c2:write | - | c2Routes |
| POST | /api/c2/files/upload | c2:write | - | c2Routes |
| POST | /api/c2/profiles | c2:write | - | c2Routes |
| PUT | /api/c2/listeners/:id | c2:write | - | c2Routes |
| PUT | /api/c2/sessions/:id/sleep | c2:write | - | c2Routes |
| PUT | /api/c2/sessions/:id/note | c2:write | - | c2Routes |
| PUT | /api/c2/profiles/:id | c2:write | - | c2Routes |
| DELETE | /api/chat-uploads | files:delete | - | protected |
| GET | /api/chat-uploads | files:read | - | protected |
| GET | /api/chat-uploads/export | files:read | - | protected |
| GET | /api/chat-uploads/download | files:read | - | protected |
| GET | /api/chat-uploads/path | files:read | - | protected |
| GET | /api/chat-uploads/content | files:read | - | protected |
| POST | /api/chat-uploads | files:write | - | protected |
| POST | /api/chat-uploads/mkdir | files:write | - | protected |
| PUT | /api/chat-uploads/rename | files:write | - | protected |
| PUT | /api/chat-uploads/content | files:write | - | protected |
| GET | /api/config | config:read | - | protected |
| GET | /api/config/tools | config:read | - | protected |
| GET | /api/config/tools/:name/schema | config:read | - | protected |
| POST | /api/config/apply | config:write | - | protected |
| POST | /api/config/test-openai | config:write | - | protected |
| POST | /api/config/test-vision | config:write | - | protected |
| POST | /api/config/list-models | config:write | - | protected |
| PUT | /api/config | config:write | - | protected |
| DELETE | /api/conversations/:id | chat:delete | - | protected |
| GET | /api/conversations | chat:read | - | protected |
| GET | /api/conversations/:id | chat:read | - | protected |
| GET | /api/conversations/:id/token-usage | chat:read | - | protected |
| GET | /api/conversations/:id/plan-tasks | chat:read | - | protected |
| GET | /api/conversations/:id/results | chat:read | - | protected |
| POST | /api/conversations | chat:write | - | protected |
| POST | /api/conversations/:id/delete-turn | chat:write | - | protected |
| PUT | /api/conversations/:id | chat:write | - | protected |
| PUT | /api/conversations/:id/project | chat:write | - | protected |
| PUT | /api/conversations/:id/pinned | chat:write | - | protected |
| POST | /api/eino-agent | agent:execute | - | protected |
| POST | /api/eino-agent/stream | agent:execute | - | protected |
| DELETE | /api/external-mcp/:name | mcp:write | - | protected |
| GET | /api/external-mcp | mcp:read | - | protected |
| GET | /api/external-mcp/stats | mcp:read | - | protected |
| GET | /api/external-mcp/:name | mcp:read | - | protected |
| POST | /api/external-mcp/:name/start | mcp:write | - | protected |
| POST | /api/external-mcp/:name/stop | mcp:write | - | protected |
| PUT | /api/external-mcp/:name | mcp:write | - | protected |
| POST | /api/fofa/search | fofa:execute | - | protected |
| POST | /api/fofa/parse | fofa:execute | - | protected |
| DELETE | /api/hitl/logs | hitl:write | - | protected |
| GET | /api/hitl/pending | hitl:read | - | protected |
| GET | /api/hitl/logs | hitl:read | - | protected |
| GET | /api/hitl/logs/:id | hitl:read | - | protected |
| GET | /api/hitl/config/:conversationId | hitl:read | - | protected |
| GET | /api/hitl/tool-whitelist | hitl:read | - | protected |
| GET | /api/hitl/default-config | hitl:read | - | protected |
| GET | /api/hitl/default-reviewer | hitl:read | - | protected |
| GET | /api/hitl/audit-strategy | hitl:read | - | protected |
| POST | /api/hitl/decision | hitl:write | - | protected |
| POST | /api/hitl/dismiss | hitl:write | - | protected |
| POST | /api/hitl/tool-whitelist | hitl:write | - | protected |
| PUT | /api/hitl/config | hitl:write | - | protected |
| PUT | /api/hitl/tool-whitelist | hitl:write | - | protected |
| PUT | /api/hitl/default-config | hitl:write | - | protected |
| PUT | /api/hitl/default-reviewer | hitl:write | - | protected |
| PUT | /api/hitl/audit-strategy | hitl:write | - | protected |
| DELETE | /api/knowledge/items/:id | knowledge:delete | - | knowledgeRoutes |
| DELETE | /api/knowledge/retrieval-logs/:id | knowledge:delete | - | knowledgeRoutes |
| GET | /api/knowledge/categories | knowledge:read | - | knowledgeRoutes |
| GET | /api/knowledge/items | knowledge:read | - | knowledgeRoutes |
| GET | /api/knowledge/items/:id | knowledge:read | - | knowledgeRoutes |
| GET | /api/knowledge/index-status | knowledge:read | - | knowledgeRoutes |
| GET | /api/knowledge/retrieval-logs | knowledge:read | - | knowledgeRoutes |
| GET | /api/knowledge/stats | knowledge:read | - | knowledgeRoutes |
| POST | /api/knowledge/items | knowledge:write | - | knowledgeRoutes |
| POST | /api/knowledge/index | knowledge:write | - | knowledgeRoutes |
| POST | /api/knowledge/scan | knowledge:write | - | knowledgeRoutes |
| POST | /api/knowledge/search | knowledge:read | - | knowledgeRoutes |
| PUT | /api/knowledge/items/:id | knowledge:write | - | knowledgeRoutes |
| POST | /api/mcp | mcp:execute | - | protected |
| GET | /api/messages/:id/process-details | chat:read | - | protected |
| DELETE | /api/monitor/execution/:id | monitor:delete | - | protected |
| DELETE | /api/monitor/executions | monitor:delete | - | protected |
| GET | /api/monitor | monitor:read | - | protected |
| GET | /api/monitor/execution/:id | monitor:read | - | protected |
| GET | /api/monitor/stats | monitor:read | - | protected |
| GET | /api/monitor/calls-timeline | monitor:read | - | protected |
| POST | /api/monitor/execution/:id/cancel | monitor:write | - | protected |
| POST | /api/monitor/executions/names | monitor:write | - | protected |
| DELETE | /api/multi-agent/markdown-agents/:filename | agents:delete | - | protected |
| GET | /api/multi-agent/markdown-agents | agents:read | - | protected |
| GET | /api/multi-agent/markdown-agents/:filename | agents:read | - | protected |
| POST | /api/multi-agent | agent:execute | - | protected |
| POST | /api/multi-agent/stream | agent:execute | - | protected |
| POST | /api/multi-agent/markdown-agents | agents:write | - | protected |
| PUT | /api/multi-agent/markdown-agents/:filename | agents:write | - | protected |
| GET | /api/notifications/summary | notification:read | - | protected |
| POST | /api/notifications/read | notification:write | - | protected |
| GET | /api/openapi/spec | openapi:read | - | protected |
| GET | /api/process-details/:id | chat:read | - | protected |
| DELETE | /api/projects/:id | project:delete | - | protected |
| DELETE | /api/projects/:id/fact-edges/:edgeId | project:delete | - | protected |
| DELETE | /api/projects/:id/facts/:factId | project:delete | - | protected |
| GET | /api/projects/dashboard-summary | project:read | - | protected |
| GET | /api/projects | project:read | - | protected |
| GET | /api/projects/:id/stats | project:read | - | protected |
| GET | /api/projects/:id/conversations | project:read | - | protected |
| GET | /api/projects/:id | project:read | - | protected |
| GET | /api/projects/:id/fact-graph | project:read | - | protected |
| GET | /api/projects/:id/fact-edges | project:read | - | protected |
| GET | /api/projects/:id/facts | project:read | - | protected |
| POST | /api/projects | project:write | - | protected |
| POST | /api/projects/:id/fact-edges | project:write | - | protected |
| POST | /api/projects/:id/promote-attack-chain/:conversationId | project:write | - | protected |
| POST | /api/projects/:id/facts | project:write | - | protected |
| POST | /api/projects/:id/facts/deprecate | project:write | - | protected |
| POST | /api/projects/:id/facts/restore | project:write | - | protected |
| PUT | /api/projects/:id | project:write | - | protected |
| PUT | /api/projects/:id/facts/:factId | project:write | - | protected |
| DELETE | /api/rbac/users/:id | rbac:write | - | protected |
| DELETE | /api/rbac/roles/:id | rbac:write | - | protected |
| DELETE | /api/rbac/resource-assignments/:id | rbac:write | - | protected |
| GET | /api/rbac/me | auth:self | - | protected |
| GET | /api/rbac/metadata | rbac:read | - | protected |
| GET | /api/rbac/users | rbac:read | - | protected |
| GET | /api/rbac/roles | rbac:read | - | protected |
| GET | /api/rbac/resource-assignments | rbac:read | - | protected |
| GET | /api/rbac/resources | rbac:write | - | protected |
| POST | /api/rbac/users | rbac:write | - | protected |
| POST | /api/rbac/roles | rbac:write | - | protected |
| POST | /api/rbac/resource-assignments | rbac:write | - | protected |
| PUT | /api/rbac/users/:id | rbac:write | - | protected |
| PUT | /api/rbac/roles/:id | rbac:write | - | protected |
| GET | /api/robot/wecom | robot:write | - | robotGroup |
| GET | /api/robot/wechat/qrcode/status | robot:write | - | protected |
| GET | /api/robot/wechat/status | robot:read | - | protected |
| POST | /api/robot/wecom | robot:write | - | robotGroup |
| POST | /api/robot/dingtalk | robot:write | - | robotGroup |
| POST | /api/robot/lark | robot:write | - | robotGroup |
| POST | /api/robot/test | robot:write | - | protected |
| POST | /api/robot/wechat/qrcode | robot:write | - | protected |
| POST | /api/robot/wechat/qrcode/verify | robot:write | - | protected |
| DELETE | /api/roles/:name | roles:delete | - | protected |
| GET | /api/roles | roles:read | - | protected |
| GET | /api/roles/:name | roles:read | - | protected |
| POST | /api/roles | roles:write | - | protected |
| PUT | /api/roles/:name | roles:write | - | protected |
| DELETE | /api/skills/stats | skills:delete | - | protected |
| DELETE | /api/skills/:name | skills:delete | - | protected |
| DELETE | /api/skills/:name/stats | skills:delete | - | protected |
| GET | /api/skills | skills:read | - | protected |
| GET | /api/skills/stats | skills:read | - | protected |
| GET | /api/skills/:name/files | skills:read | - | protected |
| GET | /api/skills/:name/file | skills:read | - | protected |
| GET | /api/skills/:name/bound-roles | skills:read | - | protected |
| GET | /api/skills/:name | skills:read | - | protected |
| POST | /api/skills | skills:write | - | protected |
| PUT | /api/skills/:name/file | skills:write | - | protected |
| PUT | /api/skills/:name | skills:write | - | protected |
| GET | /api/terminal/ws | terminal:execute | - | protected |
| POST | /api/terminal/run | terminal:execute | - | protected |
| POST | /api/terminal/run/stream | terminal:execute | - | protected |
| GET | /api/tool-guard | config:read | - | protected |
| POST | /api/tool-guard/test | config:read | - | protected |
| PUT | /api/tool-guard | config:write | - | protected |
| GET | /api/usage/tokens | dashboard:read | - | protected |
| DELETE | /api/vulnerabilities/batch | vulnerability:delete | - | protected |
| DELETE | /api/vulnerabilities/:id | vulnerability:delete | - | protected |
| GET | /api/vulnerabilities | vulnerability:read | - | protected |
| GET | /api/vulnerabilities/export | vulnerability:export | - | protected |
| GET | /api/vulnerabilities/export-records | vulnerability:export | - | protected |
| GET | /api/vulnerabilities/export-urls | vulnerability:export | - | protected |
| GET | /api/vulnerabilities/filter-options | vulnerability:read | - | protected |
| GET | /api/vulnerabilities/stats | vulnerability:read | - | protected |
| GET | /api/vulnerabilities/triage/runs | vulnerability:read | - | protected |
| GET | /api/vulnerabilities/triage/runs/:id | vulnerability:read | - | protected |
| GET | /api/vulnerabilities/:id | vulnerability:read | - | protected |
| POST | /api/vulnerabilities/batch-generate-poc | vulnerability:write | - | protected |
| POST | /api/vulnerabilities/triage/run | vulnerability:write | - | protected |
| POST | /api/vulnerabilities/triage/runs/:id/apply | vulnerability:write | - | protected |
| POST | /api/vulnerabilities/:id/generate-poc | vulnerability:write | - | protected |
| POST | /api/vulnerabilities | vulnerability:write | - | protected |
| PUT | /api/vulnerabilities/:id | vulnerability:write | - | protected |
| GET | /api/vulnerability-alerts/subscription | vulnerability:read | - | protected |
| PUT | /api/vulnerability-alerts/subscription | vulnerability:read | - | protected |
| DELETE | /api/webshell/connections/:id | webshell:delete | - | protected |
| GET | /api/webshell/connections | webshell:read | - | protected |
| GET | /api/webshell/connections/:id/ai-history | webshell:read | - | protected |
| GET | /api/webshell/connections/:id/ai-conversations | webshell:read | - | protected |
| GET | /api/webshell/connections/:id/state | webshell:read | - | protected |
| POST | /api/webshell/connections | webshell:write | - | protected |
| POST | /api/webshell/exec | webshell:write | - | protected |
| POST | /api/webshell/file | webshell:write | - | protected |
| PUT | /api/webshell/connections/:id | webshell:write | - | protected |
| PUT | /api/webshell/connections/:id/state | webshell:write | - | protected |
| GET | /api/workflow-package-imports/:importId | workflow:write | - | protected |
| POST | /api/workflow-package-imports | workflow:write | - | protected |
| GET | /api/workflow-package-inspections/:inspectionId | workflow:write | - | protected |
| POST | /api/workflow-package-inspections | workflow:write | - | protected |
| DELETE | /api/workflows/:id | workflow:delete | - | protected |
| GET | /api/workflows/runs/pending | workflow:read | - | protected |
| GET | /api/workflows/runs/:runId/replay | workflow:read | - | protected |
| GET | /api/workflows/runs/:runId | workflow:read | - | protected |
| GET | /api/workflows/:id/package | workflow:read | - | protected |
| GET | /api/workflows | workflow:read | - | protected |
| GET | /api/workflows/:id | workflow:read | - | protected |
| POST | /api/workflows/runs/:runId/resume | workflow:execute | - | protected |
| POST | /api/workflows/validate | workflow:execute | - | protected |
| POST | /api/workflows/dry-run | workflow:execute | - | protected |
| POST | /api/workflows/generate-draft | workflow:write | - | protected |
| POST | /api/workflows | workflow:write | - | protected |
| PUT | /api/workflows/:id | workflow:write | - | protected |
| DELETE | /api/xss/payloads/:id | xss:delete | - | xssRoutes |
| GET | /api/xss/config | xss:read | - | xssRoutes |
| GET | /api/xss/payloads | xss:read | - | xssRoutes |
| GET | /api/xss/payloads/:id | xss:read | - | xssRoutes |
| GET | /api/xss/captures | xss:read | - | xssRoutes |
| POST | /api/xss/payloads | xss:write | - | xssRoutes |

---

## 2. Findings

### [S0] `GET /api/vulnerabilities/triage/runs` returns every tenant's triage history

- **File:** `internal/handler/vulnerability_triage.go:577` -> `internal/database/vulnerability_triage.go:207`
- **The defect**

  `ListTriageRuns` selects from `vulnerability_triage_runs` with **no `WHERE` clause at all**:

  ```go
  // internal/database/vulnerability_triage.go:211
  rows, err := db.Query(`SELECT `+triageRunColumns+` FROM vulnerability_triage_runs
      ORDER BY created_at DESC LIMIT ?`, limit)
  ```

  `internal/handler/vulnerability_triage.go:577-585` passes only a `limit` from the query string --
  the session is never consulted. The table carries a `created_by` column
  (`internal/database/database.go:454`) that is written on creation but never used as a predicate.

- **Concrete exploit**

  `GET /api/vulnerabilities/triage/runs?limit=100` as any user holding `vulnerability:read`.
  That permission is granted to **viewer, operator and auditor** by the
  `strings.HasSuffix(key, ":read")` branch of `grantSystemRolePermissions`
  (`internal/database/rbac.go:395-400`). A default read-only account with zero assignments
  receives every other user's triage runs, each carrying `proposal_json` (AI-generated grouping of
  vulnerability IDs and titles), `scope_json` (project id and filters), `headline`, `summary`, and
  `created_by` / `applied_by` usernames. No ID guessing required.

- **Suggested fix**

  Add `ListTriageRunsForAccess(limit, access)` filtering on `created_by = ?` for non-`all` scope,
  mirroring `notificationAccessFromContext` (`internal/handler/notification.go:135`) and the
  fail-closed `AND 1=0` convention already used at `internal/handler/notification.go:148-150`.

---

### [S0] `GET /api/vulnerabilities/triage/runs/:id` -- IDOR; the middleware prefix test misses this path

- **File:** `internal/handler/vulnerability_triage.go:588` -> `internal/database/vulnerability_triage.go:194`
- **The defect**

  ```go
  // internal/handler/vulnerability_triage.go:589
  run, err := h.db.GetTriageRun(c.Param("id"))
  ```
  ```go
  // internal/database/vulnerability_triage.go:199
  ... FROM vulnerability_triage_runs WHERE id = ? ...
  ```

  The middleware *looks* like it covers this. It does not. `resourceAllowed` gates the prefix
  `/vulnerabilities/:id` (`internal/security/rbac_middleware.go:247`) with `strings.HasPrefix`, but
  `c.FullPath()` for this route is the literal string `/api/vulnerabilities/triage/runs/:id`.
  Comparing character 16 gives `t` vs `:`, the prefix test fails, and control falls to
  `default: return true` at `internal/security/rbac_middleware.go:262-263`. The route is registered
  at `internal/app/app.go:1284`; the ordering comment at `internal/app/app.go:1280-1281` explains
  the registration order but not the ACL gap.

  **This is the same class of miss as the `/xss` gap that was already found and fixed** -- a
  longer, more specific path nested under an already-cased prefix.

- **Concrete exploit**

  Any `vulnerability:read` holder (viewer/operator/auditor) iterates run IDs from the unfiltered
  list in the previous finding, or reads them from an audit-log `ResourceID`, and calls
  `GET /api/vulnerabilities/triage/runs/<id>`. Returns the full triage proposal for another
  tenant's vulnerabilities, including raw vulnerability IDs and the usernames of the people who
  created and applied the run.

- **Suggested fix**

  Do not rely on raw string prefixes for nested siblings. Either add explicit cases --
  `strings.HasPrefix(path, "/vulnerabilities/triage/runs/:id")` and
  `strings.HasPrefix(path, "/vulnerabilities/triage/runs")` -- or, better, make the switch
  segment-aware (split on `/` and match path segments rather than substrings) so a new nested
  route can never silently inherit `default: true`. Fix ownership in the handler as well (previous
  finding), since the run's owner is a `created_by` string column, not a resource type resolvable
  by `UserCanAccessResource`.

---

### [S0] `GET /api/knowledge/retrieval-logs` leaks other users' prompt text, and is also a targeted IDOR

- **File:** `internal/handler/knowledge.go:446` -> `internal/knowledge/manager.go:797`
- **The defect**

  `GetRetrievalLogs` takes `conversationId` and `messageId` straight from the query string and hands
  them to the manager, which turns them into an unfiltered predicate:

  ```go
  // internal/knowledge/manager.go:797-812
  if messageID != "" {
      ... WHERE message_id = ? ...
  } else if conversationID != "" {
      ... WHERE conversation_id = ? ...
  } else {
      ... FROM knowledge_retrieval_logs ORDER BY created_at DESC LIMIT ?   // <-- every tenant
  }
  ```

  There is no ownership check in the handler and none in the SQL. The `else` branch is the default
  path: calling the endpoint with no query parameters returns every tenant's rows.

- **Concrete exploit**

  `GET /api/knowledge/retrieval-logs` as any user holding `knowledge:read`. Note `knowledge:read`
  is *not* in the operator/auditor/viewer exclusion list at `internal/database/rbac.go:389-393`
  (which excludes only `knowledge:write` and `knowledge:delete`), so it propagates to all three
  read-capable roles via the `:read` branch. The leaked columns are `query` -- the user's literal
  knowledge-retriever prompt text -- and `retrieved_items`, plus the `conversation_id` /
  `message_id` foreign keys that let the attacker pivot to other endpoints.

  Because the same parameters become a bare `WHERE`, this doubles as an IDOR:
  `GET /api/knowledge/retrieval-logs?conversationId=<victim-conversation-id>` returns that
  conversation's retrieval log directly, without needing the unfiltered listing.

- **Suggested fix**

  Filter through `db.UserCanAccessResource(access.UserID, access.Scope, "conversation", conversationID)`
  per row, or push the predicate into SQL using `appendConversationAccessSQL`
  (`internal/handler/notification.go:143`) joined on `knowledge_retrieval_logs.conversation_id`.
  Reject a caller-supplied `conversationId` the caller cannot access rather than trusting it.

---

### [S1] `POST /api/vulnerabilities/triage/runs/:id/apply` lets one tenant mark another tenant's run applied

- **File:** `internal/handler/vulnerability_triage.go:600`
- **The defect**

  The per-vulnerability writes are correctly authorized -- `internal/handler/vulnerability_triage.go:652`
  calls `UserCanAccessResource(access.UserID, access.Scope, "vulnerability", id)` for every ID, and
  the `covered` map at `:624-629` prevents the run from being used as an arbitrary write channel.
  That part is good.

  But the triage run record itself is read and then mutated with no ownership check:

  ```go
  // internal/handler/vulnerability_triage.go:602
  run, err := h.db.GetTriageRun(runID)     // no ownership check
  if run.AppliedAt != nil { ... }          // :607 -- gating only
  ```
  ```go
  // internal/database/vulnerability_triage.go:233
  func (db *DB) ApplyTriageStatuses(runID string, ...)  // writes applied_at / applied_by
  ```

  `applied_at` and `applied_by` are written onto a row the caller does not own.

- **Concrete exploit**

  A `vulnerability:write` holder (operator, scope `assigned`) who knows or guesses a run ID posts
  `{"updates": {...}}` to `/api/vulnerabilities/triage/runs/<victim-run-id>/apply`. If the run has
  not yet been applied, the update proceeds. Even with `updates` limited to IDs the caller does not
  own (which the per-ID check correctly rejects), the run is marked applied -- permanently blocking
  the victim from applying their own triage results, since `:607` rejects any subsequent apply with
  `run.AppliedAt != nil`. The attacker also reads the run's proposal en route.

- **Suggested fix**

  Gate on run ownership *before* the `AppliedAt` check, e.g. compare `run.CreatedBy` to
  `access.UserID` for non-`all` scope and return 403. Because `created_by` is a username column
  rather than a resource assignment, add a `created_by` index and a dedicated
  `UserCanOwnTriageRun(userID, runID)` helper rather than forcing it through `UserCanAccessResource`.

---

### [S3] List-scope filters fail *open* on an empty user ID

- **File:** `internal/database/vulnerability.go:110` and `internal/database/conversation.go:454`
- **The defect**

  ```go
  func appendVulnerabilityAccessFilter(query string, args []interface{}, access RBACListAccess) (string, []interface{}) {
      userID := strings.TrimSpace(access.UserID)
      if userID == "" || access.Scope == RBACScopeAll {
          return query, args        // <-- no predicate appended: caller sees EVERYTHING
      }
  ```

  The zero value of `RBACListAccess` therefore means "unrestricted", not "nothing". Contrast the
  correct in-codebase convention at `internal/handler/notification.go:148-150`, which returns
  `AND 1=0` when the user ID is empty.

  **Not currently reachable.** `AuthMiddleware` always sets a session
  (`internal/security/auth_middleware.go:39`), so `access.UserID` cannot be empty on a protected
  route. It is a latent fail-open, not a live hole -- but three call sites are one refactor away
  from reaching it: `internal/handler/agent.go:2032` `ListBatchQueues` discards the `ok` from
  `security.CurrentSession`, and `internal/handler/vulnerability.go:698` /
  `internal/handler/notification.go:136` return the zero `RBACListAccess{}` on the `!ok` branch.

- **Concrete exploit**

  None today. If any of those three call sites is ever reached without a session, the endpoint
  silently returns every tenant's rows instead of erroring.

- **Suggested fix**

  Flip the condition to match the notification convention:

  ```go
  if access.Scope == RBACScopeAll { return query, args }
  if userID == "" { return query + " AND 1=0", args }
  ```

  Apply the same change at `internal/database/conversation.go:454`.

---

### [S3] `ScopeFor` falls back to the *broadest* scope when a permission's scope is unknown

- **File:** `internal/security/auth_manager.go:146`
- **The defect**

  ```go
  func (s Session) ScopeFor(permission string) string {
      if scope := strings.TrimSpace(s.PermissionScopes[strings.TrimSpace(permission)]); scope != "" {
          return scope
      }
      return strings.TrimSpace(s.Scope)     // <-- broadest scope across ALL roles
  }
  ```

  `s.Scope` is `mergeRBACScope` over every role the user holds
  (`internal/database/rbac.go:464,477`), i.e. the widest. So "I do not know the scope for this
  permission" resolves to the most permissive answer rather than the least.

  **Currently safe, and the reason is subtle.** The middleware only calls `ScopeFor` *after*
  `sessionHasRoutePermission` has already confirmed the user holds the permission
  (`internal/security/rbac_middleware.go:32,47`), and `ResolveRBACAccess` populates
  `PermissionScopes` for every granted key (`internal/database/rbac.go:494-505`). So the fallback
  branch is unreachable on the RBAC-protected path. It is a trap for the next caller, not a bug in
  this one.

- **Concrete exploit**

  None on the current path.

- **Suggested fix**

  Make the fallback the narrowest scope and deny on genuine ambiguity:

  ```go
  scope := strings.TrimSpace(s.PermissionScopes[strings.TrimSpace(permission)])
  if scope != "" { return scope }
  return database.RBACScopeOwn    // never widen to s.Scope
  ```

---

### [S3] `GET /api/xss/config` discloses listener infrastructure to every `xss:read` holder

- **File:** `internal/handler/xss.go:366`
- **The defect**

  Returns `bind_host`, `bind_port`, `public_url` and `canary_cookie_name` to any user holding
  `xss:read` with no gate. The codebase has already decided that process-global configuration is
  not readable by `assigned`/`own` scope -- `resourceAllowed` blocks `/monitor/stats` and
  `/monitor/calls-timeline` to `scope == "all"` for exactly this reason, with the comment at
  `internal/security/rbac_middleware.go:219-223`. The XSS equivalent was not given the same
  treatment.

- **Concrete exploit**

  A `viewer` (which receives `xss:read` via the `:read` branch at
  `internal/database/rbac.go:395-400`) reads the operator's callback URL and canary cookie name.
  This is reconnaissance, not victim data, hence S3 -- but it hands a low-privilege account the
  exact origin it needs to social-engineer a higher-privileged one into visiting the panel.

- **Suggested fix**

  Add `/xss/config` to the `scope == "all"` gate list in `resourceAllowed`, next to the
  `/monitor/stats` case.

---

### [S3] `GET /api/c2/profiles/:id` -- global read paired with admin-only write

- **File:** `internal/handler/c2.go:1052`
- **The defect**

  `c2_profiles` has no `owner_user_id` column, and `resourceAllowed` deliberately gates only
  *non-GET* on `/c2/profiles` to `scope == "all"` (`internal/security/rbac_middleware.go:224-225`).
  `GET /api/c2/profiles/:id` therefore reaches `default: return true` and is readable by any
  `c2:read` holder, while `PUT` / `DELETE` on the same row require admin. The read/write asymmetry
  means any read-only user can enumerate every profile but change none of them.

  Contents are Malleable C2 User-Agent / URI / header / body templates -- infrastructure
  configuration, not victim data. Recorded because the asymmetry should be a conscious design
  choice rather than a side effect of which switch cases were written.

- **Concrete exploit**

  A `viewer` enumerates all C2 profiles and their templates. No mutation possible.

- **Suggested fix**

  Either add `owner_user_id` to `c2_profiles` and extend `rbacAssignableResourceTables`
  (`internal/database/rbac.go:26-35`), or move infra reads behind the same `scope == "all"` gate as
  `/monitor/stats`.

---

### [S3] `GET /api/conversations/:id/results` has no authorization of its own

- **File:** `internal/handler/openapi.go:6340`
- **The defect**

  `GetConversationResults` calls `h.db.GetConversation`, `h.db.GetMessages` and
  `h.db.ListVulnerabilities(..., RBACListAccess{})` -- the *unscoped* zero value, which per the
  finding above means "no predicate". It is safe today only because the route's `FullPath` matches
  `strings.HasPrefix(path, "/conversations/:id")` at
  `internal/security/rbac_middleware.go:235`.

  All of this endpoint's authorization lives in a path-string prefix maintained in a different
  file from the handler. Rename the route, add a sibling alias, or register it under a different
  prefix and it becomes S0 with no change to the handler.

- **Concrete exploit**

  None today.

- **Suggested fix**

  Add an explicit `UserCanAccessResource(..., "conversation", c.Param("id"))` call at the top of
  `GetConversationResults`, matching the belt-and-braces pattern already used by
  `GetConversationPlanTasks` (`internal/handler/conversation.go:250`).

---

### [S3] CORS same-origin test compares host but not scheme

- **File:** `internal/app/app.go:2272`
- **The defect**

  ```go
  sameHost := valid && strings.EqualFold(parsed.Host, c.Request.Host)
  ```

  An `http://app.example` Origin is treated as same-origin for a request to `https://app.example`.
  Anyone who can serve content on the plain-HTTP variant of the host -- a network position between
  client and server, or control of the HTTP vhost -- is inside the CORS allowlist with
  `Access-Control-Allow-Credentials: true` (`:2279`).

  The rest of the middleware is correctly hardened: `*` and `null` are rejected
  (`internal/app/app.go:2317`), origins carrying credentials/paths/queries are rejected
  (`:2321-2324`), and the Chromium-extension check requires a canonical 32-char ID (`:2297-2311`).
  This is the one residual gap.

- **Concrete exploit**

  An attacker who can MITM plaintext HTTP to the app host, or who compromises the HTTP-only
  vhost, gains credentialed cross-origin read/write against the API. Impact depends on whether
  the deployment actually issues the `auth_token` cookie -- `Login` returns the token in the JSON
  body (`internal/handler/auth.go:89-102`) and does not set a cookie, so a `localStorage`-token
  frontend is unaffected. The cookie reader at `internal/security/auth_middleware.go:146` means a
  cookie-based deployment *would* be affected.

- **Suggested fix**

  Require scheme equality too:

  ```go
  sameOrigin := valid && strings.EqualFold(parsed.Scheme, schemeOf(c.Request)) &&
      strings.EqualFold(parsed.Host, c.Request.Host)
  ```

---

### [S3] XSS capture listing ignores resource assignments

- **File:** `internal/database/database.go:2171`
- **The defect**

  `ListPayloads` (`internal/handler/xss.go:398-406`) routes through `UserCanAccessResource`, which
  honors `rbac_resource_assignments`. `ListXssCapturesForUser` does not -- it filters only on
  `p.owner_user_id = ? OR p.created_by = ?`:

  ```sql
  FROM xss_captures c JOIN xss_payloads p ON p.id = c.payload_id
  WHERE (p.owner_user_id = ? OR p.created_by = ?)
  ```

  A user granted a payload through the admin assignment picker sees it in `GET /api/xss/payloads`
  but receives zero captures from `GET /api/xss/captures`. It fails closed, so this is a
  correctness bug rather than a vulnerability -- but it will read to an administrator as "the grant
  silently doesn't work".

- **Suggested fix**

  Add the same `EXISTS (SELECT 1 FROM rbac_resource_assignments ...)` clause used by
  `appendVulnerabilityAccessFilter` (`internal/database/vulnerability.go:115-118`).

---

## 3. Previously-flagged items -- verdict

### (a) `batch_queue_executor.go:130` confused deputy -- **REFUTED, already fixed**

Traced end to end. The execution principal is derived from the **queue owner stored in the
database**, never from the request:

```go
// internal/handler/batch_queue_executor.go:130-136
ownerUserID := h.db.GetResourceOwner("batch_task", queueID)
access, accessErr := h.db.ResolveRBACAccess(ownerUserID)
if accessErr != nil || access == nil || !access.User.Enabled {
    h.batchTaskManager.UpdateTaskStatus(queueID, task.ID, BatchTaskStatusFailed, "", "队列所有者不存在或已禁用")
    return
}
principal := authctx.NewPrincipalWithScopes(access.User.ID, ...)
```

The owner is stamped from the authenticated session at creation time
(`internal/handler/agent.go:1938`: `h.db.SetResourceOwner("batch_task", queue.ID, session.UserID)`),
so it cannot be influenced by a later caller. The conversation created for each subtask is owned by
that same principal (`:146-147`). Missing-owner and disabled-owner both fail closed.

### (b) `ScopeFor` widening -- **CONFIRMED PRESENT but not reachable**

See the S3 finding above. The fallback to the broadest scope exists at
`internal/security/auth_manager.go:150`, but the middleware only reaches it after authorization has
already succeeded and `ResolveRBACAccess` has populated `PermissionScopes` for every granted key.

### (c) Handler trusting `user_id` / `owner_id` from the request body -- **REFUTED**

Swept every handler that reads an owner-bearing identifier. All are session-derived or routed
through `UserCanAccessResource` / an `...ForAccess` query. Two near-misses checked and cleared:

- `POST /api/robot/test` (`internal/handler/robot.go:1929`) does accept a `user_id` in the body, but
  the route requires `robot:write`, which is admin-only
  (`internal/database/rbac.go:389-393`).
- The asset bulk-mutate paths verify `accessible == len(unique)` before writing
  (`internal/handler/asset.go:1091-1095,1201-1205`), so a partially-unauthorized batch is rejected
  wholesale rather than partially applied.

### (d) Session fixation and logout -- **CLEAN**

- **No fixation.** `authenticateSession` mints a fresh `uuid.NewString()` per login
  (`internal/security/auth_manager.go:101`). No pre-authenticated identifier is accepted and reused.
- **Logout is server-side.** `internal/handler/auth.go:117` calls `h.manager.RevokeToken(token)`,
  which deletes from the server-side session map (`internal/security/auth_manager.go:225-233`).
  `ValidateToken` only consults that map (`:154-173`), so a revoked token is genuinely dead.
- **Administrative changes propagate.** Disabling a user, changing their roles, or changing their
  password revokes their sessions (`internal/handler/rbac.go:301`, `:317`;
  `internal/security/auth_manager.go:214-220`). Role edits revoke *all* sessions globally
  (`internal/handler/rbac.go:174,189`), so a permission change cannot be raced by a live token.
- **Expiry is enforced** at validation time (`internal/security/auth_manager.go:166-171`), 12 hours
  by default (`:45-46`).
- No cookie is set by `Login` (`internal/handler/auth.go:89-102` returns the token in the body);
  the `auth_token` cookie reader at `internal/security/auth_middleware.go:146` exists for external
  clients. `router.ForwardedByClientIP = false` (`internal/app/app.go:99`) prevents IP spoofing
  from bypassing the login rate limiter.

---

## 4. Fail-closed verification

| Question | Answer | Evidence |
|---|---|---|
| Route path with no permission mapping? | **Fails closed.** 403 | `internal/security/rbac_middleware.go:22-31` |
| Any mapped permission missing from `PermissionCatalog`? | **No.** All 275 protected routes map to a catalog key | Verified programmatically over all 286 registrations |
| `UserCanAccessResource` with empty user/type/ID? | `false` | `internal/database/rbac.go:523-525` |
| Non-existent resource ID under a gated prefix? | 403 before the handler runs; no existence oracle | `internal/security/rbac_middleware.go:50-56` |
| C2 parent-walk on lookup error? | `false` (fail-closed) | `internal/database/rbac.go:605-638` |
| XSS capture query with a foreign `payload_id`? | Returns empty, not the owner's rows | `internal/database/database.go:2175` |
| `appendConversationAccessSQL` with empty user ID? | `AND 1=0` -- fail-closed | `internal/handler/notification.go:148-150` |
| `appendVulnerabilityAccessFilter` with empty user ID? | **No predicate -- fails OPEN** | `internal/database/vulnerability.go:110` (S3 above) |
| `hitlInterruptAllowed` on missing interrupt? | `false` | `internal/handler/hitl_logs.go:323-328` |
| Unauthenticated robot webhooks? | WeCom verifies an HMAC signature (`internal/handler/robot.go:1653-1670`); DingTalk and Lark are inert placeholders that echo a challenge and touch no state (`:2031-2056`). Rate-limited at 60/min/IP (`internal/app/app.go:944-946`). | -- |

---

## 5. What is already correctly hardened

For completeness -- these were all checked and are **not** findings:

- **Vulnerability data extraction (3 routes).** `GET /api/vulnerabilities/export`,
  `/export-urls` and `/export-records` were mapped to `vulnerability:read`, which
  `grantSystemRolePermissions` grants to **viewer, operator and auditor** through the
  `strings.HasSuffix(key, ":read")` branch (`internal/database/rbac.go:395-400`). That made
  "read the list" identical to "carry the whole record set out" -- a viewer with no
  assignments could pull every vulnerability's target, evidence and reproduction steps.
  They now map to a dedicated `vulnerability:export` permission, granted to **operator and
  auditor only** (admin holds everything by construction). The three handlers additionally
  apply the same ownership scope as the list endpoint, so an `own`-scoped export cannot
  reach another tenant's records.

- **The batch-queue confused deputy** (see 3a) -- fixed.
- **C2 (34 routes).** The ownership chain `c2_tasks -> c2_sessions -> c2_listeners.owner_user_id`
  is enforced in `appendC2SessionAccessFilter`, `appendC2TaskAccessFilter`,
  `appendC2EventAccessFilter` and `appendC2ListenerAccessFilter`, all of which emit `1=0` on an
  empty user ID and no-op only for `scope == "all"`. Body- and query-supplied IDs
  (`DeleteSessions`, `DeleteEvents`, `ListFiles`, `UploadFileForImplant`) are pushed into the SQL
  predicate rather than trusted. Aggregate counts route through the same builders, so totals do
  not leak.
- **XSS captures** (`internal/handler/xss.go:561-574`) -- the highest-value target given they hold
  victim cookies and tokens, and they are correctly filtered via `ListXssCapturesForUser`.
- **Monitor (8 routes).** `tool_executions.owner_user_id` and `.conversation_id` are populated and
  used; `monitorExecutionAllowed` (`internal/handler/monitor.go:337-355`) gates GET, cancel and
  delete *before* any lookup. List responses are slimmed to drop `arguments` / `result`.
- **Chat uploads (10 routes).** `chat_upload_artifacts` is consulted as an *authorization source*,
  not merely written to (`internal/handler/chat_uploads.go:73-75`), and `pathAllowed` returns
  `false` when there is no session or no DB (`:64-67`).
- **WebShell exec** (`internal/handler/webshell.go:930-948`) -- correctly splits saved connections
  (per-connection ACL, DB credentials authoritative, attacker-supplied URL/password discarded) from
  unsaved connections (gated behind the admin-only `webshell:connect-unsaved`).
- **HITL** -- `hitlConversationAllowed` and `hitlInterruptAllowed` are fail-closed, and the global
  config endpoints are pinned to `scope == "all"`
  (`internal/security/rbac_middleware.go:226-227`).
- **List endpoints** -- projects, assets, conversations, vulnerabilities, webshell connections,
  workflow runs, HITL queues, agent tasks and audit logs all scope their result sets via
  `...ForAccess` helpers or a post-fetch `filterSlice`.
- **`route_inventory_test.go`** (`internal/security/route_inventory_test.go:13`) asserts that every
  protected route maps to a catalog permission. It inspects only the `protected`, `c2Routes` and
  `knowledgeRoutes` groups -- `authRoutes` and `robotGroup` are outside its AST scan. That is
  correct today (those two groups do not use `RBACMiddleware`), but the test gives no coverage if a
  route is ever moved onto `protected` with an inline `RequirePermission` only.
