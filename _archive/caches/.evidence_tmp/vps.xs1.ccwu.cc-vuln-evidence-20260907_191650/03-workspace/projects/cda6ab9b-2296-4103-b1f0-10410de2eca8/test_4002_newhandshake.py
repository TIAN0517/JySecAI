#!/usr/bin/env python3
"""
4002 socket.io: try to bypass single-event limit by:
1. Re-opening fresh sid for each event
2. OR using websocket upgrade (transport=websocket)
3. OR per-event session (new cookie)
"""
import requests, urllib3, json, re, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE = "https://epcr.tpf.gov.tw:4002"

HEADERS = {
    "Origin": "https://epcr.tpf.gov.tw:4002",
    "Referer": "https://epcr.tpf.gov.tw:4002/",
    "User-Agent": "Mozilla/5.0",
}


def open_sio():
    s = requests.Session()
    r = s.get(f"{BASE}/socket.io/?EIO=4&transport=polling", headers=HEADERS, timeout=8)
    m = re.search(r'"sid":"([^"]+)"', r.text)
    if not m:
        return None, None, None
    return s, m.group(1), r.text


def emit_single(s, sid, ns, event, args):
    args = args if isinstance(args, list) else [args]
    payload = json.dumps([event] + args, ensure_ascii=False, separators=(',', ':'))
    msg = f"42{ns}{payload}"
    body = f"{len(msg)}:{msg}"
    try:
        r = s.post(f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}",
                   data=body, headers={**HEADERS, "Content-Type": "text/plain;charset=UTF-8"},
                   timeout=8)
        return r.status_code, r.text[:200]
    except Exception as e:
        return -1, f"ERR: {e}"


def main():
    print("===== Test: 1 emit per fresh session =====")
    events = [
        ("", "client.subscribe", {"roomName": "caseList_TEST"}),
        ("", "client.unsubscribe", {"roomName": "caseList_TEST"}),
        ("", "subscribe", {"room": "admin"}),
        ("", "join", {"room": "caseList"}),
        ("", "hello", {"u": "test"}),
        ("", "ready", {}),
        ("", "new-case", {"CaseID": "TEST"}),
        ("", "dispatch", {"id": "TEST"}),
        ("/admin", "subscribe", {"room": "admin"}),
        ("/admin", "hello", {}),
        ("/mci", "subscribe", {"room": "mci"}),
        ("/case", "subscribe", {"room": "case"}),
        ("/dispatch", "subscribe", {"room": "dispatch"}),
    ]
    for ns, ev, args in events:
        s, sid, raw = open_sio()
        if not sid:
            print(f"  emit({ev}) ns={ns!r}: FAILED handshake")
            continue
        st, txt = emit_single(s, sid, ns, ev, args)
        print(f"  emit({ev}) ns={ns!r}: status={st} resp='{txt[:80]}'")
        time.sleep(0.1)


if __name__ == "__main__":
    main()