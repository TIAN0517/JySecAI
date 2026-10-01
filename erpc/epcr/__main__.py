#!/usr/bin/env python3
"""新北 119 推播。

  python3 -m epcr probe     # 公開端點
  python3 -m epcr token     # 看 JWT 剩餘秒數（不登入、不空轉 refresh）
  python3 -m epcr login     # 明確 OCR 登入，寫 data/tokens.json
  python3 -m epcr run       # 主源 DispatchRecords 5/6；沒 JWT 才 E1
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import telegram
from .card import fmt_card
from .config import CFG
from .dest import targets
from .http import curl
from .listener import listen_seconds
from .models import cases_from_event
from .polling import summarize
from .socketio import parse_eio_polling


def _setup_log(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if CFG.log_path:
        CFG.log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(CFG.log_path, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )


def _get(url: str, timeout: float = 15.0):
    return curl(url, timeout=timeout, retries=1)


def cmd_probe(_args: argparse.Namespace) -> int:
    v = _get(f"{CFG.base_4000}/version/")
    c = _get(f"{CFG.base_4000}/config")
    m = _get(f"{CFG.base_4005}/config")
    s = _get(f"{CFG.base_4000}/socket.io/?EIO=4&transport=polling")
    s5 = _get(f"{CFG.base_4005}/socket.io/?EIO=4&transport=polling")
    cfg = None
    try:
        cfg = c.json() if c.status == 200 else None
    except Exception:
        cfg = None
    safe = {}
    if isinstance(cfg, dict):
        for key in (
            "hostname",
            "port",
            "authServer",
            "epcrServer",
            "ntpcCloud",
            "MAX_IDLE_DURATION",
            "MerSocketio",
        ):
            if key in cfg:
                safe[key] = cfg[key]
    mon = None
    try:
        mon = m.json() if m.status == 200 else m.text()[:200]
    except Exception:
        mon = m.text()[:200]
    print(
        json.dumps(
            {
                "proxy": CFG.proxy,
                "version": {"http": v.status, "value": (v.text() if v.status == 200 else v.error)[:80]},
                "config4000": {"http": c.status, "safe": safe},
                "config4005": {"http": m.status, "value": mon},
                "socket4000": {
                    "http": s.status,
                    "packets": parse_eio_polling(s.text())[:3] if s.status == 200 else s.text()[:120],
                },
                "socket4005": {
                    "http": s5.status,
                    "packets": parse_eio_polling(s5.text())[:3] if s5.status == 200 else s5.text()[:120],
                },
                "ws": CFG.ws_url,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if v.status == 200 and s.status == 200 else 1


def cmd_listen(args: argparse.Namespace) -> int:
    print(f"# polling capture {args.seconds}s via {CFG.proxy}", flush=True)
    pkts = listen_seconds(args.seconds, dump_all=True, upgrade=args.upgrade)
    events = [p for p in pkts if p.get("kind") == "event"]
    extracted = []
    for ev in events:
        extracted.extend(cases_from_event(ev))
    summary = summarize(pkts)
    summary["extracted_cases"] = extracted
    summary["capture_file"] = str(CFG.data_dir / "capture.jsonl")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str), flush=True)
    if not events:
        print(
            "# 沒有 42 事件：polling 在 30s 被 CLOSE；"
            "請用 --upgrade 或 python3 -m epcr run 改走 websocket 長掛。",
            flush=True,
        )
    return 0 if pkts else 1


def cmd_dests(_args: argparse.Namespace) -> int:
    rows = []
    for t in targets():
        tok = str(t.get("token") or "")
        rows.append(
            {
                "tenant": t.get("tenant"),
                "bot": t.get("bot"),
                "chat_id": t.get("chat_id"),
                "token": (tok[:10] + "…" + tok[-6:]) if len(tok) > 20 else tok,
            }
        )
    print(json.dumps({"n": len(rows), "targets": rows, "proxy": CFG.proxy}, ensure_ascii=False, indent=2))
    return 0 if rows else 1


def cmd_ping(_args: argparse.Namespace) -> int:
    """只打試車群，確認 bot 能發。"""
    from .dest import load_destinations

    test = (load_destinations().get("test") or {})
    if not test.get("token"):
        print("no test dest", file=sys.stderr)
        return 1
    case = {
        "caseNo": "PING",
        "address": "新北市板橋區測試",
        "type": "測試",
        "branch": "試車",
        "ambulance": "",
        "time": "",
        "coordinate": "",
    }
    from datetime import datetime, timedelta, timezone

    case["time"] = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    ok, body = telegram.send_one(test["token"], test["chat_id"], fmt_card(case), case)
    print(json.dumps({"ok": ok, "body": body, "chat_id": test["chat_id"]}, ensure_ascii=False))
    return 0 if ok else 1


def cmd_login(_args: argparse.Namespace) -> int:
    from . import auth

    try:
        auth.login_ocr()
    except Exception as exc:
        print(f"login fail: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "exp": auth.jwt_exp(CFG.token), "path": str(CFG.token_path)}))
    return 0


SSO_REDIRECT = "https://epcr.tpf.gov.tw:4000"


def sso_authorize_url(state: str = "epcr") -> str:
    from urllib.parse import urlencode

    return "https://oauth.ntpc.gov.tw/oauthServer.do?" + urlencode(
        {
            "response_type": "code",
            "client_id": "epcr",
            "redirect_uri": SSO_REDIRECT,
            "state": state,
        }
    )


_SSO_HINT = (
    "這條網址不要貼進終端機當指令（& 會被 bash 拆開）。\n"
    "步驟：\n"
    "  1) 在【瀏覽器】打開：python3 -m epcr sso-url 印出的那條\n"
    "  2) 用公務雲帳號登入（圖形驗證碼）\n"
    "  3) 成功後網址列會變成 https://epcr.tpf.gov.tw:4000/?code=一長串亂碼\n"
    "  4) 回到這裡執行：python3 -m epcr sso    （不要加參數）\n"
    "  5) 把步驟 3 的整段網址貼上、按 Enter\n"
    "code= 後面必須是授權碼，不能再貼 oauthServer.do。"
)


def cmd_sso_url(_args: argparse.Namespace) -> int:
    url = sso_authorize_url()
    print(url)
    print("\n" + _SSO_HINT, file=sys.stderr)
    return 0


def _sso_extract(raw: str, session_id: str) -> tuple[str, str]:
    """Return (token, error). token is sessionId or OAuth code."""
    from urllib.parse import parse_qs, unquote, urlparse

    session_id = (session_id or "").strip().strip("'\"")
    raw = (raw or "").strip().strip("'\"")
    if not raw:
        if session_id:
            return session_id, ""
        return "", "沒貼網址。\n" + _SSO_HINT
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()
    is_authorize = "oauth.ntpc.gov.tw" in host and "oauthserver" in path
    code = unquote((qs.get("code") or [""])[0].strip())
    sid = (
        (qs.get("sessionId") or qs.get("session_id") or [""])[0].strip()
        or session_id
    )
    code_looks_like_url = code.lower().startswith("http") or "oauthserver" in code.lower()
    if is_authorize or code_looks_like_url:
        return "", (
            "你貼的還是公務雲【登入起始網址】，或把起始網址塞進了 ?code=。\n"
            "這一步還沒登入，沒有授權碼。\n" + _SSO_HINT
        )
    token = sid or code
    if not token:
        keys = ",".join(sorted(qs.keys())) or "(none)"
        return "", (
            f"URL 裡的 code/sessionId 是空的（query：{keys}）。\n" + _SSO_HINT
        )
    if len(token) < 8:
        return "", f"code/sessionId 太短（{token!r}），不像真的授權碼。\n" + _SSO_HINT
    return token, ""


def cmd_sso(args: argparse.Namespace) -> int:
    from . import auth

    raw = (getattr(args, "callback", None) or getattr(args, "url", None) or "").strip()
    sid = (getattr(args, "session_id", None) or "").strip()
    file_path = (getattr(args, "file", None) or "").strip()
    if file_path:
        try:
            raw = Path(file_path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            print(f"讀檔失敗 {file_path}: {exc}", file=sys.stderr)
            return 2
        if not raw:
            print(
                f"{file_path} 是空的（0 byte）。\n"
                "聊天室裡執行 cat > 檔案 不會讓你貼字，只會建成空檔。\n"
                "請先在瀏覽器登入公務雲，把成功後的網址\n"
                "  https://epcr.tpf.gov.tw:4000/?code=一長串\n"
                "貼在這則對話裡，或用 SSH 執行：\n"
                f"  printf '%s\\n' '回跳網址' > {file_path}\n"
                f"  python3 -m epcr sso --file {file_path}",
                file=sys.stderr,
            )
            return 2
    if not raw and not sid:
        if not sys.stdin.isatty():
            print(
                "不是閃退：這個指令在等你貼回跳網址，但目前 stdin 不是互動終端（聊天室執行指令會立刻 EOF）。\n"
                "請在 SSH 裡打：\n"
                "  python3 -m epcr sso\n"
                "出現提示後再貼 https://epcr.tpf.gov.tw:4000/?code=… 然後 Enter。\n"
                "或把回跳網址寫進檔案再：\n"
                "  python3 -m epcr sso --file /root/erpc/data/sso-callback.txt\n"
                "或直接在這則聊天貼上回跳 URL，不要跑這個指令。",
                file=sys.stderr,
            )
            return 2
        print(
            "請貼【瀏覽器網址列】登入成功後的回跳 URL，然後按 Enter。\n"
            "（不要貼 oauthServer.do；不要在 shell 直接打 https://）",
            file=sys.stderr,
        )
        try:
            raw = input()
        except EOFError:
            raw = ""
        raw = (raw or "").strip().strip("'\"")
    token, err = _sso_extract(raw, sid)
    if err:
        print(err, file=sys.stderr)
        return 2
    try:
        auth.sso_login(token)
    except Exception as exc:
        print(f"sso fail: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "exp": auth.jwt_exp(CFG.token),
                "path": str(CFG.token_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_token(_args: argparse.Namespace) -> int:
    from .tokens import TokenManager

    tm = TokenManager()
    ok = tm.ensure(allow_login=False)
    print(
        json.dumps(
            {
                "ok": ok,
                "remaining_sec": round(tm.remaining(), 1),
                "has_refresh": bool(CFG.refresh_token),
                "refresh_halted": tm.halted(),
                "token_file": CFG.token_path.is_file(),
                "path": str(CFG.token_path),
            }
        )
    )
    return 0 if ok else 1


def cmd_run(_args: argparse.Namespace) -> int:
    from .runner import run_forever

    run_forever()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m epcr",
        description="新北 119：EPCR GET /DispatchRecords StatusId 5/6；沒 JWT 才 E1",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe", help="公開端點（不需登入）")
    p_listen = sub.add_parser("listen", help="polling 握手+抓 packet，確認 event name")
    p_listen.add_argument("-t", "--seconds", type=float, default=30.0)
    p_listen.add_argument("--upgrade", action="store_true", help="握手後再升 websocket")
    sub.add_parser("dests", help="列出將推播的 bot／群（token 脫敏）")
    sub.add_parser("ping", help="只送一則測試卡到試車群")
    sub.add_parser("login", help="captcha OCR 登入，寫入 data/tokens.json")
    sub.add_parser("sso-url", help="印出活的公務雲 OAuth URL（cloud2 已死）")
    p_sso = sub.add_parser("sso", help="用回跳 URL / sessionId 換 JWT，寫 data/tokens.json")
    p_sso.add_argument("url", nargs="?", default="", help="回跳 URL（也可不填，改從標準輸入貼）")
    p_sso.add_argument("--callback", default="", help="瀏覽器回跳的完整 URL")
    p_sso.add_argument("--session-id", default="", help="sessionId 或 OAuth code")
    p_sso.add_argument("--file", default="", help="從檔案讀回跳 URL（避開 bash &）")
    sub.add_parser("token", help="檢查 JWT 剩餘秒數；到期前 180s 才 refresh，400 則停")
    sub.add_parser("run", help="主源 EPCR 5/6；沒 JWT 才 E1")
    args = parser.parse_args(argv)
    _setup_log(args.verbose)
    return {
        "probe": cmd_probe,
        "listen": cmd_listen,
        "dests": cmd_dests,
        "ping": cmd_ping,
        "login": cmd_login,
        "sso-url": cmd_sso_url,
        "sso": cmd_sso,
        "token": cmd_token,
        "run": cmd_run,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
