#!/usr/bin/env python3
"""Nous free-tier models -> OpenAI-compatible local bridge.

Reads the Nous login Hermes already stores in ~/.hermes/auth.json. When the
inference key is near expiry, refreshes it by calling Hermes's own
resolve_nous_runtime_credentials in a short-lived subprocess (that path
persists the rotated refresh token). This process does not call the OAuth
token endpoint itself.

Listens on 127.0.0.1:18789.
Models:
  ornith/ornith-1.5-122b:free
  poolside/laguna-s-2.1:free
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error as urlerror
import urllib.request as urlrequest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer as Server

TOKEN = os.environ.get("NOUS_BRIDGE_TOKEN", "jysec-nous-bridge")
HOST = os.environ.get("NOUS_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("NOUS_BRIDGE_PORT", "18789"))
AUTH_PATH = os.environ.get("HERMES_AUTH_JSON", os.path.expanduser("~/.hermes/auth.json"))
HERMES_PY = os.environ.get(
    "HERMES_PYTHON",
    "/home/bossjy/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3",
)
HERMES_ROOT = os.environ.get("HERMES_ROOT", "/home/bossjy/.hermes/hermes-agent")
MIN_TTL_SECONDS = int(os.environ.get("NOUS_BRIDGE_MIN_TTL", "180"))

ORNITH = "ornith/ornith-1.5-122b:free"
LAGUNA = "poolside/laguna-s-2.1:free"
DEFAULT_MODEL = os.environ.get("NOUS_BRIDGE_DEFAULT_MODEL", ORNITH)
DEFAULT_BASE = "https://inference-api.nousresearch.com/v1"

ADVERTISED_MODELS = [ORNITH, LAGUNA, "ornith-1.5-122b:free", "laguna-s-2.1:free"]
MODEL_ALIASES = {
    "ornith": ORNITH,
    "ornith-1.5-122b:free": ORNITH,
    ORNITH: ORNITH,
    "laguna": LAGUNA,
    "laguna-s-2.1:free": LAGUNA,
    LAGUNA: LAGUNA,
}

FORWARDED_FIELDS = (
    "messages",
    "tools",
    "tool_choice",
    "temperature",
    "top_p",
    "max_tokens",
    "max_completion_tokens",
    "stop",
    "response_format",
    "parallel_tool_calls",
    "stream",
    "presence_penalty",
    "frequency_penalty",
    "seed",
    "user",
)

_cred_lock = threading.Lock()

_REFRESH_SNIPPET = r"""
import json, sys
sys.path.insert(0, %r)
import hermes_bootstrap
from hermes_cli.auth import resolve_nous_runtime_credentials
creds = resolve_nous_runtime_credentials(timeout_seconds=20, force_refresh=%s)
if not isinstance(creds, dict) or not creds.get("api_key") or not creds.get("base_url"):
    sys.exit(2)
json.dump({"api_key": creds["api_key"], "base_url": creds["base_url"]}, sys.stdout)
""" % (HERMES_ROOT, "True")


def resolve_model(requested: str | None) -> str:
    raw = (requested or "").strip()
    if not raw:
        return DEFAULT_MODEL
    return MODEL_ALIASES.get(raw, raw)


def _parse_expiry(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _read_stored() -> tuple[str, str] | None:
    try:
        with open(AUTH_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    nous = ((data.get("providers") or {}).get("nous") or {})
    key = nous.get("agent_key") or nous.get("access_token")
    base = nous.get("inference_base_url") or DEFAULT_BASE
    expires = _parse_expiry(nous.get("agent_key_expires_at") or nous.get("expires_at"))
    if not isinstance(key, str) or not key.strip() or not isinstance(base, str):
        return None
    if expires is not None:
        remaining = (expires - datetime.now(timezone.utc)).total_seconds()
        if remaining < MIN_TTL_SECONDS:
            return None
    return key, base.rstrip("/")


def _refresh() -> tuple[str, str]:
    python = HERMES_PY if os.path.exists(HERMES_PY) else sys.executable
    proc = subprocess.run(
        [python, "-c", _REFRESH_SNIPPET],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else f"exit {proc.returncode}"
        raise RuntimeError(f"Nous credential refresh failed: {tail}")
    payload = json.loads(proc.stdout)
    return str(payload["api_key"]), str(payload["base_url"]).rstrip("/")


def nous_credentials() -> tuple[str, str]:
    with _cred_lock:
        stored = _read_stored()
        if stored:
            return stored
        return _refresh()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"[nous-bridge] {self.address_string()} {fmt % args}", flush=True)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
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
        if path in ("/health", "/v1/health", ""):
            try:
                _, base = nous_credentials()
                return self._send_json(200, {
                    "status": "ok",
                    "default_model": DEFAULT_MODEL,
                    "upstream": base,
                })
            except Exception as exc:  # noqa: BLE001
                return self._send_json(503, {"status": "login_required", "message": str(exc)})
        if path in ("/v1/models", "/models"):
            if not self._auth_ok():
                return self._send_json(401, {"error": {"message": "invalid token"}})
            now = int(time.time())
            return self._send_json(200, {
                "object": "list",
                "data": [
                    {"id": model_id, "object": "model", "created": now, "owned_by": "nous"}
                    for model_id in ADVERTISED_MODELS
                ],
            })
        self._send_json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path not in ("/v1/chat/completions", "/chat/completions"):
            return self._send_json(404, {"error": {"message": f"unsupported path {path}"}})
        if not self._auth_ok():
            return self._send_json(401, {"error": {"message": "invalid token"}})

        length = int(self.headers.get("Content-Length", "0") or "0")
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send_json(400, {"error": {"message": "invalid json"}})
        if not req.get("messages"):
            return self._send_json(400, {"error": {"message": "no messages"}})

        requested = req.get("model") or DEFAULT_MODEL
        target = resolve_model(requested)
        payload = {key: req[key] for key in FORWARDED_FIELDS if key in req and req[key] is not None}
        payload["model"] = target
        started = time.time()
        try:
            status, body, content_type = self._post_upstream(payload)
        except Exception as exc:  # noqa: BLE001
            return self._send_json(502, {"error": {"message": f"nous free model error: {exc}"}})

        print(
            f"[nous-bridge] upstream status={status} req={requested}->target={target} "
            f"took={time.time()-started:.1f}s bytes={len(body)}",
            flush=True,
        )
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", content_type or "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _post_upstream(self, payload: dict) -> tuple[int, bytes, str]:
        last_status = 502
        last_body = b""
        last_type = "application/json"
        for attempt in range(2):
            if attempt:
                with _cred_lock:
                    api_key, base_url = _refresh()
            else:
                api_key, base_url = nous_credentials()
            request = urlrequest.Request(
                f"{base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlrequest.urlopen(request, timeout=300) as response:
                    return response.status, response.read(), response.headers.get("content-type") or "application/json"
            except urlerror.HTTPError as exc:
                last_status = exc.code
                last_body = exc.read()
                last_type = exc.headers.get("content-type") or "application/json"
                if last_status != 401 or attempt == 1:
                    return last_status, last_body, last_type
        return last_status, last_body, last_type


def main():
    server = Server((HOST, PORT), Handler)
    print(f"[nous-bridge] listening on {HOST}:{PORT} default_model={DEFAULT_MODEL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
