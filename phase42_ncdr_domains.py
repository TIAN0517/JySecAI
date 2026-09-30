#!/usr/bin/env python3
"""Phase 42: Investigate capvalue.ncdr.nat.gov.tw and alertsmodule.ncdr.nat.gov.tw."""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import requests, urllib3, json, re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {'https': 'socks5h://202.160.76.154:11085', 'http': 'socks5h://202.160.76.154:11085'}
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

# 1. Check capvalue.ncdr.nat.gov.tw
print("=== capvalue.ncdr.nat.gov.tw ===")
for path in ['/', '/swagger', '/swagger/index.html', '/api', '/api/key', '/api/values',
             '/capapikey', '/key', '/config', '/.env', '/api/capapikey']:
    try:
        r = requests.get(f'https://capvalue.ncdr.nat.gov.tw{path}', proxies=PROXY, verify=False, timeout=15,
                        headers=HEADERS)
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')[:50]}")
        if r.status_code == 200 and len(r.text) > 1:
            print(f"    Body: {r.text[:300]}")
            # Save if it has content
            with open(f'/mnt/c/Users/Administrator/desktop/JySecAI/tpe119_evidence/ncdr_capvalue_{path.replace("/","_").strip("_")}.html', 'w') as f:
                f.write(r.text[:5000])
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:60]}")

# 2. Check alertsmodule.ncdr.nat.gov.tw
print("\n=== alertsmodule.ncdr.nat.gov.tw ===")
for path in ['/', '/swagger', '/api', '/config', '/.env', '/js', '/js/app.js']:
    try:
        r = requests.get(f'https://alertsmodule.ncdr.nat.gov.tw{path}', proxies=PROXY, verify=False, timeout=15,
                        headers=HEADERS)
        print(f"  GET {path} -> {r.status_code}, len={len(r.text)}, ct={r.headers.get('Content-Type','')[:50]}")
        if r.status_code == 200 and len(r.text) > 1:
            print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  GET {path} -> ERR {str(e)[:60]}")

# 3. The homepage referenced capvalue.ncdr.nat.gov.tw - check if the homepage has any JS
# that sets the Capapikey header
print("\n=== Fetch and parse homepage HTML ===")
r = requests.get('https://alerts.ncdr.nat.gov.tw/', proxies=PROXY, verify=False, timeout=15,
                headers={'User-Agent': 'Mozilla/5.0'})
if r.status_code == 200:
    html = r.text
    # Find script tags
    scripts = re.findall(r'src=["\']([^"\']+)["\']', html)
    print(f"  Scripts: {scripts}")
    # Find any inline scripts
    inline = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(inline):
        if len(s.strip()) > 10:
            print(f"  Inline script {i}: {s[:300]}")
    # Look for Capapikey usage
    capapikey_refs = re.findall(r'Capapikey|capapikey|API[_-]?Key|apiKey', html, re.I)
    print(f"  API key refs: {capapikey_refs}")
    # Look for fetch/XHR calls to the AddValueApi
    fetch_urls = re.findall(r'fetch\(["\'`]([^"\'`]+)', html)
    print(f"  Fetch URLs: {fetch_urls}")
    ajax_urls = re.findall(r'\.ajax\(\{[^}]*url["\']?\s*:\s*["\']([^"\']+)', html, re.DOTALL)
    print(f"  Ajax URLs: {ajax_urls}")

# 4. Try the alerts.ncdr.nat.gov.tw/AddValueApi/swagger again with different Accept
# Maybe there's a v2 of the spec
print("\n=== Check for alternate swagger specs ===")
for url in ['/AddValueApi/swagger/v1/swagger.json', '/AddValueApi/swagger.json',
            '/AddValueApi/openapi.json', '/AddValueApi/swagger/v2/swagger.json',
            '/AddValueApi/v2/swagger.json', '/AddValueApi/api/swagger.json',
            '/AddValueApi/swagger/config', '/AddValueApi/swagger/config.json']:
    r = requests.get(f'https://alerts.ncdr.nat.gov.tw{url}', proxies=PROXY, verify=False, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    ct = r.headers.get('Content-Type', '')
    print(f"  {url} -> {r.status_code}, len={len(r.text)}, ct={ct[:50]}")
    if r.status_code == 200 and 'json' in ct.lower():
        try:
            data = r.json()
            if 'info' in data:
                print(f"    Title: {data['info'].get('title')}")
                if 'securityDefinitions' in data:
                    print(f"    Security: {json.dumps(data['securityDefinitions'], ensure_ascii=False)}")
                if 'security' in data:
                    print(f"    Top security: {data['security']}")
        except:
            print(f"    Body: {r.text[:200]}")

print("\nDone.")
