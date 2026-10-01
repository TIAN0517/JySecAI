import urllib.request, urllib.error, json, ssl

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36","Accept":"application/json, text/plain, */*"}
def req(method, path, data=None, base="https://ofa377.net/api", headers=None):
    h=dict(UA)
    if headers: h.update(headers)
    if data is not None:
        h["Content-Type"]="application/json"
    body=json.dumps(data).encode() if data is not None else None
    req_=urllib.request.Request(base+path, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=25, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

print("=== PUBLIC GET endpoints (no auth) ===")
for p in ["/v1/info","/v1/announ","/v1/carousel","/v1/contact","/v1/games","/v1/online","/v1/promo","/v2/game/turnover_rankings"]:
    s,h,b=req("GET",p)
    print(f"GET {p} -> {s} :: {b[:200].decode(errors='ignore')}")

print("\n=== POST endpoints (no auth, empty/minimal body) ===")
for p,d in [("/v1/login",{"username":"test","password":"test","device_id":"d1"}),
            ("/v2/register/",{"username":"cybtest1","password":"Passw0rd!1"}),
            ("/v2/forgot",{"email":"a@b.com"}),
            ("/v2/sms/send",{"phone_number":"+886912345678"}),
            ("/v2/verify_email",{"email":"a@b.com","code":"123456"})]:
    s,h,b=req("POST",p,d)
    print(f"POST {p} -> {s} :: {b[:250].decode(errors='ignore')}")
