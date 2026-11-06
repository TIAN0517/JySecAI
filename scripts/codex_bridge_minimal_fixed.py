#!/usr/bin/env python3
"""Codex subscription bridge — parent HTTP server, child worker via temp files.

Hermes Python wrappers can steal/re-exec stdin, so we never pass the request on stdin.
Streaming clients (Eino/OpenAI SDK) get SSE; tool_calls MUST be preserved or
Eino rejects the turn as empty_model_output.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get("CODEX_BRIDGE_TOKEN", "jysec-codex-bridge")
HOST = os.environ.get("CODEX_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("CODEX_BRIDGE_PORT", "18787"))
DEFAULT = os.environ.get("CODEX_BRIDGE_DEFAULT_MODEL", "gpt-daybreak-blue-latest")
WORKER = os.environ.get(
    "CODEX_BRIDGE_WORKER",
    "/home/bossjy/.local/bin/codex_bridge_worker.py",
)
PYTHON = os.environ.get("CODEX_BRIDGE_PYTHON", sys.executable)


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print("[codex-bridge]", fmt % args, flush=True)

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b)

    def _auth_ok(self) -> bool:
        return self.headers.get("Authorization", "") == f"Bearer {TOKEN}"

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if not self._auth_ok():
            return self._json(401, {"error": {"message": "invalid token"}})
        if path in ("/health", "/v1/health"):
            return self._json(
                200,
                {
                    "status": "ok",
                    "default_model": DEFAULT,
                    "mode": "worker-file",
                    "stream": "sse-from-completion",
                },
            )
        if path in ("/v1/models", "/models"):
            return self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {"id": DEFAULT, "object": "model", "owned_by": "chatgpt-subscription"},
                        {
                            "id": "gpt-daybreak-blue-latest",
                            "object": "model",
                            "owned_by": "chatgpt-subscription",
                        },
                        {"id": "gpt-6-sol", "object": "model", "owned_by": "chatgpt-subscription"},
                        {"id": "gpt-6-astra", "object": "model", "owned_by": "chatgpt-subscription"},
                        {"id": "codex-default", "object": "model", "owned_by": "chatgpt-subscription"},
                    ],
                },
            )
        return self._json(404, {"error": {"message": path}})

    def _run_worker(self, req: dict) -> tuple[int, dict]:
        env = os.environ.copy()
        base_pp = "/home/bossjy/.hermes/hermes-agent"
        env["PYTHONPATH"] = base_pp + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        in_path = out_path = err_path = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f_in:
                req_for_worker = dict(req)
                req_for_worker.pop("stream", None)
                json.dump(req_for_worker, f_in, ensure_ascii=False)
                in_path = f_in.name
            out_path = in_path + ".out"
            err_path = in_path + ".err"
            started = time.time()
            proc = subprocess.run(
                [PYTHON, WORKER, in_path, out_path],
                capture_output=True,
                timeout=300,
                env=env,
            )
            took = time.time() - started
            stderr = (proc.stderr or b"").decode("utf-8", "replace")
            if err_path and os.path.exists(err_path):
                try:
                    stderr += open(err_path, encoding="utf-8", errors="replace").read()
                except Exception:
                    pass
            if proc.returncode != 0 or not os.path.exists(out_path):
                print(
                    f"[codex-bridge] worker fail rc={proc.returncode} took={took:.1f}s {stderr[-800:]}",
                    flush=True,
                )
                return 502, {"error": {"message": f"codex worker failed: {stderr[-500:]}"}}
            with open(out_path, encoding="utf-8") as f_out:
                out = json.load(f_out)
            code = int(out.get("status", 200))
            body = out.get("body", out)
            msg = ((body.get("choices") or [{}])[0].get("message") or {})
            print(
                f"[codex-bridge] ok took={took:.1f}s status={code} "
                f"content_len={len(msg.get('content') or '')} "
                f"tools={len(msg.get('tool_calls') or [])} "
                f"finish={((body.get('choices') or [{}])[0].get('finish_reason'))}",
                flush=True,
            )
            return code, body
        finally:
            for p in (in_path, out_path, err_path):
                if p:
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    def _sse_from_completion(self, body: dict) -> None:
        now = int(body.get("created") or time.time())
        cid = body.get("id") or f"chatcmpl-codex-{now}"
        model = body.get("model") or DEFAULT
        choice0 = (body.get("choices") or [{}])[0]
        msg = choice0.get("message") or {}
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []
        finish = choice0.get("finish_reason") or ("tool_calls" if tool_calls else "stop")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def sse(obj):
            self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8"))

        def chunk(delta, finish_reason=None):
            return {
                "id": cid,
                "object": "chat.completion.chunk",
                "created": now,
                "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
            }

        try:
            sse(chunk({"role": "assistant"}))
            if content:
                sse(chunk({"content": content}))
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                idx = tc.get("index", 0)
                fn = tc.get("function") or {}
                sse(
                    chunk(
                        {
                            "tool_calls": [
                                {
                                    "index": idx,
                                    "id": tc.get("id") or f"call_{idx}",
                                    "type": tc.get("type") or "function",
                                    "function": {
                                        "name": fn.get("name") or "",
                                        "arguments": "",
                                    },
                                }
                            ]
                        }
                    )
                )
                args = fn.get("arguments") or "{}"
                if not isinstance(args, str):
                    args = json.dumps(args, ensure_ascii=False)
                sse(
                    chunk(
                        {
                            "tool_calls": [
                                {
                                    "index": idx,
                                    "function": {"arguments": args},
                                }
                            ]
                        }
                    )
                )
            sse(chunk({}, finish_reason=finish))
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if not self._auth_ok():
            return self._json(401, {"error": {"message": "invalid token"}})
        if path not in ("/v1/chat/completions", "/chat/completions"):
            return self._json(404, {"error": {"message": path}})
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) or b"{}"
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            return self._json(400, {"error": {"message": "invalid json"}})

        want_stream = bool(req.get("stream"))
        try:
            code, body = self._run_worker(req)
        except subprocess.TimeoutExpired:
            return self._json(504, {"error": {"message": "codex worker timeout"}})
        except Exception as e:
            return self._json(502, {"error": {"message": f"codex bridge error: {e}"}})

        if code != 200:
            return self._json(code, body if isinstance(body, dict) else {"error": {"message": str(body)}})

        if want_stream:
            return self._sse_from_completion(body if isinstance(body, dict) else {})
        return self._json(200, body)


print(f"[codex-bridge] listening on {HOST}:{PORT} worker={WORKER} default={DEFAULT}", flush=True)
ThreadingHTTPServer((HOST, PORT), H).serve_forever()
