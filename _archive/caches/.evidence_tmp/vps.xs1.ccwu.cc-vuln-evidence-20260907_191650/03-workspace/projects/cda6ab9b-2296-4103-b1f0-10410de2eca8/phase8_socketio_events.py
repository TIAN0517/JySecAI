#!/usr/bin/env python3
"""Phase 8: :4001 socket.io realtime event stream probing
1. websocket upgrade + subscribe business events
2. event name enumeration (vitalSign / case / dispatch / newCase / patient / ePCR / live)
3. long connection test (ping/pong + passive listener)
"""
import http.client, ssl, json, time, socket, struct, os, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ws_send(sock, payload):
    data = payload.encode('utf-8')
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    if len(data) < 126:
        header = bytes([0x81, 0x80 | len(data)])
    elif len(data) < 65536:
        header = bytes([0x81, 0xFE]) + struct.pack('!H', len(data))
    else:
        header = bytes([0x81, 0xFF]) + struct.pack('!Q', len(data))
    sock.sendall(header + mask + masked)

def ws_recv(sock, timeout=3):
    sock.settimeout(timeout)
    try:
        hdr = sock.recv(2)
        if len(hdr) < 2: return None
        fin = hdr[0] & 0x80
        opcode = hdr[0] & 0x0F
        masked = hdr[1] & 0x80
        length = hdr[1] & 0x7F
        if length == 126:
            length = struct.unpack('!H', sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack('!Q', sock.recv(8))[0]
        mask_key = sock.recv(4) if masked else None
        payload = b''
        while len(payload) < length:
            chunk = sock.recv(length - len(payload))
            if not chunk: break
            payload += chunk
        if mask_key:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        return opcode, payload.decode('utf-8', errors='replace')
    except socket.timeout:
        return None
    except Exception as e:
        return ('ERR', str(e))

# 1. Polling handshake to get sid
print("="*80)
print("Phase 8-1: /socket.io polling handshake")
print("="*80)
cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=30)
cn.request('GET', '/socket.io/?EIO=4&transport=polling', headers={'User-Agent': 'Mozilla/5.0'})
r = cn.getresponse()
body = r.read()
print(f"  status={r.status}")
print(f"  body[:300]: {body[:300]!r}")
sid = None
try:
    parts = body.split(':', 1)
    if len(parts) == 2 and parts[1].startswith('0'):
        sid = json.loads(parts[1][1:]).get('sid')
        print(f"  parsed sid: {sid}")
except Exception as e:
    print(f"  parse error: {e}")
cn.close()

# 2. POST poll (trigger server push)
print()
print("="*80)
print("Phase 8-2: POST poll (3 round polling)")
print("="*80)
if sid:
    for i in range(3):
        try:
            cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=15)
            cn.request('POST', f'/socket.io/?EIO=4&transport=polling&sid={sid}', body='', headers={'Content-Type': 'text/plain;charset=UTF-8'})
            r = cn.getresponse()
            b = r.read()
            print(f"  poll #{i+1}: status={r.status} size={len(b)} body[:200]={b[:200]!r}")
            cn.close()
            time.sleep(1)
        except Exception as e:
            print(f"  poll #{i+1}: error {e}")

# 3. WebSocket upgrade
print()
print("="*80)
print("Phase 8-3: WebSocket upgrade test")
print("="*80)
sock = None
try:
    sock = socket.create_connection(('epcr.tpf.gov.tw', 4001), timeout=10)
    sock.settimeout(10)
    ws_key = 'dGhlIHNhbXBsZSBub25jZQ=='
    req = (
        f"GET /socket.io/?EIO=4&transport=websocket&sid={sid} HTTP/1.1\r\n"
        f"Host: epcr.tpf.gov.tw:4001\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    sock.sendall(req.encode('utf-8'))
    resp = b''
    while b'\r\n\r\n' not in resp:
        chunk = sock.recv(4096)
        if not chunk: break
        resp += chunk
    print(f"  WS upgrade response[:300]: {resp[:300]!r}")
    if b'101' in resp[:50]:
        print("  [+] WebSocket upgrade SUCCESS!")
        # EngineIO probe
        ws_send(sock, '2probe')
        time.sleep(0.5)
        r = ws_recv(sock)
        print(f"  probe response: {r}")
        if r and r[1] == '3probe':
            # EngineIO upgrade confirmation
            ws_send(sock, '5')
            time.sleep(0.5)
            # EngineIO open - send '0' to request open
            ws_send(sock, '')
            time.sleep(0.5)
            r = ws_recv(sock)
            print(f"  EngineIO upgrade: {r}")
        # Socket.IO CONNECT (40)
        ws_send(sock, '40')
        time.sleep(0.5)
        r = ws_recv(sock)
        print(f"  Socket.IO CONNECT: {r}")
        
        # Subscribe events
        events = [
            'subscribe', 'join', 'subscribeVitalSign', 'subscribeCase',
            'subscribeDispatch', 'subscribePatient', 'subscribeEpcr', 'subscribeLive',
            'newCase', 'updateCase', 'deleteCase', 'ping', 'pong',
            'client.subscribe', 'client.unsubscribe', 'message', 'event',
            'hello', 'ready', 'auth', 'login'
        ]
        for ev in events:
            payload = f'42["{ev}",{{}}]'
            ws_send(sock, payload)
            time.sleep(0.3)
            r = ws_recv(sock)
            print(f"  emit {ev:25s} -> recv: {r}")
        # passive listening
        print()
        print("Phase 8-4: Passive listening 5s")
        sock.settimeout(1)
        start = time.time()
        while time.time() - start < 5:
            try:
                r = ws_recv(sock, timeout=1)
                if r:
                    print(f"  recv: {r}")
            except:
                pass
    else:
        print("  [-] WebSocket upgrade FAILED")
except Exception as e:
    print(f"  WS error: {type(e).__name__}: {e}")
finally:
    if sock: sock.close()
