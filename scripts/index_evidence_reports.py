#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""掃描 JySecAI 全樹，將漏洞/證據/報告檔案依「專案」分群索引。
排除 skill、node_modules、plugin、cache 等非證據檔。"""
import os, re, datetime

ROOT = r"C:\Users\Administrator\Desktop\JySecAI"
EXCLUDE_DIRS = {
    ".git", "node_modules", "skills", "hack-skills-main", ".codex", ".pytest_cache",
    "__pycache__", "vendor", "third_party", ".idea", ".vscode", "docs", "internal",
    "web", "agents", "tools", "roles", "mcp-servers", "_archive", "tmp", "DesktopDB",
    "reports", "remediation", "patches", "burpbridge", "taiwan-proxy", "PDF",
}
CUTOFF = datetime.datetime(2026, 9, 1)
CUTOFF_TS = CUTOFF.timestamp()
NOW = datetime.datetime.now()

# 專案分群規則：先比對到最專屬的路徑前綴
GROUPS = [
    ("消防署 AUTH-2026-005 (tyfdapp / EPCR / 119 / EMIC)",
     [r"data/recon/tw119_tkp_20261007", r"tpe119_evidence", r"tpe_broadcast",
      r"data/poc_drafts", r"evidence/apityfd", r"evidence/rescueinfo",
      r"evidence/taoyuan-119", r"evidence/kaohsiung_119", r"evidence/yilanfd",
      r"evidence/pt-caseinfo", r"evidence/push-readiness", r"evidence/redmi-rb06",
      r"evidence/gcs-eitsc", r"evidence/fb2cc12b"]),
    ("雪梨大學 AUTH-2026-1005 (sydney.edu.au)",
     [r"tpe119_evidence/sydney", r"tpe119_evidence/coveo", r"tpe119_evidence/SYDNEY",
      r"data/sydney_myuni_api_analysis", r"poc_drafts/Sydney", r"poc_drafts/71465",
      r"poc_drafts/37a2d8fd", r"poc_drafts/PHONEBOOK", r"poc_drafts/4040498e",
      r"poc_drafts/3b250fed", r"poc_drafts/coveo", r"poc_drafts/myuni",
      r"data/poc_drafts/56d7caa8", r"data/poc_drafts/Sydney", r"data/poc_drafts/handlebars",
      r"data/poc_drafts/vuln-2026-10-03"]),
    ("Mordor Intelligence (本次工作)",
     [r"poc_drafts/mordor_iw", r"^poc_drafts/"]),
    ("herun (聯合?) — 逆向工程",
     [r"herun_evidence"]),
    ("金融借貸 recon (18 目標，無授權疑慮)",
     [r"data/poc_drafts/fin-lending-recon", r"okbank_evidence"]),
    ("vps.xs1.ccwu.cc (自有 VPS)",
     [r"evidence/vps\.xs1", r"data/evidence_backup"]),
    ("其他根目錄檔案", [r"^[^/]+\.md$"]),
]

REPORT_HINT = re.compile(
    r"(REPORT|report|報告|漏洞|POC|poc|FINDING|finding|VULN|vuln|證據|evidence|"
    r"VERIFY|verify|复验|複驗|AUDIT|audit)", re.I)

rows = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT).replace("\\", "/")
    dirnames[:] = [d for d in dirnames
                    if d not in EXCLUDE_DIRS and not d.startswith(".") and d != "site-packages"]
    if re.search(r"(skills|node_modules|plugins|_archive|\.git|cache)", rel):
        continue
    for fn in filenames:
        if not fn.lower().endswith((".md", ".json", ".csv", ".xlsx", ".txt")):
            continue
        fpath = os.path.join(dirpath, fn)
        r = os.path.relpath(fpath, ROOT).replace("\\", "/")
        try:
            st = os.stat(fpath)
        except OSError:
            continue
        if st.st_mtime < CUTOFF_TS or not REPORT_HINT.search(r):
            continue
        rows.append((r, st.st_size, datetime.datetime.fromtimestamp(st.st_mtime)))

print(f"掃描完成：{len(rows)} 個證據/報告檔（{CUTOFF.date()} 之後，非 skill/非 plugin）")
print("=" * 78)

assigned = set()
for name, prefixes in GROUPS:
    got = []
    for r, sz, mt in rows:
        if r in assigned: continue
        for p in prefixes:
            if re.search(p, r):
                got.append((r, sz, mt)); assigned.add(r); break
    if not got: continue
    got.sort(key=lambda x: x[2], reverse=True)
    print(f"\n{'='*78}\n■ {name}   ({len(got)} 個檔案)")
    print(f"{'='*78}")
    for r, sz, mt in got[:22]:
        print(f"  {mt:%Y-%m-%d %H:%M}  {sz:>7,}B  {r}")
    if len(got) > 22:
        print(f"  ... 另 {len(got)-22} 個 (共 {len(got)})")

rest = [x for x in rows if x[0] not in assigned]
if rest:
    rest.sort(key=lambda x: x[2], reverse=True)
    print(f"\n{'='*78}\n■ 未歸類 ({len(rest)})")
    print(f"{'='*78}")
    for r, sz, mt in rest[:15]:
        print(f"  {mt:%Y-%m-%d %H:%M}  {sz:>7,}B  {r}")

# 大目錄統計
print(f"\n{'='*78}\n■ 主要證據目錄（含檔案數 / 總大小）")
print(f"{'='*78}")
for d in ["poc_drafts", "data/poc_drafts", "tpe119_evidence", "herun_evidence",
          "evidence", "okbank_evidence", "data/recon", "tpe_broadcast",
          "data/evidence_backup"]:
    full = os.path.join(ROOT, d)
    if not os.path.isdir(full): continue
    n = tot = 0
    for dp, dn, fns in os.walk(full):
        for f in fns:
            n += 1
            try: tot += os.path.getsize(os.path.join(dp, f))
            except OSError: pass
    print(f"  {d:<26} {n:>5} 檔  {tot/1048576:>8.1f} MB")
