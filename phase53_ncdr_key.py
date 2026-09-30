#!/usr/bin/env python3
"""Phase 53: Find NCDR API key via key management endpoints."""
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
}

# Try various possible API key endpoints
endpoints = [
    # getApiKey: "/v1/a...ateD" -> likely /v1/ApiKey/ or /v1/apiKey/
    '/AddValueApi/v1/ApiKey',
    '/AddValueApi/v1/apiKey',
    '/AddValueApi/v1/apiKey/get',
    '/AddValueApi/v1/ApiKey/get',
    
    # getAddValueApiKey likely starts with /v1/A
    '/AddValueApi/v1/AddValue/ApiKey',
    '/AddValueApi/v1/Alerts/Values/apikey',
    '/AddValueApi/v1/Alerts/Values/apikey/get',
    '/AddValueApi/v1/Alert/Values/apikey',
    '/AddValueApi/v1/Apikey',
    '/AddValueApi/v1/AlertApiKey',
    
    # Try common patterns
    '/AddValueApi/v1/Auth/APIKey',
    '/AddValueApi/v1/Auth/apikey',
    '/AddValueApi/v1/Generic/apikey',
    '/AddValueApi/v1/Dashboard/apikey',
    '/AddValueApi/v1/developer/apikey',
    '/AddValueApi/v1/developer/alerts-api/apikey',
    
    # Try the getApiKey endpoint (possibly /v1/A...ateD -> /v1/ApiKey/Validate or similar)
    '/AddValueApi/v1/ApiKey/validate',
    '/AddValueApi/v1/ApiKey/get',
    '/AddValueApi/v1/ApiKey/Create',
    '/AddValueApi/v1/ApiKey/validate',
]

for endpoint in endpoints:
    # Without auth
    r = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=10,
                      headers=HEADERS)
    if r.status_code not in [404, 500]:
        print(f"  GET {endpoint}: {r.status_code}, len={len(r.text)}, ct={r.headers.get('content-type','')}")
        if r.status_code == 200:
            print(f"    *** FOUND *** Body: {r.text[:500]}")
    
    # With Capapikey
    r2 = requests.get(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=10,
                       headers={**HEADERS, 'Capapikey': 'test'})
    if r2.status_code not in [404, 500]:
        print(f"  GET {endpoint} +Capapikey: {r2.status_code}, len={len(r2.text)}, ct={r2.headers.get('content-type','')}")
        if r2.status_code == 200 and 'html' not in r2.headers.get('content-type',''):
            print(f"    *** FOUND *** Body: {r2.text[:500]}")
    
    # POST too
    r3 = requests.post(f'{BASE}{endpoint}', proxies=PROXY, verify=False, timeout=10,
                        headers={**HEADERS, 'Capapikey': 'test'})
    if r3.status_code not in [404, 500]:
        print(f"  POST {endpoint}: {r3.status_code}, len={len(r3.text)}")
        if r3.status_code == 200 and 'html' not in r3.headers.get('content-type',''):
            print(f"    *** FOUND *** Body: {r3.text[:500]}")

# Also try the homepage with egovToken to trigger the login flow
print("\n=== Testing egovToken login flow ===")
r = requests.get(f'{BASE}/?egovToken=test', proxies=PROXY, verify=False, timeout=15,
                  headers={'User-Agent': 'Mozilla/5.0'})
print(f"  Homepage with egovToken: {r.status_code}, len={len(r.text)}")

# Try to get resourceUrl (which m() calls with key=eGovProfile)
# The actual API base used by postApi is likely /AddValueApi
# m() calls: u.A.get(`${p}${h.getResourceUrl.slice(1)}`, {params:{key:e}})
# where p is the base URL and getResourceUrl = "/v1/Generic/resourceUrl"
# So it calls: {baseURL}/v1/Generic/resourceUrl?key=eGovProfile
# But baseURL might include /AddValueApi

# Let's try the resourceUrl endpoint directly
print("\n=== Trying resourceUrl (used by egov flow) ===")
for base in [f'{BASE}{ADDED}', f'{BASE}']:
    r = requests.get(f'{base}/v1/Generic/resourceUrl', proxies=PROXY, verify=False, timeout=15,
                      headers={**HEADERS, 'Capapikey': 'test'},
                      params={'key': 'eGovProfile'})
    print(f"  {base}/v1/Generic/resourceUrl?key=eGovProfile: {r.status_code}, len={len(r.text)}")
    if r.status_code == 200 and 'html' not in r.headers.get('content-type', ''):
        print(f"    *** FOUND *** Body: {r.text[:500]}")
