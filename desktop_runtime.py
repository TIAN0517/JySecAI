"""Local desktop lifecycle backend. HTTP availability is not application readiness."""

import errno
import http.client
import ipaddress
import os
from pathlib import Path
import queue
import re
import socket
import ssl
import subprocess
import threading
import time
from dataclasses import dataclass

import yaml

try:
    import psutil
except ImportError:
    psutil = None

_WINDOWS = os.name == "nt"
_LINE_LIMIT = 4096
_CREDENTIAL = r"(?:pass(?:word|wd)?|pwd|token|secret|(?:api|access|private)[_-]?key|auth(?:orization|_header_value)?|cookie|credentials?|dsn|database_url|connection_string)"
_EMPTY = dict(http_ok=False, http_status=None, latency_ms=None,
              cpu_percent=None, memory_mb=None, uptime_seconds=None)


@dataclass(frozen=True)
class EndpointSettings:
    host: str
    port: int
    tls: bool
    version: str = ""

    @property
    def url(self):
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{'https' if self.tls else 'http'}://{host}:{self.port}"


def _loopback(host):
    if not isinstance(host, str):
        raise ValueError("Server host must be a local address.")
    host = {"": "127.0.0.1", "localhost": "127.0.0.1", "0.0.0.0": "127.0.0.1",
            "::": "::1", "[::]": "::1", "[::1]": "::1"}.get(host.lower(), host)
    try:
        if "%" not in host and ipaddress.ip_address(host).is_loopback:
            return host
    except ValueError:
        pass
    raise ValueError("Non-loopback server hosts are unsupported by the desktop runtime.")


def _read_config(path):
    try:
        with Path(path).open("r", encoding="utf-8-sig") as stream:
            text = stream.read(2 * 1024 * 1024 + 1)
        if len(text) > 2 * 1024 * 1024:
            raise ValueError()
        data = yaml.safe_load(text)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, RecursionError):
        raise ValueError("Configuration could not be read as valid, bounded YAML.") from None
    if not isinstance(data, dict) or not isinstance(data.get("server"), dict):
        raise ValueError("Configuration requires a server mapping.")
    server = data["server"]
    fields = [server.get(k) for k in ("host", "port", "tls_enabled", "tls_auto_self_sign",
                                     "tls_cert_path", "tls_key_path")]
    if any(isinstance(v, str) and "$" in v for v in fields):
        raise ValueError("Environment placeholders in server fields are unsupported by the server loader.")
    # Default() advertises 6688, but Load() does not merge it: omission binds port 0.
    port = server.get("port")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Server port must be an explicit integer between 1 and 65535.")
    flags = [server.get(k, False) for k in ("tls_enabled", "tls_auto_self_sign")]
    paths = [server.get(k, "") for k in ("tls_cert_path", "tls_key_path")]
    version = data.get("version", "")
    if (any(type(v) is not bool for v in flags) or any(not isinstance(v, str) for v in paths)
            or not isinstance(version, str) or len(version) > 128
            or any(ord(c) < 32 for c in version)):
        raise ValueError("Invalid server TLS fields or version.")
    settings = EndpointSettings(_loopback(server.get("host", "")), port,
                                any(flags) or all(p.strip() for p in paths), version)
    secrets, seen, pending = set(), set(), [(data, False)]
    while pending:
        value, sensitive = pending.pop()
        if (id(value), sensitive) in seen:
            continue
        seen.add((id(value), sensitive))
        if isinstance(value, dict):
            pending.extend((v, sensitive or bool(re.search(_CREDENTIAL, str(k), re.I)))
                           for k, v in value.items())
        elif isinstance(value, list):
            pending.extend((v, sensitive) for v in value)
        elif sensitive and isinstance(value, (str, int, float)) and str(value):
            secrets.add(str(value))
            secrets.update(part for part in str(value).splitlines() if part)
    return settings, tuple(sorted(secrets, key=len, reverse=True))


def read_settings(path):
    """Return immutable, loopback-normalized settings; raise a safe ValueError on failure."""
    return _read_config(path)[0]


def redact(text, secrets=()):
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    text = re.sub(r"(?is)-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|$)", "[REDACTED]", text)
    text = re.sub(r"(?i)([a-z][a-z0-9+.-]*://)[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"(?i)\b(?:bearer|basic)\s+[^\s\"'<>]+", "[REDACTED]", text)
    return re.sub(r"(?im)([\w-]*" + _CREDENTIAL + r"[\w-]*[\"']?\s*(?:[:=]\s*|\s+)).*$",
                  r"\1[REDACTED]", text)


def _probe(settings):
    """Return (occupied/unknown, HTTP status, latency, title heuristic); never redirect."""
    host = _loopback(settings.host)  # Revalidate at the network boundary; never resolve DNS.
    started = time.monotonic()
    try:
        with socket.create_connection((host, settings.port), timeout=1):
            pass
    except OSError as exc:
        return (False if exc.errno == errno.ECONNREFUSED else None), None, None, False
    connection = (http.client.HTTPSConnection(host, settings.port, timeout=1,
                  context=ssl._create_unverified_context()) if settings.tls else
                  http.client.HTTPConnection(host, settings.port, timeout=1))
    status, latency, matched = None, None, False
    try:
        connection.request("GET", "/", headers={"Connection": "close"})
        response = connection.getresponse()
        status, latency = response.status, (time.monotonic() - started) * 1000
        body = response.read(8192).decode("utf-8", errors="replace")
        matched = bool(re.search(r"<title\b[^>]*>[^<]*JySecAI[^<]*</title\s*>", body, re.I))
    except (OSError, http.client.HTTPException, ValueError):
        pass
    finally:
        connection.close()
    return True, status, latency, matched


class DesktopRuntime:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.events = queue.Queue(maxsize=1000)
        self._lock, self._operation = threading.RLock(), threading.Lock()
        self._halt, self._monitor = threading.Event(), None
        self._proc, self._metrics, self._started = None, None, None
        self._settings, self._secrets, self._config_error = None, (), ""
        self._busy, self._generation, self._dropped = False, 0, 0
        self._data = dict(state="stopped", detail="No owned process; not checked yet.",
                          checked_at=None, **_EMPTY)
        self.reload_config()

    @property
    def settings(self):
        with self._lock:
            return self._settings

    @property
    def config_error(self):
        with self._lock:
            return self._config_error

    def snapshot(self):
        with self._lock:
            return dict(self._data, busy=self._busy, owned=self._proc is not None,
                        pid=self._proc.pid if self._proc else None, config_error=self._config_error)

    def _emit(self, level="info", message=None, secrets=None):
        with self._lock:
            try:
                if self._dropped:
                    self.events.put_nowait(("warning", f"Dropped {self._dropped} messages: event queue was full."))
                    self._dropped = 0
                if message is not None:
                    safe = redact(message, self._secrets if secrets is None else secrets)
                    self.events.put_nowait((level, safe[:_LINE_LIMIT]))
            except queue.Full:
                self._dropped += int(message is not None)

    def _publish(self, state, detail, **values):
        with self._lock:
            changed = (state, detail) != (self._data["state"], self._data["detail"])
            self._data.update(state=state, detail=detail, **values)
            if changed:
                level = {"error": "error", "conflict": "error", "external": "warning",
                         "unresponsive": "warning", "running": "success"}.get(state, "info")
                self._emit(level, detail)

    def _load(self):
        try:
            settings, secrets = _read_config(self.root / "config.yaml")
        except ValueError as exc:
            with self._lock:
                self._settings, self._config_error = None, str(exc)
            self._publish("error", self._config_error, **_EMPTY, checked_at=None)
            return False
        with self._lock:
            self._settings, self._secrets, self._config_error = settings, secrets, ""
        self._publish("stopped", "Configuration loaded; endpoint not checked yet.", **_EMPTY, checked_at=None)
        return True

    def reload_config(self):
        if not self._operation.acquire(blocking=False):
            return False
        try:
            with self._lock:
                if self._proc is not None:
                    return False
                self._generation += 1
                return self._load()
        finally:
            self._operation.release()

    def begin_monitoring(self):
        with self._lock:
            if self._monitor is None and not self._halt.is_set():
                self._monitor = threading.Thread(target=self._monitor_loop, daemon=True)
                self._monitor.start()

    def close(self):
        """Stop monitoring, not the owned service or its stdout reader."""
        self._halt.set()
        with self._lock:
            monitor = self._monitor
        if monitor and monitor is not threading.current_thread():
            monitor.join(timeout=2.5)

    def start(self):
        return self._submit("start")

    def stop(self):
        return self._submit("stop")

    def restart(self):
        return self._submit("restart")

    def _submit(self, action):
        if not self._operation.acquire(blocking=False):
            return False
        with self._lock:
            if self._halt.is_set() or (action == "start") == (self._proc is not None):
                self._operation.release()
                return False
            self._busy = True
            self._generation += 1
            self._publish("starting" if action == "start" else "stopping", "Local service command accepted.")
        try:
            threading.Thread(target=self._run, args=(action,), daemon=True).start()
            self.begin_monitoring()
        except RuntimeError:
            with self._lock:
                self._busy = False
            self._operation.release()
            self._publish("error", "Could not start the background command thread.")
            return False
        return True

    def _run(self, action):
        try:
            if action != "start" and not self._stop():
                return
            if action != "stop":
                self._start()
        except Exception:
            self._publish("error", "Local service command failed; no automatic retry.", **_EMPTY)
        finally:
            with self._lock:
                self._busy = False
            self._operation.release()

    def _start(self):
        if not self._load():
            return
        executable = self.root / ("jysecai.exe" if _WINDOWS else "jysecai")
        if not executable.is_file() or (not _WINDOWS and not os.access(executable, os.X_OK)):
            self._publish("error", "Local server executable is missing or not executable.")
            return
        occupied, status, latency, matched = _probe(self.settings)
        if occupied is not False:
            self._publish("external" if matched else "conflict" if occupied else "error",
                          "Existing listener: JySecAI title heuristic only; not readiness or ownership." if matched else
                          "Local port is occupied by an unidentified listener." if occupied else
                          "Could not determine whether the local port is available.",
                          http_ok=status is not None, http_status=status, latency_ms=latency, checked_at=time.time())
            return
        # Explicit protocol flags prevent inherited HTTPS bootstrap variables changing the endpoint.
        process = subprocess.Popen([str(executable), "--config", str(self.root / "config.yaml"),
                                    "--https" if self.settings.tls else "--http"],
                                   cwd=str(self.root), shell=False, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   creationflags=0x08000000 if _WINDOWS else 0)
        with self._lock:
            self._proc, self._started = process, time.monotonic()
        threading.Thread(target=self._drain, args=(process.stdout, self._secrets), daemon=True).start()
        if psutil is not None:
            try:
                self._metrics = psutil.Process(process.pid)
                self._metrics.cpu_percent(None)
            except (psutil.Error, OSError):
                self._metrics = None
        self._publish("starting", "Owned process launched; waiting for local HTTP availability.", **_EMPTY)

    def _stop(self):
        process = self._proc
        try:
            if process.poll() is None:
                self._emit("warning" if _WINDOWS else "info", "Terminating the owned process (forced on Windows)."
                           if _WINDOWS else "Sending SIGTERM to the owned process.")
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._emit("warning", "Stop timed out after 5 seconds; killing the owned process.")
                process.kill()
                process.wait(timeout=1)
        except (OSError, subprocess.TimeoutExpired):
            self._publish("error", "Could not confirm the owned process stopped; restart blocked.", **_EMPTY)
            return False
        with self._lock:
            self._proc, self._metrics, self._started = None, None, None
        self._publish("stopped", "Owned process exited.", **_EMPTY)
        return True

    def _drain(self, stream, secrets):
        oversized, private_key = False, False
        try:
            while True:
                line = stream.readline(_LINE_LIMIT + 1)
                if not line:
                    break
                if len(line) > _LINE_LIMIT or oversized:
                    if not oversized:
                        self._emit("warning", "Dropped an oversized log line.")
                    oversized = not line.endswith(b"\n")
                    continue
                text = line.decode("utf-8", errors="replace").rstrip()
                if re.search(r"-----BEGIN .*PRIVATE KEY-----", text):
                    private_key = True
                    self._emit("info", "[REDACTED private key]")
                if not private_key:
                    self._emit("info", text, secrets)
                if re.search(r"-----END .*PRIVATE KEY-----", text):
                    private_key = False
        except (OSError, ValueError):
            self._emit("warning", "Local process log reader stopped.")
        finally:
            stream.close()

    def _monitor_loop(self):
        while not self._halt.is_set():
            try:
                self._sample()
                self._emit()
            except Exception:
                self._emit("warning", "Local status check failed.")
            self._halt.wait(1)

    def _sample(self):
        with self._lock:
            if self._busy or self._settings is None:
                return
            generation, settings, process = self._generation, self._settings, self._proc
            metrics, started = self._metrics, self._started
        values = dict(_EMPTY, checked_at=time.time())
        code = process.poll() if process is not None else None
        if process is not None and code is not None:
            state, detail = "error", f"Owned process exited with code {code}; no automatic restart."
        else:
            occupied, status, latency, matched = _probe(settings)
            values.update(http_ok=status is not None, http_status=status, latency_ms=latency, checked_at=time.time())
            if process is not None:
                values["uptime_seconds"] = max(0.0, time.monotonic() - started)
                state = "running" if status is not None else "starting" if values["uptime_seconds"] < 10 else "unresponsive"
                detail = (f"HTTP responded with status {status}; availability only, not readiness or TLS trust."
                          if status is not None else "Owned process has not responded to local HTTP.")
                if metrics is not None:
                    try:
                        values.update(cpu_percent=float(metrics.cpu_percent(None)),
                                      memory_mb=metrics.memory_info().rss / (1024 * 1024))
                    except (psutil.Error, OSError):
                        pass
                code = process.poll()
                if code is not None:
                    state, detail = "error", f"Owned process exited with code {code}; no automatic restart."
                    values.update(_EMPTY)
            else:
                state = "external" if matched else "conflict" if occupied else "stopped" if occupied is False else "error"
                detail = ("Existing listener: JySecAI title heuristic only; not readiness or ownership." if matched else
                          "Local port is occupied by an unidentified listener." if occupied else
                          "No local listener detected." if occupied is False else "Local listener check was inconclusive.")
        with self._lock:
            if self._busy or generation != self._generation or self._halt.is_set():
                return
            if process is not None and code is not None:
                self._proc, self._metrics, self._started = None, None, None
            elif process is None and state == "stopped" and self._data["state"] == "error":
                return  # Keep launch/exit failures visible until an explicit command or config reload.
            self._publish(state, detail, **values)
