import websocket
import json
import ssl
import time
import select

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_websocket_quick(port, name):
    print(f"\n=== WebSocket 快速测试 {name} ===")
    
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
        
        # 快速测试 join room (等待 2s)
        print("\n  Join room 测试 (等待 2s):")
        test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video']
        
        for room in test_rooms:
            try:
                ws.send(f'42["{room}"]')
                time.sleep(2)
                
                if ws.connected:
                    responses = []
                    while ws.connected:
                        ready, _, _ = select.select([ws.sock], [], [], 0.5)
                        if ready:
                            msg = ws.recv()
                            responses.append(msg)
                        else:
                            break
                    
                    if responses:
                        for r in responses:
                            print(f"    JOIN {room:12} -> {r[:100]}")
                    else:
                        print(f"    JOIN {room:12} -> (no response)")
                else:
                    print(f"    JOIN {room:12} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    JOIN {room:12} -> Error: {str(e)[:50]}")
                break
        
        # 快速测试 emit (等待 2s)
        print("\n  Emit 事件测试 (等待 2s):")
        test_events = [
            ('getEvents', {}),
            ('getVitals', {}),
            ('getPCDT', {}),
            ('getData', {}),
        ]
        
        for event, data in test_events:
            try:
                ws.send(f'42["{event}",{json.dumps(data)}]')
                time.sleep(2)
                
                if ws.connected:
                    responses = []
                    while ws.connected:
                        ready, _, _ = select.select([ws.sock], [], [], 0.5)
                        if ready:
                            msg = ws.recv()
                            responses.append(msg)
                        else:
                            break
                    
                    if responses:
                        for r in responses:
                            print(f"    EMIT {event:12} -> {r[:100]}")
                    else:
                        print(f"    EMIT {event:12} -> (no response)")
                else:
                    print(f"    EMIT {event:12} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    EMIT {event:12} -> Error: {str(e)[:50]}")
                break
        
        ws.close()
        print(f"\n  Closed {name}")
    except Exception as e:
        print(f"  Error: {str(e)}")

test_websocket_quick(4000, "4000")
test_websocket_quick(4001, "4001")
