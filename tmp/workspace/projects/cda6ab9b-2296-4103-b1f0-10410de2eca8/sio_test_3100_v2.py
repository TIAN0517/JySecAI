#!/usr/bin/env python3
"""Socket.IO :3100 多 namespace + 带 payload 探测"""
import socketio
import time
import sys

TARGET = 'http://35.234.50.28:3100'

sio = socketio.Client(logger=False, engineio_logger=False, ssl_verify=False)

events_received = []

@sio.event
def connect():
    print(f'[+] CONNECTED sid={sio.sid}', flush=True)

@sio.on('*', namespace='/')
def catch_root(event, data=None):
    print(f'[EVT /] {event}: {data}', flush=True)
    events_received.append(('/' + event, data))

# 注册多 namespace
for ns in ['/patient', '/monitor', '/video', '/sign', '/auth', '/live',
           '/room', '/admin', '/socket', '/vitalSign', '/case',
           '/hospital', '/ems', '/ecg', '/ambulance']:
    @sio.on('*', namespace=ns)
    def make_handler(n=ns):
        def handler(event, data=None):
            print(f'[EVT {n}] {event}: {data}', flush=True)
            events_received.append((n + ':' + event, data))
        return handler

try:
    sio.connect(TARGET, transports=['websocket', 'polling'], wait_timeout=10)
    print(f'[*] Sleeping 3s for connect...', flush=True)
    sio.sleep(3)
    # 尝试带 payload 的事件
    print(f'[*] Emit with payload variations on / namespace...', flush=True)
    payloads = [
        ('subscribe', {'roomId': 'lobby'}),
        ('subscribe', {'roomId': 'patient:1'}),
        ('subscribe', {'hospitalId': '1'}),
        ('join', {'roomId': 'lobby'}),
        ('auth', {'token': 'test'}),
        ('login', {'username': 'admin', 'password': 'admin'}),
        ('register', {}),
        ('identify', {}),
        ('connect', {'token': 'test'}),
        ('message', {'action': 'ping'}),
    ]
    for ev, p in payloads:
        try:
            sio.emit(ev, p)
            print(f'  [emit] {ev}({p})', flush=True)
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