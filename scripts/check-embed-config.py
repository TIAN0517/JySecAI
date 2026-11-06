#!/usr/bin/env python3
"""唯讀檢查生產知識庫 embedding 設定，遮蔽金鑰。

用法：sudo python3 scripts/check-embed-config.py [config路徑]
預設讀 /var/lib/jysecai/core/config.yaml。
"""
import re
import sys

DEFAULT = "/var/lib/jysecai/core/config.yaml"

# Windows 主機預設 console 編碼會把中文印成亂碼，強制 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def mask(value: str) -> str:
    v = (value or "").strip().strip("'\"")
    if not v:
        return "(空)"
    if re.fullmatch(r"sk-x+", v) or re.search(r"x{4,}", v):
        return f"!! 佔位符 (len={len(v)}) !!"
    return f"(已設定, len={len(v)}, 前綴 {v[:3]}…{v[-2:]})"


def block(text: str, name: str) -> list[str]:
    out, inside = [], False
    for line in text.splitlines():
        if re.match(rf"^{name}:", line):
            inside = True
            out.append(line)
            continue
        if inside and re.match(r"^[a-z_]+:", line):
            break
        if inside:
            out.append(line)
    return out


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        print(f"[錯誤] 讀不到 {path}: {exc}")
        print("       需要 sudo，或用引數指定路徑。")
        return 1

    print(f"=== {path} :: knowledge.embedding ===")
    lines = block(text, "knowledge")
    if not lines:
        print("[錯誤] 沒有 knowledge: 區段")
        return 1

    for line in lines[:14]:
        stripped = line.strip()
        if stripped.startswith("enabled:"):
            print(f"  enabled: {stripped.split(':', 1)[1].strip()}")
        elif stripped.startswith(("provider:", "model:", "base_url:")):
            print(f"  {stripped}")
        elif stripped.startswith("api_key:"):
            val = stripped.split(":", 1)[1].strip()
            print(f"  api_key: {mask(val)}")

    print("\n=== 判讀 ===")
    kb = "\n".join(lines)
    enabled = re.search(r"enabled:\s*(\S+)", kb)
    if enabled and enabled.group(1) in ("false", "False"):
        print("  ! knowledge.enabled = false —— 整個知識庫功能是關閉的")
    if re.search(r"api_key:\s*sk-x+", kb):
        print("  ! embedding.api_key 還是範例檔的佔位符 sk-xxxxxxx")
    if "dashscope" in kb:
        print("  · base_url 指向 dashscope（text-embedding-v4，OpenAI 相容）")
    elif "ai5090.gasjy.com" in kb:
        print("  ! base_url 指向自己的閘道 —— 必須有 /v1/embeddings 路由")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
