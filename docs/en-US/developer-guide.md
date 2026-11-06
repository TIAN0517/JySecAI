# Developer Guide

[中文](../zh-CN/developer-guide.md)

This guide is for contributors extending JySecAI. The project is a Go single-service application with a static frontend, SQLite persistence, Agent/MCP orchestration, and optional high-risk security subsystems.

## Project Layout

```text
cmd/server/              service entrypoint
internal/app/            app wiring, routes, MCP tool registration
internal/handler/        HTTP handlers
internal/database/       SQLite access
internal/security/       auth, rate limits, shell execution
internal/mcp/            MCP server and external MCP manager
internal/multiagent/     Eino single-agent, multi-agent, middleware
internal/workflow/       graph orchestration runtime
internal/knowledge/      indexing and retrieval
internal/c2/             built-in C2
internal/project/        project fact blackboard
web/static/              frontend JS/CSS/assets
web/templates/           HTML templates
tools/                   YAML command tools
roles/                   role YAML
agents/                  multi-agent Markdown definitions
skills/                  Agent Skills
docs/                    documentation
```

## Development Startup

```bash
go run ./cmd/server --config config.yaml
```

The frontend is static. Most JS/CSS/template changes only require a browser refresh.

## Adding a Business Module

Do not add only a handler. A complete module usually needs:

1. Data model and SQLite migration.
2. Handler: parameters, errors, pagination/filtering.
3. Audit: management actions.
4. Monitor: long-running execution state.
5. MCP: whether Agents should call it.
6. HITL: approval boundary for MCP tools.
7. OpenAPI: update `/api/openapi/spec`.
8. Frontend: i18n, states, empty/error UI.
9. Tests: DB, handler, edge cases.
10. Docs: config, usage, troubleshooting, safety impact.

Missing one of these usually becomes a later usability or safety bug.

## External MySQL Receiver

The platform's own database stays SQLite. `external_mysql` is a **downstream
receiver**: it ships harvested results (vulnerability evidence, project-fact
blackboard content, their sensitivity grading and full provenance) to an
external MySQL for later aggregation and delivery.

```
vulnerability / fact written → DB-layer hook → local outbox (SQLite) → background drainer → external MySQL
```

Three rules that must not be broken:

1. **The external MySQL never destabilizes the platform.** Results land in the
   platform's own SQLite outbox table (`receiver_outbox`) first and are shipped
   when MySQL is reachable. An outage means "delivery is deferred", not
   "the data disappeared".
2. **The main write path is never blocked.** Both the outbox write and the
   delivery run on the hook's own goroutine, outside the vulnerability write
   transaction.
3. **Idempotent delivery.** Keyed on `(source_kind, source_id)`: unchanged
   content is skipped, changed content overwrites in place. Re-delivery never
   stores N copies of the same result.

Configuration (`config.yaml`; keep the password in an environment variable such
as `${JY_SEC_MYSQL_PASSWORD}`):

```yaml
external_mysql:
  enabled: true
  host: 10.0.0.1
  port: 3306
  user: jy_receiver
  password: ${JY_SEC_MYSQL_PASSWORD}
  database: jy_vuln_receiver
  poll_interval_seconds: 5
  batch_size: 50
```

Create the database and its least-privilege account (scoped to the receiver
database only — never use root):

```bash
export MYSQL_ROOT_PASSWORD='...'
python scripts/setup-receiver-db.py
```

Code: `internal/receiver/` (payload model, sensitivity grading, MySQL delivery,
outbox), `internal/app/receiver_bridge.go` (bridge and drainer),
`internal/app/receiver_setup.go` (wiring). The hooks are
`AddVulnerabilityPersistedHook` and `AddProjectFactUpsertedHook` — both fire at
the **database layer**, so every write path is covered (including the
`security_ops` auto-create path and POC draft write-back).

### De-identification on outbound data

Everything shipped to the external MySQL is **masked by default**, and the
masking happens **before the result enters the local outbox** — the outbox only
ever stores masked content, so there is no "raw in the outbox, masked on the
way out" gap.

Rules (single implementation point: `internal/vulnmask`):

| Object | Treatment |
| --- | --- |
| IPv4 / IPv6 addresses | Public addresses become a stable pseudonym `ip-<hash8>` (same address always yields the same pseudonym: correlatable, not reversible); private / loopback / link-local collapse to `internal-redacted` |
| Credentials in URL parameters or body text | Replaced with `***` |
| Hostnames | **Kept by default** (a hostname is the smallest unit of analysis); set `mask_hosts: true` to hide them too |
| Type / severity / status / confidence / IDs | Not masked — these are the analysis dimensions |

Masked columns include `target`, `title`, `evidence`, `body`, the descriptive
text inside meta, and free-text columns such as `conversation_tag` / `task_tag`.

> Address detection is "a whole digit-and-dot run that looks like an address
> gets masked", **not** a regex word boundary. `%2052.128.238.210` (an address
> right after a URL-encoded space) is skipped entirely by word-boundary
> matching — production data showed an internal address reaching the external
> database that way. Regression coverage:
> `internal/vulnmask/vulnmask_boundary_test.go`.

`disable_masking: true` turns masking off. Use it only when you know exactly
what it costs.

When adding a new harvest source: add a persistence hook in `internal/database`,
add a `Payload` mapping function in `internal/app/receiver_bridge.go`, and
register it in `internal/app/receiver_setup.go`. Never deliver to the external
database synchronously from inside a hook.

## Error Response Design

Prefer stable JSON:

```json
{
  "error": "machine_readable_code",
  "message": "human-readable explanation"
}
```

Frontend needs stable fields, users need actionable messages, and logs need detailed internal errors.

## Long-Running Tasks

For scanning, indexing, batch tasks, C2, or external operations, answer:

- Can it be cancelled?
- Can progress be queried?
- Can it be retried?
- Where is the result stored?
- Does state survive page refresh?
- Does it block the HTTP request?

If not, use task tables, event streams, or monitoring.

## Extending Tools

Prefer `tools/*.yaml` for command tools. Use Go built-in tools when the tool needs internal state or structured integration.

Built-in tools should define clear input schemas, handle timeouts and errors, and respect HITL for risky actions.

## Frontend Changes

Use existing helpers such as `apiFetch`, modal utilities, notifications, and i18n. Update both `web/static/i18n/zh-CN.json` and `web/static/i18n/en-US.json` for new visible text.

Avoid putting secrets or provider keys in frontend code.

## Test Priority

High-value tests:

- config hot-apply;
- HITL branches;
- shell timeout/no-output;
- external MCP recovery;
- KB indexing and post-processing;
- WebShell OS/encoding detection;
- SQLite migration compatibility.

## Source Anchors

- App wiring: `internal/app/app.go`
- Config apply: `internal/handler/config.go`
- OpenAPI: `internal/handler/openapi.go`
- Tool executor: `internal/security/executor.go`
- Skill package: `internal/skillpackage/`
