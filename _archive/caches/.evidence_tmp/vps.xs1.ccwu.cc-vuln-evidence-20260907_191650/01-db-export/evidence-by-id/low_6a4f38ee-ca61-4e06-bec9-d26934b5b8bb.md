# ltc.tzuchi.org.tw missing security response headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)

- ID: `6a4f38ee-ca61-4e06-bec9-d26934b5b8bb`
- Severity: **low**
- Status: open
- Type: Security Misconfiguration / Missing HTTP Security Headers
- Target: `https://ltc.tzuchi.org.tw (LongtermCareService / LongtermCareBackend, all routes)`
- Conversation: `3b694297-0b84-41bc-a589-66652e232956`
- Created: 2026-09-03 05:21:47.985464851+08:00

## Description

The ltc.tzuchi.org.tw LongtermCareService application (Citrix ADC + Java/Tomcat behind Cloudflare) returns responses with NO security-related HTTP headers: missing Strict-Transport-Security (HSTS), Content-Security-Policy, X-Frame-Options, X-Content-Type-Options (nosniff), Referrer-Policy, and Permissions-Policy. Confirmed on the API endpoint (POST /LongtermCareService/api_backend/queryAbout) and the SPA. Only JSESSIONID (Secure; HttpOnly) and citrix_ns_id are set. The absence of X-Frame-Options/CSP frame-ancestors permits clickjacking of the login and user flows; absence of HSTS permits SSL-stripping/MITM downgrades; absence of nosniff permits MIME-type confusion. This is a security-misconfiguration weakness that compounds the other ltc findings (auth bypass and PII exposure).

## Reproduction

1) curl -s -D - -o /dev/null -X POST "https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryAbout" -H "Content-Type: application/json" -d '{}'
2) Inspect the response header block.
3) Observe that HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy and Permissions-Policy are all absent.
4) Confirm clickjacking by loading the app in an <iframe> from an attacker page (no XFO/frame-ancestors to block it).

## Evidence

Response headers from POST https://ltc.tzuchi.org.tw/LongtermCareService/api_backend/queryAbout (200):
  HTTP/2 200
  content-type: application/json;charset=UTF-8
  set-cookie: JSESSIONID=DC0057...; Path=/LongtermCareService; Secure; HttpOnly
  set-cookie: citrix_ns_id=...; Domain=.tzuchi.org.tw; Path=/; Secure; HttpOnly
  cf-cache-status: DYNAMIC
  server: cloudflare
  cf-ray: a34f8b864aa7a9cd-TPE
=> No Strict-Transport-Security, no Content-Security-Policy, no X-Frame-Options, no X-Content-Type-Options, no Referrer-Policy, no Permissions-Policy in the entire header set.

## Impact

Without HSTS the site is exposed to SSL-stripping / protocol-downgrade MITM. Without X-Frame-Options or CSP frame-ancestors the login page and authenticated user actions can be embedded in attacker-controlled iframes (clickjacking), enabling forced login/CSRF-style UI redressing. Without X-Content-Type-Options: nosniff, responses can be MIME-sniffed. These weaken the overall posture and facilitate exploitation of the adjacent auth and PII-exposure issues.

## Recommendation

Add response headers across the application/edge: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload; Content-Security-Policy with a restrictive frame-ancestors 'self' (or X-Frame-Options: SAMEORIGIN); X-Content-Type-Options: nosniff; Referrer-Policy: strict-origin-when-cross-origin; Permissions-Policy for camera/mic/geo. Enforce HTTPS-only.
