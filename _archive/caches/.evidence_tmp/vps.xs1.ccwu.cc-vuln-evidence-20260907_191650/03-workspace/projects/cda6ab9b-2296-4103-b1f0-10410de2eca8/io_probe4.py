#!/usr/bin/env python3
"""Proper Socket.IO v4 polling: keep long-poll GET alive, POST events from another connection.
Use same sid and io cookie. Each request to the same sid must be on different HTTP connections
since socket.io serializes requests per session. But socket.io v4 polling allows MULTIPLE
concurrent GET requests on the same session for long-polling pattern.

Actually socket.io v4 polling is single-flight: ONE long-poll at a time per session.
But POST (write) and GET (read) are interleaved on DIFFERENT connections.
"""
import http.client, json, sys, time, threading, queue

HOST = "epcr.tpf.gov.tw"; PORT = 4000

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

def raw(method, path, body=None, cookie="", timeout=20):
    c = http.client.HTTPSConnection(HOST, PORT, timeout=timeout)
    h = {"User-Agent":"CyberStrike/1.0","Accept":"*/*",
         "Origin":"https://epcr.tpf.gov.tw:4000","Referer":"https://epcr.tpf.gov.tw:4000/"}
    if cookie: h["Cookie"] = cookie
    if body is not None: h["Content-Type"]="text/plain;charset=UTF-8"
    c.request(method, path, body=body, headers=h)
    try:
        r = c.getresponse()
        return r.status, r.getheader("set-cookie",""), r.read()
    except Exception as e:
        return -1, "", b""
    finally:
        c.close()

# 1) handshake
s, sc, body = raw("GET", "/socket.io/?EIO=4&transport=polling")
pkts = parse_eio(body)
open_obj = json.loads(pkts[0][1:])
sid = open_obj["sid"]
io_cookie = [x.split(";")[0] for x in sc.split(", ") if x.startswith("io=")][0]
print(f"SID={sid} IO={io_cookie}")

results = queue.Queue()

def reader(stop_evt):
    """Long-poll reader."""
    while not stop_evt.is_set():
        s, sc, body = raw("GET", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                          cookie=io_cookie, timeout=8)
        pkts = parse_eio(body)
        ts = time.strftime("%H:%M:%S")
        if s == 200 and pkts and pkts[0] != b'':
            print(f"[{ts}] READER got: {pkts[:5]}")
            results.put(pkts)
        elif s == -1:
            print(f"[{ts}] READER timeout/closed")
        else:
            print(f"[{ts}] READER err: status={s} body={body[:80]!r}")

# Start reader thread
stop = threading.Event()
t = threading.Thread(target=reader, args=(stop,))
t.start()
time.sleep(0.5)

# 2) Emit events
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
    # Try namespace connect via payload
    ["stream", {"sid": sid}],
]
for ev, pl in events:
    payload = f'42{json.dumps([ev, pl])}'
    s, sc, body = raw("POST", f"/socket.io/?EIO=4&transport=polling&sid={sid}",
                      body=payload, cookie=io_cookie, timeout=5)
    # refresh io
    for x in sc.split(", "):
        if x.startswith("io="):
            io_cookie = x.split(";")[0]
    print(f"  EV {ev!r:<20} status={s} resp={body[:80]!r}")
    time.sleep(0.5)

time.sleep(3)
stop.set()
t.join(timeout=10)
print("\nDone. Queue had", results.qsize(), "events.")
