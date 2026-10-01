#!/usr/bin/env python3
"""Phase 6: :4001 /imageData + /videoData 批量数据导出（1000 + 100 条样本）"""
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

# 1. /imageData 批量取 1000 条（offset 0, 1000, 10000, 100000, 500000, 1000000）
print("="*80)
print("Phase 6-1: :4001 /imageData 多偏移抽样（数据集分布）")
print("="*80)
for offset in [0, 1000, 10000, 100000, 500000, 1000000, 1400000]:
    t0 = time.time()
    s, b, h = req('epcr.tpf.gov.tw', 4001, 'GET', f'/imageData?limit=10&offset={offset}', timeout=30)
    dt = time.time()-t0
    if s == 200:
        try:
            arr = json.loads(b)
            print(f"\n  offset={offset:8d}  limit=10  → status={s}  time={dt:.2f}s  bytes={len(b)}  records={len(arr)}")
            for rec in arr[:3]:
                print(f"    id={rec.get('id'):8d}  recordUuid={rec.get('recordUuid',''):32s}  fileName={rec.get('fileName',''):50s}  ImageTypeId={rec.get('ImageTypeId')}  ImageType.name={rec.get('ImageType',{}).get('name','') if rec.get('ImageType') else ''}")
            print(f"    ... ({len(arr)-3} more records)")
        except Exception as e:
            print(f"  offset={offset:8d}  → JSON parse error {e}")
    else:
        print(f"  offset={offset:8d}  → status={s}  body[:200]={b[:200]!r}")

# 2. /videoData 批量取 100 条（offset 0, 1000, 10000, 50000, 100000）
print()
print("="*80)
print("Phase 6-2: :4001 /videoData 多偏移抽样")
print("="*80)
for offset in [0, 1000, 10000, 50000, 100000]:
    t0 = time.time()
    s, b, h = req('epcr.tpf.gov.tw', 4001, 'GET', f'/videoData?limit=10&offset={offset}', timeout=30)
    dt = time.time()-t0
    if s == 200:
        try:
            arr = json.loads(b)
            print(f"\n  offset={offset:8d}  limit=10  → status={s}  time={dt:.2f}s  bytes={len(b)}  records={len(arr)}")
            for rec in arr[:3]:
                print(f"    id={rec.get('id'):8d}  recordUuid={rec.get('recordUuid',''):32s}  fileName={rec.get('fileName','')[:80]:80s}  VideoTypeId={rec.get('VideoTypeId')}  VideoType.name={rec.get('VideoType',{}).get('name','') if rec.get('VideoType') else ''}")
            print(f"    ... ({len(arr)-3} more records)")
        except Exception as e:
            print(f"  offset={offset:8d}  → JSON parse error {e}")
    else:
        print(f"  offset={offset:8d}  → status={s}  body[:200]={b[:200]!r}")

# 3. /imageData 字段统计：CaseID 分布（真实病患 vs 测试数据）
print()
print("="*80)
print("Phase 6-3: :4001 /imageData CaseID / recordUuid 字段分析")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/imageData?limit=100', timeout=30)
if s == 200:
    arr = json.loads(b)
    print(f"取 100 条样本，统计 CaseID + recordUuid + ImageTypeId 分布:")
    caseid_null_count = 0
    caseid_real_count = 0
    recorduuid_test_count = 0  # test 开头
    recorduuid_real_count = 0
    imagetype_count = {}
    for rec in arr:
        if rec.get('CaseID') is None:
            caseid_null_count += 1
        else:
            caseid_real_count += 1
        ru = rec.get('recordUuid', '')
        if ru.startswith('test'):
            recorduuid_test_count += 1
        else:
            recorduuid_real_count += 1
        itid = rec.get('ImageTypeId')
        imagetype_count[itid] = imagetype_count.get(itid, 0) + 1
    print(f"  CaseID 分布: null={caseid_null_count}  real={caseid_real_count}")
    print(f"  recordUuid 分布: test开头={recorduuid_test_count}  真实={recorduuid_real_count}")
    print(f"  ImageTypeId 分布: {dict(imagetype_count)}")
    # 取 5 个真实样本
    print(f"\n  前 5 条真实记录:")
    for rec in arr[:5]:
        print(f"    {rec}")
elif s != 200:
    print(f"  → status={s}  body={b[:200]!r}")

# 4. /videoData EMT app UUID 分布
print()
print("="*80)
print("Phase 6-4: :4001 /videoData EMT app UUID 分布")
print("="*80)
s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', '/videoData?limit=100', timeout=30)
if s == 200:
    arr = json.loads(b)
    print(f"取 100 条样本，统计 fileName 中的 EMT app UUID 分布:")
    uuid_count = {}
    has_emtapp_count = 0
    for rec in arr:
        fn = rec.get('fileName', '')
        if 'tw.com.viewlead.emtapp' in fn:
            has_emtapp_count += 1
            # 提取 UUID
            try:
                uuid = fn.split('emtapp')[1][:36]
                uuid_count[uuid] = uuid_count.get(uuid, 0) + 1
            except:
                pass
    print(f"  含 tw.com.viewlead.emtapp 的记录: {has_emtapp_count}/100")
    print(f"  唯一 EMT app UUID 数: {len(uuid_count)}")
    print(f"  UUID 分布: {dict(list(uuid_count.items())[:10])}")

# 5. :4001 /config 探测（之前未验证）
print()
print("="*80)
print("Phase 6-5: :4001 /config + /version + /api 探测")
print("="*80)
for path in ['/config', '/version', '/api', '/api/', '/api/config', '/api/v1', '/api/v2', '/api/imageData', '/api/videoData', '/socket.io/', '/socket.io/?EIO=4&transport=polling']:
    try:
        s, b, _ = req('epcr.tpf.gov.tw', 4001, 'GET', path, timeout=15)
        print(f"  GET {path:50s} → status={s}  body[:200]={b[:200]!r}")
    except Exception as e:
        print(f"  GET {path:50s} → ERROR {type(e).__name__}: {e!r}")

