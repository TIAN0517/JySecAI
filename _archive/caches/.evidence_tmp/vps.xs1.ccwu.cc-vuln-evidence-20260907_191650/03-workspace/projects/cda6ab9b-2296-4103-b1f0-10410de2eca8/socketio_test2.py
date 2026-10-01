import http.client
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试 Socket.IO 未授权通信
print('=== Socket.IO 未授权通信测试 ===')

# 1. 获取 Socket.IO 握手
print('1. Socket.IO handshake...')
conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
conn.request('GET', '/socket.io/?EIO=3&transport=polling')
resp = conn.getresponse()
data = resp.read().decode('utf-8', errors='replace')
print(f'  Status: {resp.status}')
print(f'  Body: {data[:500]}')
conn.close()

# 2. 解析 SID
import re
sid_match = re.search(r'"sid":"([^"]+)"', data)
if sid_match:
    sid = sid_match.group(1)
    print(f'\n2. SID: {sid}')

    # 3. 加入 room "events"
    print('3. Joining room "events"...')
    msg = '42["events"]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body=msg, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 4. 获取事件（轮询）
    print('4. Polling for events...')
    for i in range(3):
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=15, context=ctx)
        conn.request('GET', f'/socket.io/?EIO=3&transport=polling&sid={sid}')
        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')
        print(f'  Poll {i+1}: {resp.status}')
        print(f'  Data: {data[:500]}')
        conn.close()
        time.sleep(1)

    # 5. 测试发送事件
    print('5. Testing event emission...')
    # 发送一个测试事件
    test_event = json.dumps({'type': 'test', 'data': 'test123'})
    msg = f'42["testEvent",{test_event}]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body=msg, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 6. 测试不同的 room
    print('6. Testing different rooms...')
    rooms = ['cases', 'patients', 'dispatch', 'ambulances', 'hospitals', 'doctors', 'monitor', 'vitals', 'videos', 'test', 'new', 'update', 'delete']

    for room in rooms:
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
        msg = f'42["{room}"]'
        headers = {'Content-Type': 'text/plain'}
        conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body=msg, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')
        if resp.status == 200:
            print(f'  Room {room}: {resp.status}')
        conn.close()

    # 7. 测试离开 room
    print('7. Leaving room...')
    msg = '43["events"]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body=msg, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 8. 关闭连接
    print('8. Closing connection...')
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body='0', headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()
else:
    print('No SID found in handshake')
