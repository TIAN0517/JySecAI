import urllib.request, urllib.error, json, ssl

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
def req(method, path, data=None, base="https://ofa377.net", ct="application/json"):
    h={"User-Agent":UA["User-Agent"],"Accept":"application/json, text/plain, */*"}
    if data is not None:
        h["Content-Type"]=ct
    body=(json.dumps(data).encode() if data is not None else None)
    req_=urllib.request.Request(base+path, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=20, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

tests=[("GET","/api/v1/user"),("POST","/api/v1/login"),("POST","/api/v1/login/"),
       ("POST","/api/v2/register/"),("POST","/api/v2/register"),("GET","/api/"),
       ("GET","/api/v1"),("POST","/api/v1/login","")]
for t in tests:
    method,path=t[0],t[1]
    data=t[2] if len(t)>2 else ({"username":"x","password":"x","device_id":"d"} if method=="POST" else None)
    s,h,b=req(method,path,data)
    srv=h.get("Server","")
    cf=h.get("Cf-Ray","") or h.get("Server","")
    print(f"{method} {path} -> {s} | Server={srv} | {b[:120].decode(errors='ignore')}")
