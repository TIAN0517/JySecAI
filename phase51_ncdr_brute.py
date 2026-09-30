#!/usr/bin/env python3
"""Phase 51: NCDR API endpoint brute force."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'zh-TW,zh;q=0.9',
    'Referer': 'https://alerts.ncdr.nat.gov.tw/',
}

# The swagger is at /AddValueApi/swagger/index.html
# The API endpoints might be at different base paths
# Let me try accessing the endpoints directly with Capapikey header

print("=== Testing API endpoints with Capapikey header ===")
endpoints = [
    '/AddValueApi/v1/Auth/Captcha',
    '/AddValueApi/v1/Generic/county/106',
    '/AddValueApi/v1/Generic/apiAmount',
    '/AddValueApi/v1/Alerts/introductions',
    '/AddValueApi/v1/Auth/Session/Token',
    '/AddValueApi/v1/Auth/Profile',
]

for endpoint in endpoints:
    # Try without auth first
    r = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=15,
                      headers=HEADERS)
    print(f"  {endpoint}: {r.status_code}, len={len(r.text)}, ct={r.headers.get('content-type','')}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type',''):
        print(f"    Body: {r.text[:300]}")
    elif r.status_code == 500:
        print(f"    Body: {r.text[:200]}")
    elif r.status_code == 401:
        print(f"    Body: {r.text[:200]}")
    
    # Try with Capapikey
    r2 = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=15,
                       headers={**HEADERS, 'Capapikey': 'test'})
    if r2.status_code != r.status_code:
        print(f"    WITH Capapikey: {r2.status_code}, len={len(r2.text)}")
        if r2.status_code == 200 and 'html' not in r2.headers.get('content-type',''):
            print(f"    Body: {r2.text[:500]}")

# Try POST for login
print("\n=== POST /login endpoints ===")
login_endpoints = [
    '/AddValueApi/v1/Auth/Session/login',
    '/AddValueApi/v1/Auth/Session/eGovlogin',
    '/AddValueApi/v1/Auth/Session/Token',
]
for endpoint in login_endpoints:
    # Try GET first
    r = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=15,
                      headers={**HEADERS, 'Capapikey': 'test'})
    print(f"  GET {endpoint}: {r.status_code}, len={len(r.text)}")
    if r.status_code not in [404, 500, 200]:
        print(f"    Body: {r.text[:200]}")
