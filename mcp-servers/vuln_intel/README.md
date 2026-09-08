# Vuln Intel MCP

Read-only vulnerability intelligence for JySecAI. It correlates NIST NVD,
CISA KEV, FIRST EPSS, OSV.dev, local ExploitDB/SearchSploit, and explicitly
unverified GitHub public PoC candidates.

The server does not download or execute PoC code. Outbound HTTP hosts are
allowlisted in code.

## Tools

- `vuln_triage_cve`
- `vuln_search_cves`
- `vuln_search_public_pocs`
- `vuln_emerging_threat_watch`
- `vuln_query_package`
- `vuln_get_advisory`
- `vuln_intel_source_health`

Optional environment variables:

- `NVD_API_KEY`: raises the NVD request allowance.
- `GITHUB_TOKEN`: raises GitHub API limits. Use a read-only fine-grained token.
- `VULN_INTEL_HTTP_TIMEOUT`: 5–60 seconds; default 20.

Run with a Python environment containing MCP SDK 1.x:

```bash
python mcp_vuln_intel.py
```
