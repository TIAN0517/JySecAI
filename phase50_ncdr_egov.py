#!/usr/bin/env python3
"""Phase 50: Get eGovProfile URL + API key with proper headers."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# The Vue app calls resourceUrl with GET method and Accept: application/json
# The m() function: u.A.get(${base}${resourceUrl.slice(1)}, {params:{key:e}, withCredentials:true})
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://alerts.ncdr.nat.gov.tw/',
    'Origin': 'https://alerts.ncdr.nat.gov.tw',
}

print("=== resourceUrl with proper Accept ===")
for key in ['eGovProfile', 'eGov', 'plugin']:
    r = requests.get(f'{BASE}/AddValueApi/v1/Generic/resourceUrl', proxies=PROXY, verify=False, timeout=30,
                      headers=HEADERS, params={'key': key})
    print(f"\n  key={key}: {r.status_code}")
    try:
        data = r.json()
        print(f"  JSON: {json.dumps(data, indent=2)[:800]}")
    except:
        print(f"  Body: {r.text[:400]}")

# Also try with session cookies from visiting the main site first
print("\n=== With session from main site ===")
session = requests.Session()
session.proxies = PROXY
session.verify = False
session.headers.update(HEADERS)

# Visit main page to get cookies
r = session.get(f'{BASE}/')
print(f"  Main site: {r.status_code}, cookies: {dict(session.cookies)}")

# Now try resourceUrl with cookies
for key in ['eGovProfile', 'eGov']:
    r = session.get(f'{BASE}/AddValueApi/v1/Generic/resourceUrl', 
                     params={'key': key})
    print(f"\n  key={key}: {r.status_code}")
    try:
        data = r.json()
        print(f"  JSON: {json.dumps(data, indent=2)[:800]}")
    except:
        print(f"  Body: {r.text[:400]}")

# Try the AddValueApi base with resourceUrl
print("\n=== Try different base paths ===")
for path in ['/AddValueApi/v1/Generic/resourceUrl', '/v1/Generic/resourceUrl', '/api/v1/Generic/resourceUrl']:
    r = requests.get(f'{BASE}{path}', proxies=PROXY, verify=False, timeout=15,
                      headers=HEADERS, params={'key': 'eGovProfile'})
    print(f"  {path}: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200:
        print(f"  Body: {r.text[:500]}")
