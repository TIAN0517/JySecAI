#!/usr/bin/env python3
"""
Anthropic Messages API → OpenAI Chat Completions 相容層（shim）
-------------------------------------------------------------------------------
為什麼需要這個：
    pent_claude_agent 使用 Claude Agent SDK，而 SDK 只會講 Anthropic 格式
    （POST /v1/messages）。但平台既有的模型 relay（127.0.0.1:18787 / :18788）
    只提供 OpenAI 格式（/v1/chat/completions）。本 shim 在兩者之間做轉換，
    讓 pent agent 直接沿用平台已配額的 relay，不需外掛任何付費 API key。

做什麼：
    POST /v1/messages          Anthropic Messages（含 stream）→ OpenAI → Anthropic
    POST /v1/messages/count_tokens  粗略 token 估算
    GET  /v1/models            回報上游模型
    GET  /health               健康檢查（systemd / watchdog 用）

安全邊界：
    - 僅綁 127.0.0.1，不對外暴露。
    - 不記錄、不輸出上游 API key；key 只從平台 config.yaml 讀入記憶體。
    - 只轉送 /v1/chat/completions 這一支路徑，不做任意 URL 代理。

設定（皆可用環境變數覆寫）：
    SHIM_BIND           監聽位址，預設 127.0.0.1
    SHIM_PORT           監聽埠，預設 18790
    SHIM_CONFIG         平台 config.yaml 路徑（預設 /var/lib/jysecai/core/config.yaml）
    SHIM_CHANNEL        取用 ai.channels 哪一組 provider，預設 codex-pro
    SHIM_UPSTREAM_URL   直接指定上游 root（例 http://127.0.0.1:18787），優先於 channel
    SHIM_UPSTREAM_KEY   直接指定上游 key，優先於 channel
    SHIM_UPSTREAM_MODEL 直接指定上游模型，優先於 channel
    SHIM_LOG            設 1 開啟除錯日誌（不記錄 key）
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND = os.environ.get("SHIM_BIND", "127.0.0.1")
PORT = int(os.environ.get("SHIM_PORT", "18790"))
CONFIG_PATH = os.environ.get("SHIM_CONFIG", "/var/lib/jysecai/core/config.yaml")
CHANNEL = os.environ.get("SHIM_CHANNEL", "codex-pro,gpt-daybreak,grok-code-fast,grok-sub")
RETRIES = max(1, int(os.environ.get("SHIM_RETRIES", "2")))
LOG = os.environ.get("SHIM_LOG", "0") not in ("0", "", "false", "False")

_lock = threading.Lock()
_upstream: list[dict] = []


def _log(msg: str) -> None:
    if LOG:
        print(f"[anthropic-shim] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 上游設定載入
# ---------------------------------------------------------------------------
def load_upstream() -> list[dict]:
    """從平台 config.yaml 的 ai.channels 讀出上游 relay 候選清單。

    relay 背後是一組上游帳號池，會輪替；其中某些帳號可能暫時失效
    （例如 codex 訂閱要求 hardware key），回 502。因此這裡保留多個
    候選通道，讓請求層可以重試並往下一個通道退避。
    """
    cands: list[dict] = []

    url = os.environ.get("SHIM_UPSTREAM_URL", "")
    key = os.environ.get("SHIM_UPSTREAM_KEY", "")
    model = os.environ.get("SHIM_UPSTREAM_MODEL", "")
    if url and key and model:
        cands.append({"name": "explicit", "url": url.rstrip("/"), "key": key, "model": model})

    names = [n.strip() for n in (os.environ.get("SHIM_CHANNELS") or CHANNEL).split(",") if n.strip()]
    try:
        import yaml  # type: ignore

        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}
        channels = ((cfg.get("ai") or {}).get("channels")) or {}
        for n in names:
            ch = channels.get(n) or {}
            u = str(ch.get("base_url", "")).rsplit("/v1", 1)[0]
            k = str(ch.get("api_key", ""))
            m = str(ch.get("model", ""))
            if u and k and m:
                cands.append({"name": n, "url": u.rstrip("/"), "key": k, "model": m})
    except Exception as exc:  # pragma: no cover - 設定異常時明確報錯
        _log(f"load_upstream failed: {exc}")

    return cands


# ---------------------------------------------------------------------------
# Anthropic → OpenAI
# ---------------------------------------------------------------------------
def _image_part(block: dict) -> dict | None:
    src = block.get("source") or {}
    st = src.get("type")
    if st == "base64":
        mt = src.get("media_type", "image/png")
        data = src.get("data", "")
        if not data:
            return None
        return {"type": "image_url", "image_url": {"url": f"data:{mt};base64,{data}"}}
    if st == "url" and src.get("url"):
        return {"type": "image_url", "image_url": {"url": src["url"]}}
    return None


def _content_parts(content) -> list | str:
    """把 Anthropic content 轉成 OpenAI content（純字串或 parts 陣列）。"""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    texts: list[str] = []
    images: list[dict] = []
    for b in content:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            texts.append(b.get("text", ""))
        elif t == "image":
            part = _image_part(b)
            if part:
                images.append(part)
    if not images:
        return "".join(texts)
    parts: list[dict] = []
    if texts:
        parts.append({"type": "text", "text": "".join(texts)})
    parts.extend(images)
    return parts


def anthropic_to_openai_messages(req: dict) -> list[dict]:
    msgs: list[dict] = []

    system = req.get("system")
    if system:
        sys_content = _content_parts(system)
        if sys_content:
            msgs.append({"role": "system", "content": sys_content})

    for m in req.get("messages") or []:
        role = m.get("role", "user")
        content = m.get("content")
        if isinstance(content, str):
            msgs.append({"role": role, "content": content})
            continue
        if not isinstance(content, list):
            continue

        texts: list[str] = []
        images: list[dict] = []
        tool_calls: list[dict] = []
        tool_results: list[dict] = []

        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                texts.append(b.get("text", ""))
            elif t == "image":
                part = _image_part(b)
                if part:
                    images.append(part)
            elif t == "tool_use":
                tool_calls.append(
                    {
                        "id": b.get("id") or f"call_{uuid.uuid4().hex[:24]}",
                        "type": "function",
                        "function": {
                            "name": b.get("name", ""),
                            "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False),
                        },
                    }
                )
            elif t == "tool_result":
                tool_results.append(b)

        # tool_result 必須先於同回合的 user 文字送出（OpenAI 格式要求）
        for tr in tool_results:
            inner = _content_parts(tr.get("content"))
            if not isinstance(inner, str):
                inner = json.dumps(inner, ensure_ascii=False)
            msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": tr.get("tool_use_id", ""),
                    "content": inner,
                }
            )

        if texts or images or tool_calls:
            out: dict = {"role": role}
            if images:
                parts: list[dict] = []
                if texts:
                    parts.append({"type": "text", "text": "".join(texts)})
                parts.extend(images)
                out["content"] = parts
            else:
                out["content"] = "".join(texts)
            if tool_calls:
                out["tool_calls"] = tool_calls
            msgs.append(out)

    return msgs


def map_tool_choice(tc) -> object:
    if not isinstance(tc, dict):
        return "auto"
    t = tc.get("type")
    if t == "any":
        return "required"
    if t == "tool" and tc.get("name"):
        return {"type": "function", "function": {"name": tc["name"]}}
    if t == "none":
        return "none"
    return "auto"


def build_openai_request(req: dict, upstream_model: str) -> dict:
    out: dict = {
        "model": upstream_model,
        "messages": anthropic_to_openai_messages(req),
    }
    if req.get("max_tokens"):
        out["max_tokens"] = int(req["max_tokens"])
    for src, dst in (("temperature", "temperature"), ("top_p", "top_p")):
        if req.get(src) is not None:
            out[dst] = req[src]
    if req.get("stop_sequences"):
        out["stop"] = req["stop_sequences"]

    tools = []
    for t in req.get("tools") or []:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
        )
    if tools:
        out["tools"] = tools
        out["tool_choice"] = map_tool_choice(req.get("tool_choice"))

    return out


# ---------------------------------------------------------------------------
# OpenAI → Anthropic
# ---------------------------------------------------------------------------
_STOP_MAP = {
    "stop": "end_turn",
    "length": "max_tokens",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "content_filter": "end_turn",
}


def map_stop(reason) -> str:
    return _STOP_MAP.get(str(reason or "stop"), "end_turn")


def _parse_tool_args(raw: str):
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"_raw": raw}


def openai_to_anthropic_message(resp: dict, upstream_model: str) -> dict:
    choices = resp.get("choices") or [{}]
    ch = choices[0] or {}
    msg = ch.get("message") or {}

    content: list[dict] = []
    text = msg.get("content")
    if text:
        content.append({"type": "text", "text": text})
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function") or {}
        content.append(
            {
                "type": "tool_use",
                "id": tc.get("id") or f"toolu_{uuid.uuid4().hex[:24]}",
                "name": fn.get("name", ""),
                "input": _parse_tool_args(fn.get("arguments") or ""),
            }
        )

    usage = resp.get("usage") or {}
    return {
        "id": resp.get("id") or f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "model": upstream_model,
        "content": content,
        "stop_reason": map_stop(ch.get("finish_reason")),
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0) or 0,
            "output_tokens": usage.get("completion_tokens", 0) or 0,
        },
    }


def _sse(event: str, data: dict) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


class _StreamState:
    """追蹤 Anthropic content block 的開合狀態。"""

    def __init__(self, upstream_model: str):
        self.msg_id = f"msg_{uuid.uuid4().hex[:24]}"
        self.upstream_model = upstream_model
        self.started = False
        self.next_index = 0
        self.text_index: int | None = None
        self.tool_index: dict[int, int] = {}
        self.usage = {"input_tokens": 0, "output_tokens": 0}
        self.stop_reason = "end_turn"
        self.text_chars = 0
        self.tool_chars = 0

    def start_message(self, out) -> None:
        if self.started:
            return
        self.started = True
        out.append(
            _sse(
                "message_start",
                {
                    "type": "message_start",
                    "message": {
                        "id": self.msg_id,
                        "type": "message",
                        "role": "assistant",
                        "model": self.upstream_model,
                        "content": [],
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                },
            )
        )

    def open_text(self, out) -> None:
        if self.text_index is not None:
            return
        self.start_message(out)
        self.text_index = self.next_index
        self.next_index += 1
        out.append(
            _sse(
                "content_block_start",
                {
                    "type": "content_block_start",
                    "index": self.text_index,
                    "content_block": {"type": "text", "text": ""},
                },
            )
        )

    def open_tool(self, out, call_index: int, call_id: str, name: str) -> None:
        self.start_message(out)
        if call_index in self.tool_index:
            return
        idx = self.next_index
        self.next_index += 1
        self.tool_index[call_index] = idx
        out.append(
            _sse(
                "content_block_start",
                {
                    "type": "content_block_start",
                    "index": idx,
                    "content_block": {
                        "type": "tool_use",
                        "id": call_id or f"toolu_{uuid.uuid4().hex[:24]}",
                        "name": name,
                        "input": {},
                    },
                },
            )
        )

    def close_all(self, out) -> None:
        if self.text_index is not None:
            out.append(_sse("content_block_stop", {"type": "content_block_stop", "index": self.text_index}))
            self.text_index = None
        for idx in self.tool_index.values():
            out.append(_sse("content_block_stop", {"type": "content_block_stop", "index": idx}))
        self.tool_index = {}

    def finish(self, out) -> None:
        self.close_all(out)
        out.append(
            _sse(
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": self.stop_reason, "stop_sequence": None},
                    "usage": {"output_tokens": self.usage["output_tokens"]},
                },
            )
        )
        out.append(_sse("message_stop", {"type": "message_stop"}))


def transform_stream(chunks: list[dict], upstream_model: str) -> list[bytes]:
    """把 OpenAI SSE chunk 轉成 Anthropic SSE 事件序列。"""
    state = _StreamState(upstream_model)
    out: list[bytes] = []
    tool_names: dict[int, str] = {}
    tool_ids: dict[int, str] = {}

    for obj in chunks:
        if obj.get("usage"):
            u = obj["usage"]
            state.usage["input_tokens"] = u.get("prompt_tokens", 0) or 0
            state.usage["output_tokens"] = u.get("completion_tokens", 0) or 0

        choices = obj.get("choices") or []
        if not choices:
            continue
        ch = choices[0] or {}
        delta = ch.get("delta") or {}

        text = delta.get("content")
        if isinstance(text, list):  # 某些轉送層會回傳 parts
            text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
        if text:
            state.open_text(out)
            state.text_chars += len(text)
            out.append(
                _sse(
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": state.text_index,
                        "delta": {"type": "text_delta", "text": text},
                    },
                )
            )

        for tc in delta.get("tool_calls") or []:
            ci = tc.get("index", 0)
            fn = tc.get("function") or {}
            if tc.get("id"):
                tool_ids[ci] = tc["id"]
            if fn.get("name"):
                tool_names[ci] = fn["name"]
            state.open_tool(out, ci, tool_ids.get(ci, ""), tool_names.get(ci, ""))
            args_frag = fn.get("arguments")
            if args_frag:
                state.tool_chars += len(args_frag)
                out.append(
                    _sse(
                        "content_block_delta",
                        {
                            "type": "content_block_delta",
                            "index": state.tool_index[ci],
                            "delta": {"type": "input_json_delta", "partial_json": args_frag},
                        },
                    )
                )

        if ch.get("finish_reason"):
            state.stop_reason = map_stop(ch.get("finish_reason"))

    if state.usage["output_tokens"] == 0 and (state.text_chars or state.tool_chars):
        # 上游 stream 模式不一定回 usage，用字元數粗估避免回 0
        state.usage["output_tokens"] = max(1, (state.text_chars + state.tool_chars) // 4)

    state.finish(out)
    return out


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "jysec-anthropic-shim/1.0"

    def log_message(self, fmt, *args):  # 關掉預設 stderr 雜訊
        if LOG:
            _log(fmt % args)

    # -- helpers ---------------------------------------------------------
    def _send_json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, code: int, message: str) -> None:
        self._send_json(code, {"type": "error", "error": {"type": "invalid_request_error", "message": message}})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # -- routes ----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/health", "/healthz"):
            self._send_json(
                200,
                {
                    "status": "ok",
                    "upstreams": [{"name": c["name"], "url": c["url"], "model": c["model"]} for c in _upstream],
                },
            )
        elif path == "/v1/models":
            self._send_json(
                200,
                {
                    "data": [
                        {"id": c["model"], "type": "model", "display_name": f"{c['name']}:{c['model']}"}
                        for c in _upstream
                    ],
                    "has_more": False,
                },
            )
        else:
            self._send_error_json(404, f"unknown path {path}")

    def do_POST(self):  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/v1/messages/count_tokens":
            req = self._read_body()
            text = json.dumps(req.get("messages") or [], ensure_ascii=False)
            self._send_json(200, {"input_tokens": max(1, len(text) // 4)})
            return

        if path != "/v1/messages":
            self._send_error_json(404, f"unknown path {path}")
            return

        if not self.headers.get("x-api-key") and not self.headers.get("authorization"):
            self._send_error_json(401, "missing x-api-key")
            return

        req = self._read_body()

        # 依序嘗試候選上游；單一通道失敗（上游帳號輪替、502、連線錯誤）時
        # 先重試，失敗就退到下一個通道，避免整個請求直接失敗。
        raw: bytes | None = None
        used: dict | None = None
        errors: list[str] = []
        for cand in _upstream:
            openai_req = build_openai_request(req, cand["model"])
            openai_req["stream"] = bool(req.get("stream"))
            if openai_req["stream"]:
                openai_req["stream_options"] = {"include_usage": True}

            target = f"{cand['url']}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cand['key']}",
            }
            for attempt in range(1, RETRIES + 1):
                try:
                    up = urllib.request.Request(
                        target, data=json.dumps(openai_req).encode("utf-8"), headers=headers
                    )
                    with urllib.request.urlopen(up, timeout=180) as resp:
                        raw = resp.read()
                    used = cand
                    break
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", "replace")[:300]
                    errors.append(f"{cand['name']}#{attempt} HTTP {exc.code}")
                    _log(f"upstream {cand['name']} HTTP {exc.code} (try {attempt}/{RETRIES}): {detail[:200]}")
                    if exc.code < 500 and exc.code != 429:
                        break  # 4xx（429 除外）換通道也沒用
                    time.sleep(1.2 * attempt)
                except Exception as exc:
                    errors.append(f"{cand['name']}#{attempt} {type(exc).__name__}")
                    _log(f"upstream {cand['name']} failure (try {attempt}/{RETRIES}): {exc}")
                    time.sleep(1.2 * attempt)
            if raw is not None:
                break

        if raw is None or used is None:
            try:
                self._send_error_json(502, "all upstreams failed: " + " | ".join(errors)[:280])
            except Exception:
                pass  # client 可能已斷線
            return

        upstream_model = used["model"]
        _log(f"messages model={req.get('model')} -> upstream={used['name']}/{upstream_model} stream={openai_req['stream']}")

        if not openai_req["stream"]:
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                self._send_error_json(502, f"bad upstream json: {exc}")
                return
            self._send_json(200, openai_to_anthropic_message(obj, upstream_model))
            return

        # ---- streaming ----
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        chunks: list[dict] = []
        for line in raw.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line or line.startswith(":") or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                chunks.append(json.loads(payload))
            except Exception:
                continue

        for event in transform_stream(chunks, upstream_model):
            try:
                self.wfile.write(event)
                self.wfile.flush()
            except Exception:
                break
        self.close_connection = True


def main() -> None:
    global _upstream
    _upstream = load_upstream()
    if not _upstream:
        print("anthropic-shim: no upstream channels configured", file=sys.stderr)
        sys.exit(2)

    srv = ThreadingHTTPServer((BIND, PORT), Handler)
    srv.daemon_threads = True
    for c in _upstream:
        _log(f"upstream candidate: {c['name']} -> {c['url']} model={c['model']}")
    print(
        "anthropic-shim listening on "
        f"{BIND}:{PORT} -> " + ", ".join(f"{c['name']}:{c['model']}" for c in _upstream),
        flush=True,
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
