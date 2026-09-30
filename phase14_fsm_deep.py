#!/usr/bin/env python3
"""Phase 14: Deep probe fsm.119.gov.taipei and af-search via proxy."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = {"https": "socks5h://202.160.76.155:11084"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# fsm login page via proxy
r = requests.get("https://fsm.119.gov.taipei/w/fsm119/index", proxies=PROXY, headers=HEADERS, verify=False, timeout=30, allow_redirects=True)
print(f"[fsm.119.gov.taipei/w/fsm119/index] Status: {r.status_code}")
print(f"  Server: {r.headers.get('Server', 'N/A')}")
print(f"  Length: {len(r.text)} bytes")
t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
print(f"  Title: {t.group(1).strip() if t else 'N/A'}")
# Check for login form elements
print(f"  Has <form>: {'<form' in r.text.lower()}")
print(f"  Has password: {'password' in r.text.lower()}")
print(f"  Has username: {'username' in r.text.lower() or '帳號' in r.text or 'account' in r.text.lower()}")
# Save the HTML
with open("tpe119_evidence/fsm_login_page.html", "w") as f:
    f.write(r.text[:8000])
print("  Saved to tpe119_evidence/fsm_login_page.html")
print()

# Also get the .env content from fsm
r2 = requests.get("https://fsm.119.gov.taipei/.env", proxies=PROXY, headers=HEADERS, verify=False, timeout=15)
print(f"[fsm.119.gov.taipei/.env] Status: {r2.status_code}")
print(f"  Content-Type: {r2.headers.get('Content-Type', 'N/A')}")
print(f"  Content: {r2.text[:500]}")

# af-search admin login
r3 = requests.get("https://www.af-search.119.gov.taipei/admin/login", headers=HEADERS, verify=False, timeout=15, allow_redirects=True)
print(f"\n[af-search/admin/login] Status: {r3.status_code}")
print(f"  Server: {r3.headers.get('Server', 'N/A')}")
print(f"  Length: {len(r3.text)} bytes")
t3 = re.search(r'<title[^>]*>(.*?)</title>', r3.text, re.I | re.S)
print(f"  Title: {t3.group(1).strip() if t3 else 'N/A'}")
with open("tpe119_evidence/afsearch_login_page.html", "w") as f:
    f.write(r3.text[:8000])
print("  Saved to tpe119_evidence/afsearch_login_page.html")

# Get the SPA JS bundle to find actual API endpoints
js_match = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r3.text)
if js_match:
    print(f"  JS files found: {js_match[:5]}")
