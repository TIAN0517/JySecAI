import requests
import urllib3
import json
import re
import time
import ssl
import socket
import base64
import os

urllib3.disable_warnings()

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
host = "tpertc.tfd.gov.tw"
port = 8787

# Try websocket upgrade with token in different header positions
ws_key = base64.b64encode(os.urandom(16)).decode()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def try_ws_upgrade(headers_dict, desc):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    ssock.connect((host, port))

    header_lines = ""
    for k, v in headers_dict.items():
        header_lines += f"{k}: {v}\r\n"

    request = (
        f"GET /socket.io/?EIO=3&transport=websocket HTTP/1.1\r\n"
        f"Host: tpesig.femet.com.tw\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Origin: https://tpesig.femet.com.tw\r\n"
        f"{header_lines}"
        f"\r\n"
    )
    ssock.send(request.encode())

    resp = ssock.recv(4096)
    if b"101" in resp:
        print(f"[{desc}] UPGRADE SUCCESS!")
        time.sleep(0.5)

        # Read initial data
        try:
            ssock.settimeout(3)
            data = ssock.recv(4096)
            print(f"  Initial: {data[:200]}")

            if b"\x88" not in data:
                # Send auth
                auth = '0{"token":"' + token + '"}'
                ssock.send(auth.encode())
                time.sleep(1)
                try:
                    resp1 = ssock.recv(4096)
                    print(f"  Auth resp: {resp1[:200]}")
                except:
                    print("  No auth resp")

                # Send join
                join = '42["join",{"name":"femet","room":"myRoom123"}]'
                ssock.send(join.encode())
                time.sleep(2)
                try:
                    resp2 = ssock.recv(4096)
                    print(f"  Join resp: {resp2[:500]}")
                except:
                    print("  No join resp")

                # Listen longer
                print("  Listening 20s...")
                for i in range(10):
                    time.sleep(2)
                    try:
                        data = ssock.recv(4096)
                        if data:
                            print(f"  [{i*2}s] {data[:300]}")
                    except socket.timeout:
                        pass
                    except:
                        break
        except:
            pass
    else:
        print(f"[{desc}] Failed: {resp[:200]}")

    ssock.close()


# Try token in various places
try_ws_upgrade({}, "no-auth")
try_ws_upgrade({"Authorization": f"Bearer {token}"}, "bearer-header")
try_ws_upgrade({"Cookie": f"cool-jwt={token}", "Cookie": f"io={token}"}, "jwt-cookie")
try_ws_upgrade({"Sec-WebSocket-Protocol": f"Bearer {token}"}, "ws-protocol")
try_ws_upgrade({"Cool-Jwt": token}, "cool-jwt-header")
try_ws_upgrade({"Token": token}, "token-header")
