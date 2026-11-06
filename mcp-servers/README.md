# MCP Servers

[中文](README_CN.md)

This directory contains **standalone MCP (Model Context Protocol) servers**. They speak the standard MCP protocol over stdio (or HTTP/SSE when a server supports it), so **any MCP client** can use them—not only JySecAI, but also **Cursor**, **VS Code** (with an MCP extension), **Claude Code**, and other clients that support MCP.

**We will keep adding useful MCP servers here.** New servers will cover security testing, automation, and integration scenarios. Stay tuned for updates.

## Available servers

| Server | Description |
|--------|-------------|
| [reverse_shell](reverse_shell/) | Reverse shell listener: start/stop listener, send commands to connected targets, full interactive workflow. |
| [redteam_skills](redteam_skills/) | Offensive methodology library: merges the upstream Claude-Red skills (MIT, 78 skills / 23 categories) with the local `skills/` library (131 skills) and matches them by trigger phrase. **Read-only — it never touches a target.** |
| [kali_gpt](kali_gpt/) | Kali GPT-style pentest reasoning: tool→ATT&CK mapping, finding-driven tool-chain suggestions, PTES phase plans, engagement memory. **Planning only — it never executes**; any real action still goes through JySecAI's HITL gate and the scope registry. |

## How to use

These MCPs are configured per client. Use **absolute paths** for `command` and `args` when using stdio.

### JySecAI

1. Open Web UI → **Settings** → **External MCP**.
2. Add a new external MCP and fill in the JSON config (see each server’s README for the exact config).
3. Save and click **Start**; the tools will appear in conversations.

### Cursor

Add the server to Cursor’s MCP config (e.g. **Settings → Tools & MCP → Add Custom MCP**, or edit `~/.cursor/mcp.json` / project `.cursor/mcp.json`). Example for a stdio server:

```json
{
  "mcpServers": {
    "reverse-shell": {
      "command": "/absolute/path/to/venv/bin/python3",
      "args": ["/absolute/path/to/JySecAI-main/mcp-servers/reverse_shell/mcp_reverse_shell.py"]
    }
  }
}
```

Replace the paths with your actual paths. Cursor will spawn the process and talk MCP over stdio.

### VS Code (MCP extension) / Claude Code / other clients

Configure the client to run the server via **stdio**: set the **command** to your Python executable and **args** to the script path (see each server’s README). The client will launch the process and communicate over stdin/stdout. Refer to your client’s docs for where to put the config (e.g. `.mcp.json`, `~/.claude.json`, or the extension’s settings).

## Requirements

- Python 3.10+ for Python-based servers.
- Use the project’s `venv` when possible: e.g. `venv/bin/python3` and the script under `mcp-servers/`.
