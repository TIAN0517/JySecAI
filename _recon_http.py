#!/usr/bin/env python3
"""HTTP request over a fresh SOCKS5 tunnel to the epcr target.
Usage: _recon_http.py <port> <method> <path> [body]
Prints status line + headers + (truncated) body.
"""
import socket, struct, sys, time

PROXY = ("202.160.76.157", 11082)
DEST_HOST = "epcr.tpf.gov.tw"
PORT = int(sys.argv[1])
METHOD = sys.argv[2]
PATH = sys.argv[3]
BODY = sys.argv[4] if len(sys.argv) > 4 else None

def socks_connect(s, host, port):
    s.sendall(b"\x05\x01\x00")
    # drain handshake reply
    hl = s.recv(4)
    print("handshake reply:", hl.hex(), file=sys.stderr)
    hb = host.encode()
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", port))
    s.settimeout(25)
    rep = b""
    while len(rep) < 4:
        c = s.recv(16)
        if not c:
            break
        rep += c
    print("connect reply:", rep.hex(), "status:", rep[1] if len(rep) > 1 else None, file=sys.stderr)
    return len(rep) > 1 and rep[1] == 0

s = socket.create_connection(PROXY, timeout=15)
if not socks_connect(s, DEST_HOST, PORT):
    print("SOCKS CONNECT FAILED")
    sys.exit(3)

req = f"{METHOD} {PATH} HTTP/1.1\r\nHost: {DEST_HOST}:{PORT}\r\nConnection: close\r\nUser-Agent: Mozilla/5.0 (recon)\r\n"
if BODY:
    req += f"Content-Type: application/json\r\nContent-Length: {len(BODY)}\r\n"
req += "\r\n"
if BODY:
    req += BODY
s.sendall(req.encode())

buf = b""
s.settimeout(25)
try:
    while True:
        d = s.recv(65536)
        if not d:
            break
        buf += d
        # stop once we've got a full response (Connection: close -> EOF anyway)
        if len(buf) > 200000:
            break
except socket.timeout:
    print("(timeout waiting for more data)", file=sys.stderr)
text = buf.decode(errors="replace")
# split headers/body
if "\r\n\r\n" in text:
    head, body = text.split("\r\n\r\n", 1)
    print("=== HEADERS ===")
    print(head[:1500])
    print("=== BODY (first 2500 chars) ===")
    print(body[:2500])
    print(f"\n[total bytes: {len(buf)}]")
else:
    print("RAW:", text[:2000])
s.close()
