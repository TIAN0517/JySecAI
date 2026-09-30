#!/usr/bin/env python3
"""Phase 23: Extract EPCR auth config + AuthService/LoginCtrl/app.js."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
PROXY = {"https": "socks5h://202.160.76.154:11085"}

s = requests.Session()
s.headers.update(HEADERS)
s.verify = False
s.proxies = PROXY

BASE = "https://118.163.107.93:4000"

# Get key JS files
for js_file in ["js/AuthService.js", "js/LoginCtrl.js", "js/app.js", "js/publicConfig.js",
                 "js/authInterceptorConfig.config.js", "js/services.js", "js/MenuCtrl.js"]:
    url = f"{BASE}/{js_file}"
    r = s.get(url, timeout=10)
    print(f"\n{'='*60}")
    print(f"=== {js_file} -> {r.status_code}, len={len(r.text)} ===")
    print(f"{'='*60}")
    print(r.text[:3000])
    with open(f"tpe119_evidence/login_pages/{js_file.replace('/','_')}", "w") as f:
        f.write(r.text)

# Get the full HTML page and extract inline config
print(f"\n{'='*60}")
print("=== EPCR Root HTML - Full inline JS ===")
r = s.get(BASE + "/", timeout=10)
# Find all inline scripts with config
inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.S)
for i, script in enumerate(inline_scripts):
    if len(script.strip()) > 100:
        print(f"\n--- Inline Script {i+1} ({len(script)} chars) ---")
        print(script.strip()[:1000])

# Also extract template URLs
templates = re.findall(r'templateUrl:\s*["\']([^"\']+)["\']', r.text)
print(f"\nTemplate URLs: {templates[:20]}")
