#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 chailease_seeds.json 產生可入庫的 payload（不需連網）。

這批資料來自使用者提供的未脫敏活頁簿（生產會員號全量 / 會員與簽約合併表），
不是本次連線抓的；來源與雜湊都寫在 evidence 裡，欄位不做任何推補。

用法:
  python3 build_member_payloads.py chailease_seeds.json <outdir>
"""
import datetime
import hashlib
import json
import os
import sys

SEEDS = sys.argv[1] if len(sys.argv) > 1 else "chailease_seeds.json"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "chailease_payload"

os.makedirs(OUTDIR, exist_ok=True)
seeds = json.load(open(SEEDS, encoding="utf-8"))
members = seeds.get("members") or []
pools = seeds.get("pool_members") or {}
src = seeds.get("source") or {}
now = datetime.datetime.now().isoformat(timespec="seconds")

pool_by_member = {}
for ph, lst in pools.items():
    for mno in lst:
        pool_by_member[mno] = ",".join(sorted(lst))

signup = []
profile = []
for m in members:
    mno = str(m.get("member_no") or "")
    if not mno:
        continue
    ph = str(m.get("phone") or "")
    ev = {"source": "extract_xlsx:%s" % src.get("file", ""),
          "source_sheet": m.get("source_sheet") or "",
          "source_sha256": src.get("sha256", ""),
          "generated_at": now}
    signup.append({
        "key": "%s|%s|%s" % (ph, mno, m.get("site_id") or ""),
        "title": mno[-6:],
        "fields": {"phone": ph, "member_no": mno,
                   "site_id": m.get("site_id") or "",
                   "channel": m.get("channel") or "",
                   "login_identifier": m.get("login_identifier") or "",
                   "business": m.get("business") or ""},
        "evidence": ev,
        "extracted_at": now,
    })
    profile.append({
        "key": mno,
        "title": "會員 %s" % mno[-6:],
        "fields": {"member_no": mno, "phone": ph,
                   "sign_pool": pool_by_member.get(mno, ""),
                   "source_file": src.get("file", "")},
        "evidence": ev,
        "extracted_at": now,
    })


def dump(name, obj):
    p = os.path.join(OUTDIR, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return p


p1 = dump("payload_member_signup.json",
          {"type_id": "member_signup", "dataset": "chailease_prod_members",
           "source": "extract_xlsx:%s" % src.get("file", ""), "records": signup})
p2 = dump("payload_member_profile.json",
          {"type_id": "member_profile", "dataset": "chailease_prod_members",
           "source": "extract_xlsx:%s" % src.get("file", ""), "records": profile})

with open(os.path.join(OUTDIR, "SHA256SUMS"), "w", encoding="utf-8") as f:
    for name in sorted(os.listdir(OUTDIR)):
        if name == "SHA256SUMS":
            continue
        p = os.path.join(OUTDIR, name)
        f.write("%s  %s\n" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))

print("member_signup records :", len(signup))
print("member_profile records:", len(profile))
print("pool members          :", len(pool_by_member))
print("→", p1)
print("→", p2)
