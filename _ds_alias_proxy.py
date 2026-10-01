#!/usr/bin/env python3
"""Rewrite Nous DeepSeek slugs to official api.deepseek.com model ids."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

UPSTREAM = os.environ.get("DEEPSEEK_UPSTREAM", "https://api.deepseek.com").rstrip("/")
HOST = os.environ.get("DS_ALIAS_HOST", "127.0.0.1")
PORT = int(os.environ.get("DS_ALIAS_PORT", "18790"))

REWRITE = {
    "deepseek/deepseek-v4-pro-0813": "deepseek-v4-pro",
    "deepseek-v4-pro-0813": "deepseek-v4-pro",
    "deepseek/deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek/deepseek-v4-flash": "deepseek-flash",
    "deepseek-v4-flash": "deepseek-flash",
    "deepseek/deepseek-chat": "deepseek-flash",
}


def rewrite_model(name: str) -> str:
    return REWRITE.get((name or "").strip(), name)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[ds-alias] {self.address_string()} {fmt % args}")

    def _copy_headers(self) -> dict[str, str]:
        skip = {"host", "content-length", "connection", "accept-encoding"}
        out = {}
        for k, v in self.headers.items():
            if k.lower() not in skip:
                out[k] = v
        return out

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        if body and "application/json" in (self.headers.get("Content-Type") or ""):
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                payload = None
            if isinstance(payload, dict) and isinstance(payload.get("model"), str):
                old = payload["model"]
                payload["model"] = rewrite_model(old)
                if payload["model"] != old:
                    print(f"[ds-alias] model {old} -> {payload['model']}")
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        url = UPSTREAM + self.path
        req = Request(url, data=body if body else None, method=self.command, headers=self._copy_headers())
        try:
            with urlopen(req, timeout=600) as resp:
                ctype = resp.headers.get("Content-Type") or ""
                models = self.path.rstrip("/").endswith("/models")
                self.send_response(resp.status)
                hop = {"transfer-encoding", "connection", "content-encoding", "content-length"}
                for k, v in resp.headers.items():
                    if k.lower() in hop:
                        continue
                    self.send_header(k, v)
                if models or "text/event-stream" not in ctype:
                    raw = resp.read()
                    if models and raw:
                        try:
                            data = json.loads(raw.decode("utf-8"))
                            ids = {m.get("id") for m in (data.get("data") or []) if isinstance(m, dict)}
                            for mid in ("deepseek-v4-pro-0813", "deepseek/deepseek-v4-pro-0813"):
                                if mid not in ids:
                                    (data.setdefault("data", [])).append(
                                        {"id": mid, "object": "model", "owned_by": "deepseek"}
                                    )
                            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
                        except Exception:
                            pass
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                    return
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except HTTPError as e:
            err = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)
        except URLError as e:
            msg = json.dumps({"error": {"message": str(e.reason), "type": "proxy_error"}}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()


if __name__ == "__main__":
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[ds-alias] {HOST}:{PORT} -> {UPSTREAM}")
    httpd.serve_forever()
