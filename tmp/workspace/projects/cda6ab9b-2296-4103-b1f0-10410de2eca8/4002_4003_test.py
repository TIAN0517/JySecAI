import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== 4002 hospitalServer 端点枚举 ===\n")

test_paths = [
    '/',
    '/config',
    '/hospitals',
    '/hospital',
    '/hosp',
    '/api',
    '/version',
    '/health',
    '/status',
    '/events',
    '/socket.io',
]

for port, name in [(4002, 'hospitalServer'), (4003, 'doctorServer')]:
    print(f"\n=== {port} {name} ===\n")
    for path in test_paths:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=5, context=ctx)
            conn.request('GET', path)
            resp = conn.getresponse()
            body = resp.read()
            content_type = resp.getheader('Content-Type', '')
            print(f"  GET {path}: {resp.status} ({len(body)} bytes) {content_type}")
            if resp.status == 200 and len(body) < 500:
                print(f"    Body: {body.decode('utf-8', errors='replace')[:200]}")
            conn.close()
        except Exception as e:
            print(f"  GET {path}: Error {e}")

# 测试 4002/4003 的 POST 方法
print("\n=== POST 方法测试 ===\n")
for port, name in [(4002, 'hospitalServer'), (4003, 'doctorServer')]:
    print(f"\n{port} {name} POST:")
    test_paths_post = [
        '/hospitals',
        '/doctor',
        '/doctors',
        '/users',
        '/patients',
        '/cases',
        '/events',
    ]
    for path in test_paths_post:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=5, context=ctx)
            conn.request('POST', path, body='{}', headers={'Content-Type': 'application/json'})
            resp = conn.getresponse()
            body = resp.read().decode('utf-8', errors='replace')[:100]
            print(f"  POST {path}: {resp.status} {body[:50]}")
            conn.close()
        except Exception as e:
            print(f"  POST {path}: Error {e}")
