#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""records_export_xlsx.py — 產出「提取記錄總表」xlsx（可重現，支援年份窗口）。

為什麼需要這一支
----------------
既有目錄裡的 JySecAI-提取記錄總表.xlsx 沒有任何腳本在產生（孤兒產物），
而且是 2026-11-06 14:48 的舊檔，仍含年份窗口外的資料，無法重現。
本腳本讓整條流水線可重跑、可稽核。

注意：本檔含**明文**個資（姓名／身分證／電話），是工作用總表，不是對外交付文件。
對外交付請用 records_deliverables.py 產生的雜湊版文件。

用法:
    python3 scripts/records_export_xlsx.py \
        --db /var/lib/jysecai/core/extracted_records.db \
        --out /var/lib/jysecai/core/workspace/reports/records-deliverables/JySecAI-提取記錄總表.xlsx \
        --years 2023-2026
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

import records_deliverables as rd

# 記錄層的固定欄位（放在型別欄位之前）
LEAD_COLS = [("記錄標題", "title"), ("資料集", "dataset"), ("去重鍵", "dedupe_key")]
TAIL_COLS = [("來源", "source"), ("擷取時間", "extracted_at"),
             ("入庫時間", "ingested_at"), ("命中次數", "hit_count")]


def parse_years(spec):
    if not spec.strip():
        return None, None
    import re
    m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", spec)
    if not m:
        raise SystemExit("--years 格式錯誤（應為 YYYY-YYYY）：%s" % spec)
    y0, y1 = int(m.group(1)), int(m.group(2))
    return (y0, y1) if y0 <= y1 else (y1, y0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/var/lib/jysecai/core/extracted_records.db")
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", default="2023-2026")
    ap.add_argument("--max-rows", type=int, default=0,
                    help="每個型別最多輸出幾列（0 = 全部）")
    args = ap.parse_args()

    y0, y1 = parse_years(args.years)

    con = __import__("sqlite3").connect("file:%s?mode=ro" % args.db, uri=True)
    types = rd.load_types(con)
    data = {tid: rd.load_records(con, tid) for tid in types}
    con.close()

    data, year_stats = rd.filter_by_years(data, y0, y1)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "摘要"

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    ws.append(["JySecAI 提取記錄總表"])
    ws["A1"].font = Font(bold=True, size=14)
    for r in ([], ["產出時間", now], ["資料庫", args.db],
              ["年份窗口", args.years if args.years.strip() else "（不過濾）"],
              ["敏感度", "含明文個資（姓名／身分證／電話）— 工作用總表，非對外交付物"],
              [], ["型別", "標籤", "原始筆數", "納入", "排除（年份外）", "無日期", "欄位數"]):
        ws.append(r)
    for tid in sorted(types):
        s = year_stats.get(tid, {})
        ws.append([tid, types[tid]["label"], s.get("total", len(data.get(tid, []))),
                   s.get("kept", len(data.get(tid, []))), s.get("excluded", 0),
                   s.get("undated", 0), len(types[tid]["columns"])])
    ws.append([])
    ws.append(["總納入筆數", sum(len(v) for v in data.values())])

    for tid in sorted(types):
        meta = types[tid]
        recs = data.get(tid) or []
        if not recs:
            continue
        cols = meta["columns"]
        headers = [h for h, _ in LEAD_COLS]
        headers += [c["label"] if isinstance(c, dict) and c.get("label") else str(c)
                    for c in cols]
        headers += [h for h, _ in TAIL_COLS]
        keys = [None] * len(LEAD_COLS)
        keys += [c["key"] if isinstance(c, dict) else str(c) for c in cols]
        keys += [None] * len(TAIL_COLS)

        sh = wb.create_sheet("%s_%s" % (tid, meta["label"])[:31])
        sh.append(headers)
        for c in sh[1]:
            c.font = Font(bold=True)
        limit = args.max_rows if args.max_rows > 0 else len(recs)
        for r in recs[:limit]:
            row = []
            for k in keys:
                if k is None:
                    row.append("")
                elif k == "title":
                    row.append(r["title"])
                elif k == "dataset":
                    row.append(r["dataset"])
                elif k == "dedupe_key":
                    row.append(r["dedupe_key"])
                elif k == "source":
                    row.append(r["source"])
                elif k == "extracted_at":
                    row.append(r["extracted_at"])
                elif k == "ingested_at":
                    row.append(r["ingested_at"])
                elif k == "hit_count":
                    row.append(r["hit_count"])
                else:
                    row.append(r["fields"].get(k, ""))
            sh.append(row)
        sh.freeze_panes = "A2"
        sh.auto_filter.ref = sh.dimensions
        for i, h in enumerate(headers, start=1):
            w = max(10, min(28, len(str(h)) * 2 + 4))
            sh.column_dimensions[get_column_letter(i)].width = w

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    wb.save(args.out)

    import hashlib
    h = hashlib.sha256(open(args.out, "rb").read()).hexdigest()
    with open(args.out + ".sha256", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%s  %s\n" % (h, os.path.basename(args.out)))

    print("總表已產出：%s" % args.out)
    print("  sha256 = %s" % h)
    print("  工作表 = 摘要 + %d 個型別" % (len(data) - sum(1 for v in data.values() if not v)))
    print("  納入筆數 = %d" % sum(len(v) for v in data.values()))
    if y0 is not None:
        exc = sum(s.get("excluded", 0) for s in year_stats.values())
        print("  年份窗口 %d-%d 排除 = %d 筆" % (y0, y1, exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
