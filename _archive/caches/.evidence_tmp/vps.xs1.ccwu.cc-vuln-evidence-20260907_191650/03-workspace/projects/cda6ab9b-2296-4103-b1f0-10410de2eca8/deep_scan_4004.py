import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def http_get(port, path, headers=None):
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=10, context=ctx)
    conn.request('GET', path, headers=headers or {})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), body

def http_post(port, path, data=None, headers=None):
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=10, context=ctx)
    h = headers or {}
    h['Content-Type'] = 'application/json'
    conn.request('POST', path, body=json.dumps(data) if data else '{}', headers=h)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), body

print("=== 4004 authServer 深度测试 ===\n")

# 1. 测试 /login 不同参数
print("1. /login 参数变体测试:")
test_logins = [
    {"username": "admin", "password": "admin", "captcha": "1234"},
    {"username": "admin", "password": "admin", "captcha": "abcd"},
    {"username": "admin", "password": "123456", "captcha": "1234"},
    {"username": "test", "password": "test", "captcha": "1234"},
    {"user": "admin", "pass": "admin", "captcha": "1234"},
    {"Username": "admin", "Password": "admin", "Captcha": "1234"},
    {"username": "admin"},
    {"password": "admin"},
]

for data in test_logins:
    status, headers, body = http_post(4004, '/login', data)
    body_str = body.decode('utf-8', errors='replace')[:150]
    print(f"  {json.dumps(data)[:50]:50} -> {status}: {body_str}")

# 2. 测试 /ssoLogin 变体
print("\n2. /ssoLogin 变体测试:")
test_sso = [
    {"sessionId": "12345"},
    {"sessionId": "admin"},
    {"sessionId": "test"},
    {"SessionId": "12345"},
    {"session_id": "12345"},
    {"token": "12345"},
    {"ssoToken": "12345"},
    {},
]

for data in test_sso:
    status, headers, body = http_post(4004, '/ssoLogin', data)
    body_str = body.decode('utf-8', errors='replace')[:150]
    print(f"  {json.dumps(data)[:50]:50} -> {status}: {body_str}")

# 3. 测试 /refreshToken 变体
print("\n3. /refreshToken 变体测试:")
test_refresh = [
    {"refreshToken": "test123"},
    {"refreshToken": ""},
    {"token": "test123"},
    {"refresh_token": "test123"},
    {},
]

for data in test_refresh:
    status, headers, body = http_post(4004, '/refreshToken', data)
    body_str = body.decode('utf-8', errors='replace')[:150]
    print(f"  {json.dumps(data)[:50]:50} -> {status}: {body_str}")

# 4. 测试 /captcha 变体
print("\n4. /captcha 变体测试:")
test_captcha = [
    '/captcha',
    '/captcha?t=1234567890',
    '/captcha/1234',
    '/captchas',
    '/captcha/validate',
    '/verify',
]

for path in test_captcha:
    status, headers, body = http_get(4004, path)
    content_type = headers.get('Content-Type', '')
    print(f"  GET {path}: {status} ({len(body)} bytes) {content_type}")
    if status == 200 and 'image' in content_type:
        print(f"    -> Image captcha ({len(body)} bytes)")
    elif status == 200:
        body_str = body.decode('utf-8', errors='replace')[:100]
        print(f"    -> {body_str}")

# 5. 测试 /logout 变体
print("\n5. /logout 变体测试:")
test_logout = [
    {'Authorization': 'Bearer test123'},
    {'Authorization': 'Bearer invalid_token'},
    {},
]

for headers in test_logout:
    status, headers_resp, body = http_post(4004, '/logout', {}, headers)
    body_str = body.decode('utf-8', errors='replace')[:100]
    print(f"  POST /logout (auth={headers.get('Authorization', 'none')[:30]}): {status}: {body_str}")

# 6. 测试其他可能的端点
print("\n6. 其他端点测试:")
other_paths = [
    '/api',
    '/auth',
    '/users',
    '/user',
    '/sessions',
    '/session',
    '/tokens',
    '/token',
    '/validate',
    '/verify',
    '/check',
    '/health',
    '/status',
    '/info',
    '/version',
    '/debug',
    '/metrics',
    '/ping',
    '/ws',
    '/websockets',
]

for path in other_paths:
    status, headers, body = http_get(4004, path)
    body_str = body.decode('utf-8', errors='replace')[:50] if body else ''
    if status != 404:
        print(f"  GET {path}: {status} {body_str[:30]}")

# 7. 测试 Socket.IO 在 4004
print("\n7. Socket.IO 4004 测试:")
status, headers, body = http_get(4004, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')[:100]
print(f"  GET /socket.io/: {status}: {body_str}")

# 8. 测试 HTTP (非 HTTPS) 4004
print("\n8. HTTP (非 HTTPS) 4004:")
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 4004, timeout=5)
    conn.request('GET', '/login')
    resp = conn.getresponse()
    body = resp.read()
    print(f"  HTTP GET /login: {resp.status} ({len(body)} bytes)")
    conn.close()
except Exception as e:
    print(f"  HTTP GET /login: Error {e}")
