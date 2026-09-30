#!/usr/bin/env python3
"""Phase 49c: Get eGovProfile URL via resourceUrl endpoint."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://alerts.ncdr.nat.gov.tw"
PROXY = {
    'https': 'socks5://202.160.76.154:11085',
    'http': 'socks5://202.160.76.154:11085',
}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'application/json'}

print("=== Getting eGovProfile URL ===")
# Call the resourceUrl endpoint to get the eGov profile URL
for key in ['eGovProfile', 'eGov', 'plugin']:
    r = requests.get(f'{BASE}/v1/Generic/resourceUrl', proxies=PROXY, verify=False, timeout=30,
                      headers=HEADERS, params={'key': key})
    print(f"\n  key={key}: {r.status_code}, len={len(r.text)}")
    try:
        data = r.json()
        print(f"  JSON: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"  Body: {r.text[:300]}")

# Also try without proxy (direct)
print("\n=== Direct (no proxy) ===")
for key in ['eGovProfile', 'eGov']:
    try:
        r = requests.get(f'{BASE}/v1/Generic/resourceUrl', verify=False, timeout=30,
                          headers=HEADERS, params={'key': key})
        print(f"\n  key={key}: {r.status_code}, len={len(r.text)}")
        try:
            data = r.json()
            print(f"  JSON: {json.dumps(data, indent=2)[:500]}")
        except:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")

# Try getting API key with various auth
print("\n=== Try getApiKey without auth ===")
r = requests.get(f'{BASE}/AddValueApi/v1/Alerts/Values/apikey', proxies=PROXY, verify=False, timeout=30,
                  headers=HEADERS)
print(f"  Status: {r.status_code}, len={len(r.text)}")

r = requests.get(f'{BASE}/AddValueApi/v1/Generic/apiAmount', proxies=PROXY, verify=False, timeout=30,
                  headers=HEADERS)
print(f"  apiAmount: {r.status_code}, len={len(r.text)}")
