#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把真實的中租（chailease）貸款案件主檔匯入 JySecAI 的貸款資料庫。

來源（唯讀，不修改）：
  /mnt/c/Users/Administrator/Desktop/888/case_master_v5_2023_2026/
    CHAILEAse_CaseMaster_v5_2023_2026.xlsx   9 個工作表（案件主檔 v5）
    manifest.json                             57 張來源表 + 行數 + sha256
    csv/                                      57 張原始匯出（供逐檔 sha256 覆核）

輸出：
  <out>  SQLite（預設 data/loan_cases.db），供 JySecAI 的 /api/loan/* 唯讀橋接。

設計原則
--------
* **只匯真實資料**：每列都來自 xlsx 的一列；不做任何補值、推估或示範列。
* **可稽核**：每張來源表的 sha256 與行數都進 loan_table_manifest；
  匯入後可由 /api/loan/verify 重新對檔案算 sha256 比對。
* **冪等**：每次匯入先重建表，不留舊資料。
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import sys

DEFAULT_SRC = "/mnt/c/Users/Administrator/Desktop/888/case_master_v5_2023_2026"
DEFAULT_OUT = "/mnt/c/Users/Administrator/Desktop/JySecAI/data/loan_cases.db"

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS loan_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS loan_cases (
    case_no             TEXT PRIMARY KEY,
    app_count           INTEGER,
    first_apply_at      TEXT,
    last_apply_at       TEXT,
    code_year           INTEGER,
    amount_source_flag  TEXT,
    amount_source_detail TEXT,
    source_tables       TEXT,
    orphan_case         TEXT,
    master_app          TEXT
);

CREATE TABLE IF NOT EXISTS loan_applications (
    app_no               TEXT NOT NULL,
    case_no              TEXT,
    apply_at             TEXT,
    code_year            INTEGER,
    apply_year           INTEGER,
    case_status          TEXT,
    case_type            TEXT,
    customer_group       TEXT,
    apply_amount         REAL,
    collateral_amount    REAL,
    interest             REAL,
    terminal_interest    REAL,
    approved_amount      REAL,
    total_approved       REAL,
    amount_source        TEXT,
    amount_source_detail TEXT,
    amount_source_detail2 TEXT,
    periods              INTEGER,
    total_amount         REAL,
    first_due            TEXT,
    last_due             TEXT,
    orphan_flag          TEXT,
    PRIMARY KEY (app_no, case_no)
);

CREATE TABLE IF NOT EXISTS loan_amount_sources (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    case_no      TEXT,
    source_field TEXT,
    amount       REAL,
    level        TEXT
);

CREATE TABLE IF NOT EXISTS loan_year_stats (
    year            INTEGER PRIMARY KEY,
    app_count       INTEGER,
    total_approved  REAL,
    src_main        REAL,
    src_clc04       REAL,
    src_clc01       REAL,
    src_clc09       REAL,
    src_eu_dyn      REAL,
    src_clc90       REAL,
    src_ucar_his    REAL,
    note            TEXT
);

CREATE TABLE IF NOT EXISTS loan_table_manifest (
    table_name TEXT PRIMARY KEY,
    rows       INTEGER,
    file       TEXT,
    sha256     TEXT
);

CREATE TABLE IF NOT EXISTS loan_repay_plans (
    app_no    TEXT PRIMARY KEY,
    periods   INTEGER,
    total_pay REAL,
    first_due TEXT,
    last_due  TEXT
);

CREATE TABLE IF NOT EXISTS loan_collateral_monthly (
    plan_no       TEXT PRIMARY KEY,
    periods       INTEGER,
    total_monthly REAL,
    cum_principal REAL,
    cum_interest  REAL,
    total_fee     REAL,
    first_date    TEXT,
    last_date     TEXT
);

CREATE TABLE IF NOT EXISTS loan_contract_details (
    row_no     INTEGER PRIMARY KEY,   -- 匯出檔無自然唯一鍵（1,358 列僅 1,344 組相異），以列序號保底
    maj_seq_id TEXT,
    sub_seq_id TEXT,
    form_id    TEXT,
    flw_id     TEXT,
    stg_id     TEXT,
    case_no    TEXT,
    apply_dt   TEXT,
    apprv_amt  REAL,
    raw_json   TEXT
);

CREATE INDEX IF NOT EXISTS idx_loan_cases_year     ON loan_cases(code_year);
CREATE INDEX IF NOT EXISTS idx_loan_apps_case      ON loan_applications(case_no);
CREATE INDEX IF NOT EXISTS idx_loan_apps_year      ON loan_applications(apply_year);
CREATE INDEX IF NOT EXISTS idx_loan_src_case       ON loan_amount_sources(case_no);
CREATE INDEX IF NOT EXISTS idx_loan_contract_case  ON loan_contract_details(case_no);
"""


def s(v):
    """轉字串：None → 空字串；datetime → ISO 格式。"""
    if v is None:
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat(sep=" ")
    return str(v)


def num(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def i(v):
    try:
        if v is None or v == "":
            return None
        return int(float(v))
    except (TypeError, ValueError):
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="匯入真實貸款案件主檔")
    ap.add_argument("--src", default=DEFAULT_SRC, help="來源目錄")
    ap.add_argument("--out", default=DEFAULT_OUT, help="輸出 SQLite")
    ap.add_argument("--verify-sources", action="store_true",
                    help="逐一重算來源 csv 的 sha256（較慢）")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    xlsx = src / "CHAILEAse_CaseMaster_v5_2023_2026.xlsx"
    manifest_path = src / "manifest.json"
    if not xlsx.exists():
        print("找不到來源檔：%s" % xlsx, file=sys.stderr)
        return 2

    try:
        import openpyxl
    except ImportError:
        print("需要 openpyxl（系統 python3 已有）", file=sys.stderr)
        return 2

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    for suffix in ("-wal", "-shm"):
        p = pathlib.Path(str(out) + suffix)
        if p.exists():
            p.unlink()

    conn = sqlite3.connect(str(out))
    conn.executescript(SCHEMA)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    wb = openpyxl.load_workbook(str(xlsx), read_only=True, data_only=True)

    stats = {}

    def sheet_rows(name):
        ws = wb[name]
        it = ws.iter_rows(values_only=True)
        hdr = next(it, None)
        return hdr, it

    # ---- 案件層 ----
    hdr, it = sheet_rows("案件層")
    n = 0
    rows = []
    for r in it:
        if r is None or all(c is None for c in r):
            continue
        rows.append((s(r[0]), i(r[1]), s(r[2]), s(r[3]), i(r[4]),
                     s(r[5]), s(r[6]), s(r[7]), s(r[8]), s(r[9])))
    conn.executemany(
        "INSERT OR REPLACE INTO loan_cases(case_no,app_count,first_apply_at,last_apply_at,"
        "code_year,amount_source_flag,amount_source_detail,source_tables,orphan_case,master_app)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
    n = len(rows)
    stats["loan_cases"] = n

    # ---- 申請單層 ----
    hdr, it = sheet_rows("CASE_MASTER_2023_2026")
    rows = []
    for r in it:
        if r is None or all(c is None for c in r):
            continue
        rows.append((s(r[0]), s(r[1]), s(r[2]), i(r[3]), i(r[4]), s(r[5]), s(r[6]),
                     s(r[7]), num(r[8]), num(r[9]), num(r[10]), num(r[11]), num(r[12]),
                     num(r[13]), s(r[14]), s(r[15]), s(r[16]), i(r[17]), num(r[18]),
                     s(r[19]), s(r[20]), s(r[21]) if len(r) > 21 else ""))
    conn.executemany(
        "INSERT OR REPLACE INTO loan_applications(app_no,case_no,apply_at,code_year,apply_year,"
        "case_status,case_type,customer_group,apply_amount,collateral_amount,interest,"
        "terminal_interest,approved_amount,total_approved,amount_source,amount_source_detail,"
        "amount_source_detail2,periods,total_amount,first_due,last_due,orphan_flag)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    stats["loan_applications"] = len(rows)

    # ---- 金額來源追蹤 ----
    hdr, it = sheet_rows("金額來源追蹤")
    rows = []
    for r in it:
        if r is None or all(c is None for c in r):
            continue
        rows.append((s(r[0]), s(r[1]), num(r[2]), s(r[3])))
    conn.executemany(
        "INSERT INTO loan_amount_sources(case_no,source_field,amount,level) VALUES(?,?,?,?)", rows)
    stats["loan_amount_sources"] = len(rows)

    # ---- YEAR_STATS ----
    hdr, it = sheet_rows("YEAR_STATS")
    rows = []
    for r in it:
        if r is None or r[0] is None:
            continue
        rows.append((i(r[0]), i(r[1]), num(r[2]), num(r[3]), num(r[4]), num(r[5]),
                     num(r[6]), num(r[7]), num(r[8]), num(r[9]), s(r[10])))
    conn.executemany(
        "INSERT OR REPLACE INTO loan_year_stats(year,app_count,total_approved,src_main,src_clc04,"
        "src_clc01,src_clc09,src_eu_dyn,src_clc90,src_ucar_his,note) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        rows)
    stats["loan_year_stats"] = len(rows)

    # ---- 還元計畫 ----
    for sheet, table in (("明細_還元計畫", "loan_repay_plans"),
                         ("明細_還元計畫_HIS", "loan_repay_plans_his")):
        if sheet not in wb.sheetnames:
            continue
        hdr, it = sheet_rows(sheet)
        rows = [(s(r[0]), i(r[1]), num(r[2]), s(r[3]), s(r[4])) for r in it
                if r and any(c is not None for c in r)]
        if table == "loan_repay_plans":
            conn.executemany(
                "INSERT OR REPLACE INTO loan_repay_plans(app_no,periods,total_pay,first_due,last_due)"
                " VALUES(?,?,?,?,?)", rows)
            stats[table] = len(rows)
        else:
            conn.execute("CREATE TABLE IF NOT EXISTS loan_repay_plans_his("
                         "app_no TEXT PRIMARY KEY, periods INTEGER, total_pay REAL,"
                         "first_due TEXT, last_due TEXT)")
            conn.executemany(
                "INSERT OR REPLACE INTO loan_repay_plans_his(app_no,periods,total_pay,first_due,last_due)"
                " VALUES(?,?,?,?,?)", rows)
            stats[table] = len(rows)

    # ---- 擔保月款 ----
    hdr, it = sheet_rows("明細_擔保月款")
    rows = [(s(r[0]), i(r[1]), num(r[2]), num(r[3]), num(r[4]), num(r[5]), s(r[6]), s(r[7]))
            for r in it if r and any(c is not None for c in r)]
    conn.executemany(
        "INSERT OR REPLACE INTO loan_collateral_monthly(plan_no,periods,total_monthly,"
        "cum_principal,cum_interest,total_fee,first_date,last_date) VALUES(?,?,?,?,?,?,?,?)", rows)
    stats["loan_collateral_monthly"] = len(rows)

    # ---- 契約明細（真表 138 欄，原樣存 JSON + 幾個關鍵欄） ----
    hdr, it = sheet_rows("明細_契約明細")
    hdr = [s(h) for h in hdr]

    # 防復發：組裝 XLSX 時曾多塞一個假欄名 'EU_DYN_CNTRT_ABT_DTL'（真表 138 欄、無此欄），
    # 導致欄名整體晚一格：值對到錯的欄位（apply_dt 全空、case_no 對不到案件層），
    # 且最後一欄的真值被多出的空欄位擠掉。
    # 真表欄數見 CHAILEAse_DB_AllTables_20261023.xlsx 的表頭註記：
    #   「T_EU_DYN_CNTRT_ABT_DTL — 動態契約明細 138 欄 (1,358 列 x 138 欄)」
    # 處理方式：去掉該假名後，欄名與值列重新一一對上（值不動、只改名）。
    if hdr and hdr[0] == "EU_DYN_CNTRT_ABT_DTL" and len(hdr) == 139:
        print("[修正] 明細_契約明細 偵測到多餘欄名 'EU_DYN_CNTRT_ABT_DTL'（真表無此欄），"
              "欄名整體後移一格 → 已去除該名重新對齊")
        hdr = hdr[1:]

    idx = {h: i for i, h in enumerate(hdr)}
    rows = []
    for row_no, r in enumerate(it, start=1):
        if r is None or all(c is None for c in r):
            continue
        obj = {hdr[i]: (s(r[i]) if i < len(r) else "") for i in range(len(hdr))}
        rows.append((row_no,
                     s(r[idx["MAJ_SEQ_ID"]]) if "MAJ_SEQ_ID" in idx else "",
                     s(r[idx["SUB_SEQ_ID"]]) if "SUB_SEQ_ID" in idx else "",
                     s(r[idx["FORM_ID"]]) if "FORM_ID" in idx else "",
                     s(r[idx["FLW_ID"]]) if "FLW_ID" in idx else "",
                     s(r[idx["STG_ID"]]) if "STG_ID" in idx else "",
                     s(r[idx["CAD_CNTRT_NO"]]) if "CAD_CNTRT_NO" in idx else "",
                     s(r[idx["APLY_DT"]]) if "APLY_DT" in idx else "",
                     num(r[idx["APRV_AMT"]]) if "APRV_AMT" in idx else None,
                     json.dumps(obj, ensure_ascii=False)))
    conn.executemany(
        "INSERT OR REPLACE INTO loan_contract_details(row_no,maj_seq_id,sub_seq_id,form_id,"
        "flw_id,stg_id,case_no,apply_dt,apprv_amt,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
    stats["loan_contract_details"] = len(rows)

    # ---- manifest（57 表 + sha256） ----
    mrows = []
    verify_report = []
    for t in manifest.get("tables", []):
        name = t.get("table")
        rows_n = t.get("rows")
        rel = t.get("file") or ("csv/%s" % name)
        sha = t.get("sha256") or ""
        mrows.append((name, rows_n, rel, sha))
        if args.verify_sources:
            fp = src / rel
            if not fp.exists():
                fp = src / "csv" / name
            if fp.exists():
                actual = sha256_file(fp)
                verify_report.append({"table": name, "ok": actual == sha,
                                      "expected": sha, "actual": actual})
    conn.executemany(
        "INSERT OR REPLACE INTO loan_table_manifest(table_name,rows,file,sha256) VALUES(?,?,?,?)",
        mrows)
    stats["loan_table_manifest"] = len(mrows)

    # ---- meta ----
    meta = {
        "dataset": "chailease_mid_sign_case_master_v5_2023_2026",
        "dataset_label": "中租 mid-sign 貸款案件主檔 v5（2023–2026）",
        "source_host": "mid-sign-dev.chailease.com.tw",
        "source_dir": str(src),
        "source_xlsx": xlsx.name,
        "source_xlsx_sha256": sha256_file(xlsx),
        "manifest_generated": manifest.get("generated", ""),
        "manifest_scope_note": manifest.get("scope_note", ""),
        "imported_at": datetime.datetime.now().astimezone().isoformat(),
        "importer": "scripts/import_loan_cases.py",
        "table_count": str(len(mrows)),
    }
    for k, v in stats.items():
        meta["rows_" + k] = str(v)
    conn.executemany("INSERT OR REPLACE INTO loan_meta(key,value) VALUES(?,?)",
                     sorted(meta.items()))
    conn.commit()

    if verify_report:
        ok = sum(1 for r in verify_report if r["ok"])
        meta["source_sha256_verified"] = "%d/%d" % (ok, len(verify_report))
        conn.executemany("INSERT OR REPLACE INTO loan_meta(key,value) VALUES(?,?)",
                         [("source_sha256_verified", meta["source_sha256_verified"])])
        conn.commit()
        print("來源檔 sha256 覆核：%d/%d 通過" % (ok, len(verify_report)))
        for r in verify_report:
            if not r["ok"]:
                print("  [MISMATCH] %s" % r["table"])

    conn.execute("VACUUM")
    conn.close()

    print("已匯入 → %s" % out)
    for k in sorted(stats):
        print("  %-28s %8d 列" % (k, stats[k]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
