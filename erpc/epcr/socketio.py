"""Engine.IO v4 / Socket.IO：免登入 websocket，走 SOCKS5。

握手後只存在預設 namespace `/`。server pingInterval=25000、pingTimeout=5000；
實測 server 不一定會主動 ping，客戶端每 20 秒送 `2` 可收到 `3` 保活。
"""
from __future__ import annotations

import json
import logging
import ssl
import time
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import urlparse

from .config import CFG, parse_proxy

log = logging.getLogger("epcr")

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None  # type: ignore[assignment]


def parse_eio_polling(payload: str) -> list[str]:
    """長度前綴 `n:packet` 或 EIO4 `\x1e` 分隔。"""
    if "\x1e" in payload:
        return [p for p in payload.split("\x1e") if p]
    packets: list[str] = []
    i = 0
    s = payload
    while i < len(s):
        if s[i] in " \r\n":
            i += 1
            continue
        nbuf = []
        while i < len(s) and s[i].isdigit():
            nbuf.append(s[i])
            i += 1
        if nbuf and i < len(s) and s[i] == ":":
            i += 1
            n = int("".join(nbuf))
            packets.append(s[i : i + n])
            i += n
        else:
            packets.append(s[i:])
            break
    return packets


def decode_packet(raw: str) -> dict[str, Any]:
    """解一則 Engine.IO/Socket.IO 文字包。"""
    if raw is None:
        return {"kind": "empty"}
    text = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
    if text == "":
        return {"kind": "empty"}
    if text == "2":
        return {"kind": "ping"}
    if text == "3":
        return {"kind": "pong"}
    if text == "2probe":
        return {"kind": "probe"}
    if text == "3probe":
        return {"kind": "probe_ack"}
    if text == "5":
        return {"kind": "upgrade"}
    if text == "6":
        return {"kind": "noop"}
    if text == "1":
        return {"kind": "close"}
    if text.startswith("0"):
        try:
            return {"kind": "open", "data": json.loads(text[1:])}
        except json.JSONDecodeError:
            return {"kind": "open", "data": text[1:]}
    if text.startswith("40"):
        rest = text[2:]
        if rest.startswith("/"):
            ns, _, payload = rest.partition(",")
            return {"kind": "ns_connect", "ns": ns, "data": payload}
        return {"kind": "ns_connect", "ns": "/", "data": rest}
    if text.startswith("44"):
        return {"kind": "ns_error", "data": text[2:]}
    if text.startswith("41"):
        return {"kind": "ns_disconnect", "data": text[2:]}
    if text.startswith("42"):
        rest = text[2:]
        ns = "/"
        if rest.startswith("/"):
            ns, _, rest = rest.partition(",")
        try:
            payload = json.loads(rest)
        except json.JSONDecodeError:
            return {"kind": "event", "ns": ns, "name": "?", "args": [rest], "raw": text}
        if isinstance(payload, list) and payload:
            name = str(payload[0])
            args = payload[1:]
            return {"kind": "event", "ns": ns, "name": name, "args": args, "raw": text}
        return {"kind": "event", "ns": ns, "name": "", "args": [payload], "raw": text}
    if text.startswith("43"):
        return {"kind": "ack", "data": text[2:]}
    return {"kind": "other", "raw": text}


def _ws_connect(url: str, proxy_url: str, origin: str, timeout: float):
    if websocket is None:
        raise RuntimeError("需要 websocket-client：pip install websocket-client python-socks")
    host, port, ptype = parse_proxy(proxy_url)
    parsed = urlparse(url)
    origin = origin or f"{parsed.scheme.replace('ws', 'http')}://{parsed.netloc}"
    return websocket.create_connection(
        url,
        sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
        http_proxy_host=host,
        http_proxy_port=port,
        proxy_type=ptype,
        timeout=timeout,
        header=[f"Origin: {origin}", f"User-Agent: {CFG.ua}"],
    )


class SocketIO:
    """長連線。yield decode_packet() 字典；自動 pong / 客戶端 ping。"""

    def __init__(
        self,
        url: str | None = None,
        *,
        proxy: str | None = None,
        origin: str | None = None,
        ping_interval: float | None = None,
    ) -> None:
        self.url = url or CFG.ws_url
        self.proxy = proxy or CFG.proxy
        self.origin = origin or CFG.origin
        self.ping_interval = CFG.ping_interval if ping_interval is None else ping_interval
        self.ws = None
        self.sid = ""
        self.connected_at = 0.0

    def connect(self) -> None:
        log.info("ws connect %s via %s", self.url, self.proxy)
        self.ws = _ws_connect(self.url, self.proxy, self.origin, timeout=25)
        self.ws.settimeout(self.ping_interval)
        self.connected_at = time.time()
        self.sid = ""

    def close(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def send(self, packet: str) -> None:
        if self.ws is None:
            raise RuntimeError("not connected")
        self.ws.send(packet)

    def _handle(self, raw: str) -> dict[str, Any]:
        pkt = decode_packet(raw)
        kind = pkt.get("kind")
        if kind == "ping":
            self.send("3")
            pkt["replied"] = "3"
        elif kind == "open":
            data = pkt.get("data") or {}
            if isinstance(data, dict):
                self.sid = str(data.get("sid") or "")
            self.send("40")
            pkt["replied"] = "40"
        return pkt

    def packets(self, deadline: float | None = None) -> Iterator[dict[str, Any]]:
        if self.ws is None:
            self.connect()
        assert self.ws is not None
        last_ping = time.time()
        while True:
            remain = None if deadline is None else deadline - time.time()
            if remain is not None and remain <= 0:
                return
            timeout = self.ping_interval if remain is None else min(self.ping_interval, max(0.3, remain))
            self.ws.settimeout(timeout)
            try:
                raw = self.ws.recv()
            except Exception as exc:
                name = type(exc).__name__
                if "Timeout" in name:
                    now = time.time()
                    if deadline is not None and now >= deadline:
                        return
                    if now - last_ping >= self.ping_interval:
                        try:
                            self.send("2")
                            last_ping = now
                            yield {"kind": "client_ping"}
                        except Exception as ping_exc:
                            yield {"kind": "disconnect", "error": str(ping_exc)}
                            return
                    continue
                yield {"kind": "disconnect", "error": f"{name}: {exc}"}
                return
            if raw is None or raw == "":
                yield {"kind": "disconnect", "error": "empty"}
                return
            text = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
            pkt = self._handle(text)
            if pkt.get("kind") == "pong":
                last_ping = time.time()
            yield pkt


def iter_events(
    *,
    on_packet: Callable[[dict[str, Any]], None] | None = None,
    urls: list[str] | None = None,
    proxies: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """斷線重連，只把 kind=event 的包往外丟（其餘可經 on_packet 看）。"""
    urls = urls or [CFG.ws_url, CFG.ws_url_alt]
    proxies = proxies or CFG.proxy_chain()
    backoff = 1.0
    idx = 0
    while True:
        url = urls[idx % len(urls)]
        proxy = proxies[idx % len(proxies)]
        client = SocketIO(url, proxy=proxy)
        try:
            client.connect()
            backoff = 1.0
            for pkt in client.packets():
                if on_packet:
                    on_packet(pkt)
                if pkt.get("kind") == "event":
                    yield pkt
                elif pkt.get("kind") == "disconnect":
                    log.warning("ws disconnect %s", pkt.get("error"))
                    break
        except Exception as exc:
            log.warning("ws fail %s %s: %s", url, proxy, exc)
        finally:
            client.close()
        idx += 1
        time.sleep(backoff)
        backoff = min(30.0, backoff * 2)
