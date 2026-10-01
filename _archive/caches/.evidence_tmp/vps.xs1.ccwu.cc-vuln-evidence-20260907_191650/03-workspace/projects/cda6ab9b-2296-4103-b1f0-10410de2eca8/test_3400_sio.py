"""3400 authServer socket.io 业务事件深探测 — 已知 auth 服务相关业务事件名"""
import socketio
import time
import json

sio = socketio.Client(logger=False, engineio_logger=False)
events_received = []
connected_to_namespace = False

@sio.on('connect')
def on_connect():
    global connected_to_namespace
    connected_to_namespace = True
    print(f'[+] 3400 socket.io CONNECTED sid={sio.sid}', flush=True)

@sio.on('disconnect')
def on_disconnect():
    print('[-] 3400 socket.io DISCONNECTED', flush=True)

@sio.on('*')
def catch_all(event, data=None):
    events_received.append((event, data))
    print(f'[event] {event}: {json.dumps(data)[:300] if data else None}', flush=True)

print('[*] Step 1: connecting to 3400 socket.io /...', flush=True)
try:
    sio.connect('http://35.234.50.28:3400',
                transports=['websocket', 'polling'],
                socketio_path='/socket.io',
                wait_timeout=10)
    time.sleep(2)
    print(f'[*] connected={sio.connected} sid={sio.sid}', flush=True)

    print('[*] Step 2: emitting candidate business events on /', flush=True)
    # 业务事件猜测（基于 3400 /captcha /login /refreshToken /ssoLogin 已知端点 + socket.io 通用事件）
    candidates = [
        'login', 'captcha', 'captchaRefresh', 'refreshCaptcha',
        'refreshToken', 'refresh', 'ssoLogin', 'sso', 'auth',
        'authenticate', 'validateSession', 'checkAuth',
        'subscribe', 'client.subscribe', 'client.unsubscribe',
        'message', 'notify', 'notification', 'event',
        'join', 'leave', 'room', 'online', 'presence',
        'caseUpdate', 'caseCreated', 'caseCompleted',
        'dispatch', 'dispatchRecord', 'dispatchUpdate',
        'pong', 'heartbeat', 'ping',
    ]
    for ev in candidates:
        try:
            sio.emit(ev, {'test': 1, 'src': 'pentest', 'ts': int(time.time())})
            print(f'  emit {ev}: ok', flush=True)
        except Exception as e:
            print(f'  emit {ev}: err {e}', flush=True)

    print('[*] Step 3: waiting 8s for server-pushed events', flush=True)
    time.sleep(8)

    print(f'[*] Total events received: {len(events_received)}', flush=True)
    for ev, data in events_received[:20]:
        print(f'  - {ev}: {json.dumps(data)[:200] if data else None}', flush=True)

except Exception as e:
    print(f'[!] connection error: {type(e).__name__}: {e}', flush=True)
finally:
    try:
        sio.disconnect()
    except Exception:
        pass