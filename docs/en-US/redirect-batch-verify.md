# Batch Open Redirect Verification

[中文](../zh-CN/redirect-batch-verify.md)

The single-shot `redirect_probe` tool re-tests one target at a time. Batch verification turns that into a pipeline:

```
Recon (FOFA / ZoomEye / Quake / Shodan) → Crawl for redirect parameters → Batch verification (controlled endpoint) → Auto-record (vulnerability record) → Report
```

The "redirect target" is the operator's own controlled callback endpoint, `https://97y.me/tjneJ` by default (the endpoint held in the platform's `redirect.urls`). The probe injects that endpoint into the target's redirect parameter and reads only the response's `Location` header to decide whether the target really jumps to your endpoint. **Redirects are never followed**, so the evidence is always the original `Location`.

The endpoint list itself is documented in [Controlled Redirect Endpoints](redirect-endpoints.md).

## Console

The "Batch Redirect Verification" page (route `redirect-verify`) in the asset / security area offers four actions:

| Action | Endpoint |
| --- | --- |
| Recon import | `/api/fofa/search` (multi provider); imports the result hostnames into the target list |
| Crawl for candidates | `/api/redirect-verify/crawl`; collects `<a href>` / `<form action>` / `<link href>` and treats URLs whose query contains a common redirect parameter as candidates |
| Import existing findings | `/api/vulnerabilities/export-urls`; re-runs the targets already stored in vulnerability records |
| Start batch verification | `/api/redirect-verify/runs`; confirmed targets are recorded automatically and the report can be downloaded |

On load the page calls `/api/redirect-verify/endpoints` and prefills the first entry into the "redirect target" field. When the list is empty it tells you to fill in your own callback address.

## API

| Method | Path | Meaning |
| --- | --- | --- |
| POST | `/api/redirect-verify/runs` | Create a run: `targets[]`, `endpoints[]`, `param`, `method`, `project_id`, `conversation_id`, `auto_record`, `concurrency`, `timeout_seconds`, `proxy`, `proxy_group`; returns `202` with the `run` and executes in the background |
| POST | `/api/redirect-verify/runs/:id/cancel` | Request cancellation; the background worker observes the flag and stops before the next target |
| GET | `/api/redirect-verify/runs/:id` | Progress plus results (`run` and `results`) |
| GET | `/api/redirect-verify/runs` | List runs (`limit` defaults to 50, max 200, filtered by permission) |
| GET | `/api/redirect-verify/runs/:id/report` | Report, `format=markdown` (default) / `csv` / `json` |
| GET | `/api/redirect-verify/endpoints` | The controlled endpoints configured on the platform |
| POST | `/api/redirect-verify/crawl` | Crawl for candidates: `seeds[]`, `max_pages`, `max_depth`, `same_host_only`, `proxy`, `proxy_group` |

### Where the endpoints come from

The order is fixed, and when all three sources are empty the request fails with an error and nothing is sent:

1. `endpoints` in this request;
2. `redirect.urls` in the platform settings;
3. none → `400`.

```yaml
redirect:
  enabled: true
  urls:
    - https://97y.me/tjneJ
```

### What counts as a hit

- Only the `Location` header is read; redirects are never followed.
- The host must match the controlled endpoint **exactly**: `victim.com.97y.me` does not count as `97y.me`, and the victim's own host never counts.
- With `param` omitted, the common parameter names are tried in order (`url`, `redirect`, `redirect_uri`, `returnUrl`, `next`, `goto`, `u`, …) and the run stops at the first hit.

## Auto-recording

When a result is `confirmed=true` and `auto_record=true`, each confirmed target becomes an "Open Redirect (confirmed by controlled redirect verification)" vulnerability record:

- Title: `开放性重定向（受控跳转验证确认）- <host>`;
- Type code `open-redirect`, severity `medium`, status `confirmed`;
- Evidence carries the request URL, status code, `Location`, controlled endpoint and parameter name; the retest note is appended as a separate line;
- Attribution: `project_id` first, `conversation_id` second; with neither, no record is created and the summary says why.

Creating a record requires `vulnerability:write`. Without the permission the results are still kept, but nothing is written to the database.

## Progress and results

A run is `pending` / `running` / `completed` / `cancelled` / `failed`. Every result is persisted (`redirect_verify_runs` and `redirect_verify_results`), so refreshing the page or signing in again does not lose it. Proxy URLs that carry credentials are masked before they are stored; the original value only lives in the memory of the executing process.

## Security boundaries

- A batch only touches targets the operator supplied explicitly or that recon / crawling produced. The platform's existing `tool_guard.scope` and project scope still gate them at the interception layer; government sites and critical infrastructure outside the scope stay blocked.
- The probe never follows redirects and only reads `Location`; reports and vulnerability records contain no credentials.
- The endpoint is the operator's own callback address — point it at a server you control and keep a distinct path segment per target so each finding can be attributed.
- There are two ways out via a proxy: paste a proxy URL, or use a platform proxy group (`proxy_group`). Using `proxy_group` while the proxy pool is disabled returns an error.

## Batch rewriting the controlled endpoint in existing findings

The redirect payload in a vulnerability record usually embeds the attacker's own domain. `POST /api/vulnerabilities/rewrite-controlled-endpoints` replaces the external URL at payload positions with the controlled endpoint, so a whole batch of records can be re-tested against one set of endpoints.

```json
{
  "endpoint": "https://97y.me/tjneJ",
  "dry_run": false,
  "limit": 500,
  "project_id": ""
}
```

- `endpoint` is required: only http/https controlled endpoints are accepted.
- With `dry_run` set to true the call only reports what would change and writes nothing — run it once to see the scope, then run it for real.
- Which records can actually be changed is decided by the caller's RBAC scope; the listed records are already filtered.

The rewrite only touches payload positions, it never replaces a whole block:

| Position | Example | Rewritten |
| --- | --- | --- |
| Redirect parameter value | `?url=https://evil.example/steal`, `url=https://evil.example/steal` | yes |
| `Location` header value | `Location: https://evil.example/land` | yes |
| Sample / config assignment | `targetUrl="https://evil.example/"`, `"callbackUrl":"https://evil.example/cb"` | yes |
| Labelled controlled endpoint | `受控端點：https://evil.example/cb` | yes |
| The target's own URLs | `https://victim.example/style.js`, `https://www.victim.example/...` | no |
| External links in descriptive prose | a third-party site mentioned in the impact paragraph | no |
| Already the controlled endpoint | `https://97y.me/tjneJ` | no (so the rewrite is repeatable) |

The scope is the Description, Reproduction steps, Evidence and Retest notes fields; Impact and Recommendation are left alone.

In the console, the "Batch rewrite vulnerability endpoints" button on the Batch Redirect Verification page calls this API with the endpoint from the input field.

## Source anchors

- Config: `internal/config/config.go`
- Pure logic: `internal/redirect/redirect.go` (probe primitive), `internal/redirect/batch.go` (batch engine), `internal/redirect/crawl.go` (crawler)
- REST API: `internal/handler/redirect_verify.go`
- Persistence: `internal/database/redirect_verify.go`
- Vulnerability record assembly: `internal/redirectverify/record.go`
- MCP tools: `internal/app/redirect_tools.go`, `internal/app/redirect_batch_tools.go`
- Console: `web/static/js/redirect-verify.js`, `web/static/css/redirect-verify.css`, `web/templates/index.html`
- Design spec: `docs/superpowers/specs/2026-11-01-redirect-batch-verify-design.md`
