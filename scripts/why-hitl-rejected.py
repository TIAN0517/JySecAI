#!/usr/bin/env python3
"""診斷「审计 Agent 已拒绝」到底是哪一種原因。

為什麼需要這支：internal/handler/hitl.go:713 不分情況都發同一句 UI 訊息
「审计 Agent 已拒绝本次工具调用」，但實際有 6 種成因（internal/handler/hitl_audit_agent.go），
其中 4 種是 fail-closed 的保守失敗，不是模型真的判定拒絕。
真正的原因一律寫在 hitl_interrupts.decision_comment。

用法
  sudo python3 why-hitl-rejected.py --db /var/lib/jysecai/core/conversations.db
  sudo python3 why-hitl-rejected.py --db ... --limit 20
  sudo python3 why-hitl-rejected.py --db ... --journal      # 一併抓 journal 的底層錯誤
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import subprocess
import sys

# (comment 前綴, 分類, 意義, 該查什麼)
CAUSES = [
    ("audit agent: LLM 未配置",
     "設定缺失",
     "審計模型沒有可用的 api_key 或 model。AuditModelEffective() 只會從主 openai 設定"
     "繼承『空的』欄位，兩處都空就直接擋。",
     "檢查 config.yaml 的 hitl.audit_model.api_key / .model，以及頂層 openai 區段。"),
    ("audit agent: LLM 调用失败",
     "呼叫失敗（fail-closed）",
     "HTTP 或網路層失敗就被當成拒絕。真正原因寫在 journal 的『审计 Agent LLM 调用失败』。",
     "常見：401 key 無效／過期、429 速率、400 不接受 thinking 參數、90 秒 timeout。"
     "用 --journal 抓底層 error 原文。"),
    ("audit agent: LLM 无有效响应",
     "回應為空（fail-closed）",
     "HTTP 200 但 choices 陣列是空的，模型實際上沒給內容。",
     "多半是模型回空字串或只回 reasoning；也可能是 max_completion_tokens=1024 配上"
     "很長的 audit_agent_prompt，模型還沒-output 就被截斷。"),
    ("audit agent: 响应无法解析",
     "JSON 解析失敗（fail-closed）",
     "模型有回應，但內容裡找不到 {\"decision\": \"approve\"|\"reject\"} 這種結構。",
     "模型用 markdown 包起來、夾帶前言、或回中文散文。journal 的『审计 Agent 响应解析失败』"
     "會附 240 字元 snippet，--journal 可看。"),
    ("audit agent: handler unavailable",
     "內部狀態異常",
     "h == nil，正常情況不該發生。",
     "若持續出現代表 HITL 在 AgentHandler 尚未初始化完就被呼叫。"),
    ("audit agent: reject",
     "模型判定為拒絕",
     "模型明確回 decision=reject 且沒附理由（程式補上的預設 comment）。",
     "要看 audit_agent_prompt 的拒絕規則，或讓模型務必附 comment。"),
    ("audit agent: approve",
     "模型判定為通過",
     "decision=approve，不該顯示拒絕。",
     "若你看到拒絕卻是這個 comment，代表前端把事件歸錯類。"),
]


def classify(comment: str | None, decision: str | None = None) -> tuple[str, str, str, str] | None:
    s = (comment or "").strip()
    dec = (decision or "").strip().lower()
    for prefix, cat, meaning, check in CAUSES:
        if s == prefix or s.startswith(prefix):
            return cat, meaning, check, prefix
    if s.startswith("audit agent: "):
        # 模型自己給的理由 —— 必須搭配 decision 判讀，approve 與 reject 是兩件事
        if dec == "approve":
            return ("模型判定為通過（附理由）",
                    "模型明確回 decision=approve，comment 是它自己給的理由。",
                    "這是真正的政策判斷，不是故障。可以拿這段理由確認它的判準是否合理。",
                    "")
        if dec == "reject":
            return ("模型判定為拒絕（附理由）",
                    "模型明確回 decision=reject，comment 是它自己給的理由。",
                    "這是真正的政策判斷，不是故障。看這段理由對不對，必要時調整 audit_agent_prompt。",
                    "")
        return ("模型裁決（理由格式異常）",
                f"comment 來自審計 Agent，但 decision 欄位是 {decision!r}，無法判定通過或拒絕。",
                "確認 decided_by 與 decision 是否被正確寫入。", "")
    if s == "":
        return ("原因未寫入",
                "decision_comment 是空的，無法從資料庫還原原因。",
                "改看 journal 的『审计 Agent』相關 Warn 行。", "")
    return ("非審計 Agent 的拒絕",
            f"這筆 comment 不屬於審計 Agent 的 6 種成因：{s[:120]}",
            "確認 decided_by 是不是 audit_agent；若是人工審批，則是 reviewer 設定問題。", "")


def main() -> int:
    ap = argparse.ArgumentParser(description="診斷審計 Agent 拒絕的原因")
    ap.add_argument("--db", default="/var/lib/jysecai/core/conversations.db")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--journal", action="store_true",
                    help="一併抓 journald 裡審計 Agent 的底層錯誤")
    ap.add_argument("--all", action="store_true", help="不看 decided_by 過濾，全部決策紀錄")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"[abort] 找不到 {args.db}", file=sys.stderr)
        return 2
    try:
        con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        print(f"[abort] 無法以唯讀開啟（多半是權限，需要 sudo）：{exc}", file=sys.stderr)
        return 2

    sql = ("SELECT tool_name, decision, decision_comment, decided_at, decided_by "
           "FROM hitl_interrupts WHERE decision IS NOT NULL")
    if not args.all:
        sql += " AND decided_by = 'audit_agent'"
    sql += " ORDER BY decided_at DESC LIMIT ?"
    try:
        rows = con.execute(sql, (args.limit,)).fetchall()
    except sqlite3.Error as exc:
        print(f"[abort] 查詢失敗：{exc}", file=sys.stderr)
        return 2
    con.close()

    if not rows:
        print("查不到任何審計 Agent 的決策紀錄。")
        print("可能原因：")
        print("  - reviewer 不是 audit_agent（檢查 hitl.default_reviewer 與該對話的覆寫值）")
        print("  - 這台服務的紀錄在別的資料庫（--db 換路徑試試）")
        print("  - 真的還沒被審計 Agent 裁決過")
        return 0

    print(f"== 最近 {len(rows)} 筆審計 Agent 決策（來源：hitl_interrupts）==\n")
    buckets: dict[str, int] = {}
    per_bucket: dict[str, tuple[str, str, str]] = {}
    for i, (tool, decision, comment, decided_at, by) in enumerate(rows, 1):
        cat, meaning, check, _ = classify(comment, decision) or ("?", "?", "?", "")
        buckets[cat] = buckets.get(cat, 0) + 1
        per_bucket.setdefault(cat, (meaning, check, decision or ""))
        print(f"[{i}] {decided_at}  tool={tool}")
        print(f"    decision : {decision}   (decided_by={by})")
        print(f"    分類     : {cat}")
        print(f"    comment  : {comment!r}")
        print()

    print("== 統計 ==")
    for cat, n in sorted(buckets.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>3} 筆  {cat}")

    top = max(buckets, key=buckets.get)
    meaning, check, sample_decision = per_bucket[top]
    print(f"\n== 最近最常見的成因：{top} ==")
    print(f"  sample decision: {sample_decision}")
    print(f"  {meaning}")
    print(f"  下一步：{check}")

    if args.journal:
        print("\n== journal 底層錯誤（最近 200 行）==")
        try:
            out = subprocess.run(
                ["journalctl", "-u", "jysec-core", "-n", "2000", "--no-pager"],
                capture_output=True, text=True, timeout=30,
            ).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"  抓不到 journal：{exc}")
            return 0
        pat = re.compile(r"审计 Agent|audit_agent")
        hits = [ln for ln in out.splitlines() if pat.search(ln)]
        if not hits:
            print("  （最近 2000 行沒有審計 Agent 相關紀錄）")
        for ln in hits[-25:]:
            print(f"  {ln[:600]}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
