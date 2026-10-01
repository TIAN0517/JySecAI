#!/usr/bin/env python3
"""epcr.tpf.gov.tw:4000 Socket.IO v4 polling - explore namespaces & emit events."""
import http.client, json, sys, time, socket

HOST = "epcr.tpf.gov.tw"
PORT = 4000

def parse_eio(blob):
    out=[]; i=0
    while i < len(blob):
        j = blob.find(b":", i)
        if j<0: break
        try: L = int(blob[i:j])
        except: break
        out.append(blob[j+1:j+1+L])
        i = j+1+L
    return out

def raw(method, path, body=None, cookie=""):
    c = http.client.HTTPSConnection(HOST, PORT, timeout=20)
    h = {"User-Agent":"CyberStrike/1.0","Accept":"*/*",
         "Origin":"https://epcr.tpf.gov.tw:4000","Referer":"https://epcr.tpf.gov.tw:4000/"}
    if cookie: h["Cookie"] = cookie
    if body is not None: h["Content-Type"]="text/plain;charset=UTF-8"
    c.request(method, path, body=body, headers=h)
    try:
        r = c.getresponse()
        return r.status, r.getheader("set-cookie",""), r.read()
    except (socket.timeout, TimeoutError) as e:
        return -1, "", b""
    finally:
        c.close()

# 1) handshake
s, sc, body = raw("GET", "/socket.io/?EIO=4&transport=polling")
print(f"HS: {s} {sc}")
pkts = parse_eio(body)
print("Pkts:", [p[:80] for p in pkts])
open_obj = json.loads(pkts[0][1:])  # strip '0' EIO type
sid = open_obj["sid"]
io_cookie = ""
for x in sc.split(", "):
    if x.startswith("io="):
        io_cookie = x.split(";")[0]
print(f"SID={sid} IO={io_cookie}")

# Track the latest io cookie (it rotates on POST)
def refresh_io(sc):
    global io_cookie
    for x in sc.split(", "):
        if x.startswith("io="):
            io_cookie = x.split(";")[0]
            return True
    return False

# 2) Long-poll: just GET, the server holds connection until it has data or 5s pingTimeout
print("\n=== Long-poll (after handshake) — server may push events ===")
s, sc, body = raw("GET", f"/socket.io/?EIO=4&transport=polling&sid={sid}", cookie=io_cookie)
print(f"status={s} body={body[:400]!r}")

# 3) Try namespaces
print("\n=== Namespace probe ===")
for ns in ["","/admin","/events","/socket","/live","/monitor",
           "/hosp","/case","/case-detail","/vital","/auth","/server","/merBridge"]:
    s, sc, body = raw("POST", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                      body=f'40{ns}', cookie=io_cookie)
    refresh_io(sc)
    pkts = parse_eio(body)
    show = pkts[:3] if pkts else body[:80]
    print(f"  ns={ns!r:<18} -> {show}")

# 4) Emit events
print("\n=== Emit events ===")
events = [
    ["hello", {}],
    ["ping", {}],
    ["join", "events"],
    ["join", {"room":"events"}],
    ["subscribe", "events"],
    ["getCase", {"caseId":"180817092350fed7"}],
    ["getEvents", {}],
    ["request", {"type":"events"}],
    ["auth", {"token":"anonymous"}],
    ["version", {}],
    ["config", {}],
    ["stream", {}],
    ["telemetry", {}],
]
for ev, pl in events:
    payload = f'42{json.dumps([ev, pl])}'
    s, sc, body = raw("POST", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                      body=payload, cookie=io_cookie)
    refresh_io(sc)
    pkts = parse_eio(body)
    print(f"  EV {ev!r:<18} -> {pkts[:2]}")
    time.sleep(0.1)

# 5) Final long-poll read
print("\n=== Final long-poll read ===")
s, sc, body = raw("GET", f"/socket.io/?EIO=4&transport=polling&sid={sid}", cookie=io_cookie)
print(f"status={s} body={body[:500]!r}")
