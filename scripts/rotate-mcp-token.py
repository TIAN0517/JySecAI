#!/usr/bin/env python3
"""輪替 JySecAI 內部 MCP 服務憑證（mcp.auth_header_value）。

為什麼只需要換這一把
  - mcp.auth_header_value 是**真的**共用密鑰：internal/app/app.go:630 以
    subtle.ConstantTimeCompare 比對 X-MCP-Token 標頭，且僅在 allow_global_access=true 時生效。
  - xss.token 是**死欄位**：internal/handler/xss.go 全檔從未讀取 cfg.Token。
    XSS 驗證走 database.GetXssPayloadByToken() 查 xss_payloads 表，每個 payload 一組
    crypto/rand 產生的 40 碼 hex token。換 xss.token 沒有任何效果，本腳本不碰它。

安全性
  - 文字層級單行替換，保留縮排、引號樣式、行尾註解與換行格式。
  - 寫入前做語意比對：改後 YAML 解析結果必須精確等於「原檔只換掉這一欄」。
  - 自動備份；落地後再驗一次，不符立刻從備份還原。
  - 預設不把新值印到日誌以外的任何地方；--no-print-token 可完全靜默。
  - 新值另外寫一份 0600 的 sidecar 檔，方便合法客戶端取用。

用法
  # dry-run：只看會改哪一行（不產生新值）
  python3 rotate-mcp-token.py --config /var/lib/jysecai/core/config.yaml

  # 真正輪替
  sudo python3 rotate-mcp-token.py --config /var/lib/jysecai/core/config.yaml --apply

  # 交給平台自己產生（EnsureMCPAuth 在欄位為空時自動生成 32 bytes 並寫回 config.yaml）
  sudo python3 rotate-mcp-token.py --config /var/lib/jysecai/core/config.yaml --apply --blank
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import re
import secrets
import shutil
import stat
import sys
from datetime import datetime

import yaml

KEY_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<key>[^\s#:][^:]*):(?P<rest>.*)$")


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def strip_nl(line: str) -> str:
    return line.rstrip("\r\n")


def indent_of(line: str):
    s = strip_nl(line)
    if s.strip() == "" or s.strip().startswith("#"):
        return None
    return len(s) - len(s.lstrip(" "))


def block_end(lines: list[str], start: int, indent: int) -> int:
    for i in range(start + 1, len(lines)):
        ind = indent_of(lines[i])
        if ind is not None and ind <= indent:
            return i
    return len(lines)


def find_key(lines: list[str], key: str, lo: int, hi: int, indent: int) -> list[int]:
    hits = []
    for i in range(lo, hi):
        m = KEY_LINE_RE.match(strip_nl(lines[i]))
        if m and len(m.group("indent")) == indent and m.group("key").strip() == key:
            hits.append(i)
    return hits


def child_indent(lines: list[str], lo: int, hi: int, parent: int):
    best = None
    for i in range(lo, hi):
        ind = indent_of(lines[i])
        if ind is not None and ind > parent and (best is None or ind < best):
            best = ind
    return best


def split_value(rest: str):
    """把 ':' 後面拆成 (引號字元, 值, 行尾註解)，格式不符就原樣回傳。"""
    r = rest.strip()
    m = re.match(r"^(?P<q>[\"']?)(?P<v>.*?)(?P<q2>[\"']?)(?P<c>\s*#.*)?$", r)
    if not m:
        return "", r, ""
    q = m.group("q") or ""
    v = m.group("v")
    if m.group("q2") and q and m.group("q2") != q:
        return "", r, ""
    if m.group("q2") and not q:
        q = m.group("q2")
    return q, v.strip(), (m.group("c") or "")


def main() -> int:
    ap = argparse.ArgumentParser(description="輪替 mcp.auth_header_value")
    ap.add_argument("--config", required=True)
    ap.add_argument("--apply", action="store_true", help="真的寫入（預設 dry-run）")
    ap.add_argument("--bytes", type=int, default=32, help="亂數位元組數（預設 32 → 64 hex）")
    ap.add_argument("--blank", action="store_true",
                    help="只清空欄位，讓 EnsureMCPAuth 在重啟時自動生成新值")
    ap.add_argument("--print-token", dest="print_token", action="store_true", default=True)
    ap.add_argument("--no-print-token", dest="print_token", action="store_false")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    if not raw.strip():
        die("設定檔是空的")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines(keepends=True)

    try:
        orig = yaml.safe_load(raw)
    except Exception as exc:  # noqa: BLE001
        die(f"原始 YAML 解析失敗：{exc}")
    if not isinstance(orig, dict) or not isinstance(orig.get("mcp"), dict):
        die("設定檔沒有 mcp: 區段")
    mcp = orig["mcp"]
    old_token = str(mcp.get("auth_header_value") or "")

    # ---- 定位 mcp: 與 auth_header_value ----
    mcp_hits = find_key(lines, "mcp", 0, len(lines), 0)
    if len(mcp_hits) != 1:
        die(f"預期 1 個頂層 mcp:，實際 {len(mcp_hits)} 個")
    mcp_start = mcp_hits[0]
    mcp_end = block_end(lines, mcp_start, 0)
    sub = child_indent(lines, mcp_start, mcp_end, 0)
    if sub is None:
        die("mcp: 底下是空的")
    val_hits = find_key(lines, "auth_header_value", mcp_start, mcp_end, sub)
    if len(val_hits) != 1:
        die(f"預期 1 個 mcp.auth_header_value，實際 {len(val_hits)} 個。"
            f"若為 0，代表欄位不存在 —— 平台 EnsureMCPAuth 會在啟動時自動生成，"
            f"直接重啟 jysec-core 即可輪替。")
    idx = val_hits[0]
    m = KEY_LINE_RE.match(strip_nl(lines[idx]))
    quote, cur_val, comment = split_value(m.group("rest"))

    # ---- 決定新值 ----
    if args.blank:
        new_token = ""
    else:
        if args.bytes < 16:
            die("--bytes 太小（至少 16）")
        new_token = secrets.token_hex(args.bytes)
    if new_token == old_token:
        die("新舊值相同，無意義")

    new_line = f"{m.group('indent')}auth_header_value: {quote}{new_token}{quote}{comment}{nl}"
    old_line = lines[idx]
    lines[idx] = new_line
    new_text = "".join(lines)

    # ---- 語意比對：只有這一欄應該不一樣 ----
    try:
        new = yaml.safe_load(new_text)
    except Exception as exc:  # noqa: BLE001
        die(f"改後 YAML 解析失敗，未寫入：{exc}")
    expected = copy.deepcopy(orig)
    expected["mcp"]["auth_header_value"] = new_token
    if new != expected:
        changed = [k for k in set(new.get("mcp", {})) | set(expected["mcp"])
                   if new.get("mcp", {}).get(k) != expected["mcp"].get(k)]
        die(f"語意比對失敗，mcp 下意外變動的欄位：{changed}（未寫入）")

    # ---- 報告 ----
    print(f"config        : {args.config}")
    print(f"mode          : {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"auth_header   : {mcp.get('auth_header')!r}  (不變，header 名稱不是密鑰)")
    print(f"全域存取開關  : allow_global_access={mcp.get('allow_global_access')}")
    print(f"              （為 false 時這把密鑰根本不生效，輪替只是衛生）")
    print(f"變更行        : 第 {idx + 1} 行")
    print(f"舊值          : len={len(old_token)} sha256={hashlib.sha256(old_token.encode()).hexdigest()[:12]}")
    print(f"新值          : len={len(new_token)} sha256={hashlib.sha256(new_token.encode()).hexdigest()[:12]}"
          f"  ({'清空，平台自動生成' if args.blank else f'{args.bytes} bytes CSPRNG'})")

    if not args.apply:
        print("\n[dry-run] 未寫入。加 --apply 才會真的換。")
        return 0

    # ---- 寫入 + 備份 + 落地後複驗 ----
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{args.config}.bak-mcptoken-{stamp}"
    shutil.copy2(args.config, bak)
    try:
        with open(args.config, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
        with open(args.config, "r", encoding="utf-8", newline="") as fh:
            again = yaml.safe_load(fh.read())
    except Exception as exc:  # noqa: BLE001
        shutil.copy2(bak, args.config)
        die(f"寫入/驗證失敗，已從備份還原 {bak}：{exc}")
    if again != expected:
        shutil.copy2(bak, args.config)
        die(f"落地後語意不符，已從備份還原 {bak}")

    # ---- 新值 sidecar（0600）----
    host = str(mcp.get("host") or "127.0.0.1")
    port = mcp.get("port") or 6689
    header = str(mcp.get("auth_header") or "X-MCP-Token")
    sidecar = f"{args.config}.mcp-token-{stamp}"
    try:
        fd = os.open(sidecar, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f"# JySecAI MCP 全域服務憑證，{stamp} 輪替產生\n")
            fh.write(f"# 僅限合法客戶端使用，勿提交版控、勿貼到聊天或 issue\n")
            fh.write(f"X-MCP-URL={host}:{port}\n")
            fh.write(f"X-MCP-HEADER={header}\n")
            fh.write(f"{header}={new_token}\n")
        os.chmod(sidecar, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as exc:
        print(f"[warn] sidecar 寫入失敗（不影響設定已更新）：{exc}")

    print(f"\n[ok] 已輪替。備份：{bak}")
    print(f"     sidecar（0600）：{sidecar}")
    if args.print_token and not args.blank:
        print("\n新值（只顯示這一次，請立刻複製到合法客戶端）：")
        print(f"  {header}: {new_token}")

    print("\n接著：")
    print("  sudo systemctl restart jysec-core")
    print("  sudo /usr/local/sbin/jysec-healthcheck && echo healthcheck=OK")
    print("\n驗證新舊 token（把 <NEW> / <OLD> 換成實際值）：")
    print(f"  # 新 token 應為 200")
    print(f"  curl -s -o /dev/null -w '%{{http_code}}\\n' -X POST http://{host}:{port}/mcp \\")
    print(f"    -H '{header}: <NEW>' -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'")
    print(f"  # 舊 token 應為 401")
    print(f"  curl -s -o /dev/null -w '%{{http_code}}\\n' -X POST http://{host}:{port}/mcp \\")
    print(f"    -H '{header}: <OLD>' -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'")
    print("\n回滾：")
    print(f"  sudo cp {bak} {args.config} && sudo systemctl restart jysec-core")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("已取消")
