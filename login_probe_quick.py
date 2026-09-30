#!/usr/bin/env python3
"""
Phase 7 quick: Probe login endpoints on the most critical hosts.
Lower timeout, focused on the key 119 dispatch/login systems.
"""
import re
import requests, json, time, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
})

# Quick probe - low timeout
login_paths = [
    "/", "/login", "/admin/login", "/api/login", "/auth/login",
    "/citizen/auth/genToken", "/auth/genToken", "/auth/fetchServerData",
    "/api/getUserToken", "/user/login", "/oauth/token", "/sso/login",
    "/cas/login", "/admin", "/console", "/dashboard",
    "/swagger-ui.html", "/api-docs", "/config", "/config.json",
    "/robots.txt", "/favicon.ico", "/.env",
    "/citizenCase/caseList", "/caseList", "/dispatch",
    "/index.php", "/index.html",
    "/Socket.io", "/socket.io/",
]

# Critical hosts in priority order
critical_hosts = [
    "https://service119.tfd.gov.tw/service119",
    "https://appservice119.tfd.gov.tw",
    "https://www.119.gov.taipei",
    "https://fsm.119.gov.taipei",
    "https://taipeiciiis.119.gov.taipei",
    "https://taipeiciiis-dashboard.119.gov.taipei",
    "https://service119.119.gov.taipei",
    "https://www.af-search.119.gov.taipei",
    "https://camcall.119.gov.taipei",
    "https://tpertc.tfd.gov.tw",
    "https://mer2.tpf.gov.tw",
    "https://epcr.tpf.gov.tw",
    "https://119api.tpf.gov.tw",
    "https://119appcaseapi.tpf.gov.tw",
    "https://119epcrapi.tpf.gov.tw",
    "https://smartems.tpf.gov.tw",
    "https://mntfd119web.tpf.gov.tw",
    "https://trauma.tfd.gov.tw",
    "https://gis119.tfd.gov.tw",
    "https://taipeiepcr.tfd.gov.tw",
]

print("=" * 70)
print("QUICK LOGIN ENDPOINT PROBE - CRITICAL 119 HOSTS")
print("=" * 70)

for base in critical_hosts:
    try:
        r = s.get(base, timeout=8, verify=False, allow_redirects=False)
    except:
        r = None
    
    if r is None:
        print(f"\n[--] {base} - unreachable")
        continue
    
    status = r.status_code
    length = len(r.text)
    server = r.headers.get("Server", "").strip()[:60]
    title = ""
    if r.text and "<title>" in r.text.lower():
        t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
        if t:
            title = t.group(1)[:80].strip()
    
    # Only probe sub-paths for interesting hosts (200, 302, 401)
    marker = ""
    if status == 200:
        marker = " <-- LIVE"
    elif status in [301, 302, 307, 308]:
        marker = f" <-- redirect->{r.headers.get('Location', '')}"
    elif status in [401, 403]:
        marker = f" (auth:{status})"
    
    print(f"  [{status}] {base} ({length}b) [{server}] {title}{marker}")
    
    # If host is responsive (not 403/404), probe login paths
    if status not in [404, 502, 503]:
        for path in login_paths:
            url = f"{base}{path}"
            try:
                r = s.get(url, timeout=5, verify=False, allow_redirects=False)
                if r.status_code in [200, 302, 301, 401, 403]:
                    s2 = r.status_code
                    l2 = len(r.text) if r.text else 0
                    loc = r.headers.get("Location", "").strip()[:100]
                    # Only show non-trivial responses
                    if s2 == 200 and l2 > 100:
                        t2 = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
                        t2 = t2.group(1)[:60].strip() if t2 else ""
                        print(f"      -> [{s2}] {path} ({l2}b) {t2}")
                    elif s2 in [302, 301] and loc:
                        print(f"      -> [{s2}] {path} -> {loc}")
                    elif s2 in [401, 403]:
                        print(f"      -> [{s2}] {path} (auth required)")
            except:
                pass
        time.sleep(0.1)

print("\n[*] Done")
