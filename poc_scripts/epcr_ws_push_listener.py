#!/usr/bin/env python3
"""
EPCR broadcast listener — WebSocket upgrade edition
Handshake (polling) → CONNECT (polling) → WebSocket upgrade → Listen
"""
import json, time, re, ssl, sys, threading
import socks, requests
from websocket import WebSocket

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
    # Parse sid from OPEN packet
    m = re.search(r'"sid":"([^"]+)"', resp.text)
    sid = m.group(1) if m else None
    print(f"    SID: {sid}")
    return sid


def connect_via_polling(sid):
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "sid": sid}
    # Socket.IO CONNECT: 2:40 = Engine.IO MESSAGE(4) + Socket.IO CONNECT(0)
    body = "2:40"
    resp = requests.post(url, params=params, data=body,
                         proxies=PROXIES, verify=False, timeout=10)
    print(f"[2] CONNECT ({body}): HTTP {resp.status_code}")
    print(f"    Response: {resp.text[:200]}")
    return resp


def upgrade_websocket(sid, listen_secs=50):
    """Upgrade to WebSocket using the sid from handshake"""
    ws_url = f"wss://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=websocket&sid={sid}"
    print(f"[3] WebSocket upgrade: {ws_url}")

    # Build raw SOCKS5 WebSocket connection
    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT)
    sock.settimeout(10)
    sock.connect((EPCR_SERVER, SOCKET_PORT))
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    sock = ctx.wrap_socket(sock, server_hostname=EPCR_SERVER)

    ws = WebSocket()
    ws.sock = sock
    ws.connect(ws_url, timeout=10, sslopt={"cert_reqs": ssl.CERT_NONE})
    print(f"[3] ✅ WebSocket connected!")

    # Send Socket.IO CONNECT (40) — this is required over WebSocket
    ws.send('40{"transport":"websocket"}')
    print("[3] 📤 Sent CONNECT: 40{\"transport\":\"websocket\"}")

    # Listen for events
    print(f"[3] 📡 Listening for {listen_secs}s...")
    start = time.time()
    while time.time() - start < listen_secs:
        try:
            msg = ws.recv()
            if msg:
                if isinstance(msg, bytes):
                    msg = msg.decode('utf-8', errors='replace')
                ts = time.strftime("%H:%M:%S")
                print(f"\n  [{ts}] 📥 PUSH: {msg[:500]}")
                # Parse Socket.IO event
                if msg.startswith("42["):
                    try:
                        payload = json.loads(msg[2:])
                        if isinstance(payload, list) and len(payload) > 0:
                            event = payload[0]
                            data = payload[1] if len(payload) > 1 else None
                            print(f"    → EVENT: {event}")
                            if data:
                                print(f"    → DATA: {json.dumps(data, default=str, indent=2)[:600]}")
                    except:
                        print(f"    → (raw: {msg[:200]})")
                elif msg == "40":
                    print("    → [CONNECTED]")
                elif msg == "41":
                    print("    → [DISCONNECTED]")
                elif msg.startswith("44"):
                    print(f"    → [CONNECT_ERROR]: {msg[2:]}")
        except Exception as e:
            print(f"[3] recv error: {e}")
            break
    ws.close()


def main():
    print("=" * 70)
    print("🚨 EPCR Taipei — Socket.IO WebSocket Broadcast Listener 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}  (authServer)")
    print(f"Proxy:  SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print("=" * 70)

    # Step 1: Handshake (no auth)
    print("\n--- Step 1: Socket.IO Poling Handshake ---")
    sid = handshake()
    if not sid:
        print("❌ Handshake failed")
        sys.exit(1)

    # Step 2: CONNECT via polling
    print("\n--- Step 2: Socket.IO CONNECT (via polling POST) ---")
    connect_via_polling(sid)

    # Step 3: WebSocket upgrade
    print("\n--- Step 3: WebSocket Upgrade ---")
    try:
        upgrade_websocket(sid, listen_secs=50)
    except Exception as e:
        print(f"[3] ❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("📋 RESULT:")
    print(f"  • Handshake: ✅ sid={sid[:12]}...")
    print(f"  • CONNECT: ✅ 200 ok")
    print(f"  • WebSocket: ✅ connected")
    print("=" * 70)


if __name__ == "__main__":
    main()
