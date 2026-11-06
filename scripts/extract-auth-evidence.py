#!/usr/bin/env python3
"""從平台既有的工具執行紀錄中取回認證端點的證據，完全離線、不發任何新請求。

為什麼是這個路徑
  針對特定目標的登入端點做「帳號列舉」驗證，標準做法需要對不同輸入各打一次請求。
  但平台在每次工具呼叫時已經把「原始回應」與「耗時」記進 tool_executions：
      result       = 服務端回應全文（狀態碼、header、body、堆疊）
      duration_ms  = 該次呼叫的端到端耗時
  也就是說，狀態碼差異、堆疊內容、以及時間差通道三項證據都已經存在於本機。
  把它們取出來做離線分析，既不增加目標的負擔，也不重複已被計入的測試行為。

輸出
  - 終端摘要：各狀態碼的筆數、耗時分布（最小/中位/最大/平均）
  - 每個狀態碼的原始回應樣本存檔（供人工比對與報告引用）
  - 證據清單 JSON（含耗時統計，供報告引用）

安全
  - arguments 內的憑證欄位一律遮蔽，只輸出長度與 sha256 前 12 碼。
  - 預設唯讀開啟資料庫，不做任何寫入。

用法
  sudo python3 extract-auth-evidence.py --db /var/lib/jysecai/core/conversations.db \\
    --target th-api.hcfd.gov.tw
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys

# 常見的憑證欄位名
SECRET_FIELDS = re.compile(
    r'"(?P<k>[^"]*(?:pass|pwd|secret|token|key|credential)[^"]*)"\s*:\s*"(?P<v>[^"]*)"',
    re.I)

# 從回應文字抓 HTTP 狀態碼。
# 實測發現平台把工具結果存成 MCP 封包 {"content":[{"type":"text","text":"..."}]}，
# 而腳本輸出用的是 STATUS: 200 / HTTPError: 401 / "status_code": 401 等多種寫法，
# 不是標準的 "HTTP/1.1 401" 狀態列，所以要比對多種樣式。
STATUS_PATTERNS = [
    re.compile(r'(?i)\bHTTP/[\d.]+\s+(\d{3})\b'),          # HTTP/1.1 401
    re.compile(r'(?i)\bSTATUS\s*[:=]\s*(\d{3})\b'),        # STATUS: 200
    re.compile(r'(?i)\bHTTPError\s*[:=]\s*(\d{3})\b'),     # HTTPError: 401
    re.compile(r'(?i)["\']?status_?code["\']?\s*[:=]\s*["\']?(\d{3})'),  # "status_code": 401
    re.compile(r'(?i)["\']?status["\']?\s*[:=]\s*["\']?(\d{3})\b'),      # "status": 401
    re.compile(r'(?i)\bHTTP\s+status\s*[:=]?\s*(\d{3})\b'),
    re.compile(r'(?i)\bcode\s*[:=]\s*(\d{3})\b'),
]

# 被平台安全規則攔截的嘗試（不是 HTTP 回應）
BLOCKED_MARKERS = re.compile(
    r'(安全规则|安全規則|安全规则拦截|政府网站保护|government-domains|'
    r'禁止攻击政府网站|禁止攻擊政府網站|tool guard|toolguard)')
# 判斷是不是認證端點的回應
AUTH_HINT = re.compile(r'(?i)(login|signin|sign-in|/auth|登入|認證|unauthor|forbidden|密碼|密码)')


def extract_status(text: str):
    """回傳第一個狀態碼；若不是 HTTP 回應則回 None。"""
    if not text:
        return None
    for pat in STATUS_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def classify_record(arguments: str, blob: str) -> str:
    """把紀錄分成三類：真的拿到 HTTP 回應 / 被平台規則攔截 / 其他內部工具呼叫。"""
    if BLOCKED_MARKERS.search(blob):
        return "blocked-by-toolguard"
    if extract_status(blob) is not None:
        return "http-response"
    return "other"


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def redact_args(text: str) -> str:
    def sub(m):
        k, v = m.group('k'), m.group('v')
        if not v:
            return m.group(0)
        q = f'"{v}"'
        return (f'"{k}": "<redacted len={len(v)} '
                f'sha256:{hashlib.sha256(v.encode("utf-8","replace")).hexdigest()[:12]}">"')
    return SECRET_FIELDS.sub(sub, text or "")


def search_signature(args) -> int:
    """在全庫搜尋特徵字串，回答「證據到底還在不在」。只讀。"""
    try:
        con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        die(f"無法唯讀開啟（多半需要 sudo）：{exc}")
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    pat = f"%{args.signature}%"
    print(f"== 搜尋特徵：{args.signature!r} ==\n")
    total = 0
    for tbl in ("messages", "process_details", "tool_executions"):
        if tbl not in tables:
            continue
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({tbl})")]
        text_cols = [c for c in cols if c in
                     ("content", "result", "payload", "error", "data", "summary", "body")]
        if not text_cols:
            continue
        where = " OR ".join(f"IFNULL({c},'') LIKE ?" for c in text_cols)
        try:
            rows = con.execute(
                f"SELECT rowid, {', '.join(text_cols)} FROM {tbl} WHERE {where}",
                tuple([pat] * len(text_cols))).fetchall()
        except sqlite3.Error as exc:
            print(f"  {tbl}: 查詢失敗 {exc}")
            continue
        print(f"  {tbl:<16} 命中 {len(rows)} 筆")
        total += len(rows)
        for row in rows[:3]:
            blob = " ".join(str(x) for x in row[1:] if x)
            i = blob.find(args.signature)
            snippet = blob[max(0, i - 220): i + 320].replace("\n", "\\n")
            print(f"      rowid={row[0]}  …{snippet}…")
        print()
    con.close()
    if total == 0:
        print("  沒有任何命中。")
        print()
        print("  這代表：該證據不在資料庫中（可能只留在對話正文、")
        print("  或當時只記錄了狀態碼與長度、body 沒被保存）。")
        print("  在這種情況下，該發現不能標為 confirmed。")
    else:
        print(f"  合計命中 {total} 筆。請用上面的 rowid 取出原文作為證據引用。")
    print("\n[完成] 全程唯讀，未發任何請求。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="離線取回認證端點的既有證據")
    ap.add_argument("--db", default="/var/lib/jysecai/core/conversations.db")
    ap.add_argument("--target", required=True, help="目標主機，用來挑出相關紀錄")
    ap.add_argument("--out", default="/tmp/auth-evidence", help="樣本輸出目錄")
    ap.add_argument("--limit", type=int, default=4000, help="最多檢視幾筆紀錄")
    ap.add_argument("--signature", default="",
                    help="改為模式：在整個 messages / process_details / tool_executions "
                         "中搜尋特徵字串（例如 at .*Single\\[TSource\\] 或 路徑洩漏字樣），"
                         "列出命中的紀錄位置。只讀，不發任何請求。")
    args = ap.parse_args()

    if args.signature:
        return search_signature(args)

    if not os.path.exists(args.db):
        die(f"找不到 {args.db}")
    try:
        con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        die(f"無法唯讀開啟（多半需要 sudo）：{exc}")

    os.makedirs(args.out, exist_ok=True)

    # 先確認欄位存在
    cols = {r[1] for r in con.execute("PRAGMA table_info(tool_executions)")}
    need = {"tool_name", "arguments", "result", "duration_ms"}
    if not need.issubset(cols):
        die(f"tool_executions 缺少欄位：{need - cols}")
    has_conv = "conversation_id" in cols

    sql = ("SELECT id, tool_name, arguments, result, error, status, duration_ms,"
           + (" conversation_id," if has_conv else " '',")
           + " start_time FROM tool_executions "
           "WHERE (arguments LIKE ? OR IFNULL(result,'') LIKE ?) "
           "ORDER BY start_time DESC LIMIT ?")
    rows = con.execute(sql, (f"%{args.target}%", f"%{args.target}%", args.limit)).fetchall()
    con.close()

    if not rows:
        print(f"沒有任何 tool_executions 的 arguments/result 提到 {args.target}")
        print()
        print("可能原因：")
        print("  - 該目標的測試是在別的對話，且 result 被清空或只存在 partial_output")
        print("  - 目標字串寫法不同（試試只給主機名，不要含 scheme/路徑）")
        print("  - 紀錄已在保留期內被清掉")
        print()
        print("可改試：")
        print(f"  --target {args.target.split('.')[0]}")
        return 0

    print(f"== 找到 {len(rows)} 筆相關紀錄（唯讀，未發任何新請求）==\n")

    by_status: dict[str, list] = {}
    kinds: dict[str, int] = {}
    for r in rows:
        rid, tool, arguments, result, err, st, dur, conv, started = r
        blob = f"{result or ''}\n{err or ''}"
        kind = classify_record(arguments or "", blob)
        kinds[kind] = kinds.get(kind, 0) + 1
        rec = {
            "id": rid, "tool": tool, "status": st, "duration_ms": dur,
            "arguments": arguments or "",
            "result": result or "", "error": err or "", "started": started,
            "conversation_id": conv, "kind": kind,
        }
        if kind == "http-response":
            rec["http_status"] = extract_status(blob)
            rec["auth_related"] = bool(
                AUTH_HINT.search(blob) or AUTH_HINT.search(arguments or ""))
            by_status.setdefault(rec["http_status"], []).append(rec)

    print("== 紀錄類型 ==")
    label = {"http-response": "真的拿到 HTTP 回應",
             "blocked-by-toolguard": "被平台安全規則攔截（不是回應）",
             "other": "其他內部工具呼叫／文件寫入"}
    for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {label.get(k, k):<34} {n:>4} 筆")
    if kinds.get("blocked-by-toolguard"):
        print(f"  -> 這些被攔截的紀錄不是證據，僅代表「該目標需要授權範圍才能探測」")
    print()

    if not by_status:
        print("== 沒有任何帶 HTTP 狀態碼的回應 ==")
        print("  這代表既有紀錄裡沒有該目標的實際 HTTP 證據。")
        print("  可能原因：")
        print("   - 測試當下就被平台安全規則攔下（見上方 blocked 計數）")
        print("   - 原始回應未寫入 tool_executions（只留在訊息正文或 process_details）")
        print("   - 紀錄已在保留期內被清掉")
        print()
        print("  下一步建議：改從 process_details / messages 找原始回應，")
        print("  或由測試者提供離線樣本（HAR / 原始回應），全程不需要再打目標。")
        with open(os.path.join(args.out, "evidence-summary.json"), "w", encoding="utf-8") as fh:
            json.dump({"target": args.target, "total_records": len(rows),
                       "record_kinds": kinds, "by_status": {}},
                      fh, ensure_ascii=False, indent=2)
        return 0

    # 摘要
    summary = {"target": args.target, "total_records": len(rows),
               "record_kinds": kinds, "by_status": {}}
    print("== 狀態碼分布（僅計真的拿到回應的紀錄）==")
    for key in sorted(by_status, key=lambda k: (-len(by_status[k]), k)):
        items = by_status[key]
        durs = [i["duration_ms"] for i in items if i["duration_ms"] is not None]
        authn = sum(1 for i in items if i["auth_related"])
        line = f"  {key:<12} {len(items):>4} 筆（其中認證相關 {authn}）"
        if durs:
            line += (f"   耗時 min={min(durs)}ms  中位={int(statistics.median(durs))}ms"
                     f"  max={max(durs)}ms  平均={int(statistics.mean(durs))}ms")
        else:
            line += "   （無耗時資料）"
        print(line)
        summary["by_status"][key] = {
            "count": len(items), "auth_related": authn,
            "duration_ms": ({
                "min": min(durs), "median": int(statistics.median(durs)),
                "max": max(durs), "mean": int(statistics.mean(durs)), "n": len(durs),
            } if durs else None),
        }

    # 兩組狀態碼之間的時間差（帳號列舉的第三通道）
    multi = {k: v for k, v in by_status.items()
             if k.isdigit() and len([i for i in v if i["auth_related"]]) >= 3}
    if len(multi) >= 2:
        print("\n== 時間通道分析（帳號列舉的第三通道，僅計認證相關紀錄）==")
        for key, items in sorted(multi.items()):
            d = sorted(i["duration_ms"] for i in items
                       if i["duration_ms"] is not None and i["auth_related"])
            if d:
                print(f"  {key}: n={len(d)}  min={d[0]}  p50={d[len(d)//2]}  max={d[-1]}")
        groups = {k: [i["duration_ms"] for i in v
                      if i["duration_ms"] is not None and i["auth_related"]]
                  for k, v in multi.items()}
        keys = sorted(groups)
        if len(keys) == 2:
            a, b = groups[keys[0]], groups[keys[1]]
            if a and b:
                ma, mb = statistics.mean(a), statistics.mean(b)
                print(f"\n  {keys[0]} 平均 {ma:.1f}ms  vs  {keys[1]} 平均 {mb:.1f}ms"
                      f"   差異 {abs(ma-mb):.1f}ms")
                if abs(ma - mb) > 1:
                    print("  -> 存在可量測的時間差。即使回應狀態碼與 body 都被統一，"
                          "這個通道仍可用來列舉。")
                    summary["timing_channel_detected"] = True
                    summary["timing_delta_ms"] = round(abs(ma - mb), 1)
                else:
                    print("  -> 兩組耗時接近，時間通道不明顯（仍需更多樣本確認）")
                    summary["timing_channel_detected"] = False
        else:
            print("  （認證相關紀錄只落在單一狀態碼組，無法比較）")
    else:
        print("\n（認證相關且同一狀態碼的樣本少於 3 筆，無法做時間通道分析）")

    # 樣本存檔
    print(f"\n== 樣本已存到 {args.out} ==")
    written = 0
    for key, items in by_status.items():
        for i, item in enumerate(items[:3]):
            safe = re.sub(r"[^0-9A-Za-z._-]", "_", key)
            path = os.path.join(args.out, f"{safe}-{i + 1}.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f"# tool: {item['tool']}  status: {item['status']}  "
                         f"duration_ms: {item['duration_ms']}\n")
                fh.write(f"# started: {item['started']}  id: {item['id']}\n")
                fh.write(f"# arguments (憑證已遮蔽): "
                         f"{redact_args((item['arguments'] or '')[:2000])}\n")
                fh.write("\n===== result =====\n")
                fh.write(item["result"][:20000])
                if item["error"]:
                    fh.write("\n===== error =====\n")
                    fh.write(item["error"][:5000])
            written += 1
    print(f"  寫出 {written} 個樣本檔")

    with open(os.path.join(args.out, "evidence-summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(f"  統計摘要 → {os.path.join(args.out, 'evidence-summary.json')}")
    print("\n[完成] 以上全部來自本機既有紀錄，未對目標發送任何請求。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("已取消")
