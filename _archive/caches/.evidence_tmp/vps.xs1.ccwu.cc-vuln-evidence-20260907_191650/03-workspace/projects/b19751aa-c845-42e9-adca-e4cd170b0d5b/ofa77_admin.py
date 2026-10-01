import urllib.request, urllib.error, json, ssl, re

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36","Accept":"text/html,*/*"}
def req(method, url, data=None, headers=None):
    h=dict(UA)
    if headers: h.update(headers)
    body=None
    if data is not None:
        h["Content-Type"]="application/json"
        body=json.dumps(data).encode()
    req_=urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        r=urllib.request.urlopen(req_, timeout=20, context=ctx)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()

base="https://ofa77.shop"
# admin + laravel + unishop candidate paths
cands=["/admin","/admin/","/admin/login","/index.php/admin","/admin/index","/admin/index.php",
 "/console","/telescope","/horizon","/_debugbar","/debug","/api/admin","/api/admin/login",
 "/admin/api","/manager","/backend","/sys","/system","/login","/api/login","/api/v1/admin/login",
 "/install","/up.php","/artisan","/.env.bak","/web.config","/robots.txt","/sitemap.xml",
 "/api/v1","/api/v2","/module","/views","/uploads","/storage","/public"]
print(f"{'PATH':32} {'ST':>4} {'LEN':>7}  TYPE")
for p in cands:
    s,b=req("GET", base+p)
    t=b.decode(errors="ignore")
    kind = "DEBUGDUMP" if "Sfdump" in t else ("HTML" if "<html" in t.lower() or "<!doctype" in t.lower() else "OTHER")
    if s not in (None,404):
        marker=""
        if "login" in t.lower() and kind!="DEBUGDUMP": marker="**LOGIN-HTML**"
        if kind!="DEBUGDUMP" and s==200: marker="**REAL-200**"
        print(f"{p:32} {s if s else 'ERR':>4} {len(b):>7}  {kind} {marker} :: {t[:50].strip()}")

print("\n=== robots.txt / sitemap content (if real) ===")
for p in ["/robots.txt","/sitemap.xml","/.env"]:
    s,b=req("GET", base+p)
    t=b.decode(errors="ignore")
    if "Sfdump" not in t:
        print(f"--- {p} ({s}) ---\n{t[:800]}")
