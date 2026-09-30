#!/usr/bin/env python3
"""
Phase 3: FOFA search via relay/proxy and investigate port 18999.
The token path dicl79nhrtolm07vqxk03fcqjyt4nvxu may be a FOFA API relay token.
Try using it as an API key/token parameter.
"""
import requests
import json
import base64
import urllib3
import urllib.parse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_IP = "107.173.248.139"
TOKEN_PATH = "/dicl79nhrtolm07vqxk03fcqjyt4nvxu"
TOKEN_VALUE = "dicl79nhrtolm07vqxk03fcqjyt4nvxu"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# ===== Try port 18999 as FOFA relay =====
print("=" * 70)
print("Phase 3a: Investigating port 18999 as FOFA relay")
print("=" * 70)

# Maybe the token path IS the FOFA relay - try it with FOFA query params
queries = [
    "service119.tfd.gov.tw",
    "tfd.gov.tw",
    "epcr.tpf.gov.tw",
    "tpf.gov.tw",
]

for q in queries:
    enc = base64.b64encode(q.encode()).decode()
    
    # Try the token path as a relay endpoint with FOFA query params
    relay_urls = [
        # FOFA v1 search with token as key
        f"http://{TARGET_IP}:18999{TOKEN_PATH}?qbase64={enc}",
        f"http://{TARGET_IP}:18999{TOKEN_PATH}?key={TOKEN_VALUE}&qbase64={enc}",
        f"http://{TARGET_IP}:18999{TOKEN_PATH}?api_key={TOKEN_VALUE}&q={q}",
        f"http://{TARGET_IP}:18999{TOKEN_PATH}?token={TOKEN_VALUE}&q={q}",
        # Try the token path as the base, with standard FOFA paths
        f"http://{TARGET_IP}:18999{TOKEN_PATH}/api/v1/search/all?qbase64={enc}",
        f"http://{TARGET_IP}:18999{TOKEN_PATH}/v1/search/all?qbase64={enc}",
    ]
    
    print(f"\n[*] Query: {q}")
    for url in relay_urls:
        try:
            r = s.get(url, timeout=15, verify=False, allow_redirects=False)
            body = r.text[:200]
            print(f"  [{r.status_code}] {url.replace(f'http://{TARGET_IP}:18999', '')}")
            if r.status_code not in [403, 404]:
                print(f"    Body: {body}")
        except Exception as e:
            print(f"  ERR: {url} -> {e}")

# ===== Try port 18999 as HTTP proxy =====
print("\n" + "=" * 70)
print("Phase 3b: Try port 18999 as HTTP proxy")
print("=" * 70)

# Try using 18999 as a proxy
proxy_urls = [
    f"http://107.173.248.139:18999",
    f"socks5://107.173.248.139:18999",
    f"socks5h://107.173.248.139:18999",
]

for proxy_url in proxy_urls:
    print(f"\n[*] Trying as proxy: {proxy_url}")
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        r = s.get("https://fofoapi.com/api/v1/search/all?qbase64=c2VydmljZTExOS50ZmQuZ292LnR3",
                  timeout=15, verify=False, proxies=proxies, allow_redirects=False)
        print(f"  Status: {r.status_code}")
        print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")

# ===== Try FOFA with token parameter =====
print("\n" + "=" * 70)
print("Phase 3c: FOFA API with token parameter")
print("=" * 70)

for q in queries[:2]:
    enc = base64.b64encode(q.encode()).decode()
    fofa_urls = [
        f"https://api.fofa.info/v1/search/all?qbase64={enc}&token={TOKEN_VALUE}",
        f"https://api.fofa.info/v1/search/all?qbase64={enc}&key={TOKEN_VALUE}",
        f"https://api.fofa.info/v1/search/all?qbase64={enc}&api_key={TOKEN_VALUE}",
    ]
    for url in fofa_urls:
        try:
            r = s.get(url, timeout=15, verify=False)
            print(f"  [{r.status_code}] {url.replace('https://api.fofa.info', '')}")
            if r.status_code == 200:
                try:
                    j = r.json()
                    if not j.get("error"):
                        print(f"    SUCCESS: {json.dumps(j, indent=2, ensure_ascii=False)[:500]}")
                    else:
                        print(f"    Error: {j.get('errmsg', j.get('message', ''))}")
                except:
                    print(f"    Body: {r.text[:200]}")
        except Exception as e:
            print(f"    Error: {e}")

# ===== Try connecting to port 18999 with specific protocols =====
print("\n" + "=" * 70)
print("Phase 3d: Port 18999 protocol investigation")
print("=" * 70)

# Try WebSocket
import socket

# Raw TCP banner grab
print("[*] Raw TCP banner grab on port 18999:")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((TARGET_IP, 18999))
    # Try sending an HTTP request with the token path as Host
    request = f"GET {TOKEN_PATH} HTTP/1.1\r\nHost: {TARGET_IP}:18999\r\nAuthorization: Bearer {TOKEN_VALUE}\r\n\r\n"
    sock.send(request.encode())
    response = sock.recv(4096).decode(errors='replace')
    print(f"  Response: {response[:300]}")
    sock.close()
except Exception as e:
    print(f"  Error: {e}")

# Try with different auth methods
print("\n[*] Trying with Authorization headers:")
auth_types = [
    ("Bearer", f"Bearer {TOKEN_VALUE}"),
    ("Basic", f"Basic {base64.b64encode(TOKEN_VALUE.encode()).decode()}"),
    ("Token", f"Token {TOKEN_VALUE}"),
    ("X-API-Key", TOKEN_VALUE),
    ("X-Forwarded-For", "127.0.0.1"),
]

for header_name, header_val in auth_types:
    try:
        r = s.get(f"http://{TARGET_IP}:18999{TOKEN_PATH}",
                  timeout=10, verify=False, allow_redirects=False,
                  headers={header_name: header_val, "User-Agent": "Mozilla/5.0"})
        if r.status_code != 403:
            print(f"  [{r.status_code}] {header_name}: {header_val[:30]}")
            print(f"    Body: {r.text[:200]}")
        else:
            print(f"  [403] {header_name} (still forbidden)")
    except Exception as e:
        print(f"  ERR {header_name}: {e}")
