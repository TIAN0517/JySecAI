#!/usr/bin/env python3
"""SOCKS5-tunnel recon helper. Connects to the proxy, opens a persistent
SOCKS5 tunnel to the target, and streams plain TCP both ways.

Usage: _recon_proxy.py <dest_host> <dest_port>
  stdin  -> forwarded to dest
  stdout <- forwarded from dest
  (stderr kept for diagnostics)
"""
import socket, struct, sys, threading

PROXY = ("202.160.76.157", 11082)
HOST = sys.argv[1]
PORT = int(sys.argv[2])

s = socket.create_connection(PROXY, timeout=15)
s.sendall(b"\x05\x01\x00")
print("handshake:", s.recv(4).hex(), file=sys.stderr)
hb = HOST.encode()
s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", PORT))
s.settimeout(25)
rep = s.recv(16)
print("connect reply:", rep.hex(), "status:", rep[1], file=sys.stderr)
if rep[1] != 0:
    print("CONNECT FAILED status=%d" % rep[1], file=sys.stderr)
    sys.exit(3)

# pump stdin -> dest
def up():
    try:
        while True:
            d = sys.stdin.buffer.read(4096)
            if not d:
                break
            s.sendall(d)
    except Exception as e:
        pass
    finally:
        try:
            s.shutdown(socket.SHUT_WR)
        except Exception:
            pass

t = threading.Thread(target=up, daemon=True)
t.start()

# pump dest -> stdout
try:
    while True:
        d = s.recv(65536)
        if not d:
            break
        sys.stdout.buffer.write(d)
        sys.stdout.buffer.flush()
except Exception as e:
    print("recv err:", e, file=sys.stderr)
s.close()
