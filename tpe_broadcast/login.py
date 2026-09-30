#!/usr/bin/env python3
"""
TPE 119 Auto-Login Service

自動登入台北119 service119 平台，取得 JWT token。
支援自動續期：token 過期前 (3小時) 自動重新登入。

使用方式:
  python3 login.py                    # 執行一次性登入 (取得 + 保存 token)
  python3 login.py --check            # 檢查 token 是否有效 (自動續期如果快過期)
  python3 login.py --daemon           # 背景守護模式: 每 2.5 小時自動重登
  python3 login.py --get            # 印出當前有效 token (stdout only)

Token 保存位置: tpe119_token.json
  - token: JWT 字符串
  - iat:   發行時間戳
  - exp:   過期時間戳 (通常 iat + 10800 = 3 小時)
  - renewed_at: 最後續期時間
"""
import os
import sys
import io
import json
import time
import base64
import signal
import threading
import urllib.parse

import requests
import ddddocr


# ── 設定 ─────────────────────────────────────────────────────────
BASE_URL = "https://service119.tfd.gov.tw/service119"
PROXY = "socks5://202.160.76.166:11086"
PROXIES = {"http": PROXY, "https": PROXY}
ACCOUNT = "R122937618"
PASSWORD = "680726"
CATEGORY = "01"                    # 01=臺北市消防同仁, 02=臺北市義消, 03=新聞媒體, 05=市府同仁

LOGIN_PAGE_URL = f"{BASE_URL}/accCase/login"
CAPTCHER_URL = f"{BASE_URL}/verifycode/get"
GEN_TOKEN_URL = f"{BASE_URL}/citizen/auth/genToken"

# Token 過期前多少秒開始續期 (2.5 小時 = 9000 秒，3小時=10800秒)
REFRESH_BEFORE_SECONDS = 9000
# Daemon 模式續期間隔
DAEMON_INTERVAL_SECONDS = 9000

# Token 檔案路徑
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tpe119_token.json")


class AutoLoginService119:
    """Auto-login for TPE 119 service119 with token persistence + auto-renewal."""

    def __init__(self, username=None, password=None, category=None,
                 token_file=None, session_cookie_url=None):
        self.username = username or ACCOUNT
        self.password = password or PASSWORD
        self.category = category or CATEGORY
        self.base_url = BASE_URL
        self.token_file = token_file or TOKEN_FILE
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # Session cookie 初始化 — 有些流程需要先拿到 JSESSIONID
        self.session_cookie_init_url = session_cookie_url or f"{BASE_URL}/accCaseLogin"

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"{self.base_url}/accCase/login",
            "Origin": "https://service119.tfd.gov.tw",
            "X-Requested-With": "XMLHttpRequest",
        })
        self.token = None

    # ── Captcha ────────────────────────────────────────────────────

    def get_captcha_code(self, max_ocr_attempts=8):
        """下載驗證碼圖片並 OCR 辨識。成功率 ~75% per attempt。"""
        for attempt in range(max_ocr_attempts):
            ts = int(time.time() * 1000)
            captcha_url = f"{CAPTCHER_URL}?t={ts}"
            resp = self.session.get(captcha_url)

            if resp.status_code != 200 or len(resp.content) <= 100:
                print(f"  [captcha] 第 {attempt + 1} 次: 狀態 {resp.status_code}, "
                      f"{len(resp.content)} bytes — 沒有有效圖片", flush=True)
                time.sleep(0.5)
                continue

            code = self.ocr.classification(resp.content)
            code = ''.join(filter(str.isalnum, code))[:4].upper()

            # 驗證碼應該是 4 個英數字
            if len(code) == 4:
                return code
            print(f"  [captcha] 第 {attempt + 1} 次: OCR 結果 '{code}' (長度 != 4) — 重試",
                  flush=True)
            time.sleep(0.3)

        return None

    # ── Login ─────────────────────────────────────────────────────

    def login(self, max_retries=5):
        """執行 OCR 驗證碼登入，取得 JWT token。

        回傳 True/False，成功時 self.token 會被設定。
        """
        # Clear any stale cookies from previous sessions
        self.session.cookies.clear()
        # 1. 取得 session cookie (JSESSIONID)
        try:
            self.session.get(LOGIN_PAGE_URL, timeout=10)
        except Exception:
            pass

        for attempt in range(1, max_retries + 1):
            print(f"[*] 第 {attempt} 次登入嘗試", flush=True)

            # 2. OCR 驗證碼
            captcha_code = self.get_captcha_code()
            if not captcha_code:
                print("[-] 無法取得驗證碼，重試中...", flush=True)
                time.sleep(2)
                continue
            print(f"  [captcha] OCR 識別: {captcha_code}", flush=True)

            # 3. POST genToken
            payload = {
                "pinText": self.username,
                "pazzW0rd": self.password,
                "useFor": self.category,
                "verifyCode": captcha_code,
            }
            resp = self.session.post(GEN_TOKEN_URL, data=payload, timeout=15)
            print(f"  [login] HTTP {resp.status_code}", flush=True)

            try:
                res_json = resp.json()
            except Exception:
                print(f"  [login] 非 JSON 回應: {resp.text[:200]}", flush=True)
                time.sleep(2)
                continue

            # 4. 判斷登入結果 — response 有 token 即為成功
            if res_json.get("success") or "citizen" in res_json or res_json.get("token"):
                token = res_json.get("token") or res_json.get("citizen", {}).get("token")
                if token:
                    self.token = token
                    print(f"[+] 登入成功！Token: {token[:30]}...", flush=True)
                    # 4a. Authenticate the session by calling fetchServerData
                    #     This marks the JSESSIONID as authenticated for citizenCase/search API
                    try:
                        self.session.post(
                            f"{self.base_url}/citizen/auth/fetchServerData",
                            data={"token": token}, timeout=15
                        )
                        print("  [auth] Session authenticated via fetchServerData", flush=True)
                    except Exception as e:
                        print(f"  [auth] fetchServerData failed (non-fatal): {e}", flush=True)
                    self._save_token(token)
                    return True

            err = res_json.get("message") or res_json.get("msg") or str(res_json)
            print(f"  [login] 失敗: {err} — 重試中...", flush=True)
            time.sleep(2)

        print("[!] 登入失敗，已達最大重試次數。", flush=True)
        return False

    # ── JWT 解析 ──────────────────────────────────────────────────

    @staticmethod
    def decode_jwt_payload(token):
        """解析 JWT payload (不驗證簽名，只讀取 claims)。

        回傳 dict 包含 iat, exp 等欄位，解析失敗回傳空 dict。
        """
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}
            # base64url decode + padding
            payload_b64 = parts[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            return json.loads(payload_bytes)
        except Exception:
            return {}

    def get_token_expiry(self, token=None):
        """取得 token 的過期時間戳。"""
        token = token or self.token
        if not token:
            return 0
        payload = self.decode_jwt_payload(token)
        return payload.get("exp", 0)

    def is_token_valid(self):
        """檢查當前 token 是否仍有效 (未過期)。"""
        if not self.token:
            return False
        exp = self.get_token_expiry()
        if not exp:
            return False
        remaining = exp - int(time.time())
        return remaining > 0

    # ── Token 持久化 ──────────────────────────────────────────────

    def _save_token(self, token):
        """將 token + metadata 保存到檔案。"""
        payload = self.decode_jwt_payload(token)
        data = {
            "token": token,
            "iat": payload.get("iat", int(time.time())),
            "exp": payload.get("exp", 0),
            "renewed_at": int(time.time()),
            "account": self.username,
            "category": self.category,
        }
        # Also save JSESSIONID cookie (needed for citizenCase/search API)
        try:
            jsession = self.session.cookies.get("JSESSIONID")
        except Exception:
            jsession = None
        if jsession:
            data["jsessionid"] = jsession
        try:
            with open(self.token_file, "w") as f:
                json.dump(data, f, indent=2)
            remaining = data["exp"] - data["iat"]
            print(f"[+] Token 已保存至 {self.token_file} "
                  f"(剩餘 {remaining // 3600} 小時)", flush=True)
        except Exception as e:
            print(f"[-] 保存 token 失敗: {e}", flush=True)

    def _load_token(self):
        """從檔案載入 token (如果存在且未過期)"""
        if not os.path.exists(self.token_file):
            return None
        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
            token = data.get("token")
            if token and self.is_token_valid_from(data):
                # Restore JSESSIONID into session
                jsession = data.get("jsessionid")
                if jsession:
                    self.session.cookies.set("JSESSIONID", jsession)
                print(f"[+] 載入有效 token (剩餘 "
                      f"{(data['exp'] - int(time.time())) // 60} 分鐘)", flush=True)
                self.token = token
                return token
            else:
                remaining = data.get("exp", 0) - int(time.time())
                print(f"[*] 已保存 token 過期了 (剩餘 {remaining}s) — 需要重登", flush=True)
        except Exception as e:
            print(f"[-] 載入 token 檔案失敗: {e}", flush=True)
        return None

    @staticmethod
    def is_token_valid_from(data):
        """檢查保存的 token 資料是否仍有效。"""
        exp = data.get("exp", 0)
        if not exp:
            return False
        remaining = exp - int(time.time())
        # 在過期前 60 秒內也視為快過期，需要續期
        return remaining > 60

    # ── 公開 API ──────────────────────────────────────────────────

    def get_token(self, force_relogin=False):
        """取得有效的 token。

        - 如果保存的 token 仍有效 (並沒�快過期): 直接回傳
        - 如果過期或 force_relogin: 重新登入
        """
        if not force_relogin:
            cached = self._load_token()
            if cached:
                return cached

        self.login()
        return self.token

    def needs_renewal(self):
        """檢查 token 是否需要續期 (剩餘時間 < REFRESH_BEFORE_SECONDS)。"""
        exp = self.get_token_expiry()
        if not exp:
            return True
        remaining = exp - int(time.time())
        return remaining < REFRESH_BEFORE_SECONDS

    def ensure_valid_token(self):
        """確保 token 有效，如果快過期則自動重新登入。"""
        if not self.token:
            self._load_token()

        if self.token and not self.needs_renewal():
            return True

        if self.needs_renewal():
            print(f"[*] Token 將過期 (剩餘 < {REFRESH_BEFORE_SECONDS}s) — 自動續期中...",
                  flush=True)

        return self.login()

    # ── Case fetching ────────────────────────────────────────────────

    def fetch_cases(self):
        """Call citizenCase/search API with current token + JSESSIONID.
        Returns list of case dicts or None on failure.
        """
        token = self.get_token()
        if not token:
            return None

        import urllib.parse
        url = "https://service119.tfd.gov.tw/service119/citizenCase/search"

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://service119.tfd.gov.tw",
            "referer": "https://service119.tfd.gov.tw/service119/ews1821",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/153.0.0.0 Safari/537.36",
        }

        import time as _time
        import random as _random
        data = f"token={urllib.parse.quote(token)}&t={_random.random()}"

        try:
            resp = self.session.post(url, headers=headers,
                             data=data, timeout=15)
            if resp.status_code != 200:
                # Try to detect session expiry and auto-relogin
                try:
                    err = resp.json()
                    if "Session" in err.get("message", "") or "登入" in err.get("message", ""):
                        print("[*] Session expired — auto-relogin and retry...", flush=True)
                        self.login()
                        token = self.token
                        data = f"token={urllib.parse.quote(token)}&t={_random.random()}"
                        resp = self.session.post(url, headers=headers,
                                         data=data, timeout=15)
                except Exception:
                    pass
                if resp.status_code != 200:
                    return None
            result = resp.json()
            if result.get("total", 0) == 0:
                return []
            return result.get("rows", [])
        except Exception as e:
            print(f"[-] fetch_cases 失敗: {e}", flush=True)
            return None

    # ── Daemon 模式 ───────────────────────────────────────────────

    def daemon_refresh(self, interval=None, stop_event=None):
        """背景執行續期，每隔 interval 秒重新登入。

        使用 signal 處理 Ctrl+C。
        """
        interval = interval or DAEMON_INTERVAL_SECONDS
        stop = stop_event or threading.Event()

        def _run():
            print(f"[*] Daemon 模式啟動 (續期間隔: {interval}s)", flush=True)
            # 先確保有一個 token
            if not self.get_token():
                print("[!] 初始登入失敗，daemon 將繼續嘗試...", flush=True)

            while not stop.is_set():
                # 計算下次續期時間
                exp = self.get_token_expiry()
                now = int(time.time())

                if exp:
                    remaining = exp - now
                    if remaining > interval:
                        # token 還有效，睡到快過期
                        sleep_time = remaining - REFRESH_BEFORE_SECONDS
                        if sleep_time > 0:
                            print(f"[*] Token 有效剩餘 {remaining // 60} 分鐘，"
                                  f"睡 {sleep_time // 60} 分鐘後檢查續期...", flush=True)
                            stop.wait(timeout=sleep_time)
                            continue

                # 需要重新登入
                print(f"[*] {time.strftime('%Y-%m-%d %H:%M:%S')} — 重新登入中...",
                      flush=True)
                if self.login():
                    print(f"[+] 續期成功 (exp: {self.get_token_expiry()})", flush=True)
                else:
                    print("[-] 續期失敗，將在下次 interval 重試...", flush=True)
                stop.wait(timeout=interval)

            print("[*] Daemon 已停止。", flush=True)

        # 註�冊 signal handler for Ctrl+C
        def _signal_handler(signum, frame):
            print("\n[*] 收到終止信號 (SIGINT)，正在停止 daemon...", flush=True)
            stop.set()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        # 啟動 daemon thread
        t = threading.Thread(target=_run, daemon=True, name="tpe119-refresh")
        t.start()
        return t, stop


# ── CLI ─────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="TPE 119 自動登入 (3小時 token 自動續期)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python3 login.py              # 一次性登入，保存 token
  python3 login.py --check      # 檢查 token，過期則自動重登
  python3 login.py --daemon     # 背景守護，2.5h 自動續期
  python3 login.py --get        # 印出有效 token (stdout)
"""
    )
    parser.add_argument("--check", action="store_true",
                        help="檢查 token 是否有效，過期則自動重登")
    parser.add_argument("--daemon", action="store_true",
                        help="背景守護模式 — 自動續期 token")
    parser.add_argument("--get", action="store_true",
                        help="印出當前有效 token (僅 stdout)")
    parser.add_argument("--force", action="store_true",
                        help="強制重新登入 (忽略快取)")
    parser.add_argument("--interval", type=int, default=DAEMON_INTERVAL_SECONDS,
                        help=f"Daemon 續期間隔秒數 (預設: {DAEMON_INTERVAL_SECONDS})")
    args = parser.parse_args()

    bot = AutoLoginService119()

    if args.get:
        # 只印 token 到 stdout
        token = bot.get_token(force_relogin=args.force)
        if token:
            print(token)
            return 0
        else:
            print("ERROR: 無法取得 token", file=sys.stderr)
            return 1

    if args.check:
        bot._load_token()
        if bot.is_token_valid():
            remaining = bot.get_token_expiry() - int(time.time())
            print(f"[+] Token 有效 (剩餘 {remaining // 60} 分 {remaining % 60} 秒)")
            if bot.needs_renewal():
                print("[*] 但快過期了，建議重新登入")
            return 0
        else:
            print("[-] Token 過期或不存在 — 重新登入中...")
            return 0 if bot.login() else 1

    if args.daemon:
        if bot.get_token(force_relogin=args.force):
            t, stop = bot.daemon_refresh(interval=args.interval)
            print("[*] 按 Ctrl+C 停止...", flush=True)
            t.join()
        else:
            print("[!] 初始登入失敗", flush=True)
            return 1
        return 0

    # 預設: 一次性登入
    success = bot.login()
    if success:
        print(f"[+] Token: {bot.token}")
        print(f"[+] 保存至: {bot.token_file}")
        print(f"[+] 過期時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bot.get_token_expiry()))}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
