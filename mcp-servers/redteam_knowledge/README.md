# Red-team Knowledge MCP

Read-only correlation for authoritative MITRE ATT&CK, LOLBAS, GTFOBins, and
Atomic Red Team data. It exposes six MCP tools and never executes commands or
downloads payloads. Command/test examples are omitted unless explicitly
requested through an opt-in argument.

Run over stdio with Python 3.10+, `mcp`, and `PyYAML` installed:

```bash
python mcp_redteam_knowledge.py
```
