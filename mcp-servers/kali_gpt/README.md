# Kali GPT MCP

Offline, reasoning-only pentest assistant for JySecAI. It re-implements the
OBSERVE → THINK → ACT → LEARN loop of the upstream
[`kali-gpt`](https://github.com/alishahid74/kali-gpt) project as **MCP tools**
inside the platform:

| Capability | How it is exposed |
|---|---|
| MITRE ATT&CK mapping of every planned tool invocation | `kali_map_to_mitre` |
| Dynamic tool-chain selection driven by discovered findings | `kali_suggest_toolchain` |
| PTES-phased methodology planning | `kali_plan_phase` |
| Persistent memory of target fingerprints and tool success rates | `kali_record_memory` / `kali_recall_memory` |
| Self check | `kali_gpt_status` |

> **Planning only — it never executes anything.**
> This server starts no processes, opens no sockets and makes no network calls.
> It never touches a target. Every `command_template` it returns is a
> placeholder string containing `{target}` / `{port}` / `{wordlist}` / `{url}`;
> the server never substitutes a real target and never runs the result.

## Tools

### `kali_map_to_mitre(tool: str, args_hint: str = "")`

Maps a tool invocation to MITRE ATT&CK Enterprise using a **curated offline
table** (no network, no STIX fetch).

Returns
`{"tool", "tactic", "technique_id", "technique_name", "tactic_rationale",
"related_techniques": [{"technique_id", "technique_name", "tactic"}],
"technique_source": "curated-offline", "mapped": bool}`

Unknown tools never raise: they return a structured fallback with
`tactic: "unknown"`, `mapped: false` and
`technique_source: "curated-offline:unmapped"`.

### `kali_suggest_toolchain(findings: list, limit: int = 8)`

Builds a tool chain from discovered findings. `findings` accepts a list of
dicts (`{"type": "open_port", "port": 80}`, `{"type": "web_tech",
"value": "wordpress"}`, `{"type": "service", "service": "smb"}`) or a
free-form string.

Returns
`{"findings": N, "chain": [{"step", "tool", "purpose", "mitre_tactic",
"technique_id", "depends_on", "command_template", "requires_authorization"}],
"notes": [...], "execution_policy": "..."}`

Built-in rules include: web ports → whatweb → nikto → ffuf → nuclei;
WordPress → wpscan + nuclei templates; SMB → enum4linux → smbmap → netexec;
LDAP → ldapsearch → bloodhound → kerbrute; SSH → ssh-audit → hydra; MySQL →
enumeration, adding sqlmap **only** when a web front-end exists; an existing
SQLi finding → sqlmap with a clearly-marked non-destructive profile
(`--batch --level --risk`, `tamper=space2comment`, no `--dump`); container /
Kubernetes findings → docker + kubectl audit paths.

### `kali_plan_phase(phase: str, target: str, context: str = "")`

Returns a PTES phase plan. Supported phases: `recon`, `scan`, `enumeration`,
`vulnerability-analysis`, `exploitation`, `reporting`. Aliases:
`information-gathering` → recon, `vuln-analysis` → vulnerability-analysis,
`report` → reporting, `attack` → exploitation.

Returns
`{"ok": true, "phase", "phase_title", "target", "steps": [{"order", "title",
"description", "tools", "mitre_tactics", "expected_output",
"requires_authorization"}], "mitre_coverage": [...], "execution_policy": "..."}`

### `kali_record_memory(entry: dict)`

Persists one engagement lesson. `entry` fields: `target_fingerprint` (str,
required), `tool` (str, required), `technique_id` (str, optional),
`outcome` (`success` / `failure` / `partial`, defaults to `partial`),
`notes` (str, capped at 2000 chars), `tags` (list[str], capped at 16 entries
of 64 chars).

Returns `{"ok": true, "id": N, "memory_db": path}` or
`{"ok": false, "error": "..."}`.

### `kali_recall_memory(target_fingerprint: str = "", tool: str = "", limit: int = 10)`

Returns past lessons ranked by exact fingerprint match first, then tool and
tag overlap. Returns `{"entries": [{"id", "target_fingerprint", "tool",
"technique_id", "outcome", "notes", "tags", "updated_at", "score"}],
"total": N, "matched_total": N}`. An empty fingerprint returns the most
recent entries. A missing database returns an empty list, not an error.

### `kali_gpt_status()`

Returns `{"ok": true, "tool_count": 6, "memory_db": path,
"memory_entries": N, "provider": "curated-offline-rule-engine", "note": "..."}`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `KALI_GPT_MEMORY_DB` | `~/.jysecai/kali_gpt/memory.db` | SQLite path for engagement memory. Parent directories are created on first write. |

The database is created lazily on the first write; reads against a missing
file return an empty list. Schema:

```sql
CREATE TABLE engagement_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fingerprint TEXT,
    tool TEXT,
    technique_id TEXT,
    outcome TEXT,
    notes TEXT,
    tags TEXT,          -- comma-joined
    updated_at TEXT     -- RFC3339 UTC
);
CREATE INDEX idx_engagement_memory_fingerprint ON engagement_memory(target_fingerprint);
```

All SQL uses parameterised statements. Tags are stored comma-joined and
parsed back on read. Returned rows are capped at 100.

## Registering in JySecAI (`config.yaml`)

Paste this block under `external_mcp.servers`:

```yaml
    kali-gpt:
      command: python3
      args:
      - mcp-servers/kali_gpt/mcp_kali_gpt.py
      description: 'Kali GPT: offline pentest reasoning (ATT&CK mapping, tool-chain selection, PTES planning, engagement memory). Planning only, never executes.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        kali_map_to_mitre: true
        kali_suggest_toolchain: true
        kali_plan_phase: true
        kali_record_memory: true
        kali_recall_memory: true
        kali_gpt_status: true
```

## Running and testing

```bash
# stdio transport
python3 mcp-servers/kali_gpt/mcp_kali_gpt.py

# tests (no network, temp DB via KALI_GPT_MEMORY_DB)
python3 -m unittest discover -s mcp-servers/kali_gpt -v
```

## ATT&CK mapping caveat

The mapping table is **hand-curated and offline**. It is not the official
MITRE ATT&CK dataset and it will drift from upstream as techniques change.

Before using a technique ID in a report, cross-check it against the sibling
`redteam-knowledge` MCP (`redteam_get_attack`), which fetches the official
ATT&CK STIX data and returns mitigations, detections and version metadata.
`kali_map_to_mitre` also returns `related_techniques` so a reviewer can see
nearby techniques that the curated entry deliberately did not pick.

## Execution policy

`execution_policy` is returned by every planning tool and states the same
thing:

- This MCP never executes commands, never contacts a target, performs no
  network I/O.
- Running a `command_template` requires the normal JySecAI tool path:
  the **HITL approval gate** must approve the call, and the **scope
  registry** must authorize the target and the action class
  (`credential_enum` / `bulk_scan` / `arbitrary` are never implicit;
  `destructive` and `real_transaction` can never be unlocked).
- Templates are conservative defaults and must be reviewed against the
  engagement rules of engagement.
