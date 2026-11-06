#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_chailease_seeds_v2.py — 從新版中租活頁簿抽母體（4,353 會員 + 22 簽約）

新版活頁簿工作表：
  生產會員全量  會員號 / 站點ID / 渠道名稱 / 會員登入識別碼 / 對應手機號(查詢鍵) / 已開通業務 / 開通業務數
  簽約記錄      手機號 / 會員號池 / 簽約姓名 / 身份證字號 / 車牌號 / 簽約完成 / 簽約完成時間 / 建檔時間

為什麼會員檔沒有姓名
--------------------
`/Member/UserSiteList` 的回應欄位只有 memberNo / siteID / channelName / memberLoginID /
beforeMemberNo —— 沒有姓名欄；且 memberLoginID 4,353 筆全部為空。
所以「會員檔」在來源端就沒有姓名，姓名只存在於 22 筆簽約記錄（9 個唯一姓名），
完整姓名要靠 Oracle `UCAR_CUST_DATA.CUST_NAME`（sqli_pull_scope.py 會取）。

用法:
  python3 extract_chailease_seeds_v2.py <xlsx> <out_seeds.json>
"""
import hashlib
import json
import os
import sys

from openpyxl import load_workbook

XLSX = sys.argv[1]
OUT = sys.argv[2]

wb = load_workbook(XLSX, read_only=True, data_only=True)
names = wb.sheetnames


def find_sheet(*keys):
    for n in names:
        for k in keys:
            if k in n:
                return n
    return None


def cell(v):
    if v is None:
        return ""
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def rows_of(sheet):
    ws = wb[sheet]
    out = list(ws.iter_rows(values_only=True))
    return out[0], out[1:]


# ---------------- 生產會員全量 ----------------
sh_members = find_sheet("生產會員", "生产会员")
hdr, rows = rows_of(sh_members)
idx = {cell(h).strip(): i for i, h in enumerate(hdr)}


def col(*names_):
    for n in names_:
        for k, i in idx.items():
            if n in k:
                return i
    return None


i_mno = col("會員號", "会员号")
i_site = col("站點", "站点", "站台")
i_chan = col("渠道", "channel")
i_login = col("登入識別碼", "登录识别")
i_phone = col("手機號", "手机号", "phone")
i_biz = col("已開通業務", "已开通业务")
i_bizn = col("開通業務數", "开通业务数")

members = []
for r in rows:
    mno = cell(r[i_mno]) if i_mno is not None and i_mno < len(r) else ""
    if not mno:
        continue
    login = cell(r[i_login]) if i_login is not None and i_login < len(r) else ""
    if login in ("(空字串)", "空字串", "(空)", "-"):
        login = ""
    members.append({
        "member_no": mno,
        "phone": cell(r[i_phone]) if i_phone is not None and i_phone < len(r) else "",
        "site_id": cell(r[i_site]) if i_site is not None and i_site < len(r) else "",
        "channel": cell(r[i_chan]) if i_chan is not None and i_chan < len(r) else "",
        "login_identifier": login,
        "business": cell(r[i_biz]) if i_biz is not None and i_biz < len(r) else "",
        "business_count": cell(r[i_bizn]) if i_bizn is not None and i_bizn < len(r) else "",
        "source_sheet": sh_members,
    })

# ---------------- 簽約記錄 ----------------
sh_sign = find_sheet("簽約記錄", "签约记录", "簽約")
sign_rows = []
if sh_sign:
    hdr2, rows2 = rows_of(sh_sign)
    idx2 = {cell(h).strip(): i for i, h in enumerate(hdr2)}

    def col2(*names_):
        for n in names_:
            for k, i in idx2.items():
                if n in k:
                    return i
        return None

    j_phone = col2("手機號", "手机号")
    j_pool = col2("會員號池", "会员号池")
    j_name = col2("簽約姓名", "签约姓名")
    j_id = col2("身份證", "身份证", "身分證")
    j_plate = col2("車牌", "车牌")
    j_done = col2("簽約完成", "签约完成")
    j_time = col2("簽約完成時間", "签约完成时间")
    j_created = col2("建檔時間", "建档时间", "申請")
    for r in rows2:
        ph = cell(r[j_phone]) if j_phone is not None and j_phone < len(r) else ""
        if not ph:
            continue
        sign_rows.append({
            "phone": ph,
            "member_pool": cell(r[j_pool]) if j_pool is not None and j_pool < len(r) else "",
            "sign_name": cell(r[j_name]) if j_name is not None and j_name < len(r) else "",
            "id_number": cell(r[j_id]) if j_id is not None and j_id < len(r) else "",
            "plate": cell(r[j_plate]) if j_plate is not None and j_plate < len(r) else "",
            "sign_done": cell(r[j_done]) if j_done is not None and j_done < len(r) else "",
            "sign_time": cell(r[j_time]) if j_time is not None and j_time < len(r) else "",
            "created_at": cell(r[j_created]) if j_created is not None and j_created < len(r) else "",
        })

phones = sorted({m["phone"] for m in members if m["phone"]})
pool_members = {}
for s in sign_rows:
    lst = [x.strip() for x in s["member_pool"].split(";") if x.strip()]
    pool_members.setdefault(s["phone"], [])
    for m in lst:
        if m not in pool_members[s["phone"]]:
            pool_members[s["phone"]].append(m)

sha = hashlib.sha256(open(XLSX, "rb").read()).hexdigest()
out = {
    "members": sorted(members, key=lambda x: x["member_no"]),
    "phones": phones,
    "pool_members": pool_members,
    "sign_records": sign_rows,
    "source": {"file": os.path.basename(XLSX), "sha256": sha,
               "sheets": names},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("會員（生產全量）：", len(members))
print("查詢鍵手機號數　：", len(phones))
print("簽約記錄　　　　：", len(sign_rows))
print("唯一簽約姓名數　：", len({s["sign_name"] for s in sign_rows if s["sign_name"]}))
print("唯一身分證數　　：", len({s["id_number"] for s in sign_rows if s["id_number"]}))
print("會員號池　　　　：", {k: len(v) for k, v in pool_members.items()})
print("來源 sha256　　 ：", sha)
print("→", OUT)
