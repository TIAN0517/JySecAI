# Scope Registry

> The single source of truth for authorization on the platform side: who may touch which targets, with which actions — all of it in the database, auditable and expandable.

## What problem this solves

Before the Scope Registry, the platform side (Go) had **no target allow-list at all**:

- MCP tools fired at any host;
- the only real protections were RBAC (who may use the platform), HITL (whether to approve this call), the SSRF guard, and the forbidden-zone rules that were wired into exactly one feature (controlled redirect verification);
- authorization itself existed in one place, and the wrong one — `all/漏洞庫/_授權.json` (Python side).

In other words: authorization was **single-sourced, misplaced, and half-covered**. Going through the console was blocked by `guard.py`; going straight to the platform's MCP tools bypassed it entirely.

The Scope Registry turns authorization into a state machine that is **single-sourced, authoritative, auditable, and expandable by the tool chain itself**. The cost of expanding scope drops from "hand-edit a JSON file and reconcile both sides" to "press a button".

The full design lives in [`docs/superpowers/specs/2026-11-02-scope-registry-handoff-design.md`](../../docs/superpowers/specs/2026-11-02-scope-registry-handoff-design.md).

## Three terms first

| Term | Meaning | Who writes it |
| --- | --- | --- |
| **Standing set** (`scope_targets`) | Permanent authorization: your own assets, approved client scopes | Maintained by the operator; imported on rollout |
| **Grant** (`scope_grants`) | Conditional / one-shot authorization, carries its own target description | Created when the operator picks "allow once" or "approve with conditions" |
| **Denial memory** (`scope_denials`) | Targets that were rejected | Created on "reject"; the same target is refused directly afterwards and never asks again |

## Data model

The three tables are created by `EnsureScopeSchema()` in `internal/database/scope.go`. The migration is **idempotent and backward compatible** — existing database files open without a rebuild.

### `scope_targets` — standing set

| Column | Meaning |
| --- | --- |
| `id` | Primary key (`scope_` + uuid) |
| `owner` | Owner: `self` or a client name |
| `target_type` | `host` / `wildcard` / `cidr` / `url_prefix` |
| `target_value` | Target value (host, network, normalized URL) |
| `action_classes` | JSON array; **an empty array means the four general classes only**, not everything |
| `conditions` | JSON: `{port, max_uses, valid_until}` |
| `valid_from` / `valid_until` | Authorization validity window |
| `provenance` | JSON: `{source, decided_by, decided_at, evidence_hash, note}` |
| `status` | `active` / `revoked` |

### `scope_grants` — grants

| Column | Meaning |
| --- | --- |
| `id` | Primary key |
| `target_type` / `target_value` | A grant carries its own target description, so a brand-new target needs no standing-set row first |
| `action_classes` | Action classes this grant permits |
| `max_uses` / `uses_used` | Use limit and used count |
| `valid_until` | Grant expiry |
| `issued_by` / `issued_at` / `evidence` | Who issued it, when, on what evidence |
| `status` | `active` / `exhausted` / `expired` / `revoked` |

### `scope_denials` — denial memory

`target` (the normalized target key) is the primary key, plus `owner` / `reason` / `decided_by` / `decided_at`.

## Action classes

The vocabulary reuses the eight classes already present in `all/工具/guard.py` so both sides stay aligned:

| Class | Meaning | Default authorization |
| --- | --- | --- |
| `local_analysis` | Local file analysis | No authorization needed |
| `offline_replay` | Offline replay / local evidence matching | No authorization needed |
| `harmless_request` | Harmless request (GET/HEAD class) | Allowed when `action_classes` is empty |
| `db_read_extract` | Read-only database extraction | Allowed when `action_classes` is empty |
| `credential_enum` | Credential enumeration | **Must be listed explicitly** |
| `bulk_scan` | Bulk scanning | **Must be listed explicitly** |
| `destructive` | Destructive action (write / delete / tamper) | **Permanently blocked** |
| `real_transaction` | Real transaction (order / payment / transfer) | **Permanently blocked** |
| `arbitrary` | Tool declares no `action_class` | **Must be listed explicitly**, and always requires approval |

**The easiest thing to get wrong**: an empty `action_classes` array means "all general classes are allowed" (`local_analysis` / `offline_replay` / `harmless_request` / `db_read_extract`) — **not** "all classes are allowed". `credential_enum` / `bulk_scan` / `arbitrary` must be listed explicitly, and `destructive` / `real_transaction` cannot be unlocked by any scope.

Tools declare their action class in `tools/*.yaml`:

```yaml
name: "httpx"
action_class: "harmless_request"
parameters:
  - name: "targets"
    type: "string"
    target: true
    target_kind: "mixed"
```

A tool with no `action_class` is always treated as `arbitrary` (strictest).

## Enforcement modes

```yaml
scope:
  enforcement: "enforce"   # off | audit | enforce
  default_owner: "self"
  timeout_seconds: 0       # 0 = inherit the conversation's HITL timeout
```

| Mode | Behaviour | When to use |
| --- | --- | --- |
| `off` (default) | No evaluation at all; existing behaviour preserved | Right after upgrading, before any import |
| `audit` | Evaluate and write `audit_logs` (`action=scope_resolve`), **never block a call** | See the coverage gaps before deciding to enforce |
| `enforce` | Uncovered targets raise a `scope_extension` interrupt; forbidden zones and permanently blocked classes are refused outright | After the authorization set is imported and you want the platform to actually hold the line |

> **`off` is the default on purpose**: with an empty registry, `enforce` would raise an authorization card on every network-touching tool call, which effectively locks the platform. Use `audit` to see the gaps, import the authorization, and only then switch to `enforce`.

Config edits require `systemctl restart jysec-core` — the configuration file is read once at startup.

## Matching rules

The order is fixed and must not be swapped:

1. **Forbidden zones first**: targets matched by `internal/forbidden` (119 / EPCR / fire-rescue) are refused outright and are **not** listed as uncovered — they are not "not yet authorized", they are "must never be touched". Even an explicit operator approval does not lift them.
2. **Permanently blocked classes**: `destructive` / `real_transaction` refuse the whole batch.
3. **Denial memory**: previously rejected targets are refused directly.
4. **Standing set** (`scope_targets`) → **grants** (`scope_grants`).

Target-type matching:

- `host`: exact hostname;
- `wildcard`: one label of subdomain (`*.example.com` matches `x.example.com` but **not** `x.y.example.com`);
- `cidr`: network block (`192.0.2.0/24`);
- `url_prefix`: URL prefix.

`conditions.port` is only compared when present; without an explicit port the scheme default applies (http=80, https=443).

## Where targets come from

Authorization can only hold if we know who the call will touch. Targets can hide in three places, and **all three are required**:

1. **The tool's target parameter itself**: `positional`, `flag`, and `template` formats are all read;
2. **A list file inside `additional_args`**: `-l <file>` / `--list <file>` → **the file is read and expanded** (one file can hold thousands of entries);
3. **The tool's stdin**: `httpx` receives its targets on stdin.

If none of the three yields anything, the call is treated as **arbitrary execution** (`arbitrary`). That does not mean "there are no targets" — it means "the targets are hidden in the command". In that case the operator must declare the target list for that call, and **approval is refused if nothing was declared**.

## The scope_extension card

Under `enforce`, an uncovered target is not refused outright. It raises an authorization decision card, reusing the existing HITL flow and SSE events — **no separate queue mechanism**:

```
Uncovered target : new.api.example.com
Source tool      : httpx            Action class: harmless_request
Reason           : not covered by any scope allow-list
Adjacent grant   : api.example.com · Owner: example-client · Valid until: 2026-12-01T00:00:00Z
Choices: [Approve permanently] [Allow once] [Approve with conditions] [Reject]
```

| Decision | Written to | Effect |
| --- | --- | --- |
| **Approve permanently** (`approve_permanent`) | `scope_targets` | Added to the permanent scope; later calls of the same kind stop asking |
| **Allow once** (`approve_once`) | `scope_grants` (`max_uses=1`) | This call only, then it is spent |
| **Approve with conditions** (`approve_conditional`) | `scope_grants` (uses / window / classes) | Allowed N times, or until a given time |
| **Reject** (`reject`) | `scope_denials` | Remembered; the target is refused directly afterwards and never asks again |

Approval **resumes in place**: once the interrupt ends, the original tool call proceeds with no argument rewriting.

Conditional approval accepts: owner, max uses, valid-until (RFC3339), and action classes (comma separated).

### API

`POST /api/hitl/decision` keeps the existing endpoint; `scope_extension` mode accepts two extra fields:

```json
{
  "interruptId": "hitl_xxx",
  "decision": "approve_conditional",
  "comment": "client confirmed this test in writing",
  "scopeConditions": {
    "owner": "example-client",
    "actionClasses": ["harmless_request"],
    "maxUses": 3,
    "validUntil": "2026-12-01T00:00:00Z"
  },
  "scopeTargets": ["new.api.example.com"]
}
```

- `scopeConditions` is only used by `scope_extension` mode; other modes ignore it.
- `scopeTargets` is the operator-declared target list; it is **mandatory for arbitrary-execution tools**, and a decision without it is refused (nothing is written).
- The existing `approval` / `review_edit` modes still accept **only** `approve` / `reject`; their behaviour was not widened at all.

## Importing existing authorization

The platform ships an import CLI that is safe to re-run and idempotent:

```bash
# Inspect what would be imported (writes nothing)
go run ./cmd/scopeimport --config /var/lib/jysecai/core/config.yaml \
  --source /path/to/_授權.json --dry-run

# Actually import
go run ./cmd/scopeimport --config /var/lib/jysecai/core/config.yaml \
  --source /path/to/_授權.json
```

Rules:

- entries in `allowed_hosts` starting with `*.` become `target_type=wildcard`, the rest become `host`;
- `authorized_until` becomes `valid_until` (a parse failure leaves it empty and warns — it never fails the whole import);
- `allowed_action_classes` becomes `action_classes` (empty stays empty, i.e. the general classes);
- `provenance.source` records the source file name;
- **forbidden-zone targets are skipped with a warning** — forbidden zones always win and never enter the registry through an import;
- the idempotency key is `owner` + `target_type` + `target_value`, so re-running the same source creates no duplicate rows.

## Audit

- Every evaluation writes `audit_logs`: `action=scope_resolve`, with the targets, the matched scope (`grantId` / `source` / `owner`), the uncovered list, the denied list, the decision, the decision maker, the linked HITL interrupt id, and the enforcement mode in effect.
- Authorization state changes are recorded in `scope_targets.provenance` (who, when, on what evidence, from which source).
- The interrupt itself uses the existing `hitl_interrupts` table and the existing retention policy.

## Pending grants: turning "always refuse" into a visible, approvable queue

### The problem

With `scope.enforcement` on but an empty registry, the agent degrades into
"I won't do it" for every target that needs authorization — the platform never
asked the operator whether the action was allowed. Reviewing a thousand
confirmed critical/high targets one by one is not realistic, so the workflow
deadlocks on doing nothing at all.

### Coverage audit (scope-audit)

Quantify the gap before talking about authorization:

```bash
# Produce the coverage report (read-only, writes no data)
./build/releases/scope-audit \
  --config /var/lib/jysecai/core/config.yaml \
  --status confirmed --severity critical,high \
  --action-class db_read_extract \
  --out docs/scope-audit-$(date +%Y%m%d-%H%M%S).md
```

Measured on 2026-11-07: 1023 confirmed critical/high vulnerability records,
803 distinct target keys after deduplication — 729 usable hosts and 74
unparseable entries (free-text descriptions in the vulnerability `target`
column). Coverage 0%.

Noisy entries are never drafted: `scopeaudit.PlausibleHost` rejects
descriptions like "dns.example.tw (61.63.14.15 與 61.218.16.228)", because
turning those into grants only fills the registry with garbage.

### Automatic drafting (scope-drafter)

```bash
# Inspect first (writes nothing, sends nothing)
./build/releases/scope-drafter --config /var/lib/jysecai/core/config.yaml --limit 20 --dry-run

# Actually draft + push the approval notification
./build/releases/scope-drafter --config /var/lib/jysecai/core/config.yaml --limit 20
```

Every drafted grant is `status=pending`, `max_uses=1`, valid for 24 hours by
default, with `action_classes` listed explicitly
(`db_read_extract,harmless_request,local_analysis,offline_replay`).

**A pending grant is not an authorization.** `matchGrantRows` in
`internal/scope` skips grants whose status is `pending`, so drafting only
moves the problem in front of a human — it never makes an unapproved target
reachable. A test pins this behaviour (`TestPendingGrantDoesNotCover`).

### Three approval paths

| Path | Permission | When |
|---|---|---|
| `POST /api/scope/grants/:id/activate` | `scope:write` (admin only by default) | From inside the platform |
| Telegram inline button | bound account holding `scope:write` | Quick approval from a phone |
| `scripts/scope-approve.sh --activate <id>` | root | Fallback when the Telegram token is dead |

The CLI and the API share the same data-layer semantics (pending → active
only, no replay, expired or exhausted grants cannot be activated); the CLI
just records the approver as `cli:<unix-user>`.

```bash
# List pending grants
bash scripts/scope-approve.sh --list

# Approve one
bash scripts/scope-approve.sh --activate grant_draft_a7dfc90c4c108436 --by operator

# Reject (also writes denial memory, so the target stops interrupting)
bash scripts/scope-approve.sh --reject grant_draft_a7dfc90c4c108436 --owner operator
```

### Permission model

`scope:write` is admin-only by default: approving a grant changes the
security boundary itself. Granting it to operators too would let them
approve their own requests — which is no control at all. `scope:read` follows
the platform's existing convention and goes to operator/auditor/viewer.

### Telegram approval buttons

Button presses arrive as Telegram `callback_query` updates. The platform now
handles them (`internal/robot/telegram_callback.go`), and **the person who
presses the button must be a bound platform account holding `scope:write`** —
everyone who can message the bot can see the notification, so without the
permission check the approval right would belong to all of them.

Note: if `getMe` answers 404 Not Found, the bot token has been revoked or
rotated and `robots.telegram.enabled` should stay `false` — otherwise the
poller retries every 5 seconds and fills the log while receiving nothing.
A valid token is all that is needed to turn it back on.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every network-touching tool call raises an authorization card | `enforcement: enforce` with an empty registry | Import the authorization first, or switch to `audit` / `off` |
| Edited `config.yaml` but nothing changed | The config file is read once at startup | `systemctl restart jysec-core` |
| Blocked even though the target is authorized | The action class was not listed explicitly (`credential_enum` / `bulk_scan` / `arbitrary`) | Add the class to `action_classes`, or use authorization that matches the class |
| A target is refused and there is no way around it | Forbidden zone, or a permanently blocked class | By design: forbidden zones and `destructive` / `real_transaction` cannot be unlocked |
| The same target keeps raising a card | It was a "timeout auto-reject" rather than an explicit "reject" | Timeouts are written to denial memory too; delete the matching `scope_denials` row to reopen it |
| Approved, yet interception point B still refuses | A race between writing the grant and resuming | Approval writes the registry first and resumes afterwards; if it still happens, check whether `scope_grants.uses_used` is already exhausted |
| The guard suite (`verify_all.py`) turns red after an import | The import changed a verdict | Verdicts must be identical before and after the import; compare the same scope set on both sides |

## Related documentation

- [HITL Best Practices](hitl-best-practices.md) — how to run human approval well
- [Tool Execution Governance](tool-execution-governance.md) — governance of the tool execution surface
- [Security Model](security-model.md) — the platform's overall security model
- [Audit and Monitoring](audit-and-monitoring.md) — auditing and monitoring
