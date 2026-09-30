#!/usr/bin/env python3
"""Phase 55: NCDR CSRF + session flow."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
ADDED = "/AddValueApi"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# Create a session and replicate the website's flow
s = requests.Session()
s.proxies = PROXY
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-TW,zh;q=0.9',
    'Referer': f'{BASE}/',
})

print("=== Full website flow ===")
# 1. Visit main page
r = s.get(f'{BASE}/')
print(f"1. Main page: {r.status_code}, cookies: {dict(s.cookies)}")

# 2. Get CSRF token
r = s.get(f'{BASE}{ADDED}/v1/Csrf/token', headers={'Capapikey': 'test'})
print(f"2. CSRF token: {r.status_code}, body: {r.text[:200]}")

# 3. Get captcha
r = s.get(f'{BASE}{ADDED}/v1/Auth/Captcha', headers={'Capapikey': 'test'})
print(f"3. Captcha: {r.status_code}, ct={r.headers.get('content-type','')}, len={len(r.text)}")

# 4. Try login with session cookies
r = s.post(f'{BASE}{ADDED}/v1/Auth/Session/login',
            headers={'Capapikey': 'test', 'Content-Type': 'application/json'},
            json={'username': 'admin', 'password': 'admin', 'captchaCode': '', 'captchaId': ''})
print(f"4. Login: {r.status_code}, body: {r.text[:300]}")

# 5. Try with session cookies + Capapikey 
r = s.get(f'{BASE}{ADDED}/v1/Auth/Profile', headers={'Capapikey': 'test'})
print(f"5. Profile: {r.status_code}, body: {r.text[:200]}")

# 6. Check if the AddValueApi prefix is needed or if there are alternative paths
print("\n=== Try without AddValueApi prefix + Capapikey ===")
for endpoint in ['/v1/Auth/Session/login', '/v1/Auth/Captcha', '/v1/Auth/Profile', '/v1/Generic/county/106']:
    r = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=10,
                      headers={**s.headers, 'Capapikey': 'test'})
    print(f"  GET {endpoint}: {r.status_code}, ct={r.headers.get('content-type','')[:30]}, len={len(r.text)}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        print(f"    *** JSON FOUND: {r.text[:500]}")
