#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4004 authServer Socket.IO WebSocket upgrade 测试"""
import socket, ssl, time, json, base64, struct, os, urllib.parse

HOST = "epcr.tpf.gov.tw"
PORT = 4004


def ws_handshake(host, port, path):
    sock = socket.create_connection((host, port), timeout=10)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    key = base64.b64encode(os.urandom(16)).decode()
    crlf = "\r\n"
    req = (
        "GET " + path + " HTTP/1.1" + crlf +
        "Host: " + host + ":" + str(port) + crlf +
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
        print("[!] WS handshake failed: " + response[:200].decode(errors='replace'))
        ssock.close()
        return None
    print("[+] WS handshake OK")
    return ssock


def ws_recv(ssock, timeout=5):
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
    except socket.timeout:
        return None


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


def main():
    print("=" * 80)
    print("4004 authServer WS 升级测试")
    print("=" * 80)

    print("\n[测试 1] 根 NS WS 握手")
    ws = ws_handshake(HOST, PORT, "/socket.io/?EIO=4&transport=websocket")
    if not ws:
        return
    msg = ws_recv(ws, timeout=5)
    if msg:
        opcode, payload = msg
        text = payload.decode(errors='replace')
        print("  Recv opcode=" + str(opcode) + " payload=" + text[:200])
    print("\n[测试 2] 发 Engine.IO CONNECT (40)")
    ws_send(ws, "40")
    msg = ws_recv(ws, timeout=5)
    if msg:
        opcode, payload = msg
        text = payload.decode(errors='replace')
        print("  Recv opcode=" + str(opcode) + " payload=" + text[:200])
    print("\n[测试 3] 发 42[subscribe,...]")
    ws_send(ws, '42["subscribe",{"roomName":"test"}]')
    time.sleep(2)
    msg = ws_recv(ws, timeout=5)
    if msg:
        opcode, payload = msg
        text = payload.decode(errors='replace')
        print("  Recv opcode=" + str(opcode) + " payload=" + text[:200])
    else:
        print("  (timeout / 无响应)")
    ws.close()


if __name__ == "__main__":
    main()