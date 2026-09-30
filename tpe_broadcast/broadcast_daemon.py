#!/usr/bin/env python3
"""
TOCP Broadcast Daemon

Auto-pulls up:
  1. Starts login.py --daemon (auto-renews TPE 119 JWT every 2.5h)
  2. Monitors it — auto-restarts on disconnect/crash
  3. Polls citizenCase/search API -> TWD coords -> WGS84 -> reverse-geocode -> push
  4. Only pushes addresses with 號 (building number) — fuzzy skipped
  5. Deduplicates cases by case ID, never re-pushes

Usage:
  python3 broadcast_daemon.py                          # daemon mode (poll TPE 119 API)
  python3 broadcast_daemon.py --coords 25.038779,121.512820  # one-shot push
  python3 broadcast_daemon.py --interval 60             # poll every 60s
  python3 broadcast_daemon.py --city 01                 # Taipei 119 (default)
"""
import os, sys, json, time, subprocess, signal, threading, argparse
import urllib.request, urllib.parse
import requests

# ── Config ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_SCRIPT = os.path.join(BASE_DIR, "login.py")
TOKEN_FILE = os.path.join(BASE_DIR, "tpe119_token.json")

# SOCKS5 proxy for TPE 119 API requests
PROXY = "socks5://202.160.76.166:11086"
PROXIES = {"http": PROXY, "https": PROXY}

# ── IPS (Taiwan Fire Dept dispatch) — authenticated, real-time unit dispatch ──
IPS_COOKIE_FILE = os.path.join(
    os.environ.get("HERMES_CACHE_DIR", os.path.join(os.environ.get("HOME", "/tmp"), ".hermes/cache/scratch")),
    "ips_dispatch_cache.json"
)
IPS_CACHE_TTL = 30  # reuse parsed dispatch data within 30s to avoid re-login

# ── EPCR (Taipei) — port 4008, no auth needed for /MciCaseRecords ──
EPCR_PROXY = "socks5://202.160.76.157:11082"
EPCR_PROXIES = {"http": EPCR_PROXY, "https": EPCR_PROXY}
EPCR_MCI_URL = "https://epcr.tpf.gov.tw:4008/MciCaseRecords"
# Env vars for subprocess (login.py --daemon) — passed explicitly in start_login_daemon

# Import telegram config from tocp_tpe_broadcast.py (avoids duplicating tokens)
sys.path.insert(0, BASE_DIR)
from tocp_tpe_broadcast import TELEGRAM_BOTS, GROUP_ID

# ── Reverse-geocoding ───────────────────────────────────────────
try:
    from geocoding import reverse_geocode, forward_geocode
    HAS_GEOCODING = True
except ImportError:
    HAS_GEOCODING = False

# ── TWD97 → WGS84 coordinate conversion ─────────────────────────
try:
    from pyproj import Transformer
    _twd = Transformer.from_crs("epsg:3826", "epsg:4326", always_xy=True)

    def twd_to_wgs84(cs_x, cs_y):
        """Convert TWD97 (EPSG:3826) coordinates to WGS84 (lat, lng)."""
        lng, lat = _twd.transform(cs_x, cs_y)
        return lat, lng
    HAS_TWD = True

    # Reverse transform: WGS84 → TWD97 (for EPCR address geocoding)
    _wgs_to_twd = Transformer.from_crs("epsg:4326", "epsg:3826", always_xy=True)

    def wgs_to_twd97(lat, lng):
        """Convert WGS84 (lat, lng) to TWD97 (cs_x, cs_y)."""
        cs_x, cs_y = _wgs_to_twd.transform(lng, lat)
        return cs_x, cs_y
except ImportError:
    HAS_TWD = False

# ── Case tracking ────────────────────────────────────────────────
_pushed_cases = set()  # track pushed case IDs to avoid duplicates
_address_counts = {}   # track address → count for OHCA detection
# Cross-cycle OHCA tracking: addr_key → (timestamp, case_data)
_recent_scenes = {}
SCENE_WINDOW_SECONDS = 90  # consider OHCA if same address within 90s

# ── Auto-renew daemon for login.py ──────────────────────────────
_login_process = None
_login_lock = threading.Lock()
_running = True


def start_login_daemon():
    """Start login.py --daemon as a subprocess for auto token renewal."""
    global _login_process
    with _login_lock:
        if _login_process and _login_process.poll() is None:
            return  # already running
        _login_process = subprocess.Popen(
            [sys.executable, LOGIN_SCRIPT, "--daemon"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=BASE_DIR,
            env={**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY,
                 "http_proxy": PROXY, "https_proxy": PROXY}
        )
        print(f"[+] login.py --daemon started (pid={_login_process.pid})", flush=True)


def monitor_login_daemon():
    """Monitor login.py subprocess, restart on crash."""
    global _login_process, _running
    while _running:
        if _login_process:
            rc = _login_process.poll()
            if rc is not None:
                print(f"[!] login.py exited (rc={rc}) — restarting in 5s...", flush=True)
                time.sleep(5)
                start_login_daemon()
        time.sleep(5)


def get_valid_token():
    """Get current TPE 119 token from file, auto-renew via login.py if expired.
    Returns (token, jsessionid) tuple.
    """
    if os.path.exists(TOKEN_FILE):
        try:
            data = json.load(open(TOKEN_FILE))
            token = data.get("token", "")
            exp = data.get("exp", 0)
            if token and time.time() < exp - 9000:  # 2.5h safety margin
                return token, data.get("jsessionid", "")
        except Exception:
            pass
    # Token expired or missing — trigger login.py --check
    subprocess.run([sys.executable, LOGIN_SCRIPT, "--check"],
                   cwd=BASE_DIR, timeout=120,
                   env={**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY,
                        "http_proxy": PROXY, "https_proxy": PROXY})
    if os.path.exists(TOKEN_FILE):
        data = json.load(open(TOKEN_FILE))
        return data.get("token", ""), data.get("jsessionid", "")
    return None, None


def fetch_tpe119_cases(city_code="01"):
    """Fetch real-time cases from TPE 119 citizenCase/search API.

    Uses login.py's fetch_cases() which handles token + JSESSIONID.
    Returns list of case dicts or empty list.
    """
    if city_code != "01":
        return []
    sys.path.insert(0, BASE_DIR)
    from login import AutoLoginService119
    bot = AutoLoginService119()
    cases = bot.fetch_cases()
    if cases is None:
        return []
    return cases


def push_to_telegram(city_code, address, coords, case_data=None):
    """Push a single case to Telegram group.

    Pushes whatever the page shows — address, coords, case type, etc.
    Only called for addresses with 號 (building number).
    """
    token = TELEGRAM_BOTS[city_code]["token"]

    # Build message from real case data if available
    if case_data:
        in_time = case_data.get("inTime", "")
        cs_kind = case_data.get("csKindName", "")
        cs_code = case_data.get("csCodeName", "")
        status = case_data.get("caseStatus", "")
        people = case_data.get("peopleCount", "")
        cars = case_data.get("dispCarList", "")
    else:
        in_time = ""
        cs_kind = ""
        cs_code = ""
        status = ""
        people = ""
        cars = ""

    msg = (
        f"🚨 <b>緊急案件 / Case Dispatch</b>\n\n"
        f"🏙️ <b>縣市:</b> {TELEGRAM_BOTS[city_code]['city']}\n"
        f"📍 <b>地址:</b> {address}\n"
        f"🪪 <b>類別:</b> {cs_kind} / {cs_code}\n"
        f"🚑 <b>出勤:</b> {status}\n"
        f"👥 <b>人數:</b> {people}\n"
        f"🚒 <b>車輛:</b> {cars}\n"
        f"⏰ <b>時間:</b> {in_time}\n"
        f"🌐 <b>座標:</b> {coords[0]:.6f}, {coords[1]:.6f}\n"
    )

    payload = {
        "chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"
    }
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            timeout=10,
            data=payload
        )
        r = resp.json()
        mid = r.get("result", {}).get("message_id", "?")
        print(f"  [PUSH] {address} → msg_id={mid}", flush=True)
        return True
    except Exception as e:
        print(f"  [ERR]  Telegram push failed: {e}", flush=True)
        return False


def _case_addr_key(case):
    """Generate a normalized address key for grouping OHCA cases.

    Uses TWD97 coordinates when available; falls back to address-string
    hash for cases without geocoding (e.g. IPS dispatch without forward-geocode).
    """
    x = case.get("csX", 0)
    y = case.get("csY", 0)
    if x and y:
        return f"{round(x, 0)}:{round(y, 0)}"
    # Fallback: deterministic hash of address string (same addr → same key)
    addr = case.get("csPlace", "")
    return f"addr_{abs(hash(addr)) % 1000000}"


def push_ohca_alert(city_code, case_list, epcr=False, num_amb=0):
    """Push an OHCA suspicion alert when 2+ ambulances dispatched to same address."""
    if not case_list:
        return
    case = case_list[0]
    cs_x = float(case.get("csX", 0) or 0)
    cs_y = float(case.get("csY", 0) or 0)

    # Address: use csPlace directly if no coordinates (forward-geocode fallback)
    addr = case.get("csPlace", "")
    lat, lng = 0.0, 0.0
    if not cs_x or not cs_y:
        # No coordinates available — use csPlace as-is for display
        pass
    else:
        if HAS_TWD:
            lat, lng = twd_to_wgs84(cs_x, cs_y)
        else:
            print(f"  [FAIL] pyproj not available", flush=True)
            return
        # Try reverse-geocode for a cleaner address; keep csPlace as fallback
        if HAS_GEOCODING:
            geo = reverse_geocode(lat, lng)
            r_addr = geo.get("formatted_address", "")
            if r_addr and "號" in r_addr:
                addr = r_addr

    token = TELEGRAM_BOTS[city_code]["token"]
    car_list = [c.get("dispCarList", "") for c in case_list]
    times = [c.get("inTime", "") for c in case_list]
    amb_count = num_amb if num_amb >= 2 else len(case_list)
    src = "EPCR" if epcr else ("IPS" if num_amb >= 2 else "119")
    coord_str = f"{lat:.6f}, {lng:.6f}" if (lat and lng) else "未知 (地址哈希分組)"
    msg = (
        f"⚠️ <b>疑似OHCA/OHCA懷疑</b>\n"
        f"🚨 <b>{amb_count} 台救護車前往同一地址</b>\n\n"
        f"🏙️ <b>縣市:</b> {TELEGRAM_BOTS[city_code]['city']}\n"
        f"📍 <b>地址:</b> {addr}\n"
        f"⏰ <b>時間:</b> {', '.join(t for t in times if t)}\n"
        f"🚑 <b>車輆:</b> {'; '.join(c for c in car_list if c)}\n"
        f"🌐 <b>座標:</b> {coord_str}\n"
        + (f"📊 <b>資料來源:</b> EPCR 官方 (車數: {num_amb} 輆)\n"
           if epcr else (f"📊 <b>資料來源:</b> IPS 119 即時派遣 (單位數: {num_amb} 隊)\n"
                         if num_amb >= 2 else ""))
    )
    payload = {
        "chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"
    }
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            timeout=10, data=payload
        )
        r = resp.json()
        mid = r.get("result", {}).get("message_id", "?")
        print(f"  [OHCA] {addr} ({amb_count} cars, {src}) → msg_id={mid}", flush=True)
    except Exception as e:
        print(f"  [ERR]  OHCA push failed: {e}", flush=True)


def process_case(case, city_code):
    """Process a single case from the API: TWD coords → WGS84 → geocode → push."""
    # Deduplicate by case ID
    # Deduplicate by composite key (no caseId field in API response)
    case_id = f"{case.get('inTime','')}_{round(case.get('csX',0),4)}_{round(case.get('csY',0),4)}"
    if case_id and case_id in _pushed_cases:
        return
    if case_id:
        _pushed_cases.add(case_id)

    # Get TWD coordinates from API response
    cs_x = case.get("csX") or case.get("x")
    cs_y = case.get("csY") or case.get("y")
    if not cs_x or not cs_y:
        print(f"  [SKIP] No coordinates in case", flush=True)
        return

    # Convert TWD → WGS84
    if HAS_TWD:
        lat, lng = twd_to_wgs84(float(cs_x), float(cs_y))
    else:
        print(f"  [FAIL] pyproj not available for TWD conversion", flush=True)
        return

    # Reverse-geocode to get full address with 號
    if not HAS_GEOCODING:
        print(f"  [FAIL] geocoding module not available", flush=True)
        return

    geo = reverse_geocode(lat, lng)
    if not geo["success"]:
        print(f"  [FAIL] reverse-geocode failed for ({lat}, {lng})", flush=True)
        return

    addr = geo["formatted_address"]
    has_no = geo.get("has_building_no", False)
    street_num = geo.get("street_number", "")

    print(f"  [GEOCODE] ({lat:.6f}, {lng:.6f}) → {addr}"
          f"{' (' + street_num + ')' if street_num else ''}", flush=True)

    # Skip if no 號 (building number) — fuzzy address, not scene-level
    if not has_no and "號" not in addr:
        print(f"  [SKIP] {addr} — no 號, fuzzy address", flush=True)
        return

    # Push to Telegram with real case data
    push_to_telegram(city_code, addr, (lat, lng), case_data=case)


def process_coords(coords_str, city_code="01"):
    """One-shot: take a coordinates string (lat,lng), reverse-geocode, push."""
    if "," not in coords_str:
        print(f"[!] Format: lat,lng (e.g. 25.038779,121.512820)", flush=True)
        return
    lat_s, lng_s = coords_str.split(",")
    coords = (float(lat_s.strip()), float(lng_s.strip()))

    if not HAS_GEOCODING:
        print("[!] geocoding module not available", flush=True)
        return

    geo = reverse_geocode(coords[0], coords[1])
    if not geo["success"]:
        print(f"  [FAIL] reverse-geocode failed for {coords}", flush=True)
        return

    addr = geo["formatted_address"]
    has_no = geo.get("has_building_no", False)
    street_num = geo.get("street_number", "")
    print(f"  [GEOCODE] {coords} → {addr}"
          f"{' (' + street_num + ')' if street_num else ''}", flush=True)

    if not has_no and "號" not in addr:
        print(f"  [SKIP] {addr} — no 號, fuzzy address", flush=True)
        return

    push_to_telegram(city_code, addr, coords)


def fetch_epcr_mci():
    """Fetch active MCI/OHCA records from Taipei EPCR port 4008 (no auth).

    Only returns records that:
    - isSimulation == False (not a drill)
    - Status != '結束' (still active/ongoing)
    - Have a non-null address
    """
    # Try multiple proxies — one may be temporarily down
    epcr_proxies_list = [
        {"http": "socks5://202.160.76.157:11082", "https": "socks5://202.160.76.157:11082"},
        {"http": "socks5://202.160.76.165:11082", "https": "socks5://202.160.76.165:11082"},
        {"http": "socks5://202.160.76.166:11086", "https": "socks5://202.160.76.166:11086"},
        {"http": "socks5://202.160.76.165:11081", "https": "socks5://202.160.76.165:11081"},
    ]
    r = None
    for proxy_attempt in epcr_proxies_list:
        try:
            r = requests.get(
                EPCR_MCI_URL,
                params={"limit": 50},
                proxies=proxy_attempt,
                timeout=15,
                verify=False,
            )
            if r.status_code == 200:
                break
            r = None
        except Exception:
            r = None

    if r is None:
        print(f"[ERR] EPCR MCI fetch failed: all proxies exhausted", flush=True)
        return []

    if r.status_code != 200:
        print(f"[ERR] EPCR MCI returned {r.status_code}", flush=True)
        return []

    records = r.json()
    if not isinstance(records, list):
        return []

    active = [
        rec for rec in records
        if rec.get("isSimulation") is False
        and rec.get("Status", {}).get("name") != "結束"
        and rec.get("address")
    ]
    if active:
        print(f"[+] EPCR: {len(active)} active MCI records (out of {len(records)} total)", flush=True)
    return active


def process_epcr_case(epcr_record, city_code):
    """Process an EPCR MCI record: address → forward-geocode → TWD97 → push.

    Only pushes records that have occurred (isSimulation=False, active status).
    Fuzzy addresses (no 號) are skipped.
    """
    case_id = f"epcr_{epcr_record.get('id', '')}"
    if case_id in _pushed_cases:
        return
    if case_id:
        _pushed_cases.add(case_id)

    address = epcr_record.get("address", "")
    if not address:
        return

    if not HAS_GEOCODING:
        print(f"  [FAIL] geocoding module not available for EPCR", flush=True)
        return

    # Forward geocode: address → lat/lng (WGS84)
    geo = forward_geocode(address)
    if not geo["success"]:
        print(f"  [FAIL] EPCR forward-geocode failed for {address}", flush=True)
        return

    lat, lng = geo["lat"], geo["lng"]
    if not lat or not lng:
        print(f"  [FAIL] No coordinates for EPCR address {address}", flush=True)
        return

    # Convert WGS84 → TWD97 so EPCR cases can be grouped with TPE 119 cases
    if HAS_TWD:
        cs_x, cs_y = wgs_to_twd97(lat, lng)
    else:
        cs_x, cs_y = lng * 100000, lat * 100000

    # Build a case dict compatible with the service119 pipeline
    case = {
        "inTime": epcr_record.get("createdAt", ""),
        "csPlace": address,
        "csX": cs_x,
        "csY": cs_y,
        "caseStatus": "到達現場",
        "dispCarList": f"EPCR {epcr_record.get('numberOfAmbulance', '?')} 輛",
        "epcr_id": epcr_record.get("id", ""),
        "_lat": lat,
        "_lng": lng,
    }

    # Check for 號 (building number) — skip fuzzy addresses
    has_no = "號" in address
    if not has_no:
        print(f"  [SKIP] EPCR {address} — no 號, fuzzy", flush=True)
        return

    print(f"  [EPCR] {address} → ({lat:.6f}, {lng:.6f})", flush=True)

    # OHCA check: numberOfAmbulance >= 2 means multiple ambulances dispatched
    num_amb = epcr_record.get("numberOfAmbulance", 0)
    if num_amb >= 2:
        push_ohca_alert(city_code, [case], epcr=True, num_amb=num_amb)
    else:
        # Standard push
        push_to_telegram(city_code, address, (lat, lng), case_data=case)
    _pushed_cases.add(case_id)


# ── EPCR case conversion ─────────────────────────────────────────
_epcr_geocache = {}  # address → (lat, lng) cache to avoid repeated forward geocoding


def epcr_record_to_case(rec):
    """Convert an EPCR MCI record to a service119-compatible case dict.

    Used by daemon_loop to merge EPCR records with TPE 119 API results.
    Forward-geocodes address → lat/lng → TWD97 for addr_key compatibility.
    Returns None if already processed, fuzzy (no 號), or geocode fails.
    """
    epcr_id = rec.get("id", "")
    case_ext_id = f"epcr_{epcr_id}"
    if case_ext_id in _pushed_cases:
        return None
    _pushed_cases.add(case_ext_id)

    address = rec.get("address", "")
    if not address:
        return None
    # Skip fuzzy addresses (no 號 = building number)
    if "號" not in address:
        print(f"  [SKIP] EPCR {address} — no 號, fuzzy", flush=True)
        return None

    if not HAS_GEOCODING:
        print(f"  [FAIL] geocoding module not available for EPCR", flush=True)
        return None

    # Forward geocode with caching (avoid repeated calls for same address)
    if address in _epcr_geocache:
        lat, lng = _epcr_geocache[address]
    else:
        geo = forward_geocode(address)
        if not geo["success"]:
            print(f"  [FAIL] EPCR forward-geocode failed for {address}", flush=True)
            return None
        lat, lng = geo.get("lat"), geo.get("lng")
        if not lat or not lng:
            print(f"  [FAIL] No coordinates for EPCR address {address}", flush=True)
            return None
        _epcr_geocache[address] = (lat, lng)

    # Convert WGS84 → TWD97 for addr_key compatibility with service119 cases
    if HAS_TWD:
        cs_x, cs_y = wgs_to_twd97(lat, lng)
    else:
        cs_x, cs_y = lng * 100000, lat * 100000

    print(f"  [EPCR] {address} → ({lat:.6f}, {lng:.6f})", flush=True)

    return {
        "inTime": rec.get("createdAt", ""),
        "csPlace": address,
        "csX": cs_x,
        "csY": cs_y,
        "caseStatus": "到達現場",
        "dispCarList": f"EPCR {rec.get('numberOfAmbulance', '?')} 輆",
        "epcr_id": epcr_id,
        "numberOfAmbulance": rec.get("numberOfAmbulance", 0),
    }


_ips_dispatch_cache = {}  # address → case dict cache for IPS dispatch
_ips_cache_time = 0

def fetch_ips_dispatch_with_cache():
    """Fetch IPS dispatch cases with 30s cache to avoid repeated re-login."""
    global _ips_cache_time
    now = time.time()
    if _ips_cache_time and (now - _ips_cache_time) < IPS_CACHE_TTL:
        return _ips_dispatch_cache.get("cases", [])
    # Re-fetch
    try:
        sys.path.insert(0, BASE_DIR)
        import ips_dispatch_handler
        cases = ips_dispatch_handler.fetch_ips_dispatch()
        _ips_dispatch_cache["cases"] = cases
        _ips_cache_time = now
        return cases
    except Exception as e:
        print(f"  [ERR] IPS dispatch handler error: {e}", flush=True)
        return []


_ips_geocache = {}  # address → (lat, lng) cache for IPS addresses


def ips_dispatch_to_case(ips_case, city_code):
    """Convert an IPS dispatch case dict to a service119-compatible case dict.

    Forward-geocodes the address → WGS84 → TWD97 for addr_key compatibility.
    Maps '處理中' → '到達現場' (in-progress = units on scene).
    """
    case_id = f"ips_{ips_case.get('case_no', '')}"
    if case_id in _pushed_cases:
        return None
    _pushed_cases.add(case_id)

    address = ips_case.get("address", "")
    if not address:
        return None

    # Skip fuzzy addresses (no 號 = building number)
    if "號" not in address:
        return None

    num_units = ips_case.get("num_units", 0)  # moved before geocoding for error msg
    status_text = ips_case.get("status", "")

    if not HAS_GEOCODING:
        print(f"  [FAIL] geocoding module not available for IPS", flush=True)
        return None

    # Forward geocode with caching
    if address in _ips_geocache:
        lat, lng = _ips_geocache[address]
    else:
        geo = forward_geocode(address)
        if not geo["success"]:
            # Geocoding failed — use address hash for coord-based addr_key
            # OHCA detection via numberOfAmbulance still works (push_ohca_alert handles 0 coords)
            print(f"  [IPS] {address} — geocoding failed, using address-hash key ({num_units} units)", flush=True)
            if HAS_TWD:
                cs_x, cs_y = wgs_to_twd97(0, 0)  # placeholder — addr_key will use hash fallback
            else:
                cs_x, cs_y = 0.0, 0.0
            # Fall through to return case dict without coordinates
            lat, lng = None, None
        else:
            lat, lng = geo.get("lat"), geo.get("lng")
            if not lat or not lng:
                print(f"  [FAIL] No coordinates for IPS address {address}", flush=True)
                return None
        if lat is not None:
            _ips_geocache[address] = (lat, lng)

    # Convert WGS84 → TWD97 for addr_key compatibility with service119/EPCR cases
    if lat is not None and HAS_TWD:
        cs_x, cs_y = wgs_to_twd97(lat, lng)
    elif lat is None:
        cs_x, cs_y = 0.0, 0.0  # will trigger addr_key hash fallback
    elif lat and lng:
        cs_x, cs_y = lng * 100000, lat * 100000  # HAS_TWD not available, use raw
    else:
        cs_x, cs_y = 0.0, 0.0  # fallback

    # Map status: 處理中 (in progress) → 到達現場 (arrived at scene)
    # For OHCA pipeline, "in progress" = units are on scene
    status = "到達現場" if "處理中" in ips_case.get("status", "") else ips_case.get("status", "")

    # Build unit string: e.g. "第一大隊-華山分隊、忠孝分隊、雙園分隊、龍山分隊"
    units = ips_case.get("units", [])
    if units:
        # Use first unit's prefix and append all suffixes
        parts = []
        prefix = ""
        for u in units:
            if "-" in u:
                p, s = u.split("-", 1)
                prefix = p
                parts.append(s)
            else:
                parts.append(u)
        join_str = "、".join(parts)
        disp_str = f"{prefix}-{join_str}" if prefix else join_str
    else:
        disp_str = ""

    if lat is not None:
        print(f"  [IPS] {address} → ({lat:.6f}, {lng:.6f}) — {num_units} units", flush=True)
    else:
        print(f"  [IPS] {address} — {num_units} units (geocoding failed, hash key)", flush=True)

    return {
        "inTime": ips_case.get("last_modified", ""),
        "csPlace": address,
        "csX": cs_x,
        "csY": cs_y,
        "caseStatus": status,
        "dispCarList": disp_str,
        "numberOfAmbulance": num_units,  # dispatched unit count
        "ips_case_no": ips_case.get("case_no", ""),
    }


def daemon_loop(interval=60, city_code="01"):
    """Main daemon: keep login alive, poll API for new cases, push."""
    global _running
    print(f"\n🛡️ Broadcast Daemon starting "
          f"(interval={interval}s, city={city_code})", flush=True)

    # Start login daemon for auto token renewal
    start_login_daemon()
    t = threading.Thread(target=monitor_login_daemon, daemon=True)
    t.start()

    print(f"[*] Polling citizenCase/search every {interval}s...", flush=True)

    while _running:
        try:
            token, jsession = get_valid_token()
            if token:
                print(f"[+] Token valid: {token[:25]}...", flush=True)
            else:
                print(f"[!] Token unavailable — login.py will auto-renew", flush=True)

            cases = fetch_tpe119_cases(city_code)
            # Also fetch EPCR MCI/OHCA records (Taipei only)
            if city_code == "01":
                epcr_records = fetch_epcr_mci()
                for rec in epcr_records:
                    epcr_case = epcr_record_to_case(rec)
                    if epcr_case:
                        cases.append(epcr_case)
                # Also fetch IPS dispatch cases (CaseUnitMgt.aspx — real-time unit dispatches)
                ips_cases = fetch_ips_dispatch_with_cache()
                for ips_case in ips_cases:
                    ips_dict = ips_dispatch_to_case(ips_case, city_code)
                    if ips_dict:
                        cases.append(ips_dict)
            # Only push cases that have arrived at scene ("到現場")
            scene_cases = [c for c in cases if "到達現場" in (c.get("caseStatus", "") or "")]
            if scene_cases:
                # Sort oldest-first for clean chronological broadcast order
                scene_cases.sort(key=lambda c: c.get("inTime", ""))
                # Group by address for OHCA detection
                by_addr = {}
                for case in scene_cases:
                    case_id = f"{case.get('inTime','')}_{round(case.get('csX',0),4)}_{round(case.get('csY',0),4)}"
                    if case_id and case_id in _pushed_cases:
                        continue
                    addr_key = _case_addr_key(case)
                    by_addr.setdefault(addr_key, []).append(case)
                for addr_key, case_list in by_addr.items():
                    if len(case_list) >= 2:
                        # OHCA: two+ ambulances at same address in this cycle
                        for c in case_list:
                            cid = f"{c.get('inTime','')}_{round(c.get('csX',0),4)}_{round(c.get('csY',0),4)}"
                            _pushed_cases.add(cid)
                        push_ohca_alert(city_code, case_list)
                    else:
                        case = case_list[0]
                        cid = f"{case.get('inTime','')}_{round(case.get('csX',0),4)}_{round(case.get('csY',0),4)}"
                        # OHCA: any single case with numberOfAmbulance >= 2
                        num_amb = case.get("numberOfAmbulance", 0)
                        if num_amb >= 2:
                            is_epcr = case.get("epcr_id") is not None
                            push_ohca_alert(city_code, [case], epcr=is_epcr,
                                            num_amb=num_amb)
                            _pushed_cases.add(cid)
                            continue
                        # Cross-cycle OHCA: was a scene at this address in the last 90s?
                        if addr_key in _recent_scenes:
                            old_case = _recent_scenes[addr_key]
                            push_ohca_alert(city_code, [old_case, case])
                        process_case(case, city_code)
                        _pushed_cases.add(cid)
                # Update recent scene tracking + prune old entries
                now = time.time()
                for case in scene_cases:
                    ak = _case_addr_key(case)
                    _recent_scenes[ak] = case
                for ak in list(_recent_scenes.keys()):
                    if ak not in by_addr:  # address not seen in this cycle — expire it
                        del _recent_scenes[ak]
                new_count = len(by_addr)
                if new_count > 0:
                    print(f"[+] {len(scene_cases)} scene cases, {new_count} addresses processed", flush=True)
            else:
                print(f"[*] No cases or API error", flush=True)
        except Exception as e:
            print(f"[-] Daemon error: {e}", flush=True)

        time.sleep(interval)

    # Cleanup
    if _login_process:
        _login_process.terminate()
        print("[*] login.py daemon stopped", flush=True)
    print("[*] Broadcast Daemon stopped", flush=True)


def _sigint_handler(signum, frame):
    global _running
    _running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOCP Broadcast Auto-Daemon")
    parser.add_argument("--coords", help="One-shot: coordinates to push (lat,lng)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Polling interval seconds (default: 60)")
    parser.add_argument("--city", default="01", choices=list(TELEGRAM_BOTS.keys()),
                        help="City code: 01=Taipei, 05=Taoyuan, 11=Kaohsiung")
    parser.add_argument("--daemon", action="store_true",
                        help="Run as background daemon")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _sigint_handler)
    signal.signal(signal.SIGINT, _sigint_handler)

    if args.coords:
        process_coords(args.coords, args.city)
    else:
        daemon_loop(interval=args.interval, city_code=args.city)
