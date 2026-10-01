import asyncio
import ssl
import json
import requests
import urllib3

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
base = "https://tpertc.tfd.gov.tw:8787"

# Test EIO=3 with tpesig Host header
r = requests.get(
    f"{base}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"tpesig EIO=3: {r.status_code} {r.text[:200]}")

# The EIO=3 handshake now offers websocket upgrade
# Let's do the proper EIO=3 websocket flow
sid_match = None
import re
m = re.search(r'"sid":"([^"]+)"', r.text)
if m:
    sid = m[1]
    print(f"SID: {sid}")

# Now try websocket upgrade with auth
import websockets

ws_url = f"wss://tpertc.tfd.gov.tw:8787/socket.io/?EIO=3&transport=websocket&sid={sid}"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

headers = {
    "Host": "tpesig.femet.com.tw",
    "Connection": "Upgrade",
    "Upgrade": "websocket",
    "Sec-WebSocket-Version": "13",
}

async def connect_ws():
    async with websockets.connect(
        ws_url, ssl=ssl_ctx, additional_headers=headers
    ) as ws:
        # Wait for handshake
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        print(f"WS handshake: {msg}")
        
        # Send auth as Socket.IO v3 CONNECT packet
        auth = json.dumps({"token": token})
        await ws.send(f"0{auth}")
        
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Auth response: {resp}")
        except asyncio.TimeoutError:
            print("No response after auth (timeout)")
        
        # Send join
        join_data = json.dumps({"name": "femet", "room": "myRoom123"})
        await ws.send(f'42["join",{join_data}]')
        
        # Listen for events
        for i in range(15):
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"  [{i*2}s] Recv: {resp[:200]}")
            except asyncio.TimeoutError:
                print(f"  [{i*2}s] timeout")
                # Send ping
                await ws.send("2")
                try:
                    pong = await asyncio.wait_for(ws.recv(), timeout=2)
                    print(f"  Pong: {pong}")
                except:
                    pass

asyncio.run(connect_ws())
