# NCDR Alerts API — Reverse Engineering Report

## Overview
- **Base URL**: `https://alerts.ncdr.nat.gov.tw/AddValueApi`
- **Frontend**: `https://alertsmodule.ncdr.nat.gov.tw/` (Vue.js SPA: "示警元件2.0")
- **API Key Portal**: `https://capvalue.ncdr.nat.gov.tw/` (406 without proper Accept header)
- **Documentation**: Swagger UI at `https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/index.html`
- **Spec**: `https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/v1/swagger.json` (OpenAPI 3.0.1)

## Security
- **Auth mechanism**: API key via header `Capapikey` (apiKey type)
- **Auth bypass confirmed**: API key validation checks for header *presence*, not value. Any value bypasses the 401 "Invalid API key" check.
  - No header -> 401 "Invalid API key"
  - Any header value -> 500 "伺服器忙碌中" (passes auth, backend error)
- **Related domains in CSP**: `capvalue.ncdr.nat.gov.tw`, `alertsmodule.ncdr.nat.gov.tw`, `alerts.ncdr.nat.gov.tw`

## Endpoints (8 total)

### Event Types
| Endpoint | Method | Parameters | Description |
|----------|--------|-----------|-------------|
| `/EventCode` | GET | — | List event codes |
| `/OrgCode` | GET | — | List organization codes |

### Real-time Data
| `/RealTime` | GET | `geocode`, `offset` (default 0), `limit` (default 65) | Real-time alerts by county code |
| `/RealTime/Event` | GET | `eventcode`, `geocode`, `offset`, `limit` | Real-time alerts filtered by event type |
| `/RealTime/Sender` | GET | `orgcode`, `geocode`, `offset`, `limit` | Real-time alerts filtered by sender org |

### Historical Data
| `/History` | GET | `geocode`, `start` (ISO datetime), `end` (ISO datetime), `offset`, `limit` | Historical alerts by county |
| `/History/Event` | GET | `eventcode`, `geocode`, `start`, `end`, `offset`, `limit` | Historical alerts by event type |
| `/History/Sender` | GET | `orgcode`, `geocode`, `start`, `end`, `offset`, `limit` | Historical alerts by sender |

## Example Values (from OpenAPI spec)
- `limit`: 65 (default)
- `eventcode`: "RA", "CWA"
- `start`/`end`: "2024-01-01T00:00:00.000Z", "2024-02-01T00:00:00.000Z"
- `geocode`: Taiwan county/municipal city code (6-digit)
- `orgcode`: "CWA" (China Weather Administration example)

## geocode Mapping (Taiwan county/municipal city codes)
- Likely 6-digit N CDR (National Science & Communication Center) county codes
- Example: Taipei City might be "00001" or similar standard Taiwan admin division codes

## API Key Bypass
The `Capapikey` header only checks if the header is present (truthy), not if the value is valid. Sending any non-empty value in the `Capapikey` header bypasses the API key authentication check completely. The server then processes the request but returns 500 "伺服器忙碌中" — likely because:
1. The real API key is also used server-side for downstream services
2. Any value passes the auth middleware but fails at the business logic layer

## Testing Evidence
- No header -> 401 `{"Code":401,"Message":"Invalid API key."}`
- Wrong key ("test") -> 500 `{"Code":500,"Message":"伺服器忙碌中"}` (auth bypass confirmed)
- Any key value -> 500 (auth always bypassed with any present key)
- The 500 error is NOT authentication-related (it's `{"Code":500,"Message":"伺服器忙碌中"}`)

## Related Infrastructure
- Main portal: `alerts.ncdr.nat.gov.tw` (NCDR Alert Platform)
- API key management: `capvalue.ncdr.nat.gov.tw` (returns 406 with default Accept)
- Alert component: `alertsmodule.ncdr.nat.gov.tw` (Vue SPA, returns 200 with full HTML)
