---
name: authorized-agent-kali-hunt
description: "Two-phase authorized vuln hunt on JySecAI using local skills plus Kali MCP plus HexStrike. Phase 1 is recon and threat modeling only. Phase 2 loads matching skills and probes without exploit. Use when the user asks to hunt vulns with Agent/Skill/Kali, run a two-phase pentest, threat-model then test, or follow the Xiaozao Agent+Skill+Kali workflow."
license: MIT
metadata:
  author: JySecAI (workflow from Xiaozao)
  source: https://mp.weixin.qq.com/s/_s-QWJtWlLnJvtCq9_MXDw
---

# Agent + Skill + Kali two-phase hunt

JySecAI already has the console the article describes:

- Skills in `skills_dir` (`offensive-*`, Strix, OWASP, SecLists, Claude-Red, this skill)
- Kali tools MCP `kali-mcp` → `http://127.0.0.1:5000` (local stdio, not SSH to a lab VM)
- HexStrike MCP `hexstrike-ai` → `http://127.0.0.1:8888` (decision layer, 150+ tools)
- Catalog hints: **acs-skill-catalog** (818-name index, pentest subset only)

Do not reinstall `mcp-kali-server`. Do not open HexStrike on `0.0.0.0`. Do not copy all 818 ACS bodies into `skills_dir`.

## Before anything

1. Named target, written authorization (or bug-bounty / owned lab).
2. Environment (staging preferred), out-of-scope paths, test accounts.
3. Both health endpoints 200: Kali `:5000/health`, HexStrike `:8888/health`.

Stop if any of those is missing.

## Why two phases

A single "go pentest this URL" prompt misses skill matching, drops coverage, burns tokens on raw HTML/logs, and can overstep into exploit. Split the work.

Copy the phase prompts from `references/phase1-prompt.md` and `references/phase2-prompt.md`. Fill in the actual target, RoE, and account notes at the top. Run phase 1 to completion and **stop**. Start phase 2 only with the phase-1 JSON.

## Phase 1 — recon + threat model (no vuln testing)

Collect stack, services, pages, APIs, auth, roles, data flows. For each function list plausible vuln classes from **features**, not from the name alone. Match candidate skills. Output the six artifacts in the phase-1 prompt, including a compact JSON handoff with stable IDs.

Tools allowed: passive/light recon only (`httpx_probe`, `katana_crawl`, `subfinder_scan`, `tools_httpx`, `tools_subfinder`, fetch of in-scope URLs). No sqlmap, hydra, nuclei-full, exploit, or brute.

## Phase 2 — skill-based probe (no exploit)

Read the phase-1 JSON. For each interface × vuln class, pick **one** matching skill, read its `SKILL.md`, then probe with the method it defines. Prefer local skills over ACS names:

| Risk class | Load |
|---|---|
| SQLi | `offensive-sqli` |
| XSS | `offensive-xss` |
| SSRF | `offensive-ssrf` |
| IDOR / BAC | `offensive-idor`, `testing-for-broken-access-control` (ACS name → local `offensive-idor`) |
| SSTI | `offensive-ssti` |
| XXE | `offensive-xxe` |
| JWT | `offensive-jwt` |
| GraphQL | `offensive-graphql` |
| Upload | `offensive-file-upload` |
| RCE (probe only) | `offensive-rce` |
| Web app end-to-end | `web-app-penetration-testing` / `owasp-top-10-testing` |
| API | `api-security-testing` / `offensive-api-security` |

HexStrike: `select_optimal_tools_ai` then the short list it returns. Kali MCP: named tools (`tools_nmap`, `tools_nikto`, `tools_gobuster`, `tools_sqlmap` only when phase 1 already flagged SQLi).

A tool error, a 500, or a single nuclei hit is **not** a finding. Need a replayable request/response (or equivalent) plus a second check.

## Token and trace rules

- Summarize tool output; keep raw bodies behind evidence IDs.
- Per-interface test log: ID, URL, method, vuln classes, skill used, status (`untested|running|done|suspected|blocked|skipped`), evidence IDs, skip reason.
- End of phase 2: diff the log against the phase-1 interface list. Untested ≠ safe.

## Out of default scope

Exploit, persistence, credential spraying, reverse shells, Metasploit sessions, data exfil. Those need an explicit extra authorization step after phase 2.
