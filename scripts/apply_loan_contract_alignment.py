#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「契約明細欄名錯位」修復套用到 data/loan_cases.db。

先備份 → 單一交易套用 → 驗證 → 提交。分析請用 fix_loan_contract_alignment.py（唯讀）。

修復內容（純改名，不搬值）
--------------------------
真表 138 欄（權威：CHAILEAse_DB_AllTables_20261023.xlsx 表頭註記
「T_EU_DYN_CNTRT_ABT_DTL — 動態契約明細 138 欄 (1,358 列 x 138 欄)」）。
DB 的 raw_json 有 139 個欄名，第 1 個 'EU_DYN_CNTRT_ABT_DTL' 是多塞的假名，
導致欄名整體晚一格：

    repaired[csv_hdr[k]] = DB_value[k]     (k = 0..137)

連帶修正索引欄：maj_seq_id / sub_seq_id / form_id / flw_id / stg_id / case_no /
apply_dt / apprv_amt。

Usage:
  python3 scripts/apply_loan_contract_alignment.py --db data/loan_cases.db
  python3 scripts/apply_loan_contract_alignment.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

SRC_CSV = Path("/mnt/c/Users/Administrator/Desktop/888/case_master_v5_2023_2026/csv/EU_DYN_CNTRT_ABT_DTL.csv")
KEYS = {
    "maj_seq_id": "MAJ_SEQ_ID",
    "sub_seq_id": "SUB_SEQ_ID",
    "form_id": "FORM_ID",
    "flw_id": "FLW_ID",
    "stg_id": "STG_ID",
    "case_no": "CAD_CNTRT_NO",
    "apply_dt": "APLY_DT",
    "apprv_amt": "APRV_AMT",
}


def load_source_headers(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return next(csv.reader(fh))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/loan_cases.db")
    ap.add_argument("--src-csv", default=str(SRC_CSV))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db = Path(args.db)
    csv_hdr = load_source_headers(Path(args.src_csv))
    if len(csv_hdr) != 138:
        print(f"！來源 CSV 欄名數 {len(csv_hdr)} ≠ 138，中止", file=sys.stderr)
        return 2

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys=ON")
    rows = conn.execute(
        "SELECT row_no, raw_json FROM loan_contract_details ORDER BY row_no").fetchall()
    if not rows:
        print("loan_contract_details 是空的，中止", file=sys.stderr)
        return 2

    db_names: list[str] = []
    seen = set()
    for _, rj in rows:
        for k in json.loads(rj).keys():
            if k not in seen:
                seen.add(k)
                db_names.append(k)
    if len(db_names) != len(csv_hdr) + 1:
        print(f"！DB 欄名數 {len(db_names)} ≠ {len(csv_hdr)}+1，中止（版本不符）", file=sys.stderr)
        return 2
    if db_names[1:] != csv_hdr:
        print("！DB 欄名（去掉第 1 個）與來源 CSV 不一致，中止", file=sys.stderr)
        return 2
    print(f"檢查通過：DB {len(db_names)} 名（去掉假名 {db_names[0]!r} 後）≡ 來源 CSV {len(csv_hdr)} 名")

    # ---- 組出修復後的每列 ----
    plan = []
    for row_no, rj in rows:
        obj = json.loads(rj)
        vals = ["" if obj.get(nm) is None else str(obj.get(nm)) for nm in db_names]
        rep = {csv_hdr[k]: vals[k] for k in range(len(csv_hdr))}
        plan.append((row_no, rep))

    before = conn.execute(
        "SELECT COUNT(*) FROM loan_contract_details WHERE apply_dt IS NULL OR TRIM(apply_dt)=''").fetchone()[0]
    join_before = conn.execute(
        "SELECT COUNT(*) FROM loan_contract_details d JOIN loan_cases c ON c.case_no=d.case_no").fetchone()[0]
    print(f"套用前：apply_dt 空 {before}/{len(rows)}；case_no 可 join 案件層 {join_before}/{len(rows)}")

    if args.dry_run:
        print("dry-run：未寫入。首列修復結果：")
        rep = plan[0][1]
        for k, name in KEYS.items():
            print(f"   {k:12} {rep.get(name,'')}")
        return 0

    # ---- 備份 ----
    stamp = time.strftime("%Y%m%dT%H%M%S")
    backup = db.with_name(db.name + f".bak-before-align-fix-{stamp}")
    shutil.copy2(db, backup)
    for suffix in ("-wal", "-shm"):
        p = Path(str(db) + suffix)
        if p.exists() and p.stat().st_size > 0:
            shutil.copy2(p, Path(str(backup) + suffix))
    print(f"已備份：{backup}（{backup.stat().st_size:,} bytes）")

    # ---- 套用（單一交易）----
    try:
        conn.execute("BEGIN IMMEDIATE")
        for row_no, rep in plan:
            conn.execute(
                "UPDATE loan_contract_details SET maj_seq_id=?, sub_seq_id=?, form_id=?, flw_id=?,"
                " stg_id=?, case_no=?, apply_dt=?, apprv_amt=?, raw_json=? WHERE row_no=?",
                (rep.get("MAJ_SEQ_ID", ""), rep.get("SUB_SEQ_ID", ""), rep.get("FORM_ID", ""),
                 rep.get("FLW_ID", ""), rep.get("STG_ID", ""), rep.get("CAD_CNTRT_NO", ""),
                 rep.get("APLY_DT", ""), rep.get("APRV_AMT", ""),
                 json.dumps(rep, ensure_ascii=False), row_no))
        conn.commit()
    except Exception:
        conn.rollback()
        print("套用失敗，已回滾", file=sys.stderr)
        raise
    print(f"已提交 {len(plan)} 列")

    # ---- 驗證 ----
    after = conn.execute(
        "SELECT COUNT(*) FROM loan_contract_details WHERE apply_dt IS NULL OR TRIM(apply_dt)=''").fetchone()[0]
    join_after = conn.execute(
        "SELECT COUNT(*) FROM loan_contract_details d JOIN loan_cases c ON c.case_no=d.case_no").fetchone()[0]
    n_case = conn.execute("SELECT COUNT(*) FROM loan_cases").fetchone()[0]
    n_app = conn.execute("SELECT COUNT(*) FROM loan_applications").fetchone()[0]
    n_det = conn.execute("SELECT COUNT(*) FROM loan_contract_details").fetchone()[0]
    integ = conn.execute("PRAGMA integrity_check").fetchone()[0]
    sample = conn.execute(
        "SELECT row_no, maj_seq_id, sub_seq_id, form_id, flw_id, stg_id, case_no, apply_dt, apprv_amt"
        " FROM loan_contract_details ORDER BY row_no LIMIT 3").fetchall()
    conn.close()

    print(f"\n套用後：apply_dt 空 {after}/{n_det}；case_no 可 join 案件層 {join_after}/{n_det}")
    print(f"完整性：integrity_check={integ}；loan_cases={n_case} loan_applications={n_app} loan_contract_details={n_det}")
    print("\n抽樣：")
    for s in sample:
        print("   ", s)

    ok = (after == 0 and integ == "ok" and n_case == 28678 and n_app == 31730
          and n_det == 1358 and join_after > join_before)
    print("\n驗證結果：", "PASS" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
