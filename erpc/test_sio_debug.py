import socketio
import urllib3, requests, json, time
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

events = []

sio = socketio.Client(ssl_verify=False, logger=True, engineio_logger=True)

@sio.event
def connect():
    print("\n>>> CONNECTED!")
    sio.emit("join", {"name": "femet", "room": "myRoom123"})

@sio.event
def connect_error(data):
    print(f"\n>>> CONNECT_ERROR: {data}")

@sio.event
def disconnect():
    print(f"\n>>> DISCONNECTED")

@sio.on("*")
def catch_all(event, data):
    print(f">>> EVENT {event}: {json.dumps(data, default=str)[:300]}")
    events.append({"event": event, "data": str(data)})

@sio.on("message")
def on_message(data):
    print(f">>> MESSAGE: {json.dumps(data, default=str)[:300]}")
    events.append({"event": "message", "data": str(data)})

try:
    sio.connect(
        "wss://tpertc.tfd.gov.tw:8787",
        auth={"token": token},
        transports=["websocket"],
        socketio_path="/socket.io",
        wait_timeout=10
    )
    
    print(f"Connected: {sio.connected}")
    
    for i in range(30):
        time.sleep(1)
        if not sio.connected:
            print(f"Disconnected after {i}s")
            break
    
    sio.disconnect()
except Exception as e:
    print(f"Error: {e}")

print(f"\nTotal events: {len(events)}")
