import http.client
import json
import ssl
import time

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

print("=== Socket.IO 深度测试 v2 ===\n")

# 1. 获取 4000 的 SID
print("1. 获取 4000 SID:")
status, headers, body = http_get(4000, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')
print(f"  Raw: {body_str[:200]}")

# 解析 Engine.IO 消息格式: 96:0{json}2:40
# 96 = message length, 0 = open, 2 = ping, 40 = ack
import re
match = re.search(r'0\{.*?\}', body_str)
if match:
    json_str = match.group(0)[1:]  # 去掉 '0'
    handshake_data = json.loads(json_str)
    sid = handshake_data.get('sid', '')
    print(f"  SID: {sid}")
    
    # 2. 测试 join room
    print("\n2. Join room 测试:")
    test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch', 'monitor', 'stat']
    
    for room in test_rooms:
        # Socket.IO v4 格式: 42["room_name"]
        msg = f'42["{room}"]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  JOIN {room:12} -> {resp.status} {resp_body[:80]}")
    
    # 3. 测试 emit 事件
    print("\n3. Emit 事件测试:")
    test_events = [
        ('getEvents', {}),
        ('getVitals', {}),
        ('getPCDT', {}),
        ('subscribe', {'channel': 'events'}),
        ('unsubscribe', {'channel': 'events'}),
        ('ping', {}),
        ('pong', {}),
        ('hello', {}),
        ('test', {}),
        ('emit', {'event': 'test'}),
    ]
    
    for event, data in test_events:
        # Socket.IO v4 格式: 42["event_name",{"data":"..."}]
        msg = f'42["{event}",{json.dumps(data)}]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  EMIT {event:15} -> {resp.status} {resp_body[:80]}")
    
    # 4. 测试不同房间的消息
    print("\n4. 带房间的消息测试:")
    test_room_events = [
        ('events', 'getEvents', {}),
        ('events', 'subscribe', {}),
        ('vitals', 'getVitals', {}),
        ('pcdt', 'getData', {}),
        ('live', 'startStream', {}),
    ]
    
    for room, event, data in test_room_events:
        # 先 join room
        join_msg = f'42["{room}"]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=join_msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        join_resp = resp.read().decode('utf-8', errors='replace')[:50]
        conn.close()
        
        # 再 emit 事件
        msg = f'42["{event}",{json.dumps(data)}]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  ROOM {room:8} EMIT {event:12} -> JOIN:{join_resp[:30]} EMIT:{resp.status} {resp_body[:60]}")

# 5. 测试 4001 的 Socket.IO
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
    
    # 测试 join room
    test_rooms = ['events', 'vitals', 'pcdt', 'video']
    for room in test_rooms:
        msg = f'42["{room}"]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  JOIN {room:12} -> {resp.status} {resp_body[:80]}")
    
    # 测试 emit
    test_events = [('getEvents', {}), ('getData', {}), ('ping', {})]
    for event, data in test_events:
        msg = f'42["{event}",{json.dumps(data)}]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:150]
        conn.close()
        print(f"  EMIT {event:15} -> {resp.status} {resp_body[:80]}")
