import websocket
import json
import ssl
import time

# 禁用 SSL 验证
ssl._create_default_https_context = ssl._create_unverified_context

def test_socketio_v2(port, name):
    print(f"\n{'='*60}")
    print(f"测试 {name} (端口 {port})")
    print(f"{'='*60}")
    
    url = f"wss://epcr.tpf.gov.tw:{port}/socket.io/?EIO=4&transport=websocket"
    
    try:
        ws = websocket.create_connection(url, timeout=5)
        print(f"✓ WebSocket 连接成功: {url}")
        
        # 接收初始消息（注意：以 0 开头）
        msg = ws.recv()
        print(f"初始消息: {msg}")
        
        # 解析 JSON（去掉开头的 0）
        json_str = msg[1:] if msg.startswith('0') else msg
        data = json.loads(json_str)
        sid = data.get('sid')
        print(f"SID: {sid}")
        
        # 测试 1: JOIN 到 "events" 房间
        print("\n--- 测试 JOIN 'events' 房间 ---")
        ws.send('42["events"]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 2: JOIN 到 "vitals" 房间
        print("\n--- 测试 JOIN 'vitals' 房间 ---")
        ws.send('42["vitals"]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 3: EMIT "getEvents"
        print("\n--- 测试 EMIT 'getEvents' ---")
        ws.send('42["getEvents",{}]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 4: EMIT "getVitals"
        print("\n--- 测试 EMIT 'getVitals' ---")
        ws.send('42["getVitals",{}]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 5: EMIT "subscribe"
        print("\n--- 测试 EMIT 'subscribe' ---")
        ws.send('42["subscribe",["events","vitals"]]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 6: EMIT "join"
        print("\n--- 测试 EMIT 'join' ---")
        ws.send('42["join","events"]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 7: EMIT "request"
        print("\n--- 测试 EMIT 'request' ---")
        ws.send('42["request","events"]')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        # 测试 8: PING
        print("\n--- 测试 PING ---")
        ws.send('2')
        time.sleep(1)
        try:
            resp = ws.recv()
            print(f"响应: {resp[:200]}")
        except:
            print("无响应或超时")
        
        ws.close()
        print("\n✓ 连接关闭")
        
    except Exception as e:
        print(f"✗ 连接失败: {str(e)}")

# 测试所有端口
test_socketio_v2(4000, "EPCRServe")
test_socketio_v2(4001, "VitalSignVideoServer")
test_socketio_v2(4005, "MonitorServer")
test_socketio_v2(4007, "StatServer")
test_socketio_v2(4008, "MCIServe")
