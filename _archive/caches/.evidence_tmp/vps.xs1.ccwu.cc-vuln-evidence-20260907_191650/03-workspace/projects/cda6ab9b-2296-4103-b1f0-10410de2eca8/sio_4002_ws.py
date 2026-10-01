#!/usr/bin/env python3
"""4002 Socket.IO WebSocket 双工探测 - cookie token 绕过鉴权后"""
import websocket, json, time, threading

URL = "wss://epcr.tpf.gov.tw:4002/socket.io/?EIO=4&transport=websocket"
COOKIE = "token=anonymous"

received = []
ws_ref = [None]

def on_open(ws):
    print("[*] WS open (with cookie token=anonymous)")

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
    header=[f"Cookie: {COOKIE}"],
    on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error,
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

time.sleep(2.5)

# Engine.IO PING 验证
send_later(1, "2", "engine PING")
# Socket.IO CONNECT (with token auth payload)
send_later(3, '40', 'CONNECT 40')
send_later(4, '40{"token":"anonymous"}', 'CONNECT+token')
send_later(5, '40{"auth":{"token":"anonymous","hospitalUuid":"hospitalUuid-hosp1"}}', 'CONNECT+auth+hospital')

# 业务事件 - 详尽
biz = [
    '42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"*"}]',
    '42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"events:created"}]',
    '42["client.subscribe",{"roomName":"hospitalUuid-hosp1"}]',
    '42["client.unsubscribe",{}]',
    '42["subscribe","*"]',
    '42["join","hospitalUuid-hosp1"]',
    '42["getHospitals"]',
    '42["foo","bar"]',
    '42["connect"]',
    '42["disconnect"]',
]
for i, p in enumerate(biz):
    send_later(8 + i*1.5, p, f"biz[{i}]: {p[:60]}")

time.sleep(45)
print("\n========== 总接收 =============")
for r in received:
    print(r[:400])
print(f"========== 共 {len(received)} 条 ==========")
try: ws.close()
except: pass
