#!/usr/bin/env python3
"""Probe epcr.tpf.gov.tw:4000 Socket.IO via polling transport.
Goal: enumerate namespaces, listen for pushed events, attempt event emission.
"""
import http.client
import urllib.parse
import json
import sys
import time

HOST = "epcr.tpf.gov.tw"
PORT = 4000
BASE = f"/socket.io/"

def req(method, path, body=None, cookies=""):
    conn = http.client.HTTPSConnection(HOST, PORT, timeout=15)
    headers = {
        "User-Agent": "Mozilla/5.0 CyberStrike/1.0",
        "Accept": "*/*",
        "Origin": "https://epcr.tpf.gov.tw:4000",
    }
    if cookies:
        headers["Cookie"] = cookies
    if body is not None:
        # EIO v4 polling POST must be raw octet-stream length-prefixed form
        # but most servers accept raw body too
        headers["Content-Type"] = "text/plain;charset=UTF-8"
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    setcookie = resp.getheader("set-cookie", "")
    print(f"--- {method} {path}")
    print(f"  status: {resp.status} {resp.reason}")
    print(f"  set-cookie: {setcookie!r}")
    print(f"  body ({len(data)} bytes): {data[:800]!r}")
    print()
    conn.close()
    return data, setcookie

# 1) Handshake
print("=== HANDSHAKE ===")
hs_body, hs_cookie = req("GET", f"{BASE}?EIO=4&transport=polling")
# Extract sid and io cookie value
sid = None
io_cookie = ""
for sc in hs_cookie.split(", "):
    if sc.startswith("io="):
        io_cookie = sc.split(";")[0]
        print(f"  -> io cookie: {io_cookie}")
if not io_cookie:
    io_cookie = ""
# Parse sid from body
try:
    # body: '96:0{"sid":"..."...}'
    payload = hs_body.split(b"0", 1)[1]
    obj = json.loads(payload)
    sid = obj["sid"]
    print(f"  -> sid: {sid}")
except Exception as e:
    print(f"  parse fail: {e}")
    sys.exit(1)

cookies = io_cookie

# 2) Try multiple namespaces: /admin, /events, /socket, /live, /monitor, /hosp
print("\n=== NAMESPACE PROBE ===")
for ns in ["", "/admin", "/events", "/socket", "/live", "/monitor",
          "/hosp", "/hospital", "/doctor", "/monitor-server",
          "/case", "/case-detail", "/caseDetail", "/record",
          "/socket.io/", "/vital", "/auth", "/auth-server"]:
    path = f"{BASE}?EIO=4&transport=polling"
    body = f'40{ns}'  # CONNECT to namespace
    out, _ = req("POST", path, body=body, cookies=cookies)
    if b"NOOP" not in out and b'"sid"' in out:
        print(f"  ! NON-NOOP response on ns={ns!r}: {out[:200]!r}")
    time.sleep(0.3)

# 3) Send a Socket.IO event: 42["eventName", payload]
print("\n=== EVENT EMISSION PROBE ===")
events_to_try = [
    ("hello", {}),
    ("ping", {}),
    ("join", {"room": "events"}),
    ("join", "events"),
    ("subscribe", "events"),
    ("auth", {"token": "anonymous"}),
    ("login", {"user": "guest"}),
    ("getCase", {"caseId": "180817092350fed7"}),
    ("getEvents", {}),
    ("request", {"type": "events"}),
]
for ev, payload in events_to_try:
    pdata = f'42{json.dumps([ev, payload])}'
    out, _ = req("POST", f"{BASE}?EIO=4&transport=polling&sid={sid}",
                 body=pdata, cookies=cookies)
    time.sleep(0.2)

# 4) Long-poll: GET server messages
print("\n=== SERVER POLL (long-poll 5s) ===")
out, _ = req("GET", f"{BASE}?EIO=4&transport=polling&sid={sid}",
             cookies=cookies)
print("Final body:", out[:500])

print("\nDONE.")
