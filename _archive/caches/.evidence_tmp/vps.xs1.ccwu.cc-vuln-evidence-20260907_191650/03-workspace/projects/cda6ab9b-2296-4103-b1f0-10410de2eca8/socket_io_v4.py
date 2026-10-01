import http.client
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== Socket.IO v4 (长轮询) ===\n")

# 1. 获取 SID
print("1. 获取 4000 SID:")
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=30, context=ctx)
conn.request('GET', '/socket.io/?EIO=4&transport=polling')
resp = conn.getresponse()
body = resp.read().decode('utf-8', errors='replace')
conn.close()

import re
match = re.search(r'0\{.*?\}', body)
if not match:
    print(f"  No SID: {body}")
    exit()

handshake_data = json.loads(match.group(0)[1:])
sid = handshake_data.get('sid', '')
print(f"  SID: {sid}")
print(f"  Full: {body}")

# 2. 长轮询: 保持连接并发送消息
print("\n2. 长轮询测试:")

# 先发送 join room 消息
test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']

for room in test_rooms:
    msg = f'42["{room}"]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=30, context=ctx)
    conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                body=msg, headers={'Content-Type': 'text/plain'})
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='replace')[:150]
    conn.close()
    print(f"  JOIN {room:12} -> {resp.status} {resp_body[:80]}")
    time.sleep(1)

# 3. 测试 emit 事件
print("\n3. Emit 事件测试:")
test_events = [
    ('getEvents', {}),
    ('getVitals', {}),
    ('getPCDT', {}),
    ('getData', {}),
    ('subscribe', {'channel': 'events'}),
    ('ping', {}),
    ('pong', {}),
]

for event, data in test_events:
    msg = f'42["{event}",{json.dumps(data)}]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=30, context=ctx)
    conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                body=msg, headers={'Content-Type': 'text/plain'})
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='replace')[:150]
    conn.close()
    print(f"  EMIT {event:15} -> {resp.status} {resp_body[:80]}")
    time.sleep(1)

# 4. 测试 4001
print("\n4. 4001 Socket.IO 测试:")
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=30, context=ctx)
conn.request('GET', '/socket.io/?EIO=4&transport=polling')
resp = conn.getresponse()
body = resp.read().decode('utf-8', errors='replace')
conn.close()

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
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=30, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  POST {msg[:30]:30} -> {resp.status} {resp_body[:80]}")
        time.sleep(1)
