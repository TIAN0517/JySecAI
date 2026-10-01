import urllib3, json, re, time, ssl, socket, base64, os
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

# Try token in URL query
request = (
    f"GET /socket.io/?EIO=3&transport=websocket&token={token} HTTP/1.1\r\n"
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
print(f"Token in URL: {resp[:300]}")

if b"101" in resp:
    print("SUCCESS! Reading data...")
    ssock.settimeout(5)
    for i in range(13):
        try:
            data = ssock.recv(4096)
            if data:
                # Check if it's a websocket frame
                if len(data) > 0:
                    print(f"  [{i*2}s] {data[:500]}")
        except socket.timeout:
            pass
        except Exception as e:
            print(f"  [{i*2}s] {e}")
            break
        time.sleep(2)

ssock.close()
