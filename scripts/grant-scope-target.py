#!/usr/bin/env python3
"""把已授權的政府／關鍵基礎設施目標加入 tool_guard 的授權範圍（Scope）。

為什麼需要這支
  工具守衛預設阻擋所有政府網域（規則 ID: government-domains）。這是預設的保守行為，
  但對「有正式授權的政府案件」會讓工具完全不能用。程式碼裡本來就有 Scope 機制
  （internal/toolguard/toolguard.go）讓**單一命中的主機**在授權範圍內時放行，
  其餘規則與其餘目標照常評估。

這個工具的設計重點是「不能順手把保護關掉」
  1. 只接受「精確網域」或「萬用字元」兩種加法，預設不動 domain_suffixes。
     加 ".gov.tw" 這種後綴等同於關閉整條保護，腳本會直接拒絕。
  2. 寫入前必做雙向控制測試：
       負向控制：未授權的政府網域必須「仍被阻擋」 —— 證明保護沒有被弱化
       正向控制：你要加的這個目標必須「被放行」   —— 證明例外確實生效
     兩個控制都通過才允許 PUT。
  3. 預設 dry-run，沒有 --apply 不會送出任何寫入請求。

用法
  # 取 token：瀏覽器 console 執行 JSON.parse(localStorage['jysec-auth']).token
  python3 grant-scope-target.py --target th-api.hcfd.gov.tw            # dry-run
  python3 grant-scope-target.py --target th-api.hcfd.gov.tw --apply
  python3 grant-scope-target.py --target '*.hcfd.gov.tw' --wildcard --apply
  python3 grant-scope-target.py --target .tpf.gov.tw --suffix --apply  # 整個機關

  根後綴（.gov.tw / .gov.cn …）會放行該 TLD 底下的所有政府網域，預設拒絕；
  必須附上書面授權依據，這個決定才會留在稽核軌跡裡而不是手改設定檔夾帶：
  python3 grant-scope-target.py --target .gov.tw --suffix \\
      --authorization-ref '2026-edu-gov-hackathon-合約編號' --apply
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

from jysecai_config import DEFAULT_CONFIG, FALLBACK_BASE_URL, default_base_url

# 未授權的政府網域控制組。刻意用 .gov.example，避免指涉任何真實目標。
CONTROL_HOST = "portal.agency.gov.example"

# 這幾個後綴一加進去，該 ccTLD 底下的**所有**政府網域都會放行，等同關閉整條
# 保護在該 TLD 上的作用。預設拒絕；要加必須同時提供書面授權依據，讓這個決定
# 留在工具的稽核軌跡裡，而不是只能靠手改設定檔夾帶。
ROOT_GOV_SUFFIXES = (".gov", ".gov.tw", ".gov.cn", ".gov.hk", ".gov.uk",
                     ".gov.au", ".gov.jp", ".gov.sg", ".gov.in", ".gov.us",
                     ".gov.*")


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def api(base: str, path: str, token: str, method: str = "GET", body=None, timeout: int = 20):
    url = base.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body_txt or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {"error": body_txt[:300]}
    except Exception as e:  # noqa: BLE001
        die(f"無法連線 {url}：{e}")


def valid_host(h: str) -> bool:
    if not h or len(h) > 253:
        return False
    if h.startswith(".") or h.endswith("."):
        return False
    if "://" in h or "/" in h:
        return False
    return all(c.isalnum() or c in ".-*" for c in h)


def build_scope(current: dict, target: str, key: str) -> dict:
    """把 target 加進 scope 的 key 欄位。key 為 domains / wildcards / domain_suffixes。"""
    scope = dict(current.get("scope") or {})
    lst = list(scope.get(key) or [])
    if target in lst:
        print(f"  （{target} 已經在 scope.{key} 中，無需變更）")
    else:
        lst.append(target)
    # 排序讓設定檔穩定可 diff
    scope[key] = sorted(set(x for x in lst if x))
    return scope


def probe(base, token, cfg, tool, args, label):
    code, res = api(base, "/tool-guard/test", token, "POST",
                    {"config": cfg, "toolName": tool, "arguments": args})
    if code != 200:
        die(f"試匹配請求失敗 HTTP {code}：{res}")
    blocked = bool(res.get("blocked"))
    print(f"  {label}")
    print(f"    結果：{'仍被阻擋 ⛔' if blocked else '放行 ✅'}")
    if blocked and res.get("match"):
        m = res["match"]
        print(f"    規則：{m.get('ruleId', '?')}  命中：{m.get('matchedText', '?')}")
    return blocked


def main() -> int:
    ap = argparse.ArgumentParser(description="把已授權目標加入 tool_guard 授權範圍")
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help=f"設定檔路徑，用來推導 --base-url（預設 {DEFAULT_CONFIG}）")
    ap.add_argument("--base-url", default=None,
                    help=f"API base URL（預設從 --config 的 server 區塊推導，"
                         f"讀不到時用 {FALLBACK_BASE_URL}）")
    ap.add_argument("--target", required=True, help="已授權的目標主機名")
    ap.add_argument("--wildcard", action="store_true", help="當作萬用字元加入（預設精確網域）")
    ap.add_argument("--suffix", action="store_true",
                    help="當作網域後綴加入（須以 '.' 開頭，例：.tpf.gov.tw）。"
                         "會放行該後綴底下的所有主機，範圍比精確網域大得多")
    ap.add_argument("--authorization-ref", default="",
                    help="書面授權依據（案號／服務契約編號／授權書檔名）。"
                         "加入 .gov.tw 這類根後綴時必填")
    ap.add_argument("--token", default=os.environ.get("JYSSECAI_TOKEN", ""))
    ap.add_argument("--token-file", default="", help="從檔案讀 token")
    ap.add_argument("--probe-tool", default="exec")
    ap.add_argument("--probe-arg", default="command",
                    help="試匹配時使用的參數欄位名")
    ap.add_argument("--probe-value", default="", help="預設以 https://<target>/ 當參數值")
    ap.add_argument("--apply", action="store_true", help="真的寫入（預設 dry-run）")
    args = ap.parse_args()
    if args.base_url is None:
        args.base_url = default_base_url(args.config)

    if args.wildcard and args.suffix:
        die("--wildcard 與 --suffix 只能擇一")
    if args.suffix and not args.target.startswith("."):
        die(f"--suffix 必須以 '.' 開頭，收到：{args.target!r}")
    if not args.suffix and not valid_host(args.target):
        die(f"看起來不像主機名：{args.target!r}（不接受 scheme、路徑、前後點）")

    key = "domain_suffixes" if args.suffix else ("wildcards" if args.wildcard else "domains")

    # 前置閘：要在碰服務之前就拒絕。放在後面的迴圈只能看到「設定檔裡已存在的
    # 整組後綴」，使用者自己剛打的那個必須在這裡擋，否則沒服務在手時根本看不到
    # 這道閘，等於形同虛設。
    if args.suffix and args.target in ROOT_GOV_SUFFIXES and not args.authorization_ref:
        die(f"拒絕：--suffix {args.target} 會放行該 TLD 底下的**所有**政府網域，\n"
            "等同關閉整條政府網域保護在該 TLD 上的作用。\n"
            "若這確實是本案書面授權的範圍，附上依據重跑：\n"
            f"  --suffix {args.target} --authorization-ref '<案號或授權書檔名>'\n"
            "否則請改用精確網域（--target 主機名）或受限制的萬用字元（--wildcard）。")

    token = args.token
    if args.token_file:
        with open(args.token_file, "r", encoding="utf-8") as fh:
            token = fh.read().strip()
    if not token:
        die("需要 --token / --token-file / 環境變數 JYSSECAI_TOKEN\n"
            "取得方式：瀏覽器 console → JSON.parse(localStorage['jysec-auth']).token")

    code, cur = api(args.base_url, "/tool-guard", token)
    if code != 200:
        die(f"GET /tool-guard 失敗 HTTP {code}：{cur}\n"
            "（PUT 需要 config:write 權限且 session scope=all）")
    if "enabled" not in cur:
        die(f"回應格式不符：{json.dumps(cur, ensure_ascii=False)[:200]}")

    print("== 現況 ==")
    print(f"  enabled : {cur.get('enabled')}")
    print(f"  rules   : {len(cur.get('rules') or [])} 條")
    old_scope = cur.get("scope")
    if old_scope:
        for k, v in old_scope.items():
            print(f"  scope.{k:<16}: {v}")
    else:
        print("  scope   : (未設定 → 所有政府目標一律阻擋)")
    print()

    # 安全閘：根後綴會放行整個 TLD 的政府網域，預設拒絕；要有書面授權才放行。
    new_scope = build_scope(cur, args.target, key)
    for s in (new_scope.get("domain_suffixes") or []):
        if s in ROOT_GOV_SUFFIXES and not args.authorization_ref:
            die(f"拒絕：domain_suffixes 含有 {s!r}，這等同關閉整條政府網域保護在該 TLD 上的作用。\n"
                "如果這確實是本案書面授權的範圍，請附上依據重跑：\n"
                f"  --suffix {s} --authorization-ref '<案號或授權書檔名>'\n"
                "否則請改用精確網域（--target 主機名）或受限制的萬用字元（--wildcard）。")
        if s in ROOT_GOV_SUFFIXES:
            print(f"  [授權依據] {s} → {args.authorization_ref}")
            print(f"  [注意] {s} 底下的所有政府網域都會放行，該 TLD 的保護到此為止失效。")

    proposed = {
        "enabled": cur.get("enabled"),
        "rules": cur.get("rules") or [],
        "scope": new_scope,
    }

    print("== 擬變更 ==")
    print(f"  scope.{key} 新增：{args.target}")
    print(f"  其他設定完全不動（rules / enabled 沿用現值）")
    print(f"  未列入範圍的政府目標仍然照常阻擋")
    print()

    print("== 控制測試（寫入前必做）==")
    # 後綴沒有主機名可用，挑一個必然落在該後綴底下、且不指涉真實目標的探針主機，
    # 這樣「正向」才真的在測「這個後綴會放行」，而不是測到別的東西。
    if args.suffix:
        default_probe = f"https://probe-host{args.target}/"
    else:
        default_probe = f"https://{args.target}/"
    probe_value = args.probe_value or default_probe
    pos = probe(args.base_url, token, proposed, args.probe_tool,
                {args.probe_arg: probe_value}, f"正向：{probe_value} 應被放行")
    neg = probe(args.base_url, token, proposed, args.probe_tool,
                {args.probe_arg: f"https://{CONTROL_HOST}/"},
                f"負向：{CONTROL_HOST} 應仍被阻擋")

    if pos:
        die("正向控制失敗：加入範圍後目標仍被阻擋，不寫入")
    if not neg:
        die("負向控制失敗：未授權的政府目標竟然被放行了 —— "
            "這代表範圍設定會弱化保護，拒絕寫入")

    if not args.apply:
        print("\n[dry-run] 兩項控制都通過，未寫入。加 --apply 才會送出 PUT。")
        return 0

    print("\n== 寫入 ==")
    code, res = api(args.base_url, "/tool-guard", token, "PUT", proposed)
    if code != 200:
        die(f"PUT 失敗 HTTP {code}：{res}")
    print(f"  [OK] 已寫入並即時生效（不需重啟）")

    code, after = api(args.base_url, "/tool-guard", token)
    got = (after.get("scope") or {}).get(key) or []
    if args.target in got:
        print(f"  [OK] 回讀確認：scope.{key} 已包含 {args.target}")
    else:
        die(f"回讀確認失敗：{args.target} 不在 scope.{key} 中（實際：{got}）")
    print("\n[完成] 現在可以對該目標執行工具呼叫。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("已取消")
