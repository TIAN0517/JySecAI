import urllib.request, urllib.error, json, ssl

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36","Accept":"*/*",
    "Origin":"https://ofa377.net","Referer":"https://ofa377.net/"}
def req(method, path, data=None, base="https://ofa377.net/api"):
    h=dict(UA)
    if data is not None: h["Content-Type"]="application/json"
    body=json.dumps(data).encode() if data is not None else None
    req_=urllib.request.Request(base+path, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=20, context=ctx)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()

routes=[
 ("GET","/v1/info"),("GET","/v1/user"),("GET","/v1/user/wallet"),("GET","/v1/user/record/bet"),
 ("GET","/v1/user/friends"),("GET","/v2/user/vip"),("GET","/v2/verify_email"),
 ("POST","/v1/login"),("POST","/v2/register/"),("POST","/v2/forgot"),("POST","/v2/sms/send"),
 ("POST","/v2/verify_email"),("POST","/v1/user/bank"),("POST","/v1/user/promo"),
 ("POST","/v1/user/wallet"),("POST","/v1/user/wallet/withdrawal"),("POST","/v1/user/promo/order"),
 ("PUT","/v1/user"),("PATCH","/v1/user"),("PUT","/v1/user/letter"),
]
d={"username":"u","password":"p","device_id":"d"}
for m,p in routes:
    payload = d if m in ("POST","PUT","PATCH") else None
    if p=="/v2/verify_email": payload={"email":"a@b.com"}
    s,b=req(m,p,payload)
    print(f"{m:6} {p:38} -> {s} :: {b[:70].decode(errors='ignore')}")
