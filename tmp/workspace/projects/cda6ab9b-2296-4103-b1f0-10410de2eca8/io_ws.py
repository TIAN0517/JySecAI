#!/usr/bin/env python3
"""Socket.IO v4 WebSocket upgrade — the server may behave differently over WS."""
import socket, base64, os, struct, json, time, threading, queue

HOST = "epcr.tpf.gov.tw"; PORT = 4000

def ws_connect(path="/socket.io/?EIO=4&transport=websocket"):
    s = socket.create_connection((HOST, PORT), timeout=15)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {path} HTTP/1.1\r\n"
           f"Host: {HOST}:{PORT}\r\n"
           "Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
           "Origin: https://epcr.tpf.gov.tw:4000\r\n"
           "Sec-WebSocket-Protocol: socket.io\r\n"
           "User-Agent: CyberStrike/1.0\r\n\r\n")
    s.sendall(req.encode())
    # read response headers
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk: break
        buf += chunk
    print("WS HANDSHAKE RESP:")
    print(buf.decode(errors='replace'))
    return s, buf

def ws_send_text(s, data):
    payload = data.encode() if isinstance(data, str) else data
    header = bytes([0x81])  # FIN + text
    L = len(payload)
    mask_key = os.urandom(4)
    if L < 126:
        header += bytes([0x80 | L])
    elif L < 65536:
        header += bytes([0x80 | 126]) + struct.pack(">H", L)
    else:
        header += bytes([0x80 | 127]) + struct.pack(">Q", L)
    header += mask_key
    masked = bytes(b ^ mask_key[i%4] for i,b in enumerate(payload))
    s.sendall(header + masked)

def ws_recv(s, timeout=10):
    s.settimeout(timeout)
    try:
        # read 2 header bytes
        h = s.recv(2)
        if not h: return None, b''
        fin_op = h[0]; L = h[1] & 0x7f
        if L == 126:
            L = struct.unpack(">H", s.recv(2))[0]
        elif L == 127:
            L = struct.unpack(">Q", s.recv(8))[0]
        data = b""
        while len(data) < L:
            data += s.recv(L - len(data))
        op = fin_op & 0x0f
        return op, data
    except Exception as e:
        return None, str(e).encode()

s, hdrbuf = ws_connect()
# After handshake, server should send EIO '0' OPEN + '40' CONNECT (default namespace)
print("\n=== Reading initial packets ===")
time.sleep(1)
op, d = ws_recv(s, timeout=5)
print(f"OP={op} DATA={d!r}")
op, d = ws_recv(s, timeout=5)
print(f"OP={op} DATA={d!r}")

# Try to CONNECT to namespaces
print("\n=== Namespace CONNECTs ===")
for ns in ["", "/admin", "/events", "/monitor", "/hosp", "/live"]:
    pkt = f'40{ns}'
    ws_send_text(s, pkt)
    print(f"Sent: {pkt}")
    op, d = ws_recv(s, timeout=3)
    print(f"  RESP: OP={op} DATA={d!r}")

# Emit events
print("\n=== Emit events ===")
events = [
    ["hello", {}],
    ["ping", {}],
    ["join", "events"],
    ["join", {"room":"events"}],
    ["subscribe", "events"],
    ["getCase", {"caseId":"180817092350fed7"}],
    ["getEvents", {}],
    ["request", {"type":"events"}],
    ["auth", {"token":"anonymous"}],
    ["version", {}],
    ["config", {}],
    ["stream", {}],
    ["telemetry", {}],
]
for ev, pl in events:
    ws_send_text(s, f'42{json.dumps([ev, pl])}')
    print(f"EV {ev!r:<20} -> ", end="")
    op, d = ws_recv(s, timeout=2)
    print(f"OP={op} DATA={d!r}")

# Final listening period
print("\n=== Listening 10s for server-pushed events ===")
end = time.time() + 10
while time.time() < end:
    op, d = ws_recv(s, timeout=2)
    if op is None: continue
    if not d: continue
    print(f"PUSH: OP={op} DATA={d!r}")

# Close gracefully
ws_send_text(s, bytes([0x88, 0x80, 0,0,0,0]))  # close
s.close()
print("\nDone.")
