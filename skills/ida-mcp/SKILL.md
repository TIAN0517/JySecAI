---
name: ida-mcp
description: "Drive IDA Professional 9.5 through the official Hex-Rays IDA MCP (ida-mcp) from Grok. Use when reversing ELF/PE/Mach-O/firmware, opening an IDB, decompiling, disassembling, renaming, typing, xrefing, or patching in IDA."
---

# IDA MCP (Hex-Rays official, wired for Grok)

IDA Pro 9.5 is installed on Windows. Grok talks to it through **official Hex-Rays `ida-mcp` stdio**, not the community `mrexodia/ida-pro-mcp` HTTP plugin.

## Runtime

- IDA: `C:\Program Files\IDA Professional 9.5`
- GUI plugin: `%AppData%\Hex-Rays\IDA Pro\plugins\ida-mcp` (restart IDA after first install)
- IDA Python venv: `%AppData%\Hex-Rays\IDA Pro\venv` via `IDAPYTHON_VENV_EXECUTABLE`
- Grok MCP: `cmd.exe /c uvx --exclude-newer=1s ida-mcp stdio --agent=grok`
- Handshake: protocol `2025-11-25`, 6 tools

Headless analysis uses **idalib** and does not require the GUI. The GUI plugin is for attaching to an already-open IDB.

Pass **Windows paths** (`C:\...`) into MCP tools. WSL `/mnt/c/...` is not an IDA path.

## Tool sequence

1. `list_databases` — see GUI + headless workers already open.
2. `open_database` — `path` to the binary or `.i64`/`.idb`. `set_current=true`. `gui=true` only when the operator asked for the IDA GUI.
3. `reference` — look up ida-domain API **before** guessing (`"decompile function"`, `"xrefs to address"`, `"list strings"`, `"rename local variable"`).
4. `execute_python` — run IDAPython / ida-domain against the open DB. `db` is the current Database; `ida_domain` is imported. Definitions persist on this agent's lease. Prefer `reference` then a short `run(db)` / trailing expression.
5. `save_database` then `close_database` when the analysis is done.

Do not convert number bases by hand in prompts; compute in `execute_python`.

## execute_python shape

```python
# after reference("decompile function")
def run(db):
    f = db.functions.get_at(0x401000)  # use real API from reference()
    return {"name": str(f), "addr": hex(int(f.start_ea))}
```

Or a trailing expression. Timeouts default to 360s and do not include first auto-analysis.

## OPSEC / operator notes

- Scope is authorized reversing only.
- First `open_database` on a large binary blocks on auto-analysis.
- Multiple DBs: pass `instance_id` from `list_databases` / `open_database`.
- If stdio MCP is down, start IDA GUI (plugin loads) or rerun `grok mcp doctor`.
- HTTP fallback (only if operator starts it): `uvx ida-mcp http --host 127.0.0.1 --port 8737`
