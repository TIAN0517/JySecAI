#!/usr/bin/env python3
"""Phase 56: eGov token flow + direct API data extraction attempts."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
ADDED = "/AddValueApi"
PROXY = {'https': 'socks5://202.160.76.154:11085', 'http': 'socks5://202.160.76.154:11085'}

# The Vue app's m() function fetches: POST {base}/v1/Generic/resourceUrl?key=eGovProfile
# with withCredentials: true
# Then uses the response URL to fetch: GET {returned_url}?egovToken={token}

# Let me try to brute force geocode values with the RealTime endpoint
# and also try POST to resourceUrl with Capapikey

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Capapikey': 'test',
}

# Try POST to resourceUrl (the m() function uses GET, but the website's postApi could be different)
print("=== resourceUrl with different methods ===")
for method in ['GET', 'POST']:
    r = requests.request(method, f'{BASE}{ADDED}/v1/Generic/resourceUrl',
                          proxies=PROXY, verify=False, timeout=15,
                          headers=headers, params={'key': 'eGovProfile'})
    print(f"  {method} resourceUrl?key=eGovProfile: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        print(f"    *** FOUND: {r.text[:500]}")

# Let me also check the full swagger spec for more endpoint details
print("\n=== Swagger API paths ===")
r = requests.get(f'{BASE}{ADDED}/swagger/v1/swagger.json', proxies=PROXY, verify=False, timeout=15,
                  headers={'User-Agent': 'Mozilla/5.0'})
spec = r.json()
paths = spec.get('paths', {})
for path in sorted(paths.keys()):
    methods = list(paths[path].keys())
    print(f"  {path}: {methods}")
    for method in methods:
        detail = paths[path][method]
        params = detail.get('parameters', [])
        param_strs = []
        for p in params:
            if 'schema' in p:
                param_strs.append(f"{p['name']}:{p.get('in','')}={p['schema'].get('type','')}")
            else:
                param_strs.append(p['name'])
        if param_strs:
            print(f"    params: {param_strs}")

# Try some Taiwan county geocodes with the RealTime endpoint
print("\n=== Brute force geocode values ===")
# Taiwan county/city codes (old 2010 codes)
geocodes = ['000000', '001', '010000', '100001', '650000', '106', '108']
for gc in geocodes:
    r = requests.get(f'{BASE}{ADDED}/RealTime', proxies=PROXY, verify=False, timeout=15,
                      headers=headers, params={'geocode': gc, 'offset': 0, 'limit': 5})
    print(f"  geocode={gc}: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        print(f"    *** FOUND: {r.text[:500]}")

# Try EventCode and OrgCode
print("\n=== EventCode + OrgCode with Capapikey ===")
for endpoint in ['/EventCode', '/OrgCode']:
    r = requests.get(f'{BASE}{ADDED}{endpoint}', proxies=PROXY, verify=False, timeout=15,
                      headers=headers)
    print(f"  GET {endpoint}: {r.status_code}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        print(f"    *** FOUND: {r.text[:500]}")
