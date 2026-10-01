import websocket
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_websocket(port, name):
    print(f"\n=== WebSocket 测试 {name} ===")
    
    # 1. 获取 SID
    try:
        ws = websocket.create_connection(
            f"wss://epcr.tpf.gov.tw:{port}/socket.io/?EIO=4&transport=websocket",
            sslopt={"context": ctx},
            timeout=10
        )
        print(f"  Connected to {name}")
        
        # 2. 接收初始消息
        msg = ws.recv()
        print(f"  Initial: {msg[:200]}")
        
        # 解析 SID
        # Engine.IO v4 消息格式: 40 = open, 42 = message
        import re
        match = re.search(r'40\{.*?\}', msg)
        if match:
            json_str = match.group(0)[2:]  # 去掉 '40'
            handshake_data = json.loads(json_str)
            sid = handshake_data.get('sid', '')
            print(f"  SID: {sid}")
        
        # 3. 测试 join room
        print("\n  Join room 测试:")
        test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']
        
        for room in test_rooms:
            try:
                # Socket.IO v4 格式: 42["room"]
                ws.send(f'42["{room}"]')
                time.sleep(0.5)
                # 尝试接收响应
                if ws.connected:
                    msg = ws.recv()
                    print(f"    JOIN {room:12} -> {msg[:100]}")
                else:
                    print(f"    JOIN {room:12} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    JOIN {room:12} -> Error: {str(e)[:50]}")
                break
        
        # 4. 测试 emit
        print("\n  Emit 事件测试:")
        test_events = [
            ('getEvents', {}),
            ('getVitals', {}),
            ('getPCDT', {}),
            ('getData', {}),
            ('subscribe', {'channel': 'events'}),
        ]
        
        for event, data in test_events:
            try:
                ws.send(f'42["{event}",{json.dumps(data)}]')
                time.sleep(0.5)
                if ws.connected:
                    msg = ws.recv()
                    print(f"    EMIT {event:15} -> {msg[:100]}")
                else:
                    print(f"    EMIT {event:15} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    EMIT {event:15} -> Error: {str(e)[:50]}")
                break
        
        ws.close()
        print(f"\n  Closed {name}")
    except Exception as e:
        print(f"  Error: {str(e)}")

test_websocket(4000, "4000")
test_websocket(4001, "4001")
