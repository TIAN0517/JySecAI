---
name: opentrap
description: "Drive OpenTRAP, the open-source Burp-style intercepting proxy and web-app security suite built on OWASP ZAP. Use when the user wants OpenTRAP, a Burp alternative, intercepting proxy, HTTP repeater, Intruder, Collaborator, Decoder, site map, crawl-and-audit, or ZAP-backed DAST against an in-scope target. Use when the user asks to /opentrap."
---

# OpenTRAP

Linux AppImage. GUI suite. Detection is OWASP ZAP; the workspace is proxy-first.

Binary: `$HOME/.local/bin/opentrap` → `$HOME/.local/opt/opentrap/opentrap-x86_64.appimage` (release `20261031-175205`).

Default proxy listener: `127.0.0.1:8080`. Override with `-Dopentrap.port=<port>`. Confirm in **Settings → Proxy / Listeners**.

## Launch

```bash
# GUI (needs a display / WSLg)
opentrap

# explicit AppImage
"$HOME/.local/opt/opentrap/opentrap-x86_64.appimage"
```

If the binary is missing, re-fetch:

```bash
mkdir -p "$HOME/.local/opt/opentrap"
curl --http1.1 -fL -o "$HOME/.local/opt/opentrap/opentrap-x86_64.appimage" \
  https://github.com/opentrap/opentrap/releases/latest/download/opentrap-x86_64.appimage
chmod +x "$HOME/.local/opt/opentrap/opentrap-x86_64.appimage"
ln -sfn "$HOME/.local/opt/opentrap/opentrap-x86_64.appimage" "$HOME/.local/bin/opentrap"
```

OpenTRAP ships no MCP server and no CLI scan API. Drive it through the GUI (and the built-in browser). Do not invent REST/MCP endpoints.

## Operator workflow

1. Confirm the target is in authorized scope.
2. Launch OpenTRAP. Create or open a project at the splash screen.
3. **Proxy** tab → **open browser**. Bundled Chromium is already proxied and trusts the OpenTRAP CA. TLS intercept works with no extra install.
4. Point that browser at the in-scope app. Traffic lands in HTTP history, site map, and Logger.
5. Add the host/path to **scope** from the site map. Accept the prompt to stop recording out-of-scope traffic.
6. Start a scan from the Dashboard wizard:
   - **Crawl** — map only
   - **Crawl and audit** — map + ZAP active/passive checks
   - **API-only** — API surface
   - Tier: Lightweight / Fast / Balanced / Deep, or Custom
7. Triage issues on **Target**: advisory, evidence, request, response.
8. Right-click a request → send to **Repeater** (manual replay/tamper), **Intruder** (fuzz: sniper / battering ram / pitchfork / cluster bomb), **Decoder**, **Comparer**, **Organizer**.
9. For blind SSRF/XXE/OAST, use **Collaborator** and plant its payload in the request under test.

Scan configs live in Settings (gear). Passive audit also runs on in-scope proxy traffic while you browse.

## What each tab is for

| Tab | Use |
|---|---|
| Dashboard | Live tasks, issue counts, scan wizard |
| Target | Site map, scope, issues + advisories |
| Proxy | Intercept, history, match/replace, open browser |
| Scanner | Enable/disable ZAP active/passive rules |
| Logger | Every request OpenTRAP or the engine sent |
| Intruder | Payload attacks |
| Repeater | Single-request edit/replay |
| Collaborator | Out-of-band DNS/HTTP callbacks |
| Organizer | Stash interesting requests |
| Sequencer | Token entropy |
| Decoder / Comparer | Encode/decode/hash and diffs |

## Reporting back

After a scan or a proxy session, report:

- target and scope rules
- scan type + tier
- issue count by severity, with the request that proved each finding
- proxy listen address actually used
- whether the built-in browser or an external client was used

## Limits

- Linux AppImage only. On Windows Grok, run it inside WSL.
- GUI application. No packaged MCP, no `SKILL.md` upstream, no headless scan CLI in this release.
- Roadmap items that are laid out but unimplemented open a dialog with a code such as `OT-…`. Do not claim those features work.
- Do not send OpenTRAP traffic to a third-party model. The project ships no AI features on purpose.
