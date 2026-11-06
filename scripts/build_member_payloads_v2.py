#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_member_payloads_v2.py — 產生可入庫 payload（去重鍵與 Go 端正規化規則一致）

去重鍵規則（必須與 internal/records/records.go 的 normalizeValue 完全一致）
--------------------------------------------------------------------------
phone : 只保留數字；長度>9 且開頭為 0 → 去前導 0
alnum : 移除非 [0-9a-zA-ZÀ-ỹ] 字元並轉小寫
text  : 轉小寫並把連續空白壓成單一空白

型別歸屬（依去重欄位的語意決定，不硬塞）
--------------------------------------
member_profile (去重鍵 member_no)
    生產會員全量 4,353 筆：會員號唯一 → 放這裡。
    欄位：member_no / phone（查詢鍵）/ site_id / channel / business / business_count /
          login_identifier / sign_pool / source_file
member_signup  (去重鍵 phone|id_number|sign_time)
    簽約記錄 22 筆：同一支手機號可對多個會員號，不能塞進以 member_no 為鍵的型別。

用法:
  python3 build_member_payloads_v2.py <seeds.json> <outdir>
"""
import datetime
import hashlib
import json
import os
import re
import sys

SEEDS = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

NON_ALNUM = re.compile(r"[^0-9a-zA-ZÀ-ỹ]+")


def norm_phone(v):
    out = "".join(ch for ch in str(v or "").strip() if ch.isdigit())
    if len(out) > 9 and out.startswith("0"):
        out = out.lstrip("0")
    return out


def norm_alnum(v):
    return NON_ALNUM.sub("", str(v or "").strip()).lower()


def norm_text(v):
    return " ".join(str(v or "").strip().split()).lower()


def signup_key(phone, id_number, sign_time):
    """與 Go DedupeKey(member_signup) 完全一致。"""
    return "%s|%s|%s" % (norm_phone(phone), norm_alnum(id_number), norm_text(sign_time))


seeds = json.load(open(SEEDS, encoding="utf-8"))
members = seeds.get("members") or []
sign_rows = seeds.get("sign_records") or []
pools = seeds.get("pool_members") or {}
src = seeds.get("source") or {}
now = datetime.datetime.now().isoformat(timespec="seconds")

pool_by_member = {}
for ph, lst in pools.items():
    for mno in lst:
        pool_by_member[mno] = ",".join(sorted(lst))

ev_base = {"source": "extract_xlsx:%s" % src.get("file", ""),
           "source_sha256": src.get("sha256", ""),
           "generated_at": now}

# ---------------- member_profile：生產會員全量 ----------------
profile = []
for m in members:
    mno = m.get("member_no") or ""
    if not mno:
        continue
    profile.append({
        "key": mno,
        "title": "會員 %s" % mno[-6:],
        "fields": {
            "member_no": mno,
            "phone": m.get("phone") or "",
            "site_id": m.get("site_id") or "",
            "channel": m.get("channel") or "",
            "business": m.get("business") or "",
            "business_count": m.get("business_count") or "",
            "login_identifier": m.get("login_identifier") or "",
            "sign_pool": pool_by_member.get(mno, ""),
            "source_file": src.get("file", ""),
        },
        "evidence": dict(ev_base, source_sheet=m.get("source_sheet") or ""),
        "extracted_at": now,
    })

# ---------------- member_signup：簽約記錄 ----------------
signup = []
for s in sign_rows:
    ph = s.get("phone") or ""
    idn = s.get("id_number") or ""
    st = s.get("sign_time") or ""
    signup.append({
        "key": signup_key(ph, idn, st),
        "title": s.get("sign_name") or (idn[-6:] if idn else ph),
        "fields": {
            "phone": ph,
            "member_no": s.get("member_pool") or "",
            "site_id": "AP-MemberCenter / ZEROCARD_APP",
            "channel": "中租會員中心",
            "login_identifier": "",
            "sign_name": s.get("sign_name") or "",
            "id_number": idn,
            "plate": s.get("plate") or "",
            "sign_done": s.get("sign_done") or "",
            "sign_time": st,
            "created_at": s.get("created_at") or "",
            "business": "",
        },
        "evidence": dict(ev_base, source_sheet="簽約記錄",
                         note="同一手機號對多個會員號，member_no 欄為會員號池（非一對一）"),
        "extracted_at": now,
    })


def dump(name, obj):
    p = os.path.join(OUTDIR, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return p


p1 = dump("payload_member_profile.json",
          {"type_id": "member_profile", "dataset": "chailease_prod_members",
           "source": "extract_xlsx:%s" % src.get("file", ""), "records": profile})
p2 = dump("payload_member_signup.json",
          {"type_id": "member_signup", "dataset": "chailease_member_signup",
           "source": "extract_xlsx:%s" % src.get("file", ""), "records": signup})

with open(os.path.join(OUTDIR, "SHA256SUMS"), "w", encoding="utf-8") as f:
    for name in sorted(os.listdir(OUTDIR)):
        if name == "SHA256SUMS":
            continue
        p = os.path.join(OUTDIR, name)
        f.write("%s  %s\n" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), name))

print("member_profile records :", len(profile))
print("member_signup  records :", len(signup))
print("唯一會員號             :", len({r["key"] for r in profile}))
print("唯一簽約去重鍵         :", len({r["key"] for r in signup}))
print("範例簽約去重鍵         :", signup[0]["key"] if signup else "-")
print("→", p1)
print("→", p2)
