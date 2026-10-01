# Version disclosure, CSP internal-origin leak, and token-in-URL on EPCR cluster

- ID: `bdb43a96-8dbe-4fda-86fb-dafab6fa4ae1`
- Severity: **low**
- Status: open
- Type: Information Disclosure / Insecure Configuration
- Target: `https://epcr.tpf.gov.tw:4000/version/ and CSP header`
- Conversation: `0e6944a5-643d-4cd9-9a2a-7b1676a25139`
- Created: 2026-09-02 23:46:09.699338048+08:00

## Description

Multiple low-severity information-disclosure issues on the EPCR cluster: (1) GET /version/ returns "1.6.26080" (9 bytes) with no authentication, disclosing exact application build; (2) the Content-Security-Policy header on the primary app leaks 11 internal origins, including non-public IPs and localhost dev ports (http://35.234.50.28, http://localhost:8100, http://localhost:18081, epcr.tpf.gov.tw:4000-4008, 9000); (3) the Angular auth token is carried in the URL query string (?token=) and in localStorage, and the angular-jwt interceptor is commented out in app.js (both :4000 and :4004), weakening token handling. Together these aid an attacker by revealing internal topology, build version, and internal dev/VM hosts.

## Reproduction

1. `curl -sk https://epcr.tpf.gov.tw:4000/version/` -> "1.6.26080".
2. `curl -sk -D - https://epcr.tpf.gov.tw:4000/ | grep -i content-security-policy` -> shows internal origins (35.234.50.28, localhost:8100, localhost:18081, epcr.tpf.gov.tw:4000-4008, 9000).
3. Open app.js on :4000/:4004 and observe the commented-out jwtInterceptor and ?token= tokenGetter.

## Evidence

1) GET /version/ -> 200, content-length 9, body "1.6.26080" (no auth).
2) CSP header (on epcr.tpf.gov.tw:4000) content includes connect-src/child-frame-src listing: http://35.234.50.28, http://localhost:8100, http://localhost:18081, and epcr.tpf.gov.tw:4000..4008 and :9000.
3) app.js (port 4000 & 4004): jwtInterceptor registered line commented out; tokenGetter reads ?token= query param; whiteListedDomains includes internal 35.234.50.28.

## Impact

Facilitates further reconnaissance: attacker learns exact build (1.6.26080) to match known CVEs, internal VM/GCP host (35.234.50.28), localhost dev ports, and the full multi-port service topology. Token-in-URL risks leakage via logs/referrers. Low direct impact but reduces attacker effort for the higher-impact findings in this scope.

## Recommendation

Remove or require auth for /version/ in production; trim CSP connect-src to required origins and remove internal IPs/localhost; move the auth token out of the URL query string (use an HttpOnly cookie or Authorization header) and re-enable proper token handling.
