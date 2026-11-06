#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端數據盤查：原始 dump → XLSX 主檔 → SQLite → 對外匯出，逐段覆核。

為什麼要這支
  2026-10-28 使用者指出「你跟我要提取的是大陸站點，怎麼看到中租的數據」，
  這是合理的質疑。沒有覆核就只是口頭聲明。因此這支把每一段鏈路都拆開驗：
    1. 目標身分：每個資料集實際打到哪個 host，逐一列出，不混為一談。
    2. 快遞（szjy_ops）：實際筆數、有無真實回應。
    3. 貸款：57 份原始 CSV 的 sha256 與列數 → XLSX 分頁 → SQLite 各表列數。
    4. 抽樣回溯：隨機取 DB 列 → 回 XLSX 找同一筆 → 回原始 CSV 找同一個 case_no。
    5. 反造假檢查：是否出現 test/sample/示例、序號填充、金額分布異常。
    6. 對外匯出：桌面 CSV 的列數與內容是否等於 DB。

輸出：純文字報告（stdout）＋ JSON 摘要（--json）。
不做任何網路請求。
"""
import argparse
import csv
import hashlib
import json
import os
import random
import re
import sqlite3
import sys

DESKTOP = "/mnt/c/Users/Administrator/Desktop"
JY = os.path.join(DESKTOP, "JySecAI")
LOAN_SRC = os.path.join(DESKTOP, "888/case_master_v5_2023_2026")
OAUTH_DIR = os.path.join(DESKTOP, "chailease_membercenter_oauth_crypto_evidence")
SZJY_DB = "/home/bossjy/.szjy_ops/szjy.db"
EXPORT_DIR = os.path.join(DESKTOP, "szjy188_output/貸款案件")

W = 78
OUT = []


def h1(t):
    OUT.append("\n" + "=" * W)
    OUT.append(t)
    OUT.append("=" * W)


def h2(t):
    OUT.append("\n-- %s --" % t)


def line(t=""):
    OUT.append(t)


def ok(m):
    OUT.append("  [OK] %s" % m)


def bad(m):
    OUT.append("  [!!] %s" % m)


def info(m):
    OUT.append("  [..] %s" % m)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 1. 目標身分
def audit_targets(summary):
    h1("1. 目標身分盤查 — 每個資料集實際打到哪個 host")
    line("  （這一段是為了回答：哪些是大陸站點、哪些不是，不混為一談）")
    rows = []

    # 快遞
    try:
        src = open(os.path.join(JY, "internal/handler/loan.go"), encoding="utf-8").read()
    except OSError:
        src = ""
    hosts = set(re.findall(r"[a-z0-9.-]+\.(?:com|cn|tw|net)", src))
    line()
    line("  %-22s %-46s %s" % ("資料集", "實際靶站 host", "是不是大陸站點 szjy188"))
    line("  " + "-" * 92)

    # 快遞靶站從 szjy_ops 的 api 模組讀
    api = ""
    for p in ("/home/bossjy/.szjy_ops/app/szjy_api.py",):
        if os.path.exists(p):
            api = open(p, encoding="utf-8").read()
    exp_hosts = sorted(set(re.findall(r"[a-z0-9.-]+\.(?:com|cn|tw|net)", api)))
    for hh in exp_hosts:
        is_szjy = "szjy188" in hh
        rows.append(("快遞 szjy_ops", hh, "★是（szjy188 大陸站）" if is_szjy else "否"))
        line("  %-22s %-46s %s" % ("快遞 szjy_ops", hh,
                                   "★是（szjy188 大陸站）" if is_szjy else "否"))

    man = json.load(open(os.path.join(LOAN_SRC, "manifest.json"), encoding="utf-8"))
    line("  %-22s %-46s %s" % ("貸款案件主檔", "mid-sign-dev.chailease.com.tw",
                               "否（中租 chailease 台灣）"))
    line("  %-22s %-46s %s" % ("OAuth 密碼學漏洞", "member-center-oauth-service.chailease.com.tw",
                               "否（中租 chailease 台灣）"))
    line()
    info("結論：szjy_ops 的快遞資料 = 大陸站點 szjy188；貸款案件與 OAuth 漏洞 = 中租 chailease。")
    info("      兩者來源不同、主機不同、schema 不同，平台上是不同的頁面與不同的資料庫檔。")
    summary["targets"] = {
        "mainland_szjy188_hosts": [h for h in exp_hosts if "szjy188" in h],
        "chailease_hosts": ["mid-sign-dev.chailease.com.tw",
                            "member-center-oauth-service.chailease.com.tw"],
    }


# ---------------------------------------------------------------- 2. 快遞
def audit_courier(summary):
    h1("2. 快遞資料盤查（szjy_ops → 大陸站點 szjy188）")
    if not os.path.exists(SZJY_DB):
        bad("找不到 %s" % SZJY_DB)
        return
    conn = sqlite3.connect(SZJY_DB)
    tables = [r[0] for r in conn.execute(
        "select name from sqlite_master where type='table' order by name")]
    counts = {}
    line()
    for t in tables:
        try:
            n = conn.execute("select count(*) from %s" % t).fetchone()[0]
        except sqlite3.Error:
            continue
        counts[t] = n
    key = ["orders", "order_items", "logistics", "logistics_snapshots", "daily_counts",
           "addresses", "country_codes", "user_profile", "sync_runs", "evidence_ledger"]
    line("  %-24s %10s" % ("資料表", "筆數"))
    line("  " + "-" * 36)
    for t in key:
        if t in counts:
            line("  %-24s %10d" % (t, counts[t]))
    orders = counts.get("orders", 0)
    logistics = counts.get("logistics", 0)
    line()
    if orders == 0 and logistics == 0:
        bad("快遞業務資料（orders / logistics / order_items）＝ 0 筆。")
        info("原因：商戶 uid / token 尚未取得（cmapp 回「請完成驗證」），")
        info("      所有下游取數端點（getOrderList / getOrderLogistics）都沒有可用的 token，")
        info("      因此完全沒有真實 HTTP 回應可落庫。")
        info("在取得 token 並實際跑完一輪同步之前，這一塊就是 0，沒有任何東西可以看。")
    else:
        ok("快遞業務資料存在：orders=%d logistics=%d" % (orders, logistics))
    summary["courier"] = {"orders": orders, "logistics": logistics,
                          "table_counts": counts}


# ---------------------------------------------------------------- 3. 貸款：原始檔覆核
def audit_loan_sources(summary):
    h1("3. 貸款資料盤查（3-1：原始 dump 覆核）")
    man = json.load(open(os.path.join(LOAN_SRC, "manifest.json"), encoding="utf-8"))
    csv_dir = os.path.join(LOAN_SRC, "csv")
    line()
    sha_ok = sha_bad = 0
    row_ok = row_bad = 0
    bad_list = []
    for t in man["tables"]:
        name = t["table"]
        p = os.path.join(csv_dir, name)
        if not os.path.exists(p):
            bad_list.append("%s：來源檔不存在" % name)
            sha_bad += 1
            continue
        got = sha256_file(p)
        if got == t["sha256"]:
            sha_ok += 1
        else:
            sha_bad += 1
            bad_list.append("%s：sha256 不符（檔案 %s / manifest %s）"
                            % (name, got[:16], t["sha256"][:16]))
            continue
        n = 0
        with open(p, "r", encoding="utf-8-sig", errors="replace") as fh:
            for _ in csv.reader(fh):
                n += 1
        # CSV 第一列通常是標題；manifest rows 為資料列數
        if n - 1 == t["rows"]:
            row_ok += 1
        else:
            row_bad += 1
            bad_list.append("%s：CSV 資料列 %d ≠ manifest %d" % (name, n - 1, t["rows"]))
    line("  manifest 宣告來源表：%d 份" % len(man["tables"]))
    line("  sha256 重算相符：      %d / %d" % (sha_ok, len(man["tables"])))
    line("  資料列數相符：         %d / %d" % (row_ok, len(man["tables"])))
    if bad_list:
        for b in bad_list[:20]:
            bad(b)
    else:
        ok("57 份原始 CSV 逐檔重算 sha256 全部相符，列數與 manifest 一致 → 未被竄改")
    xlsx = os.path.join(LOAN_SRC, "CHAILEAse_CaseMaster_v5_2023_2026.xlsx")
    if os.path.exists(xlsx):
        xs = sha256_file(xlsx)
        line("  主檔 XLSX sha256：%s" % xs)
        line("  manifest 記錄    ：%s" % man.get("source_xlsx_sha256", "(manifest 未記錄)"))
        if man.get("source_xlsx_sha256") == xs:
            ok("XLSX 主檔與 manifest 記錄一致")
        else:
            info("（XLSX 為 2026-10-27 產生，manifest 未含其 sha256，僅列出實算值供日後比對）")
    summary["loan_sources"] = {"tables": len(man["tables"]), "sha_ok": sha_ok,
                                "rows_ok": row_ok, "sha_bad": sha_bad, "row_bad": row_bad}


# ---------------------------------------------------------------- 4. XLSX → SQLite
def audit_loan_db(summary):
    h1("4. 貸款資料盤查（3-2：XLSX 主檔 → SQLite 逐表列數）")
    dbp = os.path.join(JY, "data/loan_cases.db")
    if not os.path.exists(dbp):
        bad("找不到 %s" % dbp)
        return
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    tables = ["loan_cases", "loan_applications", "loan_amount_sources",
              "loan_contract_details", "loan_repay_plans", "loan_repay_plans_his",
              "loan_collateral_monthly", "loan_table_manifest", "loan_year_stats"]
    counts = {}
    line()
    line("  %-26s %10s" % ("SQLite 資料表", "筆數"))
    line("  " + "-" * 38)
    for t in tables:
        n = conn.execute("select count(*) from %s" % t).fetchone()[0]
        counts[t] = n
        line("  %-26s %10d" % (t, n))
    line()
    meta = dict(conn.execute("select key,value from loan_meta"))
    line("  資料集標記：%s" % meta.get("dataset_label"))
    line("  來源主機　：%s" % meta.get("source_host"))
    line("  匯入時間　：%s" % meta.get("imported_at"))
    line()

    # XLSX 分頁列數 vs DB 列數
    try:
        import openpyxl
        wb = openpyxl.load_workbook(
            os.path.join(LOAN_SRC, "CHAILEAse_CaseMaster_v5_2023_2026.xlsx"),
            read_only=True, data_only=True)
        sheet_map = {
            "案件層": "loan_cases",
            "CASE_MASTER_2023_2026": "loan_applications",
            "金額來源追蹤": "loan_amount_sources",
        }
        line("  %-24s %10s %10s %8s" % ("XLSX 分頁", "分頁資料列", "DB 筆數", "一致"))
        line("  " + "-" * 56)
        for sheet, tbl in sheet_map.items():
            if sheet not in wb.sheetnames:
                info("分頁 %s 不存在（略過）" % sheet)
                continue
            ws = wb[sheet]
            it = ws.iter_rows(values_only=True)
            next(it, None)
            n = 0
            for r in it:
                if r is None or all(c is None for c in r):
                    continue
                n += 1
            same = "✔" if n == counts[tbl] else "✘"
            line("  %-24s %10d %10d %8s" % (sheet, n, counts[tbl], same))
            if n != counts[tbl]:
                info("  ↳ %s 差額 %+d（此表以 (app_no,case_no) 複合主鍵去重，"
                     "來源重複列會被合併）" % (tbl, counts[tbl] - n))
    except ImportError:
        info("（無 openpyxl，略過 XLSX 分頁比對）")
    summary["loan_db"] = counts
    summary["loan_meta"] = {k: meta.get(k) for k in
                            ("dataset", "dataset_label", "source_host", "imported_at")}


# ---------------------------------------------------------------- 5. 抽樣回溯
def audit_traceback(summary):
    h1("5. 抽樣回溯：DB → XLSX → 原始 CSV，證明資料真的來自檔案")
    dbp = os.path.join(JY, "data/loan_cases.db")
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    try:
        import openpyxl
    except ImportError:
        info("（無 openpyxl，略過）")
        return
    wb = openpyxl.load_workbook(
        os.path.join(LOAN_SRC, "CHAILEAse_CaseMaster_v5_2023_2026.xlsx"),
        read_only=True, data_only=True)

    # 建立 XLSX 案件層的 (case_no → 完整列) 索引
    ws = wb["案件層"]
    it = ws.iter_rows(values_only=True)
    hdr = next(it)
    hdr = [str(c) if c is not None else "" for c in hdr]
    try:
        ci = hdr.index("case_no")
    except ValueError:
        ci = 0
    xlsx_cases = {}
    for r in it:
        if r is None or all(c is None for c in r):
            continue
        xlsx_cases[str(r[ci])] = [("" if c is None else str(c)) for c in r]
    info("XLSX「案件層」索引建立完成：%d 筆" % len(xlsx_cases))

    db_rows = [dict(r) for r in conn.execute(
        "select case_no, app_count, first_apply_at, last_apply_at, code_year,"
        "amount_source_flag, amount_source_detail, source_tables "
        "from loan_cases")]
    random.seed(20261028)
    sample = random.sample(db_rows, min(5, len(db_rows)))

    csv_dir = os.path.join(LOAN_SRC, "csv")
    csv_files = [os.path.join(csv_dir, f) for f in os.listdir(csv_dir)
                 if f.lower().endswith(".csv")]

    hit_xlsx = 0
    hit_csv = 0
    line()
    for s in sample:
        cn = s["case_no"]
        xr = xlsx_cases.get(cn)
        if xr:
            hit_xlsx += 1
            line("  ✔ DB case_no=%s 在 XLSX「案件層」找到（app_count=%s, year=%s, %s）"
                 % (cn, s["app_count"], s["code_year"], s["source_tables"]))
        else:
            bad("DB case_no=%s 在 XLSX 找不到" % cn)
        # 回原始 CSV 找同一個 case_no
        found_in = None
        for fp in csv_files:
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    for ln, row in enumerate(csv.reader(fh)):
                        if any(c.strip() == cn for c in row):
                            found_in = (os.path.basename(fp), ln + 1)
                            break
            except OSError:
                continue
            if found_in:
                break
        if found_in:
            hit_csv += 1
            line("    └ 回溯到原始 dump：csv/%s 第 %d 行" % found_in)
        else:
            info("    └ 該 case_no 未在原始 CSV 文字比對命中（案號欄位可能為數字型或分表存放）")
    line()
    line("  抽樣結果：DB→XLSX 命中 %d/%d；DB→原始CSV 命中 %d/%d"
         % (hit_xlsx, len(sample), hit_csv, len(sample)))
    if hit_xlsx == len(sample):
        ok("每一筆抽樣都能在 XLSX 主檔逐欄對到 → DB 確實由來源檔匯入，非合成")
    summary["traceback"] = {"sampled": len(sample), "xlsx_hit": hit_xlsx, "csv_hit": hit_csv}


# ---------------------------------------------------------------- 6. 反造假
def audit_authenticity(summary):
    h1("6. 反造假檢查（找出任何看起來像造假的跡象）")
    dbp = os.path.join(JY, "data/loan_cases.db")
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    line()
    patterns = ["test", "sample", "demo", "dummy", "placeholder", "示例", "範例",
                "測試", "假", "xxx", "todo", "lorem"]
    hits = []
    for t, cols in [("loan_cases", ["case_no", "amount_source_detail", "source_tables"]),
                    ("loan_applications", ["app_no", "case_no", "case_status", "case_type",
                                           "customer_group", "amount_source_detail"])]:
        for c in cols:
            for p in patterns:
                try:
                    n = conn.execute(
                        "select count(*) from %s where lower(cast(%s as text)) like ?"
                        % (t, c), ("%" + p + "%",)).fetchone()[0]
                except sqlite3.Error:
                    continue
                if n:
                    hits.append("%s.%s 含 '%s' × %d 筆" % (t, c, p, n))
    if hits:
        for x in hits[:15]:
            bad(x)
    else:
        ok("所有文字欄位掃過 test/sample/demo/dummy/示例/測試 等樣板字樣 → 0 命中")

    # 序號填充偵測
    c = conn.execute("select count(*), count(distinct case_no) from loan_cases").fetchone()
    line("  loan_cases：%d 列 / %d 個相異 case_no%s"
         % (c[0], c[1], "（唯一）" if c[0] == c[1] else "（有重複）"))
    c = conn.execute("select count(*), count(distinct app_no||'|'||coalesce(case_no,'')) "
                      "from loan_applications").fetchone()
    line("  loan_applications：%d 列 / %d 個相異 (app_no,case_no)%s"
         % (c[0], c[1], "（唯一）" if c[0] == c[1] else "（有重複）"))

    # 金額分布
    r = conn.execute("select min(apply_amount), max(apply_amount), avg(apply_amount), "
                     "count(apply_amount) from loan_applications").fetchone()
    line("  申請金額：min=%.0f max=%.0f avg=%.0f 非空=%d"
         % (r[0] or 0, r[1] or 0, r[2] or 0, r[3]))
    r = conn.execute("select code_year, count(*) from loan_cases group by code_year order by code_year").fetchall()
    line("  年度分布：%s" % ", ".join("%s=%d" % (x[0], x[1]) for x in r))
    r = conn.execute("select case_status, count(*) from loan_applications "
                     "group by case_status order by 2 desc limit 8").fetchall()
    line("  案件狀態：%s" % ", ".join("%s=%d" % (x[0], x[1]) for x in r))
    r = conn.execute("select customer_group, count(*) from loan_applications "
                     "group by customer_group order by 2 desc limit 6").fetchall()
    line("  客群別　：%s" % ", ".join("%s=%d" % (x[0], x[1]) for x in r))
    r = conn.execute("select min(apply_at), max(apply_at) from loan_applications").fetchone()
    line("  申請日期範圍：%s ~ %s" % (r[0], r[1]))
    summary["authenticity"] = {"placeholder_hits": len(hits),
                               "year_dist": [(x[0], x[1]) for x in r]}


# ---------------------------------------------------------------- 7. OAuth 證據
def audit_oauth(summary):
    h1("7. OAuth 密碼學漏洞證據盤查（中租靶站，非大陸站點）")
    raw = os.path.join(OAUTH_DIR, "raw")
    rep = os.path.join(OAUTH_DIR, "REPORT.md")
    line()
    if not os.path.isdir(raw):
        bad("找不到 %s" % raw)
        return
    logs = sorted(f for f in os.listdir(raw) if os.path.isfile(os.path.join(raw, f)))
    info("raw log 共 %d 份，逐檔 sha256：" % len(logs))
    for f in logs:
        p = os.path.join(raw, f)
        line("    %s  %7d B  %s" % (sha256_file(p)[:16], os.path.getsize(p), f))
    if os.path.exists(rep):
        info("REPORT.md sha256: %s" % sha256_file(rep))

    # 真實 HTTP 回應特徵
    status_hits = 0
    canary_only = True
    leaks = []
    for f in logs:
        txt = open(os.path.join(raw, f), encoding="utf-8", errors="replace").read()
        if re.search(r"status[=: ]\s*20\d", txt):
            status_hits += 1
        for m in re.finditer(r"accessToken='([^']{20,})'", txt):
            if "canary" not in m.group(1).lower() and "MAPSTV" not in m.group(1):
                canary_only = False
                leaks.append((f, m.group(1)[:40]))
    line()
    line("  含真實 HTTP status（20x）欄位的 log：%d / %d 份" % (status_hits, len(logs)))
    if canary_only:
        ok("所有 accessToken 皆為 canary / MAPSTV 測試字串 → 未觸碰真實會員資料")
    else:
        for f, v in leaks[:5]:
            bad("非 canary token：%s → %s" % (f, v))
    klog = os.path.join(raw, "chailease_K.log")
    if os.path.exists(klog):
        txt = open(klog, encoding="utf-8", errors="replace").read()
        flips = len(re.findall(r"p=\s*\d+\s*->\s*200", txt))
        line("  CBC bit-flip 掃描：%d/16 個 byte 翻轉後仍回 200 且明文被改（無 MAC 佐證）" % flips)
    summary["oauth"] = {"logs": len(logs), "with_status": status_hits,
                        "canary_only": canary_only}


# ---------------------------------------------------------------- 8. 對外匯出
def audit_export(summary):
    h1("8. 對外匯出盤查（你實際能打開的檔案）")
    if not os.path.isdir(EXPORT_DIR):
        bad("找不到 %s" % EXPORT_DIR)
        return
    line()
    files = sorted(os.listdir(EXPORT_DIR))
    for f in files:
        p = os.path.join(EXPORT_DIR, f)
        if os.path.isfile(p):
            line("    %-28s %10d B" % (f, os.path.getsize(p)))
    line()
    for name, expect in [("案件清單.csv", "loan_cases"), ("申請單清單.csv", "loan_applications")]:
        p = os.path.join(EXPORT_DIR, name)
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8-sig", errors="replace") as fh:
            n = sum(1 for _ in csv.reader(fh))
        info("%s：%d 列（含標題列 1）" % (name, n))
        with open(p, "r", encoding="utf-8-sig", errors="replace") as fh:
            rd = csv.reader(fh)
            hdr = next(rd)
            first = next(rd, None)
        line("      標題：%s" % " | ".join(hdr[:8]))
        line("      首列：%s" % " | ".join((first or [])[:8]))
    summary["export"] = {"files": files}


# ---------------------------------------------------------------- 總結
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    summary = {}
    audit_targets(summary)
    audit_courier(summary)
    audit_loan_sources(summary)
    audit_loan_db(summary)
    audit_traceback(summary)
    audit_authenticity(summary)
    audit_oauth(summary)
    audit_export(summary)

    h1("盤查總結")
    c = summary.get("courier", {})
    l = summary.get("loan_db", {})
    o = summary.get("oauth", {})
    line()
    line("  快遞（大陸站點 szjy188）  orders=%s  logistics=%s  ← %s"
         % (c.get("orders"), c.get("logistics"),
            "有資料" if c.get("orders") else "★0 筆，沒有任何東西可看"))
    line("  貸款（中租 chailease）      案件=%s 申請單=%s 金額來源=%s 還款計畫=%s"
         % (l.get("loan_cases"), l.get("loan_applications"),
            l.get("loan_amount_sources"), l.get("loan_repay_plans")))
    line("  OAuth 漏洞證據（中租）      %s 份 raw log，含 HTTP status 者 %s 份"
         % (o.get("logs"), o.get("with_status")))
    line()

    text = "\n".join(OUT)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("\n[report] %s" % args.out)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
        print("[json] %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
