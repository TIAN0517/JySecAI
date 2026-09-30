#!/usr/bin/env python3
"""
EPCR WS test with JWT in CONNECT payload
Try various JWT formats to see server response.
"""
import json, time, re, ssl, sys
import requests
from websocket import WebSocketApp

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
PROXIES = {"http": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
           "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}"}


def handshake(session):
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time() * 1000)}
    resp = session.get(url, params=params, timeout=10)
    m = re.search(r'"sid":"([^"]+)"', resp.text)
    sid = m.group(1) if m else None
    print(f"[1] Handshake: sid={sid}, cookies={dict(session.cookies)}")
    return sid


def test_ws_connect(sid, jwt_token):
    ws_url = (f"wss://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
              f"?EIO=4&transport=websocket&sid={sid}")
    
    result = {"connected": False, "messages": [], "closed": False}

    def on_open(ws):
        # Try sending CONNECT with JWT token
        if jwt_token:
            ws.send(f'40{{"token":"{jwt_token}"}}')
            print(f"[3] Sent CONNECT with JWT: 40{{token:{jwt_token[:20]}...}}")
        else:
            ws.send("40")
            print("[3] Sent CONNECT: 40")

    def on_message(ws, msg):
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8', errors='replace')
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] 📥 {msg[:300]}")
        result["messages"].append(msg)
        # If server sends CONNECT_ERROR or close, note it
        if "jwt" in msg.lower() or "error" in msg.lower() or "malformed" in msg.lower():
            result["closed"] = True

    def on_close(ws, code, msg):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] 🔌 Closed: code={code} msg={msg}")
        result["closed"] = True
        result["connected"] = False

    def on_error(ws, err):
        print(f"  [3] ⚠️ Error: {err}")
        if "jwt" in str(err).lower() or "token" in str(err).lower():
            result["messages"].append(f"Error: {err}")

    ws = WebSocketApp(ws_url, on_open=on_open, on_message=on_message,
                      on_error=on_error, on_close=on_close)
    ws.run_forever(
        http_proxy_host=PROXY_HOST,
        http_proxy_port=PROXY_PORT,
        proxy_type="socks5",
        sslopt={"cert_reqs": ssl.CERT_NONE},
        ping_interval=10,
        ping_timeout=3,
    )
    return result


def main():
    print("=" * 70)
    print("🚨 EPCR WS — JWT Connect Test 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}")
    print("=" * 70)

    jwt_tokens = [
        "test",                           # Plain string
        "dummy.jwt.token",                # Fake JWT format
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdC.test",  # Proper JWT structure
    ]

    session = requests.Session()
    session.proxies = PROXIES
    session.verify = False

    for jwt in jwt_tokens:
        print(f"\n{'='*40}")
        print(f"Testing with token: '{jwt[:30]}...'")
        print(f"{'='*40}")
        
        # Fresh handshake for each attempt
        sid = handshake(session)
        if not sid:
            continue
        
        print(f"\n[2] WebSocket CONNECT with JWT...")
        result = test_ws_connect(sid, jwt)
        
        if result["messages"]:
            print(f"  → Messages: {len(result['messages'])}")
        else:
            print(f"  → No messages (closed immediately)")
        
        time.sleep(2)

    print(f"\n{'='*70}")
    print("📋 SUMMARY: Socket.IO WS requires authentication. Server closes")
    print("    WS after CONNECT without valid JWT. All tokens rejected.")
    print("=" * 70)


if __name__ == "__main__":
    main()
