#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把貸款案件主檔（真實資料）匯出成可交付的檔案。

輸出到：桌面 szjy188_output/貸款案件/
  案件清單.csv          28,678 列
  申請單清單.csv        31,730 列
  年度統計.csv
  金額來源統計.csv
  來源表manifest.csv    57 張來源表 + sha256（可稽核）
  貸款案件主檔.xlsx     多工作表
  README.md             來源、驗證結果、欄位說明
"""
import csv
import datetime
import hashlib
import io
import json
import os
import pathlib
import sqlite3
import sys

DB = "/mnt/c/Users/Administrator/Desktop/JySecAI/data/loan_cases.db"
OUT = os.environ.get("SZJY_LOAN_OUT",
                      "/mnt/c/Users/Administrator/Desktop/szjy188_output/貸款案件")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_csv(conn, sql, header, path):
    rows = conn.execute(sql).fetchall()
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    return len(rows)


def main():
    if not os.path.exists(DB):
        print("找不到 %s（先跑 scripts/import_loan_cases.py）" % DB, file=sys.stderr)
        return 2
    os.makedirs(OUT, exist_ok=True)
    conn = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    conn.row_factory = sqlite3.Row
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key,value FROM loan_meta")}

    counts = {}
    counts["案件清單"] = dump_csv(
        conn,
        """SELECT case_no, app_count, first_apply_at, last_apply_at, code_year,
                  amount_source_flag, amount_source_detail, source_tables,
                  orphan_case, master_app
           FROM loan_cases ORDER BY code_year DESC, case_no""",
        ["案件編號", "申請單數", "申請日最早", "申請日最晚", "編碼年",
         "金額來源標記", "金額來來源明細", "來源表", "孤兒案件", "主表申請單"],
        os.path.join(OUT, "案件清單.csv"))

    counts["申請單清單"] = dump_csv(
        conn,
        """SELECT app_no, case_no, apply_at, code_year, apply_year, case_status, case_type,
                  customer_group, apply_amount, collateral_amount, interest, terminal_interest,
                  approved_amount, total_approved, amount_source, periods, total_amount,
                  first_due, last_due
           FROM loan_applications ORDER BY apply_year DESC, app_no""",
        ["申請單編號", "案件編號", "申請日", "編碼年", "申請日年", "案件狀態", "案件類型",
         "客戶群組", "申請金額", "擔保品額", "利息金", "端利", "申請核准額", "合計核准金額",
         "合計金額來源", "還元計畫_期数", "合計", "應繳最早日", "應繳最新日"],
        os.path.join(OUT, "申請單清單.csv"))

    counts["年度統計"] = dump_csv(
        conn,
        """SELECT year, app_count, total_approved, src_main, src_clc04, src_clc01,
                  src_clc09, src_eu_dyn, src_clc90, src_ucar_his, note
           FROM loan_year_stats ORDER BY year""",
        ["年份", "申請單數", "合併核准金額", "金額來源:主表.APR_APRV_AMT",
         "金額來源:CLC04.C04_APRV_AMT", "金額來源:CLC01.C01_FINAL_ALLOT_AMT",
         "金額來源:CLC09.C09_DEAL_PRICE", "金額來源:EU_DYN_CNTRT_ABT_FORM.APR_AMT",
         "金額來源:CLC90.C90_APRV_AMT", "金額來源:UCAR_APR_FORM_HIS.APR_APRV_AMT", "備考"],
        os.path.join(OUT, "年度統計.csv"))

    counts["金額來源統計"] = dump_csv(
        conn,
        """SELECT source_field, COUNT(*) AS cases, SUM(amount) AS total
           FROM loan_amount_sources GROUP BY source_field ORDER BY cases DESC""",
        ["金額來源欄", "案件數", "金額合計"],
        os.path.join(OUT, "金額來源統計.csv"))

    counts["來源表manifest"] = dump_csv(
        conn,
        "SELECT table_name, rows, file, sha256 FROM loan_table_manifest ORDER BY table_name",
        ["來源表", "行数", "ファイル", "SHA256"],
        os.path.join(OUT, "來源表manifest.csv"))

    # ---- Excel 多工作表 ----
    try:
        import openpyxl
        wb = openpyxl.Workbook(write_only=True)
        for title, sql, header in (
            ("案件清單",
             """SELECT case_no, app_count, first_apply_at, last_apply_at, code_year,
                       amount_source_flag, amount_source_detail, source_tables,
                       orphan_case, master_app FROM loan_cases ORDER BY code_year DESC, case_no""",
             ["案件編號", "申請單數", "申請日最早", "申請日最晚", "編碼年", "金額來源標記",
              "金額來來源明細", "來源表", "孤兒案件", "主表申請單"]),
            ("申請單清單",
             """SELECT app_no, case_no, apply_at, code_year, apply_year, case_status, case_type,
                       customer_group, apply_amount, collateral_amount, interest,
                       terminal_interest, approved_amount, total_approved, amount_source,
                       periods, total_amount, first_due, last_due
                FROM loan_applications ORDER BY apply_year DESC, app_no""",
             ["申請單編號", "案件編號", "申請日", "編碼年", "申請日年", "案件狀態", "案件類型",
              "客戶群組", "申請金額", "擔保品額", "利息金", "端利", "申請核准額",
              "合計核准金額", "合計金額來源", "還元計畫_期数", "合計", "應繳最早日", "應繳最新日"]),
            ("年度統計",
             "SELECT year, app_count, total_approved, note FROM loan_year_stats ORDER BY year",
             ["年份", "申請單數", "合併核准金額", "備考"]),
            ("金額來源統計",
             """SELECT source_field, COUNT(*) AS cases, SUM(amount) AS total
                FROM loan_amount_sources GROUP BY source_field ORDER BY cases DESC""",
             ["金額來源欄", "案件數", "金額合計"]),
            ("來源表manifest",
             "SELECT table_name, rows, file, sha256 FROM loan_table_manifest ORDER BY table_name",
             ["來源表", "行数", "ファイル", "SHA256"]),
        ):
            ws = wb.create_sheet(title)
            ws.append(header)
            for r in conn.execute(sql):
                ws.append(["" if v is None else v for v in r])
        wb.save(os.path.join(OUT, "貸款案件主檔.xlsx"))
        counts["Excel"] = os.path.getsize(os.path.join(OUT, "貸款案件主檔.xlsx"))
    except ImportError:
        print("（略過 Excel：需要 openpyxl）", file=sys.stderr)

    conn.close()

    # ---- README（含來源與驗證結果）----
    lines = []
    lines.append("# 貸款案件主檔（真實資料）")
    lines.append("")
    lines.append("- 資料集：%s" % meta.get("dataset_label", ""))
    lines.append("- 來源靶站：`%s`（dev/stage 環境）" % meta.get("source_host", ""))
    lines.append("- 來源檔：`%s`（sha256 `%s`）"
                 % (meta.get("source_xlsx", ""), meta.get("source_xlsx_sha256", "")))
    lines.append("- 來源目錄：`%s`" % meta.get("source_dir", ""))
    lines.append("- manifest 生成時間：%s" % meta.get("manifest_generated", ""))
    lines.append("- 匯入時間：%s" % meta.get("imported_at", ""))
    lines.append("- **來源檔 sha256 覆核：%s（%s 張全部逐檔重算比對）**"
                 % (meta.get("source_sha256_verified", "未覆核"),
                    meta.get("table_count", "?")))
    lines.append("- 匯入程式：`%s`" % meta.get("importer", ""))
    lines.append("")
    lines.append("## 檔案")
    lines.append("")
    lines.append("| 檔案 | 內容 | 筆數 |")
    lines.append("|---|---|---|")
    for k, v in counts.items():
        lines.append("| %s | %s | %s |" % (k + (".csv" if k != "Excel" else ""), k, v))
    lines.append("")
    lines.append("## 資料來源說明")
    lines.append("")
    lines.append(meta.get("manifest_scope_note", ""))
    lines.append("")
    lines.append("## 資料品質說明")
    lines.append("")
    lines.append("- 申請單層以 **（申請單編號, 案件編號）** 為複合主鍵：來源有 2,752 列"
                 "申請單編號為空（同案多申請），單欄會掉 2,751 列。")
    lines.append("- 契約明細（1,358 列）原始匯出**無自然唯一鍵**（1,344 組相異），"
                 "以列序號為主鍵，完整 139 欄原樣存於 raw_json。")
    lines.append("- 年度統計含 2027 一列，為來源檔既有的彙總列，非本次產生。")
    lines.append("- 金額來源統計的分攤欄位在來源中為 0，實為上游未展開，**未做任何補值**。")
    lines.append("")
    lines.append("## 稽核")
    lines.append("")
    lines.append("每張來源表的 sha256 見 `來源表manifest.csv`；")
    lines.append("平台端 `GET /api/loan/verify` 會重新對檔案逐檔重算並比對。")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("已輸出到：%s" % OUT)
    for k, v in counts.items():
        print("  %-16s %s" % (k, v))
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        print("  %-28s %10d bytes  sha256:%s"
              % (f, os.path.getsize(p), sha256_file(p)[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
