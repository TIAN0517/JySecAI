#!/usr/bin/env python3
"""Test if 35.234.50.28:3100 /socket.io broadcasts events.
The socket.io server uses EIO=3 (engine.io v3) with polling transport.
To receive broadcasts, we need to:
1. Connect and get sid
2. Join a room (if required)
3. POST an event via /events
4. Poll to see if the event appears

The key question: does the server emit events to ALL connected socket.io
clients, or only to specific rooms/cases?
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
    while b"\r\n\r\n" not in buf:
        try:
            d = s.recv(65536)
        except socket.timeout:
            break
        if not d:
            break
        buf += d
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

def poll_for_events(s, timeout=10):
    """Poll for socket.io events. Returns list of raw event frames."""
    s.settimeout(timeout)
    events = []
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            text = d.decode(errors="replace")
            # Parse engine.io frames: {n}:{payload}
            for frame in text.split("\n"):
                if frame:
                    events.append(frame)
    except socket.timeout:
        pass
    return events

print("=== Test: does socket.io broadcast events to connected clients? ===\n")

# Step 1: Connect and get sid
print("Step 1: Connect to socket.io, get sid")
s1 = socks_tunnel()
if not s1:
    print("FAIL: tunnel"); sys.exit(1)
head1, body1 = http_req(s1, "GET", "/socket.io/?EIO=3&transport=polling")
m = re.search(r'"sid":"([^"]+)"', body1)
if not m:
    print(f"FAIL: no sid. BODY: {body1}"); sys.exit(1)
sid = m.group(1)
print(f"  SID: {sid}")

# Step 2: Wait 2s, poll for any existing events
print("\nStep 2: Wait 2s, poll for existing events")
time.sleep(2)
events1 = poll_for_events(s1, timeout=3)
print(f"  Events before POST: {len(events1)}")
for e in events1:
    print(f"    {e}")

# Step 3: POST an event with a unique CaseID
print("\nStep 3: POST event with unique CaseID")
s2 = socks_tunnel()
if s2:
    event = {
        "CaseID": "PENTEST_BROADCAST_TEST_2026_0915",
        "TypeOfEventTxt": "broadcast_test",
        "TypeOfEventNum": 999,
        "Caption": "BROADCAST_TEST_MARKER",
        "Elapsed": 99999,
        "Value": "BROADCAST_MARKER",
        "Annotation": "Testing if socket.io broadcasts this event"
    }
    body_json = json.dumps(event)
    head2, body2 = http_req(s2, "POST", "/events", body_json)
    print(f"  POST status: {head2.split(chr(10))[0]}")
    print(f"  POST body: {body2[:200]}")
    s2.close()

# Step 4: Poll for 15s to see if the event is pushed
print("\nStep 4: Poll for 15s to see if event is pushed")
events2 = poll_for_events(s1, timeout=15)
print(f"  Events after POST: {len(events2)}")
for e in events2:
    print(f"    {e}")
    if "PENTEST_BROADCAST_TEST" in e or "BROADCAST_MARKER" in e:
        print("\n  *** BROADCAST CONFIRMED: socket.io pushed the event to connected client! ***")
        break
else:
    print("\n  No broadcast detected in 15s.")
    print("  Possible reasons:")
    print("  1. Events are only pushed to clients in the same room/case")
    print("  2. The event needs to match a specific room name")
    print("  3. The socket.io server doesn't broadcast /events POSTs")

s1.close()
print("\n=== DONE ===")
