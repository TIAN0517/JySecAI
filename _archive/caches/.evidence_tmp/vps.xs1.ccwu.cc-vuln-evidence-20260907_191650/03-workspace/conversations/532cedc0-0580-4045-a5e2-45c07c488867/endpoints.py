import requests, urllib3
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0"})
# 登录/认证/TFA 相关端点
paths=["/login","/login2FA","/tfa/register","/tfa/requestOtp","/tfa/verify",
  "/api/login","/auth/login","/login/2fa","/twofa","/2fa","/otp","/verify",
  "/refreshToken","/token","/logout","/tfa/unregister","/tfa/status",
  "/Users","/users","/branches","/Branches","/dispatch","/Dispatch",
  "/admin","/console","/api","/v1/login","/login3"]
print(f"{'METHOD'} {'PATH':40s} {'CODE'} {'SIZE'}  BODY")
for p in paths:
    for m in ["GET","POST"]:
        try:
            if m=="GET":
                r=s.get(BASE+p,timeout=8)
            else:
                r=s.post(BASE+p,json={},timeout=8)
            print(f"{m:6s} {p:40s} {r.status_code:5d} {len(r.content):6d}  {r.text[:55].replace(chr(10),' ')}")
        except Exception as e:
            print(f"{m:6s} {p:40s}  ERR {repr(e)[:40]}")
print("DONE")
