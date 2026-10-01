import requests, urllib3, json, re, time, ssl, socket, base64, os
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# Step 1: EIO=3 polling handshake with tpesig Host to get SID and cookie
r = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Handshake: {r.status_code} {r.text[:300]}")

sid = re.search(r'"sid":"([^"]+)"', r.text).group(1) if '"sid":' in r.text else None
io_cookie = r.headers.get("Set-Cookie", "").split(";")[0] if r.headers.get("Set-Cookie") else ""
print(f"SID: {sid}")
print(f"Cookie: {io_cookie}")

# Step 2: Websocket upgrade with same SID
# In EUI=3, the websocket connection reuses the SID from polling
ws_key = base64.b64encode(os.urandom(16)).decode()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock = ctx.wrap_socket(sock, server_hostname=host)
ssock.connect((host, port))

request = (
    f"GET /socket.io/?EIO=3&transport=websocket&sid={sid} HTTP/1.1\r\n"
    f"Host: tpesig.femet.com.tw\r\n"
    f"Upgrade: websocket\r\n"
    f"Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {ws_key}\r\n"
    f"Sec-WebSocket-Version: 13\r\n"
    f"Origin: https://tpesig.femet.com.tw\r\n"
    f"{io_cookie}\r\n"
    f"\r\n"
)
ssock.send(request.encode())

resp = ssock.recv(4096)
print(f"\nWS Upgrade: {resp[:300]}")

if b"101" in resp:
    print("WebSocket upgrade SUCCESS!")
    time.sleep(0.5)
    
    # Read engine.io open packet (re-sent after upgrade)
    data = ssock.recv(4096)
    print(f"Initial data: {data[:300]}")
    
    # Send CONNECT with auth - in EIO=3, auth goes in the Socket.IO CONNECT packet
    # The CONNECT packet is: 0{json_auth}
    auth = f'0{{"token":"{token}"}}'
    ssock.send(auth.encode())
    time.sleep(1)
    
    try:
        resp1 = ssock.recv(4096)
        print(f"CONNECT response: {resp1[:300]}")
    except:
        print("No CONNECT response")
    
    # Send join event
    join = f'42["join",{{"name":"femet","room":"myRoom123"}}]'
    ssock.send(join.encode())
    time.sleep(1)
    
    try:
        resp2 = ssock.recv(4096)
        print(f"Join response: {resp2[:500]}")
    except:
        print("No join response")
    
    # Listen for events
    print("Listening for 25 seconds...")
    ssock.settimeout(3)
    for i in range(15):
        try:
            data = ssock.recv(4096)
            if data:
                print(f"  [{i*2}s] Raw: {data[:500]}")
        except socket.timeout:
            # Send pong
            try:
                ssock.send(b"3")
            except:
                pass
        except Exception as e:
            print(f"  [{i*2}s] error: {e}")
            break
    
    ssock.close()
else:
    print("WebSocket upgrade failed")
    ssock.close()
