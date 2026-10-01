#!/usr/bin/env python3
"""Phase 8c: :4001 socket.io polling mode event subscribe + long-poll listen (fixed parse)
Strategy:
1. Polling handshake, fix parse error by stripping to first }
2. Send CONNECT (40) via POST poll
3. Send business events (42[ev, data]) via POST poll
4. Long-poll waiting for server push
"""
import http.client, ssl, json, time, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Handshake
print("="*80)
print("Phase 8c-1: handshake (fixed parse)")
print("="*80)
cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=30)
cn.request('GET', '/socket.io/?EIO=4&transport=polling', headers={'User-Agent': 'Mozilla/5.0'})
r = cn.getresponse()
body = r.read()
print(f"  status={r.status}")
print(f"  body[:300]: {body[:300]!r}")
sid = None
# EIO=4 format: <length>:<engineio_message>
# EngineIO message starts with type char (0-6). Type 0 = open, format = "0{json}"
# In body, multiple EngineIO messages concatenated: e.g. "97:0{...}2:40"
# The "97:" prefix is the length of the FIRST message (97 bytes)
# So first message = body[3:100] (length=97 means chars from index 3 to 3+97)
# OR easier: find the { and } boundaries
match = re.search(rb'\{[^}]*\}', body)
if match:
    try:
        data = json.loads(match.group(0))
        sid = data.get('sid')
        print(f"  parsed sid: {sid}")
        print(f"  parsed data: {data}")
    except Exception as e:
        print(f"  load error: {e}")
else:
    # fallback: find 0{...}
    match2 = re.search(rb'0(\{.*?\})', body)
    if match2:
        try:
            data = json.loads(match2.group(1))
            sid = data.get('sid')
            print(f"  parsed sid (fallback): {sid}")
        except Exception as e:
            print(f"  fallback load error: {e}")
cn.close()

if not sid:
    print("No sid, abort")
    exit()

# 2. Send CONNECT (Socket.IO) over polling POST
print()
print("="*80)
print("Phase 8c-2: Send Socket.IO CONNECT (40) via POST poll")
print("="*80)
for body_str in ['40', '40{}']:
    cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=15)
    cn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body=body_str,
               headers={'Content-Type': 'text/plain;charset=UTF-8'})
    r = cn.getresponse()
    b = r.read()
    print(f"  body={body_str!r}: status={r.status} resp[:200]={b[:200]!r}")
    cn.close()
    time.sleep(0.5)

# 3. Try sending various business events
print()
print("="*80)
print("Phase 8c-3: Send Socket.IO EVENT (42[ev, data]) via POST poll")
print("="*80)
events = [
    ('subscribe', {}),
    ('subscribeVitalSign', {}),
    ('subscribeCase', {}),
    ('subscribeDispatch', {}),
    ('subscribePatient', {}),
    ('subscribeEpcr', {}),
    ('subscribeLive', {}),
    ('newCase', {}),
    ('client.subscribe', {'roomName': 'admin'}),
    ('client.subscribe', {'roomName': 'vitalSign'}),
    ('client.subscribe', {'roomName': 'case'}),
    ('ping', {}),
    ('hello', {}),
    ('ready', {}),
    ('message', {'data': 'test'}),
]

for ev, data in events:
    payload = '42' + json.dumps([ev, data])
    cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=15)
    cn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body=payload,
               headers={'Content-Type': 'text/plain;charset=UTF-8'})
    r = cn.getresponse()
    b = r.read()
    print(f"  {ev:25s} status={r.status} resp[:150]={b[:150]!r}")
    cn.close()
    time.sleep(0.5)

# 4. Long-poll - 30s waiting for server push
print()
print("="*80)
print("Phase 8c-4: Long-poll 30s waiting for server push")
print("="*80)
start = time.time()
total_received = 0
while time.time() - start < 30:
    try:
        cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=30)
        cn.request('GET', f'/socket.io/?EIO=4&transport=polling&sid={sid}', headers={'User-Agent': 'Mozilla/5.0'})
        r = cn.getresponse()
        b = r.read()
        if b:
            total_received += len(b)
            print(f"  [{time.time()-start:.1f}s] received {len(b)}B: {b[:300]!r}")
        cn.close()
    except Exception as e:
        print(f"  [{time.time()-start:.1f}s] error: {e}")
    time.sleep(1)

print()
print(f"Total received during long-poll: {total_received} bytes")