#!/usr/bin/env python3
"""
check_python_syntax.py — Python 語法檢查（含 BOM）。

擋下兩類常見問題：
  1. UTF-8 BOM（U+FEFF）開頭 — Windows 編輯器常見，會導致 SyntaxError
  2. 語法錯誤 — 避免壞掉的腳本進版控
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass

BOM = b"\xef\xbb\xbf"
ALLOW_PATHS = ("node_modules/", "_archive/", "site-packages/", ".venv/", "venv/", ".codex/", "__pycache__/")


def main() -> int:
    # 檔案清單來源優先序：命令列引數 > stdin（見 scan_secret_content.py 說明）
    files: list[str] = list(sys.argv[1:])
    if not files and not sys.stdin.isatty():
        try:
            files = [ln.strip() for ln in sys.stdin if ln.strip()]
        except (OSError, ValueError):
            files = []

    bom_files: list[str] = []
    syntax_errors: list[tuple[str, str]] = []

    for f in files:
        norm = f.replace("\\", "/")
        if any(s in norm for s in ALLOW_PATHS):
            continue
        p = Path(f)
        if not p.is_file() or p.suffix != ".py":
            continue
        try:
            raw = p.read_bytes()
        except OSError:
            continue

        if raw.startswith(BOM):
            bom_files.append(f)
            raw = raw[len(BOM):]

        try:
            ast.parse(raw.decode("utf-8", errors="strict"))
        except SyntaxError as e:
            syntax_errors.append((f, f"L{e.lineno}: {e.msg}"))
        except UnicodeDecodeError:
            syntax_errors.append((f, "編碼錯誤（非 UTF-8）"))

    # BOM 是本工具可以直接修的（只移除開頭 BOM，不改內容）
    if bom_files:
        for f in bom_files:
            try:
                p = Path(f)
                p.write_bytes(p.read_bytes()[len(BOM):])
            except OSError:
                pass
        print("\n[P1] 已自動移除 UTF-8 BOM：\n", file=sys.stderr)
        for f in bom_files:
            print(f"  - {f}", file=sys.stderr)
        print("", file=sys.stderr)

    if syntax_errors:
        print("\n[P1] 偵測到 Python 語法錯誤，已阻止 commit：\n", file=sys.stderr)
        for f, err in syntax_errors:
            print(f"  - {f}: {err}", file=sys.stderr)
        print("", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
