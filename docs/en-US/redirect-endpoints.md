# Controlled Redirect Endpoints

[中文](../zh-CN/redirect-endpoints.md)

Findings about open redirects are usually stored with the attacker's own domain baked into the reproduction steps and evidence — `https://evil.example.com/steal`, `?redirect=https://evil.com`. Re-testing that way sends the callback to someone else's server, so the result cannot be attributed and cannot be turned into evidence.

`redirect` turns the callback target into a platform-level setting: configure your own endpoints once, and every stored payload can be swapped for them.

## Configuration

```yaml
redirect:
  enabled: true
  urls:
    - https://97y.me/tjneJ
    - https://97y.me/tjneK
```

| Field | Meaning |
| --- | --- |
| `enabled` | Master switch for the endpoint list. |
| `urls` | The controlled callback endpoints. Each one is used as the redirect payload. |

Rules:

- Entries without an `http`/`https` scheme are dropped, blanks are ignored, and duplicates are removed while preserving the order you wrote.
- The list is active when `enabled` is `true` **or** `urls` is non-empty. That single rule decides whether the tool exists, both at startup and after a config hot-apply.
- With the list empty and `enabled` off, `redirect_probe` is not registered at all, so the agent never sees a tool with nothing to probe with.

`PUT /api/config` accepts the same section and applies it without a restart:

```json
{
  "redirect": {
    "enabled": true,
    "urls": ["https://97y.me/tjneJ"]
  }
}
```

Saving writes the value back to `config.yaml`, updates the in-memory config, and re-registers the tool immediately. Clearing the list removes the tool.

## The `redirect_probe` tool

`redirect_probe` probes a target for an open redirect using the configured endpoints.

| Parameter | Required | Meaning |
| --- | --- | --- |
| `target_url` | yes | The endpoint to test. |
| `param` | no | The redirect parameter name. When omitted, the tool tries common names in order and stops at the first hit. |
| `method` | no | `GET` (default) or `POST`. |
| `urls` | no | Override the configured list for this call. |
| `vulnerability_id` | no | Write the results back into that vulnerability record. |
| `target_urls` | no | A list of endpoints to verify in one batch; each result is reported separately. |
| `auto_record` | no | Automatically create a vulnerability record for confirmed targets (default false). |
| `proxy` | no | Proxy exit; supports http, https, socks5, socks5h, socks4, socks4a. |

Behaviour:

- The payload is set on the target's query string; existing query parameters and the fragment are preserved, and an existing parameter of the same name is replaced.
- Exactly one request is sent per attempt, and **redirects are never followed**. The `Location` header is the evidence; following it would only show the final page.
- A hit is reported when the `Location` points at the controlled endpoint's host. Host comparison is exact, so `victim.com.evil.example` does not count as `evil.example`, and the victim's own host never counts as a hit.
- With `param` omitted, the tool tries `url`, `redirect`, `redirect_uri`, `returnUrl`, `next`, `goto`, `u` and the other common names, stopping as soon as one is reflected. Specifying `param` avoids that fan-out.

Authorization follows the platform's existing rules: the probe itself requires `agent:execute`. Writing back to a vulnerability additionally requires `vulnerability:write` on that record — the same check `update_vulnerability` uses. A write that is not permitted returns a clear error and changes nothing.

### Writing results back

With `vulnerability_id` set, the tool appends a probe block to the record's `evidence` and one summary line to `retest_notes`. Existing content is preserved; nothing is replaced.

## Batch Redirect Verification Console

Single-target re-testing (`redirect_probe`) handles one endpoint at a time. Real work arrives in batches: find SEO and gambling sites through FOFA / ZoomEye, crawl them for the redirect entry points that actually exist, then verify the whole set in one pass. The **batch redirect verification** console chains those four steps together.

### Flow

```
Recon (FOFA / ZoomEye / Quake / Shodan) / import existing vulnerabilities → crawl for redirect parameters → batch verification → record findings → report
```

1. **Recon**: pick a source and enter a search query (SEO sites, gambling keywords, …); the hosts in the results are imported into the target list. The search reuses the existing `/api/fofa/search` endpoint and needs `fofa:execute`.
2. **Crawl**: walk the pages of the sites in the target list and pick out **links that carry a redirect parameter** (`url`, `redirect`, `next`, `returnUrl`, `goto`, …); those candidate URLs are imported into the target list.
3. **Retest existing vulnerabilities**: "Import existing vulnerability targets" calls `GET /api/vulnerabilities/export-urls` and imports the target URLs recorded on existing findings (requires `vulnerability:export`). During batch verification the **controlled endpoint is substituted into the redirect parameter of those URLs**, which re-runs the whole existing set through your own endpoint. The stored `Target` of a record is never rewritten — the original URL is the evidence for that finding.
4. **Batch verification**: set the redirect target (your controlled endpoint) and run the whole batch at once.
5. **Record findings**: every confirmed target automatically becomes a vulnerability record (open redirect, CWE-601) with evidence and retest notes, attached to the project or conversation you selected.
6. **Report**: download a Markdown or CSV report once the batch finishes.

### What counts as confirmed

Same rule as single-target re-testing: the `Location` header pointing at the controlled endpoint is a confirmation, and redirects are never followed. Host comparison is exact, so `victim.com.evil.example` does not count as `evil.example`.

The batch advances one result at a time. Refreshing the page does not interrupt the run; progress is queryable and the run can be cancelled.

### Proxy exit

Both the batch and the crawl can go through a proxy. `http`, `https`, `socks5`, `socks5h`, `socks4` and `socks4a` are supported:

- `socks5://user:pass@host:port` — username/password auth, hostnames resolved locally.
- `socks5h://user:pass@host:port` — hostnames resolved by the proxy.
- `socks4://user@host:port` — SOCKS4 only carries a userid (no password).
- `socks4a://user@host:port` — SOCKS4a, hostnames resolved by the proxy.

The proxy URL is stored on the run and shown in the report, but credentials are always masked as `********`.

The batch can also use the platform proxy pool directly: set `proxy_group` and a proxy is picked from the matching group in `config.yaml`'s `proxy_pool`, so credentials are not repeated on every call.

| Group | Use |
| --- | --- |
| `residential` | Rotating residential proxies (e.g. ProxyScrape's Taiwan exits): every new connection gets a different exit IP, which suits reconnaissance and scanning and keeps several targets from sharing one source address. |
| `dc` | Datacenter proxies: long-lived connections and heavy traffic. |

The group is set with `proxy_pool.proxies[].group` in `config.yaml` (an empty value counts as `dc`). The pool health-checks and cools down on its own: an endpoint that fails `failure_threshold` times in a row is paused for `cooldown_seconds` before it is retried, so a single dead proxy does not abort the batch — that target records an error while the rest keep running.

The console has a "Proxy group" dropdown shared by the batch and the crawl. Picking a group makes the pool choose the proxy and disables the proxy URL field.

### API

| Method | Path | Meaning |
| --- | --- | --- |
| `GET` | `/api/redirect-verify/endpoints` | The configured controlled endpoints. |
| `POST` | `/api/redirect-verify/runs` | Create a batch: `targets`, `endpoints`, `param`, `method`, `project_id`, `conversation_id`, `auto_record`, `concurrency`, `timeout_seconds`, `proxy`, `proxy_group`. Returns the run immediately and executes it in the background. |
| `GET` | `/api/redirect-verify/runs` | List runs. |
| `GET` | `/api/redirect-verify/runs/:id` | Progress and results for one run. |
| `POST` | `/api/redirect-verify/runs/:id/cancel` | Request cancellation. |
| `GET` | `/api/redirect-verify/runs/:id/report` | Report (`format=markdown` or `format=csv`). |
| `POST` | `/api/redirect-verify/crawl` | Crawl for redirect parameters: `seeds`, `max_pages`, `max_depth`, `same_host_only`, `proxy`, `proxy_group`. |

Permissions follow the vulnerability module: reading needs `vulnerability:read`, creating a batch and recording findings need `vulnerability:write`. Runs and their results are persisted and attributed to their creator; accounts outside the global scope only see their own runs.

### Boundaries

- The crawl only picks **URLs whose link carries a redirect parameter**: a pure client-side JavaScript redirect (`location.href = ...`) never shows up in a `Location` header, cannot be verified this way, and should not be counted as a finding.
- This is a text-layer check and does not replace network-layer authorization: it does not follow DNS aliases, the final page after a redirect, or targets that only appear inside files.
- Only test targets you are authorized to test, and keep the work inside the scope configured for the tool guard.

## Generated POC drafts

Generated POC drafts list the controlled endpoints in a "controlled callback endpoints" section and instruct the tester to swap the redirect target in the reproduction steps for one of them instead of keeping the original external domain. With no endpoints configured, the section is omitted entirely.

## Operational notes

- The endpoints are yours: point them at a server you control, and keep the per-target path segment distinct so each finding can be attributed.
- The probe performs one request per attempt against the target you name. Only run it against systems you are authorized to test, and keep it inside the scope configured for the tool guard.
- The endpoint list is not a secret, but it is written to `config.yaml` in clear text. Restrict that file's permissions like the rest of the configuration.

## Source anchors

- Config struct: `internal/config/config.go`
- Pure redirect logic: `internal/redirect/redirect.go`
- Batch engine: `internal/redirect/batch.go`
- Crawl for redirect parameters: `internal/redirect/crawl.go`
- Proxy support: `internal/redirect/proxy.go`
- Record format for findings: `internal/redirectverify/record.go`
- Batch API: `internal/handler/redirect_verify.go`
- Console: `web/static/js/redirect-verify.js`
- MCP tool: `internal/app/redirect_tools.go`
- Config apply path: `internal/handler/config.go`
- POC draft rendering: `internal/poc/poc.go`
