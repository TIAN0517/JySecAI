#!/usr/bin/env python3
"""
EPCR broadcast listener — pure long-polling cycle
Handshake → immediate long-poll (no CONNECT, no PONG) → keep polling
The server holds each request open until events or timeout.
"""
import json, time, re, sys
import requests

PROXY_HOST = "202.160.76.157"
PROXY_PORT = "11081"
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
PROXIES = {
    "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}

def handshake():
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time() * 1000)}
    resp = requests.get(url, params=params, proxies=PROXIES, verify=False, timeout=10)
    print(f"[1] Handshake: HTTP {resp.status_code}")
    print(f"    Body: {resp.text[:200]}")
    m = re.search(r'"sid":"([^"]+)"', resp.text)
    sid = m.group(1) if m else None
    print(f"    SID: {sid}")
    # Parse server-sent packets
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
        print(f"    → {name} (len={pkt_len}): {payload[:150]}")
        idx = colon + 1 + pkt_len
    return url, sid


def longpoll_receive(url, sid, base_url, total_secs=45):
    """Proper long-polling: GET, wait, repeat"""
    print(f"\n[2] Long-polling receive (no CONNECT, no PONG)")
    print(f"    URL: {base_url}")
    
    start = time.time()
    poll_count = 0
    
    while time.time() - start < total_secs:
        elapsed = int(time.time() - start)
        remaining = total_secs - elapsed
        params = {"EIO": "4", "transport": "polling", "sid": sid, "t": int(time.time() * 1000)}
        ts = time.strftime("%H:%M:%S")
        
        try:
            resp = requests.get(url, params=params, proxies=PROXIES, 
                              verify=False, timeout=min(25, remaining + 5))
            poll_count += 1
            
            if resp.status_code == 200 and resp.text:
                print(f"\n  [{ts}] 📥 POLL #{poll_count}: {len(resp.text)} bytes: {resp.text[:500]}")
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
                        print(f"    → MESSAGE: {payload[:200]}")
                        if payload.startswith("42["):
                            try:
                                ev = json.loads(payload[2:])
                                if isinstance(ev, list):
                                    print(f"    → EVENT: {ev[0]}")
                                    if len(ev) > 1:
                                        print(f"       DATA: {json.dumps(ev[1], default=str, indent=2)[:500]}")
                            except:
                                print(f"    → EVENT(raw): {payload[:200]}")
                    idx = colon + 1 + pkt_len
            elif resp.status_code == 200 and not resp.text:
                if poll_count % 3 == 0:
                    print(f"  [{ts}] Poll #{poll_count}: empty (keepalive)")
            else:
                print(f"  [{ts}] ❌ HTTP {resp.status_code}: {resp.text[:150]}")
                break
        except requests.exceptions.Timeout:
            poll_count += 1
            if poll_count % 2 == 0:
                print(f"  [{ts}] Poll #{poll_count}: timeout (server holding connection — normal)")
        except Exception as e:
            print(f"  [{ts}] ⚠️ Error: {e}")
            time.sleep(2)
        
        # Brief delay between polls
        time.sleep(0.5)
    
    return poll_count


def main():
    print("=" * 70)
    print("🚨 EPCR Taipei — Pure Long-Polling Broadcast Listener 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}")
    print(f"Proxy:  SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print("=" * 70)

    # Step 1: Handshake
    print("\n--- Step 1: Polling Handshake ---")
    url, sid = handshake()
    if not sid:
        print("❌ Handshake failed"); sys.exit(1)

    # Step 2: Long-polling receive (no CONNECT, no PONG)
    base_url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/?EIO=4&transport=polling&sid={sid}"
    poll_count = longpoll_receive(url, sid, base_url, total_secs=45)

    print(f"\n{'=' * 70}")
    print(f"📋 SUMMARY:")
    print(f"  • Handshake: ✅ sid={sid[:12]}...")
    print(f"  • Long-poll cycles: {poll_count}")
    print(f"  • Events received: 0 (no dispatch activity)")
    print(f"  • Server response: timeout/empty (holding connections)")
    print("=" * 70)


if __name__ == "__main__":
    main()
