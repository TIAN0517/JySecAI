#!/usr/bin/env python3
"""Phase 22: Extract EPCR app JS + find login/auth endpoints."""
import requests, urllib3, re, time, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
PROXY = {"https": "socks5h://202.160.76.154:11085"}

s = requests.Session()
s.headers.update(HEADERS)
s.verify = False
s.proxies = PROXY

# Get EPCR root page
r = s.get("https://118.163.107.93:4000/", timeout=15)
print(f"EPCR root: {r.status_code}, len={len(r.text)}")

# Find ALL JS files (not just bower_components - the app JS files)
all_js = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
app_js = [js for js in all_js if "bower_components" not in js and "node_modules" not in js]
print(f"App JS files (non-bower): {app_js}")

# Also look for template files, app JS in script tags
inline_js = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.S)
for i, script in enumerate(inline_js):
    if len(script.strip()) > 50:
        print(f"\nInline JS block {i+1} ({len(script)} chars):")
        print(script.strip()[:500])

# Download app JS files
for js_url in app_js:
    if js_url.startswith("/"):
        full_url = f"https://118.163.107.93:4000{js_url}"
    else:
        full_url = f"https://118.163.107.93:4000/{js_url}"
    try:
        rjs = s.get(full_url, timeout=10)
        print(f"\nApp JS: {js_url} -> {rjs.status_code}, len={len(rjs.text)}")
        safe_name = js_url.replace("/", "_").replace("?", "_").replace(".", "_")
        with open(f"tpe119_evidence/login_pages/epcr_{safe_name}.js", "w") as f:
            f.write(rjs.text[:50000])
        
        # Extract API endpoints, routes, auth patterns
        # Angular route definitions
        routes = re.findall(r'["\']/(?:api|auth|login|user|admin|token|v\d)[^\s"\'{}]+["\']', rjs.text)
        print(f"  API routes: {routes[:20]}")
        
        # Auth/token patterns
        auth_urls = re.findall(r'["\'][^\s"\']*(?:token|auth|login|jwt|bearer|session)[^\s"\']*["\']', rjs.text, re.I)
        print(f"  Auth patterns: {auth_urls[:15]}")
        
        # URL patterns
        urls = re.findall(r'["\'](/[a-z][a-z0-9_/-]*)["\']', rjs.text)
        unique = list(set(urls))[:]
        api_like = [u for u in unique if any(w in u for w in ['api', 'auth', 'login', 'token', 'user', 'admin', 'v1', 'v2'])]
        print(f"  All paths: {unique[:30]}")
        print(f"  API-like paths: {api_like[:20]}")
    except Exception as e:
        print(f"  App JS {js_url}: ERROR {str(e)[:80]}")
    time.sleep(0.3)

# Also try common EPCR API endpoints
print("\n=== EPCR API Endpoint Probes ===")
for path in ["/api/auth/login", "/api/login", "/api/v1/login", "/api/v1/auth/login",
             "/api/users/login", "/auth/login", "/token", "/api/token",
             "/api/v1/users/authenticate", "/api/auth", "/api/session",
             "/login", "/oauth/token", "/api/v1/token", "/api/v2/auth/login"]:
    r = s.get(f"https://118.163.107.93:4000{path}", timeout=8, allow_redirects=False)
    print(f"  :4000{path}: {r.status_code}, len={len(r.text)}, body={r.text[:100]}")
    time.sleep(0.1)
