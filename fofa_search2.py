#!/usr/bin/env python3
"""
FOFA search attempt via v5 API endpoints.
Also checks the FOFA web app's embedded API calls.
"""
import requests, json, base64, urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://fofa.info/",
    "Origin": "https://fofa.info",
}

queries = [
    "service119.tfd.gov.tw",
    "tfd.gov.tw",
    "epcr.tpf.gov.tw",
    "\"119\" \"dispatch\" site:tw",
    "tpf.gov.tw",
    "twd.gov.tw 119",
]

for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    print(f"\n=== Query: {q} (b64: {enc}) ===")
    
    # Try v1 search/all
    urls = [
        f"https://api.fofa.info/v1/search/all?qbase64={enc}",
        f"https://fofa.info/api/v1/search/all?qbase64={enc}",
        f"https://fofa.info/api/v1/search/all?q={urllib.parse.quote(q)}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15, verify=False)
            print(f"  {url.replace('https://', '')} -> {r.status_code} | {r.text[:200]}")
        except Exception as e:
            print(f"  {url.replace('https://', '')} -> Error: {e}")

# Also try to get FOFA's search API by examining their JS bundle
print("\n=== Fetching FOFA web app to find API endpoints ===")
try:
    r = requests.get("https://fofa.info/", headers=headers, timeout=15, verify=False)
    print(f"Status: {r.status_code}")
    # Look for API endpoints in the HTML
    text = r.text
    import re
    api_matches = re.findall(r'(/api/[^\s"\']+)', text)
    print(f"API endpoints found in HTML: {api_matches[:10]}")
    # Look for JS bundle URLs
    js_matches = re.findall(r'src=["\']([^"\']*\.js[^"\']*)', text)
    print(f"JS bundles found: {js_matches[:5]}")
except Exception as e:
    print(f"Error: {e}")
