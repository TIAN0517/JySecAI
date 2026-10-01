import socketio
import urllib3
import requests
import json
import time
import base64

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

parts = token.split(".")
padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(padded))
print("JWT payload:", payload)
user_id = str(payload.get("id", ""))
print("User ID:", user_id)

results = {}


def run_test(name, emit_fn, listen_sec=8):
    events = []
    sio = socketio.Client(ssl_verify=False)

    @sio.on("connect")
    def on_connect():
        events.append("CONNECTED")
        try:
            emit_fn(sio, token)
        except Exception as e:
            events.append(f"EMIT ERROR: {e}")
        time.sleep(listen_sec)
        try:
            sio.disconnect()
        except:
            pass

    @sio.event
    def connect_error(data):
        events.append(f"CONNECT_ERROR: {data}")

    @sio.event
    def disconnect(reason):
        events.append(f"DISCONNECTED: {reason}")

    try:
        sio.connect(
            "wss://tpertc.tfd.gov.tw:8787",
            transports=["websocket"],
            auth={"token": token},
            wait_timeout=10
        )
        sio.wait()
    except Exception as e:
        events.append(f"CONN_ERROR: {e}")

    results[name] = events
    try:
        sio.disconnect()
    except:
        pass
    time.sleep(1)


tests = [
    ("no_join_stay_15s", lambda s, t: None, 15),
    ("join_myRoom123", lambda s, t: s.emit("join", {"name": "femet", "room": "myRoom123"}), 8),
    ("join_user_id", lambda s, t: s.emit("join", {"name": user_id, "room": user_id}), 8),
    ("join_femet_id", lambda s, t: s.emit("join", {"name": "femet", "room": user_id}), 8),
    ("join_id_femet", lambda s, t: s.emit("join", {"name": user_id, "room": "femet"}), 8),
    ("join_1_1", lambda s, t: s.emit("join", {"name": "1", "room": "1"}), 8),
    ("no_join", lambda s, t: None, 8),
    ("message_ping", lambda s, t: s.emit("message", "ping"), 8),
    ("roomMessage_call", lambda s, t: s.emit("roomMessage", {"type": "calling", "target": "patient1"}), 8),
    ("rtc_event_offer", lambda s, t: s.emit("rtcMessage", {"type": "offer", "sdp": "test"}), 8),
    ("subscribe", lambda s, t: s.emit("subscribe", {"name": "femet", "room": "myRoom123"}), 8),
    ("authenticate_event", lambda s, t: s.emit("authenticate", {"token": t}), 8),
    ("login_event", lambda s, t: s.emit("login", {"name": "femet"}), 8),
]

for name, fn, sec in tests:
    print(f"\n=== {name} ===")
    run_test(name, fn, sec)
    print(f"Result: {results.get(name, [])}")

print("\n=== SUMMARY ===")
for name, events in results.items():
    conn = "OK" if "CONNECTED" in events else "FAIL"
    dis = "Y" if any("DISCONNECT" in e for e in events) else "N"
    msgs = [e for e in events if e.startswith("MSG:") or e.startswith("CONNECT_ERROR")]
    print(f"  [{conn}|disc={dis}] {name}: {msgs}")
