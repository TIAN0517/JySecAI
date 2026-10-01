import http.client
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== Socket.IO v5 (带错误处理) ===\n")

def safe_request(port, method, path, body=None, headers=None, timeout=30):
    """安全请求，捕获 RemoteDisconnected"""
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=timeout, context=ctx)
        if method == 'GET':
            conn.request('GET', path, headers=headers or {})
        else:
            h = headers or {}
            h['Content-Type'] = 'text/plain'
            conn.request('POST', path, body=body, headers=h)
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')
        conn.close()
        return resp.status, resp_body
    except http.client.RemoteDisconnected:
        return 'REMOTE_DISCONN', ''
    except Exception as e:
        return 'ERROR', str(e)

# 1. 获取 SID
print("1. 获取 4000 SID:")
status, body = safe_request(4000, 'GET', '/socket.io/?EIO=4&transport=polling')
print(f"  Status: {status}")
print(f"  Body: {body}")

import re
match = re.search(r'0\{.*?\}', body)
if not match:
    print("  No SID found")
    exit()

handshake_data = json.loads(match.group(0)[1:])
sid = handshake_data.get('sid', '')
print(f"  SID: {sid}")

# 2. 测试 join room
print("\n2. Join room 测试:")
test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']

for room in test_rooms:
    msg = f'42["{room}"]'
    status, body = safe_request(4000, 'POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body=msg)
    print(f"  JOIN {room:12} -> {status} {body[:80]}")
    time.sleep(2)

# 3. 测试 emit
print("\n3. Emit 事件测试:")
test_events = [
    ('getEvents', {}),
    ('getVitals', {}),
    ('getPCDT', {}),
    ('getData', {}),
    ('subscribe', {'channel': 'events'}),
]

for event, data in test_events:
    msg = f'42["{event}",{json.dumps(data)}]'
    status, body = safe_request(4000, 'POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body=msg)
    print(f"  EMIT {event:15} -> {status} {body[:80]}")
    time.sleep(2)

# 4. 测试 4001
print("\n4. 4001 Socket.IO 测试:")
status, body = safe_request(4001, 'GET', '/socket.io/?EIO=4&transport=polling')
print(f"  Status: {status}")
print(f"  Body: {body}")

match = re.search(r'0\{.*?\}', body)
if match:
    handshake_data = json.loads(match.group(0)[1:])
    sid = handshake_data.get('sid', '')
    print(f"  SID: {sid}")
    
    test_msgs = [
        '42["events"]',
        '42["events",{}]',
        '42["getData"]',
        '42["getData",{}]',
    ]
    
    for msg in test_msgs:
        status, body = safe_request(4001, 'POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body=msg)
        print(f"  POST {msg[:30]:30} -> {status} {body[:80]}")
        time.sleep(2)
