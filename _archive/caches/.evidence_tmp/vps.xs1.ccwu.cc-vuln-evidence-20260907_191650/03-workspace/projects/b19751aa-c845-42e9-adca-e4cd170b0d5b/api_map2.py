import urllib.request, urllib.error, json, ssl

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36","Accept":"*/*"}
def req(method, url, data=None, ct="application/json", headers=None):
    h=dict(UA)
    if headers: h.update(headers)
    if data is not None: h["Content-Type"]=ct
    body=json.dumps(data).encode() if isinstance(data,(dict,list)) else (data.encode() if isinstance(data,str) else data)
    req_=urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=20, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

print("=== 301 Location for PUT /v1/user ===")
s,h,b=req("PUT","https://ofa377.net/api/v1/user",{"username":"x"})
print(s, "Location:", h.get("Location"), "::", b[:80].decode(errors="ignore"))

print("\n=== game-provider server.csogmes168.com/api/advertise ===")
for m in ["GET","POST"]:
    s,h,b=req(m,"https://server.csogmes168.com/api/advertise", {} if m=="POST" else None)
    print(m, s, "Server:", h.get("Server"), "::", b[:200].decode(errors="ignore"))

print("\n=== related domains: /api/v1/info (liveness) + /api/v1/login (auth) ===")
for dom in ["ofa377.net","www.ofa377.net","ofa168.net","ofa168my.net","ofa88kh.net","ofa77.shop","www.ofa88kh.net"]:
    base=f"https://{dom}"
    si=req("GET", base+"/api/v1/info")
    li=req("POST", base+"/api/v1/login", {"username":"t","password":"t","device_id":"d"})
    print(f"{dom:20} info={si[0]} login={li[0]} loginbody={li[2][:60].decode(errors='ignore')}")
