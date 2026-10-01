import http.client
import json
import ssl

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

def http_post(port, path, data=None, headers=None):
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=10, context=ctx)
    h = headers or {}
    h['Content-Type'] = 'application/json'
    conn.request('POST', path, body=json.dumps(data) if data else '{}', headers=h)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), body

print("=== Socket.IO 深度测试 ===\n")

# 1. 测试不同端口的 Socket.IO
print("1. 各端口 Socket.IO 握手测试:")
for port, name in [(4000, 'epcrServer'), (4001, 'vitalSignVideo'), (4002, 'hospital'), 
                   (4003, 'doctor'), (4004, 'auth'), (4005, 'monitor'), (4007, 'stat'), (4008, 'mci')]:
    try:
        status, headers, body = http_get(port, '/socket.io/?EIO=4&transport=polling')
        body_str = body.decode('utf-8', errors='replace')[:100]
        print(f"  {port} {name}: {status} {body_str[:60]}")
    except Exception as e:
        print(f"  {port} {name}: Error {e}")

# 2. 测试 Socket.IO 消息 (4000)
print("\n2. Socket.IO 消息测试 (4000):")

# 获取 SID
status, headers, body = http_get(4000, '/socket.io/?EIO=4&transport=polling')
body_str = body.decode('utf-8', errors='replace')
print(f"  Handshake: {body_str}")

# 解析 SID
if body_str.startswith('0{'):
    json_str = body_str[1:]
    handshake_data = json.loads(json_str)
    sid = handshake_data.get('sid', '')
    print(f"  SID: {sid}")
    
    # 测试 join room
    test_rooms = ['events', 'vitals', 'monitor', 'pcdt', 'live', 'video', 'case', 'dispatch']
    for room in test_rooms:
        # Engine.IO message format: 42["room"]
        msg = f'42["{room}"]'
        status, headers, body = http_get(4000, f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                                         {'Content-Type': 'text/plain'})
        # 用 POST 发送
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:100]
        conn.close()
        print(f"    JOIN {room}: {resp.status} {resp_body}")

    # 测试 emit 事件
    print("  \n  Emit 事件测试:")
    test_events = [
        {'event': 'getEvents', 'data': {}},
        {'event': 'getVitals', 'data': {}},
        {'event': 'subscribe', 'data': {'channel': 'events'}},
        {'event': 'ping', 'data': {}},
        {'event': 'hello', 'data': {}},
    ]
    
    for test in test_events:
        msg = f'42["{test["event"]}",{json.dumps(test["data"])}]'
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                    body=msg, headers={'Content-Type': 'text/plain'})
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf-8', errors='replace')[:100]
        conn.close()
        print(f"    EMIT {test['event']}: {resp.status} {resp_body}")

# 3. 测试 4001 Socket.IO
print("\n3. Socket.IO 4001 测试:")
try:
    status, headers, body = http_get(4001, '/socket.io/?EIO=4&transport=polling')
    body_str = body.decode('utf-8', errors='replace')[:100]
    print(f"  Handshake: {status} {body_str}")
    
    if body_str.startswith('0{'):
        json_str = body_str[1:]
        handshake_data = json.loads(json_str)
        sid = handshake_data.get('sid', '')
        print(f"  SID: {sid}")
        
        # 测试 join room
        test_rooms = ['events', 'vitals', 'pcdt']
        for room in test_rooms:
            msg = f'42["{room}"]'
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, timeout=10, context=ctx)
            conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', 
                        body=msg, headers={'Content-Type': 'text/plain'})
            resp = conn.getresponse()
            resp_body = resp.read().decode('utf-8', errors='replace')[:100]
            conn.close()
            print(f"    JOIN {room}: {resp.status} {resp_body}")
except Exception as e:
    print(f"  Error: {e}")

# 4. 测试 WebSocket 升级
print("\n4. WebSocket 升级测试:")
for port, name in [(4000, 'epcrServer'), (4001, 'vitalSignVideo')]:
    try:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', port, timeout=10, context=ctx)
        conn.request('GET', '/socket.io/?EIO=4&transport=websocket', 
                    headers={'Upgrade': 'websocket', 'Connection': 'Upgrade'})
        resp = conn.getresponse()
        status = resp.status
        headers = dict(resp.getheaders())
        body = resp.read()[:100]
        conn.close()
        print(f"  {port} {name}: {status}")
        if status == 101:
            print(f"    WebSocket upgraded! Headers: {headers}")
        else:
            print(f"    Body: {body.decode('utf-8', errors='replace')[:50]}")
    except Exception as e:
        print(f"  {port} {name}: Error {e}")

# 5. 测试 Socket.IO 在 9000 (printServer)
print("\n5. Socket.IO 9000 (printServer):")
try:
    conn = http.client.HTTPConnection('epcr.tpf.gov.tw', 9000, timeout=5)
    conn.request('GET', '/socket.io/?EIO=4&transport=polling')
    resp = conn.getresponse()
    body = resp.read()[:100]
    conn.close()
    print(f"  HTTP: {resp.status} {body.decode('utf-8', errors='replace')[:50]}")
except Exception as e:
    print(f"  HTTP: Error {e}")
