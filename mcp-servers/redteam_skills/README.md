# Claude-Red Skills MCP

Read-only MCP server that exposes the **Claude-Red** red-team methodology skill
library to the JySecAI agent, merged with JySecAI's own local `skills/` library.

It is a *retrieval* server only: it returns skill text (index, trigger phrases,
full `SKILL.md` body). It never executes a command, never downloads a payload,
never touches a target and never spawns a subprocess.

Every row returned by the tools is labelled with its origin:

- `"source": "local"` — from the JySecAI repository `skills/<name>/SKILL.md`
- `"source": "upstream"` — from the upstream Claude-Red project

## Upstream attribution and license

| Item | Value |
|---|---|
| Project | [Claude-Red](https://github.com/SnailSploit/Claude-Red) |
| Author | SnailSploit / Kai Aizen |
| License | MIT |
| Catalog | `claude-skills.json` (78 skills / 23 categories at upstream `v0.3.0`) |
| Layout | `Skills/<category>/<skill-name>/SKILL.md` |

The upstream project is fetched **read-only at runtime** over HTTPS from
`raw.githubusercontent.com` / `api.github.com`; no upstream code is vendored into
this repository. The MIT license of the upstream project applies to the
retrieved methodology text.

## MCP tools (5)

| Tool | Arguments | Returns |
|---|---|---|
| `redteam_list_skill_categories` | – | `{"categories":[{"name","skill_count","sources":["local","upstream"]}], "total":N, "sources":{"local":x,"upstream":y}}` |
| `redteam_list_skills` | `category: str = ""`, `limit: int = 50` | `{"skills":[{"name","description","category","source","triggers":[…],"local_path","upstream_path"}], "total":N, "category":…, "limit":…}` |
| `redteam_get_skill` | `name: str` | `{"ok":true,"skill":{"name","category","source","content","description"}}` or `{"ok":false,"error":"…"}` |
| `redteam_search_skills` | `query: str`, `limit: int = 10` | `{"query":…,"results":[…],"total":N}` |
| `redteam_match_skills` | `text: str`, `limit: int = 10` | `{"text":…,"matches":[{"name","score","reason","source"}],"total":N}` |

Notes:

- `total` is the number of **matching** rows before `limit` is applied.
- `redteam_get_skill` resolves upstream content first (fetched on demand and
  cached); if the upstream fetch fails it falls back to the local
  `skills/<name>/SKILL.md` file; if neither exists it returns a structured
  error — it never raises.
- `redteam_match_skills` mirrors the upstream "skills load on conversation
  trigger" mechanism: it scores trigger phrases, skill-name tokens and
  description tokens against a free-form task/target description and reports
  why each skill matched.

## Register it in JySecAI `config.yaml`

Add the following block under `external_mcp.servers` in `config.yaml`:

```yaml
external_mcp:
  servers:
    redteam-skills:
      type: stdio
      command: python3
      args:
      - mcp-servers/redteam_skills/mcp_redteam_skills.py
      description: 'Claude-Red skills: merged upstream methodology library (MIT) + JySecAI local skills, read-only.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        redteam_list_skill_categories: true
        redteam_list_skills: true
        redteam_get_skill: true
        redteam_search_skills: true
        redteam_match_skills: true
```

The relative `args` path follows the convention of the other external MCP
servers in this repository: it is resolved against the core working directory
(`/opt/jysecai/core/current/` on the deployed host). If your core runs from
another directory, use absolute paths instead:

```yaml
    redteam-skills:
      type: stdio
      command: /opt/jysecai/core/venv/bin/python
      args:
      - /opt/jysecai/core/current/mcp-servers/redteam_skills/mcp_redteam_skills.py
      description: 'Claude-Red skills: merged upstream methodology library (MIT) + JySecAI local skills, read-only.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        redteam_list_skill_categories: true
        redteam_list_skills: true
        redteam_get_skill: true
        redteam_search_skills: true
        redteam_match_skills: true
```

> `config.yaml` is read **once at startup**. After editing it, restart the core
> (`systemctl restart jysec-core`) or the change will not take effect.

The server can also be started manually over stdio:

```bash
python3 mcp_redteam_skills.py          # stdio transport
```

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `JY_TECH_SKILLS_DIR` | *(auto-detected)* | Local skills root. When set and the directory exists it wins; otherwise the server walks up from its own directory looking for a sibling/ancestor `skills/` directory (deployed layout: `/opt/jysecai/core/current/skills/`, this file lives in `/opt/jysecai/core/current/mcp-servers/redteam_skills/`). |
| `REDTEAM_SKILLS_HTTP_TIMEOUT` | `20` | Outbound HTTP timeout in seconds, clamped to 5–60. |

If no local skills root can be found, the local listing is simply empty — the
server still starts and still serves the upstream library.

## Security notes

- **Read-only by construction.** No `subprocess`, no `os.system`, no shell, no
  payload download, no target interaction. The unit test suite asserts that
  none of those appear in the source.
- **Outbound HTTP is restricted** to HTTPS and to the host allowlist
  `{raw.githubusercontent.com, api.github.com}`. Any other host or scheme raises
  internally and is converted into a structured error.
- **Response size caps**: 4 MiB per `SKILL.md`, 8 MiB for the upstream catalog /
  git tree. Oversized responses are rejected.
- **Timeouts** on every request, plus one retry for transient failures.
- **Thread-safe TTL cache** for the upstream catalog (6 h), upstream skill
  bodies (6 h) and the local index (60 s).
- **Input validation**: control characters are rejected, strings are length
  capped, and `limit` is clamped to `1..200`.
- **Traversal-safe local lookup**: the skill name must match
  `^[a-z0-9][a-z0-9._-]*$`; the path is then built and the resolved absolute
  path must still be inside the resolved skills root (symlink escapes included).
- **Tolerant front-matter parsing**: YAML is used when available and a simple
  `key: value` scan is used as a fallback when the YAML block is malformed.

## Offline behaviour

The server never raises out of a tool call. When the upstream GitHub endpoints
are unreachable:

- `redteam_list_skill_categories` / `redteam_list_skills` / `redteam_search_skills`
  / `redteam_match_skills` keep working with the **local** library only.
- `redteam_get_skill` still returns full content for locally present skills.
- `redteam_get_skill` for an upstream-only skill returns
  `{"ok": false, "error": "…"}` instead of an exception.

A failed upstream lookup is cached for a short time (60 s) so the server
recovers as soon as connectivity returns.

## Local category mapping

The JySecAI `skills/` directory is flat (no category folders). Local skills are
mapped into the upstream taxonomy by longest category-name prefix (for example
`active-directory-attack` → category `active-directory`, `web-attack-methods`
→ category `web`), so a category query returns both the upstream and the
local skills for that domain. Local skills that match no upstream category are
grouped under the `jysecai-local` category.

## Tests

The suite runs fully offline — every network call is monkeypatched at module
level:

```bash
wsl.exe -d kali-linux -u root -- /opt/jysecai/core/venv/bin/python \
  -m unittest discover -s /mnt/c/Users/Administrator/Desktop/JySecAI/mcp-servers/redteam_skills -v
```

Coverage: tool registration (exactly five tools), local skill discovery, YAML
front-matter parsing (including the malformed-YAML fallback), keyword search,
trigger matching, path-traversal and symlink-escape rejection, limit clamping,
host/path allowlists, upstream catalog merge, upstream body fetch, and the
network-failure fallback path.
