#!/usr/bin/env python3
"""Phase 8b: :4001 socket.io polling mode event subscribe + long-poll listen
Strategy:
1. Poll handshake to get sid
2. Use the sid in subsequent POST poll requests (engine.io poll-write pattern: client sends 2-> as EngineIO message)
3. Try sending Socket.IO EVENT (42["event_name"]) over POST polling
4. Long-poll waiting for server-pushed events
"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Handshake
print("="*80)
print("Phase 8b-1: handshake")
print("="*80)
cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=30)
cn.request('GET', '/socket.io/?EIO=4&transport=polling', headers={'User-Agent': 'Mozilla/5.0'})
r = cn.getresponse()
body = r.read()
print(f"  status={r.status}")
print(f"  body[:300]: {body[:300]!r}")
sid = None
try:
    parts = body.split(b':', 1)
    if len(parts) == 2 and parts[1].startswith(b'0'):
        sid = json.loads(parts[1][1:]).get('sid')
        print(f"  parsed sid: {sid}")
except Exception as e:
    print(f"  parse error: {e}")
cn.close()

if not sid:
    print("No sid, abort")
    exit()

# 2. Send CONNECT (Socket.IO) over polling POST
# EngineIO message format: <type_char><data>, e.g. "40" (message + Socket.IO CONNECT)
# When using POST polling, body should be: "<engineio_type><socketio_data>"
# Send 40 (Socket.IO CONNECT) to subscribe
print()
print("="*80)
print("Phase 8b-2: Send Socket.IO CONNECT (40) via POST poll")
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
print("Phase 8b-3: Send Socket.IO EVENT (42[...]) via POST poll")
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
print("Phase 8b-4: Long-poll 30s waiting for server push")
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
