#!/usr/bin/env python3
"""探針：用生產設定裡的正式憑證，重現審計 Agent 的 LLM 呼叫並隔離失敗原因。

為什麼需要這支
  審計 Agent 現在 100% 走「LLM 調用失敗，保守拒絕」，但 journal 的底層錯誤抓不到
  （-n 2000 翻不到那麼久以前）。這支直接重建 auditAgentReview 送出的請求，逐項
  拿掉參數重試，用回應碼差異定位是哪一個欄位讓服務端回錯。

安全
  - API key 只從設定檔讀取，只用於本機對該 base_url 發請求，永不印出。
  - 輸出只顯示 HTTP 狀態碼與回應前 500 字元；金鑰欄位以 <redacted> 取代。

用法
  sudo python3 probe-audit-llm.py --config /var/lib/jysecai/core/config.yaml
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request

import yaml

SECRET_KEYS = ("api_key", "apikey", "token", "secret", "password")


def die(msg: str, code: int = 2):
    print(f"[abort] {msg}", file=sys.stderr)
    sys.exit(code)


def resolve_audit_model(cfg: dict) -> dict:
    """鏡射 Go 的 AuditModelEffective()：audit_model 的空欄位才從主 openai 設定繼承。"""
    hitl = cfg.get("hitl") or {}
    am = hitl.get("audit_model") or {}
    main = cfg.get("openai") or {}
    out = dict(main)
    for k, v in (am or {}).items():
        # 對應 Go 的 strings.TrimSpace(x) != ""（internal/config/config.go:1299-1310）：
        # 純空白字串與未設定同義，都不覆寫主 openai 設定。
        if v is not None and str(v).strip():
            out[k] = v
    return out


def pick(cfg: dict, *names, default=""):
    for n in names:
        if cfg.get(n) not in (None, ""):
            return str(cfg[n]).strip()
    return default


def redact(text: str) -> str:
    for k in SECRET_KEYS:
        text = text.replace(k, "<redacted_key>")
    return text


def post(url: str, headers: dict, body: dict, timeout: int = 90) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in headers.items():
        req.add_header(k, v)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # 企業網路常見自我簽憑；此處只打已設定的供應商端點
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


def brief(body: str) -> str:
    try:
        j = json.loads(body)
    except Exception:  # noqa: BLE001
        return body[:500].replace("\n", " ")
    if isinstance(j, dict):
        if "content" in j and isinstance(j["content"], list):
            texts = [c.get("text", "") for c in j["content"] if isinstance(c, dict)]
            j = {**j, "content": " | ".join(t for t in texts if t)[:400]}
        if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
            m = j["choices"][0].get("message", {})
            j = {"choices[0].message.content": str(m.get("content"))[:400]}
    return json.dumps(j, ensure_ascii=False)[:500]


def main() -> int:
    ap = argparse.ArgumentParser(description="隔離審計 Agent LLM 呼叫失敗的原因")
    ap.add_argument("--config", default="/var/lib/jysecai/core/config.yaml")
    ap.add_argument("--url-only", action="store_true", help="只印端點與參數，不發請求")
    ap.add_argument("--force-openai", metavar="BASE_URL", default="",
                    help="改用 OpenAI 相容端點測試（用於驗證純改設定能否解掉，"
                         "例如 --force-openai https://api.minimaxi.com/v1）")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    m = resolve_audit_model(cfg)

    provider = pick(m, "provider", default="openai")
    base = pick(m, "base_url").rstrip("/")
    key = pick(m, "api_key")
    model = pick(m, "model")

    if args.force_openai:
        provider = "openai_compatible"
        base = args.force_openai.rstrip("/")
        print("（已強制改用 OpenAI 相容端點，僅供驗證設定層解法）")

    print(f"provider : {provider}")
    print(f"base_url : {base}")
    print(f"model    : {model}")
    print(f"api_key  : len={len(key)}  <redacted>")
    if not base or not key or not model:
        die("provider / base_url / api_key / model 有缺值，這本身就是 reject 原因（LLM 未配置）")

    hitl = cfg.get("hitl") or {}
    system = pick(hitl, "audit_agent_prompt")
    user = json.dumps({"hitlMode": "approval", "toolName": "exec",
                       "arguments": {"command": "id"}}, ensure_ascii=False, indent=2)
    print(f"system prompt: {len(system)} 字元\n")

    is_claude = provider.lower() in ("claude", "anthropic")
    if is_claude:
        url = base + "/v1/messages"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    else:
        url = base + "/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
    print(f"端點     : {url}")
    print(f"驗證標頭 : {list(headers)}\n")

    if is_claude:
        base_body = {
            "model": model,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "max_tokens": 1024,
        }
        variants = [
            ("A 照審計 Agent 現況（含 thinking）", {**base_body, "thinking": {"type": "disabled"}}),
            ("B 拿掉 thinking", dict(base_body)),
            ("C 拿掉 thinking 且放寬 max_tokens", {**base_body, "max_tokens": 4096}),
        ]
    else:
        base_body = {
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.1,
            "max_completion_tokens": 1024,
        }
        variants = [
            ("A 照審計 Agent 現況（含 thinking）", {**base_body, "thinking": {"type": "disabled"}}),
            ("B 拿掉 thinking", dict(base_body)),
            ("C 拿掉 thinking 且放寬輸出上限", {**base_body, "max_completion_tokens": 4096}),
        ]

    if args.url_only:
        for name, body in variants:
            limit = body.get("max_tokens") or body.get("max_completion_tokens")
            print(f"{name}\n  參數: {sorted(body)}  (輸出上限={limit})\n")
        return 0

    results = []
    for name, body in variants:
        code, text = post(url, headers, body)
        results.append((name, code, text))
        flag = "OK" if code == 200 else "FAIL"
        print(f"[{flag}] {name}  -> HTTP {code}")
        print(f"        {brief(text)}\n")

    ok = [r for r in results if r[1] == 200]
    bad = [r for r in results if r[1] != 200]
    print("== 判讀 ==")
    if not bad:
        print("三種變體都成功，代表憑證與端點正常。")
        print("那審計 Agent 的失敗就不在請求本身，請把 A 的回應內容貼出來 ——")
        print("重點是它有沒有回出可被 parseAuditAgentLLMContent 解析的 JSON。")
    elif not ok:
        print("三種變體都失敗，代表問題在憑證或端點，不是 thinking 參數：")
        print(f"  HTTP {bad[0][1]} -> {brief(bad[0][2])}")
    else:
        print(f"只有帶 thinking 的變體失敗 -> 確認是 thinking 參數不被接受。")
        for name, code, _ in bad:
            print(f"  {name}: HTTP {code}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
