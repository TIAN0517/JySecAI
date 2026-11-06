#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_targets.py — 逐字核驗 payload 的兩個跳轉目標
=================================================================================
需求：跳轉必須精確指向
    https://97y.me/tjneJ
    https://97y.me/5N6d8
一字都不能少（不得多尾斜線 / 多 query / 少字 / 大小寫不符）。

檢查項：
  1. style.js 內明文字串 == 期望值（逐位元組）
  2. base64 片段解碼後 == 明文
  3. len == 20
  4. sha256 == 檔頭註解所載常數
  5. 通過 style.js 自身的 valid() 規則（/^https:\/\/97y\.me\/[A-Za-z0-9]{5}$/）
  6. 全文掃描：是否出現任何「變體」字串（少字 / 多斜線 / 帶 query）
  7. assets/style.js.b64 與 scripts/style.js 內容一致
"""
import base64
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 從技能包 scripts/ 或 .validation/ 執行都能找到 style.js
CANDIDATES = [
    os.path.join(HERE, "style.js"),
    os.path.join(HERE, "..", "scripts", "style.js"),
    r"C:\Users\Administrator\Desktop\evidence\JySecAi\skills\cloaking-implant\scripts\style.js",
    "/mnt/c/Users/Administrator/Desktop/evidence/JySecAi/skills/cloaking-implant/scripts/style.js",
]
STYLE = next((p for p in CANDIDATES if os.path.exists(p)), None)
if not STYLE:
    print("!! 找不到 style.js")
    sys.exit(2)

EXPECT = [
    ("https://97y.me/tjneJ", 20,
     "51ee21b5be71637aef5e7b9f927c334327521a2173283dc5dc05f06e7c27e615",
     "aHR0cHM6Ly85N3kubWUvdGpuZUo="),
    ("https://97y.me/5N6d8", 20,
     "5070eb12a8a918f6f6da4d9b14de0332f613126ecce43c25b92aeed874dfe865",
     "aHR0cHM6Ly85N3kubWUvNU42ZDg="),
]
RX = re.compile(r"^https://97y\.me/[A-Za-z0-9]{5}$")

src = open(STYLE, encoding="utf-8").read()
print("style.js :", STYLE)
print("size     :", len(src), "bytes")
print("md5      :", hashlib.md5(src.encode("utf-8")).hexdigest())
print()

ok = True
for url, ln, sha, b64 in EXPECT:
    print("=== %s ===" % url)
    print("  1) 明文逐字存在        :", url in src)
    print("  2) 出现次数            :", src.count(url))
    print("  3) base64 片段存在     :", b64 in src)
    dec = base64.b64decode(b64).decode("utf-8")
    print("  4) base64 解码 == 明文 :", dec == url, "->", dec)
    print("  5) 长度                :", len(url), "== %d" % ln, len(url) == ln)
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    print("  6) sha256              :", h)
    print("     与注释常量一致       :", h == sha)
    print("  7) 通过 valid() 正则    :", bool(RX.match(url)))
    print("  8) 无尾斜线/空白/query  :",
          not url.endswith("/") and "?" not in url and "#" not in url
          and " " not in url and "\n" not in url and "\r" not in url)
    ok = ok and (url in src) and (src.count(url) == 2) and (dec == url) \
        and (len(url) == ln) and (h == sha) and bool(RX.match(url))
    print()

# 变体扫描：任何 https://97y.me/... 的形态（排除 JS 行注释，避免把格式说明误判为变体）
print("=== 全文 97y.me 形态扫描 ===")
code_only = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
code_only = re.sub(r"//[^\n]*", "", code_only)
found = sorted(set(re.findall(r"https://97y\.me/[^\s'\"`,)\]]*", code_only)))
for f in found:
    tag = "OK " if f in [e[0] for e in EXPECT] else "!! 变体"
    print("  %s %r  (len=%d)" % (tag, f, len(f)))
variants = [f for f in found if f not in [e[0] for e in EXPECT]]
print("  非预期变体数量 :", len(variants))
comment_forms = sorted(set(re.findall(r"https://97y\.me/[^\s'\"`,)\]]*", src)) - set(found))
if comment_forms:
    print("  仅见于注释的形态（说明文字，非活目标）:", comment_forms)

# base64 资产一致性
b64asset = os.path.join(os.path.dirname(STYLE), "..", "assets", "style.js.b64")
if os.path.exists(b64asset):
    blob = open(b64asset, encoding="utf-8").read().strip()
    try:
        dec = base64.b64decode(blob).decode("utf-8")
        same = dec.strip() == src.strip()
        print("\nassets/style.js.b64 解码后与 scripts/style.js 一致 :", same)
        print("  解码后 md5 :", hashlib.md5(dec.strip().encode("utf-8")).hexdigest())
        ok = ok and same
    except Exception as e:
        print("\nassets/style.js.b64 解码失败 :", e)
        ok = False

print("\n总体 :", "全部通过 ✅" if (ok and not variants) else "有未通过项 ❌")
sys.exit(0 if (ok and not variants) else 1)
