import socketio
import urllib3
import requests
import json
import time

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

print(f"Token: {token[:20]}...")

# Test 1: EPCR port 4000 Socket.IO with Authorization query param
print("\n=== EPCR 4000 Socket.IO with token ===")
sio1 = socketio.Client(ssl_verify=False)

@sio1.event
def connect():
    print("EPCR 4000: CONNECTED")
    sio1.emit("join", {"room": "admin"})
    time.sleep(15)
    sio1.disconnect()

@sio1.event
def disconnect(reason):
    print(f"EPCR 4000: DISCONNECTED {reason}")

@sio1.event
def message(data):
    print(f"EPCR 4000 MSG: {data}")

try:
    sio1.connect(
        f"wss://epcr.tpf.gov.tw:4000/socket.io/?Authorization=Bearer {token}",
        transports=["websocket"],
        wait_timeout=10,
    )
    sio1.wait()
except Exception as e:
    print(f"EPCR 4000 error: {e}")

# Test 2: RTC port 8787 with token in query
print("\n=== RTC 8787 Socket.IO with token in query ===")
sio2 = socketio.Client(ssl_verify=False)

@sio2.event
def connect2():
    print("RTC 8787: CONNECTED")
    sio2.emit("join", {"name": "femet", "room": "myRoom123"})
    time.sleep(15)
    sio2.disconnect()

@sio2.event
def disconnect2(reason):
    print(f"RTC 8787: DISCONNECTED {reason}")

@sio2.event
def message2(data):
    print(f"RTC 8787 MSG: {data}")

try:
    sio2.connect(
        f"wss://tpertc.tfd.gov.tw:8787/socket.io/?token={token}",
        transports=["websocket"],
        wait_timeout=10,
    )
    sio2.wait()
except Exception as e:
    print(f"RTC 8787 error: {e}")
