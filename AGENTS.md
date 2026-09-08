# JySecAI AGENTS.md

## Quick commands
- `go run ./cmd/server --config config.yaml` — Start Go console (port 6688, HTTPS auto-self-signed)
- `cd platform && cp .env.example .env && npm ci && npm run check` — Install + typecheck+test TS control plane
- `docker compose -f compose.jysec.yml up -d --build` — Full reference compose stack (Go + TS + PostgreSQL + Redis + Nginx)
- `docker compose -f compose.jysec.yml up -d --build worker` — Start Strix worker (needs Docker socket)

## Architecture boundaries
- Go core (`cmd/server/main.go`) owns: sessions, conversations, assets, vulnerabilities, blackboard, HITL, RBAC, MCP, C2, workflow orchestration
- TS control plane (`platform/`) owns: Run lifecycle, Scope validation, Redis worker queue, Prometheus metrics, Stripe billing, governance API under `/governance/`
- Gateway (`http://127.0.0.1:8787`): Routes `/` → Go console, `/governance/` → TS, `/assets/*`/`/v1/*` → TS static/API, `/metrics` → TS Prometheus, `/internal/*` → 404 (private callback only)
- Workers pull from Redis queue; C2, Strix, external MCP are optional add-ons

## Critical config files
- `config.yaml` — Main server config (port, TLS, AI channels, HITL rules, proxy pool, tools)
- `platform/.env` / `platform/env.example` — TS env (DB, Redis, JWT, Stripe keys)
- `go.mod` — Go module with many indirect deps; if `go mod download` times out: `go env -w GOPROXY=https://goproxy.cn,direct`
- `config.example.yaml` / `config.yaml` — Human-readable config with defaults; never commit real secrets

## Testing
- `go test ./...` — Go unit tests (CI runs this)
- `cd platform && npm run check` — TS typecheck + Vitest (CI step)
- `cd platform && npm audit --audit-level=high` — Dependency audit (CI step)
- `cd platform && npm run build` — TS build (CI step)
- `node --check web/static/js/*.js` — JS syntax check (CI step; AGENTS legacy path `public/app.js` no longer exists)

## MCP / External servers
- External MCP servers defined in `config.yaml` under `external_mcp.servers.*`
- **Disable semantics**: config load normalizes any server without `disabled: true` to ENABLED (`internal/config/config.go` ~L1569). Use `disabled: true` to keep a server off; enable by removing/flipping it (Web UI "External MCP" page persists `external_mcp_enable`)
- Each has: `type: stdio`, `command` (uses `${VAR}` / `${VAR:-default}` env expansion, e.g. `${JYSECAI_PYTHON:-python}`), `timeout`, `keep_alive`, `max_retries`
- Declared servers (all `disabled: true` by default): `bloodhound` (external, uv) + bundled Python MCP in `mcp-servers/`: reverse-shell, vuln-intel, redteam-knowledge, dragon-v, pent-claude-agent
- Health check every 15s auto-reconnects enabled servers

## Skills marketplace
- 48 skills in `skills/` (26 bundled + 22 imported from SpecterOps/trailofbits); import records in `skills/.marketplace-manifest.json`
- Sync tool: `python scripts/sync-skill-marketplaces.py --preset starter|c2|recon|bloodhound|timeline|code-review|audit` (also `--source`, `--import PATH`, `--dry-run`, `--update`); cache in `scripts/.marketplace-cache/`
- Eino loader scans first-level `*/SKILL.md` only; one invalid first-level SKILL.md fails the whole list
- Docs: `docs/zh-CN/skills-marketplace.md` / `docs/en-US/skills-marketplace.md`

## HITL (Human-in-the-Loop)
- Controlling via `config.yaml` under `hitl.default_mode`: off|approval|review_edit
- `tool_whitelist` list in config governs which tools are auto-approved; others go to audit_agent_prompt
- HITL prompts at `config.yaml` `hitl.audit_agent_prompt` (~L228, approval) and `hitl.audit_agent_prompt_review_edit` (~L279, review_edit)
- Default: `default_mode: off`, `default_reviewer: human`, `default_timeout_seconds: 300`

## Proxy pool
- Configurable via `config.yaml` `proxy_pool` section
- Round-robin or random strategy; health checks `https://api.ipify.org`
- Used for FOFA/ZoomEye/Quake/Shodan outbound API calls
- 10+ pre-configured SOCKS5 proxies listed; set `enabled: false` to disable

## AI channels
- Defined in `config.yaml` under `ai.channels.<id>`: need `api_key`, `base_url`, `model`
- `default_channel` determines new conversation channel
- `vision.enabled: true` + `model` registers `analyze_image` tool
- Reasoning mode: `off` | `on`; `effort` for OpenAI/Claude; `allow_client_reasoning` flag

## Known gotchas
- `workspace_root_dir` in config: never set to `/tmp` or system paths; uses `tmp/workspace` or `projects/{id}`/`conversations/{id}` isolation
- HITL `default_mode: off` in production will be rejected by the app (see `config.yaml` production section)
- MCP auth: if `cfg.MCP.Enabled` and `auth_header_value` is empty, `config.EnsureMCPAuth` generates a random key and writes it back to config
- `go.sum` may diverge; `go mod tidy` will fix, but watch for indirect dep version bumps
- TS `node --check public/app.js` in CI — this is a syntax-only check, not full runtime test

## Entry points an agent should know
- `./jysecai --config config.yaml` (built binary from `cmd/server/main.go`)
- `cd platform && npx tsx src/main.ts` (dev mode, requires Node 24+)
- `cd platform && npx tsx src/worker/main.ts` (worker dev mode)
- MCP servers: `python mcp-servers/<name>/mcp_<name>.py` (each uses its own venv python)