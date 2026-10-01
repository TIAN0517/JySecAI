"""EPCR 登入 / refreshToken。JWT idle 15 分鐘。"""
from __future__ import annotations

import base64
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from .config import CFG
from .http import curl
from .ocr import solve as ocr_solve
from .telegram_bot import broadcaster, auto_bind_group

log = logging.getLogger("epcr")

# 官方頁在 :4000；AuthService login POST 的 Origin 是頁面 origin，不是 :4004。
PAGE_ORIGIN = "https://epcr.tpf.gov.tw:4000"
PAGE_REFERER = "https://epcr.tpf.gov.tw:4000/#/login"


class AuthError(RuntimeError):
    """登入／續期失敗。status=400 表示 refresh 作廢，應停手等重新 login。"""

    def __init__(self, message: str, *, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


def _page_headers() -> dict[str, str]:
    origin = (CFG.origin or PAGE_ORIGIN).rstrip("/")
    return {
        "Origin": origin,
        "Referer": f"{origin}/#/login",
    }


def _error_message(result) -> str:
    """Parse AuthServer error body. 500 常是 JSON 字串 \"TypeError\"，不是 {message}。"""
    try:
        blob = result.json()
    except Exception:
        blob = None
    if isinstance(blob, dict):
        return str(blob.get("message") or blob.get("error") or blob.get("name") or result.text()[:200] or result.error)
    if isinstance(blob, str) and blob.strip():
        return blob.strip()
    return (result.text()[:200] or result.error or "").strip()


def jwt_payload(token: str) -> dict[str, Any]:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    raw = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(raw.encode("ascii")))
    except Exception:
        return {}


def jwt_exp(token: str) -> float:
    payload = jwt_payload(token)
    try:
        return float(payload.get("exp") or 0)
    except (TypeError, ValueError):
        return 0.0


def load_tokens() -> dict[str, str]:
    """file > env。A 寫入 tokens.json 後下一輪就能切回 EPCR。"""
    import os

    env_tok = (os.environ.get("EPCR_TOKEN") or os.environ.get("EPCR_JWT") or "").strip()
    env_ref = os.environ.get("EPCR_REFRESH_TOKEN", "").strip()
    file_tok = ""
    file_ref = ""
    if CFG.token_path.is_file():
        try:
            blob = json.loads(CFG.token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            blob = {}
        if isinstance(blob, dict):
            file_tok = str(blob.get("token") or "").strip()
            file_ref = str(blob.get("refreshToken") or blob.get("refresh_token") or "").strip()
    tok = file_tok or env_tok
    ref = file_ref or env_ref
    if tok.lower().startswith("bearer "):
        tok = tok[7:].strip()
    CFG.token = tok
    CFG.refresh_token = ref
    return {"token": tok, "refreshToken": ref}


def save_tokens(token: str, refresh_token: str) -> None:
    CFG.token = (token or "").strip()
    if CFG.token.lower().startswith("bearer "):
        CFG.token = CFG.token[7:].strip()
    CFG.refresh_token = (refresh_token or CFG.refresh_token or "").strip()
    CFG.token_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "token": CFG.token,
        "refreshToken": CFG.refresh_token,
        "exp": jwt_exp(CFG.token),
        "saved_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }
    CFG.token_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        CFG.token_path.chmod(0o600)
    except OSError:
        pass


def fetch_captcha() -> bytes:
    CFG.cookie_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{CFG.auth}/captcha?t={int(time.time() * 1000)}"
    result = curl(
        url,
        cookie_jar=CFG.cookie_path,
        timeout=15,
        retries=2,
        headers={
            **_page_headers(),
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    if result.status != 200 or not result.body:
        raise RuntimeError(f"captcha http={result.status} {result.error}")
    CFG.captcha_path.write_bytes(result.body)
    return result.body


def login(username: str, password: str, captcha: str) -> dict[str, Any]:
    if not CFG.cookie_path.exists():
        raise RuntimeError("no captcha cookie")
    result = curl(
        f"{CFG.auth}/login",
        method="POST",
        json_body={"username": username, "password": password, "captcha": captcha},
        headers=_page_headers(),
        cookie_in=CFG.cookie_path,
        cookie_jar=CFG.cookie_path,
        timeout=20,
        retries=0,
    )
    if result.status != 200:
        raise RuntimeError(f"login http={result.status} {_error_message(result)}")
    data = result.json()
    if not isinstance(data, dict) or not data.get("token"):
        raise RuntimeError(f"login no token: {result.text()[:200]}")
    save_tokens(str(data["token"]), str(data.get("refreshToken") or ""))
    log.info("login ok exp=%s", jwt_exp(CFG.token))
    return data


def login_ocr(*, tries: int = 8) -> dict[str, Any]:
    user = CFG.user
    password = CFG.password
    if not user or not password:
        raise RuntimeError("設 EPCR_USER / EPCR_PASSWORD")
    last = "no_attempt"
    for i in range(tries):
        img = fetch_captcha()
        text = ocr_solve(img)
        if len(text) < 4:
            last = f"ocr_short:{text}"
            log.warning("captcha try %d ocr_short=%s (need 4)", i + 1, text)
            time.sleep(0.4)
            continue
        try:
            return login(user, password, text)
        except Exception as exc:
            last = str(exc)
            log.warning("captcha try %d login fail %s ocr=%s", i + 1, exc, text)
            low = last.lower()
            # 驗證碼錯才值得換圖重試；AuthServer 500/TypeError 重試沒有意義
            if "http=500" in low or "typeerror" in low:
                raise RuntimeError(
                    f"login_ocr abort: AuthServer exception {last} "
                    "(not captcha; need cloud2 sessionId or AuthServer restart)"
                ) from exc
            if any(s in last for s in ("鎖", "停用", "lock", "無法辨識使用者")):
                raise RuntimeError(f"login_ocr abort: account {last}") from exc
            time.sleep(0.5)
    raise RuntimeError(f"login_ocr failed after {tries}: {last}")


def sso_login(session_id: str) -> dict[str, Any]:
    result = curl(
        f"{CFG.auth}/ssoLogin",
        method="POST",
        json_body={"sessionId": session_id},
        headers=_page_headers(),
        timeout=20,
        retries=1,
    )
    if result.status != 200:
        raise RuntimeError(f"ssoLogin http={result.status} {_error_message(result)}")
    data = result.json()
    if not isinstance(data, dict) or not data.get("token"):
        raise RuntimeError(f"ssoLogin no token: {result.text()[:200]}")
    save_tokens(str(data["token"]), str(data.get("refreshToken") or ""))
    log.info("sso login ok exp=%s", jwt_exp(CFG.token))
    return data


def refresh() -> dict[str, Any]:
    load_tokens()
    if not CFG.refresh_token:
        raise RuntimeError("沒有 refreshToken")
    result = curl(
        f"{CFG.auth}/refreshToken",
        method="POST",
        json_body={"refreshToken": CFG.refresh_token},
        headers=_page_headers(),
        timeout=20,
        retries=1,
    )
    if result.status != 200:
        raise AuthError(
            f"refresh http={result.status} {_error_message(result)}",
            status=result.status,
        )
    data = result.json()
    if not isinstance(data, dict) or not data.get("token"):
        raise AuthError(f"refresh no token: {result.text()[:200]}", status=result.status or 0)
    save_tokens(str(data["token"]), str(data.get("refreshToken") or CFG.refresh_token))
    log.info("refresh ok exp=%s", jwt_exp(CFG.token))
    return data
