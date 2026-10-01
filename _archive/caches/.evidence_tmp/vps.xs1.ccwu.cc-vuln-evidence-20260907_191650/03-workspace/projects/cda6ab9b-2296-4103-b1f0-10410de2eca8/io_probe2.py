#!/usr/bin/env python3
"""Socket.IO v4 polling - explore namespace + emit events. epcr.tpf.gov.tw:4000"""
import http.client, json, sys, time

HOST = "epcr.tpf.gov.tw"
PORT = 4000
def req(method, path, body=None, cookie=""):
    c = http.client.HTTPSConnection(HOST, PORT, timeout=15)
    h = {"User-Agent":"CyberStrike/1.0","Accept":"*/*",
         "Origin":"https://epcr.tpf.gov.tw:4000","Referer":"https://epcr.tpf.gov.tw:4000/"}
    if cookie: h["Cookie"] = cookie
    if body is not None: h["Content-Type"]="text/plain;charset=UTF-8"
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    return r.status, r.getheader("set-cookie",""), r.read()

# 1) handshake
s, sc, body = req("GET","/socket.io/?EIO=4&transport=polling")
print("HS:", s, sc)
# parse EIO packet sequence: each prefix is "<len>:<type><payload>"
def parse_eio(blob):
    # EIO packet format: <len>:<type><payload>, where payload length = len - 1 (type char)
    out=[]; i=0
    while i < len(blob):
        j = blob.find(b":", i)
        if j<0: break
        try: L = int(blob[i:j])
        except: break
        # The packet content is exactly L bytes after the ':'
        pkt = blob[j+1:j+1+L]
        out.append(pkt)
        i = j+1+L
    return out

pkt = parse_eio(body)
print("Packets:", pkt)
# First packet should be EIO OPEN: type char '0' followed by JSON
if pkt and pkt[0][:1] == b'0':
    open_obj = json.loads(pkt[0][1:])
    sid = open_obj.get("sid")
else:
    sid = None
io_cookie = ""
for x in sc.split(", "):
    if x.startswith("io="):
        io_cookie = x.split(";")[0]
print("SID:", sid, "IO:", io_cookie)

# 2) Long-poll for server-pushed events first
print("\n=== Long-poll after handshake ===")
s,sc,body = req("GET", f"/socket.io/?EIO=4&transport=polling&sid={sid}", cookie=io_cookie)
print("status:",s,"body:",body[:500])

# 3) Try namespace connect explicitly
print("\n=== Namespace probe (explicit CONNECT) ===")
for ns in ["","/admin","/events","/socket","/live","/monitor",
           "/hosp","/case","/case-detail","/vital","/auth"]:
    s,sc,body = req("POST", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                    body=f'40{ns}', cookie=io_cookie)
    parsed = parse_eio(body)
    sig = parsed[0][:60] if parsed else b""
    if b'40' in sig or b'44' in sig or b'NOOP' in sig or b'"message"' in sig:
        print(f"  ns={ns!r:<15} -> {parsed[:3]}")
    else:
        print(f"  ns={ns!r:<15} -> {parsed}")
    time.sleep(0.2)

# 4) Emit events
print("\n=== Emit events on default ns ===")
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
    s,sc,body = req("POST", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                    body=payload, cookie=io_cookie)
    parsed = parse_eio(body)
    print(f"  EV {ev!r} -> {parsed[:2]}")
    time.sleep(0.2)

# 5) Read whatever server has queued
print("\n=== Final long-poll read ===")
s,sc,body = req("GET", f"/socket.io/?EIO=4&transport=polling&sid={sid}", cookie=io_cookie)
print("status:",s,"body:",body[:1000])
