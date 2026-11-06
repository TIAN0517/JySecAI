# IDA MCP Reverse-Engineering Integration

This setup uses the official Hex-Rays `ida-mcp`, exposed by a Streamable HTTP service bound to the local loopback interface only, shared between JySecAI and Hermes. Sharing one service avoids launching duplicate workers and lets both clients see the same set of IDA database instances.

## Prerequisites

- Python 3.11 or later, Git, and `uv`.
- IDA Home or Pro 9.4+, with a valid license and IDAlib.
- IDA Free has no IDAPython/IDAlib and cannot serve as the analysis backend for the official IDA MCP.

Official references:

- [Hex-Rays IDA MCP](https://github.com/HexRaysSA/ida-mcp)
- [IDA MCP documentation](https://docs.hex-rays.com/core/mcp)
- [IDA Domain / IDAlib initialization](https://ida-domain.docs.hex-rays.com/getting_started/)
- [Hermes MCP configuration](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md)

## Installing and starting the shared service

To keep the setup reproducible, pin the verified version:

```bash
uv tool install --python 3.11 'ida-mcp==20260930.0.1'
```

If the IDA installer has not initialized IDAlib yet, run the activation script from the installation directory:

```bash
python3 /path/to/ida/idalib/python/py-activate-idalib.py
```

Install and start the user systemd service:

```bash
install -D -m 0644 deploy/systemd/user/jysec-ida-mcp.service \
  "$HOME/.config/systemd/user/jysec-ida-mcp.service"
systemctl --user daemon-reload
systemctl --user enable --now jysec-ida-mcp.service
systemctl --user status jysec-ida-mcp.service --no-pager
```

The service listens on `127.0.0.1:8737` only; never expose it directly to the public internet. For cross-host use, put TLS, authentication, and source restrictions in front of it.

To attach the service to databases already open in the IDA GUI, install the official GUI plugin:

```bash
uvx ida-hcli plugin install ida-mcp@https://github.com/HexRaysSA/ida-mcp
```

## Connecting Hermes

Add the following to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  ida:
    url: http://127.0.0.1:8737/mcp
    timeout: 120
    enabled: true
```

Verify:

```bash
hermes mcp test ida
```

You should discover six tools: `open_database`, `execute_python`, `reference`, `list_databases`, `save_database`, and `close_database`.

## Connecting JySecAI

Paste the following JSON into "Settings → MCP Management → Add External MCP":

```json
{
  "ida-official": {
    "type": "http",
    "url": "http://127.0.0.1:8737/mcp",
    "description": "Official Hex-Rays IDA MCP shared with Hermes",
    "timeout": 120,
    "keep_alive": 30,
    "max_retries": 5,
    "tool_enabled": {
      "open_database": true,
      "execute_python": true,
      "reference": true,
      "list_databases": true,
      "save_database": true,
      "close_database": true
    }
  }
}
```

After saving, confirm the status shows "connected" and the tool count is 6. Roles that use these tools need the `mcp:external:execute` permission with Scope `all`.

Alternatively, write directly into the `external_mcp.servers` section of `config.yaml`; see the root-level `config.example.yaml` for the full YAML.

## Security boundaries

`execute_python` is not just a query interface — it can also rename, comment, apply types, and patch bytes. In production:

- Grant `mcp:external:execute` only to explicitly authorized roles.
- Use JySecAI Tool Guard/HITL to require human confirmation for write-type calls to `ida-official::execute_python`.
- Analyze only authorized samples, and keep samples and their `.i64` databases inside controlled working directories.
- Retain JySecAI audit logs; never configure unconditional auto-approval for the official tools.

## Verification and troubleshooting

First verify transport and tool discovery:

```bash
systemctl --user is-active jysec-ida-mcp.service
ss -ltnp | grep '127.0.0.1:8737'
hermes mcp test ida
go run ./cmd/test-external-mcp /path/to/config.yaml
```

If `open_database` returns `cannot load IDA library`:

1. Confirm the installation is IDA 9.4+ with IDAlib, not IDA Free.
2. Run `py-activate-idalib.py`, or set the correct `IDADIR` for the service.
3. Restart the service: `systemctl --user restart jysec-ida-mcp.service`.
4. Check the logs: `journalctl --user -u jysec-ida-mcp.service -n 100 --no-pager`.

## Rollback

```bash
systemctl --user disable --now jysec-ida-mcp.service
rm "$HOME/.config/systemd/user/jysec-ida-mcp.service"
systemctl --user daemon-reload
```

Then remove the corresponding entries from Hermes and the JySecAI MCP management UI; this does not delete IDA databases or samples.
