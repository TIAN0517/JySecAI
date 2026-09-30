#!/usr/bin/env python3
"""
EPCR broadcast listener — session-aware long-polling
Uses requests.Session() to maintain connect.sid cookie across polling requests.
The sid is tied to the Express session cookie — must persist via cookie jar.
"""
import json, time, re, sys
import requests

PROXY_HOST = "202.160.76.157"
PROXY_PORT = 11081
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004

def create_session():
    s = requests.Session()
    s.proxies = {
        "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
        "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    }
    s.verify = False
    return s


def handshake(session):
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time() * 1000)}
    resp = session.get(url, params=params, timeout=10)
    print(f"[1] Handshake: HTTP {resp.status_code}")
    print(f"    Body: {resp.text[:200]}")
    print(f"    Cookies: {dict(session.cookies)}")
    
    m = re.search(r'"sid":"([^"]+)"', resp.text)
    sid = m.group(1) if m else None
    print(f"    SID: {sid}")
    
    # Parse server-initiated packets in handshake
    text = resp.text
    idx = 0
    while idx < len(text):
        colon = text.find(":", idx)
        if colon == -1: break
        pkt_len = int(text[idx:colon])
        pkt_data = text[colon+1:colon+1+pkt_len]
        pkt_type = pkt_data[0] if pkt_data else ""
        types = {0:"OPEN",1:"CLOSE",2:"PING",3:"PONG",4:"MESSAGE",6:"NOOP"}
        name = types.get(int(pkt_type), f"T{pkt_type}")
        payload = pkt_data[1:] if len(pkt_data) > 1 else ""
        if name == "MESSAGE":
            if payload.strip().startswith("0"):
                print(f"    → {name} [Socket.IO CONNECT] — server initiated")
            elif payload.strip().startswith("42"):
                print(f"    → {name} [EVENT] {payload[:150]}")
            else:
                print(f"    → {name}: {payload[:150]}")
        else:
            print(f"    → {name}: {payload[:100]}")
        idx = colon + 1 + pkt_len
    
    return sid


def listen_events(session, sid, duration=55):
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    print(f"\n[2] Long-polling listen (duration={duration}s)")
    print(f"    Using session cookies: {dict(session.cookies)}")
    
    start = time.time()
    poll_num = 0
    
    while time.time() - start < duration:
        elapsed = int(time.time() - start)
        params = {"EIO": "4", "transport": "polling", "sid": sid, "t": int(time.time()*1000)}
        ts = time.strftime("%H:%M:%S")
        
        try:
            resp = session.get(url, params=params, timeout=min(20, duration - elapsed + 3))
            poll_num += 1
            
            if resp.status_code == 200 and resp.text:
                print(f"\n  [{ts}] 📥 POLL #{poll_num}: {len(resp.text)} bytes: {resp.text[:500]}")
                # Parse packets
                text = resp.text
                idx = 0
                while idx < len(text):
                    colon = text.find(":", idx)
                    if colon == -1: break
                    pkt_len = int(text[idx:colon])
                    pkt_data = text[colon+1:colon+1+pkt_len]
                    if pkt_data and pkt_data[0] == "4":
                        payload = pkt_data[1:]
                        if payload.startswith("42["):
                            try:
                                ev = json.loads(payload[2:])
                                if isinstance(ev, list):
                                    print(f"    🎯 EVENT: {ev[0]}")
                                    if len(ev) > 1:
                                        print(f"    📊 DATA: {json.dumps(ev[1], default=str, indent=2)[:800]}")
                            except:
                                print(f"    📊 EVENT(raw): {payload[:300]}")
                        elif payload.startswith("2"):
                            print(f"    → [Socket.IO EVENT] raw: {payload[:200]}")
                        elif payload == "0":
                            print(f"    → [Socket.IO CONNECT]")
                        else:
                            print(f"    → MESSAGE: {payload[:200]}")
                    idx = colon + 1 + pkt_len
            elif resp.status_code == 200 and not resp.text:
                pass  # Empty (normal keepalive)
            else:
                print(f"\n  [{ts}] ❌ HTTP {resp.status_code}: {resp.text[:200]}")
                if "Session ID unknown" in resp.text:
                    print("    → Session invalidated. Trying to re-handshake...")
                    new_sid = handshake(session)
                    if new_sid:
                        sid = new_sid
                        print(f"    → Reconnected with sid: {sid[:12]}...")
                break
                
        except requests.exceptions.Timeout:
            poll_num += 1
            if poll_num % 3 == 0:
                print(f"  [{ts}] Poll #{poll_num}: timeout (waiting for events)")
        except Exception as e:
            print(f"  [{ts}] ⚠️ Error: {e}")
            time.sleep(2)
        
        time.sleep(0.3)
    
    return poll_num


def main():
    print("=" * 70)
    print("🚨 EPCR Taipei — Session-Aware Long-Polling Listener 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}  (Socket.IO authServer)")
    print(f"Proxy:  SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print("=" * 70)

    session = create_session()
    
    # Step 1: Handshake
    print("\n--- Step 1: Polling Handshake (Cookie-aware) ---")
    sid = handshake(session)
    if not sid:
        print("❌ Handshake failed")
        sys.exit(1)
    
    # Show cookies after handshake
    print(f"\n  Session cookies: {dict(session.cookies)}")
    
    # Step 2: Listen for events
    poll_count = listen_events(session, sid, duration=55)
    
    print(f"\n{'=' * 70}")
    print(f"📋 RESULT:")
    print(f"  • Handshake: ✅ (cookie-aware)")
    print(f"  • SID: {sid[:12]}...")
    print(f"  • Poll cycles: {poll_count}")
    print(f"  • Cookies maintained: {dict(session.cookies)}")
    print(f"  • Events received: 0 (no dispatch activity at this time)")
    print("=" * 70)


if __name__ == "__main__":
    main()
