#!/usr/bin/env python3
"""Test socket.io EIO=4 (modern) on 35.234.50.28:3100. Check if it pushes
events to connected clients."""
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

print("=== Test 1: EIO=4 polling ===")
s = socks_tunnel()
if s:
    head, body = http_req(s, "GET", "/socket.io/?EIO=4&transport=polling")
    print(f"HEAD: {head}")
    print(f"BODY: {body}")
    s.close()

print("\n=== Test 2: EIO=3 with cookie-based session ===")
s = socks_tunnel()
if s:
    head, body = http_req(s, "GET", "/socket.io/?EIO=3&transport=polling")
    print(f"HEAD: {head}")
    print(f"BODY: {body}")
    m = re.search(r'"sid":"([^"]+)"', body)
    if m:
        sid = m.group(1)
        print(f"SID: {sid}")
        # Poll with sid
        s.settimeout(5)
        try:
            d = s.recv(65536)
            print(f"Poll 1: {d.decode(errors='replace')}")
        except socket.timeout:
            print("Poll 1: timeout")
        # Try POST /socket.io/?EIO=3&transport=polling with sid
        post_body = json.dumps({"name": "test_event", "data": "PENTEST"})
        head2, body2 = http_req(s, "POST", f"/socket.io/?EIO=3&transport=polling&sid={sid}", post_body)
        print(f"POST HEAD: {head2}")
        print(f"POST BODY: {body2}")
        # Poll again
        s.settimeout(5)
        try:
            d = s.recv(65536)
            print(f"Poll 2: {d.decode(errors='replace')}")
        except socket.timeout:
            print("Poll 2: timeout")
    s.close()

print("\n=== DONE ===")
