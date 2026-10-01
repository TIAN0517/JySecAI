#!/usr/bin/env python3
"""
探索 CaseID 字段查询失效的真实原因：
- 测试不同字段组合的过滤
- 验证 $ne + recordUuid regex
"""
import httpx, urllib3, json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

c = httpx.Client(base_url="https://epcr.tpf.gov.tw:4001", verify=False, timeout=30,
    headers={"User-Agent":"Mozilla/5.0"})

print("=== 1. 验证 CaseID 字段精确查询的边界条件 ===")
# 取出抽样中的真实 recordUuid / CaseID 样本
r = c.get("/events", params={"page":1, "pageSize":10})
print(f"  Default page=1 (no filter): {len(r.json())} items")
if r.status_code == 200 and r.json():
    for evt in r.json()[:3]:
        print(f"    Sample: id={evt.get('id')}, CaseID={evt.get('CaseID')}, recordUuid={evt.get('recordUuid')}")

print("\n=== 2. 用 recordUuid 精确查询 ===")
r = c.get("/events", params={"page":1, "pageSize":10})
if r.status_code == 200 and r.json():
    sample_uuid = r.json()[0].get("recordUuid")
    if sample_uuid:
        r2 = c.get("/events", params={"page":1, "pageSize":10, "recordUuid": sample_uuid})
        print(f"  recordUuid={sample_uuid[:40]}...: items={len(r2.json())}")

print("\n=== 3. 用 Status 字段精确查询 ===")
# 检查实际 Status 字段值
statuses = set()
for pg in [1, 2, 3]:
    r = c.get("/events", params={"page":pg, "pageSize":100})
    if r.status_code == 200:
        for evt in r.json():
            s = evt.get("Status")
            if s: statuses.add(s)
print(f"  Distinct Status values: {statuses}")

print("\n=== 4. recordUuid 字段前缀匹配 (regex) ===")
r = c.get("/events", params={"page":1, "pageSize":10})
if r.status_code == 200 and r.json():
    sample_uuid = r.json()[0].get("recordUuid")
    if sample_uuid:
        # 取前 8 个字符作为 regex 模式
        prefix = sample_uuid[:8]
        r2 = c.get("/events", params={"page":1, "pageSize":10, "recordUuid[$regex]": f"^{prefix}"})
        print(f"  recordUuid[$regex]=^{prefix}: items={len(r2.json())}")

print("\n=== 5. 直接 dump page=1 看实际 case 计数 ===")
# 看实际所有数据条数(对比抽样)
for pg in [1, 100, 1000]:
    r = c.get("/events", params={"page":pg, "pageSize":100, "Status[$ne]": ""})
    if r.status_code == 200:
        items = r.json()
        unique_cases = set(e.get("CaseID") for e in items if e.get("CaseID"))
        unique_uuids = set(e.get("recordUuid") for e in items if e.get("recordUuid"))
        print(f"  page={pg}: items={len(items)}, unique CaseIDs={len(unique_cases)}, unique UUIDs={len(unique_uuids)}")
