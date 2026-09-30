#!/usr/bin/env python3
"""Phase 62: Test EPCR routes with JWT - uppercase and lowercase variants."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64, hmac, hashlib, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# The JWT secret in env is for TOCP, not EPCR. But let's try.
# First, decode existing JWT to confirm its structure
existing_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMDYzIiwiaWF0IjoxNzkwMjE0OTMzLCJleHAiOjE3OTAyMjU3MzN9." # truncated

# Let's try without JWT but with Capapikey - see if EPCR also has auth header bypass
EPCR = "https://epcr.tpf.gov.tw:4004"
headers_noauth = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, text/plain, */*',
    'Capapikey': 'test',  # Try the same bypass
    'Authorization': 'Bearer test',  # Try fake bearer
    'X-Auth-Token': 'test',
}

# All routes found in JS files
all_routes = [
    '/Users', '/Roles', '/Permissions', '/Awarenesses', '/DispatchRecords', '/MeasureStatuses',
    '/config', '/dispatch', '/hospital', '/hospitalAbility', '/hospitalCapability',
    '/hospitalCapabilityList', '/hospitalCapabilityListForHealth', '/hospitalChiefComplaint',
    '/changepassword', '/login', '/login2FA', '/login2fa', '/caseList',
    '/Users/activateAccount/', '/Users/changePassword', '/Users/enableAccount/',
    '/Users/resetPassword/', '/Users/setUserPermissionMap/',
    '/Roles/setRolePermissionMap/', '/Permissions/', '/Roles/', '/Users/',
    '/OpManagement/overviewOperatingRoom',
]

print("=== Testing EPCR routes with fake auth ===")
for ep in all_routes:
    try:
        r = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=8, headers=headers_noauth)
        ct = r.headers.get('content-type', '')
        if r.status_code not in [404]:  # Skip 404s
            print(f"  GET {ep}: {r.status_code}, ct={ct[:30]}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    *** SUCCESS: {r.text[:500]}")
    except Exception as e:
        pass

# Now check the 401 response - what auth does it expect?
print("\n=== Checking auth requirements ===")
for ep in ['/Users', '/Roles', '/Permissions', '/changepassword']:
    # No auth at all
    r1 = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=8,
                       headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  {ep} (no auth): {r1.status_code} - {r1.text.strip()[:100]}")
    
    # With Bearer
    r2 = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=8,
                       headers={'User-Agent': 'Mozilla/5.0', 'Authorization': 'Bearer test'})
    print(f"  {ep} (Bearer): {r2.status_code} - {r2.text.strip()[:100]}")
    
    # With X-Auth-Token  
    r3 = requests.get(f'{EPCR}{ep}', proxies=PROXY, verify=False, timeout=8,
                       headers={'User-Agent': 'Mozilla/5.0', 'X-Auth-Token': 'test'})
    print(f"  {ep} (X-Auth-Token): {r3.status_code} - {r3.text.strip()[:100]}")
    print()
