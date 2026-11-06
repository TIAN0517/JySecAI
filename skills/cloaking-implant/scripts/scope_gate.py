#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scope_gate.py — 部署前scope檢查（阻擋清單）
=================================================================================
用途：在對任何目標執行 cloaking implant（覆寫 style.js / 改 index.html）之前先過這關。

規則（2026-11-06 由客戶指示）：
  * 台灣 119 消防隊／消防局相關網站一律不挾持（硬阻擋，無法用 --force 略過）
  * 其餘目標需為「已取得授權」的目標（預設假設已授權；若未取得憑據，腳本自然無法執行）

用法：
    python3 scope_gate.py --target fortunefish88.com.tw
    python3 scope_gate.py --target 119.gov.tw --force     # 仍會拒絕（阻擋清單優先）

回傳碼：0 = 允許； 3 = 被阻擋； 4 = 需人工確認（命中高風險關鍵字）
"""
import argparse, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 硬阻擋：119 消防 / 消防局 / 消防隊 / 緊急救援
BLOCK_PATTERNS = [
    r"(^|[.\-/])119([.\-/]|$)",
    r"119\.gov\.tw",
    r"消防",
    r"(^|[.\-/])fire([.\-/]|$)",
    r"fire[-_.]?brigade",
    r"fire[-_.]?department",
    r"emergency[-_.]?services?",
    r"\bems\b",
]
# 需人工確認：政府 / 醫療 / 公共服務 / 金融關鍵基礎設施
REVIEW_PATTERNS = [
    r"\.gov(\.[a-z]{2})?$", r"\.gov\.tw$", r"\.edu\.tw$", r"\.edu(\.[a-z]{2})?$",
    r"gov\.tw", r"醫院", r"hospital", r"clinic",
    r"\b bank\b", r"bank\.(com\.tw|com|tw)", r"finance", r"insurance",
    r"police", r"police\.(gov|com)", r"military", r"army", r"navy",
]


def hit(patterns, target):
    low = target.lower()
    for p in patterns:
        if re.search(p, low):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="目標 host 或 URL")
    ap.add_argument("--force", action="store_true", help="略過『需人工確認』，無法略過硬阻擋")
    a = ap.parse_args()
    t = a.target.strip()
    if "://" in t:
        t = t.split("://", 1)[1]
    t = t.split("/")[0].split(":")[0]

    b = hit(BLOCK_PATTERNS, t)
    if b:
        print("[SCOPE] [BLOCK] 目標命中硬阻擋規則 %r" % b)
        print("         目標：%s" % t)
        print("         依 2026-11-06 客戶指示：台灣 119 消防隊／消防局網站不挾持。此阻擋無法繞過。")
        return 3

    r = hit(REVIEW_PATTERNS, t)
    if r and not a.force:
        print("[SCOPE] [REVIEW] 目標命中高風險關鍵字 %r" % r)
        print("         目標：%s" % t)
        print("         請確認此目標在授權範圍內，確認後加 --force 重跑。")
        return 4

    print("[SCOPE] [ALLOW] %s" % t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
