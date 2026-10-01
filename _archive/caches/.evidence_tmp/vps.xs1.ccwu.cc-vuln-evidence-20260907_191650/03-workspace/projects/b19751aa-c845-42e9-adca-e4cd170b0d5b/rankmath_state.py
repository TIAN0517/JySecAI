import urllib.request, urllib.error, urllib.parse, ssl, json

ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 Chrome/120.0"
BASE="https://ofa377.com.tw"
def req(path, data=None, method=None, rawbody=None, ctype=None, form=False):
    h={"User-Agent":UA,"Accept":"*/*","Connection":"close"}
    body=None
    if form and data is not None:
        body=urllib.parse.urlencode(data).encode(); h["Content-Type"]="application/x-www-form-urlencoded"
    elif data is not None:
        body=json.dumps(data).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+path, data=body, headers=h, method=method or ("POST" if body else "GET"))
    try:
        resp=urllib.request.urlopen(r, timeout=20, context=ctx); return resp.status, resp.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
    except Exception as e: return -1, str(e).encode()

print("=== saveModule: full state validation errors per type ===")
for label,state in [("bool true",True),("bool false",False),("str '1'","1"),("str '0'","0"),
                    ("str 'on'","on"),("int 1",1),("int 0",0),("array [1]",[1]),("array {}" ,"obj")]:
    if state=="obj": state={}
    s,b=req("/wp-json/rankmath/v1/saveModule", data={"module":"seo","state":state})
    t=b.decode(errors="ignore")
    # decode the state param message
    print(f"state={label:12} ST={s} :: {t[:200]}")

print("\n=== Save via form-encoded (in case JSON parsing differs) ===")
for state in ["1","0","true","false","on"]:
    s,b=req("/wp-json/rankmath/v1/saveModule", data={"module":"seo","state":state}, form=True)
    print(f"form state={state:6} ST={s} :: {b.decode(errors='ignore')[:160]}")

print("\n=== Try valid module names with state true (look for success) ===")
for mod in ["seo","seo_advanced","search","search_advanced","analytics","google_analytics","xml_sitemap","redirect","schema"]:
    s,b=req("/wp-json/rankmath/v1/saveModule", data={"module":mod,"state":True})
    print(f"module={mod:16} ST={s} :: {b.decode(errors='ignore')[:140]}")
