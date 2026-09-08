---
name: redteam-technique-routing
description: >-
  Map authorized red-team objectives, behaviors, platforms, and living-off-the-land
  binaries to MITRE ATT&CK, LOLBAS, GTFOBins, and Atomic Red Team evidence. Use for
  technique selection, TTP mapping, emulation planning, detection validation, and
  ATT&CK technique questions; use vulnerability intelligence for CVE/POC lookup.
metadata:
  tags: [red-team, mitre-attack, lolbas, gtfobins, atomic-red-team]
---

## Evidence routing

Use the `redteam-knowledge` MCP to ground technique selection:

- Search behavior, tactic, or platform with `redteam_search_attack`, then fetch the selected ID with `redteam_get_attack`.
- Use `redteam_search_lolbas` for Windows signed binaries and `redteam_search_gtfobins` for Unix-like executables.
- Use `redteam_get_atomic_tests` for control-validation test metadata. Keep commands excluded until the user needs implementation detail for an authorized, isolated environment.
- Use `vuln-intel` instead when the primary question is a CVE, affected version, POC/EXP, KEV, EPSS, OSV, or emerging vulnerability.

## Selection rules

- Match the target platform, permissions, tactic, and observable outcome; a keyword match alone is a lead.
- Prefer ATT&CK mitigations and detection strategies when the goal is defensive validation.
- Treat LOLBAS and GTFOBins entries as misconfiguration-dependent techniques, not proof of compromise or exploitability.
- Atomic tests are simulations, not vulnerability checks. Review prerequisites, input arguments, elevation, side effects, and cleanup before execution.

## Execution handoff

The knowledge MCP is read-only. After the technique and evidence are selected, use only the execution MCP needed for the authorized target. Record the chosen ATT&CK ID, source URL, assumptions, exact action, cleanup, and observed result. Do not execute examples merely because a knowledge lookup returned them.
