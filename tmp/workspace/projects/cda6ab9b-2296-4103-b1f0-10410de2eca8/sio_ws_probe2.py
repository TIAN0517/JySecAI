#!/usr/bin/env python3
"""Socket.IO v4 WebSocket 双工探测 - 详尽测试
精确观察：哪些事件触发 server-side data push，哪些只触发关闭
"""
import websocket, json, time, threading, ssl

URL = "wss://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=websocket"
received = []
ws_ref = [None]

def on_open(ws):
    print("[*] WS open")

def on_message(ws, msg):
    print(f"[<] {msg[:400]}")
    received.append(msg)

def on_close(ws, code, reason):
    print(f"[*] WS close code={code} reason={reason}")

def on_error(ws, err):
    print(f"[!] WS error: {err}")

ws = websocket.WebSocketApp(
    URL,
    subprotocols=["websocket"],
    on_open=on_open,
    on_message=on_message,
    on_close=on_close,
    on_error=on_error,
)
ws_ref[0] = ws

def send_later(delay, payload, label):
    def _send():
        time.sleep(delay)
        try:
            ws.send(payload)
            print(f"[>] +{delay}s  {label}")
        except Exception as e:
            print(f"[!] send err: {e}")
    threading.Thread(target=_send, daemon=True).start()

threading.Thread(target=ws.run_forever, kwargs={
    "sslopt":{"check_hostname": False, "cert_react": False},
    "ping_interval": 25, "ping_timeout": 15
}, daemon=True).start()

time.sleep(2.5)  # wait handshake

# 1. Engine.IO PING (合法)
send_later(1, "2", "engine PING")
# 2. Socket.IO DISCONNECT (合规)
send_later(3, "41", "DISCONNECT 41")
# 3. 再 PING
send_later(5, "2", "engine PING 2")

# 业务事件：分类测试
biz = [
    # 标准业务事件
    '42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"*"}]',
    '42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"events:created"}]',
    # 简化 subscribe
    '42["subscribe","*"]',
    '42["subscribe","CaseCreated"]',
    # join
    '42["join","hospitalUuid-hosp1"]',
    '42["join","admin"]',
    # ack 测试
    '43[0]',
    # 自定义事件
    '42["foo","bar"]',
    '42["connect"]',
    '42["disconnect"]',
]

for i, p in enumerate(biz):
    send_later(8 + i*1.5, p, f"biz[{i}]: {p[:60]}")

time.sleep(60)
print("\n========== 总接收 =============")
for r in received:
    print(r[:400])
print(f"========== 共 {len(received)} 条 ==========")
try: ws.close()
except: pass
