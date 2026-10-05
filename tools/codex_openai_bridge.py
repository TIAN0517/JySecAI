#!/usr/bin/env python3
"""Codex ChatGPT-login → OpenAI-compatible local bridge.

將 OpenAI Codex CLI 的 ChatGPT 訂閱登入（Pro），包裝成
OpenAI /v1/chat/completions 相容的本地 HTTP 服務，讓 JySecAI 平台
以 `provider: openai_compatible` 頻道直接接入登入版模型。

設計要點：
- 僅監聽 127.0.0.1，對外不暴露。
- Bearer token 驗證（CODEX_BRIDGE_TOKEN，對應平台頻道 api_key）。
- 獨立 CODEX_HOME（~/.codex-chatgpt），與主 ~/.codex 的
  model_provider="jy"（Jy Gateway）配置隔離，確保走 ChatGPT 登入。
- 每次請求一顆 codex exec 子程序；threading.Lock 序列化，避免併發
  觸發訂閱速率限制。
- 支援 stream（SSE）與非 stream；stream 為合成回應（收完再切片送出）。
"""

import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CODEX_HOME = os.environ.get("CODEX_BRIDGE_CODEX_HOME", os.path.expanduser("~/.codex-chatgpt"))
SCRATCH = os.environ.get("CODEX_BRIDGE_SCRATCH", os.path.expanduser("~/.codex-bridge-scratch"))
TOKEN = os.environ.get("CODEX_BRIDGE_TOKEN", "jysec-codex-bridge")
PORT = int(os.environ.get("CODEX_BRIDGE_PORT", "18787"))
TIMEOUT = int(os.environ.get("CODEX_BRIDGE_TIMEOUT", "300"))

# 序列化 codex exec：Pro 訂閱併發有限，逐顆排隊最穩
CODEX_LOCK = threading.Lock()

MODEL_ID = "codex-default"  # 平台頻道 model 填這個 → 不帶 -m，用 codex 內建預設


def build_prompt(messages):
    """把 OpenAI messages 陣列壓成單一 prompt（codex exec 只吃一段文字）。"""
    parts = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"
            )
        if not content:
            continue
        tag = {"system": "System", "user": "User", "assistant": "Assistant", "tool": "Tool"}.get(role, role)
        parts.append(f"[{tag}]\n{content}")
    return "\n\n".join(parts)


def run_codex(prompt, model):
    cmd = ["codex", "exec", "--json", "--sandbox", "read-only", "--skip-git-repo-check", "-C", SCRATCH]
    if model and model != MODEL_ID:
        cmd += ["-m", model]
    # 關鍵：剝除 SOCKS/HTTP 代理變數——ALL_PROXY 會弄死 codex 對 chatgpt 後端的連線
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    env.update(CODEX_HOME=CODEX_HOME, RUST_LOG="error")
    with CODEX_LOCK:
        started = time.time()
        proc = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=TIMEOUT,
            env=env,
            cwd=SCRATCH,
        )
    out = proc.stdout.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()[-2000:]
        raise RuntimeError(err or f"codex exec exited {proc.returncode}")
    # 解析 --json 事件流：取所有 agent_message 文字串接
    texts = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") == "item.completed" and item.get("type") == "agent_message":
            texts.append(item.get("text", ""))
    content = "\n".join(t for t in texts if t).strip()
    if not content:
        raise RuntimeError(f"codex exec produced no agent_message; raw tail: {out[-500:]}")
    print(f"[codex-bridge] ok model={model or MODEL_ID} took={time.time()-started:.1f}s len={len(content)}", flush=True)
    return content


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"[codex-bridge] {self.address_string()} {fmt % args}", flush=True)

    def _auth_ok(self):
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {TOKEN}"

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models":
            if not self._auth_ok():
                return self._send_json(401, {"error": {"message": "invalid token"}})
            return self._send_json(200, {
                "object": "list",
                "data": [{"id": MODEL_ID, "object": "model", "owned_by": "chatgpt-login"}],
            })
        self._send_json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions":
            return self._send_json(404, {"error": {"message": "not found"}})
        if not self._auth_ok():
            return self._send_json(401, {"error": {"message": "invalid token"}})

        length = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send_json(400, {"error": {"message": "invalid json"}})

        model = req.get("model") or MODEL_ID
        stream = bool(req.get("stream"))
        prompt = build_prompt(req.get("messages"))
        if not prompt:
            return self._send_json(400, {"error": {"message": "no messages"}})

        try:
            content = run_codex(prompt, model)
        except subprocess.TimeoutExpired:
            return self._send_json(504, {"error": {"message": f"codex exec timed out after {TIMEOUT}s"}})
        except RuntimeError as exc:
            return self._send_json(502, {"error": {"message": f"codex exec failed: {exc}"}})
        except Exception as exc:  # noqa: BLE001
            return self._send_json(500, {"error": {"message": str(exc)}})

        now = int(time.time())
        cid = f"chatcmpl-codex-{now}"

        if not stream:
            return self._send_json(200, {
                "id": cid,
                "object": "chat.completion",
                "created": now,
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            })

        # 合成 SSE：完整回應切成角色框 + 內容 + 結束
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def sse(obj):
            self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8"))

        def chunk(delta):
            return {
                "id": cid, "object": "chat.completion.chunk", "created": now,
                "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
            }

        try:
            sse(chunk({"role": "assistant"}))
            sse(chunk({"content": content}))
            sse({"id": cid, "object": "chat.completion.chunk", "created": now, "model": model,
                 "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[codex-bridge] listening on 127.0.0.1:{PORT} CODEX_HOME={CODEX_HOME}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
