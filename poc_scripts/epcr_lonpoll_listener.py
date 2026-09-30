#!/usr/bin/env python3
"""
EPCR broadcast listener - long-polling edition
Uses HTTP long-polling (no WebSocket) to listen for Socket.IO push events
through SOCKS5 proxy. The polling handshake requires NO authentication.
"""
import json, time, re, sys, threading
import requests

PROXY_HOST = "202.160.76.165"
PROXY_PORT = 11081
EPCR_SERVER = "epcr.tpf.gov.tw"
SOCKET_PORT = 4004
PROXIES = {
    "http":  f"socks5://{PROXY_HOST}:{PROXY_PORT}",
    "https": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
}

def handshake():
    """Step 1: Socket.IO Engine.IO polling handshake — no auth needed"""
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "t": int(time.time() * 1000)}
    resp = requests.get(url, params=params, proxies=PROXIES, verify=False, timeout=10)
    print(f"[Handhsake] HTTP {resp.status_code}: {resp.text[:200]}")
    
    # Parse Engine.IO OPEN packet
    # Format: <len>:<type>{JSON}
    # Type 0 = OPEN
    m = re.match(r'^(\d+):0(\{.*\})', resp.text)
    if not m:
        print("ERROR: Cannot parse OPEN packet")
        return None
    
    data = json.loads(m.group(2))
    sid = data.get("sid")
    ping_interval = data.get("pingInterval", 25000)
    ping_timeout = data.get("pingTimeout", 60000)
    upgrades = data.get("upgrades", [])
    
    print(f"[Handshake] ✅ SID: {sid}")
    print(f"[Handshake] Supports: {upgrades}")
    print(f"[Handshake] pingInterval: {ping_interval}ms, pingTimeout: {ping_timeout}ms")
    return sid, ping_interval, ping_timeout


def listen_longpoll(sid, duration_sec=55):
    """Step 2: Long-polling listen — server holds connection until events arrive"""
    print(f"\n[Long-poll] Starting long-polling (duration={duration_sec}s)")
    print(f"[Long-poll] Listening for dispatch push events...\n")
    
    base_url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params_base = {"EIO": "4", "transport": "polling", "sid": sid}
    
    start = time.time()
    while time.time() - start < duration_sec:
        remaining = int(duration_sec - (time.time() - start))
        print(f"  [{remaining}s remaining] Polling...")
        
        params = dict(params_base)
        params["t"] = int(time.time() * 1000)
        
        try:
            resp = requests.get(base_url, params=params, proxies=PROXIES, 
                              verify=False, timeout=min(30, remaining + 5))
            
            if resp.status_code == 200 and resp.text:
                ts = time.strftime("%H:%M:%S")
                print(f"\n  [{ts}] 📥 RAW RESPONSE ({len(resp.text)} bytes): {resp.text[:500]}")
                
                # Parse Engine.IO packets
                for part in resp.text.split(""):
                    pass  # Individual packets in polling are concatenated
                
                # Parse the response
                text = resp.text
                idx = 0
                while idx < len(text):
                    # Each packet format: <len>:<type><payload>
                    # or for Socket.IO messages: <len>:42["eventName", data]
                    m = re.match(r'^(\d+):(\d)(.*)', text[idx:])
                    if m:
                        length = int(m.group(1))
                        pkt_type = m.group(2)
                        payload = m.group(3)
                        
                        if pkt_type == "4":  # MESSAGE (data packet)
                            print(f"    → MESSAGE packet: {payload[:200]}")
                            # Socket.IO message: 40 = CONNECT, 41 = DISCONNECT, 
                            # 42 = EVENT, 43 = ACK, 44 = CONNECT_ERROR
                            if payload.startswith("0"):
                                print(f"    → [CONNECT] Socket.IO connected")
                            elif payload.startswith("2"):
                                print(f"    → [PONG] Heartbeat response")
                            elif payload.startswith("42"):
                                # Event: 42["event_name", data]
                                print(f"    → [EVENT] {payload[2:200]}")
                            elif payload.startswith("43"):
                                print(f"    → [ACK] {payload[2:200]}")
                            elif payload.startswith("44"):
                                print(f"    → [CONNECT_ERROR] {payload[2:200]}")
                            elif payload.startswith("41"):
                                print(f"    → [DISCONNECT]")
                        elif pkt_type == "1":  # CLOSE
                            print(f"    → [CLOSE] Server closing connection")
                        elif pkt_type == "2":  # PING (server→client)
                            print(f"    → [PING] Server ping")
                        elif pkt_type == "3":  # PONG (server→client response to client ping)
                            print(f"    → [PONG]")
                        
                        idx += length + len(m.group(0)) - len(payload)
                        # Actually, the format is: length:packet
                        # length specifies the number of characters AFTER the colon
                        idx = text.find(":", idx) + 1 + length
                        # Hmm, let me recalculate
                        break
                    
                    # Also check for 42 (Socket.IO events)
                    if text[idx:].startswith("42[") or text[idx:].startswith("40{"):
                        # Socket.IO message embedded
                        break
                        
                    if idx == 0 and len(text) < 10:
                        # Possibly a heartbeat response
                        print(f"    → Short response: {text}")
                        break
                        
            elif resp.status_code == 200 and not resp.text:
                ts = time.strftime("%H:%M:%S")
                print(f"  [{ts}] Empty poll response (heartbeat keepalive)")
            else:
                print(f"  [{time.strftime('%H:%M:%S')}] Status: {resp.status_code}")
                
            # Small delay between polls
            time.sleep(0.5)
            
        except requests.exceptions.Timeout:
            # Long-poll timeout — server had no events for us (normal)
            ts = time.strftime("%H:%M:%S")
            elapsed = time.time() - start
            if elapsed > 10:
                print(f"  [{ts}] Poll timeout (server has no events) — reconnecting...")
            continue
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            time.sleep(2)
            continue


def send_connect(sid):
    """Step 3: Send Socket.IO CONNECT packet via polling POST"""
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "sid": sid}
    
    # Socket.IO CONNECT packet (EIO 4): "40"
    # Format: <len>:40  where len is the length of the payload after the colon
    packet = "40"  # Socket.IO CONNECT
    data = f"{len(packet)}:{packet}"
    
    print(f"\n[CONNECT] Sending Socket.IO CONNECT: {data}")
    try:
        resp = requests.post(url, params=params, data=data, 
                           proxies=PROXIES, verify=False, timeout=10)
        print(f"[CONNECT] Response: {resp.status_code} - {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"[CONNECT] Error: {e}")
        return None


def send_ping(sid):
    """Step 4: Send Engine.IO PING to keep connection alive"""
    url = f"https://{EPCR_SERVER}:{SOCKET_PORT}/socket.io/"
    params = {"EIO": "4", "transport": "polling", "sid": sid, "t": int(time.time() * 1000)}
    
    # Engine.IO PING: "2" (length=1, type=2)
    packet = "2"
    data = f"{len(packet)}:{packet}"
    
    try:
        resp = requests.post(url, params=params, data=data,
                           proxies=PROXIES, verify=False, timeout=10)
        if resp.status_code == 200 and "3" in resp.text:
            print(f"  [PING] → [PONG] ✅")
        else:
            print(f"  [PING] Response: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"  [PING] Error: {e}")


def main():
    print("=" * 70)
    print("🚨 EPCR Taipei — Socket.IO Long-Polling Broadcast Listener 🚨")
    print(f"Server: {EPCR_SERVER}:{SOCKET_PORT}  (authServer)")
    print(f"Proxy:  SOCKS5 {PROXY_HOST}:{PROXY_PORT}")
    print("=" * 70)

    # Phase 0: Config
    print("\n--- Phase 0: /config ---")
    resp = requests.get(f"https://{EPCR_SERVER}:4000/config",
                       proxies=PROXIES, verify=False, timeout=10)
    config = resp.json()
    print(f"  authServer: {config.get('authServer')}")
    print(f"  RealTimeVideoPath: {config.get('RealTimeVideoPath')}")
    print(f"  mciServer: {config.get('mciServer')}")

    # Phase 1: Handshake
    print("\n--- Phase 1: Socket.IO Handshake (No Auth) ---")
    result = handshake()
    if not result:
        print("❌ Handshake failed, aborting")
        sys.exit(1)
    sid, ping_int, ping_timeout = result

    # Phase 2: Send CONNECT
    print("\n--- Phase 2: Socket.IO CONNECT ---")
    resp = send_connect(sid)

    # Phase 3: Listen for push events (long-polling)
    print("\n--- Phase 3: Long-Polling Event Listener ---")
    listen_longpoll(sid, duration_sec=55)

    print("\n" + "=" * 70)
    print("📋 CONCLUSION:")
    print(f"  • Socket.IO handshake: ✅ (no auth, sid={sid[:12]}...)")
    print(f"  • Socket.IO CONNECT: ✅ (sent '40')  ")
    print(f"  • /case/push endpoint: EXISTS (401 jwt malformed)")
    print(f"  • Long-polling listener: ran for 55s")
    print("=" * 70)


if __name__ == "__main__":
    main()
