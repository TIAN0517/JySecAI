import socketio
import urllib3, requests, json, time
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Test 1: Connect with auth but DON'T send join
sio1 = socketio.Client(ssl_verify=False)

@sio1.event
def connect():
    print("Test 1: Connected (no join) - staying idle")
    time.sleep(3)
    print(f"Still connected: {sio1.connected}")

@sio1.event
def disconnect():
    print("Test 1: Disconnected")

@sio1.on("*")
def on_event(event, data):
    print(f"Test 1 EVENT: {event} {json.dumps(data, default=str)[:200]}")

try:
    sio1.connect(
        "wss://tpertc.tfd.gov.tw:8787",
        auth={"token": token},
        transports=["websocket"],
        socketio_path="/socket.io",
        wait_timeout=10
    )
    time.sleep(30)
    sio1.disconnect()
except Exception as e:
    print(f"Test 1 error: {e}")

print("\n--- Test 1 done ---")

# Test 2: Try different room names
rooms = ["lobby", "default", "room1", "room", "call", "doctor", "patient", 
         "femet", "admin", "global", "main", "office"]

for room in rooms:
    sio2 = socketio.Client(ssl_verify=False)
    
    @sio2.event
    def connect():
        print(f"Test room={room}: Connected, trying join")
        sio2.emit("join", {"name": "femet", "room": room})
    
    @sio2.event
    def disconnect():
        print(f"Test room={room}: Disconnected")
    
    @sio2.on("*")
    def on_event(event, data):
        print(f"  room={room} EVENT: {event}")
    
    @sio2.on("message")
    def on_msg(data):
        print(f"  room={room} MESSAGE: {json.dumps(data, default=str)[:200]}")
    
    # Also register a handler that checks for 'join' callback
    @sio2.on("join")
    def on_join(data):
        print(f"  room={room} JOIN callback: {data}")
    
    try:
        sio2.connect(
            "wss://tpertc.tfd.gov.tw:8787",
            auth={"token": token},
            transports=["websocket"],
            socketio_path="/socket.io",
            wait_timeout=10
        )
        time.sleep(5)
        if sio2.connected:
            sio2.disconnect()
        time.sleep(1)
    except Exception as e:
        print(f"Test room={room}: Error: {e}")

print("\n--- All tests done ---")
