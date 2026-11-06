#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""從中租未脫敏活頁簿抽出「提取母體」：會員號 → 手機號 對照。

輸出 chailease_seeds.json：
  {
    "members": [{"member_no","phone","site_id","channel","business","source_sheet"}],
    "phones": ["0912345678", ...],
    "pool_members": {"0912345678": ["202411270000053", ...]},
    "source": {"file": ..., "sha256": ...}
  }

用法:
  python3 extract_chailease_seeds.py <xlsx> <out.json>
"""
import hashlib
import json
import os
import sys

from openpyxl import load_workbook

XLSX = sys.argv[1]
OUT = sys.argv[2]

wb = load_workbook(XLSX, read_only=True, data_only=True)


def rows_of(name):
    ws = wb[name]
    return list(ws.iter_rows(values_only=True))


def cell(v):
    if v is None:
        return ""
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


members = {}
pool_members = {}
phones = []

# --- 工作表「生產會員號全量」：會員號 → 對應手機號（查詢鍵）------------
for r in rows_of("生產會員號全量")[1:]:
    mno = cell(r[1] if len(r) > 1 else "")
    ph = cell(r[6] if len(r) > 6 else "")
    if not mno:
        continue
    members[mno] = {
        "member_no": mno,
        "phone": ph,
        "site_id": cell(r[2] if len(r) > 2 else ""),
        "channel": cell(r[3] if len(r) > 3 else ""),
        "login_identifier": cell(r[4] if len(r) > 4 else ""),
        "business": cell(r[5] if len(r) > 5 else ""),
        "source_sheet": "生產會員號全量",
    }
    if ph:
        phones.append(ph)

# --- 工作表「會員與簽約合併表」：手機號 → 會員號池 ----------------------
for r in rows_of("會員與簽約合併表")[1:]:
    ph = cell(r[1] if len(r) > 1 else "")
    pool = cell(r[2] if len(r) > 2 else "")
    if not ph or not pool:
        continue
    lst = [x.strip() for x in pool.split(";") if x.strip()]
    pool_members.setdefault(ph, [])
    for m in lst:
        if m not in pool_members[ph]:
            pool_members[ph].append(m)
        if m not in members:
            members[m] = {"member_no": m, "phone": ph, "site_id": "", "channel": "",
                          "login_identifier": "", "business": "",
                          "source_sheet": "會員與簽約合併表"}
    if ph not in phones:
        phones.append(ph)

# 依會員號排序輸出（穩定、可重現）
out_members = [members[k] for k in sorted(members)]
uniq_phones = sorted({p for p in phones if p})

sha = hashlib.sha256(open(XLSX, "rb").read()).hexdigest()
out = {
    "members": out_members,
    "phones": uniq_phones,
    "pool_members": pool_members,
    "source": {"file": os.path.basename(XLSX), "sha256": sha},
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("members      :", len(out_members))
print("phones       :", len(uniq_phones))
print("pool phones  :", len(pool_members))
for ph, lst in pool_members.items():
    print("   %s -> %d 個會員號" % (ph, len(lst)))
print("source sha256:", sha)
print("→", OUT)
