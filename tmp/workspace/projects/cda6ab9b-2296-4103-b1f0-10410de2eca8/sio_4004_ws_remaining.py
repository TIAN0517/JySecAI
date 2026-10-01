#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4004 Socket.IO client.* / server.* 剩余事件测试（单独连接避免 SSL EOF 中断）"""
import socket, ssl, time, base64, struct, os

HOST = "epcr.tpf.gov.tw"
PORT = 4004


def ws_handshake(path):
    sock = socket.create_connection((HOST, PORT), timeout=10)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ssock = ctx.wrap_socket(sock, server_hostname=HOST)
    key = base64.b64encode(os.urandom(16)).decode()
    crlf = "\r\n"
    req = (
        "GET " + path + " HTTP/1.1" + crlf +
        "Host: " + HOST + ":" + str(PORT) + crlf +
        "Upgrade: websocket" + crlf +
        "Connection: Upgrade" + crlf +
        "Sec-WebSocket-Key: " + key + crlf +
        "Sec-WebSocket-Version: 13" + crlf +
        "Sec-WebSocket-Protocol: socket.io" + crlf +
        "Origin: https://epcr.tpf.gov.tw" + crlf +
        crlf
    )
    ssock.send(req.encode())
    response = b""
    while b"\r\n\r\n" not in response:
        chunk = ssock.recv(4096)
        if not chunk:
            break
        response += chunk
    if b"101 Switching Protocols" not in response:
        ssock.close()
        return None
    return ssock


def ws_recv(ssock, timeout=3):
    ssock.settimeout(timeout)
    try:
        h = ssock.recv(2)
        if len(h) < 2:
            return None
        b1, b2 = h[0], h[1]
        opcode = b1 & 0x0f
        length = b2 & 0x7f
        if length == 126:
            ext = ssock.recv(2)
            length = struct.unpack(">H", ext)[0]
        elif length == 127:
            ext = ssock.recv(8)
            length = struct.unpack(">Q", ext)[0]
        payload = b""
        while len(payload) < length:
            chunk = ssock.recv(length - len(payload))
            if not chunk:
                break
            payload += chunk
        return opcode, payload
    except (socket.timeout, ssl.SSLEOFError, ConnectionResetError, BrokenPipeError) as e:
        return ("EXC", str(type(e).__name__).encode())


def ws_send(ssock, text):
    data = text.encode()
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    header = bytes([0x81])
    if len(data) < 126:
        header += bytes([0x80 | len(data)])
    elif len(data) < 65536:
        header += bytes([0x80 | 126]) + struct.pack(">H", len(data))
    else:
        header += bytes([0x80 | 127]) + struct.pack(">Q", len(data))
    ssock.send(header + mask + masked)


def single_test(event):
    ws = ws_handshake("/socket.io/?EIO=4&transport=websocket")
    if not ws:
        return "HANDSHAKE_FAILED"
    msg = ws_recv(ws, timeout=3)
    ws_send(ws, "40")
    ws_recv(ws, timeout=3)
    try:
        ws_send(ws, event)
        time.sleep(1)
        msg = ws_recv(ws, timeout=3)
        if msg is None:
            return "SILENT_TIMEOUT"
        if isinstance(msg, tuple) and msg[0] == "EXC":
            return "EXC:" + msg[1].decode(errors='replace')
        opcode, payload = msg
        return "RECV:" + payload.decode(errors='replace')[:150]
    except (ssl.SSLEOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
        return "SSL_EOF:" + type(e).__name__


import socket as socket_mod

print("=" * 80)
print("4004 Socket.IO client.* / server.* 剩余事件测试")
print("=" * 80)

events = [
    '42["client.subscribe",{"roomName":"test"}]',
    '42["client.unsubscribe",{"roomName":"test"}]',
    '42["client.login",{"username":"admin"}]',
    '42["client.authenticate",{"token":"anonymous"}]',
    '42["server.subscribe",{"roomName":"test"}]',
    '42["server.broadcast",{"data":"test"}]',
]

for ev in events:
    result = single_test(ev)
    print("  " + ev[:60])
    print("    -> " + result)