import socketio
import urllib3, requests, json, time, threading
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()

# Use python-socketio with custom headers for tpesig Host
# We need to set the Host header in the websocket connection
# python-socketio doesn't directly support custom headers in websocket,
# but we can try setting it via the transport options

results = []

def make_sio(token, desc):
    sio = socketio.Client(ssl_verify=False)
    
    @sio.event
    def connect():
        results.append(f"[{desc}] connect")
        sio.emit("join", {"name": "femet", "room": "myRoom123"})
    
    @sio.event
    def connect_error(data):
        results.append(f"[{desc}] connect_error: {data}")
    
    @sio.event
    def disconnect():
        results.append(f"[{desc}] disconnect")
    
    @sio.event
    def message(data):
        results.append(f"[{desc}] message: {json.dumps(data, default=str)[:300]}")
    
    @sio.on("*")
    def catch_all(event, data):
        results.append(f"[{desc}] {event}: {json.dumps(data, default=str)[:300]}")
    
    try:
        sio.connect(
            "wss://tpertc.tfd.gov.tw:8787",
            auth={"token": token},
            transports=["websocket"],
            socketio_path="/socket.io",
            wait_timeout=10,
            # Try to set Host header
            headers={"Host": "tpesig.femet.com.tw", "Origin": "https://tpesig.femet.com.tw"}
        )
        return sio
    except Exception as e:
        results.append(f"[{desc}] connect failed: {e}")
        return None

sio = make_sio(token, "tpesig")
if sio:
    # Wait for events
    for i in range(30):
        time.sleep(1)
        if not sio.connected:
            results.append(f"Disconnected at {i}s")
            break
    sio.disconnect()

print("\n".join(results))
