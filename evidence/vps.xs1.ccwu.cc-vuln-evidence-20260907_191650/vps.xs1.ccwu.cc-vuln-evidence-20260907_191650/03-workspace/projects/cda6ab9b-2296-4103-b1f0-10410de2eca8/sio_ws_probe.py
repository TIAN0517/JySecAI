#!/usr/bin/env python3
"""
Socket.IO v4 WebSocket 双工探测（正确协议）
- Engine.IO v4: frame '0'=open ack, '40'=message/connect, '41'=close, '42'=message/event
- Socket.IO 4: '0'=CONNECT, '1'=DISCONNECT, '2'=EVENT, '3'=ACK, '4'=CONNECT_ERROR, '5'=BINARY_EVENT, '6'=BINARY_ACK
- 客户端 EVENT 包格式: 42["event_name", args...]
"""
import websocket, json, time, sys, threading

URL = "wss://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=websocket"
received = []
ws_ref = [None]

def on_open(ws):
    print("[*] WS open, waiting handshake...")

def on_message(ws, msg):
    print(f"[<] {msg[:300]}")
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
            print(f"[>] +{delay}s  {label}: {payload[:120]}")
        except Exception as e:
            print(f"[!] send err: {e}")
    threading.Thread(target=_send, daemon=True).start()

threading.Thread(target=ws.run_forever, kwargs={"sslopt":{"check_hostname": False}, "ping_interval": 25, "ping_timeout": 15}, daemon=True).start()

# 等待 OPEN + Socket.IO CONNECT 握手
time.sleep(2.5)

payloads = [
    # 1. Engine.IO PING (probe)
    ("2", "engine.io PING"),
    # 2. 4002 暴露的 client.subscribe 业务事件
    ('42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"events:created"}]', "client.subscribe events:created"),
    # 3. 订阅所有
    ('42["client.subscribe",{"roomName":"hospitalUuid-hosp1","event":"*"}]', "client.subscribe *"),
    # 4. 经典 join room（Socket.IO 内建）
    ('42["join","events"]', "join events"),
    ('42["join","hospitalUuid-hosp1"]', "join hospitalUuid-hosp1"),
    ('42["join","admin"]', "join admin"),
    # 5. 猜测业务事件
    ('42["subscribe","CaseCreated"]', "subscribe CaseCreated"),
    ('42["subscribe","PatientUpdated"]', "subscribe PatientUpdated"),
    ('42["subscribe","EventCreated"]', "subscribe EventCreated"),
    ('42["subscribe","VitalSign"]', "subscribe VitalSign"),
    ('42["subscribe","*"]', "subscribe *"),
    # 6. 猜测业务调用
    ('42["getHospitals"]', "getHospitals"),
    ('42["getPatients"]', "getPatients"),
    ('42["getActiveCases"]', "getActiveCases"),
    # 7. ACK 测试（id=0 给服务端响应）
    ('43[0,{"ack":"hi"}]', "ACK 0"),
]

for i, (p, label) in enumerate(payloads):
    send_later(1.5 + i*1.2, p, label)

# 监听 75s
time.sleep(75)
print("\n========== 总接收 =============")
for r in received:
    print(r[:400])
print(f"========== 共 {len(received)} 条 ==========")
try: ws.close()
except: pass
