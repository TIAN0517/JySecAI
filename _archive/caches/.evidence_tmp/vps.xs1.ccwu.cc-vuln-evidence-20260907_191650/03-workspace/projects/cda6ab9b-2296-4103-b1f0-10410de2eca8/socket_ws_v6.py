import websocket
import json
import ssl
import time
import select
import threading

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_websocket_deep(port, name):
    print(f"\n=== WebSocket 深度测试 {name} ===")
    
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
        
        # 测试 join room 并等待更长时间
        print("\n  Join room 深度测试 (等待 5s):")
        test_rooms = ['events', 'vitals', 'pcdt', 'live', 'video', 'case', 'dispatch', 
                      'vitalSign', 'videoStream', 'pcdtData', 'realtime', 'monitor',
                      'events:room', 'vitals:room', 'pcdt:room']
        
        for room in test_rooms:
            try:
                ws.send(f'42["{room}"]')
                time.sleep(5)  # 等待 5 秒
                
                if ws.connected:
                    # 收集所有消息
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
                            print(f"    JOIN {room:15} -> {r[:150]}")
                    else:
                        print(f"    JOIN {room:15} -> (no response)")
                else:
                    print(f"    JOIN {room:15} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    JOIN {room:15} -> Error: {str(e)[:50]}")
                break
        
        # 测试 emit 并等待更长时间
        print("\n  Emit 事件深度测试 (等待 5s):")
        test_events = [
            ('getEvents', {}),
            ('getEvents', {'limit': 10}),
            ('getEvents', {'CaseID': '1'}),
            ('getVitals', {}),
            ('getVitals', {'CaseID': '1'}),
            ('getPCDT', {}),
            ('getPCDT', {'CaseID': '1'}),
            ('getData', {}),
            ('getData', {'type': 'events'}),
            ('subscribe', {'channel': 'events'}),
            ('subscribe', {'room': 'events'}),
            ('join', {'room': 'events'}),
            ('listen', {}),
            ('start', {}),
            ('init', {}),
        ]
        
        for event, data in test_events:
            try:
                ws.send(f'42["{event}",{json.dumps(data)}]')
                time.sleep(5)  # 等待 5 秒
                
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
                            print(f"    EMIT {event:15} {json.dumps(data)[:30]:30} -> {r[:150]}")
                    else:
                        print(f"    EMIT {event:15} {json.dumps(data)[:30]:30} -> (no response)")
                else:
                    print(f"    EMIT {event:15} {json.dumps(data)[:30]:30} -> DISCONNECTED")
                    break
            except Exception as e:
                print(f"    EMIT {event:15} {json.dumps(data)[:30]:30} -> Error: {str(e)[:50]}")
                break
        
        ws.close()
        print(f"\n  Closed {name}")
    except Exception as e:
        print(f"  Error: {str(e)}")

test_websocket_deep(4000, "4000")
test_websocket_deep(4001, "4001")
