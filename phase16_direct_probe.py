#!/usr/bin/env python3
"""Phase 16: Direct HTTP probing of accessible 210.69.x.x hosts (no proxy needed).
These are Taipei City Government data center IPs - directly routable.
Focus on finding login endpoints with actual forms."""
import requests, urllib3, re, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Directly accessible hosts (210.69.x.x range = Taipei City Government)
ACCESSIBLE_HOSTS = [
    "https://210.69.43.103",       # service119.tfd.gov.tw
    "https://210.69.43.112",       # appservice119.tfd.gov.tw
    "https://210.69.43.114",       # tpertc.tfd.gov.tw
    "https://210.69.42.9",         # fsm.119.gov.taipei
    "https://210.69.42.55",        # www.af-search.119.gov.taipei
    "https://210.69.43.127",       # taipeiciiis.119.gov.taipei
    "https://210.69.43.129",       # taipeiciiis-dashboard.119.gov.taipei
]

LOGIN_PATHS = [
    "/", "/login", "/Login", "/admin/login", "/admin", "/user/login",
    "/api/login", "/auth/login", "/signin", "/index.php", "/index.html",
    "/default.aspx", "/home", "/account/login", "/account",
]

results = []
for host in ACCESSIBLE_HOSTS:
    for path in LOGIN_PATHS:
        url = host + path
        try:
            r = requests.get(url, headers=HEADERS, verify=False, timeout=8, allow_redirects=True)
            # Check if response has login form indicators
            text_lower = r.text.lower()
            has_form = "<form" in text_lower
            has_password = "password" in text_lower or "密碼" in r.text
            has_username = "username" in text_lower or "帳號" in r.text or "account" in text_lower
            has_login = "login" in text_lower or "登入" in r.text or "signin" in text_lower
            
            if has_form and (has_password or has_login) and r.status_code == 200:
                t = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
                result = {
                    "url": url,
                    "status": r.status_code,
                    "server": r.headers.get("Server", ""),
                    "title": t.group(1).strip()[:200] if t else "",
                    "content_length": len(r.text),
                    "has_form": has_form,
                    "has_password": has_password,
                    "has_username": has_username,
                    "login_indicators": sum([has_form, has_password, has_username, has_login]),
                }
                results.append(result)
                # Save the HTML
                safe_name = host.replace("https://", "").replace(":", "_") + path.replace("/", "_")
                with open(f"tpe119_evidence/login_pages/{safe_name}.html", "w") as f:
                    f.write(r.text[:8000])
                print(f"[{len(results)}] {url} -> {r.status_code} | {result['title'][:50]} | form={has_form} pw={has_password}")
        except Exception as e:
            pass

with open("tpe119_evidence/live_login_endpoints.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nTotal login endpoints found: {len(results)}")
print(f"Results saved to tpe119_evidence/live_login_endpoints.json")
