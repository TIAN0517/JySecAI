#!/usr/bin/env python3
"""Codex ChatGPT-Subscription -> OpenAI-compatible local bridge (127.0.0.1:18787).

Uses Hermes's live ChatGPT OAuth subscription credentials (~/.hermes/auth.json)
via agent.auxiliary_client._build_codex_client, exposing a standard OpenAI
/v1/chat/completions and /v1/models HTTP service for Cursor and JySecAI.
"""

from __future__ import annotations

import ipaddress
import os
import sys

HERMES_PY = "/home/bossjy/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3"
if os.path.exists(HERMES_PY) and os.path.realpath(sys.executable) != os.path.realpath(HERMES_PY):
    os.execv(HERMES_PY, [HERMES_PY, __file__, *sys.argv[1:]])

sys.path.insert(0, "/home/bossjy/.hermes/hermes-agent")
import hermes_bootstrap  # noqa: E402,F401

import json  # noqa: E402
import time  # noqa: E402
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402
from agent.auxiliary_client import _build_codex_client  # noqa: E402

TOKEN = os.environ.get("CODEX_BRIDGE_TOKEN", "").strip()
HOST = os.environ.get("CODEX_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("CODEX_BRIDGE_PORT", "18787"))
DEFAULT_MODEL = os.environ.get("CODEX_BRIDGE_DEFAULT_MODEL", "gpt-6-astra")
# 允許跨站存取的來源清單（逗號分隔）。預設空 = 完全不送 CORS 標頭。
#
# 這個 bridge 是給平台後端呼叫的本機服務。通配 CORS 等於讓任何網站都能
# 跨站讀取並驅動這個付費訂閱（token 早期還是寫死的預設值）。要跨站就明確
# 列出來源，不要通配。
CORS_ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get("CODEX_BRIDGE_CORS_ORIGIN", "").split(",")
    if origin.strip()
}

ADVERTISED_MODELS = [
    "gpt-6-astra",
    "gpt-6-astra-900k",
    "gpt-6.1-sol",
    "gpt-6.1-sol-900k",
    "gpt-daybreak-blue-latest",
    "gpt-daybreak-blue-latest-900k",
    "gpt-6-sol",
    "gpt-6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "codex-default",
]

MODEL_ALIASES = {
    "codex-default": DEFAULT_MODEL,
    "gpt-5.4": "gpt-6.1-sol",
    "gpt-5.4-mini": "gpt-6-luna",
    "gpt-5.5": "gpt-6.1-sol",
    "gpt-4o": "gpt-6.1-sol",
}


def resolve_model(requested: str | None) -> str:
    raw = (requested or "").strip()
    if not raw:
        return DEFAULT_MODEL
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]
    return MODEL_ALIASES.get(raw, raw)


def serialize_tool_calls(tool_calls) -> list[dict] | None:
    if not tool_calls:
        return None
    out = []
    for idx, tc in enumerate(tool_calls):
        fn = getattr(tc, "function", None)
        out.append({
            "index": idx,
            "id": getattr(tc, "id", None) or f"call_{idx}",
            "type": "function",
            "function": {
                "name": getattr(fn, "name", "") if fn else "",
                "arguments": getattr(fn, "arguments", "{}") if fn else "{}",
            },
        })
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"[codex-bridge] {self.address_string()} {fmt % args}", flush=True)

    def _cors_headers(self):
        # 只在明確列出的來源才送 CORS 標頭；預設不送任何 CORS 標頭。
        origin = (self.headers.get("Origin") or "").strip()
        if not origin or origin not in CORS_ALLOWED_ORIGINS:
            return
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Requested-With")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _auth_ok(self) -> bool:
        auth = (self.headers.get("Authorization") or "").strip()
        # TOKEN 沒有預設值也沒有空值放行：啟動時就會拒絕沒有 token 的情況。
        return bool(TOKEN) and auth == f"Bearer {TOKEN}"

    def _send_json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in ("/v1/models", "/models"):
            if not self._auth_ok():
                return self._send_json(401, {"error": {"message": "invalid token"}})
            return self._send_json(200, {
                "object": "list",
                "data": [
                    {"id": m, "object": "model", "created": 1760000000, "owned_by": "chatgpt-subscription"}
                    for m in ADVERTISED_MODELS
                ],
            })
        if path in ("/health", "/v1/health", ""):
            return self._send_json(200, {"status": "ok", "default_model": DEFAULT_MODEL})
        self._send_json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path not in ("/v1/chat/completions", "/chat/completions"):
            return self._send_json(404, {"error": {"message": f"unsupported path {path}"}})
        if not self._auth_ok():
            return self._send_json(401, {"error": {"message": "invalid token"}})

        length = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send_json(400, {"error": {"message": "invalid json"}})

        requested_model = req.get("model") or DEFAULT_MODEL
        target_model = resolve_model(requested_model)
        stream = bool(req.get("stream"))
        messages = req.get("messages") or []
        if not messages:
            return self._send_json(400, {"error": {"message": "no messages"}})

        started = time.time()
        try:
            client, _ = _build_codex_client(target_model)
            if client is None:
                return self._send_json(503, {"error": {"message": "ChatGPT subscription credentials unavailable in Hermes"}})
            call_kwargs = {
                "model": target_model,
                "messages": messages,
            }
            if req.get("tools"):
                call_kwargs["tools"] = req["tools"]
            if req.get("tool_choice") is not None:
                call_kwargs["tool_choice"] = req["tool_choice"]
            if req.get("reasoning_effort"):
                call_kwargs["extra_body"] = {"reasoning": {"effort": req["reasoning_effort"]}}
            resp = client.chat.completions.create(**call_kwargs)
        except Exception as exc:  # noqa: BLE001
            return self._send_json(502, {"error": {"message": f"codex subscription error: {exc}"}})

        choice0 = resp.choices[0]
        msg = choice0.message
        content = getattr(msg, "content", None) or ""
        tool_calls = serialize_tool_calls(getattr(msg, "tool_calls", None))
        finish_reason = getattr(choice0, "finish_reason", None) or ("tool_calls" if tool_calls else "stop")
        usage_obj = getattr(resp, "usage", None)
        usage = {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage_obj, "completion_tokens", 0) or 0,
            "total_tokens": getattr(usage_obj, "total_tokens", 0) or 0,
        }
        print(
            f"[codex-bridge] ok req={requested_model}->target={target_model} "
            f"took={time.time()-started:.1f}s len={len(content)} tools={len(tool_calls or [])}",
            flush=True,
        )

        now = int(time.time())
        cid = f"chatcmpl-codex-{now}"

        if not stream:
            msg_dict = {"role": "assistant", "content": content if content or not tool_calls else None}
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
            return self._send_json(200, {
                "id": cid,
                "object": "chat.completion",
                "created": now,
                "model": requested_model,
                "choices": [{
                    "index": 0,
                    "message": msg_dict,
                    "finish_reason": finish_reason,
                }],
                "usage": usage,
            })

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def sse(obj):
            self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8"))

        def chunk(delta, finish=None):
            return {
                "id": cid,
                "object": "chat.completion.chunk",
                "created": now,
                "model": requested_model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
            }

        try:
            sse(chunk({"role": "assistant"}))
            if content:
                sse(chunk({"content": content}))
            if tool_calls:
                sse(chunk({"tool_calls": tool_calls}))
            sse(chunk({}, finish=finish_reason))
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def is_loopback_host(host: str) -> bool:
    """HOST 是否是 loopback 位址（127.0.0.0/8、::1 或 localhost）。"""
    h = (host or "").strip().lower()
    if h in ("localhost", "::1", "[::1]"):
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def main():
    # 啟動前的安全閘門：
    #   1. 沒有明確 token 就不啟動 —— 舊版預設 token 是寫死的常數，等於公開的。
    #   2. 非 loopback 位址要另外明確 opt-in —— 這是付費訂閱的代理服務。
    if not TOKEN:
        print(
            "[codex-bridge] REFUSING TO START: CODEX_BRIDGE_TOKEN is not set. "
            "Generate a strong token and export it before starting "
            "(e.g. `export CODEX_BRIDGE_TOKEN=$(openssl rand -hex 32)`).",
            flush=True,
        )
        raise SystemExit(2)
    if not is_loopback_host(HOST) and os.environ.get("CODEX_BRIDGE_ALLOW_NON_LOOPBACK", "") != "1":
        print(
            f"[codex-bridge] REFUSING TO START: HOST={HOST} is not a loopback address. "
            "Set CODEX_BRIDGE_ALLOW_NON_LOOPBACK=1 to override.",
            flush=True,
        )
        raise SystemExit(2)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[codex-bridge] listening on {HOST}:{PORT} default_model={DEFAULT_MODEL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
