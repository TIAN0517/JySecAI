import http.client
import json
import ssl

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

    # 3. 发送 ping
    print('3. Sending ping...')
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    conn.request('GET', f'/socket.io/?EIO=3&transport=polling&sid={sid}')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 4. 加入 room
    print('4. Joining room "events"...')
    # Socket.IO v3 格式: 42["room_name"]
    msg = '42["events"]'
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body=msg, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 5. 发送 ping
    print('5. Sending ping...')
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body='2', headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 6. 发送 pong
    print('6. Sending pong...')
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    headers = {'Content-Type': 'text/plain'}
    conn.request('POST', f'/socket.io/?EIO=3&transport=polling&sid={sid}', body='3', headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:200]}')
    conn.close()

    # 7. 获取事件
    print('7. Getting events...')
    conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4000, timeout=10, context=ctx)
    conn.request('GET', f'/socket.io/?EIO=3&transport=polling&sid={sid}')
    resp = conn.getresponse()
    data = resp.read().decode('utf-8', errors='replace')
    print(f'  Status: {resp.status}')
    print(f'  Body: {data[:500]}')
    conn.close()
else:
    print('No SID found in handshake')

# 8. 测试 WebSocket
print('\n8. Testing WebSocket...')
# WebSocket 需要特殊处理，这里用 polling 替代
print('Using polling instead of WebSocket')

# 9. 测试不同的 room
print('\n9. Testing different rooms...')
rooms = ['events', 'cases', 'patients', 'dispatch', 'ambulances', 'hospitals', 'doctors', 'monitor', 'vitals', 'videos']

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
