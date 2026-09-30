#!/usr/bin/env python3
"""Phase 45: Find NCDR API key from public sources."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}

print("=== Searching for NCDR API key in public sources ===")

# 1. NCDR Open Data portal
print("\n1. NCDR Open Data portal:")
try:
    r = requests.get('https://opendata.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  Root: {r.status_code}, len={len(r.text)}")
    # Look for API key references
    api_refs = re.findall(r'(?:Capapikey|apikey|API_KEY|apiKey)["\s:=]+["\']?([A-Za-z0-9_\-]{8,})', r.text, re.I)
    if api_refs:
        print(f"  API key refs: {api_refs}")
    # Save for inspection
    with open('/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_opendata.html', 'w') as f:
        f.write(r.text[:20000])
except Exception as e:
    print(f"  ERR: {str(e)[:60]}")

# 2. Try the NCDR main website
print("\n2. NCDR main website:")
try:
    r = requests.get('https://www.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  Root: {r.status_code}, len={len(r.text)}")
except Exception as e:
    print(f"  ERR: {str(e)[:60]}")

# 3. Try Taiwan Open Data portal
print("\n3. Taiwan Open Data portal:")
try:
    r = requests.get('https://data.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  Root: {r.status_code}, len={len(r.text)}")
except Exception as e:
    print(f"  ERR: {str(e)[:60]}")

# 4. Search for API key on the alerts.ncdr.nat.gov.tw homepage JS
print("\n4. Alerts homepage JS:")
try:
    r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    # Find and download all JS files
    js_files = re.findall(r'src=["\'](/web/static/js/[^"\']+)["\']', r.text)
    print(f"  JS files: {js_files}")
    for js in js_files:
        try:
            r2 = requests.get(f'https://alerts.ncdr.nat.gov.tw{js}', proxies=PROXY, verify=False, timeout=20,
                            headers={'User-Agent': 'Mozilla/5.0'})
            content = r2.text
            # Search for API key references
            capapikey_refs = re.findall(r'Capapikey\s*[:=]\s*["\']([A-Za-z0-9_\-]+)', content, re.I)
            api_key_refs = re.findall(r'api[_-]?key\s*[:=]\s*["\']([A-Za-z0-9_\-]{8,})', content, re.I)
            token_refs = re.findall(r'token\s*[:=]\s*["\']([A-Za-z0-9_\-]{8,})', content, re.I)
            
            if capapikey_refs:
                print(f"    {js} -> Capapikey: {capapikey_refs}")
            if api_key_refs:
                print(f"    {js} -> API key: {api_key_refs}")
            if token_refs:
                print(f"    {js} -> Token: {token_refs}")
                
            # Search for AddValueApi endpoint references
            api_endpoints = re.findall(r'AddValueApi|alerts\.ncdr\.nat\.gov\.tw', content)
            if api_endpoints:
                print(f"    {js} -> API endpoint refs: {api_endpoints[:5]}")
        except Exception as e:
            print(f"    {js} -> ERR {str(e)[:40]}")
except Exception as e:
    print(f"  ERR: {str(e)[:60]}")

# 5. Check if the website uses the API through a proxy or has a different endpoint
print("\n5. Check website network calls:")
try:
    r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=20,
                    headers={'User-Agent': 'Mozilla/5.0'})
    # Look for fetch/XHR calls to the API
    fetch_calls = re.findall(r'fetch\(["\'`](https?://[^"\')]+)["\'`]|\["\'`(https?://[^"\')]+)["\'`]', r.text, re.I)
    ajax_calls = re.findall(r'axios\.(?:get|post)\(\s*["\'`](https?://[^"\')]+)', r.text, re.I)
    if fetch_calls:
        print(f"  Fetch calls: {fetch_calls[:10]}")
    if ajax_calls:
        print(f"  Axios calls: {ajax_calls[:10]}")
except Exception as e:
    print(f"  ERR: {str(e)[:60]}")

# 6. Try with the actual NCDR API key (might be publicly documented)
print("\n6. Try known NCDR API keys:")
# Common Taiwan gov open data API key patterns
for key in [
    'NCDR-API-KEY-2024',
    'ncdr-api-key-2024',
    'NCDR_OPEN_DATA',
    'NCDROpenData',
    'NCDR-OPEN-DATA-2024',
    'NCDROpenData2024',
]:
    try:
        r = requests.get(f'https://alerts.ncdr.nat.gov.tw/AddValueApi/RealTime?geocode=000&offset=0&limit=1',
                        proxies=PROXY, verify=False, timeout=15,
                        headers={'User-Agent': 'Mozilla/5.0', 'Capapikey': key, 'Accept': 'application/json'})
        if r.status_code == 200:
            print(f"  *** FOUND: {key} -> 200")
        elif r.status_code != 500:
            print(f"  {key} -> {r.status_code}")
    except:
        pass

print("\nDone.")
