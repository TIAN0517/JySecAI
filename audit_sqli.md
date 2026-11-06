# SQL Injection Audit — JySecAI

- **Target:** `C:\Users\Administrator\desktop\jysecai`
- **Scope:** `internal/database/` and every SQL-building call site repo-wide
- **Driver:** `github.com/mattn/go-sqlite3 v1.14.18` (`go.mod:27`) — raw `database/sql`, `?` positional placeholders. No ORM, no query builder.
- **Date:** 2026-10-04
- **Type:** Defensive audit of the project's own code. Report only; no files were modified.

## Result

**0 confirmed SQL injection vulnerabilities. 0 candidates that survived tracing.**

Every value that reaches SQL *structure* (column name, table name, `ORDER BY` expression, `LIMIT` literal) originates from a hardcoded literal or a `switch`/map whitelist. Every value that reaches a data position is bound through a `?` placeholder.

This codebase is uncharacteristically disciplined about this. The two classic bypasses the audit brief asked about — user-controlled `ORDER BY` and user-controlled table/column names — are both present in the architecture and **both are whitelisted**. I am reporting the negative result explicitly rather than manufacturing findings to appear thorough.

## Method

1. Multi-line regex sweep for `fmt.Sprintf` / `strings.Join` / `+` concatenation adjacent to SQL keywords (`SELECT|INSERT|UPDATE|DELETE|WHERE|ORDER BY|LIMIT|GROUP BY|FROM|VALUES|SET`), excluding prose false positives.
2. Targeted grep for the classic structural sinks: `ORDER BY`/`orderBy`/`sortBy`, dynamic `+ col|column|table|field`, `sqliteEpochGE`-style helpers, and `strings.Join` into `IN (...)`.
3. Enumeration of every function in the repo that accepts a raw SQL string parameter, then upward tracing of each to see whether any caller passes user-derived text.
4. Independent subagent sweep of `internal/handler/` enumerating every `c.Query`/`c.Param`/`c.PostForm`/JSON-body value reaching a `db.*` call, classified by whether it could affect structure.
5. Manual verification of every claim from step 4 against the actual source (the subagent's conclusions were re-read, not accepted on trust — it had missed the one raw-SQL sink in the codebase, covered below).

## Surfaces examined and why each is safe

### ORDER BY / column-name interpolation (the primary bypass class)

| Site | Source | Guard |
|---|---|---|
| `internal/database/asset.go:848` `assetOrderBy()` → used at `:802`, `:832` | `handler/asset.go:167` `c.Query("sort_by")` / `c.Query("sort_order")` | `switch strings.ToLower(strings.TrimSpace(sortBy))` over 8 literals; unrecognized input hits `default: "assets.last_seen_at"`. `direction` only ever becomes `"ASC"` or `"DESC"`. |
| `internal/database/conversation.go:530` `conversationOrderClause()` → used at `:550`, `:564`, `:593`, `:606` | `handler/conversation.go:163` `c.Query("sort_by")` | Exact comparison `== "created_at"`; otherwise hardcoded `"updated_at"`. |
| `internal/app/asset_tools.go:292,306` | MCP tool arg `sort_by` | Rejected unless it is one of 9 enumerated values (`oneOfOrEmpty`), **before** reaching the DB layer. |

`sort_by` is attacker-controlled end-to-end in the asset list endpoint, and it is genuinely interpolated into `ORDER BY` — but the switch statement is a total function with a safe default, so no input can alter the emitted expression.

### Dynamic table names (RBAC — the newest and highest-risk code)

`resourceType` from the request selects a physical table. This is the most dangerous shape in the codebase and it is consistently gated:

- `internal/database/rbac.go:640` `userOwnsResource`, `:667` `SetResourceOwner`, `:697` `GetResourceOwner` — `switch resourceType` assigning a literal table, with `default: return`. An unrecognized type exits before any SQL is built.
- `internal/database/rbac.go:983` `AssignResourcesToUser` and `:742` `ListAssignableRBACResourcesPage` — gated on `if _, ok := rbacAssignableResourceTables[resourceType]; !ok { return error }` (map at `rbac.go:26`, 8 entries), then a `switch resourceType` returning a fully literal query string.
- `internal/database/rbac.go:1093` — iterates a hardcoded `typeTablePairs` literal slice; no user string reaches `pair.table`.
- Reached from `handler/rbac.go:348,350,392,401` (JSON body `resourceType`, and `type`/`q` query params).

### Column/alias interpolation in RBAC scoping filters

- `internal/handler/notification.go:143` `appendConversationAccessSQL(query, args, column, access)` interpolates `column` into five SQL positions. All 4 call sites pass the literal `"conversation_id"` (`hitl.go:849`, `hitl_logs.go:173`, `hitl_logs.go:218`, `notification.go:220`). Verified by grep of every call site.
- `internal/database/conversation.go:452` `appendConversationAccessFilter` — `%s` is `prefix`, always `""` or `"c"`.
- `internal/database/asset.go:286` `appendAssetAccess` — all 18 call sites pass the literal `"assets"` as the alias.
- `internal/database/sqltime.go:15` `sqliteEpochGE(column, op)` interpolates **both** a column and a comparison operator — the most flexible injection primitive in the codebase. All 8 callers (`audit.go:82,86,217`, `c2.go:1055,1615`, `monitor.go:843,881`) pass literal column names and literal operators (`">="`, `"<="`, `"<"`).
- `internal/database/model_token_usage.go:369`, `project.go:147,159`, `vulnerability.go:41,108` — literal aliases and bound values.
- `internal/database/asset.go:461` — `item.column` drawn from a hardcoded 8-entry struct literal slice.

### `LIMIT` / `OFFSET`

`internal/database/c2.go:638,686` use `fmt.Sprintf(" LIMIT %d", filter.Limit)`. `filter.Limit` is a Go `int` (struct at `c2.go:585`). `%d` of an `int` cannot carry SQL text, so this is not injectable — though binding it as `LIMIT ?` would be more idiomatic and would survive a future refactor to a string-typed field.

### `strings.Join` into `IN (...)`

Every occurrence generates a fixed run of `?,?,?` placeholders and passes the real values as args — the correct pattern:

- `internal/database/hitl_logs.go:25-27` — `strings.Repeat("?,", len(clean))`; ids are bound.
- `internal/database/monitor.go:733,759` — `placeholders` slice, ids bound.

### The one raw-SQL sink in the codebase (traced, not exploitable)

`internal/database/hitl_logs.go:42` `DeleteHitlInterruptLogsMatching(whereSQL string, args []interface{})` concatenates a caller-supplied string directly into a `DELETE`. This is the only place in the repo where a complete WHERE clause crosses a package boundary as a string. I traced its single caller:

`internal/handler/hitl_logs.go:219` builds `where` as:
1. `h.buildHitlLogsWhere(true)` (`hitl_logs.go:88-99`) — returns `" WHERE 1=1 AND status != 'pending'"`, fully literal.
2. `h.appendHitlListFilters(where, args, c)` (`hitl_logs.go:101-135`) — reads `conversationId`, `toolName`, `decision`, `decidedBy`, `status`, `q` from the request and appends **only** fixed fragments (`" AND conversation_id = ?"`, `" AND tool_name LIKE ?"`, etc.), pushing every user value into `args`.
3. `appendConversationAccessSQL(where, args, "conversation_id", ...)` — literal column, userID bound.

The resulting string is a constant template with `?` holes; no request value alters its structure. **Not exploitable.** Flagged only as a design-fragility note: this helper's safety depends entirely on all current and future callers building `whereSQL` from literals. A future caller that does `where := "... AND tool_name = '" + toolName + "'"` would inject silently, with no type or linting signal. Marking it `//nolint`-style safe is worth considering.

### Values reaching `?` positions

Confirmed bound, never concatenated: `handler/hitl_logs.go` filters; `handler/notification.go:210,260,504`; `handler/hitl_execution.go:117,131`; `handler/hitl.go:418,473,551,578,603-612,698,920`; `handler/agent.go:691,717,758`; `handler/multi_agent.go:188,373,392,522`; `handler/eino_single_agent.go:181,359,378`; `handler/workflow_integration.go:85,133,148,266`; `handler/finalization_helpers.go:96,140`; `handler/batch_queue_executor.go:416`; `handler/asset.go` filters; `handler/vulnerability.go:214-229,311-313`; `handler/audit_query.go:13-21,39,42`; `handler/c2.go:63,309-313,504-507,910-914`; `handler/monitor.go:108,113,120,122`; `handler/project.go:336,346-352,403,457`; `handler/webshell.go:509,596-825`; `handler/token_usage.go:34,48,55,63-75`; `handler/xss.go:505,519,549`; `handler/workflow_run.go:24,47,79,105`; `handler/knowledge.go:64,65`.

`internal/database/monitor.go:140,188` concatenate `conditions[0]` then loop `conditions[1:]` — but every element of `conditions` is a hardcoded literal (`"status = ?"`, `"LOWER(tool_name) LIKE ?"`); the values are in `args`.

## Non-issues explicitly ruled out (not findings)

- `internal/database/database.go:1609` — `Sprintf("UPDATE vulnerabilities_new SET %s = ... v.%s ...", name, name)` in a migration. `name` iterates a hardcoded `[]string{"confidence"}`.
- `internal/database/database.go:43` — `Sprintf("PRAGMA journal_size_limit=%d", ...)` with a constant.
- `internal/database/rbac.go:217` `addColumnIfMissing(table, name, stmt)` — dynamic, but every caller passes literals.
- `handler/vulnerability.go:608` `group_by` / `handler/knowledge.go:327` `mode` — rejected against an enum before use, never reaches the DB layer.
- `handler/c2.go:1006-1008` `session_id`/`category`/`level` (`QueryArray`) — reach `EventBus.Subscribe`, no SQL.
- `handler/chat_uploads.go:368,1415,1443,1496` — filesystem path construction, no SQL.
- `handler/role.go`, `handler/external_mcp.go`, `handler/markdown_agents.go`, `handler/skills.go`, `handler/config.go` — in-memory config and filesystem only; no DB access at all.

## LIKE-injection note (informational, not a finding)

LIKE patterns are built as `"%" + input + "%"` and bound — e.g. `handler/hitl_logs.go:115,130`, `database/monitor.go:135,183`, `database/asset.go` search. In SQLite this is a matching-semantics quirk, not SQL injection: an attacker can broaden a search with `%`/`_`, but cannot escape the string, alter the statement, or reach another tenant's rows (the RBAC `EXISTS` clauses are appended independently and are unaffected). Notably `rbac.go:751-755` *does* escape `%`, `_`, and `\` in its search term — the more careful implementation of the two patterns present in the repo.

## Residual risk (not findings — no current code path)

1. `DeleteHitlInterruptLogsMatching` (above) — the one function whose signature invites raw SQL. Currently safe; fragile against future callers.
2. `sqliteEpochGE(column, op)` — accepts an operator string. Safe today because all 8 callers are literals. A one-line change making `op` caller-supplied would open injection with no compiler help, since `op` is an unconstrained `string`.
3. The `switch`-based whitelists (`assetOrderBy`, `conversationOrderClause`, the four RBAC `switch resourceType` blocks, `rbacAssignableResourceTables`) are duplicated in five places. This is correct today, but a shared `map[string]string` lookup (as `rbacAssignableResourceTables` already does) would make the invariant mechanical rather than positional, and would fail closed by construction.
