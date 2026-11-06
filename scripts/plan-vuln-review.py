#!/usr/bin/env python3
"""把待處理的漏洞紀錄分流成「可審查批次」，避免把無法審查的紀錄灌進對話。

為什麼需要這支
  待處理量看起來很大（688 筆，651 筆 open），但其中：
    - target 為空者無法判定適用性與嚴重度
    - type 是 finding / target / note / configuration / exploit 者是產出端髒值，不是漏洞類型
    - 同一 (站點, 類型) 常有數十筆重複
  把這些直接送進對話審查，Agent 的 token 會花在無法判定的資料上。
  本工具先分流、去重、分級，再輸出每批可直接貼進對話的審查指令。

只讀保證
  只呼叫 GET 端點，不會修改任何漏洞狀態、證據或 POC。
  去重只影響「批次分組」，不會刪除或合併任何資料庫紀錄。

已知限制（後端曾有 bug，已修；本工具保留落差偵測當回歸警報）
  過去 /api/vulnerabilities 的 SELECT 在 GetVulnerability 與 ListVulnerabilitiesForAccess
  各寫一份，兩份都漏了 7 個欄位（description / conversation_tag / task_tag /
  vulnerability_type / target / impact / recommendation）的 COALESCE。這些欄位為 NULL 時
  Go 的 rows.Scan 會失敗，internal/database/vulnerability.go:389 當時用 `continue`
  把整筆靜默丟棄，只留一行 Warn —— 實測 651 筆 open 只回 109 筆（83.3% 靜默消失），
  GetVulnerability 更直接讓 web UI 顯示「漏洞不存在」。

  現況：欄位清單已統一成帶 COALESCE 的 vulnerabilitySelectColumns 常數
  （internal/database/vulnerability.go:392-401），兩處不可能再各漏一次；
  掃描失敗也從「只記 Warn」改成記 Error 並帶上 skipped / returned 筆數
  （internal/database/vulnerability.go:482-488），靜默蒸發在 log 裡看得到。

  本工具仍會比對 API 回報的 total 與實際抓到的筆數：落差現在代表後端又出現了同類
  欄位／掃描問題（或其他過濾條件），值得追，但不該被當成「已審完」。

用法
  # 產生審查計畫（唯讀）
  python3 plan-vuln-review.py --token '<token>'
  # 指定每批筆數
  python3 plan-vuln-review.py --token '<token>' --batch-size 20
  # 連不可審的紀錄一起排批次（預設不排）
  python3 plan-vuln-review.py --token '<token>' --include-dirty
  # 匯出完整明細 CSV 供人工複核
  python3 plan-vuln-review.py --token '<token>' --csv /tmp/vuln-review.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

from jysecai_config import DEFAULT_CONFIG, FALLBACK_BASE_URL, default_base_url

# 明確不是漏洞類型的 type 值（產出端髒值）
NOTE_TYPES = {"finding", "target", "note", "configuration", "exploit", "null", "none", ""}
# 欄位外洩的痕徵：confidence 被寫進 type
CONFIDENCE_RE = re.compile(r"(?i)confidence\s*[.:=]?\s*0?\.\d+")

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEVERITY_ZH = {"critical": "嚴重", "high": "高", "medium": "中", "low": "低", "info": "資訊"}


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def api(base: str, path: str, token: str, params: dict | None = None, timeout: int = 30):
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        die(f"GET {path} 失敗 HTTP {e.code}：{e.read().decode('utf-8','replace')[:200]}")
    except Exception as e:  # noqa: BLE001
        die(f"無法連線 {url}：{e}")


def norm_origin(target: str) -> str:
    """正規化成 origin。刻意保留 port —— 不同 port 是不同服務，不可合併。"""
    t = (target or "").strip()
    if not t:
        return ""
    t = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", t)
    t = t.split("/")[0]
    t = t.split("?")[0].rstrip(".")
    return t.lower()


def vtype(v: dict) -> str:
    """取漏洞類型。

    注意：API 回傳的欄位名是 "type" 不是 "vulnerability_type"
    （internal/database/vulnerability.go:217 的 struct tag 是 `json:"type"`）。
    兩個都試，舊版 API 或直接讀 DB 才相容。
    """
    return str(v.get("type") or v.get("vulnerability_type") or "").strip()


def classify(v: dict) -> tuple[str, str]:
    """回傳 (分組, 原因)。分組：reviewable / no-target / not-a-vuln / dirty-type"""
    typ = vtype(v)
    tgt = str(v.get("target") or "").strip()
    if CONFIDENCE_RE.search(typ):
        return "dirty-type", f"type 欄位混入 confidence 值：{typ[:40]}"
    if typ.lower() in NOTE_TYPES:
        return "not-a-vuln", f"type={typ or '(空)'} 是產出端髒值，不是漏洞類型"
    if not tgt:
        return "no-target", "target 為空，無法判定適用性與嚴重度"
    return "reviewable", ""


def emit_batch(batch: list, idx: int, total_batches: int, max_chars: int):
    """輸出單一批次的完整內容，供直接貼進對話審查。"""
    def field(v, key):
        s = str(v.get(key) or "").strip()
        if len(s) > max_chars:
            return s[:max_chars] + f" …（已截斷，原始 {len(s)} 字）"
        return s or "（無）"

    print("\n" + "=" * 72)
    print(f"第 {idx}/{total_batches} 批，共 {len(batch)} 筆。以下內容可直接貼進對話。")
    print("=" * 72)
    print("""
請審查以下漏洞紀錄。對每一筆給出：
  1. 這是不是真實漏洞？還是產出端髒資料 / 重複紀錄？
  2. 嚴重度是否合理？不合理就說明應該是什麼、依據是什麼。
  3. 現有證據是否足以支持這個結論？不足就明確標為「證據不足」。
  4. 一句話的客戶端溝通版本（繁體中文，不要技術黑話）。

判定規則（不可協商）：
  - 沒有 evidence 就不要標 confirmed，只能標「證據不足，待補」。
  - 同一站點 + 同一類型重複的，標「重複」並建議保留最早建立的那筆。
  - type 是 finding / target / note / configuration 的，是產出端 bug 不是漏洞類型，標「髒資料」。
  - target 為空的，標「資料不完整」並指出需要補什麼。
  - 不要為了讓數字好看而調高嚴重度。證據不足就寫證據不足。
  - 這一輪只做判讀與建議，不要直接呼叫 API 修改任何狀態。
""".strip())
    print("-" * 72)
    for i, v in enumerate(batch, 1):
        print(f"\n[{i}/{len(batch)}] {v.get('id')}")
        print(f"  嚴重度 : {v.get('severity')}")
        print(f"  類型   : {vtype(v) or '（無）'}")
        print(f"  標題   : {field(v, 'title')}")
        print(f"  目標   : {field(v, 'target')}")
        print(f"  描述   : {field(v, 'description')}")
        print(f"  前置條件: {field(v, 'preconditions')}")
        print(f"  重現步驟: {field(v, 'reproduction_steps')}")
        print(f"  證據   : {field(v, 'evidence')}")
        print(f"  影響   : {field(v, 'impact')}")
        print(f"  建議   : {field(v, 'recommendation')}")
    print("\n" + "-" * 72)
    print("請以上面 " + str(len(batch)) + " 筆為範圍逐筆回覆判定結果。")


def main() -> int:
    ap = argparse.ArgumentParser(description="分流待處理漏洞，產生可執行的審查批次")
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help=f"設定檔路徑，用來推導 --base-url（預設 {DEFAULT_CONFIG}）")
    ap.add_argument("--base-url", default=None,
                    help=f"API base URL（預設從 --config 的 server 區塊推導，"
                         f"讀不到時用 {FALLBACK_BASE_URL}）")
    ap.add_argument("--token", default=os.environ.get("JYSSECAI_TOKEN", ""))
    ap.add_argument("--status", default="open", help="要處理的狀態（預設 open）")
    ap.add_argument("--batch-size", type=int, default=25)
    ap.add_argument("--csv", default="", help="匯出完整明細的 CSV 路徑")
    ap.add_argument("--emit-batch", type=int, default=0,
                    help="輸出某一批的完整內容（可直接貼進對話審查）")
    ap.add_argument("--emit-offset", type=int, default=0,
                    help="配合 --emit-batch：從該批的第幾筆開始輸出（0-based）")
    ap.add_argument("--emit-count", type=int, default=0,
                    help="配合 --emit-batch：只輸出幾筆（0 = 整批）")
    ap.add_argument("--max-field-chars", type=int, default=1200,
                    help="單一欄位截斷長度，避免超長 evidence 灌爆對話（預設 1200）")
    ap.add_argument("--include-dirty", action="store_true",
                    help="把不可審的紀錄也排進批次（不建議）")
    args = ap.parse_args()
    if args.base_url is None:
        args.base_url = default_base_url(args.config)

    if not args.token:
        die("需要 --token 或環境變數 JYSSECAI_TOKEN\n"
            "取得：JSON.parse(localStorage['jysec-auth']).token")

    stats = api(args.base_url, "/vulnerabilities/stats", args.token)
    print("== 平台現況統計 ==")
    bs = stats.get("by_status") if isinstance(stats.get("by_status"), dict) else {}
    by_sev = stats.get("by_severity") if isinstance(stats.get("by_severity"), dict) else {}
    total = stats.get("total")
    if not isinstance(total, int):
        total = sum(bs.values()) if bs else 0
    print(f"  總計 {total} 筆")
    for k, v in sorted(bs.items(), key=lambda kv: -kv[1]):
        print(f"    status={k:<12} {v}")
    for k, v in sorted(by_sev.items(), key=lambda kv: -kv[1]):
        pct = f"{v / total * 100:.1f}%" if total else "?"
        print(f"    severity={k:<10} {v:>4}  ({pct})")
    print()

    # 逐頁撈出目標狀態的紀錄。
    # 分頁本身不能靠「遇到空頁」判斷結束：空頁可能是後端掃描／過濾造成的（見檔頭「已知限制」，
    # 該 bug 已修但落差偵測保留），也可能是分頁邊界抖動。必須走完 total_pages 或累積到
    # total 才停，空頁照樣繼續，否則會提前誤判結束（過往實測會漏掉最後 9 筆）。
    items: list[dict] = []
    seen_ids: set[str] = set()
    page, page_size = 1, 100
    reported_total = None
    pages_fetched = 0
    empty_pages = 0
    while True:
        resp = api(args.base_url, "/vulnerabilities", args.token,
                   {"status": args.status, "page": page, "limit": page_size})
        pages_fetched += 1
        batch = resp.get("vulnerabilities") or []
        if isinstance(resp.get("total"), int):
            reported_total = resp["total"]
        fresh = 0
        for v in batch:
            vid = str(v.get("id") or "")
            if vid and vid in seen_ids:
                continue
            if vid:
                seen_ids.add(vid)
            items.append(v)
            fresh += 1
        if fresh == 0:
            empty_pages += 1
        tp = resp.get("total_pages") or 1
        if page >= tp:
            break
        if reported_total and len(items) >= reported_total:
            break
        page += 1
        if pages_fetched > 200:  # 安全上限，避免異常回應造成無限迴圈
            print("[warn] 已抓 200 頁仍無法收斂，停止。", file=sys.stderr)
            break

    print(f"== 抓取 {args.status} 紀錄 ==")
    if reported_total is None:
        print(f"  API 未提供 total，實抓 {len(items)} 筆（{pages_fetched} 頁）\n")
    elif len(items) < reported_total:
        missing = reported_total - len(items)
        pct = len(items) / reported_total * 100 if reported_total else 0
        print(f"  ⚠ API 回報 {reported_total} 筆，實際只回傳 {len(items)} 筆"
              f"（{pct:.1f}%，缺 {missing} 筆）")
        print(f"    欄位漏包 COALESCE 的 bug 已在 internal/database/vulnerability.go:392-401 修掉：")
        print(f"    欄位清單已統一成 vulnerabilitySelectColumns，所有可能為 NULL 的欄位都包了 COALESCE。")
        print(f"    若仍有落差，代表後端又出現同類的欄位／掃描問題，值得追。")
        print(f"    伺服器 log 可查：掃描失敗現在記 Error 而非 Warn，帶 skipped / returned 筆數")
        print(f"    （internal/database/vulnerability.go:482-488）。")
        if empty_pages:
            print(f"    實測 {pages_fetched} 頁中有 {empty_pages} 頁回傳 0 筆。")
        print(f"    ⚠ 下面這份審查計畫只涵蓋可見的 {len(items)} 筆，缺的那 {missing} 筆無法審。\n")
    else:
        print(f"  完整取得 {len(items)} 筆（{pages_fetched} 頁）\n")

    groups: dict[str, list] = defaultdict(list)
    reasons: dict[str, int] = defaultdict(int)
    for v in items:
        g, why = classify(v)
        v["_group"] = g
        v["_reason"] = why
        groups[g].append(v)
    for k, vs in groups.items():
        for v in vs:
            if v["_reason"]:
                reasons[v["_reason"]] += 1

    print("== 分流結果 ==")
    order = [("reviewable", "可審查"), ("no-target", "缺 target，無法判定"),
             ("not-a-vuln", "type 是筆記/髒值"), ("dirty-type", "type 混入 confidence")]
    for key, label in order:
        n = len(groups.get(key, []))
        mark = "✅" if key == "reviewable" else "⏭"
        print(f"  {mark} {label:<26} {n:>4} 筆")
    rev = groups.get("reviewable", [])
    print(f"\n  可審查佔全部的 {len(rev) / len(items) * 100:.1f}%" if items else "")

    if groups.get("no-target"):
        print(f"\n  ⚠ {len(groups['no-target'])} 筆缺 target。")
        print("    這些不是「待審查」，而是「待補資料」。優先回填 target，否則它們永遠不可審。")
    if groups.get("not-a-vuln"):
        print(f"\n  ⚠ {len(groups['not-a-vuln'])} 筆的 type 是筆記類值。")
        print("    這是 P1 的產出端 bug（type 被寫成 finding/target/note），修資料不如修來源。")
    if groups.get("dirty-type"):
        print(f"\n  ⚠ {len(groups['dirty-type'])} 筆 type 混入 confidence。")
        print("    對應漏洞 05a32395 同源的欄位外洩問題。")

    # 去重分組（僅影響批次建議，不動資料）
    buckets: dict[tuple, list] = defaultdict(list)
    for v in rev:
        key = (norm_origin(v.get("target")), vtype(v).lower())
        buckets[key].append(v)
    dup_groups = {k: vs for k, vs in buckets.items() if len(vs) > 1}
    dup_saved = sum(len(vs) - 1 for vs in dup_groups.values())

    print("\n== 去重（同站點 + 同類型）==")
    print(f"  可審查 {len(rev)} 筆 → {len(buckets)} 組")
    if dup_groups:
        print(f"  其中 {len(dup_groups)} 組有重複，可合併節省 {dup_saved} 筆審查量")
        for (origin, typ), vs in sorted(dup_groups.items(), key=lambda kv: -len(kv[1]))[:8]:
            print(f"    {len(vs):>3} 筆  {origin or '(無)'}  {typ[:36]}")
    print("  ※ 只影響批次建議，不會刪除或合併任何資料。")

    # 證據覆蓋率 —— 決定這批能不能直接審
    with_ev = sum(1 for v in rev if (v.get("evidence") or "").strip())
    with_steps = sum(1 for v in rev if (v.get("reproduction_steps") or "").strip())
    with_poc = sum(1 for v in rev if (v.get("evidence") or "").strip().lower().find("poc") >= 0)
    print("\n== 可審查池的證據覆蓋率 ==")
    print(f"  有 evidence 欄位        {with_ev:>4} / {len(rev)}  ({with_ev / len(rev) * 100 if rev else 0:.1f}%)")
    print(f"  有 reproduction_steps    {with_steps:>4} / {len(rev)}  ({with_steps / len(rev) * 100 if rev else 0:.1f}%)")
    print(f"  evidence 提到 poc        {with_poc:>4} / {len(rev)}")
    if with_ev < len(rev) * 0.5:
        print("  ⚠ 超過一半的紀錄沒有任何證據欄位。這些只能審『結論與類型是否合理』，")
        print("    無法審『漏洞是否真的存在』。不要對它們標 confirmed。")

    # 排序 + 分批
    # 排序鍵：嚴重度 -> 有無證據 -> 描述長度（描述長通常代表內容紮實）-> id（確保可重現）
    def sort_key(v: dict):
        return (SEVERITY_ORDER.get(str(v.get("severity") or "").lower(), 9),
                0 if (v.get("evidence") or "").strip() else 1,
                -(len(v.get("description") or "")),
                str(v.get("id")))

    rev.sort(key=sort_key)
    if args.include_dirty:
        pool = list(rev)
        for key in ("no-target", "not-a-vuln", "dirty-type"):
            pool.extend(groups.get(key, []))
    else:
        pool = rev
    batches = [pool[i:i + args.batch_size] for i in range(0, len(pool), args.batch_size)]

    print(f"\n== 審查批次（每批 {args.batch_size} 筆，共 {len(batches)} 批）==")
    for i, b in enumerate(batches, 1):
        sev_count: dict[str, int] = defaultdict(int)
        origins = set()
        for v in b:
            sev_count[str(v.get("severity") or "?").lower()] += 1
            o = norm_origin(v.get("target"))
            if o:
                origins.add(o)
        mix = " ".join(f"{SEVERITY_ZH.get(k, k)}x{n}" for k, n in
                       sorted(sev_count.items(), key=lambda kv: SEVERITY_ORDER.get(kv[0], 9)))
        print(f"\n  ── 第 {i}/{len(batches)} 批：{len(b)} 筆  [{mix}]  {len(origins)} 個站點"
              f"  有證據 {sum(1 for v in b if (v.get('evidence') or '').strip())} 筆")
        ids = [str(v.get("id")) for v in b]
        print(f"     IDs: {', '.join(ids[:6])}{' ...' if len(ids) > 6 else ''}")
        print(f"     站點: {', '.join(sorted(origins)[:4])}"
              f"{' ...' if len(origins) > 4 else ''}")

    if args.emit_batch:
        n = args.emit_batch
        if n < 1 or n > len(batches):
            die(f"--emit-batch 超出範圍：共 {len(batches)} 批，請指定 1..{len(batches)}")
        batch = batches[n - 1]
        start = max(0, args.emit_offset)
        if start >= len(batch):
            die(f"--emit-offset {start} 超出這批的筆數 {len(batch)}")
        if args.emit_count > 0:
            batch = batch[start:start + args.emit_count]
        else:
            batch = batch[start:]
        emit_batch(batch, n, len(batches), args.max_field_chars)
        return 0

    if batches:
        print("\n== 可直接貼進對話的審查指令模板 ==")
        first = batches[0]
        print("""
請審查以下漏洞紀錄。對每一筆給出：
  1. 這是不是真實漏洞？還是產出端髒資料 / 重複紀錄？
  2. 嚴重度是否合理？不合理就說明應該是什麼、依據是什麼。
  3. 現有證據是否足以支持這個結論？不足就明確標為「證據不足」。
  4. 一句話的客戶端溝通版本（繁體中文，不要技術黑話）。

判定規則（不可協商）：
  - 沒有 evidence 就不要標 confirmed，只能標「證據不足，待補」。
  - 同一站點 + 同一類型重複的，標「重複」並保留最早建立的那筆，其餘建議合併。
  - type 是 finding / target / note / configuration 的，是產出端 bug 不是漏洞類型，標「髒資料」。
  - target 為空的，標「資料不完整」並指出需要補什麼。
  - 不要為了讓數字好看而調高嚴重度。證據不足就寫證據不足。
  - 這一輪只做判讀與建議，不要直接呼叫 API 修改任何狀態。

漏洞 ID：
""".strip())
        for v in first:
            ev = (v.get("evidence") or "").strip()
            print(f"  - {v.get('id')}  [{v.get('severity')}]  {vtype(v) or '（無）'}"
                  f"  target={v.get('target') or '(空)'}"
                  f"  evidence={'有' if ev else '無'}")

    # CSV 明細
    if args.csv:
        with open(args.csv, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "status", "severity", "type", "target", "origin",
                        "group", "reason", "has_evidence", "has_steps", "batch"])
            batch_of = {}
            for i, b in enumerate(batches, 1):
                for v in b:
                    batch_of[str(v.get("id"))] = i
            for v in items:
                w.writerow([v.get("id"), v.get("status"), v.get("severity"),
                            vtype(v), v.get("target"),
                            norm_origin(v.get("target")), v.get("_group"),
                            v.get("_reason"),
                            "Y" if (v.get("evidence") or "").strip() else "N",
                            "Y" if (v.get("reproduction_steps") or "").strip() else "N",
                            batch_of.get(str(v.get("id")), "")])
        print(f"\n完整明細已匯出 → {args.csv}")

    print("\n[完成] 全程唯讀，未修改任何漏洞紀錄。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("已取消")
