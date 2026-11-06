#!/usr/bin/env python3
"""
block_secret_filenames.py — 阻擋憑證檔名進入版控。

從 stdin 讀取待 commit 的檔案清單（pre-commit pass_filenames 行為）。
若任一檔名符合憑證特徵即以 exit 1 擋下，並列出應如何處理。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 檔名特徵：命中任一即擋下
NAME_RULES: list[tuple[str, re.Pattern[str]]] = [
    (".env 檔", re.compile(r"(^|/)\.env($|\.)", re.I)),
    ("PEM/憑證", re.compile(r"\.(pem|key|crt|p12|pfx|jks)$", re.I)),
    ("JWT/權杖 JSON", re.compile(r"token.*\.json$|cookie.*\.json$|session.*\.json$", re.I)),
    ("憑證/密碼檔", re.compile(r"credential|secret|password|passwd", re.I)),
    ("待刪金鑰", re.compile(r"(^|/)\.tmp-.*\.(key|pem)$", re.I)),
]

# 明確允許（範例檔、測試 fixture）
# 註：這個倉庫是 Go 專案，測試檔名是 *_test.go；只放行 *_test.py 會讓每個
# 檔名帶 "secret" 的 Go 測試都被擋下（例如 config_secrets_test.go）。
ALLOW = re.compile(
    r"(^|/)(config\.example\.yaml|config\.yaml\.example|.*\.example\.(env|yaml|yml|json)"
    r"|.*_test\.(py|go)|test_.*\.py|.*/conftest\.py"
    r"|CREDENTIAL_ROTATION_CHECKLIST\.md|SECRET_EXPOSURE_REPORT\.md"
    r"|docs/security/config-secret-migration-assessment\.md"
    r"|\.githooks/(block_secret_filenames|scan_secret_content)\.py)$",
    re.I,
)

# 2026-11-07 補充：以下三個檔名帶 "secret"，但內容完全不是憑證檔
# （已用 scan_secret_content.py 與 check_python_syntax.py 驗證 rc=0）：
#   internal/config/secret_protection.go   —— 實作機密保護的原始碼
#   internal/database/secret_crypto.go      —— 加密輔助原始碼
#   skills/offensive-cicd-secrets/SKILL.md  —— CI/CD 憑證滲透方法論文件
# 豁免是精確路徑而非放寬規則：真正的憑證檔仍然會被擋下。
ALLOW_EXACT = {
    "internal/config/secret_protection.go",
    "internal/database/secret_crypto.go",
    "skills/offensive-cicd-secrets/SKILL.md",
}

# 允許追蹤的憑證路徑（若確定為公開測試資料）
ALLOW_PATHS = re.compile(
    r"^(_archive|node_modules|site-packages|\.venv|venv|\.codex)/",
    re.I,
)


def main() -> int:
    # 檔案清單來源優先序：命令列引數 > stdin（見 scan_secret_content.py 說明）
    files: list[str] = list(sys.argv[1:])
    if not files and not sys.stdin.isatty():
        try:
            files = [ln.strip() for ln in sys.stdin if ln.strip()]
        except (OSError, ValueError):
            files = []

    violations: list[tuple[str, str]] = []

    for f in files:
        p = f.replace("\\", "/")
        if p in ALLOW_EXACT:
            continue
        if ALLOW.match(p) or ALLOW_PATHS.match(p):
            continue
        # 已刪除的檔案不需要檢查內容
        if not Path(f).exists():
            continue
        for label, pat in NAME_RULES:
            if pat.search(p):
                violations.append((f, label))
                break

    if not violations:
        return 0

    print("\n[P0] 偵測到疑似憑證檔案，已阻止 commit：\n", file=sys.stderr)
    for fname, label in violations:
        print(f"  - {fname}  ({label})", file=sys.stderr)
    print(
        "\n處理方式：\n"
        "  1. 若是真實憑證 → 不要 commit，改從環境變數或 config.example.yaml 讀取\n"
        "  2. 若是範例檔   → 改名為 <name>.example.env / .example.yaml\n"
        "  3. 確定是測試 fixture → 加進本腳本的 ALLOW 清單\n"
        "  4. 已在歷史中    → 依 SECRET_EXPOSURE_REPORT.md 執行 git filter-repo\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
