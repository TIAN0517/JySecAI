import http.client
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试 4005-4008 和 9000 端口
print('=== 4005-4008 和 9000 端口测试 ===')

# 4005 - monitorServer (HTTP)
print('1. Testing 4005 (monitorServer)...')
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 4005, timeout=10)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  GET /config: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        print(f'  Data: {data[:500]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')

# 4006 - merBridge (HTTP)
print('2. Testing 4006 (merBridge)...')
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 4006, timeout=10)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  GET /config: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        print(f'  Data: {data[:500]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')

# 4007 - statServer (HTTP)
print('3. Testing 4007 (statServer)...')
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 4007, timeout=10)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  GET /config: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        print(f'  Data: {data[:500]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')

# 4008 - mciServer (HTTP)
print('4. Testing 4008 (mciServer)...')
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 4008, timeout=10)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  GET /config: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        print(f'  Data: {data[:500]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')

# 9000 - printServer (HTTP)
print('5. Testing 9000 (printServer)...')
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 9000, timeout=10)
    conn.request('GET', '/config')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  GET /config: {resp.status} ({len(data)} bytes)')
    if resp.status == 200:
        print(f'  Data: {data[:500]}')
    conn.close()
except Exception as e:
    print(f'  Error: {e}')

# 测试 HTTPS 版本
print('\n6. Testing HTTPS versions...')
for port in [4005, 4006, 4007, 4008, 9000]:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=10, context=ctx)
        conn.request('GET', '/config')
        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')
        print(f'  HTTPS /{port}/config: {resp.status} ({len(data)} bytes)')
        if resp.status == 200:
            print(f'    Data: {data[:300]}')
        conn.close()
    except Exception as e:
        print(f'  HTTPS /{port}/config: Error - {e}')

# 测试常见端点
print('\n7. Testing common endpoints on all ports...')
endpoints = ['/', '/health', '/status', '/api', '/api/v1', '/version', '/info', '/metrics', '/docs']

for port in [4005, 4006, 4007, 4008, 9000]:
    print(f'  Port {port}:')
    for endpoint in endpoints:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=5, context=ctx)
            conn.request('GET', endpoint)
            resp = conn.getresponse()
            data = resp.read().decode('utf-8', errors='replace')
            if resp.status != 404:
                print(f'    GET {endpoint}: {resp.status} ({len(data)} bytes)')
            conn.close()
        except:
            pass
