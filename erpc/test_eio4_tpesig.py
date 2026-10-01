import ssl
import socket
import base64
import struct
import time
import os

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

def make_frame(data, opcode=0x1, fin=True):
    if isinstance(data, str):
        data = data.encode()
    header = bytearray()
    b0 = (0x80 if fin else 0x00) | opcode
    header.append(b0)
    length = len(data)
    mask_bit = 0x80
    if length <= 125:
        header.append(mask_bit | length)
    elif length <= 65535:
        header.append(mask_bit | 126)
        header.extend(struct.pack(">H", length))
    else:
        header.append(mask_bit | 127)
        header.extend(struct.pack(">Q", length))
    mask_key = os.urandom(4)
    header.extend(mask_key)
    masked_data = bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))
    return bytes(header) + masked_data

def parse_frames(data):
    frames = []
    pos = 0
    while pos < len(data):
        if pos + 2 > len(data): break
        b0 = data[pos]
        b1 = data[pos + 1]
        opcode = b0 & 0x0F
        length = b1 & 0x7F
        masked = b1 & 0x80
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
            payload = bytes(b ^ mask_key[i%4] for i,b in enumerate(data[pos:pos+length]))
        else:
            payload = data[pos:pos+length]
        pos += length
        frames.append((opcode, payload))
    return frames

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock = ctx.wrap_socket(sock, server_hostname=host)
ssock.connect((host, port))
ssock.settimeout(5)

# EIO=4 with tpesig Host and token in URL
ws_key = base64.b64encode(os.urandom(16)).decode()
request = (
    f"GET /socket.io/?EIO=4&transport=websocket&token={token} HTTP/1.1\r\n"
    f"Host: tpesig.femet.com.tw\r\n"
    f"Upgrade: websocket\r\n"
    f"Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {ws_key}\r\n"
    f"Sec-WebSocket-Version: 13\r\n"
    f"Origin: https://tpesig.femet.com.tw\r\n"
    f"\r\n"
)
ssock.send(request.encode())

resp = ssock.recv(4096)
print(f"Upgrade: {'SUCCESS' if b'101' in resp else 'FAILED'}")
print(f"Response: {resp[:200]}")

if b"101" in resp:
    time.sleep(0.5)
    data = ssock.recv(4096)
    frames = parse_frames(data)
    for op, payload in frames:
        print(f"  Initial frame: opcode={op} payload={payload[:300]}")
    
    # Send CONNECT with auth (EUI=4: 0{auth})
    auth = f'0{{"token":"{token}"}}'
    ssock.send(make_frame(auth))
    print(f"\nSent auth: {auth}")
    
    time.sleep(2)
    try:
        data = ssock.recv(4096)
        frames = parse_frames(data)
        for op, payload in frames:
            print(f"  Auth resp: opcode={op} payload={payload[:300]}")
    except socket.timeout:
        print("No auth response (timeout)")
    
    # Send join
    join = '42["join",{"name":"femet","room":"myRoom123"}]'
    ssock.send(make_frame(join))
    print(f"Sent join")
    
    time.sleep(2)
    try:
        data = ssock.recv(4096)
        frames = parse_frames(data)
        for op, payload in frames:
            print(f"  Join resp: opcode={op} payload={payload[:500]}")
    except socket.timeout:
        print("No join response (timeout)")
    
    # Listen
    print("\nListening for 20s...")
    start = time.time()
    while time.time() - start < 20:
        try:
            data = ssock.recv(4096)
            if data:
                frames = parse_frames(data)
                for op, payload in frames:
                    print(f"  [{time.time()-start:.1f}s] opcode={op} payload={payload[:500]}")
        except socket.timeout:
            ssock.send(make_frame("2"))
            try:
                data = ssock.recv(4096)
                frames = parse_frames(data)
                for op, payload in frames:
                    print(f"  [{time.time()-start:.1f}s] recv after ping: opcode={op} payload={payload[:100]}")
            except: pass
    ssock.close()
