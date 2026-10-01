#!/usr/bin/env python3
"""Socket.IO v4 WebSocket — proper client using websocket-client."""
import websocket, json, time, threading

URL = "wss://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=websocket"
HOST = "epcr.tpf.gov.tw"

# websocket-client doesn't speak socket.io protocol natively, so we encode packets manually
# But ws supports subprotocols='socket.io' (negotiated)

ws = websocket.WebSocket()
ws.connect(URL,
           header=[f"Host: {HOST}:4000",
                   f"Origin: https://{HOST}:4000",
                   "User-Agent: CyberStrike/1.0"],
           subprotocols=["socket.io"],
           timeout=10)
ws.settimeout(5)

def recv_all(dur=1.0):
    end = time.time() + dur
    out = []
    while time.time() < end:
        try:
            d = ws.recv()
            if not d: break
            out.append(d)
        except Exception as e:
            break
    return out

# Initial burst
print("=== Initial packets ===")
for d in recv_all(2.0):
    print(f"  < {d!r}")

def send(s):
    print(f"  > {s!r}")
    ws.send(s)

# Emit events
print("\n=== Emit events ===")
events = [
    "40",  # connect to default ns (server should ack 40)
    "40/admin",
    "40/events",
    "40/monitor",
    "40/hosp",
    "40/live",
    "42" + json.dumps(["hello", {}]),
    "42" + json.dumps(["ping", {}]),
    "42" + json.dumps(["join", "events"]),
    "42" + json.dumps(["join", {"room": "events"}]),
    "42" + json.dumps(["subscribe", "events"]),
    "42" + json.dumps(["getCase", {"caseId": "180817092350fed7"}]),
    "42" + json.dumps(["getEvents", {}]),
    "42" + json.dumps(["request", {"type": "events"}]),
    "42" + json.dumps(["auth", {"token": "anonymous"}]),
    "42" + json.dumps(["version", {}]),
    "42" + json.dumps(["config", {}]),
    "42" + json.dumps(["stream", {}]),
    "42" + json.dumps(["telemetry", {}]),
    "42" + json.dumps(["emit", {"x":1}]),
]
for e in events:
    send(e)
    for d in recv_all(0.3):
        print(f"  < {d!r}")

# Long listen
print("\n=== Listen 10s ===")
end = time.time() + 10
while time.time() < end:
    try:
        d = ws.recv()
        if d:
            print(f"  < {d!r}")
    except Exception:
        break

ws.close()
print("Done.")