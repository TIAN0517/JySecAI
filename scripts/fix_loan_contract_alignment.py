#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""契約明細（EU_DYN_CNTRT_ABT_DTL）欄名錯位修復。

根因（已驗證到欄位級）
----------------------
真表 = 138 欄（權威來源：CHAILEAse_DB_AllTables_20261023.xlsx 的表頭註記
「T_EU_DYN_CNTRT_ABT_DTL — 動態契約明細 138 欄 (1,358 列 x 138 欄)」）。
來源 csv/EU_DYN_CNTRT_ABT_DTL.csv = 138 個欄名 + 138 個值，**本身是對齊的**：
    MAJ_SEQ_ID=1889  SUB_SEQ_ID=1  FORM_ID=81287  FLW_ID=1000329
    STG_ID=0  INST_CD=T250301889  APLCNT_ID=07186  APLCNT_DEPT_ID=20640
    APLY_DT=2025-03-25 09:20:25

但組裝 XLSX「明細_契約明細」時，欄名列被多塞了一個假名
'EU_DYN_CNTRT_ABT_DTL'（139 個名），資料原樣帶入 → **欄名整體晚一格**：

    DB raw_json['MAJ_SEQ_ID']      實際是 SUB_SEQ_ID 的值
    DB raw_json['APLCNT_DEPT_ID']  實際是 APLY_DT 的值（日期！）
    DB raw_json['APLY_DT']         實際是 HNDLR_USR_ID 的值（空）
    DB raw_json['UPD_DT']          實際是 INST_CD 的值（代碼）
    最後一欄的真值因多一個名而**被丟棄**

交叉驗證：FORM 表（已對齊）同組 FORM_ID=81287、FLW_ID=1000329 與 DTL 表一致 ✓

修復 = 純改名（不搬值）
----------------------
    repaired[CSV_hdr[k]] = DB_value[k]   （k = 0..137）
即 DB_name[k+1] 才是 value[k] 的正確名稱；DB_name[0] 這個假名丟棄。

本腳本唯讀來源 DB，產出：
  1. loan_contract_details_repaired.csv   完整重標後的 138 欄 + 關鍵索引欄
  2. loan_contract_details_repair.sql     對應 UPDATE 語句（供人工執行）
  3. loan_contract_alignment_summary.json 前後對照摘要

Usage:
  python3 scripts/fix_loan_contract_alignment.py [--db data/loan_cases.db] [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$")
NUM_RE = re.compile(r"^-?\.?\d+(\.\d+)?$")
CODE_RE = re.compile(r"^[A-Za-z]{1,3}[\w\-]*$")

SRC_CSV = Path("/mnt/c/Users/Administrator/Desktop/888/case_master_v5_2023_2026/csv/EU_DYN_CNTRT_ABT_DTL.csv")

KEY_FIELDS = ["MAJ_SEQ_ID", "SUB_SEQ_ID", "FORM_ID", "FLW_ID", "STG_ID", "CAD_CNTRT_NO", "APLY_DT", "APRV_AMT"]


def expected(name: str):
    n = name.upper()
    if n.endswith(("_DT", "_DATE")):
        return "date"
    if n.endswith(("_ID", "_NO", "_AMT", "_PRD", "_SEQ", "_RATE", "_IRR", "_PCT",
                    "_IND", "_CNTRT", "_CD", "_TYP", "_QTY", "_DAYS", "_NME", "_USR")):
        return "num"
    return None


def actual_of(values: list[str]) -> str:
    ne = [v for v in values if str(v or "").strip() != ""]
    if not ne:
        return "empty"
    d = sum(1 for v in ne if DATE_RE.match(str(v).strip()))
    n = sum(1 for v in ne if NUM_RE.match(str(v).strip()))
    c = sum(1 for v in ne if CODE_RE.match(str(v).strip()))
    if d / len(ne) >= 0.6:
        return "date"
    if n / len(ne) >= 0.6:
        return "num"
    if c / len(ne) >= 0.6:
        return "code"
    return "text"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/loan_cases.db")
    ap.add_argument("--out", default="/mnt/c/Users/Administrator/Desktop/chailease_midsig_exp/loot")
    ap.add_argument("--src-csv", default=str(SRC_CSV))
    args = ap.parse_args()

    # ---- 來源 CSV 的真欄名（138 個） ----
    with open(args.src_csv, encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh)
        csv_hdr = next(rd)
    print(f"來源 CSV 欄名數：{len(csv_hdr)}（真表應為 138）")
    if len(csv_hdr) != 138:
        print("！欄名數與權威值不符，請先確認來源 CSV 版本", file=__import__("sys").stderr)

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT row_no, maj_seq_id, sub_seq_id, form_id, flw_id, stg_id, case_no,"
        " apply_dt, apprv_amt, raw_json FROM loan_contract_details ORDER BY row_no"
    ).fetchall()
    conn.close()

    db_names: list[str] = []
    seen = set()
    for r in rows:
        for k in json.loads(r[9]).keys():
            if k not in seen:
                seen.add(k)
                db_names.append(k)
    print(f"DB raw_json 欄名數：{len(db_names)}（多出 {len(db_names) - len(csv_hdr)} 個）")
    print(f"DB 第 1 個欄名（假名，應丟棄）：{db_names[0]!r}")
    print(f"DB 第 2 個欄名（= CSV 第 1 欄）：{db_names[1]!r} vs CSV {csv_hdr[0]!r}")
    print(f"DB 末欄名：{db_names[-1]!r}（其對應的真值被丟棄）")

    # ---- 修復：repaired[csv_hdr[k]] = DB_value[k] ----
    repaired_rows = []
    sql_stmts = []
    for r in rows:
        obj = json.loads(r[9])
        vals = ["" if obj.get(nm) is None else str(obj.get(nm)) for nm in db_names]
        rep = {csv_hdr[k]: vals[k] for k in range(len(csv_hdr))}
        rec = {"row_no": r[0]}
        for kf in KEY_FIELDS:
            rec[kf] = rep.get(kf, "")
        rec["_full"] = rep
        repaired_rows.append(rec)
        sql_stmts.append(
            "UPDATE loan_contract_details SET maj_seq_id=%s, sub_seq_id=%s, form_id=%s,"
            " flw_id=%s, stg_id=%s, case_no=%s, apply_dt=%s, apprv_amt=%s, raw_json=%s"
            " WHERE row_no=%s;" % (
                _q(rep.get("MAJ_SEQ_ID", "")), _q(rep.get("SUB_SEQ_ID", "")),
                _q(rep.get("FORM_ID", "")), _q(rep.get("FLW_ID", "")),
                _q(rep.get("STG_ID", "")), _q(rep.get("CAD_CNTRT_NO", "")),
                _q(rep.get("APLY_DT", "")), _q(rep.get("APRV_AMT", "")),
                _q(json.dumps(rep, ensure_ascii=False)), r[0]))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # 1) 完整重標 CSV
    cp = out / "loan_contract_details_repaired.csv"
    with cp.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["row_no"] + KEY_FIELDS + csv_hdr)
        for rec in repaired_rows:
            w.writerow([rec["row_no"]] + [rec[kf] for kf in KEY_FIELDS] +
                       [rec["_full"].get(c, "") for c in csv_hdr])
    print(f"\n→ {cp}（{len(repaired_rows)} 列 × {len(csv_hdr)+1+len(KEY_FIELDS)} 欄）")

    # 2) UPDATE 語句
    sp = out / "loan_contract_details_repair.sql"
    sp.write_text("-- 由 fix_loan_contract_alignment.py 產生；執行前請先備份 loan_cases.db\n"
                  + "\n".join(sql_stmts) + "\n", encoding="utf-8")
    print(f"→ {sp}")

    # 3) 摘要
    buckets = defaultdict(list)
    for rec in repaired_rows:
        for k, v in rec["_full"].items():
            buckets[k].append(v)
    mismatched = []
    for k in csv_hdr:
        exp = expected(k)
        act = actual_of(buckets[k])
        ne = sum(1 for v in buckets[k] if str(v).strip() != "")
        rate = ne / len(buckets[k]) * 100
        if exp and act != "empty" and exp != act and not (exp == "num" and act == "code"):
            mismatched.append({"column": k, "expected": exp, "actual": act, "nonempty_pct": round(rate, 1)})

    before = {
        "maj_seq_id": rows[0][1], "sub_seq_id": rows[0][2], "form_id": rows[0][3],
        "flw_id": rows[0][4], "stg_id": rows[0][5], "case_no": rows[0][6],
        "apply_dt": rows[0][7], "apprv_amt": rows[0][8],
    }
    after = {kf: repaired_rows[0][kf] for kf in KEY_FIELDS}
    after["apply_dt"] = repaired_rows[0]["APLY_DT"]
    after["case_no"] = repaired_rows[0]["CAD_CNTRT_NO"]

    summary = {
        "table": "loan_contract_details",
        "rows": len(rows),
        "true_columns": len(csv_hdr),
        "db_columns": len(db_names),
        "bogus_first_column": db_names[0],
        "repair_rule": "repaired[csv_hdr[k]] = raw_json_value[k]; 欄名整體晚一格，純改名不搬值",
        "apply_dt_empty_before": sum(1 for r in rows if not str(r[7] or "").strip()),
        "apply_dt_nonempty_after": sum(1 for rec in repaired_rows if rec["APLY_DT"].strip()),
        "index_row1_before": before,
        "index_row1_after": after,
        "residual_type_mismatch_after_repair": mismatched,
        "outputs": {"repaired_csv": str(cp), "repair_sql": str(sp)},
    }
    jp = out / "loan_contract_alignment_summary.json"
    jp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {jp}")

    print("\n第 1 列修復前後：")
    pairs = [("maj_seq_id", "MAJ_SEQ_ID"), ("sub_seq_id", "SUB_SEQ_ID"), ("form_id", "FORM_ID"),
             ("flw_id", "FLW_ID"), ("stg_id", "STG_ID"), ("case_no", "CAD_CNTRT_NO"),
             ("apply_dt", "APLY_DT")]
    for bkey, akey in pairs:
        print(f"   {bkey:12} {str(before.get(bkey, '')):22} → {repaired_rows[0][akey]}")
    print(f"\napply_dt：修復前空 {summary['apply_dt_empty_before']}/{len(rows)}"
          f"，修復後非空 {summary['apply_dt_nonempty_after']}/{len(rows)}")
    print(f"修復後仍型態不符欄位：{len(mismatched)} 個")
    for m in mismatched:
        print(f"   {m['column']:26} 期望 {m['expected']:5} 實際 {m['actual']:5} 非空 {m['nonempty_pct']:5.1f}%")
    return 0


def _q(v) -> str:
    if v is None or v == "":
        return "''"
    s = str(v)
    return "'" + s.replace("'", "''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
