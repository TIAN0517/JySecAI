import http.client
import json
import ssl
import time
import threading

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=== Socket.IO v6 (长轮询 + 后台线程) ===\n")

class SocketIOClient:
    def __init__(self, port, name=""):
        self.port = port
        self.name = name
        self.sid = None
        self.connected = False
        self.msg_queue = []
        self.poll_thread = None
        self.stop_event = threading.Event()
    
    def connect(self):
        """建立连接并获取 SID"""
        conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', self.port, timeout=30, context=ctx)
        conn.request('GET', '/socket.io/?EIO=4&transport=polling')
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', errors='replace')
        conn.close()
        
        import re
        match = re.search(r'0\{.*?\}', body)
        if not match:
            return False
        
        handshake_data = json.loads(match.group(0)[1:])
        self.sid = handshake_data.get('sid', '')
        self.connected = True
        print(f"  [{self.name}] Connected, SID: {self.sid}")
        
        # 启动后台轮询线程
        self.stop_event.clear()
        self.poll_thread = threading.Thread(target=self._poll, daemon=True)
        self.poll_thread.start()
        return True
    
    def _poll(self):
        """后台轮询接收消息"""
        while not self.stop_event.is_set():
            try:
                conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', self.port, timeout=30, context=ctx)
                conn.request('GET', f'/socket.io/?EIO=4&transport=polling&sid={self.sid}')
                resp = conn.getresponse()
                body = resp.read().decode('utf-8', errors='replace')
                conn.close()
                
                if body:
                    print(f"  [{self.name}] RECEIVED: {body[:100]}")
                    self.msg_queue.append(body)
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"  [{self.name}] Poll error: {str(e)[:50]}")
                break
    
    def send(self, msg, timeout=5):
        """发送消息"""
        try:
            conn = http.client.HTTPSConnection('epcr.tpf.gov.tw', self.port, timeout=timeout, context=ctx)
            conn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={self.sid}', 
                        body=msg, headers={'Content-Type': 'text/plain'})
            resp = conn.getresponse()
            resp_body = resp.read().decode('utf-8', errors='replace')
            conn.close()
            return resp.status, resp_body
        except Exception as e:
            return 'ERROR', str(e)
    
    def disconnect(self):
        """断开连接"""
        self.stop_event.set()
        if self.poll_thread:
            self.poll_thread.join(timeout=5)
        self.connected = False

# 1. 连接 4000
print("1. 连接 4000:")
client4000 = SocketIOClient(4000, "4000")
if not client4000.connect():
    print("  Connection failed")
    exit()

time.sleep(2)

# 2. 测试 join room
print("\n2. Join room 测试 (4000):")
test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']

for room in test_rooms:
    msg = f'42["{room}"]'
    status, body = client4000.send(msg, timeout=10)
    print(f"  JOIN {room:12} -> {status} {body[:80]}")
    time.sleep(1)

# 3. 测试 emit
print("\n3. Emit 事件测试 (4000):")
test_events = [
    ('getEvents', {}),
    ('getVitals', {}),
    ('getPCDT', {}),
    ('getData', {}),
    ('subscribe', {'channel': 'events'}),
]

for event, data in test_events:
    msg = f'42["{event}",{json.dumps(data)}]'
    status, body = client4000.send(msg, timeout=10)
    print(f"  EMIT {event:15} -> {status} {body[:80]}")
    time.sleep(1)

# 4. 断开 4000
print("\n4. 断开 4000:")
client4000.disconnect()

# 5. 连接 4001
print("\n5. 连接 4001:")
client4001 = SocketIOClient(4001, "4001")
if not client4001.connect():
    print("  Connection failed")
    exit()

time.sleep(2)

# 6. 测试 join room (4001)
print("\n6. Join room 测试 (4001):")
test_rooms = ['events', 'vitals', 'pcdt', 'video']

for room in test_rooms:
    msg = f'42["{room}"]'
    status, body = client4001.send(msg, timeout=10)
    print(f"  JOIN {room:12} -> {status} {body[:80]}")
    time.sleep(1)

# 7. 测试 emit (4001)
print("\n7. Emit 事件测试 (4001):")
test_events = [
    ('getEvents', {}),
    ('getData', {}),
    ('getVideo', {}),
]

for event, data in test_events:
    msg = f'42["{event}",{json.dumps(data)}]'
    status, body = client4001.send(msg, timeout=10)
    print(f"  EMIT {event:15} -> {status} {body[:80]}")
    time.sleep(1)

# 8. 断开 4001
print("\n8. 断开 4001:")
client4001.disconnect()
