import http.client
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def http_get(port, path, headers=None):
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=15, context=ctx)
    conn.request('GET', path, headers=headers or {})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), body

print("=== Socket.IO 深度测试 v3 (保持连接) ===\n")

# 1. 获取 4000 的 SID 并保持连接
print("1. 获取 4000 SID:")
status, headers, body = http_get(4000, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')
print(f"  Raw: {body_str[:200]}")

import re
match = re.search(r'0\{.*?\}', body_str)
if not match:
    print("  No SID found")
    exit()

json_str = match.group(0)[1:]
handshake_data = json.loads(json_str)
sid = handshake_data.get('sid', '')
print(f"  SID: {sid}")

# 2. 测试 join room (使用 GET 方法，Engine.IO polling 用 GET)
print("\n2. Join room 测试 (GET):")
test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']

for room in test_rooms:
    try:
        # Engine.IO v4 polling 用 GET 发送消息
        msg = f'42["{room}"]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
        conn.request('GET', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  JOIN {room:12} -> {resp.status} {resp_body[:80]}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  JOIN {room:12} -> Error: {str(e)[:50]}")

# 3. 测试 POST 消息
print("\n3. POST 消息测试:")
test_msgs = [
    '42["events"]',
    '42["events",{}]',
    '42["getEvents"]',
    '42["getEvents",{}]',
    '2',  # ping
    '3',  # pong
]

for msg in test_msgs:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  POST {msg[:30]:30} -> {resp.status} {resp_body[:80]}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  POST {msg[:30]:30} -> Error: {str(e)[:50]}")

# 4. 测试带 payload 的消息
print("\n4. 带 payload 消息测试:")
test_payloads = [
    ('42["events",{"type":"get"}]', 'get events'),
    ('42["vitals",{"type":"get"}]', 'get vitals'),
    ('42["pcdt",{"type":"get"}]', 'get pcdt'),
    ('42["monitor",{"type":"get"}]', 'get monitor'),
    ('42["subscribe",{"room":"events"}]', 'subscribe'),
    ('42["emit",{"event":"test"}]', 'emit test'),
]

for msg, desc in test_payloads:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  {desc:15} -> {resp.status} {resp_body[:80]}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {desc:15} -> Error: {str(e)[:50]}")

# 5. 测试 4001
print("\n5. 4001 Socket.IO 测试:")
status, headers, body = http_get(4001, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')
print(f"  Handshake: {body_str[:200]}")

match = re.search(r'0\{.*?\}', body_str)
if match:
    json_str = match.group(0)[1:]
    handshake_data = json.loads(json_str)
    sid = handshake_data.get('sid', '')
    print(f"  SID: {sid}")
    
    test_msgs = [
        '42["events"]',
        '42["events",{}]',
        '42["getData"]',
        '42["getData",{}]',
        '2',
    ]
    
    for msg in test_msgs:
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=15, context=ctx)
            conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                        body=msg, headers={'Content-Type': 'text/plain'})
            resp = conn.getresponse()
            resp_body = resp.read().decode('utf-8', errors='replace')[:150]
            conn.close()
            print(f"  POST {msg[:30]:30} -> {resp.status} {resp_body[:80]}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  POST {msg[:30]:30} -> Error: {str(e)[:50]}")

# 6. 测试 ping 保持连接
print("\n6. Ping 保持连接测试:")
status, headers, body = http_get(4000, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')
match = re.search(r'0\{.*?\}', body_str)
if match:
    json_str = match.group(0)[1:]
    handshake_data = json.loads(json_str)
    sid = handshake_data.get('sid', '')
    
    # 发送 ping
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
    conn.request('GET', f'/socket.io/?EIO=4&transport=polling&sid={sid}')
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='replace')[:100]
    conn.close()
    print(f"  GET (ping): {resp.status} {resp_body}")
    
    # 发送 pong
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
    conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                body='3', headers={'Content-Type': 'text/plain'})
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='replace')[:100]
    conn.close()
    print(f"  POST pong: {resp.status} {resp_body}")
