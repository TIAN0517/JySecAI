#!/usr/bin/env python3
"""Fetch full HTML + index of JS files from EPCR 4000 main site."""
import ssl
import urllib.request
import urllib.error
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.status
            headers = dict(resp.headers)
            body = resp.read()
            return code, headers, body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""
    except Exception as e:
        return None, {}, str(e).encode()

# 1. Get main 4000 HTML
print("=" * 80)
print("[1] GET https://epcr.tpf.gov.tw:4000/")
print("=" * 80)
code, headers, body = fetch("https://epcr.tpf.gov.tw:4000/")
print(f"HTTP {code}")
print(f"Headers: {headers}")
print(f"Body length: {len(body)}")
with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/epcr_main_4000.html", "wb") as f:
    f.write(body)

# Extract JS / CSS hrefs
hrefs = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', body.decode('utf-8', errors='ignore'))
print(f"\nExtracted {len(hrefs)} hrefs:")
for h in hrefs[:50]:
    print(f"  {h}")

# 2. Get AuthService.js (key file from 4000 - probably talks to 4004)
print("\n" + "=" * 80)
print("[2] GET https://epcr.tpf.gov.tw:4000/js/AuthService.js")
print("=" * 80)
code2, headers2, body2 = fetch("https://epcr.tpf.gov.tw:4000/js/AuthService.js")
print(f"HTTP {code2}")
print(f"Body length: {len(body2)}")
with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/epcr_4000_AuthService.js", "wb") as f:
    f.write(body2)

# 3. Get 4004 main HTML
print("\n" + "=" * 80)
print("[3] GET https://epcr.tpf.gov.tw:4004/")
print("=" * 80)
code3, headers3, body3 = fetch("https://epcr.tpf.gov.tw:4004/")
print(f"HTTP {code3}")
print(f"Headers: {headers3}")
print(f"Body length: {len(body3)}")
with open("/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/epcr_auth_4004.html", "wb") as f:
    f.write(body3)

# Extract JS / CSS hrefs
hrefs3 = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', body3.decode('utf-8', errors='ignore'))
print(f"\nExtracted {len(hrefs3)} hrefs:")
for h in hrefs3[:50]:
    print(f"  {h}")