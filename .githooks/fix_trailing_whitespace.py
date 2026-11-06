#!/usr/bin/env python3
"""
fix_trailing_whitespace.py — 移除行尾空白並確保檔案以單一換行結尾。
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass

BINARY_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
                 ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".exe", ".dll"}


def main() -> int:
    # 檔案清單來源優先序：命令列引數 > stdin（見 scan_secret_content.py 說明）
    files: list[str] = list(sys.argv[1:])
    if not files and not sys.stdin.isatty():
        try:
            files = [ln.strip() for ln in sys.stdin if ln.strip()]
        except (OSError, ValueError):
            files = []

    changed: list[str] = []

    for f in files:
        p = Path(f)
        if not p.is_file() or p.suffix.lower() in BINARY_SUFFIX:
            continue
        try:
            raw = p.read_bytes()
            if b"\x00" in raw[:4096]:
                continue  # 二進位檔
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        nl = "\r\n" if "\r\n" in text else "\n"
        lines = text.splitlines()
        cleaned = [ln.rstrip() for ln in lines]
        new = nl.join(cleaned)
        if cleaned:
            new += nl
        if new != text:
            try:
                p.write_text(new, encoding="utf-8", newline="")
                changed.append(f)
            except OSError:
                pass

    if changed:
        print(f"\n[P2] 已清理 {len(changed)} 個檔案的行尾空白/結尾換行", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
