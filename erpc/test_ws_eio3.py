import requests, urllib3, json, re, time, ssl, socket, base64, os
urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787
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
    ssock.settimeout(3)
    
    # Read initial handshake
    time.sleep(0.5)
    data = ssock.recv(4096)
    print(f"Handshake: {data[:300]}")
    
    # Send join event
    join = '42["join",{"name":"femet","room":"myRoom123"}]'
    ssock.send(join.encode())
    time.sleep(1)
    
    try:
        resp1 = ssock.recv(4096)
        print(f"After join: {resp1[:500]}")
    except:
        print("No join response")
    
    # Listen for events
    print("Listening for 25 seconds...")
    for i in range(13):
        try:
            data = ssock.recv(4096)
            if data:
                print(f"  [{i*2}s] {data[:500]}")
        except socket.timeout:
            # Send ping
            try:
                ssock.send(b"2")
                try:
                    pong = ssock.recv(4096)
                    print(f"  [{i*2}s] Pong: {pong[:100]}")
                except:
                    pass
            except:
                pass
        except Exception as e:
            print(f"  [{i*2}s] {e}")
            break
        time.sleep(2)
    
    ssock.close()
else:
    print(f"Upgrade failed: {resp[:200]}")
    ssock.close()
