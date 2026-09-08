# Skills Marketplace

JySecAI skills live in `skills/`, one directory per skill with a `SKILL.md` (YAML front matter: `name` / `description` / optional `metadata`) following the [agentskills.io](https://agentskills.io) standard. Multi-agent sessions load them progressively via the built-in `skill` tool (see `multi_agent.eino_skills` in config).

## Current inventory

- **Bundled (26)**: pentest workflow, methodology and output-standard skills (`pentest-blackboard`, `pentest-output-standards`, `web-attack-methods`, `cloud-attack-methods`, `post-exploitation`, `dragon-v-pentest`, ...).
- **Imported from marketplaces (22)**: sources [SpecterOps/skills](https://github.com/SpecterOps/skills) and [trailofbits/skills](https://github.com/trailofbits/skills).
  - Code review: `cwe-code-review`, `openssf-python-review`, `owasp-security-code-review`
  - C2: `cobalt-strike-aggressor-development`, `cobalt-strike-aggressor-reference`, `cobalt-strike-malleable-c2-development`
  - Recon: `nmap-parse`, `osint-recon`, `shodan`
  - BloodHound / directory analysis: `bloodhound-query`, `bloodhound-analysis`, `bloodhound-ad-analysis`, `bloodhound-opengraph`, `azurehound-analysis`, `openhound-development`, `openhound-github`, `openhound-jamf`, `openhound-okta`
  - Reporting timeline: `timeline-consolidator`, `timeline-workflow`
  - TrailOfBits: `burpsuite-project-parser`, `yara-rule-authoring`

Import records (source repo, commit, MCP deps) are kept in `skills/.marketplace-manifest.json`.

## Sync tool

```bash
# Preset import (specterops: starter / c2 / recon / bloodhound / timeline / code-review; trailofbits: audit)
python scripts/sync-skill-marketplaces.py --preset starter

# Full pull from one source
python scripts/sync-skill-marketplaces.py --source specterops

# Import from local paths
python scripts/sync-skill-marketplaces.py --import path/to/skill_dir

# Options
#   --dry-run      print what would be imported, write nothing
#   --update       force re-clone/pull of the marketplace repo
#   --skills-dir   target directory (default skills/)
#   --cache-dir    clone cache (default scripts/.marketplace-cache/, gitignored)
```

On import the tool normalizes directory name == front matter `name`, injects `metadata.marketplace` / `metadata.source` provenance fields, and updates the manifest.

## MCP-dependent skills (important)

Some marketplace skills need an external MCP server for full capability; see `deps_mcp` in the manifest:

| MCP | Declaration (config.yaml) | Skills |
|---|---|---|
| `bloodhound` | `external_mcp.servers.bloodhound` | bloodhound-query / bloodhound-analysis / bloodhound-ad-analysis / azurehound-analysis, ... |
| `dragon-v` | `external_mcp.servers.dragon-v` | dragon-v-pentest (plus the agents/dragon-v.md sub-agent) |
| `vuln-intel` | `external_mcp.servers.vuln-intel` | online CVE/KEV cross-checks |

### Enable semantics (read this)

On config load a normalization runs: **any external MCP server without `disabled: true` is force-enabled** (see `internal/config/config.go`). Therefore:

- Disabled = `disabled: true` (the official MCP field)
- Enabled = remove `disabled` or set it to `false` (or manage via the Web UI "External MCP" page, which persists `external_mcp_enable`)

The main config declares 6 servers (`bloodhound` plus the 5 bundled Python MCP servers: `reverse-shell`, `vuln-intel`, `redteam-knowledge`, `dragon-v`, `pent-claude-agent`), **all disabled by default**. Python MCP sources live in `mcp-servers/<name>/`; commands support `${VAR}` / `${VAR:-default}` env expansion (e.g. `${JYSECAI_PYTHON:-python}`).

## Loading rules & supply-chain notes

- The Eino skill loader only scans **first-level** subdirectories of `skills_dir` (`*/SKILL.md`); a single invalid first-level SKILL.md fails the whole skill list.
- `skills/.marketplace-manifest.json` and `skills/.eino/` (plantask runtime) do not affect loading.
- Review SKILL.md content and referenced scripts before importing; use `python scripts/sync-skill-marketplaces.py --dry-run --update` to diff upstream changes before upgrading.
- Skill bodies are prompts: marketplace wording (including authorization assumptions) enters conversation context — review before production use.
