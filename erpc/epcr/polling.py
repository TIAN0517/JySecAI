"""Engine.IO xhr-polling：handshake 拿 sid，再 GET 長輪詢 30 秒抓 packet。

curl 走 --socks5-hostname（與已驗證指令相同）。
收到 ping `2` 立刻 POST pong `3`；必要時用同一個 sid 升 websocket。
"""
from __future__ import annotations

import json
import logging
import ssl
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from .config import CFG, parse_proxy
from .socketio import decode_packet, parse_eio_polling

log = logging.getLogger("epcr")

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None  # type: ignore[assignment]


def _socks_host_port(proxy: str | None = None) -> tuple[str, int]:
    host, port, _ = parse_proxy(proxy or CFG.proxy)
    return host, port


def _t() -> str:
    return format(int(time.time() * 1000), "x")


def curl_raw(
    url: str,
    *,
    method: str = "GET",
    body: str | None = None,
    timeout: float = 30.0,
    cookie_jar: Path | None = None,
    origin: str | None = None,
) -> tuple[int, str, str]:
    """回 (http_code, body, stderr)。長輪詢用 -N 不緩衝。"""
    import subprocess

    host, port = _socks_host_port()
    origin = origin or CFG.origin
    cmd = [
        "curl",
        "-sk",
        "-N",
        "--socks5-hostname",
        f"{host}:{port}",
        "-m",
        str(int(timeout)),
        "-X",
        method,
        "-H",
        "Accept: */*",
        "-H",
        "Accept-Encoding: identity",
        "-H",
        f"Origin: {origin}",
        "-H",
        f"User-Agent: {CFG.ua}",
        "-H",
        "Content-Type: text/plain;charset=UTF-8",
        "-w",
        "\n__HTTP__:%{http_code}",
    ]
    if cookie_jar:
        cookie_jar.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["-c", str(cookie_jar), "-b", str(cookie_jar)])
    if body is not None:
        cmd.extend(["--data-binary", body])
    cmd.append(url)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 8)
    except subprocess.TimeoutExpired:
        return 0, "", "timeout"
    mixed = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace").strip()
    status = 0
    if "\n__HTTP__:" in mixed:
        text, code = mixed.rsplit("\n__HTTP__:", 1)
        try:
            status = int(code.strip() or "0")
        except ValueError:
            status = 0
    else:
        text = mixed
    return status, text, err


def encode_post(packet: str) -> str:
    """EIO 長度前綴（握手回的就是這種）。"""
    return f"{len(packet)}:{packet}"


class Capture:
    def __init__(self, base: str | None = None) -> None:
        self.base = (base or CFG.base_4000).rstrip("/")
        self.origin = self.base
        self.cookie_jar = CFG.data_dir / "sio_cookies.txt"
        self.sid = ""
        self.ping_interval = 25.0
        self.ping_timeout = 5.0
        self.packets: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def _url(self, *, sid: str = "", transport: str = "polling") -> str:
        q = f"EIO=4&transport={transport}&t={_t()}"
        if sid:
            q += f"&sid={quote(sid)}"
        return f"{self.base}/socket.io/?{q}"

    def _record(self, raw: str, *, via: str) -> dict[str, Any]:
        pkt = decode_packet(raw)
        pkt["via"] = via
        pkt["ts"] = time.time()
        pkt["raw"] = raw if len(raw) < 4000 else raw[:4000]
        with self._lock:
            self.packets.append(pkt)
        log.info("pkt via=%s kind=%s name=%s raw=%s", via, pkt.get("kind"), pkt.get("name"), raw[:240])
        return pkt

    def handshake(self) -> dict[str, Any]:
        url = self._url()
        status, body, err = curl_raw(
            url, timeout=15, cookie_jar=self.cookie_jar, origin=self.origin
        )
        if status != 200:
            raise RuntimeError(f"handshake http={status} err={err} body={body[:200]}")
        parts = parse_eio_polling(body)
        open_data: dict[str, Any] = {}
        for raw in parts:
            pkt = self._record(raw, via="poll-hs")
            if pkt.get("kind") == "open" and isinstance(pkt.get("data"), dict):
                open_data = pkt["data"]
                self.sid = str(open_data.get("sid") or "")
                self.ping_interval = float(open_data.get("pingInterval") or 25000) / 1000.0
                self.ping_timeout = float(open_data.get("pingTimeout") or 5000) / 1000.0
        if not self.sid:
            raise RuntimeError(f"no sid in handshake {body[:200]}")
        log.info("sid=%s pingInterval=%s pingTimeout=%s", self.sid, self.ping_interval, self.ping_timeout)
        return open_data

    def _pong(self) -> None:
        url = self._url(sid=self.sid)
        for body in (encode_post("3"), "3"):
            status, text, err = curl_raw(
                url,
                method="POST",
                body=body,
                timeout=10,
                cookie_jar=self.cookie_jar,
                origin=self.origin,
            )
            log.info("pong POST body=%r http=%s resp=%s err=%s", body, status, text[:80], err)
            if status == 200:
                return

    def _emit(self, name: str, data: Any = None) -> None:
        payload = [name] if data is None else [name, data]
        packet = "42" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        url = self._url(sid=self.sid)
        status, text, err = curl_raw(
            url,
            method="POST",
            body=encode_post(packet),
            timeout=10,
            cookie_jar=self.cookie_jar,
            origin=self.origin,
        )
        log.info("emit %s http=%s resp=%s err=%s", name, status, text[:80], err)

    def poll_once(self, timeout: float) -> list[dict[str, Any]]:
        url = self._url(sid=self.sid)
        t0 = time.time()
        status, body, err = curl_raw(
            url, timeout=timeout, cookie_jar=self.cookie_jar, origin=self.origin
        )
        elapsed = time.time() - t0
        log.info(
            "poll GET %.1fs http=%s bytes=%d body=%r err=%s",
            elapsed,
            status,
            len(body),
            body[:200],
            err,
        )
        got: list[dict[str, Any]] = []
        if status != 200:
            log.warning("poll http=%s err=%s body=%s", status, err, body[:160])
            got.append(
                {
                    "kind": "http_error",
                    "via": "poll",
                    "status": status,
                    "error": err,
                    "body": body[:300],
                    "ts": time.time(),
                }
            )
            with self._lock:
                self.packets.append(got[-1])
            return got
        for raw in parse_eio_polling(body):
            pkt = self._record(raw, via="poll")
            got.append(pkt)
            if pkt.get("kind") == "ping":
                self._pong()
        return got

    def poll_for(self, seconds: float) -> None:
        deadline = time.time() + seconds
        wait = self.ping_interval + self.ping_timeout + 3
        bad = 0
        while time.time() < deadline and not self._stop.is_set():
            remain = deadline - time.time()
            if remain <= 0:
                break
            got = self.poll_once(timeout=min(wait, max(3.0, remain + 1)))
            if got and got[0].get("kind") == "http_error":
                bad += 1
                status = got[0].get("status")
                # 已升 websocket 或 sid 失效：停止狂輪
                if status in (400, 403) or bad >= 3:
                    log.info("stop polling after http=%s (bad=%d)", status, bad)
                    return
            else:
                bad = 0
                if any(p.get("kind") == "close" for p in got):
                    log.info("server closed polling")
                    return

    def upgrade_websocket(self, seconds: float) -> None:
        if websocket is None:
            log.warning("no websocket-client, skip upgrade")
            return
        host, port = _socks_host_port()
        parsed = urlparse(self.base)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        url = (
            f"{ws_scheme}://{parsed.netloc}/socket.io/"
            f"?EIO=4&transport=websocket&sid={quote(self.sid)}"
        )
        log.info("ws upgrade %s", url)
        try:
            ws = websocket.create_connection(
                url,
                sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
                http_proxy_host=host,
                http_proxy_port=port,
                proxy_type="socks5h",
                timeout=20,
                header=[f"Origin: {self.origin}", f"User-Agent: {CFG.ua}"],
            )
        except Exception as exc:
            log.warning("ws upgrade fail: %s", exc)
            return
        try:
            ws.send("2probe")
            ws.settimeout(5)
            try:
                probe = ws.recv()
                self._record(probe if isinstance(probe, str) else repr(probe), via="ws-probe")
            except Exception as exc:
                log.warning("ws probe recv: %s", exc)
            ws.send("5")
            deadline = time.time() + seconds
            ws.settimeout(min(self.ping_interval, 8))
            last_ping = time.time()
            while time.time() < deadline and not self._stop.is_set():
                try:
                    raw = ws.recv()
                except Exception as exc:
                    if "Timeout" in type(exc).__name__:
                        if time.time() - last_ping >= 20:
                            try:
                                ws.send("2")
                                last_ping = time.time()
                                self._record("2", via="ws-client-ping")
                            except Exception:
                                break
                        continue
                    log.warning("ws recv: %s", exc)
                    break
                if not raw:
                    break
                text = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
                pkt = self._record(text, via="ws")
                if pkt.get("kind") == "ping":
                    ws.send("3")
                    last_ping = time.time()
                elif pkt.get("kind") == "pong":
                    last_ping = time.time()
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def run(
        self,
        seconds: float = 30.0,
        *,
        upgrade: bool = False,
        emit: bool = False,
    ) -> list[dict[str, Any]]:
        self.handshake()
        threads: list[threading.Thread] = []
        t_poll = threading.Thread(target=self.poll_for, args=(seconds,), daemon=True)
        threads.append(t_poll)
        t_poll.start()
        if upgrade:
            t_ws = threading.Thread(
                target=self.upgrade_websocket, args=(seconds,), daemon=True
            )
            threads.append(t_ws)
            t_ws.start()
        if emit:
            time.sleep(0.4)
            for name in ("join", "subscribe", "watch", "listen"):
                try:
                    self._emit(name)
                except Exception as exc:
                    log.warning("emit %s fail: %s", name, exc)
        for t in threads:
            t.join(timeout=seconds + 15)
        self._stop.set()
        return list(self.packets)


def summarize(packets: list[dict[str, Any]]) -> dict[str, Any]:
    events = [p for p in packets if p.get("kind") == "event"]
    names: dict[str, int] = {}
    for ev in events:
        name = str(ev.get("name") or "")
        names[name] = names.get(name, 0) + 1
    kinds: dict[str, int] = {}
    for p in packets:
        k = str(p.get("kind") or "?")
        kinds[k] = kinds.get(k, 0) + 1
    return {
        "packets": len(packets),
        "events": len(events),
        "event_names": names,
        "kinds": kinds,
        "sid": next((p.get("data", {}).get("sid") for p in packets if p.get("kind") == "open"), None),
    }
