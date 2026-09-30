#!/usr/bin/env python3
"""Phase 41: Final NCDR key discovery + test with correct methods."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# 1. Read the saved swagger HTML
print("=== Read saved swagger HTML for key hints ===")
try:
    with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_swagger_index.html', 'r') as f:
        html = f.read()
    # Find any spec URL
    spec_urls = re.findall(r'url:["\']([^"\']+)', html)
    print(f"  Spec URLs: {spec_urls}")
    # Find any key/API references
    key_refs = re.findall(r'(?:Capapikey|apikey|api_key|key)["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', html, re.I)
    print(f"  Key refs: {key_refs}")
except FileNotFoundError:
    # Fetch it fresh
    r = requests.get(f'{BASE}/swagger', proxies=PROXY, verify=False, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0'})
    with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_swagger_index.html', 'w') as f:
        f.write(r.text)
    key_refs = re.findall(r'(?:Capapikey|apikey|api_key|key)["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', r.text, re.I)
    print(f"  Key refs: {key_refs}")

# 2. Test if the 500 is because the key is being consumed but invalid -> try with known open data keys
# The NCDR open data platform sometimes publishes demo keys
print("\n=== Try known NCDR/open data API keys ===")
# Get the swagger spec to see if there are example values
r = requests.get(f'{BASE}/swagger/v1/swagger.json', proxies=PROXY, verify=False, timeout=15)
spec = r.json()

# Look for examples in the spec
for path, methods in spec.get('paths', {}).items():
    for method, info in methods.items():
        if isinstance(info, dict):
            for param in info.get('parameters', []):
                if param.get('in') == 'header' and param.get('name') == 'Capapikey':
                    schema = param.get('schema', {})
                    if 'example' in schema:
                        print(f"  Example key in spec: {schema['example']}")
                    if 'default' in schema:
                        print(f"  Default key in spec: {schema['default']}")
                    # Check all possible keys
                    for k, v in schema.items():
                        if k in ['example', 'default', 'enum']:
                            print(f"  Schema {k}: {v}")

# 3. The 500 might be because we need to pass BOTH the right key AND the right params
# Let's try the exact same request but check the response more carefully  
print("\n=== Detailed 500 response headers check ===")
r = requests.get(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'test', 'Accept': 'application/json'},)
print(f"  Status: {r.status_code}")
print(f"  All headers: {dict(r.headers)}")
print(f"  Body: {r.text}")

# 4. Try with the exact Swagger UI default behavior
# The swagger page sets up the auth via the UI. If tryItOut is disabled, 
# maybe we need to use the API through the swagger proxy or with a specific format
print("\n=== Try EventCode as POST with JSON body ===")
r = requests.post(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=15,
                 headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'test', 'Accept': 'application/json',
                          'Content-Type': 'application/json'},
                 json={})
print(f"  POST /EventCode: {r.status_code} - {r.text[:200]}")

# 5. Try with x-api-key format as the spec says HeaderAuth -> apiKey -> header -> Capapikey
# The key might be something simple that's published in their docs
print("\n=== Try with NCDR open data dataset keys ===")
# Common patterns for Taiwan gov open data
for key in ['NCDR-OPEN-API-KEY', 'ncdr-open-api-key', 'NcdrOpenData',
            'NCDROpenData2024', 'AlertPlatform', 'ncdr-alert']:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': key},)
    if r.status_code != 500:
        print(f"  Capapikey={key} -> {r.status_code} ***")
    else:
        pass  # Still 500

# 6. Check the alerts.ncdr.nat.gov.tw homepage for key
print("\n=== Homepage root check ===")
r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0'})
print(f"  Root: {r.status_code}, len={len(r.text)}")
key_on_home = re.findall(r'(?:Capapikey|apikey|api_key|key)["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', r.text, re.I)
print(f"  Keys on homepage: {key_on_home}")
# Look for any script that might set the key
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
for s in scripts:
    if 'capapikey' in s.lower() or 'apikey' in s.lower():
        keys = re.findall(r'(?:Capapikey|apikey|api_key)["\s:=]+["\']?([A-Za-z0-9_\-]{5,})', s, re.I)
        if keys:
            print(f"  Keys in script: {keys}")

# 7. Try OPTIONS to see required headers
print("\n=== OPTIONS preflight ===")
r = requests.options(f'{BASE}/EventCode', proxies=PROXY, verify=False, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0', 'Origin': 'https://alerts.ncdr.nat.gov.tw',
                             'Access-Control-Request-Method': 'GET',
                             'Access-Control-Request-Headers': 'capapikey'})
print(f"  OPTIONS: {r.status_code}")
req_headers = r.headers.get('Access-Control-Request-Headers', r.headers.get('Access-Control-Allow-Headers', ''))
print(f"  ACAH: {req_headers}")
print(f"  All response headers: {dict(r.headers)}")

print("\nDone.")
