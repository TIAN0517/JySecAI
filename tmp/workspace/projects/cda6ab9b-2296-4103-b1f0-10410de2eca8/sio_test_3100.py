#!/usr/bin/env python3
"""Socket.IO 长连接 + 业务事件 emit 测试 :3100 vitalSignVideoServer"""
import socketio
import time
import sys

TARGET = 'http://35.234.50.28:3100'

sio = socketio.Client(logger=True, engineio_logger=True, ssl_verify=False)

events_received = []

@sio.event
def connect():
    print(f'[+] CONNECTED to {TARGET}', flush=True)

@sio.event
def connect_error(data):
    print(f'[-] CONNECT_ERROR: {data}', flush=True)

@sio.event
def disconnect():
    print(f'[-] DISCONNECTED', flush=True)

# 捕获所有未知事件
@sio.on('*')
def catch_all(event, data=None):
    sid = sio.sid
    print(f'[EVT] {event} data={data}', flush=True)
    events_received.append((event, data))

try:
    print(f'[*] Connecting to {TARGET} ...', flush=True)
    sio.connect(TARGET, transports=['websocket', 'polling'], wait_timeout=10)
    print(f'[+] Got sid={sio.sid}', flush=True)
    print(f'[*] Sleeping 3s for any server-pushed events...', flush=True)
    sio.sleep(3)
    print(f'[*] Emitting common event names...', flush=True)
    for ev in ['vitalSign', 'stream', 'subscribe', 'join', 'room', 'patient',
               'video', 'sign', 'data', 'connect', 'auth', 'login',
               'status', 'case', 'event', 'message', 'new', 'update']:
        try:
            sio.emit(ev, {})
            print(f'  [emit] {ev}', flush=True)
        except Exception as e:
            print(f'  [emit fail] {ev}: {e}', flush=True)
    print(f'[*] Sleeping 5s for ack/push...', flush=True)
    sio.sleep(5)
    print(f'[+] Total events received: {len(events_received)}', flush=True)
    for ev, d in events_received:
        print(f'  - {ev}: {d}', flush=True)
    sio.disconnect()
except Exception as e:
    print(f'[FATAL] {type(e).__name__}: {e}', flush=True)
    sys.exit(1)
