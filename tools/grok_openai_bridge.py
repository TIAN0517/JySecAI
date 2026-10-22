#!/usr/bin/env python3
"""Grok SuperGrok / X Premium+ subscription -> OpenAI-compatible local bridge.

Uses the xAI OAuth session stored by Hermes (~/.hermes/auth.json, provider
xai-oauth) and exposes /v1/chat/completions plus /v1/models on 127.0.0.1:18788
so JySecAI can call the subscription the same way it calls the Codex bridge.
"""

from __future__ import annotations

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

from agent.auxiliary_client import _build_xai_oauth_aux_client  # noqa: E402

TOKEN = os.environ.get("GROK_BRIDGE_TOKEN", "jysec-grok-bridge")
HOST = os.environ.get("GROK_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("GROK_BRIDGE_PORT", "18788"))
DEFAULT_MODEL = os.environ.get("GROK_BRIDGE_DEFAULT_MODEL", "grok-4.6")

ADVERTISED_MODELS = [
    "grok-default",
    "grok-4.6",
    "grok-4.5",
    "grok-4.3",
    "grok-4",
    "grok-build-latest",
    "grok-code-fast",
    "grok-composer",
]

MODEL_ALIASES = {
    "grok-default": DEFAULT_MODEL,
    "grok": DEFAULT_MODEL,
    "grok-4-latest": "grok-4.6",
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
        print(f"[grok-bridge] {self.address_string()} {fmt % args}", flush=True)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Requested-With")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _auth_ok(self) -> bool:
        auth = (self.headers.get("Authorization") or "").strip()
        if not TOKEN:
            return True
        return auth == f"Bearer {TOKEN}"

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
                    {"id": m, "object": "model", "created": 1760000000, "owned_by": "xai-subscription"}
                    for m in ADVERTISED_MODELS
                ],
            })
        if path in ("/health", "/v1/health", ""):
            client, _ = _build_xai_oauth_aux_client(DEFAULT_MODEL)
            return self._send_json(200, {
                "status": "ok" if client is not None else "login_required",
                "default_model": DEFAULT_MODEL,
                "subscription": client is not None,
            })
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
            client, _ = _build_xai_oauth_aux_client(target_model)
            if client is None:
                return self._send_json(503, {
                    "error": {
                        "message": "Grok subscription is not logged in. Run: hermes auth add xai-oauth --type oauth --no-browser",
                    },
                })
            call_kwargs = {"model": target_model, "messages": messages}
            if req.get("tools"):
                call_kwargs["tools"] = req["tools"]
            if req.get("tool_choice") is not None:
                call_kwargs["tool_choice"] = req["tool_choice"]
            resp = client.chat.completions.create(**call_kwargs)
        except Exception as exc:  # noqa: BLE001
            return self._send_json(502, {"error": {"message": f"grok subscription error: {exc}"}})

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
            f"[grok-bridge] ok req={requested_model}->target={target_model} "
            f"took={time.time()-started:.1f}s len={len(content)} tools={len(tool_calls or [])}",
            flush=True,
        )

        now = int(time.time())
        cid = f"chatcmpl-grok-{now}"
        if not stream:
            msg_dict = {"role": "assistant", "content": content if content or not tool_calls else None}
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
            return self._send_json(200, {
                "id": cid,
                "object": "chat.completion",
                "created": now,
                "model": requested_model,
                "choices": [{"index": 0, "message": msg_dict, "finish_reason": finish_reason}],
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


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[grok-bridge] listening on {HOST}:{PORT} default_model={DEFAULT_MODEL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
