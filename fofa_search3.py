#!/usr/bin/env python3
"""
Try FOFA v5 API endpoints (the Nuxt SPA uses these).
Also try alternative cyberspace search engines.
"""
import requests, json, base64, urllib.parse

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://fofa.info/",
    "Origin": "https://fofa.info",
})

# FOFA v5 API - the Nuxt app typically uses /api/ routes
queries = [
    "service119.tfd.gov.tw",
    "tfd.gov.tw",
    "epcr.tpf.gov.tw",
    "tpf.gov.tw",
]

for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    print(f"\n=== Query: {q} ===")
    
    # Try v5 API endpoints
    endpoints = [
        f"https://fofa.info/api/v1/search/all?qbase64={enc}",
        f"https://fofa.info/v1/api/search?keyword={urllib.parse.quote(q)}",
        f"https://fofa.info/api/search?q={urllib.parse.quote(q)}",
    ]
    for url in endpoints:
        try:
            r = s.get(url, timeout=15, verify=False)
            status = r.status_code
            body = r.text[:300]
            print(f"  [{status}] {url.replace('https://fofa.info', '')}")
            if status == 200 and 'errmsg' not in body and 'Not Found' not in body:
                print(f"  BODY: {body}")
            elif status == 200:
                try:
                    j = r.json()
                    if j.get('error'):
                        print(f"  ERROR: {j.get('errmsg', j.get('message', ''))}")
                except:
                    print(f"  BODY: {body[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

# Try alternative: use the FOFA web app's internal API by examining the Nuxt build
print("\n=== Fetching FOFA v5 Nuxt data API ===")
try:
    r = s.get("https://fofa.info/search", timeout=15, verify=False)
    print(f"  Status: {r.status_code}")
    # Look for __NUXT__ data
    import re
    nuxt_matches = re.findall(r'__NUXT__.*?=.*?</script>', r.text, re.DOTALL)
    print(f"  Nuxt data blocks: {len(nuxt_matches)}")
    # Look for API routes in the page
    api_routes = re.findall(r'["\'](/api/[^\s"\']+)', r.text)
    print(f"  API routes in page: {api_routes[:10]}")
except Exception as e:
    print(f"  Error: {e}")
