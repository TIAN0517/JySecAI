#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_loan_classification.py — 貸款案件分類字典＋交叉統計

輸出到：桌面 szjy188_output/貸款案件/
  貸款案件分類字典.xlsx   多工作表
  分類/狀態代碼字典.csv
  分類/類型字典.csv
  分類/客群字典.csv
  分類/狀態x年度.csv
  分類/狀態x類型.csv
  分類/客群x狀態.csv
  分類/金額來源x年度.csv
  分類/案件來源表分布.csv
  分類/案件層與申請單層對照.csv

資料血緣（務必如實標註）
--------------------------
  來源：data/loan_cases.db  ←  scripts/import_loan_cases.py
        ←  Desktop/888/case_master_v5_2023_2026/（本機既有匯出檔，57 表 sha256 全過）
        ←  同一靶站 mid-sign-dev.chailease.com.tw
  **不是**本次線上直拉的資料。字典的中文名稱在中租同站點的離線資料中不存在，
  因此「中文名稱」欄一律標「待補」，只填**可由資料推得**的特徵，不臆測。
"""
import csv
import datetime
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("LOAN_DB_PATH", os.path.join(ROOT, "data", "loan_cases.db"))
OUT = os.environ.get("SZJY_LOAN_OUT",
                     "/mnt/c/Users/Administrator/Desktop/szjy188_output/貸款案件")
SUB = os.path.join(OUT, "分類")

PENDING = "待補（同站點離線資料無中文字典）"


def q(conn, sql, args=()):
    return conn.execute(sql, args).fetchall()


def money(v):
    try:
        return round(float(v or 0))
    except Exception:
        return 0


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def build_status_dict(conn):
    """狀態代碼字典：以資料可推得的特徵描述，不臆測中文名。"""
    total = q(conn, "select count(*) c, sum(coalesce(approved_amount,0)) a "
                    "from loan_applications")[0]
    rows = []
    for r in q(conn, """
        select coalesce(nullif(a.case_status,''),'(空)') st,
               count(*) n,
               sum(coalesce(a.approved_amount,0)) amt,
               sum(coalesce(a.apply_amount,0)) app,
               sum(case when p.app_no is null then 0 else 1 end) with_plan,
               round(avg(coalesce(p.periods,0)),1) avg_periods,
               min(a.apply_year) y0, max(a.apply_year) y1,
               sum(case when a.orphan_flag<>'' and a.orphan_flag is not null then 1 else 0 end) orphan
        from loan_applications a
        left join loan_repay_plans p on p.app_no = a.app_no
        group by st order by n desc"""):
        st, n, amt, app, wp, ap, y0, y1, orphan = r
        feat = []
        if n and wp == n:
            feat.append("全部具還款計畫 → 已核准放款")
        elif wp == 0:
            feat.append("無還款計畫 → 未放款/僅申請")
        else:
            feat.append("部分有還款計畫")
        if y0:
            feat.append("年度 %s–%s" % (y0, y1))
        if ap:
            feat.append("平均還款期數 %s 期" % ap)
        if orphan:
            feat.append("其中孤兒申請單 %d" % orphan)
        rows.append([
            st, n, round(100.0 * n / total["c"], 2) if total["c"] else 0,
            money(amt), money(app),
            round(money(amt) / n) if n else 0,
            wp, ap, y0, y1,
            "；".join(feat), PENDING,
        ])
    return (["狀態代碼", "申請單筆數", "佔比%", "核准額合計", "申請額合計",
             "平均核准額", "有還款計畫筆數", "平均還款期數", "最早年度", "最近年度",
             "資料可推得特徵", "中文名稱"], rows)


def build_simple_dict(conn, col, label):
    total = q(conn, "select count(*) c, sum(coalesce(approved_amount,0)) a "
                    "from loan_applications")[0]
    rows = []
    for r in q(conn, """
        select coalesce(nullif(%s,''),'(空)') v, count(*) n,
               sum(coalesce(approved_amount,0)) amt,
               sum(case when p.app_no is null then 0 else 1 end) wp
        from loan_applications a
        left join loan_repay_plans p on p.app_no=a.app_no
        group by v order by n desc""" % col):
        v, n, amt, wp = r
        rows.append([v, n, round(100.0 * n / total["c"], 2) if total["c"] else 0,
                     money(amt), round(money(amt) / n) if n else 0, wp, PENDING])
    return ([label, "筆數", "佔比%", "核准額合計", "平均核准額",
             "有還款計畫筆數", "中文名稱"], rows)


def build_cross(conn, row_col, col_col, label_a, label_b, year_col=None):
    if year_col:
        sql = ("select coalesce(nullif(%s,''),'(空)') a, coalesce(nullif(%s,''),'(空)') b,"
               " count(*) n, sum(coalesce(approved_amount,0)) amt"
               " from loan_applications group by a, b order by n desc" % (row_col, col_col))
    else:
        sql = ("select coalesce(nullif(%s,''),'(空)') a, coalesce(nullif(%s,''),'(空)') b,"
               " count(*) n, sum(coalesce(approved_amount,0)) amt"
               " from loan_applications group by a, b order by n desc" % (row_col, col_col))
    rows = [[r[0], r[1], r[2], money(r[3])] for r in q(conn, sql)]
    return ([label_a, label_b, "筆數", "核准額合計"], rows)


def build_source_tables(conn):
    rows = []
    for r in q(conn, """
        select coalesce(nullif(source_tables,''),'(未標註)') v, count(*) n,
               sum(case when orphan_case<>'' and orphan_case is not null then 1 else 0 end) orphan
        from loan_cases group by v order by n desc"""):
        rows.append([r[0], r[1], r[2]])
    return (["案件來源表組合", "案件數", "其中孤兒案件"], rows)


def build_case_link(conn):
    """案件層 ↔ 申請單層：同一案件下各申請單的狀態分歧。"""
    rows = []
    for r in q(conn, """
        select c.case_no, c.app_count, c.code_year,
               coalesce(c.amount_source_flag,'') amt_src,
               coalesce(c.source_tables,'') src,
               coalesce(c.orphan_case,'') orphan,
               count(distinct a.case_status) st_cnt,
               group_concat(distinct coalesce(nullif(a.case_status,''),'(空)')) sts,
               group_concat(distinct coalesce(nullif(a.case_type,''),'(空)')) tys
        from loan_cases c
        left join loan_applications a on a.case_no = c.case_no
        group by c.case_no"""):
        rows.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
    # 摘要：狀態分歧統計
    summary = []
    for r in q(conn, """
        select st_cnt, count(*) n from (
          select c.case_no, count(distinct a.case_status) st_cnt
          from loan_cases c left join loan_applications a on a.case_no=c.case_no
          group by c.case_no) group by st_cnt order by st_cnt"""):
        summary.append([r[0], r[1]])
    return (["案件編號", "申請單數", "年度", "金額來源欄位", "來源表組合", "孤兒標記",
             "狀態碼數", "該案件出現的狀態碼", "該案件出現的類型"], rows), \
           (["同一案件內不同狀態碼的數量", "案件數"], summary)


def main():
    if not os.path.exists(DB):
        print("找不到 DB：%s" % DB, file=sys.stderr)
        return 2
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    os.makedirs(SUB, exist_ok=True)

    sheets = []

    hdr, rows = build_status_dict(conn)
    sheets.append(("狀態代碼字典", hdr, rows))
    write_csv(os.path.join(SUB, "狀態代碼字典.csv"), hdr, rows)

    hdr, rows = build_simple_dict(conn, "case_type", "類型代碼")
    sheets.append(("類型字典", hdr, rows))
    write_csv(os.path.join(SUB, "類型字典.csv"), hdr, rows)

    hdr, rows = build_simple_dict(conn, "customer_group", "客群代碼")
    sheets.append(("客群字典", hdr, rows))
    write_csv(os.path.join(SUB, "客群字典.csv"), hdr, rows)

    hdr, rows = build_cross(conn, "case_status", "code_year", "狀態代碼", "年度")
    sheets.append(("狀態x年度", hdr, rows))
    write_csv(os.path.join(SUB, "狀態x年度.csv"), hdr, rows)

    hdr, rows = build_cross(conn, "case_status", "case_type", "狀態代碼", "類型代碼")
    sheets.append(("狀態x類型", hdr, rows))
    write_csv(os.path.join(SUB, "狀態x類型.csv"), hdr, rows)

    hdr, rows = build_cross(conn, "customer_group", "case_status", "客群代碼", "狀態代碼")
    sheets.append(("客群x狀態", hdr, rows))
    write_csv(os.path.join(SUB, "客群x狀態.csv"), hdr, rows)

    hdr, rows = build_cross(conn, "amount_source", "code_year", "金額來源", "年度")
    sheets.append(("金額來源x年度", hdr, rows))
    write_csv(os.path.join(SUB, "金額來源x年度.csv"), hdr, rows)

    hdr, rows = build_source_tables(conn)
    sheets.append(("案件來源表分布", hdr, rows))
    write_csv(os.path.join(SUB, "案件來源表分布.csv"), hdr, rows)

    (hdr, rows), (hdr2, rows2) = build_case_link(conn)
    sheets.append(("案件層與申請單層對照", hdr, rows))
    write_csv(os.path.join(SUB, "案件層與申請單層對照.csv"), hdr, rows)
    sheets.append(("案件狀態分歧統計", hdr2, rows2))

    # 血緣說明表
    meta = {k: v for k, v in q(conn, "select key, value from loan_meta")}
    prov = [
        ["資料集", meta.get("dataset", "")],
        ["資料集說明", meta.get("dataset_label", "")],
        ["來源主機", meta.get("source_host", "")],
        ["來源目錄", meta.get("source_dir", "")],
        ["來源 XLSX", meta.get("source_xlsx", "")],
        ["來源 XLSX sha256", meta.get("source_xlsx_sha256", "")],
        ["來源 sha256 校驗", meta.get("source_sha256_verified", "")],
        ["匯入時間", meta.get("imported_at", "")],
        ["申請單層筆數", meta.get("rows_loan_applications", "")],
        ["案件層筆數", meta.get("rows_loan_cases", "")],
        ["血統界線", "本檔來自本機既有匯出檔（Desktop/888/case_master_v5_2023_2026），"
                     "非本次線上直拉；sha256 校驗證明「匯入後與來源檔一致」，"
                     "不證明「來源檔本身由本次操作取得」。"],
        ["字典缺口", "APR_CASE_STAT / APR_CASE_TYPE / APR_CUST_LEVEL / C01_CASE_STAT "
                     "的中文名稱，在中租同站點的離線資料中不存在；本檔只填資料可推得特徵。"],
    ]
    sheets.append(("血緣與限制", ["項目", "內容"], prov))

    # ---- XLSX
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment
        from openpyxl.utils import get_column_letter
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for name, header, rows in sheets:
            ws = wb.create_sheet(title=name[:31])
            ws.append(header)
            for c in ws[1]:
                c.font = Font(bold=True)
                c.alignment = Alignment(vertical="center")
            for r in rows:
                ws.append(list(r))
            ws.freeze_panes = "A2"
            for i, _ in enumerate(header, start=1):
                w = 14
                if i <= len(header) and header[i - 1] in ("資料可推得特徵", "中文名稱",
                                                          "血緣界線", "字典缺口",
                                                          "該案件出現的狀態碼"):
                    w = 60
                elif i <= len(header) and header[i - 1] in ("案件編號", "金額來源欄位",
                                                            "來源表組合"):
                    w = 28
                ws.column_dimensions[get_column_letter(i)].width = w
            ws.auto_filter.ref = ws.dimensions
        path = os.path.join(OUT, "貸款案件分類字典.xlsx")
        wb.save(path)
        print("已輸出：%s (%d bytes)" % (path, os.path.getsize(path)))
    except ImportError:
        print("（無 openpyxl，只輸出 CSV）", file=sys.stderr)

    # README
    with open(os.path.join(SUB, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# 貸款案件分類字典\n\n")
        fh.write("- 資料來源：`data/loan_cases.db`（本機既有匯出檔匯入，sha256 57/57 全過）\n")
        fh.write("- 來源主機（標記）：%s\n" % meta.get("source_host", ""))
        fh.write("- **不是**本次線上直拉，見 XLSX「血緣與限制」表\n")
        fh.write("- 狀態／類型／客群的中文名稱在同站點離線資料中不存在，一律標「待補」\n")
        fh.write("- 已完成：狀態×年度、狀態×類型、客群×狀態、金額來源×年度、案件層↔申請單層對照\n")

    print("已輸出到：%s" % SUB)
    for f in sorted(os.listdir(SUB)):
        p = os.path.join(SUB, f)
        print("  %-34s %d bytes" % (f, os.path.getsize(p)))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
