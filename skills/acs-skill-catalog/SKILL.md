---
name: acs-skill-catalog
description: "Index of the community ACS cybersecurity skill library (mukul975, 818 SKILL.md files). JySecAI keeps the catalog for two-phase skill matching; the 818 bodies stay out of skills_dir. Use when matching ACS names during authorized-agent-kali-hunt phase 1, when the user names Anthropic-Cybersecurity-Skills, or when mapping an ACS pentest skill to a local offensive or Strix skill."
license: Apache-2.0
metadata:
  author: mukul975 (community)
  homepage: https://github.com/mukul975/Anthropic-Cybersecurity-Skills
  source: https://mp.weixin.qq.com/s/_s-QWJtWlLnJvtCq9_MXDw
---

# Anthropic-Cybersecurity-Skills catalog (index only)

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills — community skill library, 818 procedures under `skills/<name>/SKILL.md`, `domain: cybersecurity`. This is not an Anthropic Inc. product.

The 小枣信安 article lists it as one Skill source next to Strix, Artex, PentestGPT, and HexStrike. JySecAI already has the overlapping offensive / Strix / OWASP / Claude-Red / SecLists set. Copying all 818 bodies into the default `skills_dir` inflates matching noise and false positives.

## What is installed here

| File | Role |
|---|---|
| `references/all-skill-names.txt` | 818 upstream directory names |
| `references/pentest-catalog.md` | Curated pentest / web / red-team / API subset with local skill mapping |
| This `SKILL.md` | How to use the catalog during a hunt |

## How to use during a hunt

1. In **authorized-agent-kali-hunt** phase 1, match risks to **local** `SKILL.md` first.
2. If a local skill is missing, look up the ACS name in `references/pentest-catalog.md`. Use that name as a *procedure hint* (what to test), then execute with Kali MCP / HexStrike / an existing local skill.
3. Load an ACS body from GitHub only when the user asks for that one skill and it is in-scope. Fetch `skills/<name>/SKILL.md` from the repo; do not rsync the tree.

## Local coverage already in skills_dir

Strix: `penetration-testing-with-strix`, `web-app-penetration-testing`, `api-security-testing`, `owasp-top-10-testing`, `ci-security-scanning-with-strix`, `fix-security-vulnerabilities-with-strix`, `managed-pentesting-with-strix`.

Web/API classes: `offensive-sqli`, `offensive-xss`, `offensive-ssrf`, `offensive-idor`, `offensive-ssti`, `offensive-xxe`, `offensive-jwt`, `offensive-graphql`, `offensive-rce`, `offensive-file-upload`, `offensive-api-security`, `offensive-waf-bypass`.

HexStrike orchestration: **hexstrike-ai**. Two-phase flow: **authorized-agent-kali-hunt**.
