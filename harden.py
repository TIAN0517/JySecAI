#!/usr/bin/env python3
"""
harden.py — JySecAI 腳本安全強化工具（可重跑）

用途
----
1. **檢查**（預設）：掃描全 repo，列出 TLS 驗證停用、硬編碼憑證等問題。
2. **修復**（--fix）：自動修補「對外第三方 API」的 TLS 驗證。

設計原則：不改变既有行为
------------------------
只修「对第三方商业 API 关闭 TLS 验证」这一类问题。这类请求会携带 API key
（FOFA / ZoomEye / Quake / Shodan），verify=False 等于把凭据交给中间人。

**不修**「探测目标系统」的 verify=False —— 政务系统常用自签凭证，
关闭验证是刻意且必要的；改成 True 会让脚本直接失败，反而削弱工具。

用法
----
    python harden.py              # 只检查，输出报告
    python harden.py --fix        # 自动修复第三方 API 的 TLS
    python harden.py --report     # 写出 harden_report.json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Windows console defaults to cp950/cp936 (Big5) and cannot encode all CJK
# punctuation used in this script's output. Force UTF-8 so the tool is usable
# on both Windows and POSIX without changing any scan/fix behaviour.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 分级定义

# 第三方商业 API 网段：这些服务使用公开受信任 CA，verify=False 纯属缺陷
THIRD_PARTY = ("fofa.info", "fofoapi.com", "zoomeye", "quake.360.net", "shodan.io",
               "certifi", "google.com", "duckduckgo", "github.com", "api.github")

# 探测目标：政务系统常用自签凭证，保持关闭验证
TARGET_PROBE = ("gov.tw", "gov.taipei", "ncdr.nat.gov.tw", "tpf.gov.tw", "tfd.gov.tw",
                "119.gov.taipei", "kcg.gov.tw", "tycg.gov.tw", "hcfd.gov.tw")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "site-packages",
             "_archive", ".codex", "site-packages", "dist", "build", ".build"}
SKIP_FILES = {"harden.py", "tls_policy.py"}

VERIFY_FALSE = re.compile(r"verify\s*=\s*False")
CERT_NONE = re.compile(r"verify_mode\s*=\s*ssl\.CERT_NONE|check_hostname\s*=\s*False")


class Finding(NamedTuple):
    path: Path
    lineno: int
    kind: str          # "thirdparty" | "target" | "cert_none"
    snippet: str

    @property
    def rel(self) -> str:
        try:
            return str(self.path.relative_to(ROOT))
        except ValueError:
            return str(self.path)


def iter_python_files():
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        yield p


def classify(line: str, file_text: str) -> str:
    """判断这一行属于哪一类。"""
    low = line.lower()
    if any(t in low for t in THIRD_PARTY):
        return "thirdparty"
    # 同行含目标域名 -> 视为目标探测
    if any(t in low for t in TARGET_PROBE):
        return "target"
    # 看 URL 变量来源：若来自 BASE/PROXY 常量且全文件无第三方标记，视为目标
    if any(t in file_text.lower() for t in THIRD_PARTY):
        return "thirdparty"
    return "target"


def scan() -> tuple[list[Finding], list[Finding]]:
    third: list[Finding] = []
    target: list[Finding] = []
    for path in iter_python_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if VERIFY_FALSE.search(line) or CERT_NONE.search(line):
                kind = classify(line, text)
                f = Finding(path, i, kind, line.strip()[:120])
                (third if kind == "thirdparty" else target).append(f)
    return third, target


# ---------------------------------------------------------------- 自动修复

IMPORT_BLOCK = (
    "import sys, os\n"
    "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
    "from tls_policy import VERIFY  # 第三方 API 验证凭证链"
)


def fix_file(path: Path, findings: list[Finding]) -> int:
    """把该文件中的 verify=False 换成 verify=VERIFY，并插入 import。返回修改数。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    target_lines = {f.lineno for f in findings}

    changed = 0
    for idx, line in enumerate(lines, 1):
        if idx in target_lines and VERIFY_FALSE.search(line):
            lines[idx - 1] = VERIFY_FALSE.sub("verify=VERIFY", line)
            changed += 1
        elif idx in target_lines and CERT_NONE.search(line):
            # ssl.CERT_NONE 无法用 requests 的 verify 表达；标记出来交人工处理
            pass

    if not changed:
        return 0

    new_text = "".join(lines)
    if "from tls_policy import VERIFY" not in new_text:
        nl = "\r\n" if "\r\n" in new_text else "\n"
        parts = new_text.splitlines(keepends=True)
        insert_at = _last_top_level_import(parts)
        parts.insert(insert_at, IMPORT_BLOCK.replace("\n", nl) + nl)
        new_text = "".join(parts)

    path.write_text(new_text, encoding="utf-8")
    return changed


def _last_top_level_import(parts: list[str]) -> int:
    """
    回傳「最後一個頂層 import 陳述式結束後」的插入位置（0-based 行索引）。

    必須限定在模組頂層：若腳本把 import 寫在 try/except 內（例如常見的
    `try: import re except ImportError: ...`），用 ast.walk 取最大行號會把
    新的 import 插進 try 區塊，造成 SyntaxError。
    """
    src = "".join(parts)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return 0
    insert_at = 0
    for node in tree.body:  # 只看模組頂層
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            insert_at = max(insert_at, node.end_lineno or 0)
    # 吃掉紧接在 import 之后的 docstring 区块
    while insert_at < len(parts) and not parts[insert_at].strip():
        insert_at += 1
    return insert_at


# ---------------------------------------------------------------- 硬编码凭证

SECRET_PATTERNS = {
    "jwt_secret": re.compile(r"JWT_SECRET\s*=\s*[\"']([^\"']{8,})[\"']"),
    "bot_token": re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}"),
    "api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "gov_credential": re.compile(r"(?:PIN|PASSWORD)\s*=\s*[\"'](\w{6,})[\"']", re.I),
}


def scan_secrets() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {k: [] for k in SECRET_PATTERNS}
    for path in iter_python_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for kind, pat in SECRET_PATTERNS.items():
                if pat.search(line):
                    try:
                        rel = str(path.relative_to(ROOT))
                    except ValueError:
                        rel = str(path)
                    out[kind].append({"file": rel, "line": i})
    return out


# ---------------------------------------------------------------- 输出

def print_report(third: list[Finding], target: list[Finding], secrets: dict) -> None:
    print("=" * 74)
    print("JySecAI harden.py — 安全检查报告")
    print("=" * 74)

    print(f"\n[1] 第三方 API 关闭 TLS 验证  ({len(third)} 处)  ← 本工具会自动修复")
    if third:
        by_file: dict[str, list[Finding]] = {}
        for f in third:
            by_file.setdefault(f.rel, []).append(f)
        for rel in sorted(by_file):
            lines = ", ".join(str(f.lineno) for f in by_file[rel])
            print(f"    {rel}:{lines}")
    else:
        print("    无")

    print(f"\n[2] 目标探测关闭 TLS 验证  ({len(target)} 处)  ← 刻意保留，不修改")
    print("    政务系统使用自签凭证，关闭验证是必要行为。")
    if target:
        by_file = {}
        for f in target:
            by_file.setdefault(f.rel, []).append(f)
        shown = sorted(by_file.items(), key=lambda kv: -len(kv[1]))[:10]
        for rel, fs in shown:
            print(f"    {rel}: {len(fs)} 处")
        if len(by_file) > 10:
            print(f"    ... 另 {len(by_file) - 10} 个文件")

    print(f"\n[3] 硬编码凭证（仅报告，不修改）")
    for kind, hits in secrets.items():
        if hits:
            files = sorted({h["file"] for h in hits})
            print(f"    {kind}: {len(hits)} 处 / {len(files)} 文件")
            for rel in files[:5]:
                print(f"        - {rel}")
            if len(files) > 5:
                print(f"        ... 另 {len(files) - 5} 个")
        else:
            print(f"    {kind}: 无")

    print("\n" + "=" * 74)


def main() -> int:
    ap = argparse.ArgumentParser(description="JySecAI 脚本安全强化工具")
    ap.add_argument("--fix", action="store_true", help="自动修复第三方 API 的 TLS 验证")
    ap.add_argument("--report", action="store_true", help="写出 harden_report.json")
    args = ap.parse_args()

    print("扫描中...\n")
    third, target = scan()
    secrets = scan_secrets()

    if args.fix and third:
        by_file: dict[Path, list[Finding]] = {}
        for f in third:
            by_file.setdefault(f.path, []).append(f)
        total = 0
        for path, fs in sorted(by_file.items()):
            try:
                n = fix_file(path, fs)
            except Exception as e:  # noqa: BLE001
                print(f"  [SKIP] {path.name}: {e}")
                continue
            if n:
                total += n
                print(f"  [FIX] {path.relative_to(ROOT)}: {n} 处")
        print(f"\n共修复 {total} 处。")
        # 重新扫描以输出修复后状态
        third, target = scan()

    print_report(third, target, secrets)

    if args.report:
        payload = {
            "third_party_tls_disabled": [
                {"file": f.rel, "line": f.lineno, "snippet": f.snippet} for f in third
            ],
            "target_probe_tls_disabled_count": len(target),
            "hardcoded_secrets": secrets,
        }
        out = ROOT / "harden_report.json"
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"报告已写出: {out.name}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
