#!/usr/bin/env python3
"""
scan_secret_content.py — 掃描檔案內容中的憑證。

比對 Telegram bot token、平台 API key、JWT secret、政府系統帳密等高風險樣式。
只報告不修改，命中即擋下 commit。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass

# (名稱, 正則) — 正則必須含至少一個 capture group 作為值
CONTENT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Telegram Bot Token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b")),
    ("平台 API Key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    ("平台閘道金鑰 (sk-jy-)", re.compile(r"\bsk-jy-[A-Za-z0-9_-]{24,}\b")),
    ("FOFA / ZoomEye API Key", re.compile(r"\b[a-z_]*?(?:key|token|secret)[a-z_]*\b\s*[:=]\s*[\"']?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I)),
    ("JWT secret 賦值", re.compile(r"JWT_?SECRET\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']")),
    ("政府系統帳密 (.env)", re.compile(r"^\s*[A-Z_]*(?:PIN|PASSWORD)\s*=\s*[\"']?([^\"'\s#]{6,})", re.M)),
    ("PRIVATE KEY 區塊", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# 明顯是範例/佔位符的值，不算違規
PLACEHOLDERS = re.compile(
    r"^(?:x{3,}|\*{3,}|your[_-]|YOUR[_-]|<[^>]+>|\$\{.*\}|%s|changeme|placeholder|"
    r"example|dummy|test[_-]?key|demo|xxxx+|null|none|todo|fixme)",
    re.I,
)

# 允許的檔案（測試 fixture / 範例）
ALLOW_FILES = re.compile(
    r"(config\.example\.yaml|\.example\.(env|ya?ml|json)|_test\.(py|go)|test_.*\.py|"
    r"conftest\.py|harden\.py|scan_secret_content\.py|block_secret_filenames\.py|"
    r"SECRET_EXPOSURE_REPORT\.md|\.githooks/)",
    re.I,
)

# 允許的路徑（第三方套件 / 歷史封存）
# 注意：仅放行「本身就不该出现在仓库」的目录；
# 个案工作目录（tpe_broadcast/、poc_scripts/ 等）不在此列 —— 它们的
# 内容同样需要扫描，否则真实凭据会借由「已知是工作档」而逃过检查。
ALLOW_PATHS = re.compile(r"(^|/)(_archive|node_modules|site-packages|\.venv|venv|\.codex|__pycache__)/", re.I)


def looks_like_placeholder(value: str) -> bool:
    return bool(PLACEHOLDERS.search(value.strip()))


def main() -> int:
    # 檔案清單來源優先序：
    #   1. 命令列引數（手動測試 / 獨立使用時最可靠）
    #   2. stdin（pre-commit pass_filenames 的標準行為）
    # 讀 stdin 需在 tty 判斷之前進行：部分 Windows 環境的 python 以互動模式
    # 啟動時會阻塞且讀不到管線輸入，改以引數優先可避免誤判為「無違規」。
    files: list[str] = list(sys.argv[1:])
    if not files and not sys.stdin.isatty():
        try:
            files = [ln.strip() for ln in sys.stdin if ln.strip()]
        except (OSError, ValueError):
            files = []

    hits: list[tuple[str, str, str]] = []  # (file, rule, snippet)

    for f in files:
        norm = f.replace("\\", "/")
        if ALLOW_FILES.search(norm) or ALLOW_PATHS.search(norm):
            continue
        p = Path(f)
        if not p.is_file():
            continue
        try:
            if p.stat().st_size > 5_000_000:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for name, pat in CONTENT_RULES:
            for m in pat.finditer(text):
                value = m.group(1) if m.groups() else m.group(0)
                if looks_like_placeholder(value):
                    continue
                line_no = text.count("\n", 0, m.start()) + 1
                snippet = value[:12] + ("..." if len(value) > 12 else "")
                hits.append((f, f"{name} @L{line_no}", snippet))

    if not hits:
        return 0

    print("\n[P0] 偵測到疑似憑證內容，已阻止 commit：\n", file=sys.stderr)
    by_file: dict[str, list[tuple[str, str]]] = {}
    for fname, rule, snip in hits:
        by_file.setdefault(fname, []).append((rule, snip))

    for fname, rules in sorted(by_file.items()):
        print(f"  {fname}", file=sys.stderr)
        for rule, snip in rules:
            print(f"      - {rule}: {snip}", file=sys.stderr)

    print(
        "\n處理方式：\n"
        "  1. 移到環境變數或本地 config.yaml（已在 .gitignore）\n"
        "  2. 換成佔位符，例如 api_key: \"sk-xxxxxxx\"\n"
        "  3. 確認為測試資料 → 加進 ALLOW_FILES\n"
        "  4. 已在版控歷史 → 依 SECRET_EXPOSURE_REPORT.md 輪替 + git filter-repo\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
