"""Telegram broadcast handler - sends Taipei City ePCR events to specified Telegram group."""
from __future__ import annotations
import logging
import threading
import time
import json
import urllib.request
import urllib.parse
from .config import CFG, ROOT
from .districts import is_ntpc_address

log = logging.getLogger("epcr.telegram")

TELEGRAM_API = "https://api.telegram.org/bot"

def _get_bot_token() -> str:
    """Use CFG.bot_token if available (from .env), fall back to hardcoded."""
    return CFG.bot_token or "8314772330:***"

# Your Taipei test group ID (supergroup format: -100...})
DEFAULT_CHAT_ID = "-1004487319117"

def _tg_api(method: str, data: dict) -> dict:
    """Call Telegram API with bot token."""
    token = _get_bot_token()
    url = f"{TELEGRAM_API}{token}/{method}"
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Telegram API error: %s", e)
        return {"ok": False, "error": str(e)}

def load_chat_id() -> str:
    """Load chat ID from config file or use default."""
    config_file = ROOT / "data" / "telegram_config.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            cid = str(cfg.get("chat_id") or DEFAULT_CHAT_ID).strip()
            if cid:
                return cid
        except Exception:
            pass
    return DEFAULT_CHAT_ID


def auto_bind_group(chat_id: str = "") -> str:
    """Auto-discover the first supergroup chat_id via getUpdates.
    Used by auth.py to bind the user's Telegram group after login."""
    token = _get_bot_token()
    if not token:
        return ""
    result = _tg_api("getUpdates", {})
    if not result.get("ok"):
        return ""
    for upd in result.get("result", []):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = str(chat.get("id", ""))
        if cid.startswith("-100") and cid:
            return cid
    return str(chat_id) or load_chat_id()

def broadcast(message: str, *, parse_mode: str = "Markdown") -> bool:
    """Send message to configured Telegram chat."""
    cid = load_chat_id()
    if not cid:
        log.warning("No Telegram group bound - cannot broadcast")
        return False
    result = _tg_api("sendMessage", {
        "chat_id": cid,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    })
    return result.get("ok", False)

def is_taipei_case(case_data: dict) -> bool:
    """Filter: only Taipei City cases (not New Taipei)."""
    addr = str(case_data.get("address", case_data.get("realaddress", case_data.get("location", ""))))
    if not addr:
        return True  # If no address, don't filter out
    # Exclude New Taipei addresses
    if is_ntpc_address(addr):
        return False
    # Check if it's Taipei City address
    if "台北" in addr or "臺北" in addr:
        return True
    # Also accept addresses starting with Taipei districts
    # (handled by negation - not being NTPC means likely Taipei)
    return True

def format_case(case_data: dict) -> str:
    """Format case data for Telegram broadcast."""
    case_no = case_data.get("caseNo", case_data.get("caseno", "N/A"))
    addr = case_data.get("address", case_data.get("realaddress", "N/A"))
    case_type = case_data.get("type", case_data.get("casetypename", "N/A"))
    timestamp = case_data.get("time", case_data.get("timestamp", ""))
    coords = case_data.get("coordinate", case_data.get("coords", case_data.get("latlng", "")))

    text = "*🚨 Taipei City Emergency Case*"
    text += f"\n*Case:* `{case_no}`"
    text += f"\n*Address:* {addr}"
    text += f"\n*Type:* {case_type}"
    if timestamp:
        text += f"\n*Time:* `{timestamp}`"
    if coords:
        text += f"\n*Coords:* `{coords}`"
    text += "\n\n#TaipeiEmergency"
    return text

class TaipeiBroadcaster:
    """Listens for ePCR WebSocket events and broadcasts Taipei cases only."""
    def __init__(self):
        self._running = threading.Event()
        self._thread = None

    def start(self):
        self._running.set()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        log.info("Taipei City broadcaster started - listening on port 4000 WebSocket")

    def stop(self):
        self._running.clear()
        log.info("Broadcaster stopping...")

    def _listen_loop(self):
        from .polling import Capture
        cap = Capture()
        log.info("Connecting to WebSocket: wss://epcr.tpf.gov.tw:4000/socket.io/")
        while self._running.is_set():
            try:
                packets = cap.run(seconds=30, upgrade=True, emit=True)
                for pkt in packets:
                    self._process_packet(pkt)
            except Exception as e:
                log.warning("Broadcast loop error: %s", e)
                time.sleep(5)

    def _process_packet(self, pkt: dict):
        """Process a single packet and broadcast if Taipei case."""
        kind = pkt.get("kind")
        if kind != "event":
            return
        name = pkt.get("name", "")
        data = pkt.get("data", {})
        if not isinstance(data, dict):
            return

        # Handle dispatch events (new cases)
        if name in ("dispatch", "new_case", "case_update"):
            if is_taipei_case(data):
                case_text = format_case(data)
                log.info("Broadcasting Taipei case: %s -> %s",
                        data.get("caseNo", "N/A"),
                        load_chat_id())
                success = broadcast(case_text)
                if not success:
                    log.warning("Failed to broadcast case to Telegram")

broadcaster = TaipeiBroadcaster()