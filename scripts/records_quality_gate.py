#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""records_quality_gate.py — 記錄庫資料品質閘門。

為什麼需要這一支
----------------
原本的 verify_release.sh 只檢查「去重 0 筆重複」「有資料型別 N 個」，
這兩件事都跟欄位有沒有值無關。實測發現：
  * member_profile 4353 筆的 name / id_number / address 全部不存在
  * loan_case 5713 筆的 address 只有 1 筆有值
  * 「描述」在業務型別裡沒有對應欄位
這些缺口在舊閘門下完全不會被發現。

三層設計
--------
  1. 回歸門檻（REGRESSION_THRESHOLDS）：現在就達標、往後不可退步的欄位。
     這些會阻擋發佈（verify_release.sh 預設走這層）。
  2. 需求門檻（REQUIREMENT_THRESHOLDS）：使用者明確要求的欄位
     （姓名/電話/描述/地址/身份證/貸款日期）在各業務型別的目標涵蓋率。
     目前尚未達成 —— 預設只報「需求未達成」，加 --strict 才阻擋。
  3. 年份窗口（--years）：只檢視指定年份區間，回報被排除筆數。

用法:
    python3 scripts/records_quality_gate.py --db <db> --years 2023-2026
    python3 scripts/records_quality_gate.py --db <db> --strict     # 需求未達成也 FAIL
    python3 scripts/records_quality_gate.py --db <db> --json
退出碼：0 = 通過；1 = 有項目未達標；2 = 執行錯誤
"""
import argparse
import json
import os
import re
import sqlite3
import sys

# 每個型別的日期欄位候選（依優先序），用來套用年份窗口。
DATE_FIELDS = {
    "loan_application": ["apply_at", "apply_year", "first_apply_at"],
    "loan_case": ["apply_date"],
    "loan_case_master": ["first_apply_at", "code_year"],
    "member_profile": ["sign_time", "created_at"],
    "member_signup": ["sign_time", "created_at", "apply_at"],
    "vulnerability": ["discovered_at"],
}

# 欄位別名：需求欄位 -> 可接受的實際欄位名（依優先序）
FIELD_ALIASES = {
    "姓名": ["name", "cust_name", "sign_name", "contact_name"],
    "電話": ["phone", "mobile", "landline", "company_phone", "contact_phone",
             "guarantor_phone", "guarantor2_phone"],
    "描述": ["description", "note", "detail", "remark", "value"],
    "地址": ["address", "county", "district", "city"],
    "身份證": ["id_number", "cust_id_no", "guarantor_id", "guarantor2_id",
               "company_tax_id"],
    "貸款日期": ["apply_date", "apply_at", "first_apply_at", "last_apply_at",
                 "sign_time", "created_at"],
}

# ---------------------------------------------------------------------------
# 第 1 層：回歸門檻（現在就達標；掉了就阻擋發佈）
# ---------------------------------------------------------------------------
REGRESSION_THRESHOLDS = {
    "loan_case": {
        "name": 0.95, "id_number": 0.95, "mobile": 0.90, "apply_date": 0.95,
    },
    "member_profile": {"phone": 0.95, "member_no": 0.99},
    "member_signup": {"phone": 0.90, "id_number": 0.90},
    "loan_application": {"apply_at": 0.85, "app_no": 0.85},
    "loan_case_master": {"code_year": 0.90, "case_no": 0.95},
    "generic": {"note": 0.90},
}

# ---------------------------------------------------------------------------
# 第 2 層：需求門檻（使用者明確要求的六個欄位；尚未達成，--strict 才阻擋）
# ---------------------------------------------------------------------------
REQUIREMENT_THRESHOLDS = {
    "loan_case": {
        "姓名": 0.95, "電話": 0.90, "描述": 0.50, "地址": 0.50,
        "身份證": 0.95, "貸款日期": 0.95,
    },
    "member_profile": {
        "姓名": 0.80, "電話": 0.95, "描述": 0.50, "地址": 0.50,
        "身份證": 0.80, "貸款日期": 0.50,
    },
    "member_signup": {
        "姓名": 0.90, "電話": 0.90, "身份證": 0.90, "貸款日期": 0.90,
    },
    "loan_application": {"貸款日期": 0.85},
    "loan_case_master": {"貸款日期": 0.85},
}

YEAR_RE = re.compile(r"(19|20)\d{2}")


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def year_of(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 1900 <= value <= 2100:
            return int(value)
        return None
    m = YEAR_RE.search(str(value))
    return int(m.group(0)) if m else None


def resolve(rates, aliases):
    """在實際欄位中找出別名對應到的欄位，回傳 (欄位名, 非空率) 或 (None, 0)。"""
    best = (None, 0.0)
    for a in aliases:
        if a in rates and rates[a] > best[1]:
            best = (a, rates[a])
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/var/lib/jysecai/core/extracted_records.db")
    ap.add_argument("--years", default="2023-2026",
                    help="年份窗口，例如 2023-2026；空字串代表不過濾")
    ap.add_argument("--json", action="store_true", help="額外輸出 JSON 結果")
    ap.add_argument("--strict", action="store_true",
                    help="需求門檻未達成也判定為 FAIL")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print("[abort] 找不到記錄庫：%s" % args.db, file=sys.stderr)
        return 2

    y0 = y1 = None
    if args.years.strip():
        m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", args.years)
        if not m:
            print("[abort] --years 格式錯誤（應為 YYYY-YYYY）：%s" % args.years,
                  file=sys.stderr)
            return 2
        y0, y1 = int(m.group(1)), int(m.group(2))
        if y0 > y1:
            y0, y1 = y1, y0

    con = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    cur = con.cursor()

    type_meta = {}
    for tid, label, cols in cur.execute(
            "SELECT type_id,label,columns_json FROM record_types"):
        try:
            c = json.loads(cols)
        except Exception:
            c = []
        names = []
        for x in c:
            if isinstance(x, str):
                names.append(x)
            elif isinstance(x, dict):
                n = x.get("key") or x.get("name") or x.get("label")
                if n:
                    names.append(n)
        type_meta[tid] = {"label": label, "columns": names}

    failures = []      # 回歸門檻未達標 → 阻擋
    unmet = []         # 需求門檻未達成 → 預設僅報告，--strict 時併入 failures
    per_type = {}

    for tid, meta in sorted(type_meta.items()):
        rows = cur.execute(
            "SELECT fields_json FROM records WHERE type_id=?", (tid,)).fetchall()

        kept = excluded = undated = scanned = 0
        have = {}
        date_field = None

        for (fj,) in rows:
            try:
                d = json.loads(fj or "{}")
            except Exception:
                d = {}
            if not isinstance(d, dict):
                d = {}

            if y0 is not None:
                if date_field is None:
                    for cand in DATE_FIELDS.get(tid, []):
                        if cand in d:
                            date_field = cand
                            break
                y = year_of(d.get(date_field)) if date_field else None
                if y is None:
                    undated += 1
                elif not (y0 <= y <= y1):
                    excluded += 1
                    continue

            kept += 1
            scanned += 1
            for k, v in d.items():
                if k not in have:
                    have[k] = 0
                if nonempty(v):
                    have[k] += 1

        rates = {k: (h / scanned if scanned else 0.0) for k, h in have.items()}
        per_type[tid] = {
            "label": meta["label"], "total": len(rows), "kept": kept,
            "excluded_out_of_window": excluded, "undated": undated,
            "date_field": date_field,
            "rates": {k: round(v, 4) for k, v in rates.items()},
        }

        # 第 1 層：回歸門檻
        for field, need in (REGRESSION_THRESHOLDS.get(tid) or {}).items():
            got = rates.get(field)
            if got is None:
                failures.append("%s.%s：型別內查無此欄位（回歸門檻要求存在）" % (tid, field))
            elif got < need:
                failures.append("%s.%s 填值率 %.1f%% < 回歸門檻 %.0f%%"
                                % (tid, field, got * 100, need * 100))

        # 第 2 層：需求門檻
        for label, need in (REQUIREMENT_THRESHOLDS.get(tid) or {}).items():
            fname, got = resolve(rates, FIELD_ALIASES[label])
            if fname is None:
                unmet.append("%s / %s：此型別沒有對應欄位（需求 %.0f%%）"
                             % (meta["label"], label, need * 100))
            elif got < need:
                unmet.append("%s / %s（%s）填值率 %.1f%% < 需求 %.0f%%"
                             % (meta["label"], label, fname, got * 100, need * 100))

    con.close()

    # ---------------- 報告 ----------------
    print("=" * 78)
    print("記錄庫資料品質閘門")
    print("資料庫：%s" % args.db)
    print("年份窗口：%s" % (args.years if args.years.strip() else "（不過濾）"))
    print("模式：%s" % ("嚴格（需求未達成也阻擋）" if args.strict else "標準（需求僅報告）"))
    print("=" * 78)

    print()
    print("■ 各型別：筆數 / 年份窗口 / 日期欄位")
    for tid, info in per_type.items():
        print("  %-18s %-12s 總 %6d ｜ 納入 %6d ｜ 排除 %5d ｜ 無日期 %5d ｜ 日期欄位=%s"
              % (tid, info["label"], info["total"], info["kept"],
                 info["excluded_out_of_window"], info["undated"],
                 info["date_field"] or "-"))

    print()
    print("■ 需求欄位覆蓋（使用者指定：姓名／電話／描述／地址／身份證／貸款日期）")
    for tid, reqs in REQUIREMENT_THRESHOLDS.items():
        info = per_type.get(tid)
        if not info or info["kept"] == 0:
            continue
        rates = info["rates"]
        parts = []
        for label, need in reqs.items():
            fname, got = resolve(rates, FIELD_ALIASES[label])
            mark = "✓" if got >= need else "✗"
            shown = fname if fname else "（無）"
            parts.append("%s %s %s %.0f%%/需%.0f%%"
                         % (mark, label, shown, got * 100, need * 100))
        print("  %-12s %s" % (info["label"], " ｜ ".join(parts)))

    print()
    if unmet:
        print("■ 需求未達成（來源本身沒有該欄位，不是抽取器漏映射）")
        for u in unmet:
            print("  ✗ %s" % u)
        print()

    print("■ 判定")
    if args.strict:
        failures = failures + unmet
    if failures:
        for f in failures:
            print("  ✗ FAIL  %s" % f)
        print("  結果：不通過（%d 項）" % len(failures))
    else:
        print("  ✓ 回歸門檻全部達標")
        if unmet and not args.strict:
            print("  （另有 %d 項需求未達成，未阻擋；要阻擋請加 --strict）" % len(unmet))

    if args.json:
        print()
        print(json.dumps({
            "db": args.db, "years": args.years, "strict": args.strict,
            "per_type": per_type, "failures": failures, "unmet_requirements": unmet,
            "passed": not failures,
        }, ensure_ascii=False, indent=2))

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
