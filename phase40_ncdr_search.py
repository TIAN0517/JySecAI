#!/usr/bin/env python3
"""Phase 40: Search for NCDR open data API key on public portals."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

# 1. Check NCDR open data platform for this API
print("=== NCDR Open Data Portal ===")
urls_to_check = [
    'https://data.ncdr.nat.gov.tw/',
    'https://data.ncdr.gov.tw/',
    'https://www.ncdr.gov.tw/',
    'https://alerts.ncdr.nat.gov.tw/',
    'https://alerts.ncdr.nat.gov.tw/AddValueApi/',
]
for url in urls_to_check:
    try:
        r = requests.get(url, proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  {url} -> {r.status_code}, len={len(r.text)}")
    except Exception as e:
        print(f"  {url} -> ERR {str(e)[:60]}")

# 2. Search for Capapikey in the swagger bundle JS
print("\n=== Search for key patterns in swagger-ui-bundle.js ===")
r = requests.get('https://alerts.ncdr.nat.gov.tw/AddValueApi/swagger/swagger-ui-bundle.js',
                 proxies=PROXY, verify=False, timeout=15)
if r.status_code == 200:
    js = r.text
    # Look for actual key values near Capapikey references
    for pattern in [r'Capapikey["\s:]+[^\s,;)}]+', r'api[_-]?key["\s:]+[^\s,;)}"]{5,}',
                   r'key["\s:]+"[A-Za-z0-9_\-]{8,}"', r'Authorization.+Bearer',
                   r'capapikey', r'NCDR.{0,5}[A-Z0-9]{5,}']:
        matches = re.findall(pattern, js, re.I)
        if matches:
            unique = set(matches)
            print(f"  Pattern '{pattern[:30]}': {list(unique)[:5]}")

# 3. Check if there's a config.json or settings file
print("\n=== Config/settings/probe files ===")
for path in ['/AddValueApi/config.json', '/AddValueApi/appsettings.json', '/AddValueApi/settings.json',
             '/AddValueApi/web.config', '/AddValueApi/.env', '/AddValueApi/swagger/config.json',
             '/AddValueApi/v1/swagger.json', '/AddValueApi/swagger/v1/swagger.json',
             '/AddValueApi/capapikey', '/AddValueApi/key']:
    r = requests.get(f'https://alerts.ncdr.nat.gov.tw{path}', proxies=PROXY, verify=False, timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'test'})
    ct = r.headers.get('Content-Type', '')
    print(f"  GET {path}: {r.status_code}, len={len(r.text)}, ct={ct[:40]}")
    if r.status_code != 404 and r.status_code != 401:
        print(f"    Body: {r.text[:200]}")

# 4. Try to find actual key from NCDR portal
print("\n=== NCDR portal search for API key ===")
r = requests.get('https://data.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0'})
if r.status_code == 200:
    # Find any API key references
    keys = re.findall(r'[A-Z0-9]{8,}-[A-Z0-9]{4,}', r.text)
    print(f"  Potential keys: {keys[:5]}")
    # Or look for Capapikey
    capapikey_vals = re.findall(r'Capapikey["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', r.text)
    print(f"  Capapikey values: {capapikey_vals[:5]}")

print("\nDone.")
