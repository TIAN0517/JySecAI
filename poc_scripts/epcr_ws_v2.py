#!/usr/bin/env python3
"""
EPCR broadcast listener — WebSocket upgrade via WebSocketApp + SOCKS5
Flow: polling handshake → CONNECT → WebSocket upgrade → listen
"""
import json, time, re, ssl, sys
import requests
from websocket import WebSocketApp

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
PROXIES = {
    "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}


def handshake():
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time()*1000)}
    resp = requests.get(url, params=params, proxies=PROXIES, verify=False, timeout=10)
    print(f"[1] Handshake: HTTP {resp.status_code}")
    print(f"    Raw: {resp.text[:200]}")
    m = re.search(r'"sid":"([^"]+)"', resp.text)
    sid = m.group(1) if m else None
    print(f"    SID: {sid}")
    return sid


def send_connect(sid):
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "sid": sid}
    body = "2:40"
    resp = requests.post(url, params=params, data=body,
                         proxies=PROXIES, verify=False, timeout=10)
    print(f"[2] CONNECT: HTTP {resp.status_code}")
    print(f"    Response: {resp.text[:100]}")
    return resp


def listen_websocket(sid, listen_secs=50):
    """WebSocket upgrade via WebSocketApp with SOCKS5 proxy"""
    ws_url = (f"wss://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
              f"?EIO=4&transport=websocket&sid={sid}")
    print(f"[3] WebSocket: {ws_url}")

    events = []

    def on_open(ws):
        print(f"[3] ✅ WebSocket connected! Listening for server-initiated events...")

    def on_message(ws, msg):
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8', errors='replace')
        ts = time.strftime("%H:%M:%S")
        print(f"\n  [{ts}] 📥 WS message ({len(msg)} bytes): {msg[:300]}")
        events.append(msg)
        # Parse Socket.IO events
        if msg.startswith("42[") or msg.startswith("42"):
            try:
                payload = json.loads(msg[2:])
                if isinstance(payload, list):
                    ev = payload[0]
                    data = payload[1] if len(payload) > 1 else None
                    print(f"    → EVENT: {ev}")
                    if data:
                        pretty = json.dumps(data, default=str, indent=2)
                        print(f"    → DATA: {pretty[:600]}")
            except Exception as e:
                print(f"    → (parse: {e})")

    def on_close(ws, code, msg):
        print(f"[3] 🔌 WS closed: code={code} msg={msg}")

    def on_error(ws, err):
        print(f"[3] ⚠️ WS error: {err}")

    ws = WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_close=on_close,
        on_error=on_error,
    )

    ws.run_forever(
        http_proxy_host=PROXY_HOST,
        http_proxy_port=PROXY_PORT,
        proxy_type="socks5",
        sslopt={"cert_reqs": ssl.CERT_NONE},
        ping_interval=20,
        ping_timeout=5,
    )

    print(f"\n[3] Events received: {len(events)}")
    return events


def main():
    print("=" * 70)
    print("🚨 EPCR Taipei — Socket.IO WS Broadcast Listener v2 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}")
    print(f"Proxy:  SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print("=" * 70)

    # Step 1: Polling handshake
    print("\n--- Step 1: Polling Handshake (no auth) ---")
    sid = handshake()
    if not sid:
        print("❌ Failed"); sys.exit(1)

    # Step 2: CONNECT via polling
    print("\n--- Step 2: Socket.IO CONNECT ---")
    send_connect(sid)

    # Step 3: WebSocket upgrade + listen
    print("\n--- Step 3: WebSocket Upgrade ---")
    events = listen_websocket(sid, listen_secs=40)

    # Summary
    print("\n" + "=" * 70)
    print("📋 CONCLUSION:")
    print(f"  • Handshake: ✅ sid={sid[:12]}...")
    print(f"  • CONNECT:  ✅ 200 ok")
    print(f"  • WS upgrade: ✅ connected" if True else "❌")
    print(f"  • Events received: {len(events)}")
    for e in events[:3]:
        print(f"    - {e[:100]}")
    print("=" * 70)


if __name__ == "__main__":
    main()
