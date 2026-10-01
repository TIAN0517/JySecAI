import os
import urllib3, requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
_orig_request = requests.Session.request
_fallback_proxies = [
    os.environ.get("TPE_BROADCAST_PROXY", ""),
    "socks5h://52.128.241.106:1080",
    "socks5h://52.128.241.107:1080",
    "socks5h://52.128.241.108:1080",
    "socks5h://52.128.241.109:1080",
    "socks5h://52.128.241.110:1080",
    "socks5h://18.170.56.6:1080",
]
_fallback_proxies = [p for p in _fallback_proxies if p]
def _insecure_request(self, method, url, *args, **kwargs):
    kwargs["verify"] = False
    try:
        return _orig_request(self, method, url, *args, **kwargs)
    except requests.RequestException:
        if kwargs.get("proxies") is not None or not _fallback_proxies:
            raise
        for proxy_url in _fallback_proxies:
            retry_kwargs = dict(kwargs)
            retry_kwargs["proxies"] = {
                "http": proxy_url,
                "https": proxy_url,
            }
            try:
                print(f"[NET] Direct failed; retrying {url} via {proxy_url}", flush=True)
                return _orig_request(self, method, url, *args, **retry_kwargs)
            except requests.RequestException:
                continue
        raise
requests.Session.request = _insecure_request

import multi_dispatcher
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
from concurrent.futures import ThreadPoolExecutor
from scene_policy import (
    ACTIVE_STATUSES, PUBLIC_CASE_URL, PUBLIC_PAGE_URL, has_doorplate,
    is_excluded_location, normalize_address, resolve_scene_address,
    source_scene_address, verify_public_against_login,
)

# ── Config ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_SCRIPT = os.path.join(BASE_DIR, "login.py")
TOKEN_FILE = os.path.join(BASE_DIR, "tpe119_token.json")

# SOCKS5 proxy for TPE 119 API requests
PROXY = None
PROXIES = {}

# ── IPS (Taiwan Fire Dept dispatch) — authenticated, real-time unit dispatch ──
IPS_COOKIE_FILE = os.path.join(
    os.environ.get("HERMES_CACHE_DIR", os.path.join(os.environ.get("HOME", "/tmp"), ".hermes/cache/scratch")),
    "ips_dispatch_cache.json"
)
IPS_CACHE_TTL = 30  # reuse parsed dispatch data within 30s to avoid re-login
LOCK_FILE = "/tmp/broadcast_daemon.lock"

# ── Dispatch caseList endpoint — unauthenticated, real-time emergency cases ──
DISPATCH_CASELIST_URL = "https://service119.119.gov.taipei/service119/citizenCase/caseList"
_dispatch_cache = {}
_dispatch_cache_time = 0
DISPATCH_CACHE_TTL = 10  # match the production poll interval

# Env vars for subprocess (login.py --daemon) — passed explicitly in start_login_daemon

# Import telegram config from tocp_tpe_broadcast.py (avoids duplicating tokens)
sys.path.insert(0, BASE_DIR)
from tocp_tpe_broadcast import TELEGRAM_BOTS, GROUP_ID

# Traffic routing: OHCA alerts can go to a separate group from regular dispatches
# Support multiple target groups per channel for parallel distribution
GROUP_ID_OHCA = None  # Override with --ohca-group-id (comma-separated for multiple)
GROUP_ID_DISPATCH = None  # Override with --dispatch-group-id for regular dispatches
GROUP_ID_OHCA_LIST = []  # Resolved list of target group IDs for OHCA
GROUP_ID_DISPATCH_LIST = []  # Resolved list of target group IDs for dispatches
TELEGRAM_BOT_TOKENS = {}  # Multi-bot config: {city_code: {city, en, token, address, ...}}
_BOT_HEALTH = {}  # Bot health cache: {token_prefix: {ok, last_check, error}}

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

    # Reverse transform: WGS84 → TWD97 (for dispatch address geocoding)
    _wgs_to_twd = Transformer.from_crs("epsg:4326", "epsg:3826", always_xy=True)

    def wgs_to_twd97(lat, lng):
        """Convert WGS84 (lat, lng) to TWD97 (cs_x, cs_y)."""
        cs_x, cs_y = _wgs_to_twd.transform(lng, lat)
        return cs_x, cs_y
except ImportError:
    HAS_TWD = False

# ── Case tracking ────────────────────────────────────────────────
def _safe_round(val, ndigits=4):
    """round() that handles None / missing values safely."""
    return round(float(val or 0), ndigits)

_pushed_cases = set()  # track pushed case IDs to avoid duplicates
_pushed_cases_file = "/tmp/broadcast_pushed_cases.json"  # persisted dedup (survives restart)
# Addresses that already triggered OHCA — prevents cross-cycle repeat at same address
_ohca_addr_keys = set()
_address_counts = {}   # track address → count for OHCA detection
# Cross-cycle OHCA tracking: addr_key → (timestamp, case_data)
_recent_scenes = {}
SCENE_WINDOW_SECONDS = 90  # consider OHCA if same address within 90s

# ── Auto-renew daemon for login.py ──────────────────────────────
_login_process = None
_login_lock = threading.Lock()
_running = True


def load_pushed_cases():
    """Load persisted _pushed_cases and _ohca_addr_keys from file (survives restart)."""
    global _pushed_cases, _ohca_addr_keys
    try:
        with open(_pushed_cases_file, 'r') as f:
            state = json.load(f)
        _pushed_cases = set(state.get("cases", []))
        _ohca_addr_keys = set(state.get("ohca_keys", []))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass  # fresh start


def save_pushed_cases():
    """Persist _pushed_cases and _ohca_addr_keys so restart doesn't re-push everything."""
    try:
        with open(_pushed_cases_file, 'w') as f:
            json.dump({"cases": sorted(_pushed_cases),
                       "ohca_keys": sorted(_ohca_addr_keys)}, f)
    except Exception:
        pass  # non-fatal


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
            env=os.environ.copy()
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
                   env=os.environ.copy())
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
    result = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        addr = case.get("csPlace", "") or ""
        normalized = normalize_address(addr)
        outside = not (normalized.startswith("臺北市") or normalized.startswith("台北市"))
        result.append(dict(case,
                           source="service119",
                           source_url="https://service119.tfd.gov.tw/service119/citizenCase/search",
                           public_source_url=PUBLIC_CASE_URL,
                           outside_taipei=outside))
    return result


def push_to_telegram(city_code, address, coords, case_data=None, target_groups=None):
    """Push a single case to one or more Telegram groups (multi-channel).
    Pushes whatever the page shows — address, coords, case type, etc.
    Only called for addresses with 號 (building number).
    target_groups: list of chat_ids to push to (parallel distribution);
                   defaults to GROUP_ID_DISPATCH_LIST or [GROUP_ID].
    """
    if not case_data:
        print("[SCENE_SKIP] unlinked_coordinates", flush=True)
        return False
    resolved = _resolve_case_location(case_data, city_code)
    if not resolved or resolved["address"] != address:
        print("[SCENE_SKIP] outgoing_address_not_verified", flush=True)
        return False
    coords = resolved["coords"]
    token = TELEGRAM_BOTS[city_code]["token"]
    if target_groups is None:
        target_groups = GROUP_ID_DISPATCH_LIST or [GROUP_ID]
    
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
        f"📍 <b>地址:</b> <code>{address}</code>\n"
        f"🪪 <b>類別:</b> {cs_kind} / {cs_code}\n"
        f"🚑 <b>出勤:</b> {status}\n"
        f"👥 <b>人數:</b> {people}\n"
        f"🚒 <b>車輛:</b> {cars}\n"
        f"⏰ <b>時間:</b> {in_time}\n"
        f"📤 <b>推播時間:</b> {time.strftime('%Y/%m/%d %H:%M:%S')}\n"
        f"🌐 <b>座標:</b> "
        + (f"{coords[0]:.6f}, {coords[1]:.6f}\n" if coords else "來源未提供\n")
    )

    return _broadcast_telegram_message(
        msg, token, target_groups, log_label=f"PUSH {address}"
    )


def _broadcast_telegram_message(message, fallback_token, fallback_groups, log_label):
    """Send through every enabled bot_routes.json route.

    When no multi-bot routes are configured, retain the legacy one-bot,
    multi-group behavior. Each configured bot is retried independently by
    multi_dispatcher so one slow bot cannot block the other.
    """
    routes = multi_dispatcher.enabled_routes()
    if routes:
        results = multi_dispatcher.broadcast_all_detailed(message)
        for result in results:
            _update_bot_health(result["token"], result["ok"])
            state = "OK" if result["ok"] else "FAIL"
            print(
                f"  [{state}] {log_label} → route={result['name']} "
                f"chat={result['group_id']}",
                flush=True,
            )
        success = sum(result["ok"] for result in results)
        print(f"  [MULTIBOT] {success}/{len(results)} routes delivered", flush=True)
        return bool(results) and success == len(results)

    all_ok = True
    for chat_id in fallback_groups:
        ok = multi_dispatcher.send_single(
            fallback_token, chat_id, message, parse_mode="HTML"
        )
        _update_bot_health(fallback_token, ok)
        state = "OK" if ok else "FAIL"
        print(f"  [{state}] {log_label} → chat={chat_id}", flush=True)
        all_ok = all_ok and ok
    return all_ok


def _update_bot_health(token, ok, error_msg=""):
    """Track bot health status for GUI monitoring."""
    key = token[:12] if token else "unknown"
    _BOT_HEALTH[key] = {
        "ok": ok,
        "last_check": time.time(),
        "error": error_msg if not ok else "",
        "city": None,
    }
    for ck, cfg in TELEGRAM_BOTS.items():
        if cfg.get("token", "").startswith(token[:12]):
            _BOT_HEALTH[key]["city"] = ck
            break


def check_bot_health(city_code):
    """Check if a Telegram bot is alive via getMe API. Returns (ok, info_dict)."""
    token = TELEGRAM_BOTS[city_code]["token"]
    key = token[:12]
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=10
        )
        data = resp.json()
        if data.get("ok"):
            info = data.get("result", {})
            _update_bot_health(token, True)
            return True, info
        else:
            _update_bot_health(token, False, data.get("description", "API error"))
            return False, data
    except Exception as e:
        _update_bot_health(token, False, str(e))
        return False, {"error": str(e)}


def get_all_bot_health():
    """Return health status for all configured bots. Used by GUI."""
    result = {}
    for ck, cfg in TELEGRAM_BOTS.items():
        token = cfg.get("token", "")
        key = token[:12] if token else "unknown"
        # Cache valid for 60s
        cached = _BOT_HEALTH.get(key, {})
        if cached and (time.time() - cached.get("last_check", 0)) < 60:
            result[ck] = {
                "city": cfg.get("city", ck),
                "ok": cached.get("ok", False),
                "last_check": cached.get("last_check", 0),
                "error": cached.get("error", ""),
            }
        else:
            ok, info = check_bot_health(ck)
            result[ck] = {
                "city": cfg.get("city", ck),
                "ok": ok,
                "last_check": time.time(),
                "error": info.get("error", "") if not ok else "",
                "bot_info": info if ok else {},
            }
    return result


def get_daemon_status():
    """Return current daemon health status for GUI monitoring."""
    return {
        "running": _running,
        "lock_file_exists": os.path.exists("/tmp/broadcast_daemon.lock"),
        "login_pid": _login_process.pid if _login_process and _login_process.poll() is None else None,
        "pushed_cases": len(_pushed_cases),
        "ohca_addresses": len(_ohca_addr_keys),
        "recent_scenes": len(_recent_scenes),
        "ips_cache_time": _ips_cache_time,
        "dispatch_cache_time": _dispatch_cache_time,
        "bot_health": get_all_bot_health(),
    }


def _case_addr_key(case):
    """Generate a normalized address key for grouping OHCA cases.

    Uses TWD97 coordinates when available; falls back to address-string
    hash for cases without geocoding (e.g. IPS dispatch without forward-geocode).
    """
    address = case.get("csPlace", "")
    if has_doorplate(address):
        return "source:" + normalize_address(address)
    x = case.get("csX", 0)
    y = case.get("csY", 0)
    if x and y:
        return f"{_safe_round(x, 0)}:{_safe_round(y, 0)}"
    # Fallback: deterministic hash of address string (same addr → same key)
    addr = case.get("csPlace", "")
    return "source:" + normalize_address(addr)


# ── IPS case deduplication (same incident, different addresses) ──
# Threshold in TWD97 units (meters). Cases with same inTime and
# coordinates within this distance are the same incident.
IPS_MERGE_DIST_METERS = 80


def _merge_nearby_ips_cases(cases):
    """Merge only same-time IPS rows with the exact same reported address."""
    ips_cases = [c for c in cases if "ips_case_no" in c]
    non_ips = [c for c in cases if "ips_case_no" not in c]
    if len(ips_cases) < 2:
        return cases

    merged = []
    used = set()

    for i, base in enumerate(ips_cases):
        if i in used:
            continue
        base = dict(base)
        bx = _safe_round(base.get("csX"))
        by = _safe_round(base.get("csY"))
        bt = base.get("inTime", "")

        cluster = [i]
        for j in range(i + 1, len(ips_cases)):
            if j in used:
                continue
            other = ips_cases[j]
            if not bt or other.get("inTime", "") != bt:
                continue
            if not has_doorplate(base.get("csPlace")) or normalize_address(
                other.get("csPlace")
            ) != normalize_address(base.get("csPlace")):
                continue
            ox = _safe_round(other.get("csX"))
            oy = _safe_round(other.get("csY"))
            # TWD97 is in meters, so 4-decimal rounding ~0.1m precision.
            # Compare at meter-level granularity.
            dist = ((bx - ox) ** 2 + (by - oy) ** 2) ** 0.5
            if dist < IPS_MERGE_DIST_METERS:
                cluster.append(j)

        if len(cluster) == 1:
            merged.append(base)
            used.add(i)
        else:
            # Merge cluster into base case
            for idx in cluster:
                used.add(idx)
                if idx == i:
                    continue
                other = ips_cases[idx]
                base["dispatch_units"] = list(dict.fromkeys(
                    base.get("dispatch_units", []) + other.get("dispatch_units", [])
                ))
                base["numberOfAmbulance"] = len(base["dispatch_units"])
            merged.append(base)
            print(f"  [DEDUP] Merged {len(cluster)} IPS cases @ {bt} "
                  f"→ {base.get('csPlace', '?')} "
                  f"({base.get('numberOfAmbulance')} units total)", flush=True)

    return non_ips + merged


def _has_explicit_ohca_signal(case):
    text = " ".join(str(case.get(key) or "") for key in (
        "csKindName", "csCodeName", "caseType", "condition"
    )).upper()
    return any(pattern in text for pattern in (
        "OHCA", "心跳停止", "無呼吸", "心肺功能停止", "到院前心肺功能停止",
        "自殺", "自殺未遂",
    ))


def _resolve_case_location(case, city_code="01"):
    """One address gate for ordinary dispatches and suspected OHCA."""
    original, reason = source_scene_address(case)
    if reason:
        print(f"[SCENE_SKIP] {reason}", flush=True)
        return None
    cached = case.get("_verified_scene_location")
    if cached:
        if city_code == "01" and "臺北市" not in normalize_address(cached.get("address")):
            print("[SCENE_SKIP] not_explicitly_taipei", flush=True)
            return None
        return cached
    x, y = case.get("csX"), case.get("csY")
    coords = None
    if x and y and HAS_TWD:
        try:
            coords = twd_to_wgs84(float(x), float(y))
        except (TypeError, ValueError):
            pass
    geo = None
    if coords and HAS_GEOCODING:
        geo = reverse_geocode(*coords)
    resolved, reason = resolve_scene_address(case, coords, geo)
    if reason:
        print(f"[SCENE_SKIP] {reason}", flush=True)
        return None
    if city_code == "01" and "臺北市" not in normalize_address(resolved["address"]):
        print("[SCENE_SKIP] not_explicitly_taipei", flush=True)
        return None
    resolved["coords"] = coords
    case["_verified_scene_location"] = resolved
    return resolved


def push_ohca_alert(city_code, case_list, num_amb=0, target_groups=None,
                    evidence="multi_unit"):
    """Push a clearly-labelled OHCA suspicion from real dispatch evidence.
    Routes to GROUP_ID_OHCA_LIST if set, otherwise falls back to GROUP_ID.
    Supports multiple target groups for traffic separation / parallel distribution.
    """
    if not case_list:
        return
    locations = [_resolve_case_location(case, city_code) for case in case_list]
    if any(location is None for location in locations):
        return False
    if len({normalize_address(location["address"]) for location in locations}) != 1:
        print("[SCENE_SKIP] ohca_reported_addresses_differ", flush=True)
        return False
    location = locations[0]
    addr = location["address"]
    lat, lng = location["coords"] or (0, 0)

    token = TELEGRAM_BOTS[city_code]["token"]
    car_list = list(dict.fromkeys(
        c.get("dispCarList", "") for c in case_list if c.get("dispCarList", "")
    ))
    times = list(dict.fromkeys(
        c.get("inTime", "") for c in case_list if c.get("inTime", "")
    ))
    reported_units = max(
        (int(c.get("numberOfAmbulance", 0) or 0) for c in case_list),
        default=0,
    )
    amb_count = max(num_amb, reported_units, 1)
    has_ips = any("ips_case_no" in c for c in case_list)
    src = "IPS" if has_ips else "119"
    coord_str = f"{lat:.6f}, {lng:.6f}" if (lat and lng) else "未知 (地址哈希分組)"
    msg = (
        f"⚠️ <b>疑似 OHCA</b>\n"
        f"\n"
        f"🏙️ <b>縣市:</b> {TELEGRAM_BOTS[city_code]['city']}\n"
        f"📍 <b>地址:</b> <code>{addr}</code>\n"
        f"⏰ <b>時間:</b> {', '.join(t for t in times if t)}\n"
        f"📤 <b>推播時間:</b> {time.strftime('%Y/%m/%d %H:%M:%S')}\n"
        f"🚑 <b>派遣單位:</b> {'; '.join(c for c in car_list if c)}\n"
        f"🌐 <b>座標:</b> {coord_str}\n"
        + (f"📊 <b>資料來源:</b> IPS 119 即時派遣\n"
           if has_ips else f"📊 <b>資料來源:</b> TPE 119 即時資料\n")
    )
    # Route OHCA alerts to dedicated group(s) if configured (traffic separation)
    target_groups = target_groups or GROUP_ID_OHCA_LIST or [GROUP_ID]
    return _broadcast_telegram_message(
        msg,
        token,
        target_groups,
        log_label=f"OHCA {addr} ({amb_count} cars, {src})",
    )


def process_case(case, city_code):
    """Process a single case from the API: TWD coords → WGS84 → geocode → push."""
    # Deduplicate by case ID
    # Deduplicate by composite key (no caseId field in API response)
    case_id = f"{case.get('inTime','')}_{_safe_round(case.get('csX'))}_{_safe_round(case.get('csY'))}"
    if case_id and case_id in _pushed_cases:
        return
    location = _resolve_case_location(case, city_code)
    if not location:
        return False
    delivered = push_to_telegram(
        city_code, location["address"], location["coords"], case_data=case
    )
    if delivered and case_id:
        _pushed_cases.add(case_id)
    return delivered


def process_coords(coords_str, city_code="01"):
    """Inspect a coordinate without broadcasting an unlinked address."""
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

    print("  [SKIP] 座標未連結登入案件與公開案件，不進行推播", flush=True)


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


def fetch_dispatch_cases(city_code="01"):
    """Fetch real-time dispatch cases from the public caseList endpoint.
    
    Endpoint: POST service119.119.gov.taipei/service119/citizenCase/caseList
    No authentication required (token=anything works). Returns real-time
    emergency dispatch records with TWD97 coordinates and addresses.
    
    Only cases at the scene with a public precise-location signal and valid
    csX/csY are returned. fuzzyX/fuzzyY are never used for doorplate pushes.
    """
    global _dispatch_cache_time
    now = time.time()
    if _dispatch_cache_time and (now - _dispatch_cache_time) < DISPATCH_CACHE_TTL:
        return _dispatch_cache.get("cases", [])
    
    try:
        r = requests.post(
            DISPATCH_CASELIST_URL,
            data={"token": "anyone"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if r.status_code != 200:
            print(f"[-] Dispatch fetch failed: HTTP {r.status_code}", flush=True)
            return []
        
        data = r.json()
        rows = data.get("rows") or data.get("data") or []
        
        # --- Group scene rows by address to count dispatch cars per incident ---
        # dpKdid (e.g. "A", "B") identifies the dispatch car/unit.
        # Multiple cars at the same address in one polling cycle indicates
        # a potential OHCA (multi-ambulance response).
        def is_precise_scene(row):
            if row.get("caseStatus", "") not in ("已出勤", "到達現場"):
                return False
            try:
                x = float(row.get("csX"))
                y = float(row.get("csY"))
            except (TypeError, ValueError):
                return False
            if not (280000 <= x <= 330000 and 2750000 <= y <= 2790000):
                return False
            # csX/csY are the exact fields. fuzzyX/fuzzyY are deliberately
            # ignored regardless of dpKdid/fuzzyAble values.
            place = str(row.get("csPlace") or "")
            return not is_excluded_location(place)

        scene_rows = [row for row in rows if is_precise_scene(row)]
        
        cases = []
        for row in scene_rows:
            # Keep the official exact-place field untouched. csPlaceFuzzy is
            # only a district-level display value and is never an address.
            addr = str(row.get("csPlace") or "").strip()
            in_time = row.get("inTime", "")
            dpkdid = row.get("dpKdid", "A")
            cs_kind = row.get("csKindName", "")
            
            # Dedup key: stable per-case using available fields.
            # The API does NOT return an "sn" field — derive from
            # inTime + dpKdid + address to avoid collisions.
            dispatch_sn = f"{in_time}_{dpkdid}_{addr}"
            # Exact incident coordinates only. Never reverse-geocode fuzzyX/Y
            # into a nearby doorplate for the precise dispatch channel.
            cs_x = float(row["csX"])
            cs_y = float(row["csY"])
            address = addr
            source_ids = {
                key: row.get(key)
                for key in ("csNo", "caseNo", "sn")
                if row.get(key) not in (None, "")
            }
            
            case = {
                "inTime": in_time,
                "csPlace": address,
                "csX": cs_x,
                "csY": cs_y,
                "csKindName": cs_kind,
                "caseStatus": row.get("caseStatus", ""),
                "dispCarList": dpkdid,
                # dpKdid controls public location precision; it is not a
                # reliable vehicle count and must not trigger OHCA inference.
                "numberOfAmbulance": 0,
                "source": "caseList",
                "source_url": PUBLIC_CASE_URL,
                "public_page_url": PUBLIC_PAGE_URL,
                "official_scene_x": cs_x,
                "official_scene_y": cs_y,
                "dpKdid": dpkdid,
                "fuzzyAble": row.get("fuzzyAble"),
                "source_case_ids": source_ids,
                "address_origin": "original" if address else "public_coordinates",
                "dispatch_sn": dispatch_sn,
                "csCodeName": "",
            }
            cases.append(case)
        
        _dispatch_cache["cases"] = cases
        _dispatch_cache_time = now
        print(
            f"[+] Dispatch: {len(cases)} precise scene cases "
            f"(out of {len(rows)} rows)",
            flush=True,
        )
        return cases
    except Exception as e:
        print(f"[-] Dispatch fetch error: {e}", flush=True)
        return []


def ips_dispatch_to_case(ips_case, city_code):
    """Convert an IPS dispatch case dict to a service119-compatible case dict.

    Forward-geocodes the address → WGS84 → TWD97 for addr_key compatibility.
    Preserves the upstream status; downstream policy decides whether it is live.
    """
    case_id = f"ips_{ips_case.get('case_no', '')}"
    address = ips_case.get("address", "")
    if not address or is_excluded_location(address):
        return None
    if city_code == "01" and "臺北市" not in normalize_address(address):
        print("  [IPS_SKIP] not_explicitly_taipei", flush=True)
        return None

    # Skip fuzzy addresses (no 號 = building number)
    # BUT: 2+ unit dispatch (OHCA candidate) bypasses this — parks,
    # intersections, and other non-doorplate locations with multiple
    # ambulances are still valid OHCA signals per policy.
    num_units = ips_case.get("num_units", 0)
    if "號" not in address and num_units < 2:
        return None
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

    # Convert WGS84 → TWD97 for addr_key compatibility with service119 dispatch cases
    if lat is not None and HAS_TWD:
        cs_x, cs_y = wgs_to_twd97(lat, lng)
    elif lat is None:
        cs_x, cs_y = 0.0, 0.0  # will trigger addr_key hash fallback
    elif lat and lng:
        cs_x, cs_y = lng * 100000, lat * 100000  # HAS_TWD not available, use raw
    else:
        cs_x, cs_y = 0.0, 0.0  # fallback

    status = ips_case.get("status", "")

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

    return {
        "inTime": ips_case.get("last_modified", ""),
        "csPlace": address,
        "csX": cs_x,
        "csY": cs_y,
        "caseStatus": status,
        "dispCarList": disp_str,
        "numberOfAmbulance": len(set(units)),
        "dispatch_units": list(dict.fromkeys(units)),
        "ips_case_no": ips_case.get("case_no", ""),
        "source": "ips",
    }


def _status_server(port=58888):
    """Lightweight HTTP server exposing daemon status JSON for the GUI."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/status":
                data = get_daemon_status()
                body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/health":
                data = {"ok": True, "bots": get_all_bot_health()}
                body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), _Handler)
    server.timeout = 1
    while _running:
        server.handle_request()


def daemon_loop(interval=60, city_code="01", status_port=58888,
                skip_existing_on_start=True):
    """Main daemon: keep login alive, poll API for new cases, push."""
    global _running
    print(f"\n🛡️ Broadcast Daemon starting "
          f"(interval={interval}s, city={city_code})", flush=True)
    route_count = len(multi_dispatcher.enabled_routes())
    print(f"[+] Telegram multi-bot routes enabled: {route_count}", flush=True)

    # Start login daemon for auto token renewal
    start_login_daemon()
    monitor_t = threading.Thread(target=monitor_login_daemon, daemon=True)
    monitor_t.start()

    # Start status HTTP server for GUI monitoring
    status_t = threading.Thread(target=_status_server, kwargs={"port": status_port}, daemon=True)
    status_t.start()

    # Restore persisted dedup state (survives daemon restart)
    load_pushed_cases()
    if _pushed_cases:
        print(f"[+] Restored {len(_pushed_cases)} pushed case IDs + "
              f"{len(_ohca_addr_keys)} OHCA addresses from cache", flush=True)

    print(f"[*] Polling citizenCase/search every {interval}s...", flush=True)

    baseline_pending = skip_existing_on_start
    while _running:
        cycle_started = time.monotonic()
        try:
            token, jsession = get_valid_token()
            if token:
                print(f"[+] Token valid: {token[:25]}...", flush=True)
            else:
                print(f"[!] Token unavailable — login.py will auto-renew", flush=True)

            if city_code == "01":
                # Fetch all three live sources concurrently. A slow IPS login
                # must not delay the public caseList or citizenCase/search.
                with ThreadPoolExecutor(max_workers=3) as pool:
                    tpe_future = pool.submit(fetch_tpe119_cases, city_code)
                    ips_future = pool.submit(fetch_ips_dispatch_with_cache)
                    dispatch_future = pool.submit(fetch_dispatch_cases, city_code)
                    cases = tpe_future.result() or []
                    dispatch_cases = dispatch_future.result() or []
                    ips_cases = ips_future.result() or []
                verified_dispatch_cases = []
                for public_case in dispatch_cases:
                    verified = verify_public_against_login(public_case, cases)
                    if verified:
                        verified_dispatch_cases.append(verified)
                print(
                    f"[COORD_COMPARE] public={len(dispatch_cases)} "
                    f"login_matched={len(verified_dispatch_cases)} "
                    f"rejected={len(dispatch_cases) - len(verified_dispatch_cases)}",
                    flush=True,
                )
                verified_keys = {
                    (
                        str(c.get("inTime") or ""),
                        _safe_round(c.get("csX")),
                        _safe_round(c.get("csY")),
                    )
                    for c in verified_dispatch_cases
                }
                # Keep citizenCase/search as the canonical source. Replace a
                # matched login row with its public-coordinate-attested copy.
                cases = [
                    c for c in cases
                    if (
                        str(c.get("inTime") or ""),
                        _safe_round(c.get("csX")),
                        _safe_round(c.get("csY")),
                    ) not in verified_keys
                ]
                cases.extend(verified_dispatch_cases)
                for ips_case in ips_cases:
                    ips_dict = ips_dispatch_to_case(ips_case, city_code)
                    if ips_dict:
                        cases.append(ips_dict)
            else:
                cases = fetch_tpe119_cases(city_code)
            # Merge nearby IPS cases for the same incident
            # (same inTime + nearby coords = one incident, not separate)
            cases = _merge_nearby_ips_cases(cases)
            # Push while units are dispatched or at the incident scene. Later
            # statuses (left scene, hospital, returned) are always excluded.
            scene_cases = [
                c for c in cases
                if (c.get("caseStatus", "") or "") in ACTIVE_STATUSES
            ]
            if baseline_pending:
                baseline_count = 0
                for case in scene_cases:
                    if case.get("source") == "ips":
                        continue  # IPS cases must reach OHCA dispatch, not pre-deduped
                    case_id = (
                        f"{case.get('inTime','')}_"
                        f"{_safe_round(case.get('csX'))}_"
                        f"{_safe_round(case.get('csY'))}"
                    )
                    if case_id not in _pushed_cases:
                        _pushed_cases.add(case_id)
                        baseline_count += 1
                save_pushed_cases()
                baseline_pending = False
                print(
                    f"[BASELINE] Suppressed {baseline_count} existing scene cases; "
                    "only cases first seen after startup will be pushed",
                    flush=True,
                )
                elapsed = time.monotonic() - cycle_started
                time.sleep(max(0, interval - elapsed))
                continue
            if scene_cases:
                # Sort oldest-first for clean chronological broadcast order
                scene_cases.sort(key=lambda c: c.get("inTime", ""))
                # Group by address for OHCA detection.
                # NOTE: do NOT pre-skip cases whose case_id is in _pushed_cases
                # here — that set only blocks regular dispatch. OHCA-eligible
                # cases (multi-unit or keyword-signalled) must always enter the
                # grouping so the _ohca_addr_keys dedup can correctly evaluate
                # them. Moving the _pushed_cases check into the regular-dispatch
                # section below prevents stale case_ids (from a previous run's
                # baseline) from blocking new OHCA alerts.
                by_addr = {}
                for case in scene_cases:
                    addr_key = _case_addr_key(case)
                    by_addr.setdefault(addr_key, []).append(case)
                for addr_key, case_list in by_addr.items():
                    explicit_ohca = [c for c in case_list if _has_explicit_ohca_signal(c)]
                    distinct_units = {
                        unit
                        for c in case_list
                        for unit in c.get("dispatch_units", [])
                        if unit
                    }
                    num_amb = max(
                        len(distinct_units),
                        max(
                            (int(c.get("numberOfAmbulance", 0) or 0) for c in case_list),
                            default=0,
                        ),
                    )
                    should_alert = bool(explicit_ohca) or num_amb >= 2

                    if should_alert and addr_key not in _ohca_addr_keys:
                        evidence = "explicit" if explicit_ohca else "multi_unit"
                        delivered = push_ohca_alert(
                            city_code,
                            explicit_ohca or case_list,
                            num_amb=num_amb,
                            target_groups=GROUP_ID_OHCA_LIST,
                            evidence=evidence,
                        )
                        if delivered:
                            for c in case_list:
                                cid = f"{c.get('inTime','')}_{_safe_round(c.get('csX'))}_{_safe_round(c.get('csY'))}"
                                _pushed_cases.add(cid)
                            _ohca_addr_keys.add(addr_key)
                            continue  # only skip regular dispatch if OHCA was delivered
                    # OHCA push failed or not applicable: fall through to regular dispatch.
                    # No explicit OHCA signal and no trustworthy multi-unit
                    # count: send each real incident as a regular dispatch.
                    for case in case_list:
                        cid = f"{case.get('inTime','')}_{_safe_round(case.get('csX'))}_{_safe_round(case.get('csY'))}"
                        if cid and cid in _pushed_cases:
                            continue  # already dispatched as a regular case
                        if process_case(case, city_code):
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

        # Persist dedup state (survives daemon restart / SIGKILL)
        save_pushed_cases()
        elapsed = time.monotonic() - cycle_started
        print(f"[CYCLE] completed in {elapsed:.1f}s", flush=True)
        time.sleep(max(0, interval - elapsed))

    # Cleanup
    if _login_process:
        _login_process.terminate()
        print("[*] login.py daemon stopped", flush=True)
    print("[*] Broadcast Daemon stopped", flush=True)


def _sigint_handler(signum, frame):
    global _running
    _running = False


def bind_telegram_group(bot_token):
    """Use Telegram getUpdates API to discover the group chat ID where the bot was added.
    
    The bot must first be added to the target group, then send a message (or the bot
    will be promoted). This auto-discovers the group ID without manual configuration.
    
    Returns the group chat ID (string) or None if not found.
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        r = requests.get(url, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return None
        for update in data.get("result", []):
            # Check my_chat_member events (bot added to group)
            chat = update.get("my_chat_member", {}).get("chat", {})
            if chat.get("type") in ("group", "supergroup"):
                return str(chat.get("id"))
            # Check message events (someone messaged the bot in a group)
            chat = update.get("message", {}).get("chat", {})
            if chat.get("type") in ("group", "supergroup"):
                return str(chat.get("id"))
        return None
    except Exception as e:
        print(f"[!] Auto-bind group ID failed: {e}", flush=True)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOCP Broadcast Auto-Daemon")
    parser.add_argument("--coords", help="One-shot: coordinates to push (lat,lng)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Polling interval seconds (default: 60)")
    parser.add_argument("--city", default="01", choices=list(TELEGRAM_BOTS.keys()),
                        help="City code: 01=Taipei, 05=Taoyuan, 11=Kaohsiung")
    parser.add_argument("--daemon", action="store_true",
                        help="Run as background daemon")
    # One-click: bot token + auto-bind group ID
    parser.add_argument("--all-cities", action="store_true",
                        help="Run daemon loops for ALL configured cities (each on its own status port)")
    parser.add_argument("--tg-bot-token",
                        help="One-click: Telegram bot token (auto-binds group via getUpdates)")
    parser.add_argument("--group-id",
                        help="Explicit group ID (auto-discovered from getUpdates if omitted)")
    parser.add_argument("--ohca-group-id",
                        help="OHCA alerts → this group (comma-separated for multiple targets)")
    parser.add_argument("--dispatch-group-id",
                        help="Regular dispatches → this group (comma-separated for multiple targets)")
    parser.add_argument("--status-port", type=int, default=58888,
                        help="HTTP status server port for GUI monitoring (default: 58888)")
    parser.add_argument(
        "--skip-existing-on-start",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Baseline existing scene cases on startup and push only newly seen cases",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _sigint_handler)
    signal.signal(signal.SIGINT, _sigint_handler)

    # Kernel-backed lock: prevent multiple instances without stale-lock loops.
    # The file may remain after SIGKILL; flock itself is released by the OS.
    import atexit
    import fcntl
    _lock_file = "/tmp/broadcast_daemon.lock"
    _lock_fd = os.open(_lock_file, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(_lock_fd, 0)
        os.write(_lock_fd, str(os.getpid()).encode())
    except BlockingIOError:
        os.close(_lock_fd)
        print("[!] Another daemon instance is already running — kill it first or remove", flush=True)
        print(f"    lock file: {_lock_file}", flush=True)
        sys.exit(1)

    def _cleanup_lock():
        try:
            fcntl.flock(_lock_fd, fcntl.LOCK_UN)
            os.close(_lock_fd)
        except OSError:
            pass
    atexit.register(_cleanup_lock)
    if args.tg_bot_token:
        TELEGRAM_BOTS[args.city]["token"] = args.tg_bot_token
        if args.group_id:
            GROUP_ID = args.group_id
        else:
            bound = bind_telegram_group(args.tg_bot_token)
            if bound:
                GROUP_ID = bound
                print(f"[+] Auto-bound group ID: {bound}", flush=True)
            else:
                print("[!] Could not auto-bind — add bot to target group first", flush=True)

    if args.ohca_group_id:
        GROUP_ID_OHCA = args.ohca_group_id
        GROUP_ID_OHCA_LIST = [g.strip() for g in args.ohca_group_id.split(",") if g.strip()]

    if args.dispatch_group_id:
        GROUP_ID_DISPATCH = args.dispatch_group_id
        GROUP_ID_DISPATCH_LIST = [g.strip() for g in args.dispatch_group_id.split(",") if g.strip()]

    if args.coords:
        process_coords(args.coords, args.city)
    elif args.all_cities:
        # Multi-city mode: run a daemon loop per configured city, each on its own status port:
        #   city 01 -> port 58888, city 05 -> 58889, city 11 -> 58890, etc.
        # Each city has isolated dedup state (ips_{case_no} / ohca_addr_keys are city-scoped).
        base_port = args.status_port
        threads = []
        for i, city_code in enumerate(sorted(TELEGRAM_BOTS.keys())):
            port = base_port + i
            t = threading.Thread(
                target=daemon_loop,
                kwargs={
                    "interval": args.interval,
                    "city_code": city_code,
                    "status_port": port,
                    "skip_existing_on_start": args.skip_existing_on_start,
                },
                daemon=True,
                name=f"daemon-{city_code}",
            )
            t.start()
            threads.append(t)
            print(f"[+] Spawned daemon thread for city {city_code} on status port {port}", flush=True)
        print(f"[*] All {len(threads)} city daemons running. Waiting...", flush=True)
        try:
            while _running:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            _running = False
        print("[*] All city daemons stopped.", flush=True)
    else:
        daemon_loop(
            interval=args.interval,
            city_code=args.city,
            status_port=args.status_port,
            skip_existing_on_start=args.skip_existing_on_start,
        )
