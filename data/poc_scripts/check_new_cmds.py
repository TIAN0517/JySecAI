#!/usr/bin/env python3
"""Check new admin/cmd endpoints discovered in scan."""
import requests, urllib3, json
urllib3.disable_warnings()
import pprint

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

resp = requests.post(url, data={"cmd": "1000", "wechatId": "testwechat001", **base}, timeout=10, verify=False)
d = resp.json()
sid = d["msg"]["sid"]
print(f"sid={sid[:16]}..., username={d['msg']['username']}")

# Check the new interesting endpoints
for cmd in [1001, 516, 519, 537, 542, 544, 713, 716, 810, 814, 815, 912, 913, 925, 533, 536, 529, 530, 531, 532, 534, 535, 541, 543, 545]:
    params = {"cmd": str(cmd), "sid": sid, "username": "cffcna6qzp", **base}
    try:
        r = requests.post(url, data=params, timeout=5, verify=False)
        j = r.json()
        msg = j.get("msg", j.get("data", ""))
        if isinstance(msg, dict):
            print(f"  cmd={cmd}: dict keys={list(msg.keys())}")
            if cmd in [516, 519, 537]:
                print(f"    data: {json.dumps(msg, ensure_ascii=False)[:300]}")
        elif isinstance(msg, list):
            print(f"  cmd={cmd}: list[{len(msg)}]")
            if msg and cmd == 537:
                print(f"    first: {json.dumps(msg[0], ensure_ascii=False)[:300]}")
            elif msg and len(msg) > 0:
                print(f"    first: {json.dumps(msg[0], ensure_ascii=False)[:200]}")
        elif isinstance(msg, str):
            print(f"  cmd={cmd}: str='{msg[:80]}'")
        else:
            print(f"  cmd={cmd}: {str(msg)[:80]}")
    except Exception as e:
        print(f"  cmd={cmd}: ERROR {e}")