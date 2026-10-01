import websocket
import json
import ssl
import time
import select

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_websocket(port, name):
    print(f"\n=== WebSocket 测试 {name} ===")
    
    try:
        ws = websocket.create_connection(
            f"wss://epcr.tpf.gov.tw:{port}/socket.io/?EIO=4&transport=websocket",
            sslopt={"context": ctx},
            timeout=5
        )
        print(f"  Connected to {name}")
        
        # 接收初始消息
        msg = ws.recv()
        print(f"  Initial: {msg}")
        
        # 测试 join room - 保持连接
        print("\n  Join room 测试 (保持连接):")
        test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch']
        
        for room in test_rooms:
            try:
                # 先发送 ping 保持连接
                ws.send('2')
                time.sleep(0.5)
                
                # 发送 join room
                ws.send(f'42["{room}"]')
                time.sleep(2)
                
                # 非阻塞接收
                if ws.connected:
                    ready, _, _ = select.select([ws.sock], [], [], 1)
                    if ready:
                        msg = ws.recv()
                        print(f"    JOIN {room:12} -> {msg[:150]}")
                    else:
                        print(f"    JOIN {room:12} -> (no response)")
                else:
                    print(f"    JOIN {room:12} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    JOIN {room:12} -> Error: {str(e)[:50]}")
                break
        
        # 测试 emit - 保持连接
        print("\n  Emit 事件测试 (保持连接):")
        test_events = [
            ('getEvents', {}),
            ('getVitals', {}),
            ('getPCDT', {}),
            ('getData', {}),
            ('subscribe', {'channel': 'events'}),
        ]
        
        for event, data in test_events:
            try:
                # 先发送 ping 保持连接
                ws.send('2')
                time.sleep(0.5)
                
                # 发送 emit
                ws.send(f'42["{event}",{json.dumps(data)}]')
                time.sleep(2)
                
                if ws.connected:
                    ready, _, _ = select.select([ws.sock], [], [], 1)
                    if ready:
                        msg = ws.recv()
                        print(f"    EMIT {event:15} -> {msg[:150]}")
                    else:
                        print(f"    EMIT {event:15} -> (no response)")
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
