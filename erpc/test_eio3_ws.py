import requests, urllib3, json, re, time, ssl, socket, struct
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# Step 1: EIO=3 polling handshake with tpesig Host
r = requests.get(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling",
    headers={"Host": "tpesig.femet.com.tw"},
    verify=False, timeout=10
)
print(f"Handshake: {r.status_code}")
print(f"Body: {r.text[:300]}")

# Parse SID and cookie
sid_match = re.search(r'"sid":"([^"]+)"', r.text)
set_cookie = r.headers.get("Set-Cookie", "")
print(f"SID: {sid_match.group(1) if sid_match else 'N/A'}")
print(f"Cookie: {set_cookie[:100]}")

# Step 2: Send auth via polling
sid = sid_match.group(1)
cookies = r.cookies

# Send CONNECT with auth
auth_packet = f'0{{"token":"{token}"}}'

r2 = requests.post(
    f"https://{host}:{port}/socket.io/?EIO=3&transport=polling&sid={sid}",
    headers={
        "Host": "tpesig.femat.com.tw" if False else "tpesig.femet.com.tw",
    },
    cookies=cookies,
    data=auth_packet,
    verify=False, timeout=15
)
print(f"\nAuth POST: {r2.status_code}")
print(f"Auth body: {r2.text[:300]}")

# Check if sid changed (it does after auth in some implementations)
sid2_match = re.search(r'"sid":"([^"]+)"', r2.text)
print(f"New SID: {sid2_match.group(1) if sid2_match else 'same'}")

# Step 3: Websocket upgrade
sid_final = sid2_match.group(1) if sid2_match else sid
ws_key = "dGhlIHNhbXBsZSBub25jZQ=="

# Generate a proper websocket key
import os, base64
ws_key = base64.b64encode(os.urandom(16)).decode()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock = ctx.wrap_socket(sock, server_hostname=host)
ssock.connect((host, port))

# WebSocket upgrade request with tpesig Host
request = (
    f"GET /socket.io/?EIO=3&transport=websocket&sid={sid_final} HTTP/1.1\r\n"
    f"Host: tpesig.femet.com.tw\r\n"
    f"Upgrade: websocket\r\n"
    f"Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {ws_key}\r\n"
    f"Sec-WebSocket-Version: 13\r\n"
    f"Origin: https://tpesig.femet.com.tw\r\n"
    f"Cookie: {set_cookie.split(';')[0] if set_cookie else ''}\r\n"
    f"\r\n"
)
ssock.send(request.encode())

resp = ssock.recv(4096)
print(f"\nWS Upgrade: {resp[:300]}")

if b"101" in resp:
    print("WebSocket upgrade SUCCESS!")
    time.sleep(0.5)
    
    # Read initial handshake (engine.io open packet)
    data = ssock.recv(4096)
    print(f"After upgrade: {data[:300]}")
    
    # The server might send the open packet again or go straight to Socket.IO
    # In EIO=3, after upgrade, server sends: 0{"sid":"...","upgrades":[],...}
    # Then we need to send our CONNECT auth
    
    # Send CONNECT with auth (0{json})
    auth = f'0{{"token":"{token}"}}'
    ssock.send(auth.encode())
    time.sleep(1)
    
    resp1 = ssock.recv(4096)
    print(f"Auth response: {resp1[:300]}")
    
    # Send join event
    join = '42["join",{"name":"femet","room":"myRoom123"}]'
    ssock.send(join.encode())
    time.sleep(2)
    
    resp2 = ssock.recv(4096)
    print(f"After join: {resp2[:500]}")
    
    # Listen for events
    print("Listening for 30 seconds...")
    for i in range(15):
        time.sleep(2)
        try:
            ssock.settimeout(2)
            data = ssock.recv(4096)
            if data:
                # Decode websocket frames
                if len(data) > 2:
                    opcode = data[0] & 0x0F
                    if opcode == 0x8:  # Close
                        print(f"  [{i*2}s] Close frame: {data}")
                        break
                    elif opcode == 0x1:  # Text
                        print(f"  [{i*2}s] Text: {data[2:].decode('utf-8', errors='replace')[:500]}")
                    elif opcode == 0x88:  # Close (masked from server)
                        print(f"  [{i*2}s] Close: {data}")
                        break
            else:
                print(f"  [{i*2}s] connection closed")
                break
        except socket.timeout:
            pass
        except Exception as e:
            print(f"  [{i*2}s] error: {e}")
            break
    
    ssock.close()
else:
    print("WebSocket upgrade failed")
    ssock.close()
