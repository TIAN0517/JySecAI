# Security Hardening

[中文](../zh-CN/security-hardening.md)

This checklist covers pre-production and continuous hardening for JySecAI.

## Before Going Live

- Change the initial `admin` password from the Web UI after first login.
- Use HTTPS or a trusted reverse proxy.
- Restrict access by IP, VPN, or bastion.
- Enable `audit.enabled`.
- Set `c2.enabled: false` when C2 is not required.
- Do not expose standalone HTTP MCP without strong auth and network isolation.
- Connect only trusted external MCP services.
- Back up `config.yaml`, `data/`, and custom resource directories.

## Reverse Proxy Baseline

```nginx
client_max_body_size 200m;
proxy_buffering off;
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

Recommended security headers:

```nginx
add_header X-Content-Type-Options nosniff;
add_header Referrer-Policy no-referrer;
add_header X-Frame-Options DENY;
```

## HITL Allowlist Baseline

Minimal allowlist:

```yaml
hitl:
  tool_whitelist:
    - read_file
    - glob
    - grep
    - tool_search
```

Do not globally allowlist:

- `execute`;
- WebShell write/execute tools;
- C2 task/payload tools;
- high-risk external MCP tools;
- delete, write, upload, persistence tools.

## File Permissions

```bash
chmod 600 config.yaml
chmod 700 data
```

Run under a dedicated OS user. Avoid root unless explicitly required.

## External MCP Review

Before connecting:

- Can it execute commands?
- Can it read/write local files?
- Does it send data to third parties?
- Does it authenticate?
- Can output contain untrusted model/web content?
- Should it run in a container or separate user?

After connecting:

- keep high-risk tools out of allowlist;
- review tool list changes;
- audit config changes.

## C2 and WebShell

C2:

- disabled by default;
- enabled only during authorized window;
- listener ports separated from admin UI;
- `allow_legacy_shell` and `allow_plaintext_checkin` both default to off. Enabling either puts sessions or beacon traffic on the wire in cleartext — hostnames, usernames, internal IPs and dispatched task commands become readable to anyone on the path. Keep them off outside a lab network;
- cleanup payloads, sessions, tasks, and events.

WebShell:

- authorized targets only;
- clear naming;
- write/delete/execute requires approval;
- delete connections after project end.

## At-Rest Secret Encryption

C2 listener `encryption_key` / `implant_token` and WebShell `password` are stored in SQLite encrypted with AES-256-GCM. The master key comes from the `JY_SECMASTER_KEY` environment variable — 32 bytes as 64 hex characters, e.g. `openssl rand -hex 32`.

- set `JY_SECMASTER_KEY` before starting the service; the key is never written to the config file, the database, the repository, or backups;
- back the key up **separately** from the database — a database backup without the key cannot be decrypted, and a key without the database is worthless;
- a fresh install with no stored secrets starts without the key. Once any secret exists, a missing, malformed, or mismatched key makes startup **fail** rather than fall back to plaintext;
- a wrong key does not corrupt data: reads of affected rows error out instead of returning garbage;
- the key never reaches a child process. Every subprocess environment — external MCP, interactive shell, tool execution, C2 payload build — is filtered before launch, so a compromised third-party process cannot decrypt the database. No legitimate child needs it, and an MCP server configured with it explicitly still does not receive it;
- legacy plaintext values are migrated in place at startup and marked with a `v1:` prefix; the migration is idempotent and re-verifies every row it rewrites.

There is no automated key rotation. Changing `JY_SECMASTER_KEY` while encrypted values exist will block startup by design; rotating requires re-encrypting those rows out of band (export with the old key, restart with the new key, re-import).

## Retention

Suggested:

- audit: 30-90 days;
- monitor: 90-180 days;
- uploads: clean after project;
- C2/WebShell outputs: keep only report evidence;
- knowledge base: no real credentials or customer secrets.

## Periodic Review

Weekly:

- failed logins and unusual IPs;
- config changes;
- external MCP changes;
- long-running tools;
- unexpected C2 enablement;
- stale WebShell connections;
- disk and DB size.

Project closeout:

- clean temp workspaces;
- delete unnecessary uploads;
- archive evidence;
- delete stale WebShell/C2 resources;
- export audit records.
