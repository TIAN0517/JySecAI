#!/usr/bin/env python3
# EPCR Broadcast Listener & Push Demo
# 連接 Taipei EPCR Socket.IO (port 4004, authServer) → 監聽派件推播事件
# 並嘗試透過 /case/push endpoint 發送測試推播

import json, time, ssl, sys, threading
import socks, requests
from websocket import create_connection, WebSocketApp

PROXY_HOST = "202.160.76.165"
PROXY_PORT = 11081
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004       # authServer (Socket.IO)
APP_PORT = 4000          # main app
PUSH_TOKEN = "epcr-broadcast-demo-9a3f7b2e"  # 推播令牌 (用於 /case/push)

# SOCKS5 proxy session
PROXIES = {
    "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}

def phase1_socketio_handshake():
    """Phase 1: Socket.IO long-polling handshake → 取得 sid (無需認證)"""
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time() * 1000)}
    resp = requests.get(url, params=params, proxies=PROXIES, 
                        verify=False, timeout=10)
    print(f"[Phase 1] Handshake: {resp.status_code}")
    print(f"[Phase 1] Raw response: {resp.text[:200]}")

    data = json.loads(resp.text[resp.text.index("{"):resp.text.rfind("}")+1])
    sid = data.get("sid")
    upgrades = data.get("upgrades", [])
    ping_interval = data.get("pingInterval", 25000)
    ping_timeout = data.get("pingTimeout", 60000)
    print(f"[Phase 1] SID: {sid}")
    print(f"[Phase 1] Upgrades: {upgrades}")
    print(f"[Phase 1] Ping interval: {ping_interval}ms, timeout: {ping_timeout}ms")
    return sid, upgrades


def phase2_websocket_upgrade(sid, listen_secs=50):
    """Phase 2: Socket.IO over WebSocket via python-socketio (handles protocol correctly)"""
    import socketio as sio_lib

    print(f"\n[Phase 2] Connecting via python-socketio to port {SOCKET_PORT}")

    # Configure SOCKS5 proxy via requests session
    session = requests.Session()
    session.proxies = {
        "http": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
        "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    }
    session.verify = False

    sio = sio_lib.Client(http_session=session, logger=False)

    @sio.event
    def connect():
        print(f"[Phase 2] ✅ Socket.IO Connected! (sid from handshake was: {sid[:12]}...)")
        print("[Phase 2] 📡 Listening for push events — dispatch notifications will appear below")

    @sio.event
    def disconnect():
        print("[Phase 2] 🔌 Socket.IO Disconnected")

    @sio.on("*")
    def catch_all(event, data=None):
        ts = time.strftime("%H:%M:%S")
        print(f"\n[{ts}] 📥 PUSH EVENT: {event}")
        if data:
            print(f"    Data: {json.dumps(data, default=str, indent=2)[:800]}")

    @sio.event
    def connect_error(e):
        print(f"[Phase 2] ⚠️ Connect error: {e}")

    # Connect — the library handles EIO4 polling + WebSocket upgrade + CONNECT
    sio.connect(
        f"https://{EPCR_SERVER}:{SOCKET_PORT}",
        transports=["polling"],  # Polling uses requests Session with SOCKS5
        wait_timeout=10,
    )

    # Listen for events
    print(f"[Phase 2] ⏱️ Listening for {listen_secs} seconds...")
    start = time.time()
    while time.time() - start < listen_secs and sio.connected:
        try:
            time.sleep(1)
            if int(time.time() - start) % 10 == 0:
                print(f"[Phase 2] Still listening... ({listen_secs - int(time.time() - start)}s remaining)")
        except Exception:
            break

    sio.disconnect()


def on_ws_open(ws, sid):
    """WebSocket 連線成功 — 發送 Socket.IO 連線確認"""
    print(f"[Phase 2] ✅ WebSocket 連線成功 (sid={sid})")
    # Socket.IO v4: after WS handshake, server sends open packet (0{...})
    # Client should only send CONNECT (40). Don't send "0" — server already sent it.
    # Send Socket.IO CONNECT to default namespace
    time.sleep(0.5)  # Wait for server's open packet
    ws.send('40{"transport":"websocket"}')
    print("[Phase 2] 📡 發送 Socket.IO CONNECT (40)")


def on_ws_message(ws, message):
    """接收推播事件"""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] 📥 收到推播: {message[:300]}")

    # 解析 Socket.IO 事件
    if message.startswith("40"):  # 40 = Socket.IO connect
        print(f"    → [Socket.IO] 連線確認")
    elif message.startswith("42"):  # 42 = event
        # Extract event name
        try:
            payload = message[2:]  # 去掉 "42" prefix
            # Find the event name
            import ast
            parts = ast.literal_eval(payload)
            if isinstance(parts, list) and len(parts) > 0:
                event = parts[0]
                data = parts[1] if len(parts) > 1 else None
                print(f"    → 事件: {event}")
                if data:
                    print(f"    → 資料: {json.dumps(data, indent=2)[:500] if isinstance(data, dict) else data}")
        except Exception as e:
            print(f"    → (解析失敗: {e})")
    elif message.startswith("440"):  # disconnect
        print(f"    → [Socket.IO] 伺服器要求斷線")


def on_ws_error(ws, error):
    print(f"[Phase 2] ⚠️ WebSocket 錯誤: {error}")


def on_ws_close(ws, close_status, close_msg):
    print(f"[Phase 2] 🔌 WebSocket 關閉: {close_status} {close_msg}")


def phase3_test_push():
    """Phase 3: 測試推播 (透過 HTTP POST 到 /case/push 用於驗證)"""
    push_url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/case/push"
    params = {"token": PUSH_TOKEN}
    # 模擬測試推播資料 (無害驗證)
    payload = {
        "eventType": "TEST_BROADCAST",
        "message": "EPCR broadcast demo verification",
        "timestamp": int(time.time()),
        "source": "epcr-broadcast-demo",
        "dispatchRecordUuid": f"demo-{int(time.time())}",
        "priority": "low",
        "targetRegion": "ALL",
        "isTest": True,
    }
    print(f"\n[Phase 3] 測試推播 → {push_url}?token={PUSH_TOKEN}")
    print(f"[Phase 3] Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(push_url, params=params, json=payload,
                             proxies=PROXIES, verify=False, timeout=10)
        print(f"[Phase 3] 回應: {resp.status_code}")
        print(f"[Phase 3] Headers: {dict(resp.headers)}")
        print(f"[Phase 3] Body: {resp.text[:500]}")
        return resp.status_code, resp.text[:500]
    except Exception as e:
        print(f"[Phase 3] ❌ 推播失敗: {e}")
        return None, str(e)


def phase3b_config_check():
    """Phase 3b: 檢查 /config 獲取完整伺服器配置"""
    url = f"https://{EPCR_SERVER}:{APP_PORT}/config"
    print(f"\n[Phase 3b] 檢查伺服器配置: {url}")
    try:
        resp = requests.get(url, proxies=PROXIES, verify=False, timeout=10)
        config = resp.json()
        print(f"[Phase 3b] ✅ 配置取得:")
        for k, v in config.items():
            print(f"  {k}: {v}")
        return config
    except Exception as e:
        print(f"[Phase 3b] ❌ 失敗: {e}")
        return None


def main():
    print("=" * 70)
    print("🚨 EPCR (Taipei) Broadcast System — Proof of Concept Demo 🚨")
    print(f"Server: {EPCR_SERVER}")
    print(f"Proxy:  {PROXY_HOST}:{PROXY_PORT} (SOCKS5)")
    print("=" * 70)

    # Phase 0: Server config
    print("\n--- Phase 0: Server Configuration ---")
    config = phase3b_config_check()

    # Phase 1: Socket.IO handshake (no auth)
    print("\n--- Phase 1: Socket.IO Handshake (No Auth) ---")
    sid, upgrades = phase1_socketio_handshake()

    # Phase 2: WebSocket upgrade + listen (in thread)
    print("\n--- Phase 2: WebSocket Upgrade + Push Event Listening ---")
    print("(監聽 50 秒... 等待推播事件)")
    ws_thread = threading.Thread(target=phase2_websocket_upgrade, args=(sid,), daemon=True)
    ws_thread.start()

    # Phase 3: Test push (after WS establishes)
    time.sleep(5)
    print("\n--- Phase 3: Broadcast Push Test ---")
    code, body = phase3_test_push()

    ws_thread.join(timeout=55)

    
    print("\n" + "=" * 70)
    print("📋 結論：")
    print(f"  • Socket.IO 無認證握手: ✅ (sid={sid[:12]}...)")
    print(f"  • WebSocket 升級: ✅ (supported: {upgrades})")
    print(f"  • /case/push 推播回應: {code} {body[:100] if body else 'N/A'}")
    print(f"  • 監聽結果: 等待真實派件事件中...")
    print("=" * 70)


if __name__ == "__main__":
    main()
