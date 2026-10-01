"""JWT 管理：有效就用；到期前 180 秒 refresh；400 停手等 tokens.json。"""
from __future__ import annotations

import logging
import threading
import time

from . import auth
from .config import CFG

log = logging.getLogger("epcr")


class TokenManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_check = 0.0
        self._mtime = 0.0
        self._refresh_halted = False
        self._halt_reason = ""
        self._warned_no_token = False
        self._snap = ("", "")
        auth.load_tokens()
        self._mtime = self._file_mtime()
        self._snap = self._token_snap()

    def remaining(self) -> float:
        exp = auth.jwt_exp(CFG.token)
        if not exp:
            return 0.0
        return exp - time.time()

    def ok(self) -> bool:
        return self.remaining() > 15

    def bearer(self) -> str:
        return (CFG.token or "").strip()

    def halted(self) -> bool:
        return self._refresh_halted

    def _file_mtime(self) -> float:
        try:
            return CFG.token_path.stat().st_mtime
        except OSError:
            return 0.0

    def _token_snap(self) -> tuple[str, str]:
        return ((CFG.token or "")[:20], (CFG.refresh_token or "")[:20])

    def _reload(self) -> None:
        auth.load_tokens()
        mtime = self._file_mtime()
        snap = self._token_snap()
        if mtime != self._mtime or snap != self._snap:
            if self._refresh_halted:
                log.info("tokens.json changed — resume refresh, wait EPCR primary")
            self._mtime = mtime
            self._snap = snap
            self._refresh_halted = False
            self._halt_reason = ""
            self._warned_no_token = False

    def ensure(self, *, force: bool = False, allow_login: bool = False) -> bool:
        """不空轉 refresh、不在 run 迴圈 OCR。allow_login 只給 `python3 -m epcr login`。"""
        with self._lock:
            now = time.time()
            if not force and now - self._last_check < 5 and self.ok() and not self._refresh_halted:
                return True
            self._last_check = now
            self._reload()
            left = self.remaining()
            if left > CFG.refresh_before_sec and not force:
                return True
            if self._refresh_halted:
                if not self._warned_no_token:
                    log.warning(
                        "refresh halted (%s) — wait re-login / tokens.json",
                        self._halt_reason[:120],
                    )
                    self._warned_no_token = True
                return self.ok()
            if CFG.refresh_token and (force or left <= CFG.refresh_before_sec):
                try:
                    auth.refresh()
                    log.info("token refresh remaining=%.0fs", self.remaining())
                    self._snap = self._token_snap()
                    self._mtime = self._file_mtime()
                    return self.ok()
                except auth.AuthError as exc:
                    if exc.status in (400, 401, 403):
                        self._refresh_halted = True
                        self._halt_reason = str(exc)
                        log.warning(
                            "refresh http=%s, stop until re-login: %s",
                            exc.status,
                            str(exc)[:160],
                        )
                        return self.ok()
                    log.warning("refresh fail: %s", exc)
                except Exception as exc:
                    log.warning("refresh fail: %s", exc)
            if self.ok():
                return True
            if allow_login:
                sso = (CFG.sso_session or "").strip()
                if sso:
                    try:
                        auth.sso_login(sso)
                        return self.ok()
                    except Exception as exc:
                        log.warning("ssoLogin fail: %s", exc)
                if CFG.user and CFG.password:
                    try:
                        auth.login_ocr()
                        return self.ok()
                    except Exception as exc:
                        log.warning("login_ocr fail: %s", exc)
                        return False
            if not self._warned_no_token:
                log.warning(
                    "no valid jwt — skip refresh; wait %s ; backup E1",
                    CFG.token_path,
                )
                self._warned_no_token = True
            return False
