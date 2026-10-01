# API Findings Pending Integration

> Status: working notes for later consolidation. Observations were made on 2026-09-30 (Asia/Taipei). Sensitive response values are intentionally omitted.

## Hsinchu Disaster Reporting API

### Source

- Swagger: `https://th-api.hcfd.gov.tw/swagger/v1/swagger.json`
- Relevant endpoint: `POST /api/ReportDamage/List`
- Swagger authorization label: `no auth`
- Request model: `Application.ReportDamage.List.Query`

### Safe read-only reproduction

```bash
curl -sS -X POST 'https://th-api.hcfd.gov.tw/api/ReportDamage/List' \
  -H 'Content-Type: application/json' \
  --data '{"pageRequestParameter":{"targetPage":1,"showCount":10}}'
```

The endpoint returned HTTP 200 without a Bearer token. It exposes structured disaster records including project, district, address, coordinates, disaster type, status, create/update times, contact details, personnel names, internal UUIDs, handling notes, and photo URLs.

### Realtime assessment

The endpoint is suitable for direct polling because records contain `createTime`, `updateTime`, `status1`, and `status1p5`. However, the unauthenticated query returned only 16 records from Project 35 (`1150809白海豚颱風`): all were created on 2026-08-09 and marked `已結案` / `已回報`. As of 2026-09-30, these are historical records rather than current realtime incidents.

### Security observation

Unauthenticated responses include personal and operational fields beyond what is needed for a public incident feed. Review whether contact numbers, exact coordinates, reporter/operator names, internal user identifiers, notes, and media URLs should be publicly returned. This supports a potential excessive-data-exposure or missing-object-level-authorization report, subject to owner confirmation of the intended access policy.

## Taipei 119 App Service API Matrix

### Supplied observations

- Base: `https://appservice119.tfd.gov.tw/TFD/api/tfdserv/`
- `POST car/car_member_list` with `{}` returned HTTP 200 and application status `ac_status: 2` (`沒有Token請重新登入進行綁定`).
- `POST schedule/rotationsearch` reportedly returned the same result.
- Supplying an arbitrary token reportedly returned `ac_status: 3` (`請綁定裝置`).
- SQL injection and XSS strings reportedly did not reach an application sink because the token/device-binding checks rejected them first.
- Supplied fingerprint: Apache 2.4.68 (Win64), OpenSSL 3.6.3, PHP 8.3.31.

### Assessment

These results demonstrate reachable API routes and a working authentication/device-binding gate. Enumerating six protected endpoints does not by itself establish a vulnerability, and only two endpoint names are currently documented. Keep this item as an attack-surface inventory unless evidence shows unauthorized data access, sensitive metadata disclosure, authentication bypass, or another concrete impact.

### Evidence still needed

- Names, methods, and exact responses for the remaining four endpoints.
- Response headers supporting the server fingerprint.
- Intended public/private access policy for each endpoint.
- A concrete security impact distinct from endpoint discoverability.

## Taipei Public Dispatch Feed

### Verified endpoint

- Endpoint: `POST https://service119.119.gov.taipei/service119/citizenCase/caseList`
- Authentication observed: none; `token=anything` was accepted.
- Verification time: 2026-09-30 (Asia/Taipei).

```bash
curl -sS -X POST \
  'https://service119.119.gov.taipei/service119/citizenCase/caseList' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'token=anything'
```

The response contained 23 records with incident times from `2026/09/30 18:09:31` through `2026/09/30 21:04:15`. Status counts were:

- `已出勤`: 4
- `到達現場`: 5
- `離開現場`: 12
- `返隊`: 1
- `離開醫院`: 1

This confirms that the endpoint currently supplies same-day dispatch status and is suitable for Telegram polling. Public row fields observed were `inTime`, `csKindName`, `caseStatus`, `csCodeName`, `csPlaceFuzzy`, `fuzzyX`, `fuzzyY`, `fuzzyAble`, and `dpKdid`.

### Current integration issue

`broadcast_daemon.py::fetch_dispatch_cases()` expects `sn`, `csX`, `csY`, and `csPlace`, but those fields were absent from the verified response. Consequences:

- `row.get("sn", "")` gives every record the same `dispatch_` deduplication key, so only the first matching scene record survives a polling cycle.
- Rows with `fuzzyAble=N` currently use missing `csX/csY` fields and may become coordinates `(0, 0)`.
- The stable local key should instead be derived from available fields such as incident time, fuzzy coordinates, type, and unit data.
- Address and coordinates should use `csPlaceFuzzy`, `fuzzyX`, and `fuzzyY` unless the API actually supplies exact fields.

The public feed is viable for Telegram, but the parser/deduplication logic needs adjustment before it can reliably broadcast all current scene cases.

## Excluded Items

The supplied `kfa.kcg.gov.tw` login-oracle tests, third-party SOCKS endpoints, and `tai-jihouse.com` access-token response were not validated because they do not provide dispatch records needed for Telegram broadcasting.
