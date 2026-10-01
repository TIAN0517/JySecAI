#!/usr/bin/env python3
"""Socket.IO :3400 authServer 业务事件探测"""
import socketio
import time
import sys

TARGET = 'http://35.234.50.28:3400'

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

@sio.on('*')
def catch_all(event, data=None):
    print(f'[EVT] {event} data={data}', flush=True)
    events_received.append((event, data))

try:
    sio.connect(TARGET, transports=['websocket', 'polling'], wait_timeout=10)
    print(f'[+] Got sid={sio.sid}', flush=True)
    sio.sleep(3)
    print(f'[*] Emitting auth-related events...', flush=True)
    for ev in ['login', 'auth', 'token', 'captcha', 'verify', 'register',
               'refresh', 'oauth', 'session', 'logout', 'password',
               'reset', 'activate', 'ssoLogin', 'sso', 'user', 'users',
               'permission', '2fa', 'totp']:
        try:
            sio.emit(ev, {})
            print(f'  [emit] {ev}', flush=True)
        except Exception as e:
            print(f'  [emit fail] {ev}: {e}', flush=True)
    sio.sleep(5)
    print(f'[*] Total events received: {len(events_received)}', flush=True)
    for ev, d in events_received:
        print(f'  - {ev}: {d}', flush=True)
    sio.disconnect()
except Exception as e:
    print(f'[FATAL] {type(e).__name__}: {e}', flush=True)
    sys.exit(1)