import http.client
import json
import ssl
from urllib.parse import quote

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试 4001 /events 的更多端点
print('=== 4001 /events 深入测试 ===')

# 1. 测试不同 ID
for id in [1, 100, 567200, 567201, 567202]:
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
    conn.request('GET', f'/events/{id}')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'GET /events/{id} -> {resp.status}')
    if resp.status == 200:
        print(f'  {data[:150]}')
    conn.close()

# 2. 测试更多查询参数
print('2. GET /events?TypeOfEventTxt=startofPCDT')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?TypeOfEventTxt=startofPCDT')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 3. 测试更多查询参数
print('3. GET /events?Caption=Start%20of%20PCDT')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Caption=Start%20of%20PCDT')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 4. 测试更多查询参数
print('4. GET /events?Value=120')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Value=120')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 5. 测试更多查询参数
print('5. GET /events?Unit=1')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Unit=1')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 6. 测试更多查询参数
print('6. GET /events?Systolic=120')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Systolic=120')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 7. 测试更多查询参数
print('7. GET /events?Diastolic=80')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Diastolic=80')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 8. 测试更多查询参数
print('8. GET /events?Mean=100')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?Mean=100')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()
