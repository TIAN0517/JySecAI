#!/usr/bin/env python3
"""Persistent-tunnel HTTP: keep ONE socks tunnel open, issue multiple
requests on it. Used to hammer the flaky epcr:4000-4008 targets."""
import socket, struct, sys, time

PROXY = ("202.160.76.157", 11082)
DEST_HOST = "epcr.tpf.gov.tw"
PORT = int(sys.argv[1])

def tunnel(port):
    s = socket.create_connection(PROXY, timeout=15)
    s.sendall(b"\x05\x01\x00")
    s.recv(4)
    hb = DEST_HOST.encode()
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", port))
    s.settimeout(20)
    rep = b""
    while len(rep) < 4:
        c = s.recv(16)
        if not c: break
        rep += c
    return s, (len(rep) > 1 and rep[1] == 0)

def req(s, method, path, body=None, ctype="application/json"):
    s.settimeout(20)
    r = f"{method} {path} HTTP/1.1\r\nHost: {DEST_HOST}:{PORT}\r\nConnection: keep-alive\r\nUser-Agent: Mozilla/5.0\r\n"
    if body is not None:
        r += f"Content-Type: {ctype}\r\nContent-Length: {len(body.encode())}\r\n"
    r += "\r\n"
    if body is not None:
        r += body
    s.sendall(r.encode())
    buf = b""
    # read until we have a complete response (for keep-alive, read header then content-length)
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
        # try to parse content-length
        import re
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
    return buf.decode(errors="replace")

def fresh():
    s, ok = tunnel(PORT)
    return s, ok

def call(method, path, body=None, ctype="application/json", tries=3):
    last = None
    for t in range(tries):
        s, ok = fresh()
        if not ok:
            last = "[connect failed]"
            continue
        try:
            out = req(s, method, path, body, ctype)
            s.close()
            if out.strip():
                return out
            last = "[empty]"
        except Exception as e:
            last = f"[err {e}]"
            try: s.close()
            except: pass
    return last or "[no data]"

if __name__ == "__main__":
    # args after port: pairs of method path [body]
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        method = args[i]
        path = args[i+1]
        body = None
        if i+2 < len(args) and args[i+2] != "-":
            body = args[i+2]
            i += 3
        else:
            i += 2
        print(f"\n########## {method} {path} ##########")
        out = call(method, path, body)
        print(out[:4000])
