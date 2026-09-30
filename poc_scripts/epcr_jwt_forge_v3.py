#!/usr/bin/env python3
"""
EPCR JWT Forge v3 — fix Engine.IO message framing
Format: <len>:40{"token":"<jwt>"}
Not: 2:40{"token":"<jwt>"} (wrong frame)
"""
import requests, json, time, re, ssl, threading
import datetime
import jwt as pyjwt
from websocket import WebSocketApp

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
S = f"socks5://{PROXY_HOST}:{PROXY_PORT}"

def forge_jwt(account="admin", role="ADMIN", user_id=1, expires_hours=48):
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        "sub": str(user_id),
        "account": account,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=expires_hours),
    }, JWT_SECRET, algorithm="HS256")

def handshake():
    sess = requests.Session()
    sess.proxies = {"https": S}
    sess.verify = False
    resp = sess.get(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
        timeout=10,
    )
    sid = re.search(r'"sid":"([^"]+)"', resp.text).group(1)
    return sess, sid

def send_connect(sess, sid, token, fmt="token"):
    """Send Socket.IO CONNECT with JWT in correct Engine.IO format"""
    if fmt == "token":
        auth = json.dumps({"token": token})
    elif fmt == "auth_token":
        auth = json.dumps({"auth": {"token": token}})
    elif fmt == "bearer":
        auth = json.dumps({"auth": {"bearer": token}})
    
    # Correct Engine.IO format: <len>:40{auth_payload}
    connect_msg = f"40{auth}"
    connect_data = f"{len(connect_msg)}:{connect_msg}"
    
    print(f"  POST data: {connect_data[:80]}...")
    try:
        resp = sess.post(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            data=connect_data,
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=15,
        )
        print(f"  CONNECT: HTTP {resp.status_code} — {resp.text[:300]}")
        return resp
    except requests.exceptions.ConnectionError as e:
        print(f"  CONNECT: Connection closed! {e}")
        return None
    except Exception as e:
        print(f"  CONNECT: Error — {e}")
        return None

# Test different JWT + format combinations
token = forge_jwt(account="admin", role="ADMIN", user_id=1)
print(f"JWT Secret: {JWT_SECRET}")
print(f"JWT: {token[:60]}...")

for fmt in ["token", "auth_token", "bearer"]:
    print(f"\n--- Format: {fmt} ---")
    try:
        sess, sid = handshake()
        print(f"  Handshake: sid={sid}")
    except Exception as e:
        print(f"  Handshake failed: {e}")
        continue
    
    resp = send_connect(sess, sid, token, fmt)
    
    if resp and resp.status_code != 400:
        # Try long-poll
        try:
            poll = sess.get(
                f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
                timeout=25,
            )
            print(f"  Long-poll: HTTP {poll.status_code} — {poll.text[:300]}")
        except Exception as e:
            print(f"  Long-poll error: {e}")

# Also try without auth (just 2:40) to see if session stays alive with different polling timing
print("\n\n=== Test: no auth, immediate polling ===\n")
sess, sid = handshake()
print(f"Handshake: sid={sid}")

# Send CONNECT without auth
try:
    resp = sess.post(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
        data="2:40",
        headers={"Content-Type": "text/plain;charset=utf-8"},
        timeout=10,
    )
    print(f"CONNECT (no auth): HTTP {resp.status_code} — {resp.text[:100]}")
except Exception as e:
    print(f"CONNECT error: {e}")

# Poll immediately with short timeout
for i in range(3):
    try:
        resp = sess.get(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            timeout=5,
        )
        print(f"  Poll {i+1}: HTTP {resp.status_code} — {resp.text[:200]}")
        if '"code":1' in resp.text:
            print("  → Session invalidated")
            break
    except Exception as e:
        print(f"  Poll {i+1}: Error — {e}")
        break

# Try WebSocket with JWT in CONNECT (via ws query param)
print("\n\n=== Test: WebSocket with JWT in url query ===\n")
sess2 = requests.Session()
sess2.proxies = {"https": S}
sess2.verify = False
token2 = forge_jwt(account="admin", role="ADMIN", user_id=1)
resp = sess2.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
    timeout=10,
)
sid2 = re.search(r'"sid":"([^"]+)"', resp.text).group(1)
ws_url = f"wss://{SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=websocket&sid={sid2}"
print(f"WS URL: {ws_url[:80]}...")

msgs = []
def on_msg(ws, msg):
    if isinstance(msg, bytes): msg = msg.decode('utf-8', errors='replace')
    print(f"  📥 {msg[:500]}")
    msgs.append(msg)

def on_open(ws):
    print("  ✅ WS open — sending CONNECT with JWT")
    ws.send(f'40{{"token":"{token2}"}}')
    print("  📤 Sent CONNECT")

def on_close(ws, *a):
    print("  🔌 WS closed")

def on_err(ws, e):
    print(f"  ⚠️ WS err: {e}")

ws = WebSocketApp(ws_url, on_message=on_msg, on_open=on_open,
                  on_close=on_close, on_error=on_err)
t = threading.Thread(target=ws.run_forever, kwargs={
    "http_proxy_host": PROXY_HOST, "http_proxy_port": PROXY_PORT,
    "proxy_type": "socks5",
    "sslopt": {"cert_reqs": ssl.CERT_NONE},
    "ping_interval": 20, "ping_timeout": 10,
})
t.daemon = True
t.start()
t.join(timeout=20)
print(f"Messages: {len(msgs)}")

# Also try WebSocket with JWT in URL params directly
print("\n\n=== Test: WebSocket with JWT in ws URL ===\n")
token3 = forge_jwt(account="admin", role="ADMIN", user_id=1)
ws_url2 = f"wss://{SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=websocket&sid={sid2}&token={token3}"

msgs2 = []
def on_open2(ws):
    print("  ✅ WS open (no send, JWT in URL)")

def on_msg2(ws, msg):
    if isinstance(msg, bytes): msg = msg.decode('utf-8', errors='replace')
    print(f"  📥 {msg[:500]}")
    msgs2.append(msg)

def on_close2(ws, *a):
    print("  🔌 WS closed")

def on_err2(ws, e):
    print(f"  ⚠️ WS err: {e}")

ws2 = WebSocketApp(ws_url2, on_message=on_msg2, on_open=on_open2,
                   on_close=on_close2, on_error=on_err2)
t2 = threading.Thread(target=ws2.run_forever, kwargs={
    "http_proxy_host": PROXY_HOST, "http_proxy_port": PROXY_PORT,
    "proxy_type": "socks5",
    "sslopt": {"cert_reqs": ssl.CERT_NONE},
    "ping_interval": 20, "ping_timeout": 10,
})
t2.daemon = True
t2.start()
t2.join(timeout=20)
print(f"Messages: {len(msgs2)}")

print("\n=== Done ===")
