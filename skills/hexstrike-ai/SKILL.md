---
name: hexstrike-ai
description: "Drive HexStrike AI v6.0 (150+ Kali tools, 12+ agents, IntelligentDecisionEngine) through the already-connected JySecAI MCP hexstrike-ai on loopback port 8888. Use when the user asks for HexStrike, hexstrike-ai, AI-orchestrated nmap/nuclei/sqlmap/gobuster/ffuf, bug-bounty workflow, CVE intel, or an MCP tool-selection layer on Kali."
license: MIT
metadata:
  author: 0x4m4 / OTT Cybersecurity LLC (upstream); JySecAI wiring
  homepage: https://github.com/0x4m4/hexstrike-ai
  source: https://mp.weixin.qq.com/s/p099ln4b7oc3m3CGBo5ySg
---

# HexStrike AI v6.0 on JySecAI

HexStrike is the decision layer over Kali tools. The scanner already runs it as a background unit and an MCP client. Do not spawn a second server, a venv MCP, or `alwaysAllow`.

## Live wiring (already installed)

| Piece | Value |
|---|---|
| API | `jysec-hexstrike.service` → `http://127.0.0.1:8888/health` |
| MCP | `hexstrike-ai` stdio → `/usr/bin/python3 /usr/share/hexstrike-ai/hexstrike_mcp.py --server http://127.0.0.1:8888` |
| Version | 6.0.0 (Kali apt = GitHub master; MCP file identical) |
| Tools registered | 151 MCP tools; health reports how many binaries are actually on PATH |
| GitHub vendor | `third_party/hexstrike-ai/` |

Health check before a hunt: MCP `server_health`, or HTTP `GET http://127.0.0.1:8888/health`. Need `status=healthy` and `all_essential_tools_available=true`.

## Authorization

Written authorization, bug-bounty scope, CTF, or owned lab. Stop if the target is outside that scope.

## How to run it (low false-positive)

1. Confirm the target and RoE. Stay in phase 1 of **authorized-agent-kali-hunt** until a threat model exists.
2. Ask HexStrike to **choose** tools, then run that short list:
   - `analyze_target_intelligence`
   - `select_optimal_tools_ai`
   - `optimize_tool_parameters_ai`
   - `intelligent_smart_scan` or `ai_reconnaissance_workflow` / `bugbounty_reconnaissance_workflow`
3. Treat scanner output as **candidates**. Confirm with a second independent signal (second tool, replayed request, or page evidence). `VulnerabilityCorrelator` / `discover_attack_chains` / `ai_vulnerability_assessment` may group findings; grouping is not confirmation.
4. For web apps prefer: `httpx_probe`, `katana_crawl`, `nuclei_scan` (scoped templates), `arjun_parameter_discovery`, then one targeted `sqlmap_scan` / `dalfox_xss_scan` / `graphql_scanner` per suspected class. Skip the rest.
5. Summarize. Keep raw logs behind evidence IDs.

## Decision-layer agents (from upstream)

Use these names when explaining a plan; they live inside `hexstrike_server.py`:

- IntelligentDecisionEngine — tool pick + parameter tweak
- BugBountyWorkflowManager / CTFWorkflowManager
- CVEIntelligenceManager / monitor_cve_feeds
- AIExploitGenerator — payload **drafts** only in this skill; do not fire exploits
- VulnerabilityCorrelator / discover_attack_chains

## Do not fire unless the user asked for a destructive authorized phase

`execute_command`, `metasploit_run`, `hydra_attack`, `responder_credential_harvest`, `msfvenom_generate`, `generate_exploit_from_cve`, `ai_generate_attack_suite`, `pwntools_exploit`. Default hunt stops at probe + non-destructive validation.

## Process / cache

Long scans: `get_process_status`, `list_active_processes`, `get_live_dashboard`. Do not stack overlapping `nuclei_scan` + `intelligent_smart_scan` on the same host.

## Sibling skills

- Two-phase hunt: **authorized-agent-kali-hunt**
- Kali MCP tools API: `kali-mcp` (`http://127.0.0.1:5000/health`)
- Skill catalog matching: **acs-skill-catalog**, plus local `offensive-*` / Strix / OWASP skills
