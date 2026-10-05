# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

JySecAI is a single-service AI-native security operations platform in Go (module `jysecai`): a Gin HTTP server, static SPA frontend, SQLite persistence, Eino-based agent orchestration, MCP tooling, and optional high-risk C2 (`internal/c2`) and WebShell subsystems. It is strictly for authorized security operations — many subsystems execute commands by design.

Deeper docs: `docs/en-US/architecture.md`, `docs/en-US/developer-guide.md`, `docs/en-US/testing.md`.

## Commands

```bash
# Run dev server (frontend is static — JS/CSS/template changes only need a browser refresh)
go run ./cmd/server --config config.yaml          # add --https to match run.sh defaults

# Build (CGO is required: mattn/go-sqlite3; production Linux binary uses CGO_ENABLED=1)
go build -o jysecai ./cmd/server

# Vet + tests (CI deliberately runs the WHOLE tree, not one package)
go vet ./...
go test ./...
go test -race ./internal/handler/... ./internal/app/... ./internal/mcp/...

# Single package / single test
go test ./internal/handler
go test ./internal/c2 -run TestValidateBeaconHost -v
```

- If module downloads time out: `go env -w GOPROXY=https://goproxy.cn,direct` (see go.mod).
- CI (`.github/workflows/linux-build.yml`): govet → build → full test → race → gosec/govulncheck/staticcheck (report-only) → **authorization-boundaries job (blocking)**.
- After touching security-sensitive code (RBAC, WebShell, C2 templates, MCP config masking, CSV export, outbound URL/IP validation), run the `authorization-boundaries` job's `go test -run '...'` expression locally — that job, not gosec, is what blocks merges. gosec reports are noisy on C2/WebShell code by design.
- Pre-commit hooks (`.githooks/`, `.pre-commit-config.yaml`) block secret-looking filenames/content and check TLS-verify settings (`harden.py`). Never bypass with `--no-verify`; fix the finding instead.

## Architecture

Big picture (`docs/en-US/architecture.md` has the mermaid diagram):

- **Entry & wiring**: `cmd/server/main.go` → `internal/app.New()` (`internal/app/app.go`) constructs everything and `setupRoutes` wires Gin routes. This file is the map of the whole service.
- **Agent chat path** (`/api/eino-agent/stream`): auth middleware → `internal/handler/agent.go` → Eino runner (`internal/multiagent/`) → tool calls via MCP (`internal/mcp/`, `internal/einomcp/`) → **HITL approval gate sits before tool execution** (`internal/hitl/`) → shell/command execution boundary (`internal/security/`) → results persisted to SQLite → SSE stream to browser. A failure can live in any of these layers.
- **Config hot-apply**: `internal/handler/config.go` applies config changes at runtime across model, KB, C2, robot, and MCP — no restart. Changes there need regression tests across all apply paths.
- **Tools** come in two flavors: declarative YAML command tools in `tools/*.yaml` (~97, preferred for new tools) and built-in Go tools registered in `internal/app/` (e.g., `registerWebshellTools`) when internal state or structured integration is needed.
- **Multi-agent** prompts/orchestration live in `agents/*.md` (orchestrator, plan-execute, supervisor modes) executed by `internal/multiagent/` (streaming, retry, summarization, middleware).
- **C2** (`internal/c2/`): TCP/HTTP/WebSocket listeners, encrypted beacon templates (embedded via `payload_templates/`), HITL context, result security. High test coverage — keep it that way.
- **Database** (`internal/database/`): SQLite with WAL; schema migrations must stay backward-compatible with old data files.
- `internal/handler/` is very large (~50k lines; `openapi.go` alone is 6.4k and serves `/api/openapi/spec`).

### Adding a business module

Per `docs/en-US/developer-guide.md`, a module is not "just a handler". The project's own checklist: data model + SQLite migration, handler, audit logging, monitor state for long-running work, MCP exposure decision, HITL boundary for risky tools, OpenAPI spec update, frontend (incl. i18n), tests, docs. Missing one usually becomes a later usability or safety bug.

### Long-running work convention

Anything slow (scan, indexing, batch, C2, external call) must answer: cancellable? progress queryable? retryable? where are results stored? does state survive refresh? does it block the HTTP request? If not solvable inline, use task tables, event streams, or monitor state — never block the HTTP request.

## Conventions

- **Bilingual everything**: docs exist as `docs/en-US/` + `docs/zh-CN/` pairs (README.md + README_CN.md too) — update both sides. Frontend i18n: `web/static/i18n/zh-CN.json` + `en-US.json` must be updated together; never hardcode new visible UI text.
- **Error responses**: stable JSON `{"error": "machine_readable_code", "message": "human-readable explanation"}`.
- Code comments are commonly written in Chinese (mixed simplified/traditional); match the surrounding style.
- Tool roles are named YAML files in `roles/` (Chinese filenames); skills in `skills/` follow the standard Agent Skill layout.

## Repo safety notes

- `.gitignore` intentionally excludes `config.yaml`, `data/`, `*.db`, and evidence/archive dirs — the working tree contains real credentials and pentest artifacts. Never `git add -f` these, and don't "clean up" untracked root artifacts (evidence/, fofa_*.py, etc.) — they are active working files.
- Remotes: `origin` = TIAN0517/JySecAI (push target); `lstjks` = JyscanAiI (backup branches); `boss` = bossjyaisce. Pushes to `origin` use the `vast_ed25519` key via `core.sshCommand` (already configured).
- `go.mod` says `go 1.25.0`; CI uses Go 1.27.x. Either works locally.
