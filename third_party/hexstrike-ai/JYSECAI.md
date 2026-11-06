# HexStrike AI on JySecAI

Vendored from https://github.com/0x4m4/hexstrike-ai (master, HexStrike AI MCP Agents v6.0, MIT).

Live scanner uses the Kali apt package `hexstrike-ai` (`0.0~git20260306.8333779-0kali1`), which is the same v6.0 tree. `hexstrike_mcp.py` matches this vendor copy byte-for-byte. `hexstrike_server.py` differs by one line: GitHub hardcodes `app.run(host="0.0.0.0")`; apt uses `API_HOST` so JySecAI can bind loopback.

## Live process (do not replace with this tree)

- Unit: `jysec-hexstrike.service`
- ExecStart: `/usr/bin/python3 /usr/share/hexstrike-ai/hexstrike_server.py --port 8888`
- WorkingDirectory: `/var/lib/jysecai/hexstrike` (writable; ProtectSystem=full)
- Bind: `HEXSTRIKE_HOST=127.0.0.1` `:8888`
- MCP stdio: `/usr/bin/python3 /usr/share/hexstrike-ai/hexstrike_mcp.py --server http://127.0.0.1:8888`
- Python: system `/usr/bin/python3` + `PYTHONPATH=/usr/lib/python3/dist-packages` (FastMCP). Do not run the MCP client from the core venv.
- `alwaysAllow` stays empty.

This vendor tree is the GitHub source of truth for docs, skill text, and diffing. Switching ExecStart here would listen on `0.0.0.0`.
