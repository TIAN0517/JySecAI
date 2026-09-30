#!/usr/bin/env python3
"""
Taipei/TOCP Dual Broadcast
  1. Forges TOCP JWT → POST /CaseRecords (city dispatch centers)
  2. For each city → sends Telegram message via city-specific bot

Usage:  python3 tpe_epcr_broadcast.py [city_code]
  city_code: 01 (Taipei), 05 (Taoyuan), 11 (Kaohsiung), ALL (default)
"""
import os, json, time, ssl, urllib.request, urllib.parse, urllib.error, warnings, base64, sys
warnings.filterwarnings('ignore')

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
    "OHCA": True,
    "priority": "B",
}

# ── Helpers ────────────────────────────────────────────────────
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

def send_telegram(city_code, case_data):
    """Send case notification via city-specific Telegram bot."""
    cfg = TELEGRAM_BOTS[city_code]
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        f"🚨 <b>緊急案件推播 / Case Dispatch Alert</b>\n\n"
        f"🏙️ <b>縣市:</b> {cfg['city']} ({cfg['en']})\n"
        f"📋 <b>Case Type:</b> 傷病 (EMS) / Type 21\n"
        f"📍 <b>Address:</b> {cfg['address']}\n"
        f"🩺 <b>OHCA:</b> {'Yes' if case_data['OHCA'] else 'No'}\n"
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
        return resp.status, json.loads(resp.read().decode())
    except Exception as e:
        return 0, str(e)

# ── Main ───────────────────────────────────────────────────────
def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    codes = list(TELEGRAM_BOTS.keys()) if target.upper() == "ALL" else [target]

    print(f"[*] TOCP JWT Secret: {TOCP_JWT_SECRET[:3]}***")
    print(f"[*] Telegram Group: {GROUP_ID}")
    print(f"[*] Target: {codes}")
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
        status, body = send_telegram(code, CASE_DATA)
        if status == 200:
            tg_id = body.get('result', {}).get('message_id', '?')
            print(f"  [TG]   Bot {cfg['token'][:12]}... → group msg_id={tg_id}")
        else:
            print(f"  [TG]   Failed: {body[:100]}")
        print()

if __name__ == "__main__":
    main()
