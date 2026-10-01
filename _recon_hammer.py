#!/usr/bin/env python3
"""Hammer epcr:4000 /config with 15 attempts, 4s apart, until a body
arrives. Also try / and /health to confirm the port is alive at all."""
import socket, struct, time, sys

PROXY = ("202.160.76.157", 11082)
DEST_HOST = "epcr.tpf.gov.tw"

def one(port, path, timeout=12):
    try:
        s = socket.create_connection(PROXY, timeout=15)
        s.sendall(b"\x05\x01\x00")
        s.recv(4)
        hb = DEST_HOST.encode()
        s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", port))
        s.settimeout(timeout)
        rep = b""
        while len(rep) < 4:
            c = s.recv(16)
            if not c: break
            rep += c
        if len(rep) < 2 or rep[1] != 0:
            s.close()
            return None, "connfail"
        req = f"GET {path} HTTP/1.1\r\nHost: {DEST_HOST}:{port}\r\nConnection: close\r\nUser-Agent: Mozilla/5.0\r\n\r\n"
        s.sendall(req.encode())
        buf = b""
        while True:
            try:
                d = s.recv(65536)
            except socket.timeout:
                buf += b"\n[timeout]"
                break
            if not d:
                break
            buf += d
        s.close()
        txt = buf.decode(errors="replace")
        if not txt.strip():
            return None, "empty"
        if "\r\n\r\n" not in txt:
            return None, f"no-header {txt[:60]!r}"
        head, body = txt.split("\r\n\r\n", 1)
        return body, head.splitlines()[0]
    except Exception as e:
        return None, f"err {e}"

# First: confirm the port is alive at all
print("=== liveness probe 4000 / ===")
for i in range(5):
    b, h = one(4000, "/")
    print(f"  try{i+1}: {h if h else b} | body {len(b or '')}B")
    if b and b.strip():
        print("  LIVENESS BODY (first 300):", b[:300].replace(chr(10),' '))
    time.sleep(2)

print("\n=== hammer 4000 /config x12 (3s apart) ===")
for i in range(12):
    b, h = one(4000, "/config")
    if b:
        print(f"  try{i+1}: GOT IT {h}")
        print("  BODY:\n" + b)
        break
    else:
        print(f"  try{i+1}: {h}")
    time.sleep(3)
