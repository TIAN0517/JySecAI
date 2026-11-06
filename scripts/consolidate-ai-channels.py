#!/usr/bin/env python3
"""把 ai.channels 收斂成只留單一 channel（預設保留 nvidia-deepseek-v4）。

設計原則
  1. 文字層級的 block 手術：保留註解、key 順序、縮排、換行格式，不做 YAML round-trip 重排。
  2. 寫入前做完整語意比對（YAML 解析後 new == expected），任何不符就中止、不留半套。
  3. 預設 dry-run；沒有 --apply 絕不寫檔。
  4. 被刪的 channel 若在檔案其他處被引用（default_channel / model_failover_channels /
     系統提示詞…），直接中止並列出行號，除非明確給 --ignore-xrefs。
  5. 輸出與 diff 一律遮蔽憑證，只顯示長度與 sha256 前 12 碼。
  6. --apply 真正刪檔前，會把將被刪的 channel 逐一列出並要求輸入確認字串；
     沒有互動式終端機就中止。

用法
  # 只看現況：channel 清單 + 交叉引用 + 擬變更 diff
  python3 consolidate-ai-channels.py --config /var/lib/jysecai/core/config.yaml

  # 真正執行（會先列出將被刪的 channel 要求輸入 DELETE <筆數> 確認，再備份）
  sudo python3 consolidate-ai-channels.py --config /var/lib/jysecai/core/config.yaml --apply
"""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import re
import shutil
import sys
from datetime import datetime

import yaml

# "    key: rest" 形式的行；本專案 config 一律空格縮排
KEY_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<key>[^\s#:][^:]*):(?P<rest>.*)$")
SECRET_KEY_RE = re.compile(r"(^|_)(api_?key|token|secret|password|passwd|credential|auth)($|_)", re.I)
# 名字像密鑰但其實是數量/額度的欄位，不要遮蔽
SECRET_DENY = {
    "token_budget", "max_tokens", "max_total_tokens", "max_completion_tokens",
    "max_input_tokens", "max_output_tokens", "max_prompt_tokens", "auth_mode",
}
INLINE_CRED_RE = re.compile(r"(?P<pre>[a-z0-9+.-]+://)(?P<user>[^:/@\s]+):(?P<pw>[^@/\s]+)@", re.I)

# 預設行為：保留 jy-gateway 這一個 channel（它就是 config.yaml 現行的
# ai.default_channel），不改名、不改顯示名稱，其餘 channel 全部刪掉。
#
# 為什麼預設保留 jy-gateway：預設值必須等於生產上實際生效的預設通道，
# 否則這支腳本跑完會把 default_channel 指向另一個通道，等於默默改掉
# 整個系統預設走哪條線。
#
# 舊的預設值是 nvidia-deepseek-v4 + 改名成 "minimax" / 顯示名稱
# "JySecAI MiniMax"，但那一筆實際是 NVIDIA 端點
# （integrate.api.nvidia.com / deepseek-ai/deepseek-v4-pro-0813），
# 而真的 MiniMax 通道是 minimax-m31-flash 與 minimax-m31-openai。
# 照舊預設跑會：把 NVIDIA 通道改名成 minimax、讓它當 default_channel、
# 並把兩個真的 MiniMax 通道刪掉。已修正。
#
# 真的要用 MiniMax 請自己指定，例如：
#   --keep minimax-m31-openai --no-rename --new-name "MiniMax M3.1 Flash" \
#                             --default-channel minimax-m31-openai
#   --keep minimax-m31-flash  --no-rename   （provider: claude / api.minimaxi.com/anthropic）
DEFAULT_KEEP = "jy-gateway"
DEFAULT_RENAME = "jy-gateway"   # 與原名相同 = 不改名
DEFAULT_DISPLAY_NAME = "Jy Gateway 5.3 Coder"


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]


def strip_nl(line: str) -> str:
    return line.rstrip("\r\n")


def redact(line: str) -> str:
    """把憑證值換成長度 + sha256 前 12 碼，diff 與報表都不會洩漏原值。"""
    body = strip_nl(line)
    term = line[len(body):]  # 保留原本的換行符，不然 diff 會黏成一坨
    body = INLINE_CRED_RE.sub(
        lambda m: f"{m.group('pre')}{m.group('user')}:"
                  f"<redacted len={len(m.group('pw'))} sha256:{fingerprint(m.group('pw'))}>@",
        body,
    )
    m = KEY_LINE_RE.match(body)
    if m and m.group("key").strip().lower() not in SECRET_DENY and SECRET_KEY_RE.search(m.group("key")):
        raw = m.group("rest").strip()
        if raw and raw not in ('""', "''"):
            quote, inner = "", raw
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
                quote, inner = raw[0], raw[1:-1]
            body = (
                f"{m.group('indent')}{m.group('key')}: {quote}"
                f"<redacted len={len(inner)} sha256:{fingerprint(inner)}>{quote}"
            )
    return body + term


def is_skippable(line: str) -> bool:
    """空行與整行註解不劃分 block 邊界。"""
    s = line.strip()
    return s == "" or s.startswith("#")


def indent_of(line: str):
    s = strip_nl(line)
    if is_skippable(s):
        return None
    return len(s) - len(s.lstrip(" "))


def indent_at(lines: list[str], idx: int) -> int:
    m = KEY_LINE_RE.match(strip_nl(lines[idx]))
    if not m:
        die(f"第 {idx + 1} 行不是預期的 mapping key 行：{redact(strip_nl(lines[idx]))}")
    return len(m.group("indent"))


def block_end(lines: list[str], start: int, indent: int) -> int:
    """從 start 起掃到第一個 indent <= indent 的實體行（不含該行）。"""
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


def first_diff(a, b, path="$"):
    """回傳 new 與 expected 第一個不一致的路徑；一致則回 None。"""
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                       and isinstance(b, (int, float))):
        return [f"{path}: 型別 {type(a).__name__} != {type(b).__name__}"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                return [f"{path}.{k}: expected 多出來"]
            if k not in b:
                return [f"{path}.{k}: new 多出來"]
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: 長度 {len(b)} != {len(a)}"]
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if a == b else [f"{path}: {a!r} != {b!r}"]


def child_indent(lines: list[str], lo: int, hi: int, parent_indent: int):
    best = None
    for i in range(lo, hi):
        ind = indent_of(lines[i])
        if ind is not None and ind > parent_indent and (best is None or ind < best):
            best = ind
    return best


def confirm_delete(delete: list[str], spans: dict, keep: list[str], tty: bool) -> None:
    """真正刪除前的二次確認。

    預設行為一次會刪掉二十幾個 channel，diff 又只顯示遮蔽後的片段，很容易在不留意下
    蓋掉 --apply。所以這裡把「會被刪掉什麼」完整攤開，要求逐字輸入含筆數的確認字串；
    筆數也放進去是為了避免無腦貼上舊的確認字串。
    """
    if not delete:
        return
    n = len(delete)
    print("\n== 刪除二次確認 ==")
    print(f"  保留 : {', '.join(keep)}")
    print(f"  即將從設定檔移除 {n} 個 channel：")
    for name in delete:
        s, e = spans[name]
        print(f"    - {name:<32} 第 {s + 1}–{e} 行")
    if not tty:
        die("stdin 不是終端機，無法進行互動式確認，已中止（未修改任何檔案）。\n"
            "    請改在有 TTY 的終端機執行，或先手動核對上面的清單。")
    try:
        answer = input(f"  確定要刪除這 {n} 個 channel，請輸入 DELETE {n}：")
    except EOFError:
        die("未收到確認輸入，已中止（未修改任何檔案）")
    if answer.strip() != f"DELETE {n}":
        die(f"確認字串不符（收到 {answer.strip()!r}），已中止（未修改任何檔案）")
    print("  已確認，繼續執行。")


def main() -> int:
    ap = argparse.ArgumentParser(description="收斂 ai.channels 成單一 channel")
    ap.add_argument("--config", required=True, help="config.yaml 路徑")
    ap.add_argument("--apply", action="store_true",
                    help="真的寫入（預設 dry-run；會先列出將刪除的 channel 要求確認）")
    ap.add_argument("--keep", action="append", default=[],
                    help=f"要保留的 channel（可重複，預設 {DEFAULT_KEEP}）")
    ap.add_argument("--rename", action="append", default=[],
                    help=f"改名，格式 OLD:NEW（可重複，預設 {DEFAULT_KEEP}:{DEFAULT_RENAME}）")
    ap.add_argument("--new-name", default=DEFAULT_DISPLAY_NAME, help="保留通道的顯示名稱")
    ap.add_argument("--default-channel", default=None,
                    help="default_channel 設成什麼（預設 = 改名後的新名稱）")
    ap.add_argument("--no-rename", action="store_true", help="只刪不改名")
    ap.add_argument("--ignore-xrefs", action="store_true",
                    help="即使有交叉引用也照做（不建議）")
    args = ap.parse_args()

    keep = args.keep or [DEFAULT_KEEP]
    if args.no_rename:
        renames: dict[str, str] = {}
    elif args.rename:
        renames = dict(r.split(":", 1) for r in args.rename)
    elif DEFAULT_KEEP in keep:
        renames = {DEFAULT_KEEP: DEFAULT_RENAME}
    else:
        renames = {}
    for old, new in renames.items():
        if not old or not new:
            die("--rename 格式必須是 OLD:NEW")
    # 改名成自己的原名等於什麼都沒做。丟掉這類項目，避免產生無意義的
    # 設定變更，也让 --no-rename 不再是預設行為的必要條件。
    renames = {old: new for old, new in renames.items() if old != new}
    new_default = args.default_channel or (renames.get(keep[0], keep[0]) if keep else None)
    if not new_default:
        die("無法決定 default_channel，請用 --default-channel 指定")

    # ---- 讀檔 ----
    try:
        with open(args.config, "r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except OSError as exc:
        die(f"讀不到 {args.config}：{exc}")
    if not raw.strip():
        die("檔案是空的")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines(keepends=True)

    try:
        orig = yaml.safe_load(raw)
    except Exception as exc:  # noqa: BLE001
        die(f"原始 YAML 解析失敗，先修好再說：{exc}")
    if not isinstance(orig, dict) or not isinstance(orig.get("ai"), dict):
        die("找不到頂層 ai: 設定")
    if not isinstance(orig["ai"].get("channels"), dict):
        die("找不到 ai.channels 對應的 mapping")

    # ---- 定位 ai: / ai.channels: / 各 channel ----
    ai_hits = find_key(lines, "ai", 0, len(lines), 0)
    if len(ai_hits) != 1:
        die(f"預期 1 個頂層 ai:，實際 {len(ai_hits)} 個")
    ai_start = ai_hits[0]
    ai_end = block_end(lines, ai_start, 0)

    ai_child = child_indent(lines, ai_start, ai_end, 0)
    if ai_child is None:
        die("ai: 底下是空的")
    ch_hits = find_key(lines, "channels", ai_start, ai_end, ai_child)
    if len(ch_hits) != 1:
        die(f"預期 1 個 ai.channels:，實際 {len(ch_hits)} 個")
    ch_start = ch_hits[0]
    ch_indent = indent_at(lines, ch_start)
    ch_end = block_end(lines, ch_start, ch_indent)
    key_indent = child_indent(lines, ch_start, ch_end, ch_indent)
    if key_indent is None:
        die("ai.channels 底下沒有任何 channel")

    spans: dict[str, tuple[int, int]] = {}
    for i in range(ch_start + 1, ch_end):
        m = KEY_LINE_RE.match(strip_nl(lines[i]))
        if m and len(m.group("indent")) == key_indent:
            name = m.group("key").strip().strip("\"'")
            # 只認與 YAML 解析結果對得上的 key，避免把 block scalar 內文字誤判成 channel
            if name in orig["ai"]["channels"]:
                spans[name] = (i, block_end(lines, i, key_indent))
    if not spans:
        die("在 ai.channels 區段找不到可對應的 channel 區塊")

    ordered = sorted(spans.items(), key=lambda kv: kv[1][0])
    real_channels = orig["ai"]["channels"]
    unknown = [n for n in real_channels if n not in spans]
    if unknown:
        die(f"以下 channel 在 YAML 存在但文字區段找不到對應行（可能格式特殊，先人工確認）：{unknown}")

    # ---- 清單 ----
    print(f"config : {args.config}")
    print(f"mode   : {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"layout : ai.channels = 第 {ch_start + 1}–{ordered[-1][1][1]} 行，"
          f"{len(ordered)} 個 channel\n")
    print("== 現況 channel 清單 ==")
    for name, (s, e) in ordered:
        body = "".join(lines[s + 1:e])

        def grab(key):
            mm = re.search(rf"^[ ]*{key}:[ ]*(.+)$", body, re.M)
            return mm.group(1).strip() if mm else "?"

        url = grab("base_url")
        flag = "   <-- MiniMax" if "minimaxi" in url.lower() else ""
        print(f"  L{s + 1:<5} {name:<28} provider={grab('provider'):<18} "
              f"model={grab('model'):<34}{flag}")

    for k in keep:
        if k not in spans:
            die(f"要保留的 channel 不存在：{k}；實際有 {list(spans)}")
    for old in renames:
        if old not in spans:
            die(f"要改名的 channel 不存在：{old}")

    # ---- 擬刪清單 ----
    rename_targets = set(renames.values())
    delete = [n for n, _ in ordered if n not in keep and n not in rename_targets]

    # ---- 先定位 default_channel（比交叉引用掃描早，讓專屬錯誤訊息先生效）----
    dc_idx = None
    dc_value = None
    for i in range(ai_start, ai_end):
        m = KEY_LINE_RE.match(strip_nl(lines[i]))
        if m and m.group("key").strip() == "default_channel":
            dc_idx, dc_value = i, m.group("rest").strip().strip("\"'")
            break
    if dc_idx is None:
        die("找不到 ai.default_channel")

    # ---- 交叉引用掃描（channel 區塊內不算，全部在 block 外）----
    print("\n== 交叉引用掃描 ==")
    inside_channel: set[int] = set()
    for s, e in spans.values():
        inside_channel.update(range(s, e))
    xrefs: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if i in inside_channel or i == dc_idx:
            continue
        for n in delete:
            if re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", line):
                xrefs.append((i, n))
                break
    if xrefs:
        print("  ! 發現交叉引用（刪掉會壞掉其他設定）：")
        for i, n in xrefs:
            print(f"    L{i + 1}: [{n}] {redact(strip_nl(lines[i]))}")
        if not args.ignore_xrefs:
            die("有交叉引用，已中止。確認要刪就補 --ignore-xrefs，"
                "或先把這些引用改掉（建議手動處理，別硬刪）")
        print("  -> --ignore-xrefs 已指定，繼續（請自行確認上述引用）")
    else:
        print("  無交叉引用 OK")

    if dc_value in delete and not args.ignore_xrefs:
        die(f"ai.default_channel 指向即將被刪的 {dc_value}，請用 --default-channel 指定新值")

    # ---- 組出新內容（單趟：跳過刪除範圍 + 套用行內替換）----
    replace: dict[int, str] = {}
    drop: set[int] = set()
    for n in delete:
        s, e = spans[n]
        drop.update(range(s, e))
    for old, new_name in renames.items():
        s, e = spans[old]
        replace[s] = f"{' ' * key_indent}{new_name}:{nl}"
        for j in range(s + 1, e):
            m = KEY_LINE_RE.match(strip_nl(lines[j]))
            if m and m.group("key").strip() == "name":
                replace[j] = f"{m.group('indent')}name: {args.new_name}{nl}"
    replace[dc_idx] = f"{' ' * ai_child}default_channel: {new_default}{nl}"

    out = [replace.get(i, line) for i, line in enumerate(lines) if i not in drop]
    new_text = "".join(out)

    # ---- 語意比對：new 必須精確等於「原檔扣掉要刪的 + 改名 + 改預設」 ----
    try:
        new = yaml.safe_load(new_text)
    except Exception as exc:  # noqa: BLE001
        die(f"改後 YAML 解析失敗，未寫入：{exc}")
    expected = copy.deepcopy(orig)
    new_channels = {n: v for n, v in real_channels.items() if n not in delete}
    for old, new_name in renames.items():
        new_channels[new_name] = {**new_channels.pop(old), "name": args.new_name}
    expected["ai"]["channels"] = new_channels
    expected["ai"]["default_channel"] = new_default
    if new != expected:
        d = first_diff(new, expected)
        die("語意比對失敗（有東西被意外改動），未寫入\n       " + "\n       ".join(d or ["(不明差異)"]))

    # ---- diff（遮蔽憑證）----
    diff = list(difflib.unified_diff(
        [redact(x) for x in lines], [redact(x) for x in out],
        fromfile="config.yaml (before)", tofile="config.yaml (after)", n=3,
    ))
    print("\n== 擬變更 ==")
    print(f"  保留 : {', '.join(keep)}" + (f"   改名 -> {renames}" if renames else ""))
    print(f"  刪除 : {len(delete)} 個 -> {', '.join(delete) if delete else '(無)'}")
    print(f"  預設 : {dc_value} -> {new_default}")
    print(f"  其他 : 完全不動（語意比對通過）")
    print("\n== diff（憑證已遮蔽）==")
    print("".join(diff) if diff else "(無變更)")

    if not args.apply:
        print("\n[dry-run] 未寫入。確認無誤後加 --apply。")
        return 0

    # 不可逆的刪除，寫檔前先要人點頭
    confirm_delete(delete, spans, keep, sys.stdin.isatty())

    # ---- 寫入 + 備份 + 落地後再驗一次 ----
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{args.config}.bak-channels-{stamp}"
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

    print(f"\n[ok] 已寫入，備份：{bak}")
    print(f"     新檔 sha256 = {hashlib.sha256(new_text.encode('utf-8', 'replace')).hexdigest()}")
    print("\n接著（jysec-core 才會讀到新設定）：")
    print("  sudo systemctl restart jysec-core")
    print("  sudo /usr/local/sbin/jysec-healthcheck && echo healthcheck=OK")
    print(f"  sudo grep -nE '^  default_channel:|^    [a-z0-9_-]+:' {args.config}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("已取消")
