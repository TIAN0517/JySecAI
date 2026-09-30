#!/usr/bin/env python3
"""
Phase 3e: Deeper investigation of port 18999.
Try different Host headers, virtual host enumeration,
and FOFA relay via fofoapi.com with token path.
"""
import requests
import json
import base64
import urllib.parse
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_IP = "107.173.248.139"
TOKEN_PATH = "/dicl79nhrtolm07vqxk03fcqjyt4nvxu"
TOKEN_VALUE = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# ===== Try different Host headers on port 18999 =====
print("=" * 70)
print("Phase 3e: Host header / vhost enumeration on port 18999")
print("=" * 70)

host_headers = [
    "localhost",
    "127.0.0.1",
    "fofoapi.com",
    "api.fofa.info",
    "fofa.info",
    "service119.tfd.gov.tw",
    "epcr.tpf.gov.tw",
    f"{TARGET_IP}",
    f"{TARGET_IP}:18999",
    "107.173.248.139:18999",
    "relay.fofa.io",
    "proxy.fofa.io",
]

for host in host_headers:
    try:
        r = s.get(f"http://{TARGET_IP}:18999/",
                  timeout=5, verify=False, allow_redirects=False,
                  headers={"Host": host})
        if r.status_code != 403:
            print(f"  [{r.status_code}] Host: {host} -> DIFFERENT STATUS!")
            print(f"    Body: {r.text[:200]}")
        else:
            print(f"  [403] Host: {host}")
    except Exception as e:
        print(f"  ERR Host: {host} -> {e}")

# Also try the token path with different Host headers
print("\n[*] Token path with different Host headers:")
for host in ["localhost", "127.0.0.1", "fofoapi.com", "api.fofa.info"]:
    try:
        r = s.get(f"http://{TARGET_IP}:18999{TOKEN_PATH}",
                  timeout=5, verify=False, allow_redirects=False,
                  headers={"Host": host})
        if r.status_code != 403:
            print(f"  [{r.status_code}] Host: {host} -> DIFFERENT!")
            print(f"    Body: {r.text[:200]}")
        else:
            print(f"  [403] Host: {host}")
    except Exception as e:
        print(f"  ERR Host: {host} -> {e}")

# ===== Try FOFA search via fofoapi.com relay =====
print("\n" + "=" * 70)
print("Phase 3f: FOFA search via fofoapi.com with token")
print("=" * 70)

queries = ["service119.tfd.gov.tw", "tfd.gov.tw", "epcr.tpf.gov.tw"]

for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    print(f"\n[*] Query: {q}")
    
    # Try fofoapi.com with token as part of the path
    urls = [
        f"https://fofoapi.com/api/v1/search/all?qbase64={enc}&token={TOKEN_VALUE}",
        f"https://fofoapi.com/api/v1/search/all?qbase64={enc}&key={TOKEN_VALUE}",
        f"https://fofoapi.com/{TOKEN_PATH}/api/v1/search/all?qbase64={enc}",
        f"https://fofoapi.com/{TOKEN_PATH}?qbase64={enc}",
        f"https://fofoapi.com/{TOKEN_PATH}?q={q}",
        # Try the fofoapi.com with the token path
        f"https://fofoapi.com/?qbase64={enc}&token={TOKEN_VALUE}",
    ]
    
    for url in urls:
        try:
            r = s.get(url, timeout=15, verify=False, allow_redirects=False)
            print(f"  [{r.status_code}] {url.replace('https://fofoapi.com', '')}")
            if r.status_code == 200:
                try:
                    j = r.json()
                    if j.get("error"):
                        print(f"    Error: {j.get('errmsg', j.get('message', ''))}")
                    else:
                        print(f"    SUCCESS: {json.dumps(j, indent=2, ensure_ascii=False)[:500]}")
                except:
                    body = r.text[:300]
                    print(f"    Body: {body}")
        except Exception as e:
            print(f"    Error: {e}")

# ===== Try FOFA web search scraping (Nuxt app) =====
print("\n" + "=" * 70)
print("Phase 3g: FOFA web search page investigation")
print("=" * 70)

# The FOFA web app at fofoapi.com is a Nuxt SPA
# Try to find the actual search API by examining the Nuxt data
# Nuxt apps often use a _nuxt_data endpoint
for path in ["/search", "/search/", "/search?q=service119"]:
    url = f"https://fofoapi.com{path}"
    try:
        r = s.get(url, timeout=15, verify=False, allow_redirects=False)
        print(f"  [{r.status_code}] {path} -> {r.text[:200]}")
    except Exception as e:
        print(f"  [{path}] Error: {e}")

# Try to find the Nuxt API route by examining the JS bundle
print("\n[*] Examining Nuxt JS bundle for API routes:")
r = s.get("https://v5static.fofa.info/_nuxt/Bw0mZRLA.js", timeout=15, verify=False)
if r.status_code == 200:
    # Search for API endpoint patterns
    text = r.text
    api_patterns = re.findall(r'(/api/[a-zA-Z0-9_/.-]+)', text)
    search_patterns = re.findall(r'(/search[a-zA-Z0-9_/.-]*)', text)
    base64_patterns = re.findall(r'(qbase64|base64)', text)
    print(f"  API patterns in JS: {api_patterns[:20]}")
    print(f"  Search patterns: {search_patterns[:10]}")
    print(f"  Base64 mentions: {base64_patterns[:5]}")
    
    # Also search for token-related code
    token_refs = re.findall(r'(token|key|auth|header|Authorization)', text)
    print(f"  Token-related: {token_refs[:20]}")
    
    # Search for proxy/relay references
    relay_refs = re.findall(r'(proxy|relay|redirect)', text)
    print(f"  Relay references: {relay_refs[:10]}")
else:
    print(f"  JS bundle status: {r.status_code}")
