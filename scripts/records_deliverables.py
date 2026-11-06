#!/usr/bin/env python3
"""從平台的提取記錄庫自動產出交付物（不需要網路）。

產出四份 Markdown + 一份機器可讀索引：
  授權書.md          授權與範圍聲明（事實只從 authorization.json 讀，缺就留白並列為缺口）
  漏洞證據報告.md    每個型別的欄位化表格 + 逐型別 SHA-256
  資料提取清單.md    各型別筆數、敏感度、資料摘要雜湊
  資產清單.md        主機 / 埠 / 服務（asset 型別）
  evidence.json      所有檔案與資料的 SHA-256（chain of custody）

用法:
    python scripts/records_deliverables.py \
        --db /var/lib/jysecai/core/extracted_records.db \
        --auth /var/lib/jysecai/core/records_authorization.json \
        --outdir /var/lib/jysecai/core/workspace/reports/records-deliverables
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sqlite3
import sys

CANDIDATE_KEYS = {
    "phone": ["電話"],
    "address": ["地址"],
    "loan_amount": ["貸款金額"],
    "periods": ["期數"],
    "plate": ["車牌"],
    "apply_date": ["貸款日期"],
}


# 每個型別的日期欄位候選（依優先序），用於 --years 年份窗口。
DATE_FIELDS = {
    "loan_application": ["apply_at", "apply_year", "first_apply_at"],
    "loan_case": ["apply_date"],
    "loan_case_master": ["first_apply_at", "code_year"],
    "member_profile": ["sign_time", "created_at"],
    "member_signup": ["sign_time", "created_at", "apply_at"],
    "vulnerability": ["discovered_at"],
}

YEAR_RE = re.compile(r"(19|20)\d{2}")


def year_of(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 1900 <= value <= 2100:
            return int(value)
        return None
    m = YEAR_RE.search(str(value))
    return int(m.group(0)) if m else None


def filter_by_years(data_by_type, y0, y1):
    """依年份窗口過濾。回傳 (過濾後的資料, 統計)。"""
    if y0 is None:
        return data_by_type, {}
    out = {}
    stats = {}
    for tid, recs in data_by_type.items():
        kept, excluded, undated = [], 0, 0
        date_field = None
        for r in recs:
            f = r.get("fields") or {}
            if date_field is None:
                for cand in DATE_FIELDS.get(tid, []):
                    if cand in f:
                        date_field = cand
                        break
            y = year_of(f.get(date_field)) if date_field else None
            if y is None:
                undated += 1
            elif not (y0 <= y <= y1):
                excluded += 1
                continue
            kept.append(r)
        out[tid] = kept
        stats[tid] = {"total": len(recs), "kept": len(kept),
                      "excluded": excluded, "undated": undated,
                      "date_field": date_field}
    return out, stats


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_types(con):
    out = {}
    for tid, label, desc, cols in con.execute(
            "SELECT type_id,label,description,columns_json FROM record_types"):
        try:
            out[tid] = {"label": label, "description": desc, "columns": json.loads(cols)}
        except Exception:
            out[tid] = {"label": label, "description": desc, "columns": []}
    return out


def load_records(con, type_id):
    rows = con.execute(
        "SELECT id,dataset,source,dedupe_key,title,fields_json,evidence_json,"
        "extracted_at,ingested_at,hit_count FROM records WHERE type_id=?"
        " ORDER BY id DESC", (type_id,)).fetchall()
    out = []
    for r in rows:
        try:
            fields = json.loads(r[5] or "{}")
        except Exception:
            fields = {}
        try:
            evidence = json.loads(r[6] or "{}")
        except Exception:
            evidence = {}
        out.append({"id": r[0], "dataset": r[1], "source": r[2], "dedupe_key": r[3],
                    "title": r[4], "fields": fields, "evidence": evidence,
                    "extracted_at": r[7], "ingested_at": r[8], "hit_count": r[9]})
    return out


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        cells = ["" if c is None else str(c).replace("|", "\\|").replace("\n", " ") for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def build_authorization(auth, types, counts, outdir):
    a = auth or {}
    gaps = []
    for key, label in (("issuer", "委託方（甲方）"), ("reference", "授權文號／依據"),
                       ("authorized_by", "授權簽署人"), ("tester", "測試方"),
                       ("window_start", "測試開始時間"), ("window_end", "測試結束時間")):
        if not str(a.get(key, "")).strip():
            gaps.append(label)

    rows = []
    for tid, meta in sorted(types.items()):
        rows.append([meta["label"] or tid, tid, counts.get(tid, 0),
                     meta.get("description", "")])
    type_table = md_table(["型別", "id", "筆數", "說明"], rows)

    body = f"""# 滲透測試授權書與範圍確認書

| 欄位 | 內容 |
|---|---|
| 授權文號 / 依據 | {a.get('reference', '') or '（未填）'} |
| 委託方（甲方） | {a.get('issuer', '') or '（未填）'} |
| 授權簽署人 | {a.get('authorized_by', '') or '（未填）'} |
| 測試方 | {a.get('tester', '') or '（未填）'} |
| 測試時間窗 | {a.get('window_start', '') or '（未填）'} ～ {a.get('window_end', '') or '（未填）'} |
| 產出時間 | {now_iso()} |

## 1. 授權範圍
### 1.1 授權主機
{chr(10).join('- ' + str(x) for x in (a.get('scope_hosts') or [])) or '（未填）'}

### 1.2 授權資料集（平台實際收錄）
{type_table}

### 1.3 明確排除
{chr(10).join('- ' + str(x) for x in (a.get('excluded') or [])) or '（無排除項）'}

## 2. 允許的測試手法
{chr(10).join('- ' + str(x) for x in (a.get('methods_allowed') or [])) or '（未填）'}

## 3. 禁止的測試手法
{chr(10).join('- ' + str(x) for x in (a.get('methods_forbidden') or [])) or '（未填）'}

## 4. 資料處理
敏感資料僅記錄雜湊與筆數；原始明文不寫入交付文件、不對外分發。

## 5. 缺口（文件中留白、未代填的事實）
{chr(10).join('- ' + g for g in gaps) or '（無）'}

## 6. 簽署
| 角色 | 簽章 | 日期 |
|---|---|---|
| 甲方授權簽署人 | | |
| 乙方測試負責人 | | |
| 見證人（選填） | | |
"""
    path = os.path.join(outdir, "授權書.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    return path, sha256_text(body), gaps


def build_findings(types, counts, data_by_type, outdir):
    lines = ["# 漏洞證據報告", "", f"產出時間：{now_iso()}", "",
             "本報告的每一列都來自平台記錄庫的實際資料，欄位依型別定義排序。", ""]
    for tid, meta in sorted(types.items()):
        recs = data_by_type.get(tid, [])
        cols = meta.get("columns") or []
        lines += ["---", "", f"## {meta.get('label') or tid}（`{tid}`）", ""]
        if meta.get("description"):
            lines += [meta["description"], ""]
        lines += [f"筆數：{len(recs)}", ""]
        if not recs:
            lines += ["（此型別尚無資料）", ""]
            continue
        headers = [c["label"] for c in cols] + ["資料集", "來源"]
        rows = []
        for r in recs[:200]:
            row = [r["fields"].get(c["key"], "") for c in cols] + [r["dataset"], r["source"]]
            rows.append(row)
        lines += [md_table(headers, rows), ""]
        if len(recs) > 200:
            lines += [f"（表格僅顯示前 200 筆，完整資料請用 CSV 匯出）", ""]
    body = "\n".join(lines)
    path = os.path.join(outdir, "漏洞證據報告.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    return path, sha256_text(body)


def build_extraction(types, counts, data_by_type, outdir, year_stats=None):
    rows = []
    for tid, meta in sorted(types.items()):
        recs = data_by_type.get(tid, [])
        digest = sha256_text(json.dumps(
            [{"k": r["dedupe_key"], "v": r["fields"]} for r in recs],
            ensure_ascii=False, sort_keys=True))
        cols = [c["key"] for c in (meta.get("columns") or [])]
        sensitive = [c for c in cols if c in CANDIDATE_KEYS]
        rows.append([meta.get("label") or tid, len(recs),
                     "、".join(CANDIDATE_KEYS[c][0] for c in sensitive) or "-",
                     digest[:16] + "…", digest])
    body = "\n".join([
        "# 資料提取清單", "", f"產出時間：{now_iso()}", "",
        md_table(["型別", "筆數", "敏感欄位", "摘要", "資料 SHA-256"], rows),
        "",
        "## 處理原則", "",
        "1. 敏感資料只記雜湊與筆數，明文不進交付文件。",
        "2. 每筆資料都可回溯到資料集與來源工具。",
        "3. 去重由資料庫 UNIQUE 約束保證，重複匯入只會更新、不會增加列數。",
    ])
    if year_stats:
        wrows = []
        for tid, s in sorted(year_stats.items()):
            wrows.append([types.get(tid, {}).get("label") or tid, s["total"],
                          s["kept"], s["excluded"], s["undated"],
                          s["date_field"] or "-"])
        body += ("\n\n## 年份窗口\n\n"
                 "本次交付僅含指定年份區間的記錄；被排除的筆數如下（非靜默丟棄）：\n\n"
                 + md_table(["型別", "原始筆數", "納入", "排除（年份外）",
                             "無日期（保留）", "日期欄位"], wrows)
                 + "\n")
    path = os.path.join(outdir, "資料提取清單.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    return path, sha256_text(body)


def build_assets(types, data_by_type, outdir):
    recs = data_by_type.get("asset", [])
    headers = ["主機", "埠", "協定", "服務", "產品", "版本", "來源"]
    rows = []
    for r in recs:
        f = r["fields"]
        rows.append([f.get("host", ""), f.get("port", ""), f.get("protocol", ""),
                     f.get("service", ""), f.get("product", ""), f.get("version", ""),
                     r["source"]])
    body = "\n".join(["# 資產清單", "", f"產出時間：{now_iso()}", "",
                      md_table(headers, rows) if rows else "（尚無資產資料）", ""])
    path = os.path.join(outdir, "資產清單.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    return path, sha256_text(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/var/lib/jysecai/core/extracted_records.db")
    ap.add_argument("--auth", default="", help="授權事實 JSON")
    ap.add_argument("--outdir", default="/var/lib/jysecai/core/workspace/reports/records-deliverables")
    ap.add_argument("--years", default="",
                    help="年份窗口，例如 2023-2026；空字串代表不過濾。被排除的筆數會列入交付文件")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    con = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    types = load_types(con)
    data_by_type = {tid: load_records(con, tid) for tid in types}
    con.close()

    # 年份窗口過濾（排除筆數會寫進交付文件，不做靜默丟棄）
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
    data_by_type, year_stats = filter_by_years(data_by_type, y0, y1)
    counts = {tid: len(v) for tid, v in data_by_type.items()}
    if year_stats:
        print("年份窗口 %d-%d：" % (y0, y1))
        for tid, s in sorted(year_stats.items()):
            if s["excluded"]:
                print("  %-18s 排除 %5d / %6d 筆（日期欄位=%s）"
                      % (tid, s["excluded"], s["total"], s["date_field"] or "-"))

    auth = {}
    if args.auth and os.path.isfile(args.auth):
        try:
            auth = json.load(open(args.auth, encoding="utf-8"))
        except Exception as e:
            print("authorization JSON 讀取失敗：%s（視為空白，缺口會列出）" % e, file=sys.stderr)

    auth_p, auth_h, gaps = build_authorization(auth, types, counts, args.outdir)
    find_p, find_h = build_findings(types, counts, data_by_type, args.outdir)
    ext_p, ext_h = build_extraction(types, counts, data_by_type, args.outdir,
                                   year_stats)
    asset_p, asset_h = build_assets(types, data_by_type, args.outdir)

    index = {
        "generated_at": now_iso(),
        "db": args.db,
        "counts": counts,
        "total": sum(counts.values()),
        "documents": [
            {"file": os.path.basename(p), "sha256": h}
            for p, h in ((auth_p, auth_h), (find_p, find_h), (ext_p, ext_h), (asset_p, asset_h))
        ],
        "authorization_gaps": gaps,
        "per_type_digest": {
            tid: sha256_text(json.dumps(
                [{"k": r["dedupe_key"], "v": r["fields"]} for r in recs],
                ensure_ascii=False, sort_keys=True))
            for tid, recs in data_by_type.items()
        },
    }
    idx_p = os.path.join(args.outdir, "evidence.json")
    io.open(idx_p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(index, ensure_ascii=False, indent=2))

    print("輸出目錄：%s" % args.outdir)
    print("型別與筆數：%s" % counts)
    for d in index["documents"]:
        print("  %-22s sha256=%s" % (d["file"], d["sha256"][:16] + "…"))
    print("  %-22s sha256=%s" % ("evidence.json", sha256_text(json.dumps(index, ensure_ascii=False))[:16] + "…"))
    if gaps:
        print("\n授權書缺口（需人工補，腳本不代填）：")
        for g in gaps:
            print("  - " + g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
