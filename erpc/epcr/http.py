"""curl + SOCKS5 HTTP。TLS 預設不驗證（上游憑證鏈在代理後常失敗）。"""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from .config import CFG

log = logging.getLogger("epcr")


def jq_like(params: dict[str, Any], prefix: str = "") -> list[tuple[str, str]]:
    """對齊 Angular `$httpParamSerializerJQLike`。"""
    items: list[tuple[str, str]] = []
    for key, value in params.items():
        path = f"{prefix}[{key}]" if prefix else str(key)
        if isinstance(value, dict):
            items.extend(jq_like(value, path))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                items.append((f"{path}[{index}]", _scalar(item)))
        elif value is None:
            continue
        else:
            items.append((path, _scalar(value)))
    return items


def _scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def encode_jq(params: dict[str, Any]) -> str:
    return urlencode(jq_like(params), quote_via=quote, safe="[]$")


@dataclass
class HttpResult:
    status: int
    body: bytes
    url: str
    error: str = ""
    header_text: str = ""

    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    def json(self) -> Any:
        text = self.text()
        if not text.strip():
            return None
        return json.loads(text)

    def header_map(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in (self.header_text or "").splitlines():
            if ":" not in raw or raw.lower().startswith("http/"):
                continue
            key, value = raw.split(":", 1)
            out[key.strip().lower()] = value.strip()
        return out

    def set_cookie_lines(self) -> list[str]:
        lines: list[str] = []
        for raw in (self.header_text or "").splitlines():
            if raw.lower().startswith("set-cookie:"):
                lines.append(raw.split(":", 1)[1].strip())
        return lines


def curl(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    data: bytes | None = None,
    cookie_jar: Path | None = None,
    cookie_in: Path | None = None,
    timeout: float | None = None,
    proxy: str | None = None,
    auth: bool = False,
    token: str | None = None,
    retries: int = 2,
) -> HttpResult:
    timeout = CFG.timeout if timeout is None else timeout
    proxy = CFG.proxy if proxy is None else proxy
    hdrs = {
        "User-Agent": CFG.ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    if headers:
        hdrs.update(headers)
    tok = (token or "").strip()
    if tok.lower().startswith("bearer "):
        tok = tok[7:].strip()
    if auth:
        if not tok:
            return HttpResult(401, b"", url, error="no_token")
        hdrs["Authorization"] = f"Bearer {tok}"

    body_bytes = data
    if json_body is not None:
        body_bytes = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json;charset=utf-8")

    last = HttpResult(0, b"", url, error="no_attempt")
    for attempt in range(retries + 1):
        with tempfile.NamedTemporaryFile(prefix="epcr-http-", delete=False) as tmp:
            out_path = Path(tmp.name)
        cmd = [
            "curl",
            "-sS",
            "-g",
            "-m",
            str(int(timeout)),
            "-X",
            method.upper(),
            "-D",
            "-",
            "-o",
            str(out_path),
            "-w",
            "\n__EPCR_HTTP__:%{http_code}",
        ]
        if not CFG.ssl_verify:
            cmd.append("-k")
        if proxy:
            cmd.extend(["--proxy", proxy])
        jar = cookie_jar or cookie_in
        if cookie_jar:
            cmd.extend(["-c", str(cookie_jar)])
        if cookie_in and cookie_in.exists():
            cmd.extend(["-b", str(cookie_in)])
        elif jar and jar.exists() and cookie_jar is None:
            cmd.extend(["-b", str(jar)])
        for key, value in hdrs.items():
            cmd.extend(["-H", f"{key}: {value}"])
        if body_bytes is not None:
            cmd.extend(["--data-binary", "@-"])
        cmd.append(url)
        try:
            proc = subprocess.run(
                cmd,
                input=body_bytes,
                capture_output=True,
                timeout=timeout + 5,
            )
            mixed = proc.stdout.decode("utf-8", "replace")
            status = 0
            header_blob = mixed
            marker = "\n__EPCR_HTTP__:"
            if marker in mixed:
                header_blob, code_s = mixed.rsplit(marker, 1)
                try:
                    status = int(code_s.strip() or "0")
                except ValueError:
                    status = 0
            body = out_path.read_bytes() if out_path.exists() else b""
            err = proc.stderr.decode("utf-8", "replace").strip()
            if proc.returncode != 0 and status == 0:
                last = HttpResult(0, body, url, error=err or f"curl_rc={proc.returncode}", header_text=header_blob)
            else:
                last = HttpResult(status or 0, body, url, error=err, header_text=header_blob)
                if status:
                    return last
        except Exception as exc:
            last = HttpResult(0, b"", url, error=str(exc))
        finally:
            try:
                out_path.unlink(missing_ok=True)
            except OSError:
                pass
        time.sleep(0.35 * (attempt + 1))
    return last


def as_list(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "rows", "result", "items", "DispatchRecords"):
            if isinstance(data.get(key), list):
                return data[key]
    return []
