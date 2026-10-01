#!/usr/bin/env python3
"""Socket.IO v4 — try CONNECT with auth payload + various business events."""
import websocket, json, time, sys

URL = "wss://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=websocket"

def attempt(events, listen=8.0, label=""):
    ws = websocket.WebSocket()
    ws.connect(URL,
               header=["Host: epcr.tpf.gov.tw:4000",
                       "Origin: https://epcr.tpf.gov.tw:4000",
                       "User-Agent: CyberStrike/1.0"],
               subprotocols=["socket.io"],
               timeout=10)
    ws.settimeout(2)
    print(f"=== {label} ===")
    # Drain initial
    end = time.time() + 1.5
    while time.time() < end:
        try: print(f"  < {ws.recv()!r}")
        except: break
    # Emit
    for e in events:
        print(f"  > {e!r}")
        ws.send(e)
        end = time.time() + 0.4
        while time.time() < end:
            try: print(f"  < {ws.recv()!r}")
            except: break
    # Long listen
    end = time.time() + listen
    while time.time() < end:
        try:
            d = ws.recv()
            if d: print(f"  < {d!r}")
        except: break
    ws.close()

# Connect with auth (EIO=4 supports auth in CONNECT packet)
attempt([
    '40{"token":"anonymous"}',
    '42["hello"]',
    '42["hello",{"auth":"test"}]',
], label="Test 1: Auth in CONNECT")

attempt([
    '40',
    '42["caseUpdate"]',
    '42["caseUpdate",{"caseId":"180817092350fed7"}]',
    '42["dispatch"]',
    '42["vitalSign"]',
    '42["patient"]',
    '42["hospital"]',
    '42["ems"]',
    '42["ohca"]',
    '42["case"]',
    '42["stat40"]',
    '42["monitor"]',
], label="Test 2: EMS business events")

attempt([
    '40',
    '42["message"]',
    '42["data"]',
    '42["update"]',
    '42["event"]',
    '42["notification"]',
    '42["alert"]',
    '42["status"]',
], label="Test 3: Generic event names")

attempt([
    '40',
    '42["test"]',
    '42["foo"]',
    '42["bar"]',
], label="Test 4: Garbage names")

attempt([
    '40',
    '42["connect"]',
    '42["ready"]',
    '42["init"]',
    '42["register"]',
    '42["login"]',
], label="Test 5: Connection-related")

# Long passive listen
print("\n=== Test 6: Long passive listen (30s) ===")
ws = websocket.WebSocket()
ws.connect(URL,
           header=["Host: epcr.tpf.gov.tw:4000",
                   "Origin: https://epcr.tpf.gov.tw:4000",
                   "User-Agent: CyberStrike/1.0"],
           subprotocols=["socket.io"],
           timeout=10)
ws.settimeout(2)
ws.send('40')
end = time.time() + 30
recv_count = 0
while time.time() < end:
    try:
        d = ws.recv()
        if d:
            recv_count += 1
            print(f"  < {d!r}  (count={recv_count})")
    except: pass
print(f"Total received in 30s: {recv_count}")
ws.close()
print("Done.")