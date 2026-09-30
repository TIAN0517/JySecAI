#!/usr/bin/env python3
"""
Taipei/TOCP Dual Broadcast
  1. Forges TOCP JWT → POST /CaseRecords (city dispatch centers)
  2. For each city → sends Telegram message via city-specific bot

Usage:  python3 tocp_tpe_broadcast.py [city_code] [--coords LAT,LNG] [--ohca yes|no|auto]
  city_code: 01 (Taipei), 05 (Taoyuan), 11 (Kaohsiung), ALL (default)
  --coords   : Reverse-geocode these coords into address with 號 before push
  --ohca     : Override OHCA flag (default: auto — derived from case data)

OHCA rule:
  - yes: force OHCA=True (cardiac arrest, double-ambulance dispatch)
  - no:   force OHCA=False
  - auto: True only if case_type contains 心/急/病/創/車 (EMS emergency patterns)
    OR if 2+ ambulances dispatched (real case data only)

Auto-push integration:
  1. python3 login.py --daemon     # auto-renews TPE 119 JWT every 2.5h
  2. python3 broadcast_daemon.py  # monitors coords → geocode → push
  3. Only pushes addresses with 號 (building number) — fuzzy skipped
"""
import os, json, time, ssl, urllib.request, urllib.parse, urllib.error, warnings, base64, sys
warnings.filterwarnings('ignore')

# Reverse-geocoding support
try:
    from geocoding import reverse_geocode
    HAS_GEOCODING = True
except (ImportError, NameError):
    reverse_geocode = None
    HAS_GEOCODING = False

try:
    import jwt as pyjwt
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

# ── Configuration ──────────────────────────────────────────────
TOCP_JWT_SECRET = "ru/3xu4dkru4888"
TOCP_BASE = "https://epcr.tpf.gov.tw:8188"
TOCP_ENDPOINT = "/CaseRecords"

GROUP_ID = "-1004487319117"

TELEGRAM_BOTS = {
    "01": {  # Taipei
        "city":    "台北市",
        "en":      "Taipei",
        "token":   "8944573992:AAEdy0vHiNoOQUCiWEbBpvrARsFvB5fCZXg",
        "address": "臺北市大安區羅斯福路四段1號",
        "lat":     25.0166,
        "lng":     121.5407,
    },
    "05": {  # Taoyuan
        "city":    "桃園市",
        "en":      "Taoyuan",
        "token":   "8594661859:AAG_EEQbiPqFQcsQDdPHqpqJeN_FFztRBZo",
        "address": "桃園市桃園區中山南路158號",
        "lat":     24.9942,
        "lng":     121.2968,
    },
    "11": {  # Kaohsiung
        "city":    "高雄市",
        "en":      "Kaohsiung",
        "token":   "8962928663:AAHoQYeEpVJh7TtRq2n3F8nU7PuzzhK9rM0",
        "address": "高雄市前金區中正五路155號",
        "lat":     22.9972,
        "lng":     120.2136,
    },
}

CASE_DATA = {
    "caseType": "21",        # 傷病 (EMS)
    "OHCA": "auto",          # auto: derived from case_type or ambulance count
    "priority": "B",
}

# OHCA detection patterns — case types that indicate cardiac arrest
OHCA_PATTERNS = ["心", "止住", "心跳", "心跳停止", "EFW", "EFW1", "EFW2"]  # 心跳停止等

# ── Helpers ────────────────────────────────────────────────────
def resolve_ohca(ohca_mode, case_type="", ambulance_count=1):
    """Resolve OHCA based on mode: yes/no/auto.
    auto: True only if case_type matches OHCA patterns OR ambulance_count >= 2.
    """
    if ohca_mode == "yes":
        return True
    if ohca_mode == "no":
        return False
    # auto mode
    ct = str(case_type).upper()
    if any(p.upper() in ct for p in OHCA_PATTERNS):
        return True
    return ambulance_count >= 2


def forge_jwt():
    """Forge TOCP JWT with current timestamp."""
    now = int(time.time())
    payload = {"sub": 1, "iat": now, "exp": now + 10800}
    if HAS_PYJWT:
        return pyjwt.encode(payload, TOCP_JWT_SECRET, algorithm="HS256")
    # Manual HS256 fallback
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=')
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(',',':')).encode()
    ).rstrip(b'=')
    import hmac, hashlib
    sig = hmac.new(TOCP_JWT_SECRET.encode(), f"{header}.{body}".encode(),
                   hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(sig).rstrip(b'=')
    return f"{header.decode()}.{body.decode()}.{sig.decode()}"

def push_tocp(city_code, token):
    """POST case record to TOCP /soap."""
    cfg = TELEGRAM_BOTS[city_code]
    case = {
        "countyCode": city_code,
        "caseType": CASE_DATA["caseType"],
        "OHCA": CASE_DATA["OHCA"],
        "priority": CASE_DATA["priority"],
        "address": cfg["address"],
        "latitude": cfg["lat"],
        "longitude": cfg["lng"],
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"{TOCP_BASE}{TOCP_ENDPOINT}",
        data=json.dumps(case).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=3)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def send_telegram(city_code, case_data, coords=None, ohca_mode="auto"):
    """Send case notification via city-specific Telegram bot.

    If coords (lat, lng) provided and geocoding module is available,
    reverse-geocode to get address with 號 (building number).
    """
    cfg = TELEGRAM_BOTS[city_code]
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    # --- Reverse-geocode coords if provided ---
    has_building_no = False
    if coords and HAS_GEOCODING and reverse_geocode is not None:
        geo = reverse_geocode(coords[0], coords[1])
        if geo['success']:
            cfg = dict(cfg)  # copy, don't mutate global
            cfg['address'] = geo['formatted_address']
            building_no = geo.get('street_number') or 'N/A'
            cfg['coords'] = coords
            has_building_no = building_no not in ('N/A', None)
            print(f"  [GEOCODE] {coords} → {geo['formatted_address']} ({building_no})")

    # Resolve OHCA based on mode
    ohca_val = resolve_ohca(ohca_mode, case_data.get("caseType", ""),
                            case_data.get("ambulanceCount", 1))
    msg = (
        f"🚨 <b>緊急案件推播 / Case Dispatch Alert</b>\n\n"
        f"🏙️ <b>縣市:</b> {cfg['city']} ({cfg['en']})\n"
        f"📋 <b>Case Type:</b> 傷病 (EMS) / Type {case_data.get('caseType', '21')}\n"
        f"📍 <b>Address:</b> {cfg['address']}\n"
        f"⚡ <b>Priority:</b> {case_data['priority']}\n"
        f"🌐 <b>Coords:</b> {cfg['lat']}, {cfg['lng']}\n"
        f"🕐 <b>Time:</b> {ts}\n\n"
        f"🔧 <b>Channel:</b> TOCP JWT Forge + TPE 119 broadcast"
    )
    payload = urllib.parse.urlencode({
        "chat_id": GROUP_ID,
        "text": msg,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{cfg['token']}/sendMessage",
            data=payload, method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read().decode()), has_building_no
    except Exception as e:
        return 0, str(e), has_building_no

# ── Main ───────────────────────────────────────────────────────
def main():
    codes = list(TELEGRAM_BOTS.keys())  # default: ALL
    coords = None  # (lat, lng) for reverse-geocoding

    # Parse args: support [city_code] and [--coords LAT,LNG] in any order
    filtered = []
    ohca_mode = "auto"
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--coords" and i + 1 < len(args):
            lat_s, lng_s = args[i + 1].split(",")
            coords = (float(lat_s.strip()), float(lng_s.strip()))
            i += 2
        elif args[i].startswith("--coords="):
            _, val = args[i].split("=", 1)
            lat_s, lng_s = val.split(",")
            coords = (float(lat_s.strip()), float(lng_s.strip()))
            i += 1
        elif args[i] == "--ohca" and i + 1 < len(args):
            ohca_mode = args[i + 1].lower()
            i += 2
        elif args[i].startswith("--ohca="):
            ohca_mode = args[i].split("=", 1)[1].lower()
            i += 1
        else:
            filtered.append(args[i])
            i += 1

    if filtered and filtered[0].upper() in ("ALL", "01", "05", "11"):
        target = filtered[0]
        codes = list(TELEGRAM_BOTS.keys()) if target.upper() == "ALL" else [target]

    print(f"[*] TOCP JWT Secret: {TOCP_JWT_SECRET[:3]}***")
    print(f"[*] Telegram Group: {GROUP_ID}")
    print(f"[*] Target: {codes}")
    print(f"[*] OHCA mode: {ohca_mode}")
    print(f"[*] Geo-coords: {coords} (reverse-geocoding enabled)" if coords else "[*] Geo-coords: none (using default city coords)")
    print()

    # Forge single JWT for all cities
    token = forge_jwt()
    print(f"[+] Forged JWT: {token[:40]}...{token[-15:]}")
    print()

    for code in codes:
        cfg = TELEGRAM_BOTS[code]
        print(f"─" * 50)
        print(f"  City: {cfg['city']} ({cfg['en']}) | countyCode={code}")
        print(f"─" * 50)

        # 1. TOCP push
        status, body = push_tocp(code, token)
        print(f"  [TOCP] POST /soap → HTTP {status}")
        if status == 200:
            try:
                r = json.loads(body)
                print(f"  [TOCP] Response: {r}")
            except:
                print(f"  [TOCP] Body: {body[:100]}")
        else:
            print(f"  [TOCP] Error: {body[:100]}")

        # 2. Telegram notification
        status, body, has_building_no = send_telegram(code, CASE_DATA, coords=coords, ohca_mode=ohca_mode)
        # Skip push if coords given but no building number found
        if coords and not has_building_no:
            print(f"  [TG]   SKIP — address lacks 號 (fuzzy address, not scene-level)")
            continue
        if status == 200:
            tg_id = body.get('result', {}).get('message_id', '?')
            print(f"  [TG]   Bot {cfg['token'][:12]}... → group msg_id={tg_id}")
        else:
            print(f"  [TG]   Failed: {body[:100]}")
        print()

if __name__ == "__main__":
    main()
