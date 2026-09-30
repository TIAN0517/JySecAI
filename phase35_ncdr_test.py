#!/usr/bin/env python3
"""Phase 35: Test NCDR API endpoints + probe geocode values."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

BASE = 'https://alerts.ncdr.nat.gov.tw/AddValueApi'

# 1. Test code list endpoints (likely no auth needed)
print("=== Code List Endpoints ===")
for path in ['/EventCode', '/OrgCode']:
    try:
        r = requests.get(f'{BASE}{path}', proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
        print(f"\n  GET {path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')[:40]}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  JSON keys: {list(data.keys()) if isinstance(data, dict) else f'array({len(data)})'}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"  First entry: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                elif isinstance(data, dict):
                    print(f"  Content: {json.dumps(data, ensure_ascii=False)[:500]}")
                with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_{path.strip("/").lower()}.json', 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except:
                print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:80]}")

# 2. Test RealTime/Sender to find org codes
print("\n=== RealTime/Sender probe (find org codes) ===")
for orgcode in ['0001', '0002', '001', '01', '100', 'NCDR', 'TPEB', 'TPFB', 'TFD', 'TPF']:
    try:
        r = requests.get(f'{BASE}/RealTime/Sender', params={'orgcode': orgcode, 'geocode': '0000', 'offset': 0, 'limit': 5}, 
                        proxies=PROXY, headers=HEADERS, verify=False, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"  orgcode={orgcode}: {len(data)} results - {json.dumps(data[0], ensure_ascii=False)[:200]}")
            elif isinstance(data, dict):
                print(f"  orgcode={orgcode}: {json.dumps(data, ensure_ascii=False)[:200]}")
    except:
        pass

# 3. Test EventCode to find event codes
print("\n=== EventCode dump ===")
try:
    r = requests.get(f'{BASE}/EventCode', proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            print(f"  Total event codes: {len(data)}")
            for item in data[:20]:
                print(f"    {json.dumps(item, ensure_ascii=False)[:150]}")
        elif isinstance(data, dict):
            print(f"  {json.dumps(data, ensure_ascii=False)[:500]}")
except Exception as e:
    print(f"  Error: {str(e)[:80]}")

# 4. Test RealTime with different geocodes (Taiwan county/municipal city codes)
print("\n=== RealTime probe with Taiwan geocodes ===")
# Taiwan geocodes: 01=Taipei, 02=Taoyuan, 03=Taichung, 04=Tainan, 05=Kaohsiung, 
# New Taipei=01 with sub, Taoyuan=02, Taichung=03, Tainan=04, Kaohsiung=05
geocodes = ['000', '001', '010000', '010001', '030000', '040000', '050000', 
            '0100010000', '030001', '030002', '030003', '030004', '030005',
            '010013', '010007', '030009']
for gc in geocodes:
    try:
        r = requests.get(f'{BASE}/RealTime', params={'geocode': gc, 'offset': 0, 'limit': 5},
                        proxies=PROXY, headers=HEADERS, verify=False, timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else '?'
            print(f"  geocode={gc}: {r.status_code}, count={count}")
            if isinstance(data, list) and len(data) > 0:
                print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:200]}")
    except:
        pass

# 5. Test without geocode param
print("\n=== RealTime without geocode ===")
for path in ['/RealTime', '/History/Event']:
    try:
        r = requests.get(f'{BASE}{path}', params={'offset': 0, 'limit': 5},
                        proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
        print(f"  GET {path}?offset=0&limit=5 -> {r.status_code}, len={len(r.text)}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  JSON: {json.dumps(data, ensure_ascii=False)[:300]}")
            except:
                print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {str(e)[:60]}")

print("\nDone.")
