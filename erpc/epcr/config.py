"""環境。預設 SOCKS5、不登入。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("EPCR_DATA_DIR", ROOT / "data"))

DEFAULT_PROXY = "socks5h://202.160.76.179:1080"
FALLBACK_PROXIES = (
    "socks5h://202.160.76.178:1080",
    "socks5h://202.160.76.177:1080",
    "socks5h://202.160.76.176:1080",
    "socks5h://202.160.76.174:1080",
    "socks5h://202.160.76.181:10808",
)


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def _flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
        "",
    }


_load_dotenv(ROOT / ".env")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def parse_proxy(url: str) -> tuple[str, int, str]:
    """回 (host, port, proxy_type) ；type 為 socks5h / socks5 / http。"""
    text = (url or "").strip()
    if not text:
        raise ValueError("empty proxy")
    if "://" not in text:
        text = "socks5h://" + text
    parsed = urlparse(text)
    host = parsed.hostname or ""
    port = int(parsed.port or 1080)
    scheme = (parsed.scheme or "socks5h").lower()
    if scheme in {"socks5", "socks5h", "socks4", "socks4a", "http"}:
        ptype = scheme
    else:
        ptype = "socks5h"
    if not host:
        raise ValueError(f"bad proxy {url}")
    return host, port, ptype


class Config:
    base_4000: str = os.environ.get("EPCR_BASE_4000", "https://epcr.tpf.gov.tw:4000").rstrip("/")
    base_4005: str = os.environ.get("EPCR_BASE_4005", "https://epcr.tpf.gov.tw:4005").rstrip("/")
    proxy: str = (
        os.environ.get("EPCR_PROXY")
        or os.environ.get("ALL_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or DEFAULT_PROXY
    ).strip()
    fallback_proxies: tuple[str, ...] = tuple(
        x.strip()
        for x in os.environ.get("EPCR_PROXY_FALLBACK", ",".join(FALLBACK_PROXIES)).split(",")
        if x.strip()
    )
    ssl_verify: bool = _flag("EPCR_SSL_VERIFY", "0")
    auth: str = os.environ.get("EPCR_AUTH", "https://epcr.tpf.gov.tw:4004").rstrip("/")
    user: str = os.environ.get("EPCR_USER", "").strip()
    password: str = os.environ.get("EPCR_PASSWORD", "").strip()
    sso_session: str = os.environ.get("EPCR_SSO_SESSION", "").strip()
    token: str = os.environ.get("EPCR_TOKEN") or os.environ.get("EPCR_JWT") or ""
    refresh_token: str = os.environ.get("EPCR_REFRESH_TOKEN", "").strip()
    cookie_path: Path = DATA_DIR / "cookies.txt"
    captcha_path: Path = DATA_DIR / "captcha.gif"
    token_path: Path = Path(os.environ.get("EPCR_TOKEN_FILE", DATA_DIR / "tokens.json"))
    poll_sec: float = float(os.environ.get("EPCR_POLL_SEC", "10"))
    refresh_before_sec: float = float(os.environ.get("EPCR_REFRESH_BEFORE_SEC", "180"))
    token_check_sec: float = float(os.environ.get("EPCR_TOKEN_CHECK_SEC", "300"))
    ntpc_only: bool = _flag("EPCR_NTPC_ONLY", "0")
    taipei_only: bool = _flag("EPCR_TAIPEI_ONLY", "1")
    bot_token: str = os.environ.get("EPCR_BOT_TOKEN") or os.environ.get("TEST_BOT_TOKEN") or ""
    chat_id: str = os.environ.get("EPCR_CHAT_ID") or os.environ.get("TEST_CHAT_ID") or ""
    dry_run: bool = _flag("EPCR_DRY_RUN", "0")
    data_dir: Path = DATA_DIR
    seen_path: Path = Path(os.environ.get("EPCR_SEEN", DATA_DIR / "seen.json"))
    log_path: Path = (
        Path(os.environ.get("EPCR_LOG")) if os.environ.get("EPCR_LOG") else DATA_DIR / "epcr.log"
    )
    timeout: float = float(os.environ.get("EPCR_TIMEOUT", "20"))
    ua: str = os.environ.get(
        "EPCR_UA",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    ping_interval: float = float(os.environ.get("EPCR_PING_SEC", "20"))
    ws_url: str = os.environ.get(
        "EPCR_WS",
        "wss://epcr.tpf.gov.tw:4000/socket.io/?EIO=4&transport=websocket",
    )
    ws_url_alt: str = os.environ.get(
        "EPCR_WS_ALT",
        "wss://epcr.tpf.gov.tw:4005/socket.io/?EIO=4&transport=websocket",
    )
    origin: str = os.environ.get("EPCR_ORIGIN", "https://epcr.tpf.gov.tw:4000")
    e1_enabled: bool = _flag("EPCR_E1_ENABLED", "1")
    e1_url: str = os.environ.get(
        "EPCR_E1_URL",
        "https://e1.ntpc.gov.tw/v3/api/map/dynamic/layer/rescue",
    )
    e1_interval: float = float(os.environ.get("EPCR_E1_INTERVAL_SEC", "4"))
    e1_backup: bool = _flag("EPCR_E1_BACKUP", "1")
    emic_backup: bool = _flag("EPCR_EMIC_BACKUP", "0")
    emic_kml: Path = Path(
        os.environ.get("EPCR_EMIC_KML", "/var/lib/emic-push/emic_378.kml")
    )
    emic_max_age_min: float = float(os.environ.get("EPCR_EMIC_MAX_AGE_MIN", "90"))
    go_status_ids: tuple[int, ...] = tuple(
        int(x)
        for x in os.environ.get("EPCR_GO_STATUS_IDS", "5,6").split(",")
        if x.strip().isdigit()
    ) or (5, 6)

    def proxy_chain(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in (self.proxy, *self.fallback_proxies):
            if item and item not in seen:
                seen.add(item)
                out.append(item)
        return out


CFG = Config()


@dataclass
class ProxySpec:
    url: str
    host: str
    port: int
    type: str
