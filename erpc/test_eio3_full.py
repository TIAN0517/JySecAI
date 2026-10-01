import requests, urllib3, json, re, time, ssl, socket, base64, os, struct
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

def make_mask():
    return os.urandom(4)

def ws_send_raw(ssock, data):
    """Send a masked text frame (client-to-server must be masked)"""
    mask = make_mask()
    payload = data.encode() if isinstance(data, str) else data
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    header = bytearray()
    header.append(0x81)  # FIN + text frame
    if len(payload) <= 125:
        header.append(0x80 | len(payload))  # Masked + length
    elif len(payload) <= 65535:
        header.append(0x80 | 126)
        header.extend(struct.pack(">H", len(payload)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack(">Q", len(payload)))
    header.extend(mask)
    header.extend(masked)
    ssock.send(bytes(header))

def ws_recv_raw(ssock, timeout=3):
    """Receive raw websocket frames, return (opcode, payload)"""
    ssock.settimeout(timeout)
    try:
        data = ssock.recv(4096)
        if not data:
            return None, None
        # Parse websocket frame
        # Skip if it's just continuation data
        pos = 0
        frames = []
        while pos < len(data):
            if pos + 2 > len(data):
                break
            opcode = (data[pos] & 0x0F) 
            fin = (data[pos] & 0x80) >> 7
            length = data[pos + 1] & 0x7F
            masked = (data[pos + 1] & 0x80) >> 7
            pos += 2
            if length == 126:
                length = struct.unpack(">H", data[pos:pos+2])[0]
                pos += 2
            elif length == 127:
                length = struct.unpack(">Q", data[pos:pos+8])[0]
                pos += 8
            if masked:
                mask_key = data[pos:pos+4]
                pos += 4
                payload = data[pos:pos+length]
                payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
            else:
                payload = data[pos:pos+length]
            pos += length
            frames.append((opcode, payload))
        return frames
    except socket.timeout:
        return []
    except Exception as e:
        return [("error", str(e))]

ws_key = base64.b64encode(os.urandom(16)).decode()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock = ctx.wrap_socket(sock, server_hostname=host)
ssock.connect((host, port))

request = (
    "GET /socket.io/?EIO=3&transport=websocket&token=" + token + " HTTP/1.1\r\n"
    "Host: tpesig.femet.com.tw\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: " + ws_key + "\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Origin: https://tpesig.femet.com.tw\r\n"
    "\r\n"
)
ssock.send(request.encode())

resp = ssock.recv(4096)
if b"101" in resp:
    print("WebSocket upgrade SUCCESS!")
    
    # Read all frames
    frames = ws_recv_raw(ssock, timeout=3)
    for opcode, payload in frames:
        print(f"  Frame opcode={opcode} payload={payload[:300]}")
    
    # Now send our CONNECT auth packet (Socket.IO v3: 0{auth})
    auth = '0{"token":"' + token + '"}'
    print(f"\nSending CONNECT auth: {auth}")
    ws_send_raw(ssock, auth)
    
    time.sleep(1)
    frames = ws_recv_raw(ssock, timeout=3)
    for opcode, payload in frames:
        print(f"  Auth resp: opcode={opcode} payload={payload[:300]}")
    
    # Send join
    join = '42["join",{"name":"femet","room":"myRoom123"}]'
    print(f"\nSending join: {join}")
    ws_send_raw(ssock, join)
    
    time.sleep(2)
    frames = ws_recv_raw(ssock, timeout=3)
    for opcode, payload in frames:
        print(f"  Join resp: opcode={opcode} payload={payload[:500]}")
    
    # Listen
    print("\nListening for 25 seconds...")
    for i in range(13):
        time.sleep(2)
        frames = ws_recv_raw(ssock, timeout=3)
        for opcode, payload in frames:
            print(f"  [{i*2}s] opcode={opcode} payload={payload[:500]}")
        # Send pong
        ws_send_raw(ssock, "3")
    
    ssock.close()
else:
    print(f"Upgrade failed: {resp[:200]}")
    ssock.close()
