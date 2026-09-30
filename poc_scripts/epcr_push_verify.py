#!/usr/bin/env python3
"""
EPCR push verification — two-client test
Client A: listener (authenticated JWT, long-poll 30s)
Client B: emitter (authenticated JWT, emits Socket.IO event)
Check if A receives broadcast from B.
"""
import requests, json, time, re, threading
import datetime, jwt as pyjwt
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import warnings
warnings.filterwarnings("ignore")

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
HTTP_PORT = 4000
SOCKET_PORT = 4004
S = {"https": f"socks5://{PROXY_HOST}:{PROXY_PORT}"}
VERIFY = False

def forge_jwt(account="admin", role="ADMIN", user_id=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "account": account,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=48)).timestamp()),
        "permissions": [
            "DOCTOR_TEST_PUSH", "EPCR_PAGE_CASELIST", "EPCR_PAGE_CASEDETAIL",
            "EPCR_CASERECORD_READ", "EPCR_CASERECORD_UPDATE", "EPCR_CASERECORD_CREATE",
            "MONITOR_ALL", "AUTH_ROLE", "AUTH_USER", "MCI_DISPATCH",
            "HOSPITAL_PAGE_DISPATCH", "EPCR_PAGE_OHCACASELIST",
        ],
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def handshake_and_connect(session):
    resp = session.get(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
        proxies=S, verify=VERIFY, timeout=10,
    )
    sid = re.search(r'"sid":"([^"]+)"', resp.text).group(1)
    
    token = forge_jwt()
    connect_msg = f'40{{"token":"{token}"}}'
    connect_data = f"{len(connect_msg)}:{connect_msg}"
    resp2 = session.post(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
        data=connect_data,
        headers={"Content-Type": "text/plain;charset=utf-8"},
        proxies=S, verify=VERIFY, timeout=10,
    )
    return sid, resp2.status_code

# ─── Client A: Listener ───
listener_results = {"events": [], "done": False}

def listener():
    sess = requests.Session()
    sess.proxies = S
    sess.verify = VERIFY
    
    sid, status = handshake_and_connect(sess)
    print(f"[Listener A] Handshake+CONNECT: sid={sid[:15]}, HTTP {status}")
    
    if status != 200:
        print(f"[Listener A] CONNECT failed!")
        listener_results["done"] = True
        return
    
    print("[Listener A] Starting long-poll (30s window)...")
    t_end = time.time() + 30
    poll_count = 0
    
    while time.time() < t_end:
        try:
            resp = sess.get(
                f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
                proxies=S, verify=VERIFY, timeout=35,
            )
            poll_count += 1
            ts = time.strftime("%H:%M:%S")
            
            if resp.status_code == 200:
                body = resp.text
                # Parse Engine.IO packets
                pos = 0
                while pos < len(body):
                    m_len = re.match(r'(\d+):', body[pos:])
                    if not m_len:
                        break
                    plen = int(m_len.group(1))
                    data = body[pos + len(m_len.group(0)):pos + len(m_len.group(0)) + plen]
                    pos += len(m_len.group(0)) + plen
                    
                    if data.startswith("0"):
                        print(f"[{ts}] [A] Server OPEN/CONNECT packet")
                    elif data.startswith("2"):
                        print(f"[{ts}] [A] Server PING")
                    elif data.startswith("3"):
                        print(f"[{ts}] [A] Server PONG")
                    elif data.startswith("4"):
                        siotype = data[1] if len(data) > 1 else "?"
                        sio_names = {"0":"CONNECT", "1":"DISCONNECT", "2":"EVENT", "3":"ACK", "4":"CONNECT_ERROR"}
                        name = sio_names.get(siotype, f"type={siotype}")
                        print(f"[{ts}] [A] ✨ SOCKET.IO {name}: {data[2:][:200]}")
                        listener_results["events"].append(data)
                    elif data.startswith("41") or data.startswith("42"):
                        # Socket.IO EVENT (42) or CONNECT_ERROR (44)
                        print(f"[{ts}] [A] 📥 Socket.IO EVENT: {data[:200]}")
                        listener_results["events"].append(data)
                    else:
                        print(f"[{ts}] [A] Other packet: {data[:200]}")
            elif resp.status_code == 400:
                print(f"[{ts}] [A] ❌ 400: {resp.text[:150]} — session invalidated")
                break
            else:
                print(f"[{ts}] [A] HTTP {resp.status_code}: {resp.text[:100]}")
        except requests.exceptions.ReadTimeout:
            pass  # Expected for long-polling
        except Exception as e:
            print(f"[Listener A] Error: {e}")
            break
    
    print(f"[Listener A] Polling done ({poll_count} polls, {len(listener_results['events'])} events)")
    listener_results["done"] = True

# ─── Client B: Emitter ───
def emitter():
    time.sleep(3)  # Wait for listener to start polling
    
    sess = requests.Session()
    sess.proxies = S
    sess.verify = VERIFY
    
    sid, status = handshake_and_connect(sess)
    if status != 200:
        print(f"[Emitter B] CONNECT failed!")
        return
    
    print(f"[Emitter B] Authenticated (sid={sid[:15]})")
    
    # Try emitting Socket.IO EVENT packets
    # 42[eventName, payload]
    events_to_emit = [
        ('422["case/push", {"caseId":"EPCR_TEST","message":"dispatch test"}]', "case/push"),
        ('422["broadcast/case", {"caseId":"EPCR_TEST","status":"dispatched"}]', "broadcast/case"),
        ('422["dispatch/notify", {"caseId":"EPCR_TEST"}]', "dispatch/notify"),
        ('422["case/update", {"caseId":"EPCR_TEST","branch":"TPD"}]', "case/update"),
        ('422["notify", {"message":"test"}]', "notify"),
        ('422["newcase", {"caseId":"EPCR_TEST"}]', "newcase"),
        ('422["dispatch", {"caseId":"EPCR_TEST","type":"ohca"}]', "dispatch"),
        ('422["case_assign", {"caseId":"EPCR_TEST"}]', "case_assign"),
        ('422["pushcase", {"caseId":"EPCR_TEST"}]', "pushcase"),
    ]
    
    for payload, name in events_to_emit:
        framed = f'{len(payload)}:{payload}'
        try:
            resp = sess.post(
                f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
                data=framed,
                headers={"Content-Type": "text/plain;charset=utf-8"},
                proxies=S, verify=VERIFY, timeout=10,
            )
            print(f"[Emitter B] Emit '{name}': HTTP {resp.status_code} — {resp.text[:80]}")
        except Exception as e:
            print(f"[Emitter B] Emit '{name}': Error — {e}")

    print("[Emitter B] Done emitting")

# ─── Run both ───
print("=" * 60)
print("EPCR Push Verification — Two-Client Test")
print("=" * 60)

t_a = threading.Thread(target=listener)
t_b = threading.Thread(target=emitter)

t_a.start()
t_b.start()

t_a.join(timeout=70)
t_b.join(timeout=20)

print("\n" + "=" * 60)
print(f"RESULTS: {len(listener_results['events'])} events received by listener")
print("=" * 60)
