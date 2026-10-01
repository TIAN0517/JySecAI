import urllib.request, urllib.error, json, ssl

BASE="https://ofa377.com.tw"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def get(path, headers=None, data=None, method=None):
    url=BASE+path
    h=dict(UA)
    if headers: h.update(headers)
    body=None
    if data is not None:
        body=data.encode() if isinstance(data,str) else data
        h["Content-Type"] = h.get("Content-Type","application/x-www-form-urlencoded")
    req=urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req, timeout=20, context=ctx)
        b=r.read()
        return r.status, dict(r.headers), b
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {"err":str(e)}, str(e).encode()

paths=["/wp-login.php","/wp-admin/","/xmlrpc.php","/wp-json/wp-site-health/v1/tests",
       "/wp-config.php.bak","/wp-config.php~","/wp-config.php.old","/.git/config",
       "/wp-content/debug.log","/wp-content/uploads/","/backup.zip","/wp.zip",
       "/wp-content/backup-db/","/wp-content/plugins/","/wp-content/themes/",
       "/feed/","/wp-json/","/wp-json/wp/v2/posts","/wp-json/rankmath/v1",
       "/wp-json/wordfence/v1","/wp-json/jetpack/v4","/wp-json/wp/v2/types"]
print("=== GET probes ===")
for p in paths:
    s,h,b=get(p)
    ct=h.get("Content-Type","")[:40]
    print(f"{s}\t{p}\tlen={len(b)}\t{ct}")

print("\n=== xmlrpc methods.list ===")
xml='<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params/></methodCall>'
s,h,b=get("/xmlrpc.php", data=xml)
print("status",s, "len", len(b))
print(b[:600].decode(errors="ignore"))

print("\n=== site-health tests (plugin versions) ===")
s,h,b=get("/wp-json/wp-site-health/v1/tests")
print("status",s)
try:
    d=json.loads(b)
    for t in d.get("data",[]):
        print(" -",t.get("label") or t.get("type") or t.get("type","?"))
except Exception as e:
    print(b[:800].decode(errors="ignore"))
