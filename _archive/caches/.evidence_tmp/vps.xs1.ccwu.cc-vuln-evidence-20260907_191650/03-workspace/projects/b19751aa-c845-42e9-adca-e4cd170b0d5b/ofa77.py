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

base="https://ofa77.shop"
print("=== ofa77.shop homepage ===")
s,h,b=req("GET", base+"/")
print(s, "Server:", h.get("Server"), "X-Powered-By:", h.get("X-Powered-By"), "len:", len(b))
print(b[:600].decode(errors="ignore"))

print("\n=== ofa77.shop /api/v1/login full ===")
s,h,b=req("POST", base+"/api/v1/login", {"username":"t","password":"t"})
print(s, "len:", len(b))
txt=b.decode(errors="ignore")
# show key markers
for marker in ["Sfdump","_profiler","_wdt","profiler","Symfony","XDEBUG","PHP","Exception","stack","trace","token","password","password_hash","query","SELECT","session","cache"]:
    if marker.lower() in txt.lower():
        idx=txt.lower().find(marker.lower())
        print(f"  [{marker}] ...{txt[max(0,idx-40):idx+120]}...")

print("\n=== Symfony debug/profiler probes on ofa77.shop ===")
for p in ["/_profiler","/ _profiler","/profiler","/_wdt","/_profiler/home","/_profiler/search?q=1","/api/v1/login","/api/","/api","/_ignore","/config","/.env","/wp-json","/api/v1/info","/api/v1/user"]:
    p=p.replace(" ","")
    s,h,b=req("GET", base+p, None)
    print(f"GET {p:28} -> {s} len={len(b)} :: {b[:90].decode(errors='ignore')}")
